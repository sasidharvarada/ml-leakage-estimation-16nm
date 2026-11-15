# Diagnostic Investigations and Experiments

The diagnostic scripts `06` to `12` are optional. They are not needed to reproduce Parts A to C. They record why the final method looks the way it does: where the Part C error comes from, why four gate states are inaccurate, whether the ResNet or XGBoost is the better model for the gate-relevant bias region, and whether sampling coverage explains the gate-level error. The interpretation is in `part_a_analysis.md`, `part_b_analysis.md` and `part_c_analysis.md`. This file holds the scripts, commands and raw numbers.

## 1. Overview

| Script | Question | Needs | Output |
|---|---|---|---|
| `06_diagnose_part_c.py` | Where does the Part C error come from (temperature, vth0, structural gap or ML)? | results of `05` | `results/part_c/diagnostics.txt` |
| `07_gate_breakdown.py` | Which gate states carry the gate-level error? | results of `05` | `results/part_c/gate_breakdown.txt` |
| `08_component_audit.py` | With the ML models, which way of assembling the supply current is best for the four high-error states? | ngspice, models | `results/part_c/component_audit.txt` |
| `09_model_diagnostics.py` | How large are the Part A model errors for all four currents, by temperature, vth0 and gate bias region? | data, models | `results/model_diagnostics.txt` |
| `10_oracle_single_fet.py` | With true SPICE currents (no ML), which combination of terminal currents equals the gate supply current? | ngspice | `results/part_c/oracle_single_fet.txt` |
| `11_gate_region_compare.py` | Is the weak accuracy in the gate bias region a model-choice problem? (ResNet vs XGBoost, PMOS OFF) | data, `03_train_models.py` | `results/gate_region_compare_pmos_off.txt` |
| `12_coverage_diagnostic.py` | Does the gate-level error rise when gate queries lie far from the training data? | ngspice, models, data | `results/coverage_*.csv`, `results/part_c/coverage_*.csv`, `results/plots/coverage_vs_error.png` |

Run each from the repo root, for example `python3 scripts/06_diagnose_part_c.py | tee results/part_c/diagnostics.txt`. Scripts 08 and 10 use the same 200 corners as Part B (seed 123). Script 12 takes `--corner-seed` (see section 7). The numbers below come from runs against the final models in `models/`, produced by `03_train_models.py`. Script 11 retrains its own models, as noted in section 7. The output of script 09 is not included here (section 5).

## 2. Part C error by temperature and vth0 (script 06)

Script 06 reads `results/part_c/circuit_raw.csv` and prints, for four temperature bins and four NMOS vth0 quartiles:

* the loading-aware and plain-sum error (median, mean, 95th percentile, signed median),
* a control, the SPICE gate-sum against full-circuit SPICE (the structural gap, no ML),
* the gate-level ML error on isolated gates.

All tables are in `part_c_analysis.md`, section 4. The main points:

* Structural gap by temperature bin: 37.37%, 36.61%, 27.32%, 30.69% (by vth0 bin: 36.74%, 34.74%, 26.78%, 30.31%).
* Loading-aware median error by temperature bin: 7.48%, 4.50%, 4.20%, 10.21%. The signed median is -10.21% in the hottest bin.
* Loading-aware median error by vth0 bin: 9.28%, 6.21%, 6.16%, 5.38%.
* Gate-level ML median error by temperature bin: 9.44%, 10.06%, 9.45%, 11.42% (by vth0 bin: 11.17%, 9.33%, 9.42%, 10.11%). The mean errors in the same output (23% to 238% by temperature bin) are inflated by the high-error gate states.

## 3. Per-state gate error (script 07)

Statistics over runs with SPICE leakage above 1e-13 A, from `results/part_c/gate_ml_cache.csv`. The SPICE median here is over those runs only, so it differs from the Part B table for the states near the floor (for example NOR2 10: 2.006e-12 A here, 8.504e-13 A in Part B). The signed value is the median of (ML - SPICE) / SPICE in percent.

