"""Helpers: read the model file, build a single-transistor netlist, run ngspice."""
import os
import re
import subprocess
import tempfile


def split_models(model_path):
    """Return {'nmos': text, 'pmos': text} -- the two .model cards in the file."""
    text = open(model_path).read()
    parts = re.split(r"(?im)^(?=\s*\.model\s)", text)
    models = {}
    for p in parts:
        m = re.match(r"(?is)\s*\.model\s+(\S+)\s+(nmos|pmos)", p)
        if m:
            # keep only the .model card itself (drop trailing comment lines)
            models[m.group(2).lower()] = p.strip()
    if set(models) != {"nmos", "pmos"}:
        raise ValueError(f"Expected one nmos and one pmos model in {model_path}")
    return models


def _param_regex(name):
    # word boundary so 'xj' does not match 'xjbvs', 'u0' does not match 'u0x'
    return re.compile(rf"(?i)(\b{name}\s*=\s*)([-+0-9.eE]+)")


def get_param(model_text, name):
    m = _param_regex(name).search(model_text)
    if not m:
        raise ValueError(f"Parameter {name} not found in model card")
    return float(m.group(2))


def set_params(model_text, values, new_name):
    """Return the model card with new parameter values and a new model name."""
    out = re.sub(r"(?i)(\.model\s+)\S+", rf"\g<1>{new_name}", model_text, count=1)
    for name, val in values.items():
        rx = _param_regex(name)
        if not rx.search(out):
            raise ValueError(f"Parameter {name} not found in model card")
        out = rx.sub(lambda m: f"{m.group(1)}{val:.6e}", out, count=1)
    return out


def build_netlist(model_card, dev_type, w, l, vd, vg, vs, vb, temp, options):
    """Single-FET netlist. Every terminal has its own voltage source."""
    return f"""* single {dev_type.upper()} leakage characterisation
{options}
.temp {temp:.4f}

{model_card}

M1 d g s b mdev W={w:.6e} L={l:.6e}
Vd d 0 {vd:.6f}
Vg g 0 {vg:.6f}
Vs s 0 {vs:.6f}
Vb b 0 {vb:.6f}

.control
op
let id_ = -i(vd)
let ig_ = -i(vg)
let is_ = -i(vs)
let ib_ = -i(vb)
echo RESULT $&id_ $&ig_ $&is_ $&ib_
.endc
.end
"""


_NUM = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"


def run_ngspice(netlist, timeout=60):
    """Run ngspice in batch mode. Returns (id, ig, is, ib): current INTO each terminal."""
    with tempfile.NamedTemporaryFile("w", suffix=".cir", delete=False) as f:
        f.write(netlist)
        path = f.name
    try:
        res = subprocess.run(["ngspice", "-b", path], capture_output=True,
                             text=True, timeout=timeout)
    finally:
        os.remove(path)
    for line in res.stdout.splitlines():
        if line.startswith("RESULT"):
            nums = re.findall(_NUM, line[6:])
            if len(nums) == 4:
                return tuple(float(x) for x in nums)
    raise RuntimeError("ngspice failed:\n" + res.stdout[-2000:] + res.stderr[-2000:])
