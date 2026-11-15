#!/usr/bin/env python3
"""New, unseen test cases for the whole flow (what a TA would do: give fresh inputs and compare).

Run from the repo root:
    python testing/03_test_cases.py                       # all levels: transistor, gates, CLA
    python testing/03_test_cases.py --what transistor     # only fresh single-transistor samples
    python testing/03_test_cases.py --seed 99 --n 500     # another fresh draw

Your own test cases (e.g. given by the TA):
    python testing/03_test_cases.py --point case=nmos_off,vdd=1.0,temp=85,w=48e-9,vd=1.0,vs=0
        (process parameters default to the model-card values; give vth0=..., toxe=... to change them;
         vg and vb follow the case)
    python testing/03_test_cases.py --csv my_points.csv --case pmos_on
        (columns vdd,temp,w,vd,vs[,vg,vb,vth0,toxe,ndep,u0,xj][,id,ig,is,ib]; missing currents
         are simulated with ngspice, missing process parameters use the model-card values)

Levels (all with a NEW random seed, never used for training, validation, test or Part B/C):
  transistor  --n samples per case, drawn like the official datasets ("uniform") and with the
              terminals at the rails like inside gates ("gate-like"); SPICE vs ML for Id, Ig, Is, Ib.
  gates       all 18 gate / input cases at --gate-corners new corners (scripts/04_validate_gates.py).
  cla         the 3-bit CLA, all 128 vectors at --cla-corners new corners (scripts/05_validate_circuit.py).
Every level is run for each trained model set that exists (rail = saved_models/,
no_rail = saved_models/no_rail/).

Outputs: testing/results/test_cases/  (summary.md + CSVs; gate and CLA folders per variant)
"""
import argparse
import os
import shutil
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

from common import C, CASES, OUT, TARGETS, TransistorModel, md_table, rel_err, variants, load_script
from spice_utils import get_param, split_models

GEN = load_script("01_generate_transistor_data")
RAIL = load_script("01b_generate_rail_data")
OUTD = os.path.join(OUT, "test_cases")
CARDS = split_models(C.MODEL_FILE)
NOMINAL = {d: {p: get_param(CARDS[d], p) for p in C.PROC_PARAMS} for d in ("nmos", "pmos")}


def simulate(df, case):
    dev = C.CASES[case]["type"]
    with Pool(os.cpu_count()) as pool:
        res = pool.map(GEN.simulate_row, [(CARDS[dev], dev, r) for r in df.to_dict("records")], chunksize=10)
    df = df.copy()
    df[TARGETS] = np.array(res)
    return df.dropna(subset=TARGETS)


def complete_inputs(df, case):
    """Fill vg, vb and missing process parameters like the official datasets."""
    spec, dev = C.CASES[case], C.CASES[case]["type"]
    df = df.copy()
    if "vg" not in df:
        df["vg"] = df["vdd"] if spec["vg"] == "vdd" else 0.0
    if "vb" not in df:
        df["vb"] = df["vdd"] if spec["vb"] == "vdd" else 0.0
    for p in C.PROC_PARAMS:
        if p not in df:
            df[p] = NOMINAL[dev][p]
    return df


def score_rows(df, pred, case, kind, vname):
    rows = []
    for t in TARGETS:
        e = rel_err(df[t].values, pred[t].values)
        rows.append({"variant": vname, "case": case, "test_set": kind, "current": t, "n": len(e),
                     "median_abs_I_A": float(np.median(np.abs(df[t]))),
                     "median_err_%": float(np.median(e)), "p95_err_%": float(np.percentile(e, 95)),
                     "sign_acc": float(np.mean(np.sign(df[t].values) == np.sign(pred[t].values)))})
    return rows


def predict_all(df, case):
    out = {}
    for vname, mdir in variants():
        out[vname] = TransistorModel.load(f"{mdir}/{case}.joblib").predict(df)
    return out


