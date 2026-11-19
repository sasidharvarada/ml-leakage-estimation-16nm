#!/usr/bin/env python3
"""Run your own test case: SPICE vs our ML models, for a 3-bit CLA input, one gate, or one transistor.

Run from the repo root (models/, results/ and scripts/ as in the repository):

  3-bit CLA (a + b + cin), any input values:
    python3 scripts/run_test_case.py cla --a 5 --b 3 --cin 0
    python3 scripts/run_test_case.py cla --a 7 --b 7 --cin 1 --temp 85 --vdd 1.05
    python3 scripts/run_test_case.py cla --all                 # all 128 vectors at one corner (~1-3 min)

  One gate and input pattern:
    python3 scripts/run_test_case.py gate --gate NAND2 --inp 11
    python3 scripts/run_test_case.py gate --gate all           # all 18 gate cases at one corner

  One transistor:
    python3 scripts/run_test_case.py fet --case nmos_off --vd 1.0 --vs 0 --w 32

Corner options (any command):
  --vdd 1.0         supply voltage in V (0.9 to 1.1 is the trained range)
  --temp 27         temperature in degC (-40 to 125)
  --proc 1.0        multiply all 5 process parameters (vth0, toxe, ndep, u0, xj) of NMOS and PMOS
  --vth0 1.0        extra multiplier for vth0 only (0.9 to 1.1)
  --corner K        use corner K (0..199) of the official Part B / C corners (seed 123) instead

Error  = |ML - SPICE| / SPICE x 100 %      Accuracy = 100 % - error
"""
import argparse
import importlib.util
import os
import sys
from concurrent.futures import ThreadPoolExecutor   # threads: ngspice runs as its own process anyway

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PC = _load("part_c", "05_test_circuit.py")      # also loads Part B (04) and registers the model classes
PB = PC.PB
import torch                                      # noqa: E402
PB.DEVICE = torch.device("cpu")
import cla3                                       # noqa: E402
import config as C                               # noqa: E402
from spice_utils import split_models, set_params, build_netlist, run_ngspice   # noqa: E402

CASE_TYPE = {"nmos_on": "nmos", "nmos_off": "nmos", "pmos_on": "pmos", "pmos_off": "pmos"}
NAMES = ["Id", "Ig", "Is", "Ib"]


# ---------------------------------------------------------------- corner
def make_corner(args):
    if args.corner is not None:
        c = PB.generate_corners(num_corners=200, seed=123)[args.corner]
        print(f"Corner {args.corner} of the official set (seed 123)")
    else:
        nm = {k: v * args.proc for k, v in PB.NOM_NMOS.items()}
        pm = {k: v * args.proc for k, v in PB.NOM_PMOS.items()}
        nm["vth0"] *= args.vth0
        pm["vth0"] *= args.vth0
        c = {"vdd": args.vdd, "temp": args.temp, "nmos": nm, "pmos": pm}
    print(f"VDD = {c['vdd']:.3f} V   T = {c['temp']:.1f} degC   "
          f"NMOS vth0 = {c['nmos']['vth0']:.4f} V   PMOS vth0 = {c['pmos']['vth0']:.4f} V   "
          f"toxe(n) = {c['nmos']['toxe'] * 1e9:.3f} nm")
    return c


def err(ml, sp):
    return abs(ml - sp) / abs(sp) * 100.0 if sp != 0 else float("nan")


def line():
    print("-" * 78)


