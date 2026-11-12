# Part A: transistor models

## Data generation (`scripts/01_generate_transistor_data.py`, `scripts/01b_generate_rail_data.py`)

One transistor (L = 16 nm) with an independent voltage source on every terminal is simulated in ngspice
with the assigned PTM 16 nm LP model card. Junction areas are included: AD = AS = W x Ldiff,
PD = PS = 2 (W + Ldiff), Ldiff = 40 nm. Simulator options:
`.options gmin=1e-18 abstol=1e-18 reltol=1e-6 vntol=1e-9`.

| Case | Vg | Vb |
|---|---|---|
| nmos_on | VDD | 0 |
| nmos_off | 0 | 0 |
| pmos_on | 0 | VDD |
| pmos_off | VDD | VDD |

Per sample: VDD ~ U(0.9, 1.1) V (drawn first), Vd and Vs ~ U(0, VDD), W ~ U(16, 128) nm,
T ~ U(-40, 125) C, and vth0, toxe, ndep, u0, xj each x U(0.9, 1.1) around the model-card value.
Currents are recorded as the current INTO each terminal, so Id + Ig + Is + Ib = 0.

* `data/<case>.csv`: 10,000 uniform samples per case (seed 7 + case index). These are the official
  datasets; validation and test use only these rows.
* `data/rail/<case>.csv`: 10,000 extra samples per case with Vd and Vs concentrated at the rails
  (35 % exactly 0 or VDD, 35 % within 15 % of a rail, 30 % uniform). Inside logic gates every terminal
  sits at or near 0 or VDD, where uniform sampling places only a few percent of its points. These rows
  are added to the training set only (the project allows more samples).

## Data check (`scripts/02_check_data.py`)

* Kirchhoff residual |Id + Ig + Is + Ib| / max|I|: median about 1e-6 in all four cases
  (`results/part_a/kcl_check.csv`). The largest residuals appear only where all four currents are tiny.
* Trend plots (`results/part_a/plots/`): OFF current rises with temperature and falls with vth0, and gate
  current falls with toxe, as expected from subthreshold conduction and direct tunnelling.

## Models (`scripts/03_train_models.py`, `scripts/leak_model.py`, `scripts/torch_mlp.py`)

* Currents span about 1e-22 to 1e-5 A and can be negative, so each current is predicted as
  sign x 10^(log10|I|): a regressor learns log10|I| and a LightGBM classifier learns the sign
  (a constant if the sign never changes).
* Inputs: VDD, T, log W, Vd, Vs, the five process parameters, and derived physics features
  Vds, log|Vds|, Vgs, Vgd, Vbs, Vbd, 1/T, Vgs/toxe and Vgd/toxe (PMOS voltages are sign-flipped).
* Split: 70 / 15 / 15 train / validation / test on the uniform data, seed 7. The rail rows are added to
  training; 15 % of them are held out for an extra "rail" test score.
* Model types: MLP (PyTorch, 128-128-64, SiLU, 3,000 Adam steps then L-BFGS, GPU), LightGBM, XGBoost,
  Random Forest. Predictions are clipped to the log-current range seen in training.
* Selection: for each case and each current, the type with the lowest validation median error.
* Error metric: |pred - true| / |true| on every sample (no current floor).

## Results

Validation median error, % (mean over the four currents):

| Model | nmos_on | nmos_off | pmos_on | pmos_off |
|---|---|---|---|---|
| MLP | 0.75 | 1.54 | 0.91 | 13.89 |
| LightGBM | 13.08 | 8.05 | 12.49 | 19.13 |
| XGBoost | 12.76 | 7.87 | 12.07 | 18.07 |
| Random Forest | 21.14 | 9.67 | 21.99 | 9.54 |

For pmos_off the MLP is the best type for Id, Ig and Is (0.4 to 0.8 %); its mean is high only because of
the body current Ib, for which Random Forest is chosen.

Test-set median error of the chosen models, %:

| Case | Id | Ig | Is | Ib |
|---|---|---|---|---|
| nmos_on | 0.66 | 1.74 | 0.60 | 0.30 |
| nmos_off | 0.91 | 3.59 | 1.24 | 0.32 |
| pmos_on | 1.08 | 0.34 | 0.93 | 1.46 |
| pmos_off | 0.85 | 0.39 | 0.76 | 9.30 |

The two weaker entries are tiny currents: OFF-NMOS gate current (about 1e-20 A) and OFF-PMOS body current
(about 1e-17 A, at the simulator's numerical noise floor, which also makes its sign close to random).
Neither affects gate leakage noticeably.

Files: `results/part_a/model_comparison.csv` (every type, case and current: R2 of log10|I|, median and
95th-percentile error, sign accuracy), `results/part_a/model_comparison_summary.csv`,
`results/part_a/chosen_models_test.csv`, `results/part_a/plots/parity_<case>.png`, `saved_models/<case>.joblib`.

## Using a saved model

```python
import sys; sys.path.insert(0, "scripts")
from leak_model import TransistorModel
m = TransistorModel.load("saved_models/nmos_off.joblib")
currents = m.predict(df)   # df columns: vdd, temp, w, vd, vs, vg, vb, vth0, toxe, ndep, u0, xj
```
