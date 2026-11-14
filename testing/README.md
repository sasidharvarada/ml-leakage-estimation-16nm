# Testing and validation

Checks that the transistor models neither over-fit nor under-fit, and that the whole flow works on new,
unseen inputs (as a TA would test it). Run from the repository root.

```bash
bash testing/run_tests.sh          # everything (~2-3 h, mostly the learning curves on the GPU)
bash testing/run_tests.sh --fast   # quick version (~15 min)
```

| Script | What it does | Time | Output (`testing/results/`) |
|---|---|---|---|
| `01_check_overfit.py` | Loads the saved models and reports train / validation / test **loss** and errors for every case and current, with a verdict (good fit / over-fit / under-fit). Also counts the data points per split. | ~1 min | `overfit/` |
| `02_learning_curves.py` | Re-trains the MLP and records the train / validation / test loss **during training** (loss vs iteration) and for **500 to 7,000 training rows** (loss vs data size). | ~2-3 h (GPU) | `learning_curves/<rail\|no_rail>/` |
| `03_test_cases.py` | **New test cases** with a fresh seed (2026): new single-transistor samples (uniform and gate-like), all 18 gate cases at 50 new corners, the CLA at 20 new corners. Also takes your own test point (`--point`) or a CSV (`--csv`). | ~10-20 min | `test_cases/` |

## Definitions

* **Data split** (same as training, seed 7): each 10,000-row dataset → 7,000 train, 1,500 validation,
  1,500 test. The rail variant adds 8,500 rail-focused rows to training only; validation and test are
  always the official uniform rows. `overfit/data_counts.csv` lists the counts.
* **Loss** = mean squared error of log10|I| (decades²), the quantity the regressors minimise.
  `loss_99%` is the same over the best 99 % of points: a current that passes through zero (|I| → 0) can be
  many decades off in log space, and a single such point dominates the plain mean.
* **Verdict**: *over-fit* if the validation or test median error is more than twice the training error and
  more than 1 point worse; *under-fit* if the training median error is above 5 %; currents below 1 fA are at
  the simulator noise floor and marked as not meaningful.

## Your own test cases

```bash
# one point (process parameters default to the model-card values; vg, vb follow the case)
python testing/03_test_cases.py --point case=nmos_off,vdd=1.0,temp=85,w=48e-9,vd=1.0,vs=0
python testing/03_test_cases.py --point case=pmos_on,vdd=0.95,temp=-20,w=96e-9,vd=0,vs=0.95,vth0=-0.4

# many points from a CSV (columns vdd,temp,w,vd,vs[,vth0,toxe,ndep,u0,xj][,id,ig,is,ib])
python testing/03_test_cases.py --csv my_points.csv --case pmos_on

# another fresh random draw at all levels
python testing/03_test_cases.py --seed 99 --n 500 --gate-corners 100 --cla-corners 20
```

Missing currents are simulated with ngspice, so the ML prediction is always compared with SPICE.
