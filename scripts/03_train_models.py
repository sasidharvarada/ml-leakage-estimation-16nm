"""Part A, step 2: train and compare 4 ML model types for each of the 4 cases.

Usage (from the repo root):
    python scripts/03_train_models.py            # full training
    python scripts/03_train_models.py --fast     # quick test (a few minutes)
    python scripts/03_train_models.py --cases nmos_off

Method
    * data/<case>.csv (10,000 uniform samples) is split 70 / 15 / 15 into
      train / validation / test with a fixed seed. Validation and test are
      ONLY ever these uniform samples, so the reported numbers are honest.
    * The extra rail-focused samples in data/rail/<case>.csv (if present, made by
      01b_generate_rail_data.py) are ADDED to the training set only.
    * Each terminal current (id, ig, is, ib) gets
        - a regressor for log10(|I|)   (this is what the 4 model types differ in)
        - a sign classifier (LightGBM), shared by all model types
      and is predicted as  I = sign * 10 ** log10|I|.
    * Model types: MLP (seed ensemble; PyTorch on the GPU if available, otherwise
      scikit-learn), LightGBM, XGBoost, RandomForest.
    * Errors are |pred - true| / |true| on every sample (no current floor),
      reported as median and 95th percentile, plus R2 of log10|I|.
    * Per case and per current, the type with the lowest validation median error
      is chosen; the 4 chosen regressors are saved together as one model file
      per case and evaluated once on the test set. A second test score is also
      reported on the held-out rail samples (operating points used in gates).

Outputs
    results/part_a/model_comparison.csv    4 model types x 4 cases x 4 currents (validation)
    results/part_a/model_comparison_summary.csv   4 x 4 table (mean over the 4 currents)
    results/part_a/chosen_models_test.csv  test-set errors of the chosen models
    results/part_a/plots/parity_<case>.png  predicted vs SPICE on the test set
    saved_models/<case>.joblib             the 4 saved model files
"""
import argparse
import os
import sys
import time
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

sys.path.insert(0, os.path.dirname(__file__))
import config as C
from leak_model import (TARGETS, AvgEnsemble, SignModel, TransistorModel,
                        make_features, to_log)

warnings.filterwarnings("ignore")
RAIL_HOLDOUT = 0.15      # share of rail rows kept aside for the extra test score


def regressor_factories(fast, n_seeds, mlp_kind):
    def mlp(seed):
        return TransformedTargetRegressor(
            regressor=make_pipeline(StandardScaler(), MLPRegressor(
                hidden_layer_sizes=(128, 128, 64), activation="tanh", solver="lbfgs",
                max_iter=2000 if fast else 15000, random_state=seed)),
            transformer=StandardScaler())

    def tmlp(seed):
        from torch_mlp import TorchMLPRegressor
        return TorchMLPRegressor(adam_steps=1500 if fast else 3000,
                                 lbfgs_iters=500 if fast else 20000, seed=seed)

    seeds = [C.SEED + i for i in range(1 if fast else n_seeds)]
    n_trees = 500 if fast else 3000
    if mlp_kind == "torch":
        mlp_entry = ("MLP", lambda X, y: AvgEnsemble([tmlp(s).fit(X, y) for s in seeds]))
    else:
        mlp_entry = ("MLP", lambda X, y: AvgEnsemble([mlp(s).fit(X, y) for s in seeds]))
    return {
        mlp_entry[0]: mlp_entry[1],
        "LightGBM": lambda X, y: LGBMRegressor(
            n_estimators=n_trees, num_leaves=31, learning_rate=0.02, subsample=0.8,
            subsample_freq=1, colsample_bytree=0.9, random_state=C.SEED, verbose=-1).fit(X, y),
        "XGBoost": lambda X, y: XGBRegressor(
            n_estimators=n_trees, max_depth=6, learning_rate=0.02, subsample=0.8,
            colsample_bytree=0.9, n_jobs=-1, random_state=C.SEED).fit(X, y),
        "RandomForest": lambda X, y: RandomForestRegressor(
            n_estimators=100 if fast else 300, n_jobs=-1, random_state=C.SEED).fit(X, y),
    }


def sign_classifier():
    return LGBMClassifier(n_estimators=400, num_leaves=31, learning_rate=0.05,
                          random_state=C.SEED, verbose=-1)


def rel_err(true, pred):
    """|pred - true| / |true| in %, skipping currents that are exactly zero."""
    true, pred = np.asarray(true), np.asarray(pred)
    m = true != 0
    return 100 * np.abs(pred[m] - true[m]) / np.abs(true[m])


def scores(true_df, pred_df):
    out = {}
    for t in TARGETS:
        e = rel_err(true_df[t], pred_df[t])
        out[t] = {"r2_log": r2_score(to_log(true_df[t]), to_log(pred_df[t])),
                  "median_err_%": np.median(e),
                  "p95_err_%": np.percentile(e, 95),
                  "sign_acc": np.mean(np.sign(true_df[t]) == np.sign(pred_df[t]))}
    return out


