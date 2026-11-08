#!/usr/bin/env python3
"""Per-target diagnostics of the saved Part A models on their own test split.

Why: the Part A report scores only |Id| and floors the error denominator at 1e-12 A, so it
cannot show where the models are weak. This script scores all four targets (Id, Ig, Is, Ib)
with an unfloored relative error (denominator floored at 1e-18 A only), broken down by
temperature, vth0 quartile and, for the OFF models, the bias region that gates actually use.

It only reads data/*.csv and models/*.joblib. Nothing is retrained or overwritten.

Run from the repo root:
    python3 scripts/09_model_diagnostics.py | tee results/model_diagnostics.txt
"""
import os
import sys
import importlib.util

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import joblib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def load_part_b():
    """Importing 04 registers the model classes on __main__ so joblib can unpickle the bundles."""
    spec = importlib.util.spec_from_file_location("part_b", os.path.join(HERE, "04_simulate_gates.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["part_b"] = mod
    spec.loader.exec_module(mod)
    main = sys.modules["__main__"]
    for name in ("LeakageResNet", "PyTorchWrapper", "MultiOutputModel", "MultiXGB"):
        if hasattr(mod, name):
            setattr(main, name, getattr(mod, name))
    return mod


load_part_b()

SEED = 42  # must match the Part A training script
CASES = ["nmos_on", "nmos_off", "pmos_on", "pmos_off"]
RAW_FEATURES = ["vdd", "temp", "w", "vd", "vs", "vg", "vb", "vth0", "toxe", "ndep", "u0", "xj"]
TARGETS = ["id", "ig", "is", "ib"]
FLOOR = 1e-18


def engineer_features(df):
    X = df[RAW_FEATURES].copy()
    X["vds"] = X["vd"] - X["vs"]
    X["abs_vds"] = np.abs(X["vds"])
    X["vgs"] = X["vg"] - X["vs"]
    X["vbs"] = X["vb"] - X["vs"]
    X["vgd"] = X["vg"] - X["vd"]
    X["overdrive"] = X["vgs"] - X["vth0"]
    return X


def gate_region(case, df):
    """Bias region the gates actually use for the OFF devices (rail-to-rail drain/source)."""
    if case == "pmos_off":
        return (df.vs >= 0.8 * df.vdd) & (df.vd <= 0.2 * df.vdd)
    if case == "nmos_off":
        return (df.vd >= 0.8 * df.vdd) & (df.vs <= 0.2 * df.vdd)
    return None


def summarize(label, rel, true_abs, mask):
    row = {"subset": label, "n": int(mask.sum())}
    if mask.sum() == 0:
        return row
    row["id_true_med_A"] = float(np.median(true_abs[mask, 0]))
    for k, t in enumerate(TARGETS):
        row[f"{t}_med%"] = float(np.median(rel[mask, k]))
        row[f"{t}_p95%"] = float(np.percentile(rel[mask, k], 95))
    return row


def main():
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.float_format", "{:.4g}".format)

    for case in CASES:
        df = pd.read_csv(f"data/{case}.csv")
        bundle = joblib.load(f"models/best_{case}.joblib")
        X_df = engineer_features(df)

        idx = np.arange(len(df))
        idx_tr, idx_tmp = train_test_split(idx, test_size=0.30, random_state=SEED)
        _, idx_te = train_test_split(idx_tmp, test_size=0.50, random_state=SEED)

        X_te = bundle["scaler"].transform(X_df.iloc[idx_te][bundle["feature_names"]].values)
        pred_abs = 10.0 ** bundle["model"].predict(X_te)
        te = df.iloc[idx_te].reset_index(drop=True)
        true_abs = np.abs(te[TARGETS].values)
        rel = np.abs(pred_abs - true_abs) / np.maximum(true_abs, FLOOR) * 100.0

        rows = [summarize("all test", rel, true_abs, np.ones(len(te), bool))]
        tbin = pd.cut(te.temp, [-40, 0, 40, 80, 125], include_lowest=True)
        for b in tbin.cat.categories:
            rows.append(summarize(f"T {b}", rel, true_abs, (tbin == b).values))
        vq = pd.qcut(df.vth0, 4, labels=False).iloc[idx_te].reset_index(drop=True)
        for q in range(4):
            rows.append(summarize(f"vth0 quartile {q + 1}", rel, true_abs, (vq == q).values))

        reg_all = gate_region(case, df)
        if reg_all is not None:
            reg_te = gate_region(case, te).values
            rows.append(summarize("GATE REGION", rel, true_abs, reg_te))
            rows.append(summarize("outside gate region", rel, true_abs, ~reg_te))
            n_train = int(reg_all.iloc[idx_tr].sum())
            print(f"\n{case}: gate-region samples in train = {n_train} of {len(idx_tr)}, "
                  f"in test = {int(reg_te.sum())} of {len(idx_te)}")
        else:
            print(f"\n{case}:")

        print(pd.DataFrame(rows).to_string(index=False))

    print("\nErrors are relative, in percent: |10^pred - |true|| / max(|true|, 1e-18).")
    print("Compare 'GATE REGION' with 'outside gate region' on the OFF models: a large gap means")
    print("the training data under-covers the corner the gates use.")


if __name__ == "__main__":
    main()