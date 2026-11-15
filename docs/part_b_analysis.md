# Part B: Analysis of the Gate-Level Results

This file interprets the Part B results. The method, table and parity plot are in `part_b_gate_validation.md`. The scripts behind the diagnostic numbers (07, 08, 10, 12) are described in `diagnostics_and_experiments.md`.

## 1. Summary

* Over 3,394 gate runs above the 1e-13 A floor, the median error of the ML gate model against SPICE is 10.07%.
* 14 of the 18 gate states have a median error between 5.8% and 11.8%. The remaining four (INV 1, NAND2 11, NOR2 10, NOR2 11) have median errors of 52.7%, 53.8%, 144.2% and 68.2%. All four are output-low states whose only term in the formula is the |Id| of an OFF PMOS.
* Without those four states the overall median is 8.22% and the 95th percentile is 25.29%. With them, the four states account for 17.9% of the runs and have a pooled median error of 63.10%.
* The high-error states are mainly a formula problem. With true SPICE currents, the |Id| formula for the OFF PMOS is already 52.6% off for INV 1 and NAND2 11. The Kirchhoff expression (Is + Ib) is within 0.0076% for those two cases and within 0.42% for all four. This replacement is not applied in the final results.
* Training-data coverage is a minor factor at most. The Spearman correlation between gate error and coverage distance is -0.098.
* The four states carry very little leakage (1e-14 A to 3e-11 A median, against 2e-10 A to 9e-10 A for the other states). At circuit level only NAND2 11 occurs as a standalone gate (section 6).

## 2. How the 18 states group

| Group | States | Median error | Notes |
|---|---|---|---|
| NMOS OFF dominated, output high | INV 0, NAND2 00/01/10, NOR2 00, OR2 01/10/11 | 8.4% to 9.0% | 8.4% to 8.9% for INV 0, NAND2 00 to 10 and NOR2 00 |
| NOR2 01 | NOR2 01 | 9.55% | Mixes an OFF PMOS |Id| with a PMOS ON Ig |
| AND2 and OR2 with high totals | AND2 00/01/10, OR2 00 | 5.8% to 6.6% | Largest leakage of all states (6.7e-10 A to 9.4e-10 A) |
| AND2 11 | AND2 11 | 11.77% | Its NAND2 stage uses the OFF PMOS |Id| formula |
| High-error output-low states | INV 1, NAND2 11, NOR2 10, NOR2 11 | 52.7% to 144.2% | Only term is |Id| of an OFF PMOS |

Reading the groups:

* **The 8% level.** States built on the same mechanism have almost the same error, for example INV 0, NAND2 01 and NOR2 00 (8.39% to 8.40%). In Part A the NMOS OFF model reports a test median Id error of 0.008%. That figure is set by the 1 pA denominator floor, not by the model (`part_a_analysis.md`, section 4). The gate-level 8% is the honest size of the combined error of the NMOS OFF Id and the PMOS ON Ig terms. The available outputs do not split it between the two models. The output of script 09 would.
* **Bias.** In the states near 8% the signed median bias is mildly positive (+3.5% to +5.9%). In AND2 00/01/10 and OR2 00 it is slightly negative (-0.6% to -2.9%). The cause was not diagnosed.
* **Spread.** The 95th-percentile error is 17% to 29% in all states except the four hard ones, where it is 88% to 2,736%.

## 3. Dependence on temperature and threshold voltage

Script 06 bins the isolated-gate ML error (pooled over all states above 1e-13 A) by corner temperature and by NMOS vth0 quartile:

| Temperature bin | Median error | | vth0 bin | Median error |
|---|---|---|---|---|
| -40 C to 0 C | 9.44% | | 0.613 to 0.642 V | 11.17% |
| 0 C to 40 C | 10.06% | | 0.642 to 0.677 V | 9.33% |
| 40 C to 80 C | 9.45% | | 0.677 to 0.715 V | 9.42% |
| 80 C to 125 C | 11.42% | | 0.715 to 0.750 V | 10.11% |

The median error is nearly flat across both variables. It is highest in the hottest bin and in the lowest-vth0 bin, the corners with the most leakage. The mean errors in the same output are much larger (23% to 238% by temperature) because of the hard states, whose errors are heavy-tailed.

## 4. Why four states are wrong

The investigation ran in four steps. The scripts and full outputs are in `diagnostics_and_experiments.md`.

**Step 1: locate the error (script 07).** Per-state statistics show that the error is concentrated in INV 1, NAND2 11, NOR2 10 and NOR2 11 (section 2). The signed medians are +10.8%, +12.1%, +144.2% and -66.7%, so the formula over-predicts in three of them and under-predicts in NOR2 11.

**Step 2: try other assembly formulas with the ML models (script 08).** Median error with the existing models, using different ways to assemble the supply current:

| State | |Id| formula (final) | Is only | Is + Ib | |Id| formula + Ib |
|---|---|---|---|---|
| INV 1 | 52.71% | 20.82% | 20.69% | 52.95% |
| NAND2 11 | 53.77% | 21.45% | 21.02% | 53.63% |
| NOR2 10 | 144.2% | 52.37% | 40.35% | 152.4% |
| NOR2 11 | 68.18% | 87.62% | 10.19% | 17.78% |

Is + Ib is the best formula in every state. The |Id| formula is one of the two worst choices in every state. Adding Ib to the |Id| formula does not help (it makes INV 1, NAND2 11 and NOR2 10 slightly worse), which points to the |Id| term itself.

