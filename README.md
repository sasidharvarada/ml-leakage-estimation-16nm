# ML leakage estimation for 16 nm LP transistors, gates and a 3-bit adder

Machine-learning surrogates for static leakage current, trained on ngspice (BSIM4, 16 nm LP model card) and validated at three levels:

* **Part A:** single transistors (NMOS and PMOS, ON and OFF), four terminal currents each.
* **Part B:** five logic cells (INV, NAND2, NOR2, AND2, OR2), 18 input states, 200 random PVT corners.
* **Part C:** a 3-bit carry-lookahead adder (42 gates, 204 transistors), 128 input vectors x 200 corners.

Currents are the current flowing INTO each terminal, so id + ig + is + ib = 0.

## Documentation

| File | Content |
|---|---|
| `part_a_transistor_models.md` | Datasets, KCL audit, trend checks, model comparison, test results |
| `part_a_analysis.md` | Interpretation of Part A: metrics, PMOS OFF comparison, model choice, limitations |
| `part_b_gate_validation.md` | Gate topologies, ML assembly method, Deliverable 6 table and plot |
| `part_b_analysis.md` | Interpretation of Part B: error groups, the four high-error states, coverage |
| `part_c_circuit_validation.md` | CLA, control experiment, Deliverable 8 results |
| `part_c_analysis.md` | Interpretation of Part C: structural gap, loading-aware model, residual error |
| `diagnostics_and_experiments.md` | Optional scripts 06 to 12: commands and raw outputs |

## Requirements

* Python 3 and `ngspice` on the PATH (Parts A to C and scripts 08, 10, 12 run ngspice).
* Python packages imported by the scripts: `numpy`, `pandas`, `scikit-learn`, `xgboost`, `torch`, `matplotlib`, `joblib`, and `scipy` (script 12 only). `lightgbm` and `tqdm` are not imported by any script.
* The model card at `models/16nm_LP.pm`. It must contain exactly one NMOS and one PMOS `.model` card (`spice_utils.split_models` checks this).

All Part A settings (model file, VDD, L, ranges, seed) are in `scripts/config.py`.

## Running the pipeline

Run everything from the repo root, in order.

| Step | Command | Output | Time (approx.) |
|---|---|---|---|
| 1 | `python3 scripts/01_generate_data.py` | `data/<case>.csv` (10,000 rows each), `netlists/transistor/<case>.cir` | 5 min per case |
| 2 | `python3 scripts/02_data_check.py` | `results/kcl_check.csv`, 3 trend plots in `results/plots/` | < 1 min |
| 3 | `python3 scripts/03_train_models.py` | `models/best_<case>.joblib`, `results/model_comparison_table.csv`, `results/chosen_models_test_summary.csv`, `results/plots/parity_<case>.png` | 10-15 min per case |
| 4 | `python3 scripts/04_simulate_gates.py` | `results/gate_results_table.csv`, `results/plots/gate_parity_plot.png` | |
| 5 | `python3 scripts/05_test_circuit.py --seed 123` | `results/circuit_results_table.csv`, `results/part_c/circuit_raw.csv`, `results/plots/circuit_parity_plot.png`, `results/plots/circuit_parity_plot_loading.png`, `netlists/circuit/cla3.sp` | |

Notes:

* `01_generate_data.py --n 200` and `05_test_circuit.py --corners 10` give quick test runs. `05` also takes `--vectors N` and `--time-budget SECONDS` (progress is cached and a rerun continues).
* Step 4 uses corner seed 123, fixed inside the script. Pass `--seed 123` in step 5 so that Part C uses the same corners. The script's built-in default is 7.
* Step 5 caches gate and circuit SPICE results in `results/part_c/` (`gate_ml_cache.csv`, `gate_cases/`, `spice_cache/`). The caches are checked only by size and corner index, not by seed or model. After retraining the models or changing the seed, delete them before rerunning step 5.
* `03_train_models_v2.py` is an alternative training script and is not used for the reported results (see `diagnostics_and_experiments.md`, section 9).

