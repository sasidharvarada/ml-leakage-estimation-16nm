"""Part A: Deliverables 4 & 5 (Operational-Region Aware Production Pipeline)
Selects models based on operational gate-region accuracy (Bootstrap-validated).
Saves ResNet for pmos_off, nmos_on, nmos_off, pmos_on.
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

from xgboost import XGBRegressor
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)

os.makedirs("models", exist_ok=True)
os.makedirs("results/plots", exist_ok=True)

CASES = ['nmos_on', 'nmos_off', 'pmos_on', 'pmos_off']
RAW_FEATURES = ['vdd', 'temp', 'w', 'vd', 'vs', 'vg', 'vb', 'vth0', 'toxe', 'ndep', 'u0', 'xj']
TARGETS = ['id', 'ig', 'is', 'ib']
FLOOR_CURRENT = 1e-18

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

def engineer_features(df):
    X = df[RAW_FEATURES].copy()
    X['vds'] = X['vd'] - X['vs']
    X['abs_vds'] = np.abs(X['vds'])
    X['vgs'] = X['vg'] - X['vs']
    X['vbs'] = X['vb'] - X['vs']
    X['vgd'] = X['vg'] - X['vd']
    X['overdrive'] = X['vgs'] - X['vth0']
    return X

def evaluate_metrics(y_true_lin, y_pred_lin):
    id_true_log = np.log10(np.abs(y_true_lin[:, 0]) + FLOOR_CURRENT)
    id_pred_log = np.log10(np.abs(y_pred_lin[:, 0]) + FLOOR_CURRENT)
    r2_id = r2_score(id_true_log, id_pred_log)

    denom = np.maximum(np.abs(y_true_lin[:, 0]), 1e-12)
    rel_errors = (np.abs(y_pred_lin[:, 0] - y_true_lin[:, 0]) / denom) * 100.0

    med_err = np.median(rel_errors)
    p95_err = np.percentile(rel_errors, 95)
    return r2_id, med_err, p95_err

def train_deep_neural_network(X_tr_s, Y_tr_log, X_va_s, Y_va_log, epochs=250, batch_size=128, lr=3e-3):
    train_loader = DataLoader(
        TensorDataset(torch.tensor(X_tr_s, dtype=torch.float32), torch.tensor(Y_tr_log, dtype=torch.float32)),
        batch_size=batch_size, shuffle=True
    )
    X_va_t = torch.tensor(X_va_s, dtype=torch.float32).to(DEVICE)
    Y_va_t = torch.tensor(Y_va_log, dtype=torch.float32).to(DEVICE)

    model = LeakageResNet(X_tr_s.shape[1], 4, hidden=128).to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    criterion = nn.SmoothL1Loss()

    best_loss = float('inf')
    best_weights = None

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
                best_weights = copy.deepcopy(model.state_dict())

    model.load_state_dict(best_weights)
    return PyTorchWrapper(model)

def main():
    comp_records = []
    chosen_records = []

    for case in CASES:
        print("\n" + "=" * 70)
        print(f" PIPELINE EXECUTION: {case.upper()}")
        print("=" * 70)

        df = pd.read_csv(f"data/{case}.csv")
        X_df = engineer_features(df)
        X = X_df.values
        Y_linear = df[TARGETS].values
        Y_log = np.log10(np.maximum(np.abs(Y_linear), FLOOR_CURRENT))

        # 70% Train, 15% Val, 15% Test
        X_tr, X_tmp, Y_tr_log, Y_tmp_log, Y_tr_lin, Y_tmp_lin = train_test_split(
            X, Y_log, Y_linear, test_size=0.30, random_state=SEED
        )
        X_va, X_te, Y_va_log, Y_te_log, Y_va_lin, Y_te_lin = train_test_split(
            X_tmp, Y_tmp_log, Y_tmp_lin, test_size=0.50, random_state=SEED
        )

        scaler = StandardScaler()
        X_tr_s = scaler.fit_transform(X_tr)
        X_va_s = scaler.transform(X_va)
        X_te_s = scaler.transform(X_te)

        models = {}

        # 1. Ridge Baseline
        print("[1/4] Training Model 1: Ridge (L2 Linear)...")
        r_models = [Ridge(alpha=10.0).fit(X_tr_s, Y_tr_log[:, i]) for i in range(4)]
        models['Ridge'] = MultiOutputModel(r_models)

        # 2. Random Forest
        print("[2/4] Training Model 2: Random Forest (Bagging)...")
        rf_models = [RandomForestRegressor(n_estimators=100, max_depth=14, random_state=SEED, n_jobs=-1).fit(X_tr_s, Y_tr_log[:, i]) for i in range(4)]
        models['RandomForest'] = MultiOutputModel(rf_models)

        # 3. XGBoost
        print("[3/4] Training Model 3: XGBoost (Gradient Boosting)...")
        xgb_models = [
            XGBRegressor(n_estimators=350, max_depth=8, learning_rate=0.04, subsample=0.9,
                         random_state=SEED, n_jobs=-1).fit(X_tr_s, Y_tr_log[:, i])
            for i in range(4)
        ]
        models['XGBoost'] = MultiXGB(xgb_models)

        # 4. PyTorch Deep ResNet (250 Epochs)
        print("[4/4] Training Model 4: PyTorch Deep ResNet (250 Epochs)...")
        models['PyTorch_ResNet'] = train_deep_neural_network(X_tr_s, Y_tr_log, X_va_s, Y_va_log, epochs=250, batch_size=128, lr=3e-3)

        # Validation Benchmark
        print("\n  --- VALIDATION BENCHMARK (DELIVERABLE 4) ---")
        for name, m in models.items():
            pred_lin = np.sign(Y_va_lin) * (10.0 ** m.predict(X_va_s))
            r2, med_err, p95_err = evaluate_metrics(Y_va_lin, pred_lin)
            print(f"  {name:16s} | R²: {r2:.4f} | Med Error: {med_err:.3f}% | 95th Error: {p95_err:.2f}%")
            comp_records.append({
                'case': case, 'model_type': name,
                'val_r2': r2, 'val_median_error_pct': med_err, 'val_p95_error_pct': p95_err
            })

        # Selection: ResNet is the operational winner (Script 11 Bootstrap proof)
        best_name = 'PyTorch_ResNet'
        best_model = models[best_name]

        # Evaluate Chosen Model on Unseen Test Set (Deliverable 5)
        te_lin = np.sign(Y_te_lin) * (10.0 ** best_model.predict(X_te_s))
        te_r2, te_med, te_p95 = evaluate_metrics(Y_te_lin, te_lin)

        print(f"\n  ★ CHOSEN OPERATIONAL WINNER FOR {case.upper()}: {best_name}")
        print(f"    Unseen Test Set -> R²: {te_r2:.4f} | Med Error: {te_med:.3f}% | 95th Error: {te_p95:.2f}%")

        chosen_records.append({
            'case': case, 'chosen_model': best_name,
            'test_r2': te_r2, 'test_median_error_pct': te_med, 'test_p95_error_pct': te_p95
        })

        # Save package with compression
        bundle = {
            'model': best_model, 'scaler': scaler,
            'feature_names': list(X_df.columns), 'model_type': best_name
        }
        joblib.dump(bundle, f"models/best_{case}.joblib", compress=3)
        print(f"    Saved package -> models/best_{case}.joblib")

        # Parity Plot
        plt.figure(figsize=(6.5, 6))
        sp_id, pr_id = np.abs(Y_te_lin[:, 0]), np.abs(te_lin[:, 0])
        plt.scatter(sp_id, pr_id, alpha=0.35, s=9, color='navy', label='Unseen Test Set')
        min_v = max(min(sp_id.min(), pr_id.min()), 1e-15)
        max_v = max(sp_id.max(), pr_id.max()) * 1.5
        plt.plot([min_v, max_v], [min_v, max_v], 'r--', lw=1.6, label='Ideal Parity (y=x)')
        plt.xscale('log'); plt.yscale('log')
        plt.xlim(min_v, max_v); plt.ylim(min_v, max_v)
        plt.xlabel('SPICE Reference |Id| (A) [Log Scale]')
        plt.ylabel('ML Predicted |Id| (A) [Log Scale]')
        plt.title(f'Deliverable 5: {case.upper()} ({best_name})\nTest R² = {te_r2:.4f}, Med Error = {te_med:.2f}%')
        plt.legend(frameon=True); plt.grid(True, which='both', ls='--', alpha=0.5)
        plt.tight_layout()
        plt.savefig(f"results/plots/parity_{case}.png", dpi=300)
        plt.close()

    pd.DataFrame(comp_records).to_csv("results/model_comparison_table.csv", index=False)
    pd.DataFrame(chosen_records).to_csv("results/chosen_models_test_summary.csv", index=False)
    print("\n Deliverables 4 & 5 finalized with Operational ResNet Models!")

if __name__ == "__main__":
    main()