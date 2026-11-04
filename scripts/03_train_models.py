"""Part A, step 2: train and compare 4 ML model types for each of the 4 cases.

Usage (from the repo root):
    python scripts/03_train_models.py            # full training (about 30-60 min)
    python scripts/03_train_models.py --fast     # quick test (a few minutes)
    python scripts/03_train_models.py --cases nmos_off

Method
    * Split 70 % train / 15 % validation / 15 % test with a fixed seed.
    * Each terminal current (id, ig, is, ib) gets:
        - a regressor for log10(|I|)  (this is what the 4 model types differ in)
        - a sign classifier (LightGBM), shared by all model types
    * Model types: MLP (3-seed ensemble), LightGBM, XGBoost, RandomForest.
    * Per case, the model type with the lowest mean validation median error is
      chosen, saved, and evaluated once on the test set.

Outputs
    results/tables/model_comparison.csv    4 model types x 4 cases (validation): R2, median, p95
    results/tables/chosen_models_test.csv  test-set errors of the chosen models
    results/plots/parity_<case>.png        predicted vs SPICE on the test set
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


def regressor_factories(fast):
    def mlp(seed):
        return TransformedTargetRegressor(
            regressor=make_pipeline(StandardScaler(), MLPRegressor(
                hidden_layer_sizes=(128, 128, 64), activation="tanh", solver="lbfgs",
                max_iter=2000 if fast else 15000, random_state=seed)),
            transformer=StandardScaler())

    seeds = [C.SEED] if fast else [C.SEED, C.SEED + 1, C.SEED + 2]
    n_trees = 500 if fast else 3000
    return {
        "MLP": lambda X, y: AvgEnsemble([mlp(s).fit(X, y) for s in seeds]),
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
    ap.add_argument("--cases", nargs="+", default=list(C.CASES))
    args = ap.parse_args()
    for d in ["results/tables", "results/plots", "saved_models"]:
        os.makedirs(d, exist_ok=True)
    factories = regressor_factories(args.fast)

    comparison, chosen = [], []
    for case in args.cases:
        dev = C.CASES[case]["type"]
        df = pd.read_csv(f"data/{case}.csv")
        train, rest = train_test_split(df, test_size=0.30, random_state=C.SEED)
        val, test = train_test_split(rest, test_size=0.50, random_state=C.SEED)
        feats = list(make_features(df, dev).columns)
        Xtr, Xva = make_features(train, dev), make_features(val, dev)
        print(f"\n== {case}: train {len(train)}, val {len(val)}, test {len(test)}", flush=True)

        signs = {t: SignModel(train[t], sign_classifier, Xtr) for t in TARGETS}

        best = None
        for name, fit in factories.items():
            t0 = time.time()
            mags = {t: fit(Xtr, to_log(train[t])) for t in TARGETS}
            model = TransistorModel(case, dev, name, mags, signs, feats)
            sc = scores(val, model.predict(val))
            for t, s in sc.items():
                comparison.append({"case": case, "model": name, "target": t, **s})
            mean_med = np.mean([s["median_err_%"] for s in sc.values()])
            print(f"  {name:12s} val median error: " +
                  "  ".join(f"{t} {sc[t]['median_err_%']:6.2f}%" for t in TARGETS) +
                  f"   mean {mean_med:6.2f}%  ({time.time()-t0:.0f} s)", flush=True)
            if best is None or mean_med < best[0]:
                best = (mean_med, model)

        model = best[1]
        model.save(f"saved_models/{case}.joblib")
        pred = model.predict(test)
        for t, s in scores(test, pred).items():
            chosen.append({"case": case, "model": model.model_type, "target": t, **s})
        parity_plot(case, test, pred, f"results/plots/parity_{case}.png")
        print(f"  chosen: {model.model_type} -> saved_models/{case}.joblib", flush=True)

    comp = pd.DataFrame(comparison)
    comp.to_csv("results/tables/model_comparison.csv", index=False, float_format="%.4g")
    ch = pd.DataFrame(chosen)
    ch.to_csv("results/tables/chosen_models_test.csv", index=False, float_format="%.4g")

    pd.set_option("display.width", 160)
    print("\nValidation median error % (mean over id, ig, is, ib):")
    print(comp.pivot_table(index="model", columns="case", values="median_err_%").round(2))
    print("\nTest set, chosen models:")
    print(ch.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
