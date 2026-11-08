#!/usr/bin/env python3
"""Per gate-case ML vs SPICE error, from the Part C gate cache.

Run from the repo root after 05_test_circuit.py:
    python3 scripts/07_gate_breakdown.py
    python3 scripts/07_gate_breakdown.py | tee results/part_c/gate_breakdown.txt
"""
import pandas as pd

pd.set_option("display.width", 120)
pd.set_option("display.float_format", "{:.4g}".format)

g = pd.read_csv("results/part_c/gate_ml_cache.csv", dtype={"inp": str})
g = g[g.spice_leak > 1e-13].copy()
g["err"] = (g.ml_leak - g.spice_leak).abs() / g.spice_leak * 100
g["signed"] = (g.ml_leak - g.spice_leak) / g.spice_leak * 100

print(g.groupby(["gate", "inp"]).agg(
    spice_med=("spice_leak", "median"),
    median=("err", "median"),
    mean=("err", "mean"),
    p95=("err", lambda s: s.quantile(.95)),
    signed=("signed", "median")))

print("\nsigned = median of (ML - SPICE) / SPICE * 100; negative means ML underpredicts.")