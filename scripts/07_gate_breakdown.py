#!/usr/bin/env python3
"""Per gate-case ML vs SPICE error, from the Part B gate results.

Run from the repo root after 04_validate_gates.py:
    python3 scripts/07_gate_breakdown.py                  # default (rail) results
    python3 scripts/07_gate_breakdown.py --no-rail        # results/part_b/no_rail/
    python3 scripts/07_gate_breakdown.py | tee results/part_b/gate_breakdown.txt
"""
import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from variant import out

FLOOR = 1e-13           # runs with gate leakage below this are excluded (shown in the 'dropped' column)

ap = argparse.ArgumentParser()
ap.add_argument("--no-rail", action="store_true", help="read the no_rail/ variant of the results")
args = ap.parse_args()

pd.set_option("display.width", 120)
pd.set_option("display.float_format", "{:.4g}".format)

g = pd.read_csv(os.path.join(out("results/part_b", args.no_rail), "gate_all.csv"), dtype={"inp": str})
g["dropped"] = g.spice_leak <= FLOOR
g["err"] = (g.ml_leak - g.spice_leak).abs() / g.spice_leak * 100
g["signed"] = (g.ml_leak - g.spice_leak) / g.spice_leak * 100
kept = g[~g.dropped]

tab = kept.groupby(["gate", "inp"]).agg(
    n=("err", "size"),
    spice_med=("spice_leak", "median"),
    median=("err", "median"),
    mean=("err", "mean"),
    p95=("err", lambda s: s.quantile(.95)),
    signed=("signed", "median"))
tab.insert(1, "dropped", g.groupby(["gate", "inp"]).dropped.sum().astype(int))
print(tab)

print(f"\nsigned = median of (ML - SPICE) / SPICE * 100; positive means ML overpredicts.")
print(f"dropped = runs with SPICE leakage <= {FLOOR:g} A, excluded from the statistics above.")