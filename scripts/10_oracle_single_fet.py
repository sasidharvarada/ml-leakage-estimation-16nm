#!/usr/bin/env python3
"""Oracle test, SPICE only (no ML): which single-FET terminal currents add up to a gate's Vdd current?

For each gate case and corner it takes the SPICE node voltages (as Part B does), runs each PMOS
of the gate as a single-FET SPICE netlist at exactly that bias (same netlist builder as
01_generate_data.py), and compares ways of combining the true terminal currents against the
full-gate SPICE leakage:

  id_formula   sum of |Id| of the devices the current predict_gate_leakage uses
  kcl          | sum(Is of PMOS whose source is on Vdd) + sum(Ib of every PMOS) |   (signed)
  kcl_abs      sum(|Is| of source-on-Vdd PMOS) + sum(|Ib| of every PMOS)           (magnitudes)

Reading the result:
  - kcl within a couple of percent: the Vdd current really is source + body current, the single-FET
    netlist matches the gate netlist, and |Id| is the wrong quantity (it includes gate-edge
    tunneling supplied by the input source, not Vdd).
  - kcl far off: the single-FET and gate netlists differ (e.g. junction geometry AD/AS/PD/PS),
    which must be fixed in the data generation before any retrain.

Run from the repo root (reads and writes nothing except stdout):
    python3 scripts/10_oracle_single_fet.py | tee results/part_c/oracle_single_fet.txt
"""
import os
import sys
import importlib.util
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config as C
from spice_utils import set_params, build_netlist, run_ngspice


def load_part_b():
    spec = importlib.util.spec_from_file_location("part_b", os.path.join(HERE, "04_simulate_gates.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["part_b"] = mod
    spec.loader.exec_module(mod)
    return mod


PB = load_part_b()
WP = PB.WP
PMOS_TYPE = C.CASES["pmos_off"]["type"]
CARD = PB.MODELS_TEXT[PMOS_TYPE]

# (gate, input) cases: the four broken ones plus INV 0 as a healthy control (KCL columns only)
CASES = [("INV", "1"), ("NAND2", "11"), ("NOR2", "10"), ("NOR2", "11"), ("INV", "0")]


def pmos_devices(gate, inp, vdd, nv):
    """PMOS devices as (vd, vs, vg, source_on_vdd, used_by_formula)."""
    out, y = nv["out"], nv["y"]
    if (gate, inp) == ("INV", "1"):
        return [(out, vdd, vdd, True, True)]
    if (gate, inp) == ("INV", "0"):
        return [(out, vdd, 0.0, True, False)]
    if (gate, inp) == ("NAND2", "11"):
        return [(out, vdd, vdd, True, True), (out, vdd, vdd, True, True)]
    if (gate, inp) == ("NOR2", "10"):
        return [(y, vdd, vdd, True, True), (out, y, 0.0, False, False)]
    if (gate, inp) == ("NOR2", "11"):
        return [(y, vdd, vdd, True, True), (out, y, vdd, False, False)]
    raise ValueError((gate, inp))


def fet_currents(task):
    params, w, vd, vg, vs, vb, temp = task
    card = set_params(CARD, params, "mdev")
    net = build_netlist(card, PMOS_TYPE, w, C.LMIN, vd, vg, vs, vb, temp, C.SPICE_OPTIONS)
    try:
        return run_ngspice(net)  # (id, ig, is, ib)
    except Exception:
        return (np.nan,) * 4


def stats(sp, ml, temp):
    sp, ml, temp = map(np.asarray, (sp, ml, temp))
    ok = np.isfinite(ml) & (sp > 1e-16)
    rel = np.abs(ml[ok] - sp[ok]) / sp[ok] * 100.0
    hot = temp[ok] > 80
    return (np.median(rel), np.percentile(rel, 95),
            np.median(rel[hot]) if hot.any() else np.nan, int(ok.sum()))


def main():
    pd.set_option("display.width", 160)
    pd.set_option("display.float_format", "{:.4g}".format)
    corners = PB.generate_corners(num_corners=200, seed=123)
    workers = os.cpu_count()
    rows = []

    for gate, inp in CASES:
        print(f"[*] {gate} {inp}: gate SPICE + single-FET SPICE over {len(corners)} corners ...", flush=True)
        with ProcessPoolExecutor(max_workers=workers) as pool:
            sims = list(pool.map(PB.simulate_gate_spice, [(gate, inp, c) for c in corners]))

        tasks, owner = [], []
        for ci, (c, (leak, nv)) in enumerate(zip(corners, sims)):
            if leak <= 0:
                continue
            for vd, vs, vg, src, inf in pmos_devices(gate, inp, c["vdd"], nv):
                tasks.append((c["pmos"], WP, vd, vg, vs, c["vdd"], c["temp"]))
                owner.append((ci, src, inf))
        with ProcessPoolExecutor(max_workers=workers) as pool:
            res = list(pool.map(fet_currents, tasks, chunksize=8))

        acc = {}
        for (ci, src, inf), (id_, ig_, is_, ib_) in zip(owner, res):
            d = acc.setdefault(ci, {"id_formula": 0.0, "has_formula": False, "is_vdd": 0.0,
                                    "ib_all": 0.0, "kcl_abs": 0.0})
            if inf:
                d["id_formula"] += abs(id_)
                d["has_formula"] = True
            if src:
                d["is_vdd"] += is_
                d["kcl_abs"] += abs(is_)
            d["ib_all"] += ib_
            d["kcl_abs"] += abs(ib_)

        idx = sorted(acc)
        sp = [sims[i][0] for i in idx]
        temp = [corners[i]["temp"] for i in idx]
        cands = {"kcl": [abs(acc[i]["is_vdd"] + acc[i]["ib_all"]) for i in idx],
                 "kcl_abs": [acc[i]["kcl_abs"] for i in idx]}
        if acc[idx[0]]["has_formula"]:
            cands = {"id_formula": [acc[i]["id_formula"] for i in idx], **cands}
        for name, vals in cands.items():
            med, p95, hot, n = stats(sp, vals, temp)
            rows.append({"case": f"{gate} {inp}", "n": n, "spice_median_A": float(np.median(sp)),
                         "candidate": name, "median_err%": med, "p95_err%": p95, "hot_median_err%": hot})

    print()
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nErrors are |candidate - gate SPICE leakage| / gate SPICE leakage, in percent, over corners")
    print("with gate leakage above 1e-16 A. hot = temperature above 80 C.")


if __name__ == "__main__":
    main()