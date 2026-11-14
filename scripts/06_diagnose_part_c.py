#!/usr/bin/env python3
"""Part C diagnostics: where does the residual error come from?

Run from the repo root after 05_validate_circuit.py:
    python3 scripts/06_diagnose_part_c.py                  # default (rail) results
    python3 scripts/06_diagnose_part_c.py --no-rail        # results/part_b|c/no_rail/
    python3 scripts/06_diagnose_part_c.py | tee results/part_c/diagnostics.txt

Reads results/part_c/circuit_raw.csv and results/part_b/gate_all.csv only.
"""
import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from variant import out

GATE_FLOOR = 1e-13      # gate cases below this leakage are excluded from the gate-level control

ap = argparse.ArgumentParser()
ap.add_argument("--no-rail", action="store_true", help="read the no_rail/ variant of the results")
args = ap.parse_args()

df = pd.read_csv(os.path.join(out("results/part_c", args.no_rail), "circuit_raw.csv"))
df["signed"] = (df.ml_leak_loading - df.spice_leak) / df.spice_leak * 100
df["Tbin"] = pd.cut(df.temp, [-40, 0, 40, 80, 125], include_lowest=True)
df["vthbin"] = pd.qcut(df.vth0_n, 4)

pd.set_option("display.width", 120)

for col in ("Tbin", "vthbin"):
    print(f"\n=== Loading-aware error by {col} (percent) ===")
    print(df.groupby(col, observed=True).agg(
        n=("err_loading_pct", "size"),
        median=("err_loading_pct", "median"),
        mean=("err_loading_pct", "mean"),
        p95=("err_loading_pct", lambda s: s.quantile(.95)),
        signed=("signed", "median")).round(2))

    print(f"\n=== Plain hierarchical error by {col} (percent), for comparison ===")
    print(df.groupby(col, observed=True).agg(
        median=("err_pct", "median"),
        mean=("err_pct", "mean"),
        p95=("err_pct", lambda s: s.quantile(.95))).round(2))

print("\nsigned = median of (ML - SPICE) / SPICE * 100; negative means ML underpredicts.")

# ---------------------------------------------------------------------------
# Control: is the hot / low-vth0 error structural or does it come from the ML models?
#   (a) SPICE gate-sum vs full-circuit SPICE  -> structural gap, no ML involved
#   (b) gate-level ML vs SPICE (isolated gates) -> ML model error by bin
# ---------------------------------------------------------------------------
df["err_ctrl_pct"] = (df.spice_gate_sum - df.spice_leak).abs() / df.spice_leak * 100
df["err_ctrl_loading_pct"] = (df.spice_gate_sum_loading - df.spice_leak).abs() / df.spice_leak * 100

gdf = pd.read_csv(os.path.join(out("results/part_b", args.no_rail), "gate_all.csv"), dtype={"inp": str})
# Same bin edges as above, applied to the gate-level table (temp is already in gate_all.csv).
_, vedges = pd.qcut(df.vth0_n, 4, retbins=True)
gdf["vth0_n"] = gdf.corner.map(df.groupby("corner").vth0_n.first())
gdf["Tbin"] = pd.cut(gdf.temp, [-40, 0, 40, 80, 125], include_lowest=True)
gdf["vthbin"] = pd.cut(gdf.vth0_n, vedges, include_lowest=True)
gdf["gate_err_pct"] = (gdf.ml_leak - gdf.spice_leak).abs() / gdf.spice_leak * 100
gok = gdf[gdf.spice_leak > GATE_FLOOR]
print(f"\n(gate-level control: {len(gdf) - len(gok)} of {len(gdf)} gate runs below {GATE_FLOOR:g} A excluded)")

for col in ("Tbin", "vthbin"):
    print(f"\n=== Control by {col}: SPICE gate-sum vs full-circuit SPICE, plain (structural gap, percent) ===")
    print(df.groupby(col, observed=True).err_ctrl_pct.agg(["median", "mean"]).round(2))
    print(f"\n=== Control by {col}: SPICE gate-sum vs full-circuit SPICE, loading-aware (no ML, percent) ===")
    print(df.groupby(col, observed=True).err_ctrl_loading_pct.agg(["median", "mean"]).round(4))
    print(f"\n=== Gate-level ML vs SPICE by {col} (ML model error on isolated gates, percent) ===")
    print(gok.groupby(col, observed=True).gate_err_pct.agg(["median", "mean"]).round(2))