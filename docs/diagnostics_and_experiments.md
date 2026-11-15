# Diagnostic Investigations and Advanced Experiments

To analyze the sources of error and test potential improvements, six dedicated diagnostic scripts (`06` through `11`) were executed.

## 1. Temperature and Vth0 Sensitivity Analysis (Script 06)

Circuit-level error was decomposed into temperature and threshold voltage bins:

Loading-Aware Error by Temperature Quartile:
* [-40 C to 0 C] (n=6400): Median Error = 9.09%, Mean Error = 11.16%, P95 = 25.22%, Signed Median = +1.73%
* (0 C to 40 C] (n=6400): Median Error = 8.52%, Mean Error = 8.96%, P95 = 15.92%, Signed Median = +8.52%
* (40 C to 80 C] (n=6016): Median Error = 6.18%, Mean Error = 8.29%, P95 = 20.29%, Signed Median = -4.77%
* (80 C to 125 C] (n=6784): Median Error = 10.42%, Mean Error = 10.65%, P95 = 25.37%, Signed Median = -10.07%

Key Finding:
The structural gap (32%) remains relatively flat across temperature (30% to 37%). The lowest error is observed in the typical active operating regime (40 C to 80 C, median error 6.18%).

## 2. The Single-FET Oracle Proof (Script 10)

To resolve why output-LOW gate states (INV 1, NAND2 11, NOR2 10, NOR2 11) showed high error in earlier iterations, each PMOS transistor was re-simulated in SPICE under the exact bias voltages seen by the cell.

SPICE Oracle Evaluation:

| Case | Sample Count | id_formula Median Error (%) | KCL (Is + Ib) Median Error (%) |
|---|---|---|---|
| INV 1 | 200 | 52.62% | 0.00755% |
| NAND2 11 | 200 | 52.63% | 0.00761% |
| NOR2 10 | 200 | 272.90% | 0.01484% |
| NOR2 11 | 186 | 228.90% | 0.41740% |

Conclusions:
1. The KCL equation (I_vdd = Is + Ib) matches full-cell SPICE to 0.0076%, proving charge conservation is exact.
2. Using |Id| of the OFF PMOS was physically incorrect: |Id| sinks gate-overlap tunneling supplied by the input source Va, not the supply rail Vdd.

## 3. Dataset Sparsity Analysis (Script 09)

Script 09 analyzed model error on test samples sitting in the operational bias region (Vd <= 0.2 VDD, Vs >= 0.8 VDD) versus the general hypercube:

PMOS OFF Error Distribution:
* Overall Test Set (n=1500): Id error = 4.62%, Is error = 5.11%, Ib error = 37.77%
* Gate Operating Region (n=73): Id error = 7.47%, Is error = 17.15%, Ib error = 31.41%

Key Finding:
Under uniform parameter sweeping, only 3.7% of training points fall into the operational gate corner. While the surrogate model accurately fits the 96% non-operational volume, the lower sample density near supply rails contributes to residual error at the cell level.

## 4. Bootstrap Model Comparison (Script 11)

Script 11 compared ResNet and XGBoost in the operational gate regions using 2,000 bootstrap resamples on validation data:

Region A (Full Vds at rail, n=52):
* ResNet Mean-Target Median Error: 16.54%
* XGBoost Mean-Target Median Error: 23.79%
* Bootstrap Difference (XGBoost - ResNet): +5.66% (90% Confidence Interval: [1.55%, 10.14%])
* Result: ResNet outperformed XGBoost in 98.8% of resamples, confirming its advantage at boundary rails.

## 5. Post-Mortem of Experimental Explorations

### Experiment 1: PINN KCL Penalty
A Physics-Informed Neural Network (PINN) was tested to enforce charge conservation by penalizing (Id + Ig + Is + Ib) in linear scale inside the loss function. 
Result: Reconstructing linear currents via 10^y divided by sub-picoamp denominators caused severe gradient explosion (gradients exceeding 10^12), leading to training divergence. Backpropagating linear current sums across 9 decades of log-scale targets is numerically unstable without bounded relaxation techniques.

### Experiment 2: W-Normalized Targets (I / W)
Training surrogate models on current density (I / W) was evaluated.
Result: Factoring out width reduced single-device variance on pmos_off. However, because interconnect tunneling and internal stack capacitance scale non-linearly with fan-out, the improvement was absorbed at the circuit level.
