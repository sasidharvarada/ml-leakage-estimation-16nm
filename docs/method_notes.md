# Method notes and project history

## Settings

* Model file: PTM 16 nm LP (`models/16nm_LP.pm`). Its header comment says nominal VDD = 0.9 V; the
  assigned nominal VDD of 1.0 V is used (swept 0.9 to 1.1 V). Comment lines (`*`) are ignored by ngspice.
* All settings are in `scripts/config.py`; seeds: 7 (Part A data and splits), 1007+ (rail data),
  123 (Part B / C corners).

## What changed from the first version (v2) and why

1. **Gate leakage formula.** v2 added a hand-picked set of current magnitudes per gate (for example Id of
   the OFF NMOS plus Ig of the ON PMOS). That missed junction (body) currents and other gate currents
   that SPICE counts (66 to 190 % error in INV=1, NAND2=11, NOR2=10, NOR2=11). It is replaced by the exact
   KCL evaluator described in `part_b_gate_validation.md`, which works for any gate.
2. **Sign of the currents.** v2 predicted only log|I|. Currents now get a sign classifier.
3. **Error metric.** v2 divided by max(|I|, 1e-12 A), so currents below 1 pA looked almost perfect
   (for example 0.0067 % for nmos_off). Errors are now |pred - true| / |true| on every sample.
4. **Training data at the rails.** Extra rail-focused samples (`data/rail/`) because gates operate at
   0 and VDD.
5. **Model training.** MLP moved to PyTorch (GPU) with Adam followed by L-BFGS polishing; the best model
   type is chosen per current instead of per case. Training time on an RTX 3050 laptop GPU: about 1 hour
   for everything (about 7 hours on the CPU with the scikit-learn MLP).
6. **Robustness.** Predictions clipped to the training range; a physical cap on gate current; devices
   with no field are left out.
7. **Part C.** Added the loading-aware sum and the no-ML SPICE check, which shows the composition is exact.

## Checks that separate method error from ML error

| Check | Result |
|---|---|
| Gate KCL formula with single-transistor SPICE currents vs gate SPICE | about 0.0002 % median (16 of 18 cases) |
| Circuit composition with SPICE gate results (loading-aware) vs circuit SPICE | 0.008 % median |
| Same with ML | 0.88 % (gates), 0.84 % (circuit) |

## Known limits

* NOR2 10 / NOR2 11 leakage (1e-12 to 1e-16 A) is near the simulator's numerical noise floor.
* The OFF-PMOS body current (about 1e-17 A) is noise-level; its sign is close to random.
* Gate SPICE runs: 9 of 3,600 did not converge (excluded; Part C uses the case median there).
* The circuit composition assumes ideal logic levels on internal nets (true to within microvolts here).
