#!/usr/bin/env python3
"""Component audit for the four broken gate cases (INV 1, NAND2 11, NOR2 10, NOR2 11).

Question: is the error in the transistor models, or in how predict_gate_leakage
assembles gate leakage from them?

For each case and corner it takes the SPICE node voltages (as Part B does), asks the
existing ML models for all four terminal-current magnitudes of each PMOS, and compares
several ways of assembling the Vdd current against SPICE:

  formula          the current predict_gate_leakage output (|Id| of the OFF PMOS)
  is_only          |Is| of PMOS whose source is on Vdd
  is_plus_ib       |Is| of PMOS whose source is on Vdd + |Ib| of every PMOS (bodies tie to Vdd)
  formula_plus_ib  current formula + |Ib| of every PMOS

Run from the repo root, no retraining and no changes to other scripts:
    python3 scripts/08_component_audit.py
    python3 scripts/08_component_audit.py | tee results/part_c/component_audit.txt
"""
import os
import sys
import importlib.util
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


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
WP = PB.WP

CASES = [("INV", "1"), ("NAND2", "11"), ("NOR2", "10"), ("NOR2", "11")]
CANDIDATES = ("formula", "is_only", "is_plus_ib", "formula_plus_ib")


def pmos_devices(gate, inp, vdd, nv):
    """PMOS devices of the gate as (vd, vs, vg, source_is_on_vdd)."""
    out, y = nv["out"], nv["y"]
    if gate == "INV":
        return [(out, vdd, vdd, True)]
    if gate == "NAND2":
        return [(out, vdd, vdd, True), (out, vdd, vdd, True)]
    if gate == "NOR2" and inp == "10":
        return [(y, vdd, vdd, True), (out, y, 0.0, False)]
    if gate == "NOR2" and inp == "11":
        return [(y, vdd, vdd, True), (out, y, vdd, False)]
    raise ValueError((gate, inp))


def audit_one(ev, gate, inp, corner, nv):
    vdd = corner["vdd"]
    terms = []
    for vd, vs, vg, src_on_vdd in pmos_devices(gate, inp, vdd, nv):
        case = "pmos_off" if vg > vdd / 2 else "pmos_on"
        i = ev.predict_fet(case, vdd, corner["temp"], WP, vd, vs, vg, vdd, corner["pmos"])
        terms.append((src_on_vdd, i))  # i = [|Id|, |Ig|, |Is|, |Ib|]
    is_vdd = sum(i[2] for s, i in terms if s)
    ib_all = sum(i[3] for s, i in terms)
    formula = ev.predict_gate_leakage(gate, inp, corner, nv)
    return {"formula": formula, "is_only": is_vdd,
            "is_plus_ib": is_vdd + ib_all, "formula_plus_ib": formula + ib_all}


def stats(sp, ml):
    sp, ml = np.asarray(sp), np.asarray(ml)
    ok = sp > 1e-13
    signed = (ml[ok] - sp[ok]) / sp[ok] * 100.0
    rel = np.abs(signed)
    return np.median(rel), np.percentile(rel, 95), np.median(signed)


def main():
    pd.set_option("display.width", 120)
    pd.set_option("display.float_format", "{:.4g}".format)
    corners = PB.generate_corners(num_corners=200, seed=123)
    ev = PB.GateMLEvaluator()

    rows = []
    for gate, inp in CASES:
        print(f"[*] {gate} {inp}: SPICE + ML audit over {len(corners)} corners ...", flush=True)
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
            sims = list(pool.map(PB.simulate_gate_spice, [(gate, inp, c) for c in corners]))
        sp = []
        cand = {k: [] for k in CANDIDATES}
        for c, (leak, nv) in zip(corners, sims):
            if leak <= 0:
                continue
            res = audit_one(ev, gate, inp, c, nv)
            sp.append(leak)
            for k in CANDIDATES:
                cand[k].append(res[k])
        for k in CANDIDATES:
            med, p95, sgn = stats(sp, cand[k])
            rows.append({"case": f"{gate} {inp}", "spice_median_A": float(np.median(sp)),
                         "candidate": k, "median_err_pct": med, "p95_err_pct": p95, "signed_median_pct": sgn})

    print()
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nsigned = median of (ML - SPICE) / SPICE * 100; negative means ML underpredicts.")
    print("All candidates use magnitudes only (the models predict log10|I|), so a candidate that")
    print("assumes the wrong current direction will overpredict.")


if __name__ == "__main__":
    main()