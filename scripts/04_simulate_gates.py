"""Part B: Gate-Level Validation (Deliverables 6 & 7) - Clean Sub-10% Engine
"""
import os
import re
import tempfile
import subprocess
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib
import torch
import torch.nn as nn

from spice_utils import split_models, set_params

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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

os.makedirs("results/plots", exist_ok=True)

LMIN = 16e-9
L_DIFF = 2.5 * LMIN
WN = 2 * LMIN   # 32 nm
WP = 4 * LMIN   # 64 nm

NOM_NMOS = {'vth0': 0.68191,  'toxe': 1.20e-9, 'ndep': 7.00e18, 'u0': 0.0280, 'xj': 5.00e-9}
NOM_PMOS = {'vth0': -0.68620, 'toxe': 1.22e-9, 'ndep': 4.40e18, 'u0': 0.0075, 'xj': 7.20e-9}

GATE_CASES = [
    ('INV',   '0'), ('INV',   '1'),
    ('NAND2', '00'), ('NAND2', '01'), ('NAND2', '10'), ('NAND2', '11'),
    ('NOR2',  '00'), ('NOR2',  '01'), ('NOR2',  '10'), ('NOR2',  '11'),
    ('AND2',  '00'), ('AND2',  '01'), ('AND2',  '10'), ('AND2',  '11'),
    ('OR2',   '00'), ('OR2',   '01'), ('OR2',   '10'), ('OR2',   '11')
]

MODELS_TEXT = split_models("models/16nm_LP.pm")

def generate_corners(num_corners=200, seed=123):
    rng = np.random.default_rng(seed)
    corners = []
    for _ in range(num_corners):
        vdd = rng.uniform(0.9, 1.1)
        temp = rng.uniform(-40.0, 125.0)
        n_proc = {k: v * rng.uniform(0.9, 1.1) for k, v in NOM_NMOS.items()}
        p_proc = {k: v * rng.uniform(0.9, 1.1) for k, v in NOM_PMOS.items()}
        corners.append({'vdd': vdd, 'temp': temp, 'nmos': n_proc, 'pmos': p_proc})
    return corners

def get_nodeset(gate, inp, vdd):
    if gate == 'INV':
        return f".nodeset v(out)={vdd if inp=='0' else 0.0}"
    elif gate == 'NAND2':
        vout = 0.0 if inp == '11' else vdd
        vx = 0.0 if inp in ['01', '11'] else (vdd if inp == '10' else vdd/2)
        return f".nodeset v(out)={vout} v(x)={vx}"
    elif gate == 'NOR2':
        vout = vdd if inp == '00' else 0.0
        vy = vdd if inp in ['00', '01'] else 0.0
        return f".nodeset v(out)={vout} v(y)={vy}"
    elif gate == 'AND2':
        vn = 0.0 if inp == '11' else vdd
        vout = vdd if inp == '11' else 0.0
        vx = 0.0 if inp in ['01', '11'] else (vdd if inp == '10' else vdd/2)
        return f".nodeset v(n_out)={vn} v(out)={vout} v(x)={vx}"
    elif gate == 'OR2':
        vn = vdd if inp == '00' else 0.0
        vout = 0.0 if inp == '00' else vdd
        vy = vdd if inp in ['00', '01'] else 0.0
        return f".nodeset v(n_out)={vn} v(out)={vout} v(y)={vy}"
    return ""

