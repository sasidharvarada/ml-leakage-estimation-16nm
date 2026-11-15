"""Shared helpers for the testing/ scripts (run them from the repo root)."""
import importlib
import os
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import config as C                                   # noqa: E402
from leak_model import TARGETS, TransistorModel, to_log  # noqa: E402

CASES = list(C.CASES)
RAIL_HOLDOUT = 0.15            # same as scripts/03_train_models.py
OUT = os.path.join("testing", "results")
NOISE_FLOOR = 1e-15            # currents with median |I| below 1 fA are at the simulator noise floor


def variants(requested="both"):
    """[(name, model_dir)] for the trained model sets that exist."""
    all_v = [("rail", "saved_models"), ("no_rail", os.path.join("saved_models", "no_rail"))]
    want = [v for v in all_v if requested in ("both", v[0])]
    have = [v for v in want if all(os.path.exists(os.path.join(v[1], f"{c}.joblib")) for c in CASES)]
    for v in want:
        if v not in have:
            print(f"[!] variant '{v[0]}': no models in {v[1]}/ (train them first), skipped")
    return have


def splits(case, use_rail):
    """Exactly the splits used by scripts/03_train_models.py (seed C.SEED)."""
    df = pd.read_csv(f"data/{case}.csv")
    train, rest = train_test_split(df, test_size=0.30, random_state=C.SEED)
    val, test = train_test_split(rest, test_size=0.50, random_state=C.SEED)
    out = {"train": train, "validation": val, "test": test}
    rail_path = f"data/rail/{case}.csv"
    if use_rail and os.path.exists(rail_path):
        rail = pd.read_csv(rail_path)
        r_train, r_test = train_test_split(rail, test_size=RAIL_HOLDOUT, random_state=C.SEED)
        out["train_rail"] = r_train
        out["test_rail"] = r_test
    return out


def rel_err(true, pred):
    true, pred = np.asarray(true, float), np.asarray(pred, float)
    m = true != 0
    return 100.0 * np.abs(pred[m] - true[m]) / np.abs(true[m])


def scores(true, pred):
    """Loss = MSE of log10|I| (what the regressors are trained on), plus the error metrics."""
    lt, lp = to_log(true), to_log(pred)
    e = rel_err(true, pred)
    ss = np.sum((lt - lt.mean()) ** 2)
    se = np.sort((lt - lp) ** 2)
    keep = max(1, int(0.99 * len(se)))
    return {"loss_mse_log10": float(np.mean(se)),
            # same loss without the worst 1 % of points (currents passing through zero, |I| -> 0,
            # can be many decades off in log space and dominate the plain mean)
            "loss_mse_log10_trim1": float(np.mean(se[:keep])),
            "mae_log10": float(np.mean(np.abs(lt - lp))),
            "r2_log": float(1 - np.sum((lt - lp) ** 2) / ss) if ss > 0 else float("nan"),
            "median_err_pct": float(np.median(e)), "p95_err_pct": float(np.percentile(e, 95)),
            "sign_acc": float(np.mean(np.sign(true) == np.sign(pred))),
            "median_abs_I_A": float(np.median(np.abs(true)))}


def load_script(name):
    """Import a scripts/ module whose name starts with a digit, e.g. 01_generate_transistor_data."""
    return importlib.import_module(name)


def save(df, *parts):
    path = os.path.join(OUT, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False, float_format="%.5g")
    return path


def md_table(df, floatfmt="{:.4g}"):
    """DataFrame -> GitHub markdown table (no extra dependency)."""
    cols = list(df.columns)
    def f(v):
        return floatfmt.format(v) if isinstance(v, (float, np.floating)) else str(v)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(f(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)