def parity_plot(case, true_df, pred_df, path):
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.3))
    for ax, t in zip(axes, TARGETS):
        x, y = np.abs(true_df[t].values), np.abs(pred_df[t].values)
        m = (x > 0) & (y > 0)
        ax.scatter(x[m], y[m], s=3, alpha=0.4)
        lo, hi = min(x[m].min(), y[m].min()), max(x[m].max(), y[m].max())
        ax.plot([lo, hi], [lo, hi], "r--", lw=1)
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel(f"SPICE |{t}| (A)"); ax.set_ylabel(f"ML |{t}| (A)")
        ax.set_title(f"{case}: {t}")
        ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--seeds", type=int, default=None, help="MLP ensemble size (default: 1 for PyTorch, 3 for scikit-learn)")
    ap.add_argument("--no-rail", action="store_true", help="ignore data/rail/ (uniform data only)")
    ap.add_argument("--cases", nargs="+", default=list(C.CASES))
    ap.add_argument("--mlp", choices=["auto", "torch", "sklearn"], default="auto",
                    help="auto = PyTorch (GPU if available) when torch is installed, else scikit-learn")
    args = ap.parse_args()
    if args.mlp == "auto":
        try:
            import torch_mlp
            args.mlp = "torch" if torch_mlp.TORCH_OK else "sklearn"
        except ImportError:
            args.mlp = "sklearn"
    if args.mlp == "torch":
        import torch_mlp
        print(f"MLP backend: PyTorch on {torch_mlp.device()}")
    else:
        print("MLP backend: scikit-learn (CPU)")
    for d in ["results/part_a/plots", "saved_models"]:
        os.makedirs(d, exist_ok=True)
    if args.seeds is None:
        args.seeds = 1 if args.mlp == "torch" else 3
    factories = regressor_factories(args.fast, args.seeds, args.mlp)

    comparison, chosen = [], []
    for case in args.cases:
        dev = C.CASES[case]["type"]
        df = pd.read_csv(f"data/{case}.csv")
        train, rest = train_test_split(df, test_size=0.30, random_state=C.SEED)
        val, test = train_test_split(rest, test_size=0.50, random_state=C.SEED)

        rail_test = None
        rail_path = f"data/rail/{case}.csv"
        if os.path.exists(rail_path) and not args.no_rail:
            rail = pd.read_csv(rail_path)
            rail_train, rail_test = train_test_split(rail, test_size=RAIL_HOLDOUT, random_state=C.SEED)
            train = pd.concat([train, rail_train], ignore_index=True)

        feats = list(make_features(df, dev).columns)
        Xtr = make_features(train, dev)
        print(f"\n== {case}: train {len(train)} (incl. rail {len(train) - 7000 if rail_test is not None else 0}), "
              f"val {len(val)}, test {len(test)}", flush=True)

        signs = {t: SignModel(train[t], sign_classifier, Xtr) for t in TARGETS}
        bounds = {t: (float(to_log(train[t]).min()), float(to_log(train[t]).max())) for t in TARGETS}

        trained = {}                       # model type -> {target: regressor}
        val_scores = {}                    # model type -> {target: scores}
        for name, fit in factories.items():
            t0 = time.time()
            mags = {t: fit(Xtr, to_log(train[t])) for t in TARGETS}
            sc = scores(val, TransistorModel(case, dev, name, mags, signs, feats, bounds).predict(val))
            trained[name], val_scores[name] = mags, sc
            for t, s_ in sc.items():
                comparison.append({"case": case, "model": name, "target": t, **s_})
            mean_med = np.mean([s_["median_err_%"] for s_ in sc.values()])
            print(f"  {name:12s} val median error: " +
                  "  ".join(f"{t} {sc[t]['median_err_%']:6.2f}%" for t in TARGETS) +
                  f"   mean {mean_med:6.2f}%  ({time.time()-t0:.0f} s)", flush=True)

        # best model type for EACH current (lowest validation median error)
        pick = {t: min(trained, key=lambda n: val_scores[n][t]["median_err_%"]) for t in TARGETS}
        model = TransistorModel(case, dev, dict(pick), {t: trained[pick[t]][t] for t in TARGETS},
                                signs, feats, bounds)
        model.save(f"saved_models/{case}.joblib")
        pred = model.predict(test)
        for t, s_ in scores(test, pred).items():
            chosen.append({"case": case, "model": pick[t], "test_set": "uniform", "target": t, **s_})
        if rail_test is not None:
            for t, s_ in scores(rail_test, model.predict(rail_test)).items():
                chosen.append({"case": case, "model": pick[t], "test_set": "rail", "target": t, **s_})
        print("  chosen: " + ", ".join(f"{t}={pick[t]}" for t in TARGETS) +
              f" -> saved_models/{case}.joblib", flush=True)
        parity_plot(case, test, pred, f"results/part_a/plots/parity_{case}.png")

    comp = pd.DataFrame(comparison)
    comp.to_csv("results/part_a/model_comparison.csv", index=False, float_format="%.4g")
    summ = comp.groupby(["case", "model"]).agg(
        r2_log=("r2_log", "mean"), median_err_pct=("median_err_%", "mean"),
        p95_err_pct=("p95_err_%", "mean")).reset_index()
    summ.to_csv("results/part_a/model_comparison_summary.csv", index=False, float_format="%.4g")
    ch = pd.DataFrame(chosen)
    ch.to_csv("results/part_a/chosen_models_test.csv", index=False, float_format="%.4g")

    pd.set_option("display.width", 160)
    print("\nValidation median error % (mean over id, ig, is, ib):")
    print(comp.pivot_table(index="model", columns="case", values="median_err_%").round(2))
    print("\nTest set, chosen models:")
    print(ch.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
