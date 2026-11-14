import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gates as G
from variant import out

OUT = "results/part_b"


def metrics(sp, ml):
    sp, ml = np.asarray(sp, float), np.asarray(ml, float)
    rel = np.abs(ml - sp) / np.abs(sp) * 100.0
    return {"spice_median_A": np.median(sp), "ml_median_A": np.median(ml),
            "bias_A": np.median(ml - sp), "bias_pct": np.median((ml - sp) / sp) * 100.0,
            "median_error_pct": np.median(rel), "mean_error_pct": np.mean(rel),
            "p95_error_pct": np.percentile(rel, 95), "mean_accuracy_pct": 100.0 - np.mean(rel)}


def run_spice(corners, workers, path):
    if os.path.exists(path):
        df = pd.read_csv(path, dtype={"inp": str})
        if len(df) == 18 * len(corners):
            print(f"[*] using cached gate SPICE results: {path}")
            return df
    tasks = [(g, i, ci, c) for g, i in G.GATE_CASES for ci, c in enumerate(corners)]
    print(f"[*] SPICE: {len(tasks)} gate simulations ...", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        recs = list(pool.map(G.simulate_gate, tasks, chunksize=16))
    df = pd.DataFrame(recs)
    df.to_csv(path, index=False)
    return df


def write_example_netlists():
    os.makedirs("netlists/gates", exist_ok=True)
    nominal = {"vdd": 1.0, "temp": 27.0, "nmos": G._NOM["nmos"], "pmos": G._NOM["pmos"]}
    for gate in ["INV", "NAND2", "NOR2", "AND2", "OR2"]:
        inp = "0" if gate == "INV" else "01"
        with open(f"netlists/gates/{gate.lower()}.sp", "w") as f:
            f.write(G.gate_deck(gate, inp, nominal))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corners", type=int, default=200)
    ap.add_argument("--seed", type=int, default=71)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--no-rail", action="store_true",
                    help="use saved_models/no_rail/ and write to results/part_b/no_rail/")
    args = ap.parse_args()
    res_dir = out(OUT, args.no_rail)      # per-variant outputs; gate_spice.csv stays shared in OUT
    os.makedirs(res_dir, exist_ok=True)
    write_example_netlists()

    corners = G.generate_corners(args.corners, args.seed)
    sp = run_spice(corners, args.workers, os.path.join(OUT, "gate_spice.csv"))

    bad = sp["spice_leak"].isna() | (sp["spice_leak"] <= 0)
    print(f"[*] SPICE runs failed / non-positive: {int(bad.sum())} of {len(sp)}")

    ev = G.GateEvaluator(model_dir=out("saved_models", args.no_rail), use_rail=not args.no_rail)
    frames = []
    for gate, inp in G.GATE_CASES:
        part = sp[(sp.gate == gate) & (sp.inp == inp) & ~bad].copy()
        rows = []
        for r in part.to_dict("records"):
            c = corners[int(r["corner"])]
            rows.append({**r, "vdd": c["vdd"], "temp": c["temp"], "nmos": c["nmos"], "pmos": c["pmos"]})
        ml = ev.evaluate(gate, inp, rows)
        part[["ml_leak", "ml_pin_a", "ml_pin_b"]] = ml[["ml_leak", "ml_pin_a", "ml_pin_b"]].values
        part["vdd"] = [corners[int(c)]["vdd"] for c in part.corner]
        part["temp"] = [corners[int(c)]["temp"] for c in part.corner]
        part["err_pct"] = np.abs(part.ml_leak - part.spice_leak) / part.spice_leak * 100.0
        frames.append(part)
    allg = pd.concat(frames, ignore_index=True)
    allg.to_csv(os.path.join(res_dir, "gate_all.csv"), index=False)

    table = pd.DataFrame([{"gate": g, "input": i,
                           **metrics(allg[(allg.gate == g) & (allg.inp == i)].spice_leak,
                                     allg[(allg.gate == g) & (allg.inp == i)].ml_leak)}
                          for g, i in G.GATE_CASES])
    table.to_csv(os.path.join(res_dir, "gate_results_table.csv"), index=False, float_format="%.5g")
    overall = metrics(allg.spice_leak, allg.ml_leak)

    pd.set_option("display.width", 200)
    print("\nDELIVERABLE 6: GATE RESULTS TABLE")
    print(table.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    print("\nOVERALL (all gate runs):", {k: f"{v:.4g}" for k, v in overall.items()})

    s, m = allg.spice_leak.values, allg.ml_leak.values
    lo, hi = min(s.min(), m[m > 0].min()) * 0.5, max(s.max(), m.max()) * 2
    plt.figure(figsize=(7, 6.5))
    for g in ["INV", "NAND2", "NOR2", "AND2", "OR2"]:
        k = allg.gate == g
        plt.scatter(s[k], np.clip(m[k], lo, None), s=6, alpha=0.4, label=g)
    plt.plot([lo, hi], [lo, hi], "r--", lw=1.2, label="y = x")
    plt.xscale("log"); plt.yscale("log"); plt.xlim(lo, hi); plt.ylim(lo, hi)
    plt.xlabel("SPICE gate leakage (A)"); plt.ylabel("ML gate leakage (A)")
    plt.title(f"Gate parity plot (18 cases x {args.corners} corners)\n"
              f"median error {overall['median_error_pct']:.2f} %, mean accuracy {overall['mean_accuracy_pct']:.2f} %")
    plt.grid(True, which="both", ls="--", alpha=0.4); plt.legend()
    plt.tight_layout(); plt.savefig(os.path.join(res_dir, "gate_parity_plot.png"), dpi=200); plt.close()
    print("\nSaved results/part_b/gate_results_table.csv and results/part_b/gate_parity_plot.png")


if __name__ == "__main__":
    main()
