#!/usr/bin/env python3
"""Part C: test-circuit validation -- 3-bit carry-lookahead adder (CLA).

Run from the repo root:   python3 scripts/05_test_circuit.py
Quick test:               python3 scripts/05_test_circuit.py --corners 10
"""
import os
import re
import sys
import argparse
import subprocess
import tempfile
import time
import importlib.util
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cla3
from spice_utils import split_models, set_params

OUT_DIR = "results/part_c"
DEADLINE = None

class OutOfTime(Exception):
    pass

def check_time():
    if DEADLINE is not None and time.time() > DEADLINE:
        raise OutOfTime()

NET_DIR = "netlists/circuit"
NUM = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"

def load_part_b():
    spec = importlib.util.spec_from_file_location("part_b", os.path.join(HERE, "04_simulate_gates.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["part_b"] = mod
    spec.loader.exec_module(mod)
    main = sys.modules["__main__"]
    for name in ("LeakageResNet", "PyTorchWrapper", "MultiOutputModel", "MultiXGB"):
        if hasattr(mod, name):
            setattr(main, name, getattr(mod, name))
    return mod

PB = load_part_b()
WN, WP, LMIN, L_DIFF = PB.WN, PB.WP, PB.LMIN, PB.L_DIFF
MODELS_TEXT = PB.MODELS_TEXT

def _fet(name, kind, d, g, s):
    if kind == "n":
        w, mod, b = WN, "nmos_mod", "0"
    else:
        w, mod, b = WP, "pmos_mod", "vdd"
    ad = w * L_DIFF
    pd = 2 * (w + L_DIFF)
    return (f"M{name} {d} {g} {s} {b} {mod} W={w:.5e} L={LMIN:.5e} "
            f"AD={ad:.5e} AS={ad:.5e} PD={pd:.5e} PS={pd:.5e}")

def _inv(g, i, o):
    return [_fet(f"{g}p", "p", o, i, "vdd"), _fet(f"{g}n", "n", o, i, "0")]

def _nand(g, a, b, o):
    x = f"{g}_x"
    return [_fet(f"{g}p1", "p", o, a, "vdd"), _fet(f"{g}p2", "p", o, b, "vdd"),
            _fet(f"{g}n1", "n", o, a, x), _fet(f"{g}n2", "n", x, b, "0")]

def _nor(g, a, b, o):
    y = f"{g}_y"
    return [_fet(f"{g}p1", "p", y, a, "vdd"), _fet(f"{g}p2", "p", o, b, y),
            _fet(f"{g}n1", "n", o, a, "0"), _fet(f"{g}n2", "n", o, b, "0")]

def gate_transistors(g, t, ins, out):
    if t == "INV":
        return _inv(g, ins[0], out)
    if t == "NAND2":
        return _nand(g, ins[0], ins[1], out)
    if t == "NOR2":
        return _nor(g, ins[0], ins[1], out)
    if t == "AND2":
        return _nand(g, ins[0], ins[1], f"{g}_n") + _inv(f"{g}i", f"{g}_n", out)
    if t == "OR2":
        return _nor(g, ins[0], ins[1], f"{g}_n") + _inv(f"{g}i", f"{g}_n", out)
    raise ValueError(t)

def internal_nodesets(g, t, pat, logic_in_out, vdd):
    ns = []
    if t in ("NAND2", "AND2"):
        vx = 0.0 if pat in ("01", "11") else (vdd if pat == "10" else vdd / 2)
        ns.append(f"v({g}_x)={vx:.4f}")
    if t in ("NOR2", "OR2"):
        vy = vdd if pat in ("00", "01") else 0.0
        ns.append(f"v({g}_y)={vy:.4f}")
    return ns

def circuit_deck(corner, vec, op_only=True):
    vdd, temp = corner["vdd"], corner["temp"]
    logic = cla3.logic_eval(vec)
    n_card = set_params(MODELS_TEXT["nmos"], corner["nmos"], "nmos_mod")
    p_card = set_params(MODELS_TEXT["pmos"], corner["pmos"], "pmos_mod")
    L = [f"* 3-bit CLA, vector {vec:07b} (cin b2 b1 b0 a2 a1 a0 = bit6..bit0)", n_card, p_card,
         f"Vdd vdd 0 DC {vdd:.6f}"]
    for net in cla3.INPUTS:
        L.append(f"V{net} {net} 0 DC {vdd * logic[net]:.6f}")
    ns = []
    for g, t, ins, out in cla3.GATES:
        L += gate_transistors(g, t, ins, out)
        pat = cla3.pattern([logic[i] for i in ins])
        ns += internal_nodesets(g, t, pat, None, vdd)
        if t in ("AND2", "OR2"):
            inner = (1 - (logic[ins[0]] & logic[ins[1]])) if t == "AND2" else (1 - (logic[ins[0]] | logic[ins[1]]))
            ns.append(f"v({g}_n)={vdd * inner:.4f}")
        ns.append(f"v({out})={vdd * logic[out]:.4f}")
    L.append(".nodeset " + " ".join(ns))
    L.append(".options gmin=1e-18 abstol=1e-18 reltol=1e-6 vntol=1e-9 itl1=400")
    L.append(f".temp {temp:.2f}")
    if op_only:
        L += [".control", "set numdgt = 10", "op", "let ileak = -i(vdd)", "echo LEAK $&ileak",
              "echo OUTS $&v(s0) $&v(s1) $&v(s2) $&v(cout)", ".endc"]
    L.append(".end")
    return "\n".join(L) + "\n"

def simulate_circuit(task):
    ci, vec, corner = task
    deck = circuit_deck(corner, vec)
    with tempfile.NamedTemporaryFile("w", suffix=".cir", delete=False) as f:
        f.write(deck)
        path = f.name
    leak, outs = np.nan, [np.nan] * 4
    try:
        res = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True, timeout=60)
        for line in res.stdout.splitlines():
            if line.startswith("LEAK"):
                m = re.findall(NUM, line[4:])
                if m:
                    leak = float(m[0])
            elif line.startswith("OUTS"):
                m = re.findall(NUM, line[4:])
                if len(m) == 4:
                    outs = [float(x) for x in m]
    except subprocess.TimeoutExpired:
        pass
    finally:
        os.remove(path)
    return ci, vec, leak, outs

def gate_case_list():
    return list(PB.GATE_CASES)

def _pin_loading_ig(evaluator, gate, inp, corner, node_v):
    vdd, temp, npar = corner["vdd"], corner["temp"], corner["nmos"]
    ig = lambda vd, vs: float(evaluator.predict_fet("nmos_on", vdd, temp, WN, vd, vs, vdd, 0.0, npar)[1])
    out = node_v.get("n_out", node_v.get("out", 0.0)) if gate in ("AND2", "OR2") else node_v.get("out", 0.0)
    la = lb = 0.0
    if gate == "INV":
        la = ig(node_v.get("out", 0.0), 0.0) if inp[0] == "1" else 0.0
    elif gate in ("NAND2", "AND2"):
        x = node_v.get("x", 0.0)
        la = ig(out, x) if inp[0] == "1" else 0.0
        lb = ig(x, 0.0) if inp[1] == "1" else 0.0
    else:
        la = ig(out, 0.0) if inp[0] == "1" else 0.0
        lb = ig(out, 0.0) if inp[1] == "1" else 0.0
    return la, lb

def _table_from_df(df):
    ml, load = {}, {}
    for r in df.itertuples():
        key = (r.gate, str(r.inp).zfill(1 if r.gate == "INV" else 2), int(r.corner))
        ml[key] = r.ml_leak
        load[key] = (r.load_a, r.load_b)
    return ml, load

def build_gate_ml_table(corners, workers, cache_path):
    if os.path.exists(cache_path):
        df = pd.read_csv(cache_path, dtype={"inp": str})
        if len(df) == 18 * len(corners) and "load_a" in df.columns:
            print(f"[*] using cached gate ML table: {cache_path}")
            return _table_from_df(df)
    print("[*] building gate-level ML table (18 gate cases x corners) ...")
    evaluator = PB.GateMLEvaluator()
    case_dir = os.path.join(os.path.dirname(cache_path), "gate_cases")
    os.makedirs(case_dir, exist_ok=True)
    frames = []
    for gate, inp in gate_case_list():
        cpath = os.path.join(case_dir, f"{gate}_{inp}.csv")
        if os.path.exists(cpath):
            cdf = pd.read_csv(cpath, dtype={"inp": str})
            if len(cdf) == len(corners):
                frames.append(cdf)
                continue
        check_time()
        tasks = [(gate, inp, c) for c in corners]
        with ProcessPoolExecutor(max_workers=workers) as pool:
            sims = list(pool.map(PB.simulate_gate_spice, tasks))
        rows = []
        for ci, (spice_leak, node_v) in enumerate(sims):
            ml = evaluator.predict_gate_leakage(gate, inp, corners[ci], node_v)
            la, lb = _pin_loading_ig(evaluator, gate, inp, corners[ci], node_v)
            rows.append({"gate": gate, "inp": inp, "corner": ci, "spice_leak": spice_leak,
                         "ml_leak": ml, "load_a": la, "load_b": lb})
        part = pd.DataFrame(rows)
        part.to_csv(cpath, index=False)
        frames.append(part)
        print(f"    gate case {gate} {inp} done")
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(cache_path, index=False)
    return _table_from_df(df)

def ml_circuit_leak(table, load, corner_idx, vec):
    logic = cla3.logic_eval(vec)
    plain = extra = 0.0
    for g, t, ins, out in cla3.GATES:
        pat = cla3.pattern([logic[i] for i in ins])
        key = (t, pat, corner_idx)
        plain += table[key]
        for k, net in enumerate(ins):
            if net not in cla3.INPUTS:
                extra += load[key][k]
    return plain, plain + extra

def metrics(sp, ml):
    sp, ml = np.asarray(sp), np.asarray(ml)
    ok = sp > 1e-13
    rel = np.abs(ml[ok] - sp[ok]) / sp[ok] * 100.0
    return {"spice_median_A": float(np.median(sp)), "ml_median_A": float(np.median(ml)),
            "bias_A": float(np.median(ml - sp)),
            "median_error_pct": float(np.median(rel)) if ok.any() else 0.0,
            "p95_error_pct": float(np.percentile(rel, 95)) if ok.any() else 0.0}

def write_example_netlist():
    os.makedirs(NET_DIR, exist_ok=True)
    nominal = {"vdd": PB.__dict__.get("VDD_NOM", 1.0), "temp": 27.0,
               "nmos": dict(PB.NOM_NMOS), "pmos": dict(PB.NOM_PMOS)}
    with open(os.path.join(NET_DIR, "cla3.sp"), "w") as f:
        f.write(circuit_deck(nominal, 0b1010101))
    print(f"[*] example netlist -> {NET_DIR}/cla3.sp")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corners", type=int, default=200)
    ap.add_argument("--seed", type=int, default=123, help="must match Part B (default 123)")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--vectors", type=int, default=128, help="use only the first N input vectors (testing)")
    ap.add_argument("--time-budget", type=int, default=0,
                    help="stop cleanly after ~N seconds; progress is cached, rerun to continue (0 = no limit)")
    args = ap.parse_args()
    global DEADLINE
    DEADLINE = time.time() + args.time_budget if args.time_budget else None
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs("results/plots", exist_ok=True)

    print("=" * 70)
    print(f" PART C: 3-bit CLA  ({len(cla3.GATES)} gates, {args.corners} corners x {args.vectors} vectors)")
    print("=" * 70)
    write_example_netlist()
    corners = PB.generate_corners(num_corners=args.corners, seed=args.seed)

    table, load = build_gate_ml_table(corners, args.workers, os.path.join(OUT_DIR, "gate_ml_cache.csv"))

    vectors = cla3.VECTORS[:args.vectors]
    spice_dir = os.path.join(OUT_DIR, "spice_cache")
    os.makedirs(spice_dir, exist_ok=True)
    results = []
    print(f"[*] SPICE: {len(corners) * len(vectors)} full-circuit simulations (cached per corner) ...")
    for ci in range(len(corners)):
        cpath = os.path.join(spice_dir, f"corner_{ci}_v{len(vectors)}.csv")
        if os.path.exists(cpath):
            d = pd.read_csv(cpath)
        else:
            check_time()
            tasks = [(ci, v, corners[ci]) for v in vectors]
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                res = list(pool.map(simulate_circuit, tasks, chunksize=8))
            d = pd.DataFrame([{"corner": c, "vec": v, "leak": lk, "s0": o[0], "s1": o[1], "s2": o[2], "cout": o[3]}
                              for c, v, lk, o in res])
            d.to_csv(cpath, index=False)
            if ci % 20 == 19:
                print(f"    corner {ci + 1}/{len(corners)} done")
        results += [(int(r.corner), int(r.vec), r.leak, [r.s0, r.s1, r.s2, r.cout]) for r in d.itertuples()]

    rows, logic_bad, failed = [], 0, 0
    for ci, vec, leak, outs in results:
        if not np.isfinite(leak) or leak <= 0:
            failed += 1
            continue
        vdd = corners[ci]["vdd"]
        got = sum((1 << k) for k, o in enumerate(outs) if o > vdd / 2)
        if got != cla3.expected_sum(vec):
            logic_bad += 1
        plain, loaded = ml_circuit_leak(table, load, ci, vec)
        rows.append({"corner": ci, "vec": vec, "vdd": vdd, "temp": corners[ci]["temp"],
                     "vth0_n": corners[ci]["nmos"]["vth0"], "spice_leak": leak,
                     "ml_leak": plain, "ml_leak_loading": loaded})
    df = pd.DataFrame(rows)
    df["err_pct"] = np.abs(df.ml_leak - df.spice_leak) / df.spice_leak * 100.0
    df["err_loading_pct"] = np.abs(df.ml_leak_loading - df.spice_leak) / df.spice_leak * 100.0
    df.to_csv(os.path.join(OUT_DIR, "circuit_raw.csv"), index=False)

    gdf = pd.read_csv(os.path.join(OUT_DIR, "gate_ml_cache.csv"), dtype={"inp": str})
    sp_table = {(r.gate, str(r.inp).zfill(1 if r.gate == "INV" else 2), int(r.corner)): r.spice_leak
                for r in gdf.itertuples()}
    df["spice_gate_sum"] = [ml_circuit_leak(sp_table, load, r.corner, r.vec)[0] for r in df.itertuples()]
    chk = metrics(df.spice_leak, df.spice_gate_sum)
    print("SPICE GATE-SUM vs FULL-CIRCUIT SPICE:", {k: f"{v:.4g}" for k, v in chk.items()})

    print(f"[*] SPICE failed/invalid runs: {failed};  SPICE logic mismatches (sanity): {logic_bad}")

    recs = []
    for vec, grp in df.groupby("vec"):
        m = metrics(grp.spice_leak, grp.ml_leak)
        ml2 = metrics(grp.spice_leak, grp.ml_leak_loading)
        recs.append({"vector": f"{vec:07b}", "a": vec & 7, "b": (vec >> 3) & 7, "cin": (vec >> 6) & 1, **m,
                     "ml_loading_median_A": ml2["ml_median_A"], "median_error_loading_pct": ml2["median_error_pct"],
                     "p95_error_loading_pct": ml2["p95_error_pct"]})
    tab = pd.DataFrame(recs)
    tab.to_csv("results/circuit_results_table.csv", index=False)
    overall = metrics(df.spice_leak, df.ml_leak)
    mean_err = float(df.err_pct[df.spice_leak > 1e-13].mean())
    print("\nOVERALL (PLAIN HIERARCHICAL):", {k: f"{v:.4g}" for k, v in overall.items()})
    print(f"mean error = {mean_err:.2f} %  ->  mean accuracy = {100 - mean_err:.2f} %")
    ov2 = metrics(df.spice_leak, df.ml_leak_loading)
    mean_err2 = float(df.err_loading_pct[df.spice_leak > 1e-13].mean())
    print("LOADING-AWARE (WITH FAN-OUT TUNNELING):", {k: f"{v:.4g}" for k, v in ov2.items()})
    print(f"mean error = {mean_err2:.2f} %  ->  mean accuracy = {100 - mean_err2:.2f} %")

    sp = df.spice_leak.values
    for col, ov, me, fname, label in (
            ("ml_leak", overall, mean_err, "circuit_parity_plot.png", "plain hierarchical sum"),
            ("ml_leak_loading", ov2, mean_err2, "circuit_parity_plot_loading.png", "loading-aware")):
        ml = df[col].values
        lo = max(min(sp.min(), ml.min()), 1e-14) * 0.7
        hi = max(sp.max(), ml.max()) * 1.4
        plt.figure(figsize=(7, 6.5))
        plt.scatter(sp, ml, s=4, alpha=0.3, color="darkgreen", label="CLA (corner x vector)")
        plt.plot([lo, hi], [lo, hi], "r--", lw=1.5, label="y = x")
        plt.xscale("log"); plt.yscale("log"); plt.xlim(lo, hi); plt.ylim(lo, hi)
        plt.xlabel("SPICE leakage (A)"); plt.ylabel("ML leakage (A)")
        plt.title(f"Part C parity plot: 3-bit CLA ({label})\nmedian error {ov['median_error_pct']:.2f} %, "
                  f"mean accuracy {100 - me:.2f} %")
        plt.grid(True, which="both", ls="--", alpha=0.5); plt.legend()
        plt.tight_layout()
        plt.savefig(f"results/plots/{fname}", dpi=300)
        plt.close()
    print("\n Deliverable 8 completed successfully!")

if __name__ == "__main__":
    main()
