"""Part A, step 1b: extra "rail-focused" training data.

Why: inside a logic gate every transistor terminal sits at (or very close to)
0 V or VDD. With uniform sampling of Vd and Vs, only ~4 % of the 10,000
samples land near those rail corners, so the models are least accurate exactly
where Parts B and C use them. The project allows more samples ("the number of
samples may be increased ... as needed"), so this script draws an extra set per
case in which Vd and Vs are concentrated near the rails. Everything else
(VDD, T, W, process parameters, Vg, Vb) uses the same distributions as step 1.

These rows are used for TRAINING ONLY. The validation and test sets that are
reported stay the official uniform datasets in data/<case>.csv.

Vd and Vs are drawn independently from this mixture:
    35 %  exactly 0 or exactly VDD   (50 / 50)
    35 %  near a rail: U(0, 0.15 VDD) or U(0.85 VDD, VDD)
    30 %  uniform U(0, VDD)

Usage (from the repo root):
    python scripts/01b_generate_rail_data.py            # 10,000 rows per case
    python scripts/01b_generate_rail_data.py --n 500    # quick test
Output: data/rail/<case>.csv  (same columns as data/<case>.csv)
"""
import argparse
import os
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import config as C
from spice_utils import build_netlist, get_param, run_ngspice, set_params, split_models

RAIL_SEED_OFFSET = 1000      # different from the seeds used for data/<case>.csv


def rail_voltage(vdd, rng):
    n = len(vdd)
    u = rng.uniform(0, 1, n)
    side_hi = rng.uniform(0, 1, n) < 0.5
    exact = np.where(side_hi, vdd, 0.0)
    near = np.where(side_hi, vdd * rng.uniform(0.85, 1.0, n), vdd * rng.uniform(0.0, 0.15, n))
    unif = vdd * rng.uniform(0, 1, n)
    return np.where(u < 0.35, exact, np.where(u < 0.70, near, unif))


def draw_samples(case, nominal, n, rng):
    spec = C.CASES[case]
    vdd = rng.uniform(C.VDD_NOM * (1 - C.VDD_SPREAD), C.VDD_NOM * (1 + C.VDD_SPREAD), n)
    rows = {
        "vdd": vdd,
        "temp": rng.uniform(*C.TEMP_RANGE, n),
        "w": rng.uniform(C.W_RANGE[0] * C.LMIN, C.W_RANGE[1] * C.LMIN, n),
        "vd": rail_voltage(vdd, rng),
        "vs": rail_voltage(vdd, rng),
        "vg": vdd if spec["vg"] == "vdd" else np.zeros(n),
        "vb": vdd if spec["vb"] == "vdd" else np.zeros(n),
    }
    for p in C.PROC_PARAMS:
        rows[p] = nominal[p] * rng.uniform(1 - C.PROC_SPREAD, 1 + C.PROC_SPREAD, n)
    return pd.DataFrame(rows)


def simulate_row(args):
    model_card, dev_type, row = args
    card = set_params(model_card, {p: row[p] for p in C.PROC_PARAMS}, "mdev")
    net = build_netlist(card, dev_type, row["w"], C.LMIN, row["vd"], row["vg"],
                        row["vs"], row["vb"], row["temp"], C.SPICE_OPTIONS)
    try:
        return run_ngspice(net)
    except Exception as e:
        print("WARN:", str(e).splitlines()[0][:120])
        return (np.nan,) * 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=C.N_SAMPLES)
    ap.add_argument("--cases", nargs="+", default=list(C.CASES))
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()

    models = split_models(C.MODEL_FILE)
    os.makedirs("data/rail", exist_ok=True)
    for k, case in enumerate(args.cases):
        dev = C.CASES[case]["type"]
        card = models[dev]
        nominal = {p: get_param(card, p) for p in C.PROC_PARAMS}
        rng = np.random.default_rng(C.SEED + RAIL_SEED_OFFSET + k)
        df = draw_samples(case, nominal, args.n, rng)
        t0 = time.time()
        with Pool(args.workers) as pool:
            res = pool.map(simulate_row, [(card, dev, r) for r in df.to_dict("records")], chunksize=20)
        df[["id", "ig", "is", "ib"]] = np.array(res)
        bad = int(df["id"].isna().sum())
        df = df.dropna()[C.CSV_COLUMNS]
        out = f"data/rail/{case}.csv"
        df.to_csv(out, index=False, float_format="%.6e")
        print(f"{case:9s}: {len(df)} rail rows -> {out}  ({bad} failed, {time.time()-t0:.0f} s)", flush=True)


if __name__ == "__main__":
    main()