def level_transistor(args):
    rows, raw = [], []
    for k, case in enumerate(CASES):
        dev = C.CASES[case]["type"]
        rng_u = np.random.default_rng(args.seed + k)
        rng_r = np.random.default_rng(args.seed + 100 + k)
        sets = {"uniform": GEN.draw_samples(case, NOMINAL[dev], args.n, rng_u),
                "gate-like": RAIL.draw_samples(case, NOMINAL[dev], args.n, rng_r)}
        for kind, df in sets.items():
            df = simulate(df, case)
            for vname, pred in predict_all(df, case).items():
                rows += score_rows(df, pred, case, kind, vname)
                r = df.copy()
                for t in TARGETS:
                    r[f"ml_{t}"] = pred[t].values
                r.insert(0, "variant", vname); r.insert(1, "case", case); r.insert(2, "test_set", kind)
                raw.append(r)
        print(f"  {case}: {args.n} uniform + {args.n} gate-like fresh samples simulated", flush=True)
    os.makedirs(OUTD, exist_ok=True)
    pd.concat(raw).to_csv(os.path.join(OUTD, "transistor_fresh_raw.csv"), index=False, float_format="%.6e")
    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(OUTD, "transistor_fresh_summary.csv"), index=False, float_format="%.5g")
    # compare with the official test split
    off = pd.read_csv("results/part_a/chosen_models_test.csv")
    off = off[off.test_set == "uniform"].rename(columns={"target": "current", "median_err_%": "official_test_med_%"})
    piv = res.pivot_table(index=["case", "current"], columns=["variant", "test_set"], values="median_err_%")
    piv.columns = [f"{v}:{s} med %" for v, s in piv.columns]
    piv = piv.reset_index().merge(off[["case", "current", "official_test_med_%"]], on=["case", "current"], how="left")
    print("\nFresh transistor test cases, median error % (official test split for comparison):\n" +
          piv.to_string(index=False, float_format=lambda v: f"{v:.3g}"))
    return piv


def run(cmd):
    print("  $ " + " ".join(cmd), flush=True)
    subprocess.run([sys.executable] + cmd, check=True)


def level_gates_cla(args, do_gates, do_cla):
    summary = []
    vs = variants()
    first = None
    for vname, _ in vs:
        gdir = os.path.join(OUTD, f"gates_seed{args.seed}_{vname}")
        cdir = os.path.join(OUTD, f"cla_seed{args.seed}_{vname}")
        flag = ["--no-rail"] if vname == "no_rail" else []
        if first is not None:            # reuse the SPICE runs of the first variant (same corners)
            fg, fc = first
            os.makedirs(gdir, exist_ok=True)
            for f in os.listdir(fg):
                if f.startswith("gate_spice_seed"):
                    shutil.copy(os.path.join(fg, f), gdir)
            src = os.path.join(fc, f"spice_cache_seed{args.seed}")
            if os.path.isdir(src) and not os.path.isdir(os.path.join(cdir, f"spice_cache_seed{args.seed}")):
                shutil.copytree(src, os.path.join(cdir, f"spice_cache_seed{args.seed}"))
        if do_gates or do_cla:
            run(["scripts/04_validate_gates.py", "--seed", str(args.seed), "--corners", str(args.gate_corners),
                 "--outdir", gdir] + flag)
            g = pd.read_csv(os.path.join(gdir, "gate_all.csv"), dtype={"inp": str})
            g = g[g.err_pct.notna()]
            reg = g[~((g.gate == "NOR2") & g.inp.isin(["10", "11"]))]
            summary.append({"variant": vname, "level": f"gates (18 cases x {args.gate_corners} new corners)",
                            "median_err_%": g.err_pct.median(), "p95_err_%": np.percentile(g.err_pct, 95),
                            "mean_acc_%": 100 - g.err_pct.mean(), "mean_acc_16_cases_%": 100 - reg.err_pct.mean()})
        if do_cla:
            run(["scripts/05_validate_circuit.py", "--seed", str(args.seed), "--corners", str(args.cla_corners),
                 "--gate-csv", os.path.join(gdir, "gate_all.csv"), "--outdir", cdir])
            s = pd.read_csv(os.path.join(cdir, "circuit_summary.csv")).set_index("method")
            for m, lab in (("ML plain sum (project method)", "plain sum"), ("ML loading-aware", "loading-aware")):
                summary.append({"variant": vname, "level": f"CLA {lab} (128 vectors x {args.cla_corners} new corners)",
                                "median_err_%": s.loc[m, "median_error_pct"], "p95_err_%": s.loc[m, "p95_error_pct"],
                                "mean_acc_%": s.loc[m, "mean_accuracy_pct"], "mean_acc_16_cases_%": np.nan})
        if first is None:
            first = (gdir, cdir)
    return pd.DataFrame(summary)


