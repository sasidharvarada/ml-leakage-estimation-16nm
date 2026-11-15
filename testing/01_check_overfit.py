#!/usr/bin/env python3
"""Over-fit / under-fit check of the SAVED transistor models (no re-training, a few minutes).

Run from the repo root:
    python testing/01_check_overfit.py              # rail and no_rail models (whichever exist)
    python testing/01_check_overfit.py --variant rail

For every case and current it rebuilds the exact train / validation / test split used in
training (seed 7, 70/15/15) and reports, for each split:
    loss   = mean squared error of log10|I|   (the quantity the regressors minimise)
    R2 of log10|I|, median and 95th-percentile relative error, sign accuracy.

How to read it
    loss_99% = the same loss over the best 99 % of points. A current that passes through zero
               (|I| -> 0) can be many decades off in log space; a single such point can dominate the
               plain mean, so the verdict uses the median error and loss_99%.
    good fit   : train, validation and test errors are close
    over-fit   : validation/test median error more than 2x the training error (and > 1 point worse)
    under-fit  : median error above 5 % even on the training data
    noise-level: median |I| below 1 fA (simulator noise floor), not meaningful

Outputs (testing/results/overfit/)
    data_counts.csv               rows per split vs the project text (7,000 / 1,500 / 1,500)
    loss_table_<variant>.csv      every case x current x split
    fit_verdict_<variant>.csv     one row per case x current: train / val / test loss and verdict
    summary.md                    the same tables in markdown (for the README / report)
"""
import argparse

import numpy as np
import pandas as pd

from common import CASES, NOISE_FLOOR, TARGETS, TransistorModel, md_table, save, scores, splits, variants


def verdict(tr, va, te, med_abs):
    worst = max(va["median_err_pct"], te["median_err_pct"])
    if tr["median_err_pct"] > 5.0:
        v = "UNDER-FIT"
    elif worst > 2.0 * tr["median_err_pct"] and worst - tr["median_err_pct"] > 1.0:
        v = "OVER-FIT"
    elif worst > 1.5 * tr["median_err_pct"] and worst - tr["median_err_pct"] > 0.5:
        v = "slight gap"
    else:
        v = "good fit"
    if v != "good fit" and med_abs < NOISE_FLOOR:
        v += " (noise-level current < 1 fA, not meaningful)"
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="both", choices=["both", "rail", "no_rail"])
    args = ap.parse_args()

    md = ["# Over-fit / under-fit check of the saved transistor models", "",
          "Loss = mean squared error of log10|I| (decades^2), the quantity the regressors are trained on; "
          "loss_99% leaves out the worst 1 % of points (currents passing through zero). "
          "Errors are |pred - SPICE| / |SPICE|. Verdict: over-fit if validation/test median error is more "
          "than 2x the training error and more than 1 point worse; under-fit if training median error > 5 %.", ""]

    # ---- data counts
    counts = []
    for case in CASES:
        s = splits(case, use_rail=True)
        counts.append({"case": case, "dataset_rows": sum(len(s[k]) for k in ("train", "validation", "test")),
                       "train": len(s["train"]), "validation": len(s["validation"]), "test": len(s["test"]),
                       "spec_train/val/test": "7000/1500/1500",
                       "rail_rows_extra": len(s.get("train_rail", [])) + len(s.get("test_rail", [])),
                       "train_total_rail_variant": len(s["train"]) + len(s.get("train_rail", [])),
                       "train_total_no_rail_variant": len(s["train"])})
    counts = pd.DataFrame(counts)
    print("\n=== Data points per case\n" + counts.to_string(index=False))
    save(counts, "overfit", "data_counts.csv")
    md += ["## Data points per case", "", md_table(counts), ""]

    for vname, mdir in variants(args.variant):
        rows, verdicts = [], []
        for case in CASES:
            model = TransistorModel.load(f"{mdir}/{case}.joblib")
            s = splits(case, use_rail=True)
            if vname != "rail":
                s.pop("train_rail", None)     # not used to train the no-rail models; test_rail stays (unseen)
            pred = {k: model.predict(d) for k, d in s.items()}
            sc = {k: {t: scores(s[k][t].values, pred[k][t].values) for t in TARGETS}
                  for k in s}
            for k in s:
                for t in TARGETS:
                    rows.append({"variant": vname, "case": case, "current": t, "split": k,
                                 "rows": len(s[k]), "model": model.model_type[t], **sc[k][t]})
            for t in TARGETS:
                tr, va, te = sc["train"][t], sc["validation"][t], sc["test"][t]
                verdicts.append({
                    "case": case, "current": t, "model": model.model_type[t],
                    "train_loss": tr["loss_mse_log10"], "val_loss": va["loss_mse_log10"],
                    "test_loss": te["loss_mse_log10"],
                    "train_loss_99%": tr["loss_mse_log10_trim1"], "val_loss_99%": va["loss_mse_log10_trim1"],
                    "test_loss_99%": te["loss_mse_log10_trim1"],
                    "train_med_%": tr["median_err_pct"], "val_med_%": va["median_err_pct"],
                    "test_med_%": te["median_err_pct"],
                    "rail_test_med_%": sc["test_rail"][t]["median_err_pct"] if "test_rail" in sc else np.nan,
                    "verdict": verdict(tr, va, te, te["median_abs_I_A"])})
        rows, verdicts = pd.DataFrame(rows), pd.DataFrame(verdicts)
        save(rows, "overfit", f"loss_table_{vname}.csv")
        save(verdicts, "overfit", f"fit_verdict_{vname}.csv")
        pd.set_option("display.width", 220)
        print(f"\n=== Variant '{vname}' ({mdir}/): train vs validation vs test\n" +
              verdicts.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
        print("\nVerdicts:", verdicts.verdict.value_counts().to_dict())
        md += [f"## Variant `{vname}` (models in `{mdir}/`)", "", md_table(verdicts), "",
               "Verdicts: " + ", ".join(f"{k}: {v}" for k, v in verdicts.verdict.value_counts().items()), ""]

    with open("testing/results/overfit/summary.md", "w") as f:
        f.write("\n".join(md) + "\n")
    print("\nSaved testing/results/overfit/ (data_counts.csv, loss_table_*.csv, fit_verdict_*.csv, summary.md)")


if __name__ == "__main__":
    main()
