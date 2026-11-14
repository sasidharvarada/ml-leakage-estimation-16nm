import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
import gates as G
from spice_utils import build_netlist, run_ngspice, set_params

GATE_SPICE = "results/part_b/gate_spice.csv"     # shared by the rail and no_rail variants
FIELDS = ["id", "ig", "is", "ib"]
CASES = ("nmos_on", "nmos_off", "pmos_on", "pmos_off")


def fet_currents(task):
    dev, proc, w, vd, vg, vs, vb, temp = task
    card = set_params(G.MODELS_TEXT[dev], proc, "mdev")
    net = build_netlist(card, dev, w, C.LMIN, vd, vg, vs, vb, temp, C.SPICE_OPTIONS)
    try:
        return run_ngspice(net)              # (id, ig, is, ib), current INTO each terminal
    except Exception:
        return (np.nan,) * 4


class OracleModel:
    """Stands in for TransistorModel: predict(df) returns single-FET SPICE currents."""

    def __init__(self, case, pool):
        self.dev = "nmos" if case.startswith("nmos") else "pmos"
        self.pool = pool

    def predict(self, df):
        tasks = [(self.dev, {p: r[p] for p in C.PROC_PARAMS}, r["w"], r["vd"], r["vg"], r["vs"], r["vb"], r["temp"])
                 for r in df.to_dict("records")]
        arr = np.array(list(self.pool.map(fet_currents, tasks, chunksize=16)), dtype=float).reshape(-1, 4)
        out = pd.DataFrame(index=df.index)           # one column at a time, like TransistorModel.predict:
        for k, name in enumerate(FIELDS):             # gates.py writes into the .to_numpy() result, which
            out[name] = arr[:, k].copy()              # must therefore be a writable copy (pandas 3)
        return out


class NoCap:
    def cap(self, df, ig):
        return ig


def stats(sp, orc, temp):
    sp, orc, temp = map(np.asarray, (sp, orc, temp))
    ok = np.isfinite(orc)
    rel = np.abs(orc[ok] - sp[ok]) / sp[ok] * 100.0
    hot = temp[ok] > 80
    return {"n": int(ok.sum()), "failed": int((~ok).sum()), "spice_median_A": float(np.median(sp[ok])),
            "bias_pct": float(np.median((orc[ok] - sp[ok]) / sp[ok]) * 100.0),
            "median_err_pct": float(np.median(rel)), "p95_err_pct": float(np.percentile(rel, 95)),
            "max_err_pct": float(rel.max()),
            "hot_median_err_pct": float(np.median(rel[hot])) if hot.any() else np.nan}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corners", type=int, default=None, help="use only the first N corners (default: all in the cache)")
    ap.add_argument("--seed", type=int, default=123, help="must match 04_validate_gates.py")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()

    if not os.path.exists(GATE_SPICE):
        sys.exit(f"{GATE_SPICE} not found: run scripts/04_validate_gates.py first")
    sp = pd.read_csv(GATE_SPICE, dtype={"inp": str})
    corners = G.generate_corners(int(sp.corner.max()) + 1, args.seed)
    if args.corners:
        sp = sp[sp.corner < args.corners]
    sp = sp[sp.spice_leak.notna() & (sp.spice_leak > 0)]

    pd.set_option("display.width", 160)
    pd.set_option("display.float_format", "{:.4g}".format)
    rows, allsp, allorc, alltemp = [], [], [], []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        ev = G.GateEvaluator.__new__(G.GateEvaluator)        # skip loading saved_models
        ev.models = {c: OracleModel(c, pool) for c in CASES}
        ev.ig_bound = {c: NoCap() for c in CASES}
        for gate, inp in G.GATE_CASES:
            part = sp[(sp.gate == gate) & (sp.inp == inp)].copy()
            recs = []
            for r in part.to_dict("records"):
                c = corners[int(r["corner"])]
                recs.append({**r, "vdd": c["vdd"], "temp": c["temp"], "nmos": c["nmos"], "pmos": c["pmos"]})
            print(f"[*] {gate} {inp}: single-FET SPICE for {len(recs)} corners ...", flush=True)
            orc = ev.evaluate(gate, inp, recs)["ml_leak"].values
            temp = [r["temp"] for r in recs]
            rows.append({"case": f"{gate} {inp}", **stats(part.spice_leak.values, orc, temp)})
            allsp += list(part.spice_leak.values); allorc += list(orc); alltemp += temp
    rows.append({"case": "ALL", **stats(allsp, allorc, alltemp)})

    print("\nORACLE: gate leakage from true single-FET currents (gates.py assembly) vs gate SPICE")
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nErrors are |oracle - gate SPICE| / gate SPICE, in percent. hot = temperature above 80 C.")
    print("failed = single-FET SPICE runs that did not return a result (excluded).")


if __name__ == "__main__":
    main()