### Optional diagnostics

Not needed for the deliverables. They show why the final method looks the way it does.

| Script | Command | Output |
|---|---|---|
| 06 | `python3 scripts/06_diagnose_part_c.py \| tee results/part_c/diagnostics.txt` | Part C error by temperature and vth0 |
| 07 | `python3 scripts/07_gate_breakdown.py \| tee results/part_c/gate_breakdown.txt` | per-state gate error |
| 08 | `python3 scripts/08_component_audit.py \| tee results/part_c/component_audit.txt` | alternative supply-current formulas with ML |
| 09 | `python3 scripts/09_model_diagnostics.py \| tee results/model_diagnostics.txt` | per-target Part A errors by region |
| 10 | `python3 scripts/10_oracle_single_fet.py \| tee results/part_c/oracle_single_fet.txt` | single-FET SPICE oracle |
| 11 | `python3 scripts/11_gate_region_compare.py \| tee results/gate_region_compare_pmos_off.txt` | ResNet vs XGBoost on PMOS OFF |
| 12 | `python3 scripts/12_coverage_diagnostic.py --corner-seed 123` | training-data coverage of gate queries |

Scripts 06 and 07 need the results of step 5. Script 11 needs `scripts/03_train_models.py` next to it and retrains both models.

## How the ML works

* **Targets:** log10(max(|I|, 1e-18 A)) for Id, Ig, Is and Ib. The models predict magnitudes. In Part A the sign of the SPICE reference is used to restore the sign. Parts B and C work with magnitudes.
* **Inputs (18):** vdd, temp, w, vd, vs, vg, vb, vth0, toxe, ndep, u0, xj, plus vds, |vds|, vgs, vbs, vgd and overdrive (vgs - vth0), standardised with a scaler fit on the training split.
* **Models compared per case:** Ridge, Random Forest, XGBoost and a PyTorch ResNet (18 -> 128 -> 128 with skip -> 64 -> 4). The split is 70/15/15 with `random_state = 71`.
* **Chosen model:** the ResNet for all four cases (set in `03_train_models.py`). See `part_a_analysis.md`, section 6.

## Using the saved models (Parts B and C)

The bundles in `models/best_<case>.joblib` hold the model, the scaler, the feature names and the model type. They were pickled from a script run as `__main__`, so the classes `LeakageResNet`, `PyTorchWrapper`, `MultiOutputModel` and `MultiXGB` must be registered on `__main__` before loading. Scripts 05 and 08 to 12 do this with the same pattern:

```python
import importlib.util, sys
spec = importlib.util.spec_from_file_location("part_b", "scripts/04_simulate_gates.py")
pb = importlib.util.module_from_spec(spec)
sys.modules["part_b"] = pb
spec.loader.exec_module(pb)
for name in ("LeakageResNet", "PyTorchWrapper", "MultiOutputModel", "MultiXGB"):
    setattr(sys.modules["__main__"], name, getattr(pb, name))

ev = pb.GateMLEvaluator()
# magnitudes of [Id, Ig, Is, Ib] in amperes
currents = ev.predict_fet("nmos_off", vdd=1.0, temp=27.0, w=pb.WN,
                          vd=1.0, vs=0.0, vg=0.0, vb=0.0, proc=pb.NOM_NMOS)
```

Run it from the repo root with `scripts/` importable (for example `PYTHONPATH=scripts python3 your_script.py`).

## Headline results

| Level | Result |
|---|---|
| Part A (test set, ResNet, Id) | log-space R2 0.9808 to 0.9994, median error 0.008% to 3.97% |
| Part B (3,394 gate runs above 1e-13 A) | overall median error 10.07% |
| Part C, plain hierarchical sum | median error 34.0%, mean accuracy 66.62% |
| Part C, loading-aware model | median error 6.73%, mean accuracy 92.07% |

See the analysis files for how to read these numbers.