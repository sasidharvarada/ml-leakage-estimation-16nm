# Part C: Analysis of the Test-Circuit Results

This file interprets the Part C results. The setup and result tables are in `part_c_circuit_validation.md`. The diagnostics (scripts 06 to 08) are in `diagnostics_and_experiments.md`. The gate-level behaviour that feeds into this is analysed in `part_b_analysis.md`.

## 1. Summary

* **Headline result.** The plain hierarchical sum of the gate models has a median error of 34.0% against full-circuit SPICE (95th percentile 62.94%, mean accuracy 66.62%). It under-predicts: the median leakage is 17.5 nA against 26.9 nA.
* **The cause is structural, not machine learning.** Summing isolated gates in SPICE, with no ML at all, is already 32.25% below the full circuit. Almost the whole plain-sum error comes from circuit-level physics that isolated gates do not contain.
* **The loading-aware model removes it.** Adding the gate tunneling current that the driving gates supply to internal receiver pins brings the median error down to 6.73% (95th percentile 21.37%, mean accuracy 92.07%). No parameter is fitted to the circuit results. The added term comes from the same transistor models.
* **Residual error is mostly small except at high temperature.** The loading-aware error is 4.2% to 7.5% below 80 C and 10.21% above 80 C, where the model under-predicts.

## 2. Why the plain sum is low: the structural gap

In an isolated-gate simulation, the input pins are driven by ideal voltage sources. In the full circuit, most gate inputs are driven by the output of another gate. A gate input at logic 1 draws gate tunneling current into the receiving transistors (the NMOS that is ON and the OFF PMOS). In the isolated run, the input source supplies that current. In the circuit, the driving gate's PMOS pull-up supplies it, so it comes from the Vdd rail and appears in the full-circuit supply current. The sum of isolated gates leaves it out.

Evidence:

* The SPICE-only gate-sum is 1.735e-08 A at the median against 2.687e-08 A for the full circuit (32.25% error, bias -6.37e-09 A).
* The plain ML sum has almost the same median error (34.0%), so the ML models add little on top of the structural gap.
* The primary inputs (a, b, cin) are separate ideal sources in the full-circuit netlist, so their tunneling current is correctly outside the Vdd current. Only inputs driven by internal nets matter.

The gap is present in every temperature and vth0 bin:

| Bin | Structural gap (median) |
|---|---|
| -40 C to 0 C | 37.37% |
| 0 C to 40 C | 36.61% |
| 40 C to 80 C | 27.32% |
| 80 C to 125 C | 30.69% |
| NMOS vth0 0.613 to 0.642 V | 36.74% |
| 0.642 to 0.677 V | 34.74% |
| 0.677 to 0.715 V | 26.78% |
| 0.715 to 0.750 V | 30.31% |

It varies between 27% and 37%, being lowest for 40 C to 80 C and for the highest vth0 bins.

## 3. The loading-aware model

For each gate input at logic 1 that is driven by an internal net, the model adds the ML-predicted gate current Ig of the NMOS ON and of the OFF PMOS connected to that pin (`_pin_loading_ig` in `05_test_circuit.py`). The model assumes inputs at logic 0 add nothing, since the Ig of an ON PMOS is already part of the receiving gate's own formula.

| | Plain sum | Loading-aware |
|---|---|---|
| Median leakage | 1.752e-08 A | 2.643e-08 A |
| Median bias | -6.360e-09 A | -2.159e-10 A |
| Median error | 34.0% | 6.73% |
| 95th-percentile error | 62.94% | 21.37% |
| Mean accuracy | 66.62% | 92.07% |

* The median loading term is 6.1e-09 A. In the median instance it is 45% of the plain sum, or 31% of the loading-aware estimate. It accounts for nearly all of the 6.14e-09 A shift in the median bias.
* The remaining median bias of -2.2e-10 A is 0.8% of the full-circuit median.
* The loading-aware error (6.73%) is lower than the gate-level error of Part B (10.07% overall, 8.22% without the four hard states). A likely reason is that errors of individual gates partly cancel in the sum, since the gate-level signed biases have both signs (`part_b_analysis.md`, section 2). This was not tested.
* The parity plot of the loading-aware model follows y = x over roughly 4 nA to 150 nA. The scatter is made of short streaks, a few of them visibly below the line (for example near 1e-8 A, where the estimate is about 7e-9 A). The 128 vectors of one corner share the same PVT values, so errors are probably correlated within a corner. This was not checked.

The loading-aware model is a physical improvement and not the project's specified method. The specified method, which ignores inter-gate loading, is the plain sum, so the plain sum is the headline Deliverable 8 result.