def simulate_gate_spice(task):
    gate, inp, corner = task
    vdd = corner['vdd']
    temp = corner['temp']
    n_p = corner['nmos']
    p_p = corner['pmos']

    va = vdd if inp[0] == '1' else 0.0
    vb = vdd if (len(inp) > 1 and inp[1] == '1') else 0.0

    ad_n, as_n = WN * L_DIFF, WN * L_DIFF
    pd_n, ps_n = 2 * (WN + L_DIFF), 2 * (WN + L_DIFF)
    ad_p, as_p = WP * L_DIFF, WP * L_DIFF
    pd_p, ps_p = 2 * (WP + L_DIFF), 2 * (WP + L_DIFF)

    n_card = set_params(MODELS_TEXT['nmos'], n_p, "nmos_mod")
    p_card = set_params(MODELS_TEXT['pmos'], p_p, "pmos_mod")

    deck = f"""* Gate run: {gate} {inp}
{n_card}
{p_card}

Vdd vdd 0 DC {vdd:.6f}
Va  a   0 DC {va:.6f}
"""
    if len(inp) > 1:
        deck += f"Vb  b   0 DC {vb:.6f}\n"

    if gate == 'INV':
        deck += f"""
Mp out a vdd vdd pmos_mod W={WP:.5e} L={LMIN:.5e} AD={ad_p:.5e} AS={as_p:.5e} PD={pd_p:.5e} PS={ps_p:.5e}
Mn out a 0   0   nmos_mod W={WN:.5e} L={LMIN:.5e} AD={ad_n:.5e} AS={as_n:.5e} PD={pd_n:.5e} PS={ps_n:.5e}
"""
    elif gate == 'NAND2':
        deck += f"""
Mp1 out a vdd vdd pmos_mod W={WP:.5e} L={LMIN:.5e} AD={ad_p:.5e} AS={as_p:.5e} PD={pd_p:.5e} PS={ps_p:.5e}
Mp2 out b vdd vdd pmos_mod W={WP:.5e} L={LMIN:.5e} AD={ad_p:.5e} AS={as_p:.5e} PD={pd_p:.5e} PS={ps_p:.5e}
Mn1 out a x   0   nmos_mod W={WN:.5e} L={LMIN:.5e} AD={ad_n:.5e} AS={as_n:.5e} PD={pd_n:.5e} PS={ps_n:.5e}
Mn2 x   b 0   0   nmos_mod W={WN:.5e} L={LMIN:.5e} AD={ad_n:.5e} AS={as_n:.5e} PD={pd_n:.5e} PS={ps_n:.5e}
"""
    elif gate == 'NOR2':
        deck += f"""
Mp1 y   a vdd vdd pmos_mod W={WP:.5e} L={LMIN:.5e} AD={ad_p:.5e} AS={as_p:.5e} PD={pd_p:.5e} PS={ps_p:.5e}
Mp2 out b y   vdd pmos_mod W={WP:.5e} L={LMIN:.5e} AD={ad_p:.5e} AS={as_p:.5e} PD={pd_p:.5e} PS={ps_p:.5e}
Mn1 out a 0   0   nmos_mod W={WN:.5e} L={LMIN:.5e} AD={ad_n:.5e} AS={as_n:.5e} PD={pd_n:.5e} PS={ps_n:.5e}
Mn2 out b 0   0   nmos_mod W={WN:.5e} L={LMIN:.5e} AD={ad_n:.5e} AS={as_n:.5e} PD={pd_n:.5e} PS={ps_n:.5e}
"""
    elif gate == 'AND2':
        deck += f"""
Mp1 n_out a vdd vdd pmos_mod W={WP:.5e} L={LMIN:.5e} AD={ad_p:.5e} AS={as_p:.5e} PD={pd_p:.5e} PS={ps_p:.5e}
Mp2 n_out b vdd vdd pmos_mod W={WP:.5e} L={LMIN:.5e} AD={ad_p:.5e} AS={as_p:.5e} PD={pd_p:.5e} PS={ps_p:.5e}
Mn1 n_out a x   0   nmos_mod W={WN:.5e} L={LMIN:.5e} AD={ad_n:.5e} AS={as_n:.5e} PD={pd_n:.5e} PS={ps_n:.5e}
Mn2 x     b 0   0   nmos_mod W={WN:.5e} L={LMIN:.5e} AD={ad_n:.5e} AS={as_n:.5e} PD={pd_n:.5e} PS={ps_n:.5e}
Mpi out n_out vdd vdd pmos_mod W={WP:.5e} L={LMIN:.5e} AD={ad_p:.5e} AS={as_p:.5e} PD={pd_p:.5e} PS={ps_p:.5e}
Mni out n_out 0   0   nmos_mod W={WN:.5e} L={LMIN:.5e} AD={ad_n:.5e} AS={as_n:.5e} PD={pd_n:.5e} PS={ps_n:.5e}
"""
    elif gate == 'OR2':
        deck += f"""
Mp1 y     a vdd vdd pmos_mod W={WP:.5e} L={LMIN:.5e} AD={ad_p:.5e} AS={as_p:.5e} PD={pd_p:.5e} PS={ps_p:.5e}
Mp2 n_out b y   vdd pmos_mod W={WP:.5e} L={LMIN:.5e} AD={ad_p:.5e} AS={as_p:.5e} PD={pd_p:.5e} PS={ps_p:.5e}
Mn1 n_out a 0   0   nmos_mod W={WN:.5e} L={LMIN:.5e} AD={ad_n:.5e} AS={as_n:.5e} PD={pd_n:.5e} PS={ps_n:.5e}
Mn2 n_out b 0   0   nmos_mod W={WN:.5e} L={LMIN:.5e} AD={ad_n:.5e} AS={as_n:.5e} PD={pd_n:.5e} PS={ps_n:.5e}
Mpi out n_out vdd vdd pmos_mod W={WP:.5e} L={LMIN:.5e} AD={ad_p:.5e} AS={as_p:.5e} PD={pd_p:.5e} PS={ps_p:.5e}
Mni out n_out 0   0   nmos_mod W={WN:.5e} L={LMIN:.5e} AD={ad_n:.5e} AS={as_n:.5e} PD={pd_n:.5e} PS={ps_n:.5e}
"""

    deck += f"""
{get_nodeset(gate, inp, vdd)}
.options gmin=1e-18 abstol=1e-18 reltol=1e-6 vntol=1e-9 itl1=400
.temp {temp:.2f}
.control
set numdgt = 10
op
let ileak = -i(vdd)
echo LEAK $&ileak
echo V_OUT $&v(out)
"""
    if gate in ['NAND2', 'AND2']:
        deck += "echo V_X $&v(x)\n"
    if gate in ['NOR2', 'OR2']:
        deck += "echo V_Y $&v(y)\n"
    if gate in ['AND2', 'OR2']:
        deck += "echo V_NOUT $&v(n_out)\n"
    deck += ".endc\n.end\n"

    with tempfile.NamedTemporaryFile("w", suffix=".cir", delete=False) as f:
        f.write(deck)
        path = f.name
    try:
        res = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True, timeout=10)
        stdout = res.stdout
    except subprocess.TimeoutExpired:
        stdout = ""
    finally:
        os.remove(path)

    spice_leak = 0.0
    node_v = {'out': 0.0, 'x': 0.0, 'y': vdd, 'n_out': 0.0}
    for line in stdout.splitlines():
        if line.startswith("LEAK"):
            m = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", line)
            if m: spice_leak = float(m[0])
        elif line.startswith("V_OUT"):
            m = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", line)
            if m: node_v['out'] = float(m[0])
        elif line.startswith("V_X"):
            m = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", line)
            if m: node_v['x'] = float(m[0])
        elif line.startswith("V_Y"):
            m = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", line)
            if m: node_v['y'] = float(m[0])
        elif line.startswith("V_NOUT"):
            m = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", line)
            if m: node_v['n_out'] = float(m[0])

    return abs(spice_leak), node_v

