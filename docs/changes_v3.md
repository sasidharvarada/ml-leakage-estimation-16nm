# Pipeline v3: what changed and why

## Problems found in v2
1. **Gate leakage formula.** Part B added hand-picked currents (for example `Id` of the OFF NMOS
   plus `Ig` of the ON PMOS) using only their magnitudes. This misses junction (body) currents and
   gate currents that SPICE counts, and it cannot be applied to new gates automatically.
   That is why INV=1, NAND2=11, NOR2=10 and NOR2=11 had 66-190 % error.
2. **Sign of the currents.** The v2 models predicted only log|I|, so currents that flow out of a
   terminal could not be handled.
3. **Error metric in Part A.** v2 divided by max(|I|, 1e-12), so currents below 1 pA (most OFF
   currents) looked almost perfect (for example 0.0067 % for nmos_off). Errors are now |pred-true|/|true|.
4. **Sparse training data at the rails.** Inside gates every terminal sits at 0 or VDD, but uniform
   sampling puts only ~4 % of samples there, so the models were least accurate exactly where they are used.

## Fixes
* `scripts/gates.py`: one generic evaluator for all gates. Gate leakage = exact KCL at the VDD side:
  sum of the currents into every terminal attached to a node connected to VDD through ON
  transistors. For ON transistors only Ig and Ib are needed (Id + Is = -(Ig + Ib)), and where three
  terminals of an OFF transistor sit at VDD the device KCL is used instead (avoids cancellation).
  **Check:** with single-transistor SPICE currents instead of ML, this formula reproduces the full
  gate SPICE leakage to about 0.0002 % (median) for all 18 cases.
* `scripts/leak_model.py` + `scripts/03_train_models.py`: per current, a regressor for log10|I| and a
  sign classifier; predictions are clipped to the range seen in training.
* `scripts/01b_generate_rail_data.py`: extra training samples with Vd and Vs concentrated at the rails
  (allowed by the project: "the number of samples may be increased"). Validation and test stay the
  official uniform datasets.
* `scripts/05_test_circuit.py`: plain sum (project method) and loading-aware sum. The loading term adds
  the input-pin current of every internal net that is HIGH (in the full circuit the driving gate supplies
  it from VDD). **Check:** the same sums built from SPICE gate results reproduce the full-circuit SPICE
  leakage to 0.008 % (loading-aware) versus 31.5 % (plain), so the composition is exact and all remaining
  error comes from the transistor models.

## Run
`bash run_all.sh` (full) or `bash run_all.sh --fast` (quick check). Log in `logs/`.