**Step 3: check with SPICE only (script 10).** Each OFF PMOS was re-simulated as a single transistor at the exact bias it sees in the gate, and the true terminal currents were combined with each formula. No ML is involved:

| State | n | |Id| formula, median error | Is + Ib (KCL), median error | |Id| formula in corners above 80 C |
|---|---|---|---|---|
| INV 1 | 200 | 52.62% | 0.0076% | 7.96% |
| NAND2 11 | 200 | 52.63% | 0.0076% | 7.96% |
| NOR2 10 | 200 | 272.9% | 0.0148% | 23.39% |
| NOR2 11 | 186 | 228.9% | 0.4174% | 50.27% |

* The |Id| formula is wrong even with exact currents. For INV 1 and NAND2 11 its error with true currents (52.6%) matches its error with ML currents (52.7% and 53.8%), so the error is in the formula, not in the ML models. (For NOR2 10 and 11 the two figures differ because the oracle keeps all runs above 1e-16 A, while Part B keeps those above 1e-13 A.)
* The Is + Ib expression reproduces the full-gate SPICE leakage to within 0.42% in all four states. The |Id| of an OFF PMOS includes gate-edge tunneling that the input source supplies, not Vdd, so it is the wrong quantity for the supply current.
* The |Id| error falls sharply in corners above 80 C (INV 1: 52.6% to 7.96%). This fits the picture that the formula is acceptable where subthreshold current dominates and poor where the gate tunneling part is a large share of |Id|.
* INV 0 was included as a control (`kcl` column only). Its KCL expression gave a 13.19% median error, not 0.0076%. So the near-exact match applies to the four output-low states and is not general. This was not investigated.

**Step 4: remaining error with the ML models.** With Is + Ib and the ML models, INV 1 and NAND2 11 are at about 21%, NOR2 10 at 40% and NOR2 11 at 10%. This is the model error on very small Is and Ib values. Script 11 shows that Ib is the hardest target for the PMOS OFF models (`part_a_analysis.md`, section 4).

**Decision.** The final code keeps the |Id| formula. The numbers in Step 2 show what replacing it would change.

## 5. Is it a sampling-coverage problem? (script 12)

Script 12 measures how far each transistor query made by a gate lies from the Part A training data, as a percentile of the distances of held-out rows. A high percentile means the query is in a sparse region. An in-distribution query set would show about 5% of queries above the 95th percentile.

| Transistor case | Gate queries | Share above 95th percentile |
|---|---|---|
| NMOS OFF | 2,985 | 46.4% |
| NMOS ON | 785 | 34.4% |
| PMOS OFF | 2,985 | 49.0% |
| PMOS ON | 3,776 | 30.1% |

Gate queries do sit in sparser regions than a random held-out row, by a wide margin. But the error does not rise with the distance:

* Spearman rho between the worst-transistor coverage percentile and the gate error is -0.098 (n = 3,409). The sign is negative.
* By bin, the median gate error is 65.2% (percentile below 50, n = 69), 12.4% (50 to 90, n = 719), 9.2% (90 to 99, n = 1,506) and 10.0% (99 or higher, n = 1,115).
* The four hard states are not the ones with the highest coverage percentiles. NOR2 10 and NOR2 11 have the lowest median worst-transistor percentiles of all states (76.0 and 67.5), yet the highest errors. INV 1 and NAND2 11 are at 97.1, but AND2 and OR2 states at 98 to 99 have errors of only 6% to 12%.

Coverage is therefore not what separates the hard states from the others. This agrees with step 3, where the error appears with true currents. The sparse sampling near the supply rails (only 265 of 7,000 PMOS OFF training samples in the full-Vds corner, `part_a_analysis.md`, section 7) may still add a little error to the other states.

Script 12 was run with corner seed 7, so its gate runs use a different set of 200 corners than Part B (seed 123). Its per-state errors differ slightly from the Part B table (for example NOR2 10 is 153.7% there and 144.2% in Part B). The conclusion does not depend on the seed.

## 6. Relevance to the circuit

The 3-bit CLA of Part C contains only NAND2, AND2 and OR2 cells. INV 1, NOR2 10 and NOR2 11 therefore never occur as standalone gates there. NAND2 11 does, in 960 of the 5,376 gate instances over the 128 input vectors (17.9%), but its SPICE leakage is small: it makes up a median of 1.35% of the summed SPICE gate leakage for a corner and vector (mean 3.74%, 95th percentile 14.94%).

The formulas of INV 1, NOR2 10 and NOR2 11 also enter the totals of AND2 and OR2 through their inner stages (an AND2 with n_out high contains INV 1, and OR2 10 and 11 contain NOR2 10 and 11). In the CLA this happens for INV 1 and for NOR2 10 (inside OR2 10); OR2 11 does not occur there. The AND2 and OR2 medians stay at 5.8% to 11.8% because those totals are dominated by other terms.

## 7. Limitations

* **Floor.** The 1e-13 A floor removes 193 runs, and almost all of NOR2 11 (142 of 200). Its 68% figure rests on 58 runs.
* **Failed runs.** 13 AND2 gate runs failed in SPICE and are excluded here. They are not excluded from Part C (`part_c_analysis.md`).
* **Node voltages from SPICE.** The internal node voltages (x, y, n_out) come from the SPICE run, as the project specifies. Errors from predicting them are not part of these results.
* **Single sizing and 200 corners.** Every gate uses one sizing (WN = 32 nm, WP = 64 nm). Statistics are over 200 corners with independently varied NMOS and PMOS process parameters.
* **Formula error.** The final results include the |Id| formula error described in section 4.