## 4. Where the remaining error sits

Script 06 splits the circuit error by corner temperature and by NMOS vth0 quartile. The gate-level ML error and the structural gap are added for comparison.

| Temperature bin | Runs | Loading-aware median | Signed median | 95th percentile | Plain median | Structural gap | Gate-level ML error |
|---|---|---|---|---|---|---|---|
| -40 C to 0 C | 6,400 | 7.48% | +0.10% | 15.72% | 37.48% | 37.37% | 9.44% |
| 0 C to 40 C | 6,400 | 4.50% | +3.75% | 14.77% | 32.17% | 36.61% | 10.06% |
| 40 C to 80 C | 6,016 | 4.20% | +0.44% | 13.19% | 26.03% | 27.32% | 9.45% |
| 80 C to 125 C | 6,784 | 10.21% | -10.21% | 27.71% | 40.13% | 30.69% | 11.42% |

| NMOS vth0 bin | Runs | Loading-aware median | Signed median | 95th percentile | Plain median | Structural gap | Gate-level ML error |
|---|---|---|---|---|---|---|---|
| 0.613 to 0.642 V | 6,400 | 9.28% | -3.17% | 23.77% | 40.04% | 36.74% | 11.17% |
| 0.642 to 0.677 V | 6,400 | 6.21% | +2.26% | 15.18% | 35.37% | 34.74% | 9.33% |
| 0.677 to 0.715 V | 6,400 | 6.16% | -1.48% | 19.21% | 28.17% | 26.78% | 9.42% |
| 0.715 to 0.750 V | 6,400 | 5.38% | -2.46% | 24.27% | 32.87% | 30.31% | 10.11% |

The signed median is the median of (ML - SPICE) / SPICE, so a negative value means under-prediction.

* **The best region is 0 C to 80 C** (4.2% to 4.5% median, 95th percentile 13% to 15%). This covers the typical operating range.
* **Above 80 C the error is one-sided.** The signed median (-10.21%) equals minus the median error, so most runs under-predict. The plain-sum error in this bin (40.13%) exceeds the structural gap (30.69%) by about 9 points, while in the other temperature bins the two are within about 4 points of each other. The extra 9 points are consistent with the ML models under-predicting at high temperature. The gate-level ML error is also at its highest in this bin (11.42%). Script 09 breaks the Part A models' error down by temperature and would show this directly. Its output is not included here.
* **Cold corners have a larger spread but no bias.** The median error is 7.48% while the signed median is +0.10%, so errors of both signs occur.
* **The lowest vth0 quartile has the highest error among the vth0 bins** (9.28% median, 23.77% 95th percentile). These are also the corners with the highest leakage. The same bin has the highest gate-level ML error (11.17%) and the largest gap between plain error and structural gap (3.3 points). The bias there is small (-3.17%).

## 5. Relation to the gate-level errors

The CLA uses 11 of the 18 gate states, and only NAND2 11 among the four high-error states of Part B occurs as a standalone gate. It makes up a median of 1.35% of the summed gate leakage (`part_b_analysis.md`, section 6). The INV 1 formula appears only inside AND2 totals and the NOR2 10 formula only inside OR2 10; NOR2 11 never occurs, because OR2 11 does not occur in the CLA. The circuit-level result is therefore dominated by the well-behaved states, which have median errors of 5.8% to 11.8% at the gate level. The formula error of the four hard states is expected to be a small contributor to the circuit error, although only the NAND2 11 share has been measured.

## 6. Limitations

* **Failed gate runs.** 1,328 of the 25,600 circuit instances (5.19%) use at least one of the 13 failed AND2 gate runs, whose SPICE leakage was recorded as 0 and whose ML estimate used default node voltages. The effect is expected to be small (a single AND2 leakage is 1% to 3% of the median circuit leakage) but was not quantified.
* **Ideal logic levels.** Both models assume gate inputs at 0 or VDD and use the internal node voltages from isolated-gate runs. The loading-aware term uses the same assumption. The change in node voltages due to the load is not modelled.
* **One circuit, one sizing, 200 corners.** Statistics come from a single 42-gate circuit with one transistor sizing (WN = 32 nm, WP = 64 nm). The 128 vectors of a corner are not independent samples of the process.
* **Model choice.** The results use the ResNet models of Part A. The choice of the ResNet over XGBoost was based on the circuit-level result, but no XGBoost-based circuit run is included here to show the size of the difference (`part_a_analysis.md`, section 6).
* **Per-vector results.** Per-vector medians are in `results/circuit_results_table.csv`. They are not summarised here.