#!/usr/bin/env python3
"""Step 1 of the sampling check: is weak gate-region accuracy a model-choice problem or a coverage problem?

Trains XGBoost and the ResNet on the Part A training split (same settings, split and seed as
03_train_models_v2.py), then compares them on the VALIDATION split only, overall and in the bias
regions that gates use. The test split is never touched. No new data is generated and nothing is
saved except what you tee from stdout.

Regions (using the raw vd, vs, vdd of each sample):
  region A: source at the rail, drain at the opposite rail (full Vds). For pmos_off this is the
            output-low corner (vs >= 0.8 VDD, vd <= 0.2 VDD); for nmos_off, vd >= 0.8 VDD, vs <= 0.2 VDD.
  region B: source and drain both at the source rail (Vds near 0), for example NAND2 10 for pmos_off.

Run from the repo root (needs scripts/03_train_models_v2.py next to this file):
    python3 scripts/11_gate_region_compare.py                 # pmos_off
    python3 scripts/11_gate_region_compare.py --case nmos_off # sanity check, ResNet should win here
    python3 scripts/11_gate_region_compare.py | tee results/gate_region_compare_pmos_off.txt
"""
import argparse
import importlib.util
import os
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("v2", os.path.join(HERE, "03_train_models_v2.py"))
v2 = importlib.util.module_from_spec(_spec)
sys.modules["v2"] = v2
_spec.loader.exec_module(v2)

TARGETS = v2.TARGETS


def region_masks(case, d):
    hi, lo = 0.8 * d.vdd, 0.2 * d.vdd
    if case.startswith("pmos"):  # source sits on Vdd
        a = (d.vs >= hi) & (d.vd <= lo)
        b = (d.vs >= hi) & (d.vd >= hi)
    else:                        # source sits on ground
        a = (d.vs <= lo) & (d.vd >= hi)
        b = (d.vs <= lo) & (d.vd <= lo)
    a, b = a.values, b.values
    return {"all validation": np.ones(len(d), bool),
            "region A (full Vds at rail)": a,
            "region B (Vds near 0 at rail)": b,
            "elsewhere": ~(a | b)}


def rel_err(true_lin, pred_log):
    """Relative error in percent, both sides clipped at the 1e-18 A training floor (as in v2)."""
    true_c = np.maximum(np.abs(true_lin), v2.FLOOR_CURRENT)
    pred_c = np.maximum(10.0 ** np.clip(pred_log, -30.0, 3.0), v2.FLOOR_CURRENT)
    return np.abs(pred_c - true_c) / true_c * 100.0


def table_rows(name, rel, masks):
    rows = []
    for label, m in masks.items():
        row = {"model": name, "subset": label, "n": int(m.sum())}
        if m.sum() > 0:
            for k, t in enumerate(TARGETS):
                row[f"{t}_med%"] = float(np.median(rel[m, k]))
                row[f"{t}_p95%"] = float(np.percentile(rel[m, k], 95))
            row["mean_med%"] = float(np.median(rel[m], axis=0).mean())
        rows.append(row)
    return rows


def bootstrap(rel_x, rel_r, mask, n_boot=2000, seed=0):
    """Difference in the mean-over-targets median error, XGBoost minus ResNet (positive = ResNet better)."""
    ra, rb = rel_x[mask], rel_r[mask]
    n = len(ra)
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        s = rng.integers(0, n, n)
        diffs[i] = np.median(ra[s], axis=0).mean() - np.median(rb[s], axis=0).mean()
    return diffs.mean(), np.percentile(diffs, 5), np.percentile(diffs, 95), float((diffs > 0).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="pmos_off", choices=v2.CASES)
    ap.add_argument("--epochs", type=int, default=250)
    args = ap.parse_args()
    case = args.case

    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.float_format", "{:.4g}".format)

    df = pd.read_csv(f"data/{case}.csv")
    X_df = v2.engineer_features(df)
    X = X_df.values
    Y_lin = df[TARGETS].values
    Y_log = np.log10(np.maximum(np.abs(Y_lin), v2.FLOOR_CURRENT))
    idx = np.arange(len(df))

    (X_tr, X_tmp, Y_tr_log, Y_tmp_log, Y_tr_lin, Y_tmp_lin, idx_tr, idx_tmp) = train_test_split(
        X, Y_log, Y_lin, idx, test_size=0.30, random_state=v2.SEED)
    (X_va, _X_te, Y_va_log, _Y_te_log, Y_va_lin, _Y_te_lin, idx_va, _idx_te) = train_test_split(
        X_tmp, Y_tmp_log, Y_tmp_lin, idx_tmp, test_size=0.50, random_state=v2.SEED)

    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_va_s = scaler.transform(X_va)

    va = df.iloc[idx_va].reset_index(drop=True)
    masks = region_masks(case, va)
    tr_masks = region_masks(case, df.iloc[idx_tr].reset_index(drop=True))
    print(f"{case}: training samples in region A = {int(tr_masks['region A (full Vds at rail)'].sum())}, "
          f"region B = {int(tr_masks['region B (Vds near 0 at rail)'].sum())} of {len(idx_tr)}")

    print("Training XGBoost ...", flush=True)
    xgb = v2.MultiXGB([
        v2.XGBRegressor(n_estimators=450, max_depth=9, learning_rate=0.03, subsample=0.9,
                        random_state=v2.SEED, n_jobs=-1).fit(X_tr_s, Y_tr_log[:, i]) for i in range(4)])
    print(f"Training ResNet ({args.epochs} epochs) ...", flush=True)
    res = v2.train_resnet(X_tr_s, Y_tr_log, X_va_s, Y_va_log, epochs=args.epochs)

    rel_x = rel_err(Y_va_lin, xgb.predict(X_va_s))
    rel_r = rel_err(Y_va_lin, res.predict(X_va_s))

    print("\n=== VALIDATION split only: median and p95 relative error (%), per target ===")
    rows = table_rows("XGBoost", rel_x, masks) + table_rows("ResNet", rel_r, masks)
    out = pd.DataFrame(rows).sort_values(["subset", "model"], kind="stable")
    print(out.to_string(index=False))

    print("\n=== Bootstrap: mean-over-targets median error, XGBoost minus ResNet (positive = ResNet better) ===")
    for label, m in masks.items():
        if m.sum() < 10:
            print(f"{label:32s} n={int(m.sum()):4d}  too few samples for a bootstrap")
            continue
        mean, lo, hi, p = bootstrap(rel_x, rel_r, m)
        print(f"{label:32s} n={int(m.sum()):4d}  diff {mean:7.2f}  90% interval [{lo:7.2f}, {hi:7.2f}]  "
              f"ResNet better in {100 * p:5.1f}% of resamples")

    print("\nReading it: region medians rest on a few dozen samples, so treat a gap as real only if the")
    print("90% interval excludes 0. Both models are retrained here, so nothing in models/ is changed.")


if __name__ == "__main__":
    main()