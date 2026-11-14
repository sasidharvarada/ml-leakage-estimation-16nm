#!/usr/bin/env python3
"""Learning curves of the MLP: training, validation and test loss (re-trains, uses the GPU).

Run from the repo root:
    python testing/02_learning_curves.py                 # both curves, rail training set
    python testing/02_learning_curves.py --no-rail       # training set = 7,000 uniform rows only
    python testing/02_learning_curves.py --fast          # quick version (fewer L-BFGS iterations)
    python testing/02_learning_curves.py --only iter     # or --only size

1. Loss vs training iteration ("epoch curve"). The same MLP as scripts/torch_mlp.py
   (128-128-64, SiLU, 3,000 Adam steps, then L-BFGS) is trained on the full training set
   of each case and current. Every 100 Adam steps and every 500 L-BFGS iterations the
   loss (MSE of log10|I|) is recorded on the training, validation and test sets.
   Over-fitting shows up as a validation/test loss that turns upward while the training
   loss keeps falling.
2. Loss vs training-set size. The MLP is trained on 500, 1,000, 2,000, 4,000 and 7,000
   uniform training rows; the final training / validation / test loss and median error are
   recorded. A large train-validation gap that shrinks with more data = variance (over-fit);
   both high = bias (under-fit).

The validation and test sets are always the official 1,500 + 1,500 uniform rows (seed 7).
Losses are shown both over all points and over the best 99 % (see testing/01_check_overfit.py).

Outputs (testing/results/learning_curves/<rail|no_rail>/)
    iter_history.csv, iter_<case>.png, iter_summary.csv
    size_curve.csv, size_curve.png
"""
import argparse
import os
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import C, CASES, TARGETS, OUT, rel_err, splits, to_log
from leak_model import make_features

import torch
from torch import nn

DEV = "cuda" if torch.cuda.is_available() else "cpu"


def net_for(n_in, hidden=(128, 128, 64)):
    layers, prev = [], n_in
    for h in hidden:
        layers += [nn.Linear(prev, h), nn.SiLU()]
        prev = h
    layers.append(nn.Linear(prev, 1))
    return nn.Sequential(*layers)


def loss_stats(lt, lp, true_i):
    se = np.sort((lt - lp) ** 2)
    keep = max(1, int(0.99 * len(se)))
    pred_i = 10.0 ** lp            # magnitude only (sign is a separate classifier)
    return float(np.mean(se)), float(np.mean(se[:keep])), float(np.median(rel_err(np.abs(true_i), pred_i)))


