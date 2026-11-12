#!/usr/bin/env python3
"""Part A (v2): retrain the four transistor models with validation-based selection.

What changed against the v1 training script
  1. Metrics cover all four targets (Id, Ig, Is, Ib), not only Id. Both the prediction and the
     SPICE value are clipped at the 1e-18 A floor the models are trained on, so currents below
     the floor count as matching (the v1 metric floored the denominator at 1e-12 A, which hid
     errors on tiny currents, and it used the true sign).
  2. The best model per case is picked on the validation set, not hard-coded to XGBoost.
     Selection score = mean over the four targets of the median relative error.
  3. ResNet targets are standardised during training and the scaling is folded back into the
     last layer afterwards, so the saved model still outputs log10|I| and stays compatible with
     04_simulate_gates.py, 05_test_circuit.py and the diagnostics scripts. Default 250 epochs.

Unchanged: features, 70/15/15 split and seed, Ridge / Random Forest / XGBoost settings, the
ResNet architecture, and the saved bundle format.

Usage from the repo root:
    python3 scripts/03_train_models_v2.py
    python3 scripts/03_train_models_v2.py --cases pmos_off --epochs 400

The first run backs up the existing models/*.joblib to models/v1_backup/ and the three result
CSVs to results/v1_backup/.
"""
import argparse
import copy
import os
import shutil

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

from xgboost import XGBRegressor
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SEED = 42

CASES = ["nmos_on", "nmos_off", "pmos_on", "pmos_off"]
RAW_FEATURES = ["vdd", "temp", "w", "vd", "vs", "vg", "vb", "vth0", "toxe", "ndep", "u0", "xj"]
TARGETS = ["id", "ig", "is", "ib"]
FLOOR_CURRENT = 1e-18


# ---------------------------------------------------------------------------
# Model classes: identical to v1 so that the saved bundles load in the other scripts.
# ---------------------------------------------------------------------------
class LeakageResNet(nn.Module):
    def __init__(self, in_dim=18, out_dim=4, hidden=128):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, hidden)
        self.act1 = nn.SiLU()
        self.fc2 = nn.Linear(hidden, hidden)
        self.act2 = nn.SiLU()
        self.fc3 = nn.Linear(hidden, 64)
        self.act3 = nn.SiLU()
        self.out = nn.Linear(64, out_dim)

    def forward(self, x):
        h1 = self.act1(self.fc1(x))
        h2 = self.act2(self.fc2(h1)) + h1
        h3 = self.act3(self.fc3(h2))
        return self.out(h3)


class PyTorchWrapper:
    def __init__(self, model):
        self.model = model

    def predict(self, X):
        self.model.eval()
        with torch.no_grad():
            return self.model(torch.tensor(X, dtype=torch.float32).to(DEVICE)).cpu().numpy()


class MultiOutputModel:
    def __init__(self, models):
        self.models = models

    def predict(self, X):
        return np.column_stack([m.predict(X) for m in self.models])


class MultiXGB:
    def __init__(self, models):
        self.models = models

    def predict(self, X):
        return np.column_stack([m.predict(X) for m in self.models])


# ---------------------------------------------------------------------------
# Features and metrics
# ---------------------------------------------------------------------------
def engineer_features(df):
    X = df[RAW_FEATURES].copy()
    X["vds"] = X["vd"] - X["vs"]
    X["abs_vds"] = np.abs(X["vds"])
    X["vgs"] = X["vg"] - X["vs"]
    X["vbs"] = X["vb"] - X["vs"]
    X["vgd"] = X["vg"] - X["vd"]
    X["overdrive"] = X["vgs"] - X["vth0"]
    return X


def target_metrics(true_lin, pred_log):
    """Per-target (R2 in log space, median rel. error %, p95 rel. error %).

    Both sides are clipped at FLOOR_CURRENT, the same floor the models are trained on.
    """
    true_c = np.maximum(np.abs(true_lin), FLOOR_CURRENT)
    pred_c = np.maximum(10.0 ** np.clip(pred_log, -30.0, 3.0), FLOOR_CURRENT)
    rel = np.abs(pred_c - true_c) / true_c * 100.0
    out = {}
    for k, t in enumerate(TARGETS):
        out[t] = (r2_score(np.log10(true_c[:, k]), np.log10(pred_c[:, k])),
                  float(np.median(rel[:, k])), float(np.percentile(rel[:, k], 95)))
    return out


def summarize(per_target):
    """Mean over the four targets of (R2, median error, p95 error)."""
    arr = np.array([per_target[t] for t in TARGETS])
    return float(arr[:, 0].mean()), float(arr[:, 1].mean()), float(arr[:, 2].mean())


