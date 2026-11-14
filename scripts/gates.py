import os
import re
import subprocess
import tempfile

import numpy as np
import pandas as pd

import config as C
from spice_utils import set_params, split_models

LMIN = C.LMIN
L_DIFF = C.L_DIFF
WN = 2 * LMIN      # 32 nm
WP = 4 * LMIN      # 64 nm
NUM = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
OFF_PMOS_KCL = False     # True: use device KCL for OFF PMOS tied to VDD (tested: worse)
ZERO_FIELD_V = 1e-3      # see GateEvaluator.evaluate (zero-field OFF devices)

GATE_CASES = [
    ("INV", "0"), ("INV", "1"),
    ("NAND2", "00"), ("NAND2", "01"), ("NAND2", "10"), ("NAND2", "11"),
    ("NOR2", "00"), ("NOR2", "01"), ("NOR2", "10"), ("NOR2", "11"),
    ("AND2", "00"), ("AND2", "01"), ("AND2", "10"), ("AND2", "11"),
    ("OR2", "00"), ("OR2", "01"), ("OR2", "10"), ("OR2", "11"),
]
INTERNAL_NODES = {"INV": ["out"], "NAND2": ["out", "x"], "NOR2": ["out", "y"],
                  "AND2": ["out", "x", "n_out"], "OR2": ["out", "y", "n_out"]}

MODELS_TEXT = split_models(C.MODEL_FILE)
_NOM = {t: {p: float(re.search(rf"(?i)\b{p}\s*=\s*([-+0-9.eE]+)", MODELS_TEXT[t]).group(1))
            for p in C.PROC_PARAMS} for t in ("nmos", "pmos")}


# ----------------------------------------------------------------------------- topology
def transistors(gate):
    """List of (name, type, d, g, s, b). Nodes: vdd, 0, a, b, out, x, y, n_out."""
    def inv(p, i, o):
        return [(p + "p", "p", o, i, "vdd", "vdd"), (p + "n", "n", o, i, "0", "0")]

    def nand(o):
        return [("p1", "p", o, "a", "vdd", "vdd"), ("p2", "p", o, "b", "vdd", "vdd"),
                ("n1", "n", o, "a", "x", "0"), ("n2", "n", "x", "b", "0", "0")]

    def nor(o):
        return [("p1", "p", "y", "a", "vdd", "vdd"), ("p2", "p", o, "b", "y", "vdd"),
                ("n1", "n", o, "a", "0", "0"), ("n2", "n", o, "b", "0", "0")]

    if gate == "INV":
        return inv("", "a", "out")
    if gate == "NAND2":
        return nand("out")
    if gate == "NOR2":
        return nor("out")
    if gate == "AND2":
        return nand("n_out") + inv("i", "n_out", "out")
    if gate == "OR2":
        return nor("n_out") + inv("i", "n_out", "out")
    raise ValueError(gate)


def input_nodes(gate):
    return ["a"] if gate == "INV" else ["a", "b"]


def logic_value(gate, inp):
    x = [int(c) for c in inp]
    return {"INV": lambda: 1 - x[0], "NAND2": lambda: 1 - (x[0] & x[1]),
            "NOR2": lambda: 1 - (x[0] | x[1]), "AND2": lambda: x[0] & x[1],
            "OR2": lambda: x[0] | x[1]}[gate]()


# ----------------------------------------------------------------------------- corners
def generate_corners(num_corners=200, seed=71):
    """Same corner draw as the original Part B / Part C scripts (seed 71)."""
    rng = np.random.default_rng(seed)
    corners = []
    for _ in range(num_corners):
        vdd = rng.uniform(0.9, 1.1)
        temp = rng.uniform(-40.0, 125.0)
        n_proc = {k: v * rng.uniform(0.9, 1.1) for k, v in _NOM["nmos"].items()}
        p_proc = {k: v * rng.uniform(0.9, 1.1) for k, v in _NOM["pmos"].items()}
        corners.append({"vdd": vdd, "temp": temp, "nmos": n_proc, "pmos": p_proc})
    return corners


# ----------------------------------------------------------------------------- SPICE
def fet_line(name, kind, d, g, s, b):
    w, mod = (WN, "nmos_mod") if kind == "n" else (WP, "pmos_mod")
    ad = w * L_DIFF
    pd_ = 2 * (w + L_DIFF)
    return (f"M{name} {d} {g} {s} {b} {mod} W={w:.5e} L={LMIN:.5e} "
            f"AD={ad:.5e} AS={ad:.5e} PD={pd_:.5e} PS={pd_:.5e}")