| Gate | Input | SPICE median (A) | Median error (%) | Mean error (%) | P95 error (%) | Signed (%) |
|---|---|---|---|---|---|---|
| AND2 | 00 | 9.391e-10 | 6.618 | 8.109 | 22.76 | -0.756 |
| AND2 | 01 | 6.751e-10 | 6.091 | 7.81 | 22.11 | -2.948 |
| AND2 | 10 | 6.725e-10 | 5.84 | 8.167 | 24.8 | -2.891 |
| AND2 | 11 | 3.154e-10 | 11.77 | 12.84 | 29.48 | +3.389 |
| INV | 0 | 2.251e-10 | 8.397 | 10.26 | 25.3 | +5.226 |
| INV | 1 | 1.579e-11 | 52.71 | 352.6 | 1859 | +10.84 |
| NAND2 | 00 | 4.088e-10 | 8.563 | 10.58 | 25.38 | +4.626 |
| NAND2 | 01 | 2.251e-10 | 8.401 | 10.26 | 25.3 | +5.226 |
| NAND2 | 10 | 2.106e-10 | 8.881 | 10.53 | 25.27 | +5.235 |
| NAND2 | 11 | 2.98e-11 | 53.77 | 650.4 | 2128 | +12.13 |
| NOR2 | 00 | 4.503e-10 | 8.395 | 10.26 | 25.3 | +5.227 |
| NOR2 | 01 | 2.508e-10 | 9.545 | 11.41 | 26.42 | +3.5 |
| NOR2 | 10 | 2.006e-12 | 144.2 | 531.7 | 2736 | +144.2 |
| NOR2 | 11 | 1.001e-12 | 68.18 | 62.59 | 87.89 | -66.68 |
| OR2 | 00 | 9.207e-10 | 6.25 | 7.323 | 17.46 | -0.573 |
| OR2 | 01 | 4.871e-10 | 8.376 | 9.709 | 23.64 | +3.613 |
| OR2 | 10 | 2.279e-10 | 9.036 | 10.56 | 24.98 | +5.913 |
| OR2 | 11 | 2.265e-10 | 8.485 | 10.24 | 25.3 | +5.238 |

INV 1, NAND2 11, NOR2 10 and NOR2 11 stand out. They are the output-low states whose only formula term is the |Id| of an OFF PMOS.

## 4. Component audit with the ML models (script 08)

For the four high-error states, script 08 takes the SPICE node voltages, asks the ML models for all four terminal-current magnitudes of each PMOS, and compares four ways to assemble the supply current. Median error (%) against gate SPICE, over runs above 1e-13 A:

| State | SPICE median (A) | |Id| formula (final) | Is only | Is + Ib | |Id| formula + Ib |
|---|---|---|---|---|---|
| INV 1 | 1.491e-11 | 52.71 | 20.82 | 20.69 | 52.95 |
| NAND2 11 | 2.98e-11 | 53.77 | 21.45 | 21.02 | 53.63 |
| NOR2 10 | 8.504e-13 | 144.2 | 52.37 | 40.35 | 152.4 |
| NOR2 11 | 1.109e-14 | 68.18 | 87.62 | 10.19 | 17.78 |

The 95th-percentile errors are 1,859 / 54.22 / 1,860 for INV 1, 2,128 / 55.52 / 2,128 for NAND2 11 (|Id| formula / Is + Ib / |Id| formula + Ib), and 2,736 / 100.7 / 2,736 for NOR2 10. For NOR2 11 they are 87.89 / 73.2 / 56.84. All candidates use magnitudes only, so a candidate with the wrong current direction over-predicts.

## 5. Per-target model diagnostics (script 09)