# ---------------------------------------------------------------------------
# ResNet training with standardised targets folded back into the output layer
# ---------------------------------------------------------------------------
def train_resnet(X_tr_s, Y_tr_log, X_va_s, Y_va_log, epochs=250, batch_size=128, lr=2.5e-3):
    torch.manual_seed(SEED)
    mu = Y_tr_log.mean(axis=0)
    sd = Y_tr_log.std(axis=0) + 1e-8
    Y_tr_z = (Y_tr_log - mu) / sd
    Y_va_z = (Y_va_log - mu) / sd

    train_loader = DataLoader(
        TensorDataset(torch.tensor(X_tr_s, dtype=torch.float32), torch.tensor(Y_tr_z, dtype=torch.float32)),
        batch_size=batch_size, shuffle=True)
    X_va_t = torch.tensor(X_va_s, dtype=torch.float32).to(DEVICE)
    Y_va_t = torch.tensor(Y_va_z, dtype=torch.float32).to(DEVICE)

    model = LeakageResNet(X_tr_s.shape[1], 4, hidden=128).to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    criterion = nn.SmoothL1Loss()

    best_loss, best_weights = float("inf"), None
    for _ in range(epochs):
        model.train()
        for bx, by in train_loader:
            bx, by = bx.to(DEVICE), by.to(DEVICE)
            optimizer.zero_grad()
            criterion(model(bx), by).backward()
            optimizer.step()
        scheduler.step()
        model.eval()
        with torch.no_grad():
            v_loss = criterion(model(X_va_t), Y_va_t).item()
        if v_loss < best_loss:
            best_loss = v_loss
            best_weights = copy.deepcopy(model.state_dict())
    model.load_state_dict(best_weights)

    # y = sd * z + mu, folded into the last Linear layer so the model outputs log10|I| directly.
    with torch.no_grad():
        sd_t = torch.tensor(sd, dtype=torch.float32, device=DEVICE)
        mu_t = torch.tensor(mu, dtype=torch.float32, device=DEVICE)
        model.out.weight.mul_(sd_t[:, None])
        model.out.bias.mul_(sd_t).add_(mu_t)
    return PyTorchWrapper(model)


# ---------------------------------------------------------------------------
# Housekeeping
# ---------------------------------------------------------------------------
def backup_once(path, backup_dir):
    if os.path.exists(path):
        os.makedirs(backup_dir, exist_ok=True)
        dest = os.path.join(backup_dir, os.path.basename(path))
        if not os.path.exists(dest):
            shutil.copy2(path, dest)


