# Scripts

Run from the repository root, in order (or use `bash run_all.sh`):

| Step | Script | Output |
|---|---|---|
| 1 | `01_generate_transistor_data.py` | `data/<case>.csv`, `netlists/transistor/*.cir` |
| 1b | `01b_generate_rail_data.py` | `data/rail/<case>.csv` |
| 2 | `02_check_data.py` | `results/part_a/kcl_check.csv`, `results/part_a/plots/` (trend plots) |
| 3 | `03_train_models.py` | `results/part_a/*.csv`, `results/part_a/plots/parity_*.png`, `saved_models/` |
| 4 | `04_validate_gates.py` | `results/part_b/` |
| 5 | `05_validate_circuit.py` | `results/part_c/` |

Shared modules: `config.py` (all settings), `spice_utils.py`, `leak_model.py`, `torch_mlp.py`,
`gates.py`, `cla3.py`. Details of each part are in `docs/`.