def single_point(args):
    kv = dict(x.split("=") for x in args.point.split(","))
    case = kv.pop("case")
    df = complete_inputs(pd.DataFrame([{k: float(v) for k, v in kv.items()}]), case)
    df = simulate(df[[c for c in C.CSV_COLUMNS if c in df]], case)
    print(f"\nTest point ({case}):\n" + df[C.CSV_COLUMNS[:12]].to_string(index=False))
    for vname, pred in predict_all(df, case).items():
        print(f"\n  model set '{vname}':")
        for t in TARGETS:
            sp, ml = df[t].iloc[0], pred[t].iloc[0]
            print(f"    {t}: SPICE {sp: .4e} A   ML {ml: .4e} A   error {abs(ml - sp) / abs(sp) * 100:.3f} %")


def from_csv(args):
    df = complete_inputs(pd.read_csv(args.csv), args.case)
    if not all(t in df for t in TARGETS):
        print(f"[*] simulating {len(df)} points with ngspice ...")
        df = simulate(df[[c for c in C.CSV_COLUMNS if c in df]], args.case)
    rows = []
    for vname, pred in predict_all(df, args.case).items():
        rows += score_rows(df, pred, args.case, os.path.basename(args.csv), vname)
        for t in TARGETS:
            df[f"ml_{t}_{vname}"] = pred[t].values
    os.makedirs(OUTD, exist_ok=True)
    out = os.path.join(OUTD, f"csv_{os.path.splitext(os.path.basename(args.csv))[0]}_predictions.csv")
    df.to_csv(out, index=False, float_format="%.6e")
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    print(f"\nPredictions saved to {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--what", nargs="+", default=["transistor", "gates", "cla"],
                    choices=["transistor", "gates", "cla"])
    ap.add_argument("--seed", type=int, default=2026, help="fresh seed (not 7, 1007+, 123)")
    ap.add_argument("--n", type=int, default=300, help="fresh samples per case and kind")
    ap.add_argument("--gate-corners", type=int, default=50)
    ap.add_argument("--cla-corners", type=int, default=20)
    ap.add_argument("--point", default=None)
    ap.add_argument("--csv", default=None)
    ap.add_argument("--case", default=None, choices=CASES)
    args = ap.parse_args()
    if args.seed in (C.SEED, 123) or 1000 <= args.seed < 1020:
        sys.exit("[!] choose a seed that is not used by the training data or Part B / C (7, 1007+, 123)")
    if args.point:
        return single_point(args)
    if args.csv:
        if not args.case:
            sys.exit("--csv needs --case")
        return from_csv(args)

    os.makedirs(OUTD, exist_ok=True)
    md = [f"# Fresh test cases (seed {args.seed}, never used in training or in Parts B / C)", ""]
    if "transistor" in args.what:
        print("\n=== Transistor level")
        piv = level_transistor(args)
        md += [f"## Transistors: {args.n} uniform + {args.n} gate-like new samples per case (median error %)", "",
               md_table(piv), ""]
    if "gates" in args.what or "cla" in args.what:
        print("\n=== Gate level" + (" and CLA" if "cla" in args.what else ""))
        summ = level_gates_cla(args, "gates" in args.what, "cla" in args.what)
        summ.to_csv(os.path.join(OUTD, f"gates_cla_seed{args.seed}_summary.csv"), index=False, float_format="%.5g")
        print("\n" + summ.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
        md += ["## Gates and CLA at new corners", "", md_table(summ), "",
               "Official results (seed 123, 200 corners) for comparison: gates 0.88 % median error, "
               "99.04 % mean accuracy over 16 regular cases; CLA plain 67.9 %, loading-aware 99.01 %.", ""]
    with open(os.path.join(OUTD, "summary.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    print(f"\nSaved {OUTD}/summary.md")


if __name__ == "__main__":
    main()