Script 09 re-scores the saved Part A models on their own test split (seed 71) for all four currents (Id, Ig, Is, Ib), with the denominator floored at 1e-18 A instead of 1e-12 A. It breaks the errors down by temperature bin, vth0 quartile and, for the OFF models, the bias region the gates use (NMOS OFF: Vd at least 0.8 VDD and Vs at most 0.2 VDD; PMOS OFF: Vs at least 0.8 VDD and Vd at most 0.2 VDD). It prints the number of training samples in that region for each case, and the median and 95th-percentile error of each subset. Its output is saved to `results/model_diagnostics.txt` and is not reproduced here, so this documentation does not quote any of its figures.

## 6. Single-FET oracle (script 10)

Each PMOS of a gate is re-simulated in SPICE as a single transistor at exactly the bias it has in the gate, using the same netlist builder as `01_generate_data.py`. The true terminal currents are combined with each formula and compared with the full-gate SPICE leakage. No ML is involved.

* `id_formula`: sum of |Id| of the devices used by the final gate formula.
* `kcl`: |sum of Is of the PMOS whose source is on Vdd + sum of Ib of all PMOS| (signed).
* `kcl_abs`: the same with magnitudes.

Median errors over runs where the gate leakage exceeds 1e-16 A:

| Case | n | SPICE median (A) | Candidate | Median error (%) | P95 error (%) | Median error above 80 C (%) |
|---|---|---|---|---|---|---|
| INV 1 | 200 | 1.491e-11 | id_formula | 52.62 | 2595 | 7.958 |
| INV 1 | 200 | 1.491e-11 | kcl | 0.007552 | 0.024 | 0.005916 |
| INV 1 | 200 | 1.491e-11 | kcl_abs | 0.007592 | 0.02734 | 0.005916 |
| NAND2 11 | 200 | 2.98e-11 | id_formula | 52.63 | 2595 | 7.96 |
| NAND2 11 | 200 | 2.98e-11 | kcl | 0.007613 | 0.02067 | 0.00647 |
| NAND2 11 | 200 | 2.98e-11 | kcl_abs | 0.007782 | 0.02465 | 0.00647 |
| NOR2 10 | 200 | 8.504e-13 | id_formula | 272.9 | 26410 | 23.39 |
| NOR2 10 | 200 | 8.504e-13 | kcl | 0.01484 | 0.6407 | 0.01094 |
| NOR2 10 | 200 | 8.504e-13 | kcl_abs | 0.01484 | 0.8892 | 0.01094 |
| NOR2 11 | 186 | 1.109e-14 | id_formula | 228.9 | 8452 | 50.27 |
| NOR2 11 | 186 | 1.109e-14 | kcl | 0.4174 | 48.45 | 0.0257 |
| NOR2 11 | 186 | 1.109e-14 | kcl_abs | 0.4212 | 31.64 | 0.0257 |
| INV 0 (control) | 200 | 2.251e-10 | kcl | 13.19 | 123.3 | 4.807 |
| INV 0 (control) | 200 | 2.251e-10 | kcl_abs | 13.19 | 123.3 | 4.807 |

Conclusions:

1. In the four output-low states the supply current equals Is of the source-on-Vdd PMOS plus Ib of all PMOS, to within 0.0076% (INV 1, NAND2 11) and 0.42% (NOR2 10 and 11). The single-FET netlist matches the gate netlist.
2. The |Id| of an OFF PMOS is the wrong quantity. It includes gate-edge tunneling that the input source supplies, not the Vdd rail. Its error drops in corners above 80 C, where subthreshold current dominates.
3. The INV 0 control does not reproduce the Vdd current as closely (13.19% median error). Its cause was not investigated, so the near-exact match applies to the four output-low states and not to every state.

## 7. ResNet versus XGBoost in the gate bias region (script 11)

Script 11 trains XGBoost and the ResNet on the Part A training split (same settings and seed 71 as `03_train_models.py`) and compares them on the validation split only. The metric scores all four targets with both sides clipped at 1e-18 A. The ResNet is retrained, so it is not bit-identical to `models/best_pmos_off.joblib`.

Regions for PMOS OFF:

* Region A: Vs at least 0.8 VDD and Vd at most 0.2 VDD (full Vds at the rail).
* Region B: Vs and Vd both at least 0.8 VDD (Vds near 0).
* Elsewhere: everything else.

Training samples in region A: 265. In region B: 288. Of 7,000.

Median error (%) on the validation split, by target (the 95th-percentile columns are in the script output):

| Model | Subset | n | Id | Ig | Is | Ib | Mean over targets |
|---|---|---|---|---|---|---|---|
| ResNet | all validation | 1,500 | 12.57 | 8.344 | 10.42 | 29.18 | 15.13 |
| XGBoost | all validation | 1,500 | 6.512 | 6.477 | 6.507 | 16.79 | 9.072 |
| ResNet | elsewhere | 1,401 | 12.22 | 8.001 | 10.08 | 28.55 | 14.71 |
| XGBoost | elsewhere | 1,401 | 6.256 | 6.429 | 6.212 | 16.86 | 8.94 |
| ResNet | region A | 52 | 16.73 | 11.55 | 18.97 | 29.78 | 19.26 |
| XGBoost | region A | 52 | 8.669 | 4.889 | 49 | 12.45 | 18.75 |
| ResNet | region B | 47 | 23.01 | 10.1 | 18.1 | 37.99 | 22.3 |
| XGBoost | region B | 47 | 20.35 | 18.61 | 16.88 | 25.25 | 20.27 |

Bootstrap with 2,000 resamples. The difference is XGBoost minus ResNet in the mean-over-targets median error, so a negative value means XGBoost has the lower error:

| Subset | n | Difference | 90% interval | ResNet better in |
|---|---|---|---|---|
| All validation | 1,500 | -6.04 | [-6.74, -5.24] | 0.0% of resamples |
| Region A | 52 | -0.92 | [-7.05, 4.31] | 42.6% |
| Region B | 47 | -1.89 | [-7.27, 3.77] | 28.5% |
| Elsewhere | 1,401 | -5.69 | [-6.43, -4.84] | 0.0% |

A gap is real only if the 90% interval excludes 0. XGBoost has the lower error overall and outside the gate regions. In regions A and B, with 52 and 47 samples, the intervals include 0, so neither model is shown to be better there.

## 8. Training-data coverage of gate queries (script 12)

Script 12 reproduces each model's training split, builds a nearest-neighbour reference (mean distance to 5 neighbours in the standardised 18-feature space) from the held-out rows, and computes, for every transistor query a gate makes, the percentile of its distance within the held-out distances. A high percentile means the query lies in a sparse region. It records the worst percentile among a gate's transistors and compares it with the gate-level error. In-distribution queries would give about 5% of queries above the 95th percentile and 1% above the 99th. Script 12 matched split seed 71 for all four models, in line with `03_train_models.py`.

**Corner seed.** The run reported below used the cached gate SPICE results `coverage_spice_cache_seed7_n200.csv`, that is, corner seed 7. Part B uses seed 123. The script's default is 7. The per-state errors therefore differ slightly from the Part B table (NOR2 10 is 153.71% here and 144.15% in Part B). For results on the Part B corners, run `python3 scripts/12_coverage_diagnostic.py --corner-seed 123`.

Coverage by transistor case:

| Case | Queries | Median percentile | Share >= 95th | Share >= 99th | Training samples |
|---|---|---|---|---|---|
| NMOS OFF | 2,985 | 93.83 | 0.464 | 0.211 | 7,000 |
| NMOS ON | 785 | 88.00 | 0.344 | 0.066 | 7,000 |
| PMOS OFF | 2,985 | 94.30 | 0.490 | 0.222 | 7,000 |
| PMOS ON | 3,776 | 85.47 | 0.301 | 0.100 | 7,000 |

Gate-level error against the worst-transistor percentile (runs above 1e-13 A):

