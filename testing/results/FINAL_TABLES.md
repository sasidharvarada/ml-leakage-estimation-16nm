# Final testing tables

## Data points per case (project: 7,000 / 1,500 / 1,500)

| case | dataset_rows | train | validation | test | spec_train/val/test | rail_rows_extra | train_total_rail_variant | train_total_no_rail_variant |
|---|---|---|---|---|---|---|---|---|
| nmos_on | 10000 | 7000 | 1500 | 1500 | 7000/1500/1500 | 10000 | 15500 | 7000 |
| nmos_off | 10000 | 7000 | 1500 | 1500 | 7000/1500/1500 | 10000 | 15500 | 7000 |
| pmos_on | 10000 | 7000 | 1500 | 1500 | 7000/1500/1500 | 10000 | 15500 | 7000 |
| pmos_off | 10000 | 7000 | 1500 | 1500 | 7000/1500/1500 | 10000 | 15500 | 7000 |

## Models 'rail': median error and accuracy (100 - median error)

| case | current | model | train_err_% | val_err_% | test_err_% | new_cases_err_% | train_acc_% | val_acc_% | test_acc_% | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| nmos_on | id | MLP | 0.535 | 0.594 | 0.660 | 0.634 | 99.465 | 99.406 | 99.340 | good fit |
| nmos_on | ig | MLP | 0.805 | 1.558 | 1.736 | 1.599 | 99.195 | 98.442 | 98.264 | slight gap |
| nmos_on | is | MLP | 0.494 | 0.542 | 0.599 | 0.522 | 99.506 | 99.458 | 99.401 | good fit |
| nmos_on | ib | MLP | 0.245 | 0.287 | 0.299 | 0.296 | 99.755 | 99.713 | 99.701 | good fit |
| nmos_off | id | MLP | 0.732 | 0.940 | 0.913 | 0.898 | 99.268 | 99.060 | 99.087 | good fit |
| nmos_off | ig | MLP | 3.537 | 3.660 | 3.592 | 3.370 | 96.463 | 96.340 | 96.408 | good fit |
| nmos_off | is | MLP | 1.054 | 1.262 | 1.245 | 1.197 | 98.946 | 98.738 | 98.755 | good fit |
| nmos_off | ib | MLP | 0.287 | 0.286 | 0.322 | 0.295 | 99.713 | 99.714 | 99.678 | good fit |
| pmos_on | id | MLP | 0.757 | 0.936 | 1.076 | 1.002 | 99.243 | 99.064 | 98.924 | good fit |
| pmos_on | ig | MLP | 0.312 | 0.347 | 0.343 | 0.376 | 99.688 | 99.653 | 99.657 | good fit |
| pmos_on | is | MLP | 0.655 | 0.922 | 0.928 | 0.793 | 99.345 | 99.078 | 99.072 | good fit |
| pmos_on | ib | MLP | 0.577 | 1.428 | 1.456 | 1.429 | 99.423 | 98.572 | 98.544 | slight gap |
| pmos_off | id | MLP | 0.745 | 0.837 | 0.852 | 0.829 | 99.255 | 99.163 | 99.148 | good fit |
| pmos_off | ig | MLP | 0.338 | 0.382 | 0.388 | 0.411 | 99.662 | 99.618 | 99.612 | good fit |
| pmos_off | is | MLP | 0.671 | 0.772 | 0.762 | 0.730 | 99.329 | 99.228 | 99.238 | good fit |
| pmos_off | ib | RandomForest | 3.670 | 11.368 | 9.303 | 10.498 | 96.330 | 88.632 | 90.697 | OVER-FIT (noise-level) |

## Gates and CLA at NEW random corners (seed2026)

| variant | level | median_err_% | p95_err_% | mean_acc_% | mean_acc_16_cases_% |
|---|---|---|---|---|---|
| rail | gates (18 cases x 50 new corners) | 1.031 | 4.138 | 98.407 | 98.928 |
| rail | CLA plain sum (128 vectors x 20 new corners) | 37.046 | 58.008 | 64.956 | nan |
| rail | CLA loading-aware (128 vectors x 20 new corners) | 1.281 | 2.513 | 98.672 | nan |