def parity_plot(case, model_name, true_lin, pred_log, test_summary):
    true_c = np.maximum(np.abs(true_lin), FLOOR_CURRENT)
    pred_c = np.maximum(10.0 ** np.clip(pred_log, -30.0, 3.0), FLOOR_CURRENT)
    fig, axes = plt.subplots(2, 2, figsize=(10, 9))
    for k, (ax, t) in enumerate(zip(axes.ravel(), TARGETS)):
        lo = max(min(true_c[:, k].min(), pred_c[:, k].min()), 1e-19)
        hi = max(true_c[:, k].max(), pred_c[:, k].max()) * 1.5
        ax.scatter(true_c[:, k], pred_c[:, k], s=6, alpha=0.35, color="navy", label="Unseen test set")
        ax.plot([lo, hi], [lo, hi], "r--", lw=1.4, label="y = x")
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
        r2, med, _ = test_summary[t]
        ax.set_title(f"|{t.upper()}|  R2={r2:.4f}, median err={med:.2f}%", fontsize=10)
        ax.set_xlabel("SPICE (A)"); ax.set_ylabel("ML (A)")
        ax.grid(True, which="both", ls="--", alpha=0.5)
        if k == 0:
            ax.legend(frameon=True)
    fig.suptitle(f"{case.upper()} ({model_name}), test set", fontsize=12)
    fig.tight_layout()
    fig.savefig(f"results/plots/parity_{case}.png", dpi=300)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", nargs="+", default=CASES, choices=CASES)
    ap.add_argument("--epochs", type=int, default=250)
    args = ap.parse_args()

    os.makedirs("models", exist_ok=True)
    os.makedirs("results/plots", exist_ok=True)
    # The by-target table only exists after a v2 run; partial reruns merge into v2 tables only.
    prev_v2 = os.path.exists("results/model_comparison_by_target.csv")
    for case in args.cases:
        backup_once(f"models/best_{case}.joblib", "models/v1_backup")
    for csv in ("model_comparison_table.csv", "chosen_models_test_summary.csv"):
        backup_once(f"results/{csv}", "results/v1_backup")

    summary_rows, by_target_rows, chosen_rows = [], [], []

    for case in args.cases:
        print("\n" + "=" * 70)
        print(f" {case.upper()}")
        print("=" * 70)

        df = pd.read_csv(f"data/{case}.csv")
        X_df = engineer_features(df)
        X = X_df.values
        Y_lin = df[TARGETS].values
        Y_log = np.log10(np.maximum(np.abs(Y_lin), FLOOR_CURRENT))

        X_tr, X_tmp, Y_tr_log, Y_tmp_log, Y_tr_lin, Y_tmp_lin = train_test_split(
            X, Y_log, Y_lin, test_size=0.30, random_state=SEED)
        X_va, X_te, Y_va_log, Y_te_log, Y_va_lin, Y_te_lin = train_test_split(
            X_tmp, Y_tmp_log, Y_tmp_lin, test_size=0.50, random_state=SEED)

        scaler = StandardScaler()
        X_tr_s = scaler.fit_transform(X_tr)
        X_va_s = scaler.transform(X_va)
        X_te_s = scaler.transform(X_te)

        models = {}
        print("[1/4] Ridge ...")
        models["Ridge"] = MultiOutputModel([Ridge(alpha=10.0).fit(X_tr_s, Y_tr_log[:, i]) for i in range(4)])
        print("[2/4] Random Forest ...")
        models["RandomForest"] = MultiOutputModel([
            RandomForestRegressor(n_estimators=100, max_depth=14, random_state=SEED, n_jobs=-1)
            .fit(X_tr_s, Y_tr_log[:, i]) for i in range(4)])
        print("[3/4] XGBoost ...")
        models["XGBoost"] = MultiXGB([
            XGBRegressor(n_estimators=450, max_depth=9, learning_rate=0.03, subsample=0.9,
                         random_state=SEED, n_jobs=-1).fit(X_tr_s, Y_tr_log[:, i]) for i in range(4)])
        print(f"[4/4] PyTorch ResNet ({args.epochs} epochs) ...")
        models["PyTorch_ResNet"] = train_resnet(X_tr_s, Y_tr_log, X_va_s, Y_va_log, epochs=args.epochs)

        print("\n  --- VALIDATION (mean over Id, Ig, Is, Ib) ---")
        scores = {}
        for name, m in models.items():
            per_t = target_metrics(Y_va_lin, m.predict(X_va_s))
            r2, med, p95 = summarize(per_t)
            scores[name] = med
            print(f"  {name:15s} | R2 {r2:.4f} | median err {med:7.3f}% | p95 err {p95:8.2f}%")
            summary_rows.append({"case": case, "model_type": name, "val_r2": r2,
                                 "val_median_error_pct": med, "val_p95_error_pct": p95})
            for t in TARGETS:
                by_target_rows.append({"case": case, "model_type": name, "target": t,
                                       "val_r2": per_t[t][0], "val_median_error_pct": per_t[t][1],
                                       "val_p95_error_pct": per_t[t][2]})

        best_name = min(scores, key=scores.get)
        best_model = models[best_name]
        te_pred = best_model.predict(X_te_s)
        te_per_t = target_metrics(Y_te_lin, te_pred)
        te_r2, te_med, te_p95 = summarize(te_per_t)

        print(f"\n  CHOSEN: {best_name} (selected on validation)")
        print(f"  TEST    | mean R2 {te_r2:.4f} | mean median err {te_med:.3f}% | mean p95 err {te_p95:.2f}%")
        for t in TARGETS:
            print(f"    {t}: R2 {te_per_t[t][0]:.4f} | median {te_per_t[t][1]:.3f}% | p95 {te_per_t[t][2]:.2f}%")

        row = {"case": case, "chosen_model": best_name, "test_r2": te_r2,
               "test_median_error_pct": te_med, "test_p95_error_pct": te_p95}
        for t in TARGETS:
            row[f"test_{t}_median_error_pct"] = te_per_t[t][1]
            row[f"test_{t}_p95_error_pct"] = te_per_t[t][2]
        chosen_rows.append(row)

        joblib.dump({"model": best_model, "scaler": scaler, "feature_names": list(X_df.columns),
                     "model_type": best_name}, f"models/best_{case}.joblib", compress=3)
        print(f"  saved models/best_{case}.joblib")
        parity_plot(case, best_name, Y_te_lin, te_pred, te_per_t)

    def write_table(path, rows):
        new = pd.DataFrame(rows)
        if prev_v2 and os.path.exists(path):
            old = pd.read_csv(path)
            old = old[~old["case"].isin(new["case"].unique())]
            new = pd.concat([old, new], ignore_index=True)
        new["case"] = pd.Categorical(new["case"], CASES, ordered=True)
        new.sort_values("case", kind="stable").to_csv(path, index=False)

    write_table("results/model_comparison_table.csv", summary_rows)
    write_table("results/model_comparison_by_target.csv", by_target_rows)
    write_table("results/chosen_models_test_summary.csv", chosen_rows)
    print("\nDone. Next: rerun 04_simulate_gates.py, delete results/part_c/gate_ml_cache.csv and "
          "results/part_c/gate_cases, then rerun 05_test_circuit.py.")


if __name__ == "__main__":
    main()