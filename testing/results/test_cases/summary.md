# Fresh test cases (seed 2026, never used in training or in Parts B / C)

## Transistors: 300 uniform + 300 gate-like new samples per case (median error %)

| case | current | rail:gate-like med % | rail:uniform med % | official_test_med_% |
|---|---|---|---|---|
| nmos_off | ib | 0.446 | 0.2953 | 0.3217 |
| nmos_off | id | 0.9803 | 0.8983 | 0.9131 |
| nmos_off | ig | 6.494 | 3.37 | 3.592 |
| nmos_off | is | 1.504 | 1.197 | 1.245 |
| nmos_on | ib | 0.2976 | 0.2956 | 0.2995 |
| nmos_on | id | 0.5175 | 0.6345 | 0.6596 |
| nmos_on | ig | 0.8755 | 1.599 | 1.736 |
| nmos_on | is | 0.5199 | 0.5219 | 0.5992 |
| pmos_off | ib | 21.16 | 10.5 | 9.303 |
| pmos_off | id | 1.151 | 0.8289 | 0.8519 |
| pmos_off | ig | 0.4532 | 0.411 | 0.3883 |
| pmos_off | is | 1.257 | 0.7301 | 0.7622 |
| pmos_on | ib | 0.8834 | 1.429 | 1.456 |
| pmos_on | id | 0.8385 | 1.002 | 1.076 |
| pmos_on | ig | 0.322 | 0.376 | 0.3429 |
| pmos_on | is | 0.6835 | 0.7932 | 0.9277 |

## Gates and CLA at new corners

| variant | level | median_err_% | p95_err_% | mean_acc_% | mean_acc_16_cases_% |
|---|---|---|---|---|---|
| rail | gates (18 cases x 50 new corners) | 1.031 | 4.138 | 98.41 | 98.93 |
| rail | CLA plain sum (128 vectors x 20 new corners) | 37.05 | 58.01 | 64.96 | nan |
| rail | CLA loading-aware (128 vectors x 20 new corners) | 1.281 | 2.513 | 98.67 | nan |

Official results (seed 123, 200 corners) for comparison: gates 0.88 % median error, 99.04 % mean accuracy over 16 regular cases; CLA plain 67.9 %, loading-aware 99.01 %.

