# Part A scripts (run from the repo root, in order)

| Step | Command | Output | Time (approx.) |
|---|---|---|---|
| 0 | put the model file at `models/16nm_LP.pm` | | |
| 1 | `python scripts/01_generate_data.py` | `data/<case>.csv` (10,000 rows each), `netlists/transistor/*.cir` | 5 min per case |
| 2 | `python scripts/02_data_check.py` | `results/kcl_check.csv`, 3 trend plots in `results/plots/` | < 1 min |
| 3 | `python scripts/03_train_models.py --fast` | quick test of training | a few min |
| 4 | `python scripts/03_train_models.py` | `results/tables/model_comparison.csv`, `results/tables/chosen_models_test.csv`, `results/plots/parity_<case>.png`, `saved_models/<case>.joblib` | 10-15 min per case |

All settings (model file, VDD, L, ranges, seed) are in `scripts/config.py`.

Currents are the current flowing INTO each terminal, so id + ig + is + ib = 0.

## How the ML works
* Each current is predicted as  sign x 10^(log10|I|).
* log10|I| comes from a regressor (the 4 model types compared: MLP ensemble, LightGBM, XGBoost, RandomForest).
* The sign comes from a LightGBM classifier (or a constant if the sign never changes).
* Inputs: the raw sample parameters plus Vgs, Vgd, Vds, Vbs, Vbd, log|Vds|, 1/T, Vgs/toxe, Vgd/toxe.

## Using a saved model (Parts B and C)
```python
import sys; sys.path.insert(0, "scripts")
from leak_model import TransistorModel
m = TransistorModel.load("saved_models/nmos_off.joblib")
currents = m.predict(df)   # df columns: vdd, temp, w, vd, vs, vg, vb, vth0, toxe, ndep, u0, xj
```
