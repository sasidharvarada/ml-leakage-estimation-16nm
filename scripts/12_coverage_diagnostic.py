"""Coverage diagnostic: is gate-level error explained by gate operating points lying
outside the region the transistor models were trained on?

after 03 and 04 are in their final state:
    python3 scripts/12_coverage_diagnostic.py
    python3 scripts/12_coverage_diagnostic.py --corners 20     # quick test

Needs ngspice for the gate runs. SPICE results are cached per (seed, corners), so rerunning
after retraining the models does not repeat the SPICE work.
"""
import argparse
import importlib.util
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from sklearn.model_selection import train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OUT_DIR = "results/part_c"
RAW_FEATURES = ["vdd", "temp", "w", "vd", "vs", "vg", "vb", "vth0", "toxe", "ndep", "u0", "xj"]
BINS = [-1.0, 50.0, 90.0, 99.0, 100.01]
BIN_LABELS = ["<50", "50-90", "90-99", ">=99"]
VALID_MIN_A = 1e-13  



# Loading Part B (same trick as 05_test_circuit.py so the joblib bundles unpickle)

def load_part_b():
    spec = importlib.util.spec_from_file_location("part_b", os.path.join(HERE, "04_simulate_gates.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["part_b"] = mod
    spec.loader.exec_module(mod)
    main_mod = sys.modules["__main__"]
    for name in ("LeakageResNet", "PyTorchWrapper", "MultiOutputModel", "MultiXGB"):
        if hasattr(mod, name):
            setattr(main_mod, name, getattr(mod, name))
    return mod

PB = load_part_b()



# Features (identical to 03_train_models.py / v2)

def engineer_features(df):
    X = df[RAW_FEATURES].copy()
    X["vds"] = X["vd"] - X["vs"]
    X["abs_vds"] = np.abs(X["vds"])
    X["vgs"] = X["vg"] - X["vs"]
    X["vbs"] = X["vb"] - X["vs"]
    X["vgd"] = X["vg"] - X["vd"]
    X["overdrive"] = X["vgs"] - X["vth0"]
    return X


# Recording wrapper around a fitted StandardScaler

class RecordingScaler:
    def __init__(self, scaler, case, log):
        self._scaler, self._case, self._log = scaler, case, log

    def transform(self, X):
        Xs = self._scaler.transform(X)
        self._log.append((self._case, np.array(Xs, dtype=float)))
        return Xs

    def __getattr__(self, name):
        return getattr(self._scaler, name)



# Train split reproduction + coverage reference

def reproduce_split(df, scaler, seeds):
    """Return (seed, X_train, X_heldout) for the first seed whose train split matches the
    scaler the bundle was fit with. X_heldout = val + test rows."""
    X = engineer_features(df).values
    for seed in seeds:
        X_tr, X_tmp = train_test_split(X, test_size=0.30, random_state=seed)
        gap = np.max(np.abs(X_tr.mean(axis=0) - scaler.mean_) / scaler.scale_)
        if gap < 1e-6:
            return seed, X_tr, X_tmp
    raise RuntimeError(
        f"None of the seeds {list(seeds)} reproduces the training split of this bundle "
        f"(its scaler was fit on different rows). Pass the seed used by the script that "
        f"saved models/best_*.joblib via --seed.")


def mean_knn_dist(tree, Xs, k):
    d, _ = tree.query(Xs, k=k)
    return np.asarray(d, dtype=float).reshape(len(Xs), -1).mean(axis=1)


def build_reference(case, bundle, seeds, k):
    df = pd.read_csv(f"data/{case}.csv")
    seed, X_tr, X_held = reproduce_split(df, bundle["scaler"], seeds)
    sc = bundle["scaler"]
    tree = cKDTree(sc.transform(X_tr))
    ref = np.sort(mean_knn_dist(tree, sc.transform(X_held), k))
    return {"tree": tree, "ref": ref, "seed": seed, "n_train": len(X_tr)}


def coverage_percentile(ref_sorted, d):
    return float(np.searchsorted(ref_sorted, d, side="right")) / len(ref_sorted) * 100.0



# SPICE gate runs (cached; node voltages are needed to query the models)

def get_spice(PB, corners, seed, workers):
    path = os.path.join(OUT_DIR, f"coverage_spice_cache_seed{seed}_n{len(corners)}.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, dtype={"inp": str})
        if len(df) == len(PB.GATE_CASES) * len(corners):
            print(f"[*] using cached gate SPICE runs: {path}")
            return df
    print(f"[*] running gate SPICE: {len(PB.GATE_CASES)} cases x {len(corners)} corners ...")
    rows = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for gate, inp in PB.GATE_CASES:
            tasks = [(gate, inp, c) for c in corners]
            sims = list(pool.map(PB.simulate_gate_spice, tasks, chunksize=8))
            for ci, (leak, nv) in enumerate(sims):
                rows.append({"gate": gate, "inp": inp, "corner": ci, "spice_leak": leak,
                             "out": nv["out"], "x": nv["x"], "y": nv["y"], "n_out": nv["n_out"]})
            print(f"    {gate} {inp} done")
    df = pd.DataFrame(rows)
    os.makedirs(OUT_DIR, exist_ok=True)
    df.to_csv(path, index=False)
    return df

# Analysis

def collect(evaluator, refs, spice_df, corners, k):
    inst_rows, query_rows = [], []
    for r in spice_df.itertuples():
        if not r.spice_leak > 0:
            continue
        evaluator.log.clear()
        node_v = {"out": r.out, "x": r.x, "y": r.y, "n_out": r.n_out}
        ml = evaluator.predict_gate_leakage(r.gate, r.inp, corners[r.corner], node_v)
        pcts = []
        for case, Xs in evaluator.log:
            ref = refs[case]
            d = float(mean_knn_dist(ref["tree"], Xs, k)[0])
            p = coverage_percentile(ref["ref"], d)
            pcts.append((p, case))
            query_rows.append({"case": case, "gate": r.gate, "inp": r.inp, "corner": r.corner,
                               "dist": d, "dist_vs_median_heldout": d / float(np.median(ref["ref"])),
                               "cov_pct": p})
        worst = max(pcts, key=lambda t: t[0])
        inst_rows.append({"gate": r.gate, "inp": r.inp, "corner": r.corner,
                          "spice_leak": r.spice_leak, "ml_leak": float(ml),
                          "n_fet_queries": len(pcts),
                          "cov_max": worst[0], "worst_case": worst[1],
                          "cov_mean": float(np.mean([p for p, _ in pcts]))})
    inst = pd.DataFrame(inst_rows)
    inst["err_pct"] = np.abs(inst.ml_leak - inst.spice_leak) / inst.spice_leak * 100.0
    return inst, pd.DataFrame(query_rows)


def summarize(inst, qry, refs):
    valid = inst[inst.spice_leak > VALID_MIN_A].copy()

    print("\n" + "=" * 70)
    print(" COVERAGE OF GATE QUERIES (vs held-out in-distribution rows)")
    print("=" * 70)
    print("Training-data seed matched per case: " +
          ", ".join(f"{c}={r['seed']}" for c, r in refs.items()))
    per_case = qry.groupby("case").agg(
        n_queries=("cov_pct", "size"),
        median_cov_pct=("cov_pct", "median"),
        frac_ge95=("cov_pct", lambda s: float((s >= 95).mean())),
        frac_ge99=("cov_pct", lambda s: float((s >= 99).mean())),
    ).reset_index()
    per_case["n_train"] = per_case["case"].map(lambda c: refs[c]["n_train"])
    print("(an in-distribution case would show frac_ge95 ~ 0.05 and frac_ge99 ~ 0.01)")
    print(per_case.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    print("\n" + "=" * 70)
    print(" GATE-LEVEL ERROR vs WORST-FET COVERAGE PERCENTILE")
    print("=" * 70)
    valid["bin"] = pd.cut(valid.cov_max, BINS, labels=BIN_LABELS, right=False)
    by_bin = valid.groupby("bin", observed=False).agg(
        n=("err_pct", "size"),
        median_err_pct=("err_pct", "median"),
        p95_err_pct=("err_pct", lambda s: float(np.percentile(s, 95)) if len(s) else np.nan),
    ).reset_index()
    print(by_bin.to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    rho, pval = spearmanr(valid.cov_max, valid.err_pct)
    print(f"\nSpearman rho (cov_max vs err_pct) = {rho:.3f}   (p = {pval:.2g}, n = {len(valid)})")

    print("\n" + "=" * 70)
    print(" PER GATE STATE")
    print("=" * 70)
    per_state = valid.groupby(["gate", "inp"]).agg(
        median_err_pct=("err_pct", "median"),
        median_cov_max=("cov_max", "median"),
        frac_cov_ge95=("cov_max", lambda s: float((s >= 95).mean())),
        main_case=("worst_case", lambda s: s.mode().iat[0]),
    ).reset_index().sort_values("median_err_pct", ascending=False)
    print(per_state.to_string(index=False, float_format=lambda v: f"{v:.2f}"))

    print("""
How to read this
  - Error rising across the coverage bins, with a clearly positive Spearman rho: gate points
    lie outside the training region -> stratify / oversample the gate region and retrain.
  - frac_ge95 far above 0.05 for a case but flat error across bins: the region is
    under-covered, yet the model extrapolates acceptably there.
  - Bad states (high median_err_pct) with LOW median_cov_max: not a coverage problem. Look
    at the gate formula / assembly or at the model itself (train-vs-val gap in that region).
  - Distance is Euclidean in the standardised 18-d feature space (several features are linear
    combinations of others), so treat percentiles as a relative ranking, not a calibrated
    probability. Correlation here is not proof of cause.""")
    return per_case, by_bin, per_state, valid, rho


def make_plot(valid, per_case, rho, path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    ax = axes[0]
    ax.scatter(valid.cov_max, valid.err_pct.clip(lower=1e-3), s=6, alpha=0.3, color="navy")
    centers, meds = [], []
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        sel = valid[(valid.cov_max >= lo) & (valid.cov_max < hi)]
        if len(sel):
            centers.append(float(np.clip((max(lo, 0) + min(hi, 100)) / 2, 0, 100)))
            meds.append(float(sel.err_pct.median()))
    ax.plot(centers, meds, "r-o", lw=1.8, label="bin median")
    ax.set_yscale("log")
    ax.set_xlabel("worst-FET coverage percentile (100 = farther than every held-out row)")
    ax.set_ylabel("gate-level error vs SPICE (%)")
    ax.set_title(f"Gate error vs coverage (Spearman rho = {rho:.2f})")
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.legend()
    ax = axes[1]
    ax.bar(per_case["case"], per_case["frac_ge95"], color="steelblue", label="share of queries >= p95")
    ax.axhline(0.05, color="r", ls="--", lw=1.4, label="in-distribution expectation (0.05)")
    ax.set_ylabel("fraction of gate queries")
    ax.set_title("Gate queries beyond the 95th coverage percentile")
    ax.legend()
    ax.grid(True, axis="y", ls="--", alpha=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)



def run(args, PB):
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs("results/plots", exist_ok=True)
    seeds = [args.seed] + [s for s in (71, 42) if s != args.seed]

    corners = PB.generate_corners(num_corners=args.corners, seed=args.corner_seed)
    spice_df = get_spice(PB, corners, args.corner_seed, args.workers)

    evaluator = PB.GateMLEvaluator()
    refs = {case: build_reference(case, b, seeds, args.k) for case, b in evaluator.models.items()}

    evaluator.log = []
    for case, b in evaluator.models.items():
        b["scaler"] = RecordingScaler(b["scaler"], case, evaluator.log)

    inst, qry = collect(evaluator, refs, spice_df, corners, args.k)
    inst.to_csv(os.path.join(OUT_DIR, "coverage_gate_instances.csv"), index=False)
    qry.to_csv(os.path.join(OUT_DIR, "coverage_fet_queries.csv"), index=False)

    per_case, by_bin, per_state, valid, rho = summarize(inst, qry, refs)
    per_case.to_csv("results/coverage_by_case.csv", index=False)
    by_bin.to_csv("results/coverage_error_by_bin.csv", index=False)
    per_state.to_csv("results/coverage_by_gate_state.csv", index=False)
    make_plot(valid, per_case, rho, "results/plots/coverage_vs_error.png")
    print("\nSaved results/coverage_*.csv, results/part_c/coverage_*.csv and "
          "results/plots/coverage_vs_error.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corners", type=int, default=200)
    ap.add_argument("--corner-seed", type=int, default=7,
                    help="corner seed; 7 matches the Part C gate table (04's own main() uses 123)")
    ap.add_argument("--seed", type=int, default=71,
                    help="split seed tried first (71 = 03_train_models.py; 42 = 03_train_models_v2.py)")
    ap.add_argument("--k", type=int, default=5, help="neighbours averaged for the distance")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()
    run(args, PB)


if __name__ == "__main__":
    main()