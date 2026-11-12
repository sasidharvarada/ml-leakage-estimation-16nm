# Part C: 3-bit carry-lookahead adder

## Circuit (`scripts/cla3.py`, netlist `netlists/circuit/cla3.sp`)

42 gates built only from Part B gate types: P_i = A_i xor B_i and G_i = A_i and B_i per bit,
carry-lookahead C1 = G0 + P0 Cin, C2 = G1 + P1 G0 + P1 P0 Cin, C3 = Cout = G2 + P2 G1 + P2 P1 G0 + P2 P1 P0 Cin
(AND2 / OR2 trees), and S_i = P_i xor C_i. Each XOR is four NAND2 gates (24 NAND2, 12 AND2, 6 OR2).
Inputs a[2:0], b[2:0], cin: 128 vectors. Every SPICE run is also checked logically (outputs s0, s1, s2, cout against
a + b + cin): 0 mismatches in 25,600 runs.

## Method (`scripts/05_validate_circuit.py`)

* SPICE: the full transistor-level CLA at the same 200 corners as Part B, all 128 vectors
  (25,600 runs, cached in `results/part_c/spice_cache/`). Leakage = -i(Vdd).
* ML, plain sum (the project method): for each vector the logic value of every gate input is found, and
  the Part B gate leakages (from the transistor models, same corner) are summed.
* ML, loading-aware sum: plain sum + the input-pin current of every gate input whose net is an internal
  net driven HIGH. In the full circuit that tunnelling current flows from VDD through the driving gate's
  pull-up, so it is part of the circuit leakage; in a stand-alone gate simulation it comes from the ideal
  input source and is not part of the gate leakage. The pin currents are predicted by the same transistor
  models (gate currents of the transistors on that input).
* Check without ML: the same two sums built from the SPICE gate results.

## Results (Deliverable 8)

`results/part_c/circuit_summary.csv`, per-vector table `results/part_c/circuit_results_table.csv`,
raw data `results/part_c/circuit_raw.csv`, parity plots `results/part_c/circuit_parity_plot.png` (plain)
and `results/part_c/circuit_parity_plot_loading.png` (loading-aware).

| Method | Bias (%) | Median err (%) | Mean err (%) | P95 err (%) | Mean accuracy (%) |
|---|---|---|---|---|---|
| ML plain sum (project method) | -31.11 | 31.11 | 32.09 | 60.51 | 67.91 |
| ML loading-aware | 0.60 | 0.84 | 0.99 | 2.54 | 99.01 |
| SPICE gate sum, plain (no ML) | -31.49 | 31.49 | 32.47 | 60.53 | 67.53 |
| SPICE gate sum, loading-aware (no ML) | 0.008 | 0.008 | 0.013 | 0.040 | 99.99 |

## Interpretation

* The plain sum under-predicts by about 31 %, and it does so equally with SPICE gate values, so this gap is
  caused by the composition (loading between gates), not by the ML models. The project text anticipates
  this ("ignores loading between gates, so expect the accuracy to be somewhat lower").
* The gap is large in this technology because the gate oxide is very thin (about 1.2 nm): a HIGH gate input
  draws a tunnelling current comparable to the gate's own leakage.
* With the input-pin currents added, the composition is exact (99.99 % with SPICE values), and the ML
  version reaches 99.01 % mean accuracy. The remaining 0.8 % median error is the error of the transistor
  models.