# ---------------------------------------------------------------- gate
def gate_results(cases, corner, workers):
    """SPICE (isolated gate) + ML for a list of (gate, inp). Returns dict -> (spice, ml, load_a, load_b, node_v)."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        sims = list(pool.map(PB.simulate_gate_spice, [(g, i, corner) for g, i in cases]))
    ev = PB.GateMLEvaluator()
    out = {}
    for (g, i), (sp, node_v) in zip(cases, sims):
        ml = float(ev.predict_gate_leakage(g, i, corner, node_v))
        la, lb = PC._pin_loading_ig(ev, g, i, corner, node_v)
        out[(g, i)] = (sp, ml, la, lb, node_v)
    return out


def cmd_gate(args, corner):
    cases = list(PB.GATE_CASES) if args.gate == "all" else [(args.gate, args.inp)]
    for g, i in cases:
        if (g, i) not in PB.GATE_CASES:
            sys.exit(f"Unknown gate case {g} {i}. Choose from: {PB.GATE_CASES}")
    res = gate_results(cases, corner, args.workers)
    line()
    print(f"{'Gate':6s} {'In':3s} {'SPICE (A)':>12s} {'ML (A)':>12s} {'Error %':>9s} {'Accuracy %':>11s}   V(out)")
    line()
    errs = []
    for (g, i), (sp, ml, la, lb, nv) in res.items():
        e = err(ml, sp)
        errs.append(e)
        print(f"{g:6s} {i:3s} {sp:12.4e} {ml:12.4e} {e:9.2f} {max(0.0, 100 - e):11.2f}   {nv.get('out', 0):.4f} V")
    line()
    if len(errs) > 1:
        print(f"Median error over these cases: {np.nanmedian(errs):.2f} %")


# ---------------------------------------------------------------- CLA
def cla_one(vec, corner, gres):
    """ML plain, ML loading-aware and SPICE gate-sum for one vector, from per-gate results."""
    logic = cla3.logic_eval(vec)
    plain = extra = spsum = 0.0
    for g, t, ins, out in cla3.GATES:
        pat = cla3.pattern([logic[n] for n in ins])
        sp, ml, la, lb, _ = gres[(t, pat)]
        plain += ml
        spsum += sp
        for k, net in enumerate(ins):
            if net not in cla3.INPUTS:
                extra += (la, lb)[k]
    return plain, plain + extra, spsum


def cmd_cla(args, corner):
    if args.all:
        vecs = list(range(128))
    else:
        for name, v, hi in (("a", args.a, 7), ("b", args.b, 7), ("cin", args.cin, 1)):
            if not 0 <= v <= hi:
                sys.exit(f"--{name} must be 0..{hi}")
        vecs = [args.a | (args.b << 3) | (args.cin << 6)]
    # gate cases the chosen vectors need
    need = set()
    for vec in vecs:
        logic = cla3.logic_eval(vec)
        for g, t, ins, out in cla3.GATES:
            need.add((t, cla3.pattern([logic[n] for n in ins])))
    print(f"[*] SPICE: {len(need)} isolated gate cases + {len(vecs)} full-CLA run(s) ...")
    gres = gate_results(sorted(need), corner, args.workers)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        circ = list(pool.map(PC.simulate_circuit, [(0, v, corner) for v in vecs]))

    rows = []
    for (_, vec, leak, outs) in circ:
        plain, la, spsum = cla_one(vec, corner, gres)
        a = vec & 7
        b = (vec >> 3) & 7
        cin = (vec >> 6) & 1
        bits = [1 if o > corner["vdd"] / 2 else 0 for o in outs]
        got = bits[0] + 2 * bits[1] + 4 * bits[2] + 8 * bits[3]
        rows.append((vec, a, b, cin, a + b + cin, got, leak, plain, la, spsum))

    if not args.all:
        vec, a, b, cin, exp, got, leak, plain, la, spsum = rows[0]
        logic = cla3.logic_eval(vec)
        line()
        print(f"Test case: a = {a} ({a:03b}), b = {b} ({b:03b}), cin = {cin}   ->   expected sum = {exp} ({exp:04b})")
        print(f"SPICE outputs: cout s2 s1 s0 = {got:04b} = {got}   ->   logic {'CORRECT' if got == exp else 'WRONG'}")
        print("P = " + "".join(str(logic[f'p{i}']) for i in (2, 1, 0)) +
              "   G = " + "".join(str(logic[f'g{i}n']) for i in (2, 1, 0)) +
              f"   C1 = {logic['c1']}   C2 = {logic['c2']}   Cout = {logic['cout']}")
        line()
        print(f"{'Method':40s} {'Leakage (A)':>13s} {'Error %':>9s} {'Accuracy %':>11s}")
        line()
        print(f"{'SPICE, full CLA netlist (reference)':40s} {leak:13.4e} {'':>9s} {'':>11s}")
        for name, v in (("ML plain sum (project method)", plain),
                        ("ML loading-aware sum (our addition)", la),
                        ("SPICE gate sum, no ML (control)", spsum)):
            e = err(v, leak)
            print(f"{name:40s} {v:13.4e} {e:9.2f} {max(0.0, 100 - e):11.2f}")
        line()
        print(f"Leakage power (SPICE) = VDD x I = {corner['vdd'] * leak * 1e9:.2f} nW")
        print("Gate states used by this vector (42 gates):")
        cnt = {}
        for g, t, ins, out in cla3.GATES:
            k = (t, cla3.pattern([logic[n] for n in ins]))
            cnt[k] = cnt.get(k, 0) + 1
        print("   " + ", ".join(f"{t} {p} x{n}" for (t, p), n in sorted(cnt.items())))
    else:
        e_p = np.array([err(r[7], r[6]) for r in rows])
        e_l = np.array([err(r[8], r[6]) for r in rows])
        e_s = np.array([err(r[9], r[6]) for r in rows])
        wrong = sum(r[4] != r[5] for r in rows)
        line()
        print(f"All 128 vectors at this corner. Logic errors: {wrong}")
        print(f"{'Method':40s} {'Median err %':>13s} {'Mean accuracy %':>16s}")
        line()
        for name, e in (("ML plain sum (project method)", e_p), ("ML loading-aware sum (our addition)", e_l),
                        ("SPICE gate sum, no ML (control)", e_s)):
            print(f"{name:40s} {np.nanmedian(e):13.2f} {100 - np.nanmean(e):16.2f}")
        line()
        lo = min(rows, key=lambda r: r[6])
        hi = max(rows, key=lambda r: r[6])
        print(f"Lowest-leakage vector:  a={lo[1]} b={lo[2]} cin={lo[3]}  {lo[6]:.4e} A")
        print(f"Highest-leakage vector: a={hi[1]} b={hi[2]} cin={hi[3]}  {hi[6]:.4e} A")
        if args.csv:
            import csv
            with open(args.csv, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["vector", "a", "b", "cin", "expected", "spice_sum", "spice_leak_A",
                            "ml_plain_A", "ml_loading_A", "spice_gate_sum_A"])
                w.writerows(rows)
            print(f"Saved {args.csv}")


# ---------------------------------------------------------------- transistor
def cmd_fet(args, corner):
    dev = CASE_TYPE[args.case]
    vdd, temp = corner["vdd"], corner["temp"]
    proc = corner[dev]
    vg = vdd if args.case in ("nmos_on", "pmos_off") else 0.0
    vb = vdd if dev == "pmos" else 0.0
    vd = args.vd if args.vd is not None else vdd
    vs = args.vs if args.vs is not None else 0.0
    w = args.w * 1e-9
    card = set_params(split_models(C.MODEL_FILE)[dev], proc, "mdev")
    net = build_netlist(card, dev, w, C.LMIN, vd, vg, vs, vb, temp, C.SPICE_OPTIONS)
    sp = run_ngspice(net)
    ml = PB.GateMLEvaluator().predict_fet(args.case, vdd, temp, w, vd, vs, vg, vb, proc)
    line()
    print(f"{args.case}: W = {args.w:.0f} nm, L = 16 nm, Vd = {vd:.3f} V, Vg = {vg:.3f} V, Vs = {vs:.3f} V, Vb = {vb:.3f} V")
    print(f"AD = AS = W x 40 nm = {args.w * 40:.0f} nm^2,  PD = PS = 2(W + 40 nm) = {2 * (args.w + 40):.0f} nm")
    line()
    print(f"{'Current':8s} {'SPICE (A)':>13s} {'ML |I| (A)':>13s} {'Error %':>9s}")
    line()
    for k, name in enumerate(NAMES):
        if abs(sp[k]) < 1e-18:
            note = "   (SPICE below the 1e-18 A floor = ~0, not scored)"
            print(f"{name:8s} {sp[k]:13.4e} {ml[k]:13.4e} {'--':>9s}{note}")
        else:
            print(f"{name:8s} {sp[k]:13.4e} {ml[k]:13.4e} {err(ml[k], abs(sp[k])):9.2f}")
    line()
    print(f"KCL check: Id + Ig + Is + Ib = {sum(sp):.3e} A (should be ~0)")
    print("ML predicts the magnitude |I| (log10 model); the sign comes from the circuit.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    pc = sub.add_parser("cla")
    pc.add_argument("--a", type=int, default=5)
    pc.add_argument("--b", type=int, default=3)
    pc.add_argument("--cin", type=int, default=0)
    pc.add_argument("--all", action="store_true", help="all 128 vectors")
    pc.add_argument("--csv", default=None, help="with --all: save the per-vector table")
    pg = sub.add_parser("gate")
    pg.add_argument("--gate", default="NAND2", help="INV, NAND2, NOR2, AND2, OR2 or all")
    pg.add_argument("--inp", default="00", help="input pattern, e.g. 0, 1, 00, 01, 10, 11")
    pf = sub.add_parser("fet")
    pf.add_argument("--case", default="nmos_off", choices=list(CASE_TYPE))
    pf.add_argument("--vd", type=float, default=None, help="drain voltage (default VDD)")
    pf.add_argument("--vs", type=float, default=None, help="source voltage (default 0)")
    pf.add_argument("--w", type=float, default=32, help="width in nm (16 to 128)")
    for p in (pc, pg, pf):
        p.add_argument("--vdd", type=float, default=1.0)
        p.add_argument("--temp", type=float, default=27.0)
        p.add_argument("--proc", type=float, default=1.0)
        p.add_argument("--vth0", type=float, default=1.0)
        p.add_argument("--corner", type=int, default=None)
        p.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()
    corner = make_corner(args)
    {"cla": cmd_cla, "gate": cmd_gate, "fet": cmd_fet}[args.cmd](args, corner)


if __name__ == "__main__":
    main()