def nodeset(gate, inp, vdd):
    a = int(inp[0])
    b = int(inp[1]) if len(inp) > 1 else 0
    ns = {}
    if gate in ("NAND2", "AND2"):
        ns["x"] = 0.0 if b else (vdd if a else vdd / 2)
        ns["n_out" if gate == "AND2" else "out"] = vdd * (1 - (a & b))
    if gate in ("NOR2", "OR2"):
        ns["y"] = vdd if not a else 0.0
        ns["n_out" if gate == "OR2" else "out"] = vdd * (1 - (a | b))
    ns["out"] = vdd * logic_value(gate, inp)
    return ".nodeset " + " ".join(f"v({k})={v:.6f}" for k, v in ns.items())


def gate_deck(gate, inp, corner):
    vdd = corner["vdd"]
    lines = [f"* {gate} input {inp}",
             set_params(MODELS_TEXT["nmos"], corner["nmos"], "nmos_mod"),
             set_params(MODELS_TEXT["pmos"], corner["pmos"], "pmos_mod"),
             f"Vdd vdd 0 DC {vdd:.6f}"]
    for k, node in enumerate(input_nodes(gate)):
        lines.append(f"V{node} {node} 0 DC {vdd * int(inp[k]):.6f}")
    lines += [fet_line(*t) for t in transistors(gate)]
    lines += [nodeset(gate, inp, vdd),
              C.SPICE_OPTIONS + " itl1=400",
              f".temp {corner['temp']:.4f}",
              ".control", "set numdgt = 10", "op",
              "let ileak = -i(vdd)", "echo LEAK $&ileak"]
    for node in input_nodes(gate):
        lines += [f"let ipin_{node} = -i(v{node})", f"echo PIN_{node} $&ipin_{node}"]
    for node in INTERNAL_NODES[gate]:
        lines.append(f"echo NODE_{node} $&v({node})")
    lines += [".endc", ".end"]
    return "\n".join(lines) + "\n"


def simulate_gate(task):
    """Returns dict: spice_leak, pin_<a|b>, v_<node> (NaN if the run failed)."""
    gate, inp, ci, corner = task
    rec = {"gate": gate, "inp": inp, "corner": ci, "spice_leak": np.nan}
    with tempfile.NamedTemporaryFile("w", suffix=".cir", delete=False) as f:
        f.write(gate_deck(gate, inp, corner))
        path = f.name
    try:
        out = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True, timeout=60).stdout
    except subprocess.TimeoutExpired:
        out = ""
    finally:
        os.remove(path)
    for line in out.splitlines():
        key = line.split(" ")[0]
        nums = re.findall(NUM, line[len(key):])
        if not nums:
            continue
        if key == "LEAK":
            rec["spice_leak"] = float(nums[0])
        elif key.startswith("PIN_"):
            rec["pin_" + key[4:]] = float(nums[0])
        elif key.startswith("NODE_"):
            rec["v_" + key[5:]] = float(nums[0])
    return rec


# ----------------------------------------------------------------------------- ML
def _components(fets, on):
    """Union-find over drain/source of ON transistors."""
    parent = {}

    def find(n):
        parent.setdefault(n, n)
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    for (name, kind, d, g, s, b), is_on in zip(fets, on):
        find(d); find(s); find(g); find(b)
        if is_on:
            parent[find(d)] = find(s)
    return find


class GateCurrentBound:
    """Physical upper bound for the predicted gate current |Ig| of one case.

    Gate tunnelling current grows with the oxide voltages |Vgs| and |Vgd|. So for a
    query point, |Ig| cannot exceed the largest |Ig| seen in the training data at
    equal or smaller |Vgs| and |Vgd| (+ one 50 mV bin of margin). This removes rare
    wild predictions where the true gate current is ~0 (e.g. Vgd = 0) without
    changing any normal prediction.
    """
    STEP = 0.05

    def __init__(self, df, dev_type):
        s = 1.0 if dev_type == "nmos" else -1.0
        vgs = np.abs(s * (df["vg"] - df["vs"]).to_numpy())
        vgd = np.abs(s * (df["vg"] - df["vd"]).to_numpy())
        ig = np.abs(df["ig"].to_numpy())
        n = int(np.ceil(1.25 / self.STEP)) + 2
        tab = np.zeros((n, n))
        i, j = self._bin(vgs, n), self._bin(vgd, n)
        np.maximum.at(tab, (i, j), ig)
        self.tab = np.maximum.accumulate(np.maximum.accumulate(tab, axis=0), axis=1)
        self.n = n

    def _bin(self, v, n):
        return np.clip(np.floor(v / self.STEP).astype(int), 0, n - 1)

    def cap(self, df, ig):
        vgs = np.abs(df["vg"].to_numpy() - df["vs"].to_numpy())
        vgd = np.abs(df["vg"].to_numpy() - df["vd"].to_numpy())
        lim = self.tab[np.minimum(self._bin(vgs, self.n) + 1, self.n - 1),
                       np.minimum(self._bin(vgd, self.n) + 1, self.n - 1)]
        return np.sign(ig) * np.minimum(np.abs(ig), lim)