| Percentile bin | n | Median error (%) | P95 error (%) |
|---|---|---|---|
| < 50 | 69 | 65.23 | 1569.34 |
| 50 to 90 | 719 | 12.39 | 372.91 |
| 90 to 99 | 1,506 | 9.19 | 87.53 |
| >= 99 | 1,115 | 10.03 | 63.64 |

Spearman rho between the worst-transistor percentile and the error: -0.098 (p = 1.1e-08, n = 3,409).

Per gate state, sorted by error:

| Gate | Input | Median error (%) | Median worst percentile | Share >= 95th | Main case |
|---|---|---|---|---|---|
| NOR2 | 10 | 153.71 | 76.00 | 0.12 | pmos_off |
| NOR2 | 11 | 66.79 | 67.45 | 0.10 | pmos_off |
| NAND2 | 11 | 55.33 | 97.05 | 0.62 | pmos_off |
| INV | 1 | 55.14 | 97.07 | 0.62 | pmos_off |
| AND2 | 11 | 12.40 | 99.05 | 0.82 | pmos_off |
| NOR2 | 01 | 9.97 | 97.37 | 0.66 | pmos_off |
| NAND2 | 10 | 8.83 | 91.35 | 0.39 | pmos_on |
| OR2 | 01 | 8.69 | 99.05 | 0.82 | pmos_off |
| NAND2 | 00 | 8.41 | 93.77 | 0.44 | pmos_on |
| NAND2 | 01 | 8.31 | 97.43 | 0.68 | nmos_off |
| INV | 0 | 8.31 | 97.43 | 0.68 | nmos_off |
| NOR2 | 00 | 8.31 | 97.43 | 0.68 | nmos_off |
| OR2 | 10 | 8.20 | 97.48 | 0.69 | nmos_off |
| OR2 | 11 | 8.09 | 97.45 | 0.69 | nmos_off |
| AND2 | 00 | 6.89 | 98.43 | 0.79 | pmos_off |
| AND2 | 10 | 6.65 | 98.32 | 0.75 | pmos_off |
| AND2 | 01 | 6.51 | 99.07 | 0.84 | pmos_off |
| OR2 | 00 | 6.31 | 99.07 | 0.84 | pmos_off |

The distance is Euclidean in the standardised feature space, and several features are linear combinations of others, so the percentiles are a relative ranking and not calibrated probabilities. Correlation is not proof of cause.

## 9. Other experiments

### Alternative training script (`03_train_models_v2.py`)

This script is not part of the final pipeline: `models/` and all reported results come from `03_train_models.py`. For reference, it differs from the final script in these ways:

* It scores all four targets (Id, Ig, Is, Ib), with both the prediction and SPICE value clipped at the 1e-18 A floor.
* It selects the best model per case on the validation set (lowest mean over the four targets of the median relative error).
* It standardises the ResNet targets during training and folds the scaling back into the last layer, so the saved model still outputs log10|I|.
* It uses a larger XGBoost (450 trees, depth 9, learning rate 0.03), a ResNet learning rate of 2.5e-3 and seed 42. The features, split fractions, Ridge and Random Forest settings and the ResNet architecture are unchanged.
* On its first run it backs up the existing models and result tables to `models/v1_backup/` and `results/v1_backup/`.

### Experiments carried over from an earlier version of this document

The following two results come from the previous version of this file. No script in `scripts/` reproduces them.

**PINN KCL penalty.** A physics-informed network was tested to enforce charge conservation by penalising (Id + Ig + Is + Ib) in linear scale inside the loss. Reconstructing linear currents as 10^y and dividing by sub-picoampere denominators caused gradient explosion (gradients above 10^12) and training diverged. Back-propagating linear current sums across 9 decades of log-scale targets is numerically unstable without bounded relaxation.

**Width-normalised targets (I / W).** Training on current density reduced single-device variance on PMOS OFF. According to the earlier write-up, the improvement was absorbed at the circuit level, because interconnect tunneling and internal stack capacitance scale non-linearly with fan-out.