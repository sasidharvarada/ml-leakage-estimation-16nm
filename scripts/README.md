# Part A scripts (run from the repo root, in order)

| Step | Command | Output |
|---|---|---|
| 0 | put the model file at `models/16nm_LP.pm` | |
| 1 | `python scripts/01_generate_data.py --n 200` | quick test, 200 rows per case |
| 2 | `python scripts/01_generate_data.py` | `data/nmos_on.csv`, `nmos_off.csv`, `pmos_on.csv`, `pmos_off.csv` (10,000 rows each) and `netlists/transistor/*.cir` |
| 3 | `python scripts/02_data_check.py` | `results/kcl_check.csv`, `results/plots/*.png` |

All settings (model file, VDD, L, ranges, seed) are in `scripts/config.py`.

Currents are reported as the current flowing INTO each terminal,
so id + ig + is + ib = 0 (Kirchhoff check).
