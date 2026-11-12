"""Part A data check: Kirchhoff check per case + the 3 trend plots.

Usage (from the repo root):  python scripts/02_check_data.py
Output: results/part_a/kcl_check.csv and results/part_a/plots/*.png
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import config as C

os.makedirs("results/part_a/plots", exist_ok=True)
data = {c: pd.read_csv(f"data/{c}.csv") for c in C.CASES if os.path.exists(f"data/{c}.csv")}

# 1. Kirchhoff check: id + ig + is + ib should be ~0
rows = []
for case, df in data.items():
    total = df[["id", "ig", "is", "ib"]].sum(axis=1).abs()
    largest = df[["id", "ig", "is", "ib"]].abs().max(axis=1)
    rel = total / largest
    rows.append({"case": case, "rows": len(df),
                 "max_abs_sum_A": total.max(),
                 "median_rel_error": rel.median(),
                 "max_rel_error": rel.max()})
kcl = pd.DataFrame(rows)
kcl.to_csv("results/part_a/kcl_check.csv", index=False)
print("Kirchhoff check (sum of terminal currents):")
print(kcl.to_string(index=False))


def trend(ax, df, x, y, title, xlabel):
    ax.scatter(df[x], df[y].abs(), s=3, alpha=0.4)
    ax.set_yscale("log")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(f"|{y}| (A)")
    ax.set_title(title)
    ax.grid(True, which="both", alpha=0.3)


# 2. OFF current vs temperature, 3. OFF current vs vth0, 4. gate current vs toxe
plots = [
    ("off_current_vs_temp.png", "id", "temp", "OFF drain current vs temperature", "Temperature (degC)"),
    ("off_current_vs_vth0.png", "id", "vth0", "OFF drain current vs vth0", "vth0 (V)"),
    ("gate_current_vs_toxe.png", "ig", "toxe", "Gate current vs toxe", "toxe (m)"),
]
for fname, y, x, title, xlabel in plots:
    cases = ["nmos_off", "pmos_off"] if y == "id" else ["nmos_on", "pmos_on"]
    cases = [c for c in cases if c in data]
    fig, axes = plt.subplots(1, len(cases), figsize=(5 * len(cases), 4), squeeze=False)
    for ax, c in zip(axes[0], cases):
        trend(ax, data[c], x, y, f"{title} ({c})", xlabel)
    fig.tight_layout()
    fig.savefig(f"results/part_a/plots/{fname}", dpi=150)
    plt.close(fig)
    print("saved results/part_a/plots/" + fname)