class GateEvaluator:
    """Predicts gate leakage and input-pin currents from the 4 transistor models."""

    def __init__(self, model_dir="saved_models", use_rail=True):
        from leak_model import TransistorModel
        self.models = {c: TransistorModel.load(os.path.join(model_dir, f"{c}.joblib"))
                       for c in ("nmos_on", "nmos_off", "pmos_on", "pmos_off")}
        self.ig_bound = {}
        for c in self.models:
            files = [f"data/{c}.csv"] + ([f"data/rail/{c}.csv"] if use_rail else [])
            parts = [pd.read_csv(f) for f in files if os.path.exists(f)]
            self.ig_bound[c] = GateCurrentBound(pd.concat(parts, ignore_index=True), c[:4])

    def evaluate(self, gate, inp, rows):
        """rows: list of dicts with corner info + node voltages (v_out, v_x, ...).
        Returns DataFrame with ml_leak, ml_pin_a, ml_pin_b per row."""
        fets = transistors(gate)
        pins = input_nodes(gate)
        requests = {c: [] for c in self.models}       # case -> list of (row_idx, fet_idx, feature dict)
        plans = []
        for ri, r in enumerate(rows):
            vdd = r["vdd"]
            volt = {"vdd": vdd, "0": 0.0}
            for k, node in enumerate(pins):
                volt[node] = vdd * int(inp[k])
            for node in INTERNAL_NODES[gate]:
                volt[node] = r["v_" + node]
            on = []
            for (name, kind, d, g, s, b) in fets:
                high = volt[g] > vdd / 2
                on.append(high if kind == "n" else not high)
            find = _components(fets, on)
            n_up = {n for n in volt if find(n) == find("vdd")}
            plan = []
            for fi, ((name, kind, d, g, s, b), is_on) in enumerate(zip(fets, on)):
                case = ("nmos" if kind == "n" else "pmos") + ("_on" if is_on else "_off")
                proc = r["nmos"] if kind == "n" else r["pmos"]
                w = {"d": 0.0, "g": 0.0, "s": 0.0, "b": 0.0}   # weight of each terminal current in I_vdd
                if is_on and find(d) == find("vdd"):
                    w["g"] = 0.0 if g in n_up else -1.0
                    w["b"] = 0.0 if b in n_up else -1.0
                else:
                    up = {t: node in n_up for t, node in (("d", d), ("g", g), ("s", s), ("b", b))}
                    n_in = sum(up.values())
                    if n_in >= 3 or (OFF_PMOS_KCL and not is_on and up["b"] and (up["s"] or up["d"])):
                        # KCL on the device: sum over N_up terminals = -(sum over the others).
                        # With 3 terminals in N_up (e.g. an OFF PMOS with Vd = Vs = Vb = VDD)
                        # the direct sum Id + Is + Ib cancels almost exactly, so -Ig is far
                        # more accurate.
                        for t in "dgsb":
                            w[t] = 0.0 if up[t] else -1.0
                        vt = [volt[d], volt[g], volt[s], volt[b]]
                        if n_in >= 3 and max(vt) - min(vt) < ZERO_FIELD_V:
                            # the remaining terminal (the gate) is at the same voltage too, e.g.
                            # the OFF PMOS of a NAND with Vg = Vd = Vs = Vb = VDD: no field, so
                            # its gate current is ~0 A. The models are unreliable for ~0 A, so
                            # this device is left out.
                            w = {"d": 0.0, "g": 0.0, "s": 0.0, "b": 0.0}
                    else:
                        for t in "dgsb":
                            w[t] = 1.0 if up[t] else 0.0
                requests[case].append((ri, fi, {
                    "vdd": vdd, "temp": r["temp"], "w": WN if kind == "n" else WP,
                    "vd": volt[d], "vs": volt[s], "vg": volt[g], "vb": volt[b], **proc}))
                plan.append((case, w, g))
            plans.append(plan)

        pred = {}
        for case, req in requests.items():
            if not req:
                continue
            df = pd.DataFrame([q[2] for q in req])
            p = self.models[case].predict(df)[["id", "ig", "is", "ib"]].to_numpy()
            p[:, 1] = self.ig_bound[case].cap(df, p[:, 1])
            for (ri, fi, _), (i_d, i_g, i_s, i_b) in zip(req, p):
                pred[(ri, fi)] = {"d": i_d, "g": i_g, "s": i_s, "b": i_b}

        out = []
        for ri, plan in enumerate(plans):
            leak = 0.0
            pin = {node: 0.0 for node in pins}
            for fi, (case, w, g) in enumerate(plan):
                cur = pred[(ri, fi)]
                leak += sum(w[t] * cur[t] for t in "dgsb")
                if g in pin:
                    pin[g] += cur["g"]
            rec = {"ml_leak": leak}
            for node in ("a", "b"):
                rec["ml_pin_" + node] = pin.get(node, 0.0)
            out.append(rec)
        return pd.DataFrame(out)
