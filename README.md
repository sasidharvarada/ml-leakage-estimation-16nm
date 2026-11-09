# ML-Driven PVT-Aware Leakage Estimation
## 16 nm Low-Power CMOS, 3-Bit Carry-Lookahead Adder (CLA)

Digital VLSI Design Course Project. Single-transistor SPICE simulations are used to train machine learning models predicting all four terminal currents (Id, Ig, Is, Ib) under Process, Voltage, and Temperature (PVT) variation. These surrogate models are hierarchically composed to predict the static leakage of standard CMOS gates (INV, NAND2, NOR2, AND2, OR2) and a 42-gate 3-bit Carry-Lookahead Adder (CLA). Every prediction is verified against golden netlist simulations in ngspice.

### Project Specifications

| Parameter | Assigned Value | Implementation Details |
|---|---|---|
| Technology Node | 16 nm LP (Low Power) | PTM BSIM4 Model (`models/16nm_LP.pm`) |
| Nominal Supply Voltage | 1.0 V | Swept uniformly across plus/minus 10% (0.90 V to 1.10 V) |
| Channel Length | 16 nm | Lmin = 16e-9 m |
| Training Widths | 16 nm to 128 nm | Uniform sweep from 1x Lmin to 8x Lmin |
| Gate Transistor Sizing | NMOS: 32 nm, PMOS: 64 nm | WN = 2x Lmin, WP = 4x Lmin |
| Diffusion Overhang | 40 nm | Ldiff = 2.5x Lmin (AD = AS = W x Ldiff, PD = PS = 2 x (W + Ldiff)) |
| Test Circuit | 3-bit CLA | 42 gates, 204 transistors, 128 binary input vectors |
| Simulation Engine | ngspice 42 | 64-bit Linux CLI batch mode |

### Summary of Key Results

| Benchmark Level | Model / Method | Median Relative Error | Mean Accuracy | Key Finding |
|---|---|---|---|---|
| Part A (Single Devices) | PyTorch ResNet (250 epochs) | 2.63% to 6.99% | 93% to 97% | Continuous SiLU activations eliminate boundary tree artifacts |
| Part B (Logic Gates) | Calibrated KCL Evaluator | 12.49% | 87.51% | 12 of 18 gate cases operate between 6.0% and 8.9% error |
| Part C (3-Bit CLA) | Plain Hierarchical Sum | 32.41% | 67.42% | Baseline method; strictly matches prompt instruction to ignore wire loading |
| Part C (3-Bit CLA) | Loading-Aware Model | 8.42% | 90.20% | Accounts for receiver-pin gate tunneling; bias collapses to -0.05 nA |
| Part C (Physics Control) | Pure SPICE Gate Sum vs. Circuit | 32.25% | 67.75% | Proves 32% of plain error is structural circuit physics, not ML error |

### Repository Structure and Deliverables Map

| Deliverable | Description | File Location |
|---|---|---|
| 1. Datasets | Four 10,000-row CSV files with PVT parameters and terminal currents | `data/nmos_on.csv`, `data/nmos_off.csv`, `data/pmos_on.csv`, `data/pmos_off.csv` |
| 2. Example Netlists | Characterization decks, gate netlists, and full CLA netlist | `netlists/transistor/*.cir`, `netlists/gates/*.sp`, `netlists/circuit/cla3.sp` |
| 3. Data Check | KCL validation table and physical trend verification plots | `results/kcl_check.csv`, `results/plots/off_current_vs_temp.png`, `results/plots/off_current_vs_vth0.png`, `results/plots/gate_current_vs_toxe.png` |
| 4. Model Comparison Table | Benchmark of 4 model families across all 4 cases | `results/model_comparison_table.csv`, `results/model_comparison_by_target.csv` |
| 5. Chosen Models | Test-set performance summary, parity plots, and model files | `results/chosen_models_test_summary.csv`, `results/plots/parity_*.png`, `models/best_*.joblib` |
| 6. Gate Results Table | Median, bias, median error, and P95 error for all 18 cases | `results/gate_results_table.csv` |
| 7. Gate Parity Plot | Log-log scatter plot of all 3,600 gate simulations | `results/plots/gate_parity_plot.png` |
| 8. Circuit Results | Per-vector metrics, raw data, and circuit parity plots | `results/circuit_results_table.csv`, `results/part_c/circuit_raw.csv`, `results/plots/circuit_parity_plot.png`, `results/plots/circuit_parity_plot_loading.png` |
| 9. Reproduction Scripts | Sequential execution pipeline with fixed seeds | `scripts/01_generate_data.py` through `scripts/05_test_circuit.py` |
| 10. Written Report | Project documentation and error analysis | `report/final_report.pdf` (or `docs/`) |

### Detailed Documentation Sections

Detailed engineering analyses, circuit schematics, diagnostic data, and experimental logs are organized in the `docs/` directory:

1. `docs/part_a_transistor_models.md`: Dataset generation, physics sweeps, KCL residuals, and model comparison.
2. `docs/part_b_gate_validation.md`: Standard cell netlists, KCL nodal formulations, and the 18-case validation table.
3. `docs/part_c_circuit_validation.md`: 3-bit CLA topology, the 25,600 SPICE run suite, and the structural gap proof.
4. `docs/diagnostics_and_experiments.md`: The 0.0076% Oracle test, gate-region sparsity analysis, and PINN post-mortem.

### Installation and Environment Setup

Prerequisites:
```bash
sudo apt update && sudo apt install -y ngspice python3-venv python3-pip
```

Setting up Python virtual environment:

```bash

python3 -m venv venv
source venv/bin/activate
pip install numpy pandas scikit-learn xgboost torch joblib matplotlib
```
#### Complete Reproduction Sequence

To reproduce all results, tables, and figures from scratch with fixed seeds, run the scripts in order from the repository root:

```bash

python3 scripts/01_generate_data.py
python3 scripts/02_data_check.py
python3 scripts/03_train_models.py
python3 scripts/04_simulate_gates.py
rm -rf results/part_c/gate_ml_cache.csv results/part_c/gate_cases
python3 scripts/05_test_circuit.py
```
To run the complete diagnostic and error-analysis suite:
```bash

python3 scripts/06_diagnose_part_c.py
python3 scripts/07_gate_breakdown.py
python3 scripts/08_component_audit.py
python3 scripts/09_model_diagnostics.py
python3 scripts/10_oracle_single_fet.py
python3 scripts/11_gate_region_compare.py
```
