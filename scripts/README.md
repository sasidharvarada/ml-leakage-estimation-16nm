# ML-Driven PVT-Aware Leakage Estimation (16 nm LP CMOS)

Predicts transistor, logic-gate, and 3-bit carry-lookahead adder (CLA) leakage under PVT variation using ngspice (`models/16nm_LP.pm`) and ML models.

## Setup

**Prerequisites:** Python 3.10+ and `ngspice` available on `PATH` (PyTorch uses CUDA automatically if a GPU is present, or falls back to CPU).

```bash
pip install -r requirements.txt
```

Run the entire pipeline from the repository root:

```bash
bash run_all.sh              # full flow (data generation + training + validation)
bash run_all.sh --skip-data  # reuse existing data/ CSVs
```

---

## Project Parts

Detailed methods and results for each stage are in `docs/`:

* **Part A — Transistor Models** ([`docs/part_a_transistor_models.md`](docs/part_a_transistor_models.md)): Simulates single NMOS/PMOS devices (ON/OFF) across PVT, validates KCL/trends, and trains signed log-current ML models (`Id`, `Ig`, `Is`, `Ib`).
* **Part B — Gate Validation** ([`docs/part_b_gate_validation.md`](docs/part_b_gate_validation.md)): Simulates INV, NAND2, NOR2, AND2, and OR2 across 200 corners (18 cases) and predicts gate leakage via exact KCL from the Part A models.
* **Part C — 3-Bit CLA Validation** ([`docs/part_c_circuit_validation.md`](docs/part_c_circuit_validation.md)): Simulates a 42-gate 3-bit CLA across all 128 input vectors × 200 corners and evaluates both plain and loading-aware ML gate composition.
* **Design & History Notes**: [`docs/method_notes.md`](docs/method_notes.md)

---

## Scripts

Run individually from the repository root in order (`python scripts/<name>.py`):

| Step | Script | What it does | Output |
|---|---|---|---|
| 1 | `01_generate_transistor_data.py` | Draws 10,000 uniform PVT samples per case and runs single-FET ngspice simulations | `data/<case>.csv`, `netlists/transistor/*.cir` |
| 1b | `01b_generate_rail_data.py` | Generates extra training-only samples with $V_d, V_s$ concentrated near `0` and `VDD` | `data/rail/<case>.csv` |
| 2 | `02_check_data.py` | Checks KCL ($I_d+I_g+I_s+I_b \approx 0$) and generates physical trend plots | `results/part_a/kcl_check.csv`, `results/part_a/plots/` |
| 3 | `03_train_models.py` | Trains MLP, LightGBM, XGBoost, and RF; picks best per current on val set and evaluates test set | `saved_models/*.joblib`, `results/part_a/*.csv`, parity plots |
| 4 | `04_validate_gates.py` | Runs 200-corner SPICE gate simulations and compares against KCL-based ML gate predictions | `results/part_b/`, `netlists/gates/*.sp` |
| 5 | `05_validate_circuit.py` | Runs 200-corner × 128-vector CLA SPICE simulations and evaluates plain & loading-aware ML sums | `results/part_c/`, `netlists/circuit/cla3.sp` |

**Optional diagnostics** (run after steps 4–5):
* `06_diagnose_part_c.py` — breaks down Part C error by temperature and $V_{th0}$ and separates structural vs. ML error.
* `07_gate_breakdown.py` — prints per-gate, per-input error statistics from Part B.
* `10_oracle_single_fet.py` — tests the `gates.py` KCL formula using true single-FET SPICE currents instead of ML.

**Shared modules:** `config.py` (all sweep settings and seeds), `spice_utils.py`, `leak_model.py`, `torch_mlp.py`, `gates.py`, `cla3.py`, `variant.py` (`--no-rail` output routing).
