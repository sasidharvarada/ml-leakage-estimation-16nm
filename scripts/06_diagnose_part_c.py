#!/usr/bin/env python3
"""Part C diagnostics: where does the residual error come from?

Run from the repo root after 05_test_circuit.py:
    python3 scripts/06_diagnose_part_c.py
    python3 scripts/06_diagnose_part_c.py | tee results/part_c/diagnostics.txt
"""
import os
import sys

import pandas as pd

df = pd.read_csv("results/part_c/circuit_raw.csv")
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cla3

gdf = pd.read_csv("results/part_c/gate_ml_cache.csv", dtype={"inp": str})
sp_tab = {(r.gate, str(r.inp).zfill(1 if r.gate == "INV" else 2), int(r.corner)): r.spice_leak
          for r in gdf.itertuples()}


def spice_gate_sum(corner, vec):
    logic = cla3.logic_eval(vec)
    return sum(sp_tab[(t, cla3.pattern([logic[i] for i in ins]), corner)]
               for g, t, ins, out in cla3.GATES)


df["spice_sum"] = [spice_gate_sum(int(r.corner), int(r.vec)) for r in df.itertuples()]
df["err_ctrl_pct"] = (df.spice_sum - df.spice_leak).abs() / df.spice_leak * 100

# Same bin edges as above, applied to the gate-level table.
_, vedges = pd.qcut(df.vth0_n, 4, retbins=True)
gdf["temp"] = gdf.corner.map(df.groupby("corner").temp.first())
gdf["vth0_n"] = gdf.corner.map(df.groupby("corner").vth0_n.first())
gdf["Tbin"] = pd.cut(gdf.temp, [-40, 0, 40, 80, 125], include_lowest=True)
gdf["vthbin"] = pd.cut(gdf.vth0_n, vedges, include_lowest=True)
gdf["gate_err_pct"] = (gdf.ml_leak - gdf.spice_leak).abs() / gdf.spice_leak * 100
gok = gdf[gdf.spice_leak > 1e-13]

for col in ("Tbin", "vthbin"):
    print(f"\n=== Control by {col}: SPICE gate-sum vs full-circuit SPICE (structural gap, percent) ===")
    print(df.groupby(col, observed=True).err_ctrl_pct.agg(["median", "mean"]).round(2))
    print(f"\n=== Gate-level ML vs SPICE by {col} (ML model error on isolated gates, percent) ===")
    print(gok.groupby(col, observed=True).gate_err_pct.agg(["median", "mean"]).round(2))