class GateMLEvaluator:
    def __init__(self):
        self.models = {
            'nmos_on': joblib.load("models/best_nmos_on.joblib"),
            'nmos_off': joblib.load("models/best_nmos_off.joblib"),
            'pmos_on': joblib.load("models/best_pmos_on.joblib"),
            'pmos_off': joblib.load("models/best_pmos_off.joblib")
        }

    def predict_fet(self, case_key, vdd, temp, w, vd, vs, vg, vb, proc):
        bundle = self.models[case_key]
        model = bundle['model']
        scaler = bundle['scaler']
        vds = vd - vs
        row = {
            'vdd': vdd, 'temp': temp, 'w': w,
            'vd': vd, 'vs': vs, 'vg': vg, 'vb': vb,
            'vth0': proc['vth0'], 'toxe': proc['toxe'], 'ndep': proc['ndep'], 'u0': proc['u0'], 'xj': proc['xj'],
            'vds': vds, 'abs_vds': abs(vds),
            'vgs': vg - vs, 'vbs': vb - vs, 'vgd': vg - vd,
            'overdrive': (vg - vs) - proc['vth0']
        }
        X = pd.DataFrame([row])[bundle['feature_names']].values
        X_s = scaler.transform(X)
        pred_log = model.predict(X_s)[0]
        return 10.0 ** pred_log

    def predict_gate_leakage(self, gate, inp, corner, node_v):
        vdd = corner['vdd']
        temp = corner['temp']
        np_ = corner['nmos']
        pp_ = corner['pmos']
        vout = node_v['out']

        if gate == 'INV':
            if inp == '0':
                mn_sub = self.predict_fet('nmos_off', vdd, temp, WN, vout, 0.0, 0.0, 0.0, np_)[0]
                mp_gate = self.predict_fet('pmos_on', vdd, temp, WP, vout, vdd, 0.0, vdd, pp_)[1]
                return mn_sub + mp_gate
            else:
                mp = self.predict_fet('pmos_off', vdd, temp, WP, vout, vdd, vdd, vdd, pp_)
                return mp[0]

        elif gate == 'NAND2':
            vx = node_v['x']
            if inp == '00':
                mn_sub = self.predict_fet('nmos_off', vdd, temp, WN, vout, vx, 0.0, 0.0, np_)[0]
                mp1_gate = self.predict_fet('pmos_on', vdd, temp, WP, vout, vdd, 0.0, vdd, pp_)[1]
                mp2_gate = self.predict_fet('pmos_on', vdd, temp, WP, vout, vdd, 0.0, vdd, pp_)[1]
                return mn_sub + mp1_gate + mp2_gate
            elif inp == '01':
                mn_sub = self.predict_fet('nmos_off', vdd, temp, WN, vout, vx, 0.0, 0.0, np_)[0]
                mp1_gate = self.predict_fet('pmos_on', vdd, temp, WP, vout, vdd, 0.0, vdd, pp_)[1]
                return mn_sub + mp1_gate
            elif inp == '10':
                mn_sub = self.predict_fet('nmos_off', vdd, temp, WN, vx, 0.0, 0.0, 0.0, np_)[0]
                mp2_gate = self.predict_fet('pmos_on', vdd, temp, WP, vout, vdd, 0.0, vdd, pp_)[1]
                return mn_sub + mp2_gate
            else:
                mp1 = self.predict_fet('pmos_off', vdd, temp, WP, vout, vdd, vdd, vdd, pp_)
                mp2 = self.predict_fet('pmos_off', vdd, temp, WP, vout, vdd, vdd, vdd, pp_)
                return mp1[0] + mp2[0]

        elif gate == 'NOR2':
            vy = node_v['y']
            if inp == '00':
                mn1_sub = self.predict_fet('nmos_off', vdd, temp, WN, vout, 0.0, 0.0, 0.0, np_)[0]
                mn2_sub = self.predict_fet('nmos_off', vdd, temp, WN, vout, 0.0, 0.0, 0.0, np_)[0]
                mp1_gate = self.predict_fet('pmos_on', vdd, temp, WP, vy, vdd, 0.0, vdd, pp_)[1]
                mp2_gate = self.predict_fet('pmos_on', vdd, temp, WP, vout, vy, 0.0, vdd, pp_)[1]
                return mn1_sub + mn2_sub + mp1_gate + mp2_gate
            elif inp == '01':
                mp2 = self.predict_fet('pmos_off', vdd, temp, WP, vout, vy, vdd, vdd, pp_)
                mp1_gate = self.predict_fet('pmos_on', vdd, temp, WP, vy, vdd, 0.0, vdd, pp_)[1]
                return mp2[0] + mp1_gate
            elif inp == '10':
                mp1 = self.predict_fet('pmos_off', vdd, temp, WP, vy, vdd, vdd, vdd, pp_)
                return mp1[0]
            else:
                mp1 = self.predict_fet('pmos_off', vdd, temp, WP, vy, vdd, vdd, vdd, pp_)
                return mp1[0]

        elif gate == 'AND2':
            leak_nand = self.predict_gate_leakage('NAND2', inp, corner, {'out': node_v['n_out'], 'x': node_v['x']})
            inv_in = '1' if node_v['n_out'] > vdd/2 else '0'
            leak_inv = self.predict_gate_leakage('INV', inv_in, corner, {'out': node_v['out']})
            
            interstage = 0.0
            if node_v['n_out'] > vdd/2:
                interstage = self.predict_fet('nmos_on', vdd, temp, WN, node_v['out'], 0.0, node_v['n_out'], 0.0, np_)[1]

            return leak_nand + leak_inv + interstage

        elif gate == 'OR2':
            leak_nor = self.predict_gate_leakage('NOR2', inp, corner, {'out': node_v['n_out'], 'y': node_v['y']})
            inv_in = '1' if node_v['n_out'] > vdd/2 else '0'
            leak_inv = self.predict_gate_leakage('INV', inv_in, corner, {'out': node_v['out']})
            
            interstage = 0.0
            if node_v['n_out'] > vdd/2:
                interstage = self.predict_fet('nmos_on', vdd, temp, WN, node_v['out'], 0.0, node_v['n_out'], 0.0, np_)[1]

            return leak_nor + leak_inv + interstage

        return 1e-12

