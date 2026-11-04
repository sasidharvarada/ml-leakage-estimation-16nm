"""Team settings for Part A. Change only this file if your assignment changes."""

MODEL_FILE = "models/16nm_LP.pm"   # assigned model file (put it in models/)
VDD_NOM    = 1.0                   # assigned nominal VDD (V)
LMIN       = 16e-9                 # channel length = feature size (m)

N_SAMPLES  = 10000                 # samples per case
SEED       = 42                    # fixed seed so results can be reproduced

# Process parameters varied +-10 % around the model-file value
PROC_PARAMS = ["vth0", "toxe", "ndep", "u0", "xj"]
PROC_SPREAD = 0.10
VDD_SPREAD  = 0.10
TEMP_RANGE  = (-40.0, 125.0)       # degC
W_RANGE     = (1, 8)               # W = 1x .. 8x LMIN

# Required simulator options (from the project PDF)
SPICE_OPTIONS = ".options gmin=1e-18 abstol=1e-18 reltol=1e-6 vntol=1e-9"

# The 4 cases: device type, gate voltage, body voltage ("vdd" means = VDD)
CASES = {
    "nmos_on":  {"type": "nmos", "vg": "vdd", "vb": "0"},
    "nmos_off": {"type": "nmos", "vg": "0",   "vb": "0"},
    "pmos_on":  {"type": "pmos", "vg": "0",   "vb": "vdd"},
    "pmos_off": {"type": "pmos", "vg": "vdd", "vb": "vdd"},
}

CSV_COLUMNS = ["vdd", "temp", "w", "vd", "vs", "vg", "vb",
               "vth0", "toxe", "ndep", "u0", "xj",
               "id", "ig", "is", "ib"]