def train_logged(Xtr, ytr, evals, adam_steps, lbfgs_iters, seed, log_every=100, lbfgs_chunk=500):
    """Same recipe as scripts/torch_mlp.py, but records losses on every set while training.
    evals: {name: (X, y_log10, I_true)}.  Returns (history rows, final predictions per set)."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    xm, xs = Xtr.mean(0), Xtr.std(0) + 1e-12
    ym, ys = ytr.mean(), ytr.std() + 1e-12
    T = lambda a: torch.tensor((a - xm) / xs, dtype=torch.float32, device=DEV)
    Xt = T(Xtr)
    yt = torch.tensor((ytr - ym) / ys, dtype=torch.float32, device=DEV).view(-1, 1)
    ev = {k: (T(x), y, i) for k, (x, y, i) in evals.items()}
    net = net_for(Xtr.shape[1]).to(DEV)
    mse = nn.MSELoss()
    hist = []

    def record(phase, it):
        net.eval()
        with torch.no_grad():
            row = {"phase": phase, "iteration": it}
            for k, (x, y, i) in ev.items():
                lp = net(x).cpu().numpy().reshape(-1) * ys + ym
                row[f"{k}_loss"], row[f"{k}_loss_99"], row[f"{k}_med_err_%"] = loss_stats(y, lp, i)
        net.train()
        hist.append(row)

    opt = torch.optim.Adam(net.parameters(), lr=3e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=adam_steps, eta_min=3e-6)
    record("adam", 0)
    for step in range(1, adam_steps + 1):
        opt.zero_grad(set_to_none=True)
        loss = mse(net(Xt), yt)
        loss.backward()
        opt.step()
        sched.step()
        if step % log_every == 0:
            record("adam", step)

    done = 0
    if lbfgs_iters > 0:
        lb = torch.optim.LBFGS(net.parameters(), lr=1.0, max_iter=lbfgs_chunk, history_size=50,
                               tolerance_grad=1e-12, tolerance_change=1e-15, line_search_fn="strong_wolfe")

        def closure():
            lb.zero_grad(set_to_none=True)
            l = mse(net(Xt), yt)
            l.backward()
            return l
        prev = None
        while done < lbfgs_iters:
            lb.step(closure)
            done += lbfgs_chunk
            record("lbfgs", adam_steps + done)
            cur = hist[-1]["train_loss"]
            if prev is not None and abs(prev - cur) <= 1e-12 * max(prev, 1e-30):
                break                        # converged (same stopping rule as the real training)
            prev = cur
    net.eval()
    with torch.no_grad():
        final = {k: net(x).cpu().numpy().reshape(-1) * ys + ym for k, (x, _, _) in ev.items()}
    return hist, final


def prepare(case, use_rail):
    dev = C.CASES[case]["type"]
    s = splits(case, use_rail)
    train = pd.concat([s["train"], s["train_rail"]], ignore_index=True) if "train_rail" in s else s["train"]
    feats = list(make_features(s["train"], dev).columns)
    X = lambda d: make_features(d, dev)[feats].to_numpy(np.float64)
    return dev, s, train, X


def iter_curves(args, out_dir):
    rows, summ = [], []
    for case in args.cases:
        dev, s, train, X = prepare(case, not args.no_rail)
        fig, axes = plt.subplots(1, 4, figsize=(20, 4.2))
        for ax, t in zip(axes, TARGETS):
            t0 = time.time()
            evals = {k: (X(d), to_log(d[t]), d[t].to_numpy()) for k, d in
                     (("train", train), ("validation", s["validation"]), ("test", s["test"]))}
            hist, _ = train_logged(X(train), to_log(train[t]), evals, args.adam, args.lbfgs, C.SEED)
            h = pd.DataFrame(hist)
            h.insert(0, "current", t)
            h.insert(0, "case", case)
            rows.append(h)
            best = h.loc[h.validation_loss_99.idxmin()]
            last = h.iloc[-1]
            summ.append({"case": case, "current": t, "iterations": int(last.iteration),
                         "final_train_loss_99": last.train_loss_99, "final_val_loss_99": last.validation_loss_99,
                         "final_test_loss_99": last.test_loss_99,
                         "best_val_loss_99": best.validation_loss_99, "best_val_at_iter": int(best.iteration),
                         "final/best_val": last.validation_loss_99 / best.validation_loss_99,
                         "final_train_med_%": last["train_med_err_%"], "final_val_med_%": last["validation_med_err_%"],
                         "final_test_med_%": last["test_med_err_%"],
                         "val_loss_rises_at_end": bool(last.validation_loss_99 > 1.2 * best.validation_loss_99)})
            for k, c in (("train", "C0"), ("validation", "C1"), ("test", "C2")):
                ax.plot(h.iteration, h[f"{k}_loss_99"], c, label=f"{k} (99 %)")
                ax.plot(h.iteration, h[f"{k}_loss"], c, ls=":", lw=0.8, label=f"{k} (all)")
            ax.axvline(args.adam, color="gray", ls="--", lw=0.8)
            ax.text(args.adam, 0.98, " L-BFGS", transform=ax.get_xaxis_transform(),
                    va="top", fontsize=8, color="gray")
            ax.set_yscale("log"); ax.set_xlabel("iteration (Adam steps, then L-BFGS iterations)")
            ax.set_ylabel("loss: MSE of log10|I|"); ax.set_title(f"{case}: {t}")
            ax.grid(True, which="both", alpha=0.3)
            print(f"  {case:8s} {t}: train {last.train_loss_99:.3g}  val {last.validation_loss_99:.3g}  "
                  f"test {last.test_loss_99:.3g}  (best val {best.validation_loss_99:.3g} at {int(best.iteration)})"
                  f"  [{time.time() - t0:.0f} s]", flush=True)
        axes[0].legend(fontsize=7)
        fig.tight_layout(); fig.savefig(os.path.join(out_dir, f"iter_{case}.png"), dpi=130); plt.close(fig)
    pd.concat(rows).to_csv(os.path.join(out_dir, "iter_history.csv"), index=False, float_format="%.5g")
    summ = pd.DataFrame(summ)
    summ.to_csv(os.path.join(out_dir, "iter_summary.csv"), index=False, float_format="%.5g")
    pd.set_option("display.width", 220)
    print("\nLoss vs iteration, final values:\n" + summ.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


def size_curve(args, out_dir):
    sizes = [n for n in args.sizes if n <= 7000]
    rows = []
    for case in args.cases:
        dev, s, _, X = prepare(case, False)
        base = s["train"].sample(frac=1.0, random_state=C.SEED)       # fixed order -> nested subsets
        for n in sizes:
            sub = base.iloc[:n]
            for t in TARGETS:
                t0 = time.time()
                evals = {k: (X(d), to_log(d[t]), d[t].to_numpy()) for k, d in
                         (("train", sub), ("validation", s["validation"]), ("test", s["test"]))}
                _, fin = train_logged(X(sub), to_log(sub[t]), evals, args.adam, args.lbfgs, C.SEED,
                                      log_every=10 ** 9, lbfgs_chunk=min(args.lbfgs, 2000) or 1)
                r = {"case": case, "current": t, "train_rows": n}
                for k, (_, y, i) in evals.items():
                    r[f"{k}_loss"], r[f"{k}_loss_99"], r[f"{k}_med_err_%"] = loss_stats(y, fin[k], i)
                rows.append(r)
                print(f"  {case:8s} {t} n={n:5d}: train {r['train_med_err_%']:.2f} %  val "
                      f"{r['validation_med_err_%']:.2f} %  test {r['test_med_err_%']:.2f} %  [{time.time() - t0:.0f} s]",
                      flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "size_curve.csv"), index=False, float_format="%.5g")
    fig, axes = plt.subplots(1, len(args.cases), figsize=(5 * len(args.cases), 4), squeeze=False)
    for ax, case in zip(axes[0], args.cases):
        d = df[df.case == case].groupby("train_rows").median(numeric_only=True)
        for k, c in (("train", "C0"), ("validation", "C1"), ("test", "C2")):
            ax.plot(d.index, d[f"{k}_med_err_%"], "o-", color=c, label=k)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("training rows (uniform)")
        ax.set_ylabel("median error (%), median over the 4 currents"); ax.set_title(case)
        ax.grid(True, which="both", alpha=0.3); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(out_dir, "size_curve.png"), dpi=130); plt.close(fig)
    piv = df.pivot_table(index=["case", "train_rows"], values=["train_med_err_%", "validation_med_err_%", "test_med_err_%"],
                         aggfunc="median").round(3)
    print("\nMedian error vs training-set size (median over the 4 currents):\n" + piv.to_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-rail", action="store_true", help="iteration curve on the 7,000 uniform rows only")
    ap.add_argument("--fast", action="store_true", help="1,000 Adam steps + 2,000 L-BFGS iterations")
    ap.add_argument("--only", choices=["iter", "size"], default=None)
    ap.add_argument("--cases", nargs="+", default=CASES)
    ap.add_argument("--sizes", nargs="+", type=int, default=[500, 1000, 2000, 4000, 7000])
    ap.add_argument("--adam", type=int, default=3000)
    ap.add_argument("--lbfgs", type=int, default=20000)
    args = ap.parse_args()
    if args.fast:
        args.adam, args.lbfgs = 1000, 2000
    out_dir = os.path.join(OUT, "learning_curves", "no_rail" if args.no_rail else "rail")
    os.makedirs(out_dir, exist_ok=True)
    print(f"Device: {DEV}.  Adam {args.adam} steps, L-BFGS up to {args.lbfgs} iterations.  Output: {out_dir}/")
    t0 = time.time()
    if args.only in (None, "iter"):
        print("\n=== 1. Loss vs training iteration")
        iter_curves(args, out_dir)
    if args.only in (None, "size"):
        print("\n=== 2. Loss vs training-set size (uniform rows only)")
        size_curve(args, out_dir)
    print(f"\nDone in {(time.time() - t0) / 60:.0f} min. Results in {out_dir}/")


if __name__ == "__main__":
    main()
