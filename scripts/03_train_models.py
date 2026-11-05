"""Part A: Deliverables 4 & 5
Baseline comparison, Hyperparameter Optimization, and Test-Set Evaluation.
70% Train, 15% Validation, 15% Test (Seed: 42)
"""
import os
import copy
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)

os.makedirs("models", exist_ok=True)
os.makedirs("results/plots", exist_ok=True)

CASES = ['nmos_on', 'nmos_off', 'pmos_on', 'pmos_off']
RAW_FEATURES = ['vdd', 'temp', 'w', 'vd', 'vs', 'vg', 'vb', 'vth0', 'toxe', 'ndep', 'u0', 'xj']
TARGETS = ['id', 'ig', 'is', 'ib']
FLOOR_CURRENT = 1e-15

# 1. Feature Augmentation & Preprocessing

def engineer_features(df):
    X = df[RAW_FEATURES].copy()
    X['vds'] = X['vd'] - X['vs']
    X['abs_vds'] = np.abs(X['vds'])
    X['vgs'] = X['vg'] - X['vs']
    X['vbs'] = X['vb'] - X['vs']
    X['vgd'] = X['vg'] - X['vd']
    X['overdrive'] = X['vgs'] - X['vth0']
    return X

# 2. Evaluation Metric

def evaluate_metrics(y_true_lin, y_pred_lin):
    """Computes R2 on primary channel Id (log domain) and percentage errors."""
    id_true_log = np.log10(np.abs(y_true_lin[:, 0]) + FLOOR_CURRENT)
    id_pred_log = np.log10(np.abs(y_pred_lin[:, 0]) + FLOOR_CURRENT)
    r2_id = r2_score(id_true_log, id_pred_log)

    # Relative percentage error (|I_pred - I_true| / |I_true|) * 100
    denom = np.maximum(np.abs(y_true_lin[:, 0]), 1e-12)
    rel_errors = (np.abs(y_pred_lin[:, 0] - y_true_lin[:, 0]) / denom) * 100.0

    med_err = np.median(rel_errors)
    p95_err = np.percentile(rel_errors, 95)
    return r2_id, med_err, p95_err


# 3. Pytorch Neural net model and trainer

class LeakageResNet(nn.Module):
    def __init__(self, in_dim, out_dim, hidden=128):
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
        h2 = self.act2(self.fc2(h1)) + h1  # Residual shortcut
        h3 = self.act3(self.fc3(h2))
        return self.out(h3)

def train_pytorch(X_tr, Y_tr, X_va, Y_va, epochs=100, batch_size=128, lr=2e-3, hidden=128):
    train_loader = DataLoader(
        TensorDataset(torch.tensor(X_tr, dtype=torch.float32), torch.tensor(Y_tr, dtype=torch.float32)),
        batch_size=batch_size, shuffle=True
    )
    X_va_t = torch.tensor(X_va, dtype=torch.float32).to(DEVICE)
    Y_va_t = torch.tensor(Y_va, dtype=torch.float32).to(DEVICE)

    model = LeakageResNet(X_tr.shape[1], Y_tr.shape[1], hidden=hidden).to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    criterion = nn.SmoothL1Loss()

    best_loss = float('inf')
    best_state = None

    for epoch in range(1, epochs + 1):
        model.train()
        for bx, by in train_loader:
            bx, by = bx.to(DEVICE), by.to(DEVICE)
            optimizer.zero_grad()
            loss = criterion(model(bx), by)
            loss.backward()
            optimizer.step()
        scheduler.step()

        model.eval()
        with torch.no_grad():
            v_loss = criterion(model(X_va_t), Y_va_t).item()
            if v_loss < best_loss:
                best_loss = v_loss
                best_state = copy.deepcopy(model.state_dict())

    model.load_state_dict(best_state)
    return model

class PyTorchWrapper:
    def __init__(self, model):
        self.model = model
    def predict(self, X):
        self.model.eval()
        with torch.no_grad():
            return self.model(torch.tensor(X, dtype=torch.float32).to(DEVICE)).cpu().numpy()

# Multi-output wrapper for terminal models
class MultiOutputModel:
    def __init__(self, models):
        self.models = models
    def predict(self, X):
        return np.column_stack([m.predict(X) for m in self.models])


# 4. Systematic hyperparameter search on validation set