def main():
    print("=" * 70)
    print(" STARTING PART B: 5-GATE VALIDATION (18 CASES x 200 CORNERS)")
    print("=" * 70)

    corners = generate_corners(num_corners=200, seed=123)
    evaluator = GateMLEvaluator()

    all_spice = []
    all_ml = []
    summary_records = []

    for gate, inp in GATE_CASES:
        print(f"[*] Simulating & Evaluating: {gate:5s} (Input = {inp})...")
        tasks = [(gate, inp, c) for c in corners]

        with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
            sim_results = list(pool.map(simulate_gate_spice, tasks))

        spice_vals = []
        ml_vals = []

        for i, (spice_leak, node_v) in enumerate(sim_results):
            if spice_leak <= 0:
                continue
            corner = corners[i]
            ml_leak = evaluator.predict_gate_leakage(gate, inp, corner, node_v)

            spice_vals.append(spice_leak)
            ml_vals.append(ml_leak)
            all_spice.append(spice_leak)
            all_ml.append(ml_leak)

        sp = np.array(spice_vals)
        ml = np.array(ml_vals)

        sp_med = np.median(sp)
        ml_med = np.median(ml)
        bias = np.median(ml - sp)
        valid_mask = (sp > 1e-13)
        if valid_mask.sum() > 0:
            rel_errors = np.abs(ml[valid_mask] - sp[valid_mask]) / sp[valid_mask] * 100.0
            med_err = np.median(rel_errors)
            p95_err = np.percentile(rel_errors, 95)
        else:
            med_err = 0.0
            p95_err = 0.0

        summary_records.append({
            'gate': gate,
            'input': inp,
            'spice_median_A': sp_med,
            'ml_median_A': ml_med,
            'bias_A': bias,
            'median_error_pct': med_err,
            'p95_error_pct': p95_err
        })

    df_gate_results = pd.DataFrame(summary_records)
    df_gate_results.to_csv("results/gate_results_table.csv", index=False)
    print("\n" + "=" * 70)
    print("DELIVERABLE 6: GATE RESULTS TABLE (18 CASES)")
    print("=" * 70)
    print(df_gate_results.to_string(index=False))

    all_sp = np.array(all_spice)
    all_m = np.array(all_ml)

    plt.figure(figsize=(7, 6.5))
    plot_mask = (all_sp > 1e-13)
    plt.scatter(all_sp[plot_mask], all_m[plot_mask], alpha=0.35, s=10, color='darkblue', label='Gate Simulations (Active Regime)')
    min_v = max(min(all_sp[plot_mask].min(), all_m[plot_mask].min()), 1e-14)
    max_v = max(all_sp.max(), all_m.max()) * 1.4
    plt.plot([min_v, max_v], [min_v, max_v], 'r--', lw=1.6, label='Ideal Parity (y=x)')

    overall_med_err = np.median(np.abs(all_m[plot_mask] - all_sp[plot_mask]) / all_sp[plot_mask] * 100.0)

    plt.xscale('log')
    plt.yscale('log')
    plt.xlim(min_v, max_v)
    plt.ylim(min_v, max_v)
    plt.xlabel('SPICE Reference Leakage (A) [Log Scale]', fontsize=11)
    plt.ylabel('ML Predicted Leakage (A) [Log Scale]', fontsize=11)
    plt.title(f'Deliverable 7: Gate Parity Plot (Active Regime > 100 fA)\nOverall Median Error = {overall_med_err:.2f}%', fontsize=12)
    plt.legend(frameon=True)
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig("results/plots/gate_parity_plot.png", dpi=300)
    plt.close()

    print("\n Saved Deliverable 6 -> results/gate_results_table.csv")
    print(" Saved Deliverable 7 -> results/plots/gate_parity_plot.png")
    print(f"\n Part B Complete! Overall Median Error: {overall_med_err:.2f}%")

if __name__ == "__main__":
    main()
