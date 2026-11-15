# Over-fit / under-fit check of the saved transistor models

Loss = mean squared error of log10|I| (decades^2), the quantity the regressors are trained on; loss_99% leaves out the worst 1 % of points (currents passing through zero). Errors are |pred - SPICE| / |SPICE|. Verdict: over-fit if validation/test median error is more than 2x the training error and more than 1 point worse; under-fit if training median error > 5 %.

## Data points per case

| case | dataset_rows | train | validation | test | spec_train/val/test | rail_rows_extra | train_total_rail_variant | train_total_no_rail_variant |
|---|---|---|---|---|---|---|---|---|
| nmos_on | 10000 | 7000 | 1500 | 1500 | 7000/1500/1500 | 10000 | 15500 | 7000 |
| nmos_off | 10000 | 7000 | 1500 | 1500 | 7000/1500/1500 | 10000 | 15500 | 7000 |
| pmos_on | 10000 | 7000 | 1500 | 1500 | 7000/1500/1500 | 10000 | 15500 | 7000 |
| pmos_off | 10000 | 7000 | 1500 | 1500 | 7000/1500/1500 | 10000 | 15500 | 7000 |

## Variant `rail` (models in `saved_models/`)

| case | current | model | train_loss | val_loss | test_loss | train_loss_99% | val_loss_99% | test_loss_99% | train_med_% | val_med_% | test_med_% | rail_test_med_% | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nmos_on | id | MLP | 2.299e-05 | 0.0001882 | 0.000255 | 1.788e-05 | 5.844e-05 | 8.456e-05 | 0.535 | 0.5944 | 0.6596 | 0.5652 | good fit |
| nmos_on | ig | MLP | 0.002399 | 3.662 | 4.191 | 0.001504 | 0.9419 | 1.828 | 0.8047 | 1.558 | 1.736 | 1.042 | slight gap |
| nmos_on | is | MLP | 1.974e-05 | 0.001066 | 0.0002168 | 1.526e-05 | 3.541e-05 | 4.957e-05 | 0.494 | 0.5419 | 0.5992 | 0.5263 | good fit |
| nmos_on | ib | MLP | 7.644e-06 | 3.355e-05 | 3.268e-05 | 4.421e-06 | 1.128e-05 | 1.379e-05 | 0.245 | 0.2873 | 0.2995 | 0.2583 | good fit |
| nmos_off | id | MLP | 3.962e-05 | 0.004288 | 0.004953 | 3.152e-05 | 0.0004468 | 0.0005039 | 0.732 | 0.9403 | 0.9131 | 1.037 | good fit |
| nmos_off | ig | MLP | 0.003566 | 0.001606 | 0.04623 | 0.000789 | 0.0007932 | 0.0008747 | 3.537 | 3.66 | 3.592 | 6.442 | good fit |
| nmos_off | is | MLP | 8.695e-05 | 0.003132 | 0.004383 | 7.189e-05 | 0.0005614 | 0.0006093 | 1.054 | 1.262 | 1.245 | 1.428 | good fit |
| nmos_off | ib | MLP | 5.503e-06 | 1.321e-05 | 6.913e-05 | 4.142e-06 | 4.947e-06 | 5.945e-06 | 0.287 | 0.2855 | 0.3217 | 0.4145 | good fit |
| pmos_on | id | MLP | 3.674e-05 | 0.007291 | 0.006717 | 3.136e-05 | 0.001305 | 0.0007256 | 0.7573 | 0.9357 | 1.076 | 0.8235 | good fit |
| pmos_on | ig | MLP | 1.443e-05 | 3.007e-05 | 4.378e-05 | 9.686e-06 | 1.468e-05 | 1.611e-05 | 0.3123 | 0.347 | 0.3429 | 0.2938 | good fit |
| pmos_on | is | MLP | 2.422e-05 | 0.007699 | 0.004939 | 2.093e-05 | 0.0005252 | 0.0005226 | 0.6553 | 0.9219 | 0.9277 | 0.7641 | good fit |
| pmos_on | ib | MLP | 0.0004717 | 1.271 | 2.071 | 1.711e-05 | 0.03291 | 0.2606 | 0.5766 | 1.428 | 1.456 | 1.012 | slight gap |
| pmos_off | id | MLP | 4.537e-05 | 0.004651 | 0.004555 | 3.589e-05 | 0.0002936 | 0.0004757 | 0.7446 | 0.8367 | 0.8519 | 1.285 | good fit |
| pmos_off | ig | MLP | 7.592e-06 | 0.0001603 | 0.1638 | 6.169e-06 | 1.727e-05 | 1.227e-05 | 0.3383 | 0.3824 | 0.3883 | 0.4283 | good fit |
| pmos_off | is | MLP | 4.016e-05 | 0.009571 | 0.002487 | 3.233e-05 | 0.0005892 | 0.0001886 | 0.6705 | 0.7718 | 0.7622 | 1.249 | good fit |
| pmos_off | ib | RandomForest | 2.652 | 17.9 | 18.64 | 2.468 | 16.71 | 17.53 | 3.67 | 11.37 | 9.303 | 32.1 | OVER-FIT (noise-level current < 1 fA, not meaningful) |

Verdicts: good fit: 13, slight gap: 2, OVER-FIT (noise-level current < 1 fA, not meaningful): 1