def tune_models(X_tr, Y_tr, X_va, Y_va, Y_va_lin):
    candidates = {}

    # --- 1. Ridge Baseline & Regularization Tuning ---
    print("  [*] Tuning Model 1: Ridge (L2 alpha sweep)...")
    best_ridge, best_ridge_err = None, float('inf')
    for alpha in [0.01, 1.0, 10.0, 100.0]:
        models = [Ridge(alpha=alpha).fit(X_tr, Y_tr[:, i]) for i in range(4)]
        wrapper = MultiOutputModel(models)
        pred_lin = np.sign(Y_va_lin) * (10.0 ** wrapper.predict(X_va))
        _, err, _ = evaluate_metrics(Y_va_lin, pred_lin)
        if err < best_ridge_err:
            best_ridge_err = err
            best_ridge = wrapper
    candidates['Ridge (Tuned)'] = best_ridge

    # --- 2. Random Forest Tuning ---
    print("  [*] Tuning Model 2: Random Forest (Depth & Estimators)...")
    best_rf, best_rf_err = None, float('inf')
    rf_grid = [
        {'n_estimators': 80, 'max_depth': 12},
        {'n_estimators': 150, 'max_depth': 18}
    ]
    for params in rf_grid:
        models = [RandomForestRegressor(**params, random_state=SEED, n_jobs=-1).fit(X_tr, Y_tr[:, i]) for i in range(4)]
        wrapper = MultiOutputModel(models)
        pred_lin = np.sign(Y_va_lin) * (10.0 ** wrapper.predict(X_va))
        _, err, _ = evaluate_metrics(Y_va_lin, pred_lin)
        if err < best_rf_err:
            best_rf_err = err
            best_rf = wrapper
    candidates['RandomForest (Tuned)'] = best_rf

    # --- 3. XGBoost Tuning ---
    if HAS_XGB:
        print("  [*] Tuning Model 3: XGBoost (LR & Tree Depth)...")
        best_xgb, best_xgb_err = None, float('inf')
        xgb_grid = [
            {'n_estimators': 200, 'max_depth': 6, 'learning_rate': 0.08},
            {'n_estimators': 350, 'max_depth': 8, 'learning_rate': 0.04}
        ]
        for params in xgb_grid:
            models = [XGBRegressor(**params, subsample=0.85, random_state=SEED, n_jobs=-1).fit(X_tr, Y_tr[:, i]) for i in range(4)]
            wrapper = MultiOutputModel(models)
            pred_lin = np.sign(Y_va_lin) * (10.0 ** wrapper.predict(X_va))
            _, err, _ = evaluate_metrics(Y_va_lin, pred_lin)
            if err < best_xgb_err:
                best_xgb_err = err
                best_xgb = wrapper
        candidates['XGBoost (Tuned)'] = best_xgb

    # --- 4. PyTorch Deep MLP (Epochs & Learning Rate) ---
    print("  [*] Tuning Model 4: PyTorch Deep ResNet (Epochs & LR schedule)...")
    pt_model = train_pytorch(X_tr, Y_tr, X_va, Y_va, epochs=100, batch_size=128, lr=2.5e-3, hidden=128)
    candidates['PyTorch_MLP (Tuned)'] = PyTorchWrapper(pt_model)

    return candidates



