"""Part A, step 1: generate the 4 transistor datasets with ngspice.

Usage (from the repo root):
    python scripts/01_generate_transistor_data.py               # all 4 cases, settings from config.py
    python scripts/01_generate_transistor_data.py --n 200       # quick test with 200 samples per case
    python scripts/01_generate_transistor_data.py --cases nmos_off

Output: data/<case>.csv with the columns required by the project,
and one example netlist per case in netlists/transistor/.
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
from spice_utils import split_models, get_param, set_params, build_netlist, run_ngspice


def draw_samples(case, nominal, n, rng):
    """Draw n random samples for one case (VDD first, then Vd/Vs depend on it)."""
    spec = C.CASES[case]
    vdd = rng.uniform(C.VDD_NOM * (1 - C.VDD_SPREAD), C.VDD_NOM * (1 + C.VDD_SPREAD), n)
    rows = {
        "vdd":  vdd,
        "temp": rng.uniform(*C.TEMP_RANGE, n),
        "w":    rng.uniform(C.W_RANGE[0] * C.LMIN, C.W_RANGE[1] * C.LMIN, n),
        "vd":   rng.uniform(0, 1, n) * vdd,
        "vs":   rng.uniform(0, 1, n) * vdd,
        "vg":   vdd if spec["vg"] == "vdd" else np.zeros(n),
        "vb":   vdd if spec["vb"] == "vdd" else np.zeros(n),
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
    except Exception as e:  # keep going, mark the row as failed
        print("WARN:", str(e).splitlines()[0][:120])
        return (np.nan,) * 4


def write_example_netlist(case, model_card, dev_type, nominal):
    """Nominal-corner netlist for the deliverables (includes the model file)."""
    spec = C.CASES[case]
    vg = C.VDD_NOM if spec["vg"] == "vdd" else 0.0
    vb = C.VDD_NOM if spec["vb"] == "vdd" else 0.0
    card = set_params(model_card, {p: nominal[p] for p in C.PROC_PARAMS}, "mdev")
    net = build_netlist(card, dev_type, 2 * C.LMIN, C.LMIN, C.VDD_NOM / 2, vg,
                        0.0, vb, 27.0, C.SPICE_OPTIONS)
    os.makedirs("netlists/transistor", exist_ok=True)
    with open(f"netlists/transistor/{case}.cir", "w") as f:
        f.write(net)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=C.N_SAMPLES)
    ap.add_argument("--cases", nargs="+", default=list(C.CASES))
    ap.add_argument("--model", default=C.MODEL_FILE)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()

    models = split_models(args.model)
    os.makedirs("data", exist_ok=True)

    for k, case in enumerate(args.cases):
        dev_type = C.CASES[case]["type"]
        card = models[dev_type]
        nominal = {p: get_param(card, p) for p in C.PROC_PARAMS}
        rng = np.random.default_rng(C.SEED + k)   # different but fixed seed per case

        write_example_netlist(case, card, dev_type, nominal)
        df = draw_samples(case, nominal, args.n, rng)

        t0 = time.time()
        jobs = [(card, dev_type, row) for row in df.to_dict("records")]
        with Pool(args.workers) as pool:
            res = pool.map(simulate_row, jobs, chunksize=20)
        df[["id", "ig", "is", "ib"]] = np.array(res)

        bad = df["id"].isna().sum()
        df = df.dropna()[C.CSV_COLUMNS]
        out = f"data/{case}.csv"
        df.to_csv(out, index=False, float_format="%.6e")
        print(f"{case:9s}: {len(df)} rows -> {out}  ({bad} failed, {time.time()-t0:.0f} s)")


if __name__ == "__main__":
    main()
