import argparse
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cla3
import config as C
import gates as G
from variant import out
from spice_utils import set_params

OUT = "results/part_c"


# SPICE netlist
def gate_fets(g, t, ins, out):
    """Transistors of one CLA gate, with the gate's own node names."""
    m = {"a": ins[0], "b": ins[1] if len(ins) > 1 else None, "out": out,
         "x": f"{g}_x", "y": f"{g}_y", "n_out": f"{g}_n", "vdd": "vdd", "0": "0"}
    return [(f"{g}{name}", kind, m[d], m[gg], m[s], m[b]) for name, kind, d, gg, s, b in G.transistors(t)]


def circuit_deck(corner, vec):
    vdd = corner["vdd"]
    logic = cla3.logic_eval(vec)
    L = [f"* 3-bit CLA, vector {vec:07b} (cin b2 b1 b0 a2 a1 a0 = bit6..bit0)",
         set_params(G.MODELS_TEXT["nmos"], corner["nmos"], "nmos_mod"),
         set_params(G.MODELS_TEXT["pmos"], corner["pmos"], "pmos_mod"),
         f"Vdd vdd 0 DC {vdd:.6f}"]
    for net in cla3.INPUTS:
        L.append(f"V{net} {net} 0 DC {vdd * logic[net]:.6f}")
    ns = []
    for g, t, ins, out in cla3.GATES:
        L += [G.fet_line(*f) for f in gate_fets(g, t, ins, out)]
        pat = cla3.pattern([logic[i] for i in ins])
        local = G.nodeset(t, pat, vdd).replace(".nodeset ", "").split()
        for item in local:
            node, val = re.match(r"v\((\w+)\)=(\S+)", item).groups()
            name = {"out": out, "x": f"{g}_x", "y": f"{g}_y", "n_out": f"{g}_n"}[node]
            ns.append(f"v({name})={val}")
    L.append(".nodeset " + " ".join(ns))
    L.append(C.SPICE_OPTIONS + " itl1=400")
    L.append(f".temp {corner['temp']:.2f}")
    L += [".control", "set numdgt = 10", "op", "let ileak = -i(vdd)", "echo LEAK $&ileak",
          "echo OUTS $&v(s0) $&v(s1) $&v(s2) $&v(cout)", ".endc", ".end"]
    return "\n".join(L) + "\n"


def simulate_circuit(task):
    ci, vec, corner = task
    with tempfile.NamedTemporaryFile("w", suffix=".cir", delete=False) as f:
        f.write(circuit_deck(corner, vec))
        path = f.name
    leak, outs = np.nan, [np.nan] * 4
    try:
        res = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True, timeout=120)
        for line in res.stdout.splitlines():
            if line.startswith("LEAK"):
                m = re.findall(G.NUM, line[4:])
                leak = float(m[0]) if m else np.nan
            elif line.startswith("OUTS"):
                m = re.findall(G.NUM, line[4:])
                if len(m) == 4:
                    outs = [float(x) for x in m]
    except subprocess.TimeoutExpired:
        pass
    finally:
        os.remove(path)
    return ci, vec, leak, outs


# ----------------------------------------------------------------------------- helpers
def metrics(sp, ml):
    sp, ml = np.asarray(sp, float), np.asarray(ml, float)
    rel = np.abs(ml - sp) / np.abs(sp) * 100.0
    return {"spice_median_A": np.median(sp), "ml_median_A": np.median(ml),
            "bias_A": np.median(ml - sp), "bias_pct": np.median((ml - sp) / sp) * 100.0,
            "median_error_pct": np.median(rel), "mean_error_pct": np.mean(rel),
            "p95_error_pct": np.percentile(rel, 95), "mean_accuracy_pct": 100.0 - np.mean(rel)}


def gate_tables(n_corners, path):
    """(gate, pattern, corner) -> values from Part B (ML and SPICE)."""
    df = pd.read_csv(path, dtype={"inp": str})
    tab = {}
    for r in df.itertuples():
        tab[(r.gate, r.inp, int(r.corner))] = r
    missing = [(g, i, c) for g, i in G.GATE_CASES for c in range(n_corners) if (g, i, c) not in tab]
    return tab, missing