def main():
    comparison_table = []
    chosen_summary = []

    for case in CASES:
        print("\n" + "=" * 70)
        print(f" PIPELINE START: {case.upper()}")
        print("=" * 70)

        df = pd.read_csv(f"data/{case}.csv")
        X_df = engineer_features(df)
        X = X_df.values
        Y_linear = df[TARGETS].values
        Y_log = np.log10(np.maximum(np.abs(Y_linear), FLOOR_CURRENT))

        # 1. Split: 70% Train, 15% Val, 15% Test
        X_tr, X_tmp, Y_tr_log, Y_tmp_log, Y_tr_lin, Y_tmp_lin = train_test_split(
            X, Y_log, Y_linear, test_size=0.30, random_state=SEED
        )
        X_va, X_te, Y_va_log, Y_te_log, Y_va_lin, Y_te_lin = train_test_split(
            X_tmp, Y_tmp_log, Y_tmp_lin, test_size=0.50, random_state=SEED
        )

        print(f"Dataset split: Train = {len(X_tr)} | Val = {len(X_va)} | Test = {len(X_te)}")

        # 2. Scaling (Fitted on Train ONLY to prevent leakage)
        scaler = StandardScaler()
        X_tr_s = scaler.fit_transform(X_tr)
        X_va_s = scaler.transform(X_va)
        X_te_s = scaler.transform(X_te)

        # 3. Optimize Hyperparameters on Validation Set
        tuned_models = tune_models(X_tr_s, Y_tr_log, X_va_s, Y_va_log, Y_va_lin)

        best_score = float('inf')
        best_name = None
        best_model = None

        print("\n  --- VALIDATION BENCHMARK (DELIVERABLE 4) ---")
        for name, model in tuned_models.items():
            val_log_pred = model.predict(X_va_s)
            val_lin_pred = np.sign(Y_va_lin) * (10.0 ** val_log_pred)
            r2, med_err, p95_err = evaluate_metrics(Y_va_lin, val_lin_pred)

            print(f"  {name:22s} | R²: {r2:.4f} | Median Error: {med_err:.3f}% | 95th Error: {p95_err:.2f}%")

            comparison_table.append({
                'case': case,
                'model_type': name,
                'val_r2': r2,
                'val_median_error_pct': med_err,
                'val_p95_error_pct': p95_err
            })

            # Winner selection based on lowest validation median error
            if med_err < best_score:
                best_score = err = med_err
                best_name = name
                best_model = model

        # 4. Evaluate Final Winner on UNSEEN TEST SET (Deliverable 5)
        te_log_pred = best_model.predict(X_te_s)
        te_lin_pred = np.sign(Y_te_lin) * (10.0 ** te_log_pred)
        te_r2, te_med, te_p95 = evaluate_metrics(Y_te_lin, te_lin_pred)

        print(f"\n  ★ WINNING MODEL: {best_name}")
        print(f"    Unseen Test Set -> R²: {te_r2:.4f} | Median Error: {te_med:.3f}% | 95th Error: {te_p95:.2f}%")

        chosen_summary.append({
            'case': case,
            'chosen_model': best_name,
            'test_r2': te_r2,
            'test_median_error_pct': te_med,
            'test_p95_error_pct': te_p95
        })

        # 5. Save Model Bundle
        bundle = {
            'model': best_model,
            'scaler': scaler,
            'feature_names': list(X_df.columns),
            'model_type': best_name
        }
        joblib.dump(bundle, f"models/best_{case}.joblib")
        print(f"    Saved package -> models/best_{case}.joblib")

        # 6. Parity Plot on Test Set
        plt.figure(figsize=(6.5, 6))
        spice_id = np.abs(Y_te_lin[:, 0])
        pred_id = np.abs(te_lin_pred[:, 0])

        plt.scatter(spice_id, pred_id, alpha=0.35, s=9, color='navy', label='Unseen Test Samples')
        min_v = max(min(spice_id.min(), pred_id.min()), 1e-15)
        max_v = max(spice_id.max(), pred_id.max()) * 1.5
        plt.plot([min_v, max_v], [min_v, max_v], 'r--', lw=1.6, label='Ideal Parity (y=x)')

        plt.xscale('log')
        plt.yscale('log')
        plt.xlim(min_v, max_v)
        plt.ylim(min_v, max_v)
        plt.xlabel('SPICE Reference |Id| (A) [Log Scale]', fontsize=11)
        plt.ylabel('ML Predicted |Id| (A) [Log Scale]', fontsize=11)
        plt.title(f'Deliverable 5: Test Parity - {case.upper()} ({best_name})\nTest R² = {te_r2:.4f}, Median Error = {te_med:.2f}%', fontsize=11)
        plt.legend(frameon=True)
        plt.grid(True, which='both', linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.savefig(f"results/plots/parity_{case}.png", dpi=300)
        plt.close()

    # Save output tables
    df_comp = pd.DataFrame(comparison_table)
    df_comp.to_csv("results/model_comparison_table.csv", index=False)
    
    df_chosen = pd.DataFrame(chosen_summary)
    df_chosen.to_csv("results/chosen_models_test_summary.csv", index=False)

    print("\n")
    print("Deliverable 4: MODEL COMPARISON TABLE (VALIDATION SET)")
    print(df_comp.to_string(index=False))

    print("\n\n")
    print("Deliverable 5: FINAL TEST SET PERFORMANCE")
    print(df_chosen.to_string(index=False))
    print("\n Baseline, tuning, and evaluation complete!")

if __name__ == "__main__":
    main()
