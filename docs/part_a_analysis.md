# Part A: Analysis of the Transistor Models

This file interprets the Part A results. The setup, data audit and result tables are in `part_a_transistor_models.md`; the diagnostic scripts referred to here are described in `diagnostics_and_experiments.md`.

## 1. Summary

* Four datasets of 10,000 SPICE operating points each (NMOS ON/OFF, PMOS ON/OFF) pass the Kirchhoff audit: the median relative residual is at most 0.0008% in every case.
* The chosen model, a PyTorch ResNet, reaches a log-space R2 of 0.9808 to 0.9994 on 1,500 unseen test samples per case. The median Id error is 0.008% to 3.97% and the 95th-percentile error is 9.5% to 26.45%.
* PMOS OFF is the weakest case (test R2 0.9808, 95th-percentile error 26.45%).
* The headline metric scores Id only and floors the error denominator at 1 pA, which flatters the OFF cases (section 4). Errors on the other terminal currents, especially Ib, are larger.
* The ResNet is not the best model by every measure. XGBoost has a lower median Id error on PMOS OFF, and script 11 shows XGBoost with lower all-target error there (section 5). The ResNet was kept for all four cases because the end-to-end circuit error was lower with it (section 6).

## 2. What the data checks establish

The KCL audit confirms that the extraction pipeline is consistent: signs, units and solver tolerances are right. In the ON states the residuals come from the solver tolerance (reltol = 1e-6 on currents of roughly 140 uA). In the OFF states they stay below 2.4e-15 A. The audit does not test BSIM4 physics.

The three trend plots check the physics qualitatively: OFF current rises with temperature and falls as the threshold magnitude rises, and gate tunneling falls as the oxide gets thicker. Every other input varies at the same time in these scatters, so each trend is a wide band, not a curve. No slopes were extracted from them.

## 3. Model comparison

| Ordering by log-space R2 (all four cases) | ResNet > XGBoost > Random Forest > Ridge |
|---|---|

* **Ridge** is the baseline. R2 is 0.79 to 0.92, and on the ON states the 95th-percentile error exceeds 1,200%. A linear map cannot follow log-current across the full bias, temperature and process range.
* **Random Forest and XGBoost** close most of the gap. On the ON states their median Id errors are 14% to 25%.
* **The ResNet** lowers the ON-state median Id error to 4.28% (NMOS) and 3.28% (PMOS) on validation, 3 to 5 times below XGBoost.
* **PMOS OFF** is the exception on error: XGBoost has the lower median (2.917% vs 3.994%) and 95th-percentile error (19.83% vs 21.78%), while the ResNet has the higher R2 (0.9869 vs 0.9689).

**Fairness caveat.** The ResNet checkpoint is chosen on the validation split. The other three models use fixed settings with no tuning, so the validation comparison slightly favors the ResNet. The test split is used once, for the chosen model only, so the test table does not compare models.

## 4. How to read the metrics

* **Id only.** All four currents are trained, but only Id is scored in the Part A tables.
* **Denominator floor.** The relative error divides by max(|SPICE|, 1e-12 A). For NMOS OFF, a test median error of 0.008% next to an R2 of 0.998 means most samples sit below 1 pA, so the floor, not the model, sets that number. Compare cases by log-space R2, not by the OFF-case medians.
* **Signs.** The models predict magnitudes, and the SPICE reference sign is used to restore the sign. Sign errors are therefore not tested here. Parts B and C also work with magnitudes and assign current direction from circuit structure.
* **All-target view.** Script 11 scores all four targets with both sides clipped at 1e-18 A. For PMOS OFF on the validation split, the median errors are:

| Model (retrained in script 11) | Id | Ig | Is | Ib |
|---|---|---|---|---|
| ResNet | 12.57% | 8.34% | 10.42% | 29.18% |
| XGBoost | 6.51% | 6.48% | 6.51% | 16.79% |

These numbers are not directly comparable with the Part A table (Id median 3.99% for the saved ResNet). The metric differs (floor 1e-18 A, not 1e-12 A), and script 11 retrains the ResNet, so it is not bit-identical to the saved model. The outputs available here cannot separate the two effects. What they do show is that Ib is the hardest target for both models, with 95th-percentile errors above 1,400%.

## 5. PMOS OFF: ResNet versus XGBoost

PMOS OFF is the one case where the Id median favors XGBoost, and the OFF PMOS is also the device behind the hardest gate states in Part B. Script 11 compares the two on the validation split only. It uses the same settings and seed as `03_train_models.py` and splits the samples into the bias regions that gates use:

* Region A: source at the rail, drain at the opposite rail (full Vds). 52 validation samples.
* Region B: source and drain both at the source rail (Vds near 0). 47 validation samples.
* Elsewhere: 1,401 validation samples.

Median error, mean over the four targets:

| Subset | ResNet | XGBoost |
|---|---|---|
| All validation (n = 1,500) | 15.13% | 9.07% |
| Elsewhere (n = 1,401) | 14.71% | 8.94% |
| Region A (n = 52) | 19.26% | 18.75% |
| Region B (n = 47) | 22.30% | 20.27% |

Bootstrap (2,000 resamples), difference XGBoost minus ResNet in the mean-over-targets median error. A negative value means XGBoost has the lower error:

| Subset | Difference | 90% interval | ResNet better in |
|---|---|---|---|
| All validation | -6.04 | [-6.74, -5.24] | 0.0% of resamples |
| Elsewhere | -5.69 | [-6.43, -4.84] | 0.0% |
| Region A | -0.92 | [-7.05, 4.31] | 42.6% |
| Region B | -1.89 | [-7.27, 3.77] | 28.5% |

* Over the full validation set and outside the gate regions, XGBoost has the lower error and the interval excludes 0.
* In regions A and B the intervals include 0. With 52 and 47 samples there is no evidence that either model is better there.
* An earlier version of this analysis reported that the ResNet won region A in 98.8% of resamples. The current run does not support that.

## 6. Why the ResNet is used for all four cases

The model choice is hard-coded in `03_train_models.py`. It was made on the end-to-end circuit result, not on the transistor-level metrics. With the ResNet models, the loading-aware 3-bit CLA reaches a median error of 6.73% (Part C). The transistor-level evidence is mixed:

* The ResNet has the highest validation R2 in every case.
* The ResNet has the lowest median Id error in three of four cases.
* On PMOS OFF, XGBoost has the lower median Id error, and script 11 finds it better on all-target error.

A side-by-side circuit run with XGBoost models is not part of the saved outputs, so the size of the circuit-level improvement is not documented here.

## 7. Limitations

* **Uniform sampling.** Under uniform sampling, only 265 of 7,000 PMOS OFF training samples (3.8%) fall in region A and 288 (4.1%) in region B. Part B tests whether this explains the gate-level errors and finds it is at most a minor factor (`part_b_analysis.md`, section 5).
* **Data size.** There are 10,000 samples per case, one split and one seed.
* **Process parameters.** The five process parameters vary independently and uniformly by plus or minus 10%. Real process variation is correlated and not uniform.
* **Current floor.** Currents below 1e-18 A are clipped in training. Anything that small is not resolved.
* **Fixed length.** All models use L = 16 nm, and the widths are limited to 1x to 8x Lmin.
* **Single operating condition per case.** Each model is trained for one gate and body bias. Gate-level use relies on drain and source voltages covering [0, VDD], which the sampling does.