def compose(tab, ci, vec, fill):
    """Return plain/loading sums for ML and for SPICE gate results."""
    logic = cla3.logic_eval(vec)
    s = {"ml": 0.0, "ml_load": 0.0, "sp": 0.0, "sp_load": 0.0}
    for g, t, ins, out in cla3.GATES:
        pat = cla3.pattern([logic[i] for i in ins])
        r = tab.get((t, pat, ci)) or fill[(t, pat)]
        s["ml"] += r.ml_leak
        s["sp"] += r.spice_leak
        for k, net in enumerate(ins):
            if net not in cla3.INPUTS and logic[net] == 1:     # internal net driven HIGH
                s["ml_load"] += getattr(r, "ml_pin_" + "ab"[k])
                s["sp_load"] += getattr(r, "pin_" + "ab"[k])
    s["ml_load"] += s["ml"]
    s["sp_load"] += s["sp"]
    return s


def parity(sp, ml, title, path):
    lo, hi = min(sp.min(), ml.min()) * 0.7, max(sp.max(), ml.max()) * 1.4
    plt.figure(figsize=(7, 6.5))
    plt.scatter(sp, ml, s=4, alpha=0.3, color="darkgreen", label="CLA (corner x vector)")
    plt.plot([lo, hi], [lo, hi], "r--", lw=1.5, label="y = x")
    plt.xscale("log"); plt.yscale("log"); plt.xlim(lo, hi); plt.ylim(lo, hi)
    plt.xlabel("SPICE circuit leakage (A)"); plt.ylabel("ML circuit leakage (A)")
    plt.title(title)
    plt.grid(True, which="both", ls="--", alpha=0.5); plt.legend()
    plt.tight_layout(); plt.savefig(path, dpi=200); plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corners", type=int, default=200)
    ap.add_argument("--seed", type=int, default=71, help="must match Part B")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--no-rail", action="store_true",
                    help="read results/part_b/no_rail/gate_all.csv, write to results/part_c/no_rail/")
    args = ap.parse_args()
    res_dir = out(OUT, args.no_rail)      # per-variant outputs; spice_cache stays shared in OUT
    gate_csv = os.path.join(out("results/part_b", args.no_rail), "gate_all.csv")
    os.makedirs(res_dir, exist_ok=True)
    os.makedirs("netlists/circuit", exist_ok=True)

    corners = G.generate_corners(args.corners, args.seed)
    nominal = {"vdd": 1.0, "temp": 27.0, "nmos": G._NOM["nmos"], "pmos": G._NOM["pmos"]}
    with open("netlists/circuit/cla3.sp", "w") as f:
        f.write(circuit_deck(nominal, 0b1010101))
    print(f"PART C: 3-bit CLA ({len(cla3.GATES)} gates), {args.corners} corners x 128 vectors")

    # ---- SPICE (cached per corner)
    cache = os.path.join(OUT, "spice_cache")
    os.makedirs(cache, exist_ok=True)
    spice = []
    todo = [ci for ci in range(len(corners)) if not os.path.exists(os.path.join(cache, f"corner_{ci}_v128.csv"))]
    if todo:
        print(f"[*] SPICE: {len(todo) * 128} full-circuit simulations ...", flush=True)
    for ci in range(len(corners)):
        path = os.path.join(cache, f"corner_{ci}_v128.csv")
        if not os.path.exists(path):
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                res = list(pool.map(simulate_circuit, [(ci, v, corners[ci]) for v in cla3.VECTORS], chunksize=8))
            pd.DataFrame([{"corner": c, "vec": v, "leak": lk, "s0": o[0], "s1": o[1], "s2": o[2], "cout": o[3]}
                          for c, v, lk, o in res]).to_csv(path, index=False)
        spice.append(pd.read_csv(path))
    spice = pd.concat(spice, ignore_index=True)

    # ---- gate tables from Part B
    tab, missing = gate_tables(len(corners), gate_csv)
    fill = {}
    allg = pd.read_csv(gate_csv, dtype={"inp": str})
    for (g, i), grp in allg.groupby(["gate", "inp"]):
        fill[(g, i)] = grp.median(numeric_only=True)   # used only if a Part B run failed
        fill[(g, i)] = type("R", (), dict(fill[(g, i)]))
    if missing:
        print(f"[!] {len(missing)} gate cases missing from Part B (failed SPICE); using that case's median")

    rows, failed, logic_bad = [], 0, 0
    for r in spice.itertuples():
        ci, vec = int(r.corner), int(r.vec)
        if not np.isfinite(r.leak) or r.leak <= 0:
            failed += 1
            continue
        vdd = corners[ci]["vdd"]
        got = sum((1 << k) for k, o in enumerate([r.s0, r.s1, r.s2, r.cout]) if o > vdd / 2)
        logic_bad += int(got != cla3.expected_sum(vec))
        s = compose(tab, ci, vec, fill)
        rows.append({"corner": ci, "vec": vec, "vdd": vdd, "temp": corners[ci]["temp"],
                     "vth0_n": corners[ci]["nmos"]["vth0"], "vth0_p": corners[ci]["pmos"]["vth0"],
                     "spice_leak": r.leak, "ml_leak": s["ml"], "ml_leak_loading": s["ml_load"],
                     "spice_gate_sum": s["sp"], "spice_gate_sum_loading": s["sp_load"]})
    df = pd.DataFrame(rows)
    for col, src in (("err_pct", "ml_leak"), ("err_loading_pct", "ml_leak_loading")):
        df[col] = np.abs(df[src] - df.spice_leak) / df.spice_leak * 100.0
    df.to_csv(os.path.join(res_dir, "circuit_raw.csv"), index=False)
    print(f"[*] SPICE failed runs: {failed};  SPICE logic mismatches (sanity check): {logic_bad}")

    # ---- tables
    recs = []
    for vec, grp in df.groupby("vec"):
        m1 = metrics(grp.spice_leak, grp.ml_leak)
        m2 = metrics(grp.spice_leak, grp.ml_leak_loading)
        recs.append({"vector": f"{vec:07b}", "a": vec & 7, "b": (vec >> 3) & 7, "cin": (vec >> 6) & 1,
                     **m1, **{k + "_loading": v for k, v in m2.items() if k != "spice_median_A"}})
    pd.DataFrame(recs).to_csv(os.path.join(res_dir, "circuit_results_table.csv"), index=False, float_format="%.5g")

    summary = pd.DataFrame([
        {"method": "ML plain sum (project method)", **metrics(df.spice_leak, df.ml_leak)},
        {"method": "ML loading-aware", **metrics(df.spice_leak, df.ml_leak_loading)},
        {"method": "SPICE gate sum (no ML), plain", **metrics(df.spice_leak, df.spice_gate_sum)},
        {"method": "SPICE gate sum (no ML), loading-aware", **metrics(df.spice_leak, df.spice_gate_sum_loading)},
    ])
    summary.to_csv(os.path.join(res_dir, "circuit_summary.csv"), index=False, float_format="%.5g")
    pd.set_option("display.width", 220)
    print("\nDELIVERABLE 8: CIRCUIT SUMMARY")
    print(summary.to_string(index=False, float_format=lambda v: f"{v:.4g}"))

    for col, name, fname in (("ml_leak", "plain gate-leakage sum", "circuit_parity_plot.png"),
                             ("ml_leak_loading", "loading-aware sum", "circuit_parity_plot_loading.png")):
        m = metrics(df.spice_leak, df[col])
        parity(df.spice_leak.values, df[col].values,
               f"3-bit CLA parity plot ({name})\nmedian error {m['median_error_pct']:.2f} %, "
               f"mean accuracy {m['mean_accuracy_pct']:.2f} %", os.path.join(OUT, fname))
    print("\nSaved results/part_c/circuit_results_table.csv, circuit_summary.csv and the parity plots")


if __name__ == "__main__":
    main()
