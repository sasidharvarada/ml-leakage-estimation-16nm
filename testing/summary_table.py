#!/usr/bin/env python3
"""Final tables: training / validation / test error (and accuracy) per case and current,
fresh (unseen) test-case error, and gate / CLA results at new corners.
Run after testing/01_check_overfit.py and testing/03_test_cases.py:
    python testing/summary_table.py
Also written to testing/results/FINAL_TABLES.md
"""
import os

import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = "testing/results"
pd.set_option("display.width", 250)
out = ["# Final testing tables", ""]


def show(title, df):
    print(f"\n=== {title}\n" + df.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    cols = list(df.columns)
    out.extend([f"## {title}", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)])
    for r in df.itertuples(index=False):
        out.append("| " + " | ".join(f"{v:.3f}" if isinstance(v, float) else str(v) for v in r) + " |")
    out.append("")


c = f"{R}/overfit/data_counts.csv"
if os.path.exists(c):
    show("Data points per case (project: 7,000 / 1,500 / 1,500)", pd.read_csv(c))

fresh = None
f = f"{R}/test_cases/transistor_fresh_summary.csv"
if os.path.exists(f):
    fresh = pd.read_csv(f)

for v in ("rail", "no_rail"):
    f = f"{R}/overfit/fit_verdict_{v}.csv"
    if not os.path.exists(f):
        continue
    d = pd.read_csv(f)
    t = pd.DataFrame({"case": d.case, "current": d.current, "model": d.model,
                      "train_err_%": d["train_med_%"], "val_err_%": d["val_med_%"], "test_err_%": d["test_med_%"]})
    if fresh is not None:
        fr = fresh[(fresh.variant == v) & (fresh.test_set == "uniform")][["case", "current", "median_err_%"]]
        t = t.merge(fr.rename(columns={"median_err_%": "new_cases_err_%"}), on=["case", "current"], how="left")
    t["train_acc_%"] = 100 - t["train_err_%"]
    t["val_acc_%"] = 100 - t["val_err_%"]
    t["test_acc_%"] = 100 - t["test_err_%"]
    t["verdict"] = d.verdict.str.replace(r" \(noise.*", " (noise-level)", regex=True)
    show(f"Models '{v}': median error and accuracy (100 - median error)", t)

for f in sorted(os.listdir(f"{R}/test_cases")) if os.path.isdir(f"{R}/test_cases") else []:
    if f.startswith("gates_cla_seed") and f.endswith("_summary.csv"):
        show("Gates and CLA at NEW random corners (" + f.split("_")[2] + ")", pd.read_csv(f"{R}/test_cases/{f}"))

print("\nReference (official seed 123, 200 corners): gates 0.88 % median error, 99.04 % mean accuracy "
      "(16 regular cases); CLA plain sum 67.91 %, loading-aware 99.01 % mean accuracy.")
os.makedirs(R, exist_ok=True)
with open(f"{R}/FINAL_TABLES.md", "w") as fh:
    fh.write("\n".join(out) + "\n")
print(f"\nSaved {R}/FINAL_TABLES.md")
