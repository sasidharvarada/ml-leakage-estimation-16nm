# Part B: gate validation

## Setup (`scripts/04_validate_gates.py`, `scripts/gates.py`)

Gates: INV, NAND2, NOR2, AND2 (NAND2 + INV), OR2 (NOR2 + INV). WN = 32 nm, WP = 64 nm, L = 16 nm,
junction areas as in Part A. All input combinations (18 cases) at 200 random corners (seed 123), using
the same VDD, temperature and process ranges as Part A. Example netlists: `netlists/gates/*.sp`.

SPICE records, per run: the supply leakage -i(Vdd), the current drawn from each input source, and every
internal node voltage (out, x in NAND2, y in NOR2, the inner node of AND2 / OR2). 9 of 3,600 runs did not
converge and are excluded. The SPICE results are cached in `results/part_b/gate_spice.csv`.

## Gate leakage from the transistor models

Gate leakage is the current drawn from VDD. The recorded node voltages give every transistor's Vd, Vg,
Vs and Vb; a transistor is ON when its gate is on the conducting side of VDD/2; the matching model
(nmos_on, nmos_off, pmos_on, pmos_off) predicts its four terminal currents. The leakage is then exact
Kirchhoff current law (KCL) at the VDD side:

1. N_up = all nodes connected to VDD through ON transistors.
2. I_vdd = sum of the currents into every transistor terminal attached to a node in N_up.
3. An ON transistor inside N_up has Vds of only microvolts and a very large conductance, so its channel
   current cannot be predicted from Vd and Vs. For it, Id + Is is replaced by -(Ig + Ib) (KCL on the
   device), so only its gate and body currents are used.
4. If three terminals of an OFF transistor are in N_up (for example an OFF PMOS with Vd = Vs = Vb = VDD),
   the direct sum cancels almost exactly, so -(current of the fourth terminal) is used instead. If the
   fourth terminal is at the same voltage too (no field at all), the device carries no current and is
   left out.
5. A predicted gate current is capped at the largest gate current seen in the training data at the same
   or smaller |Vgs| and |Vgd| (tunnelling only grows with oxide voltage). This removes rare wild
   predictions where the true gate current is about 0 A.

**Check of the formula:** with single-transistor SPICE currents in place of the ML predictions, steps 1-4
reproduce the full gate SPICE leakage to a median of about 0.0002 % in 16 of 18 cases. The exceptions are
NOR2 10 and NOR2 11, whose leakage is close to the simulator's numerical noise floor (see below).

## Results (Deliverables 6 and 7)

`results/part_b/gate_results_table.csv`, all runs in `results/part_b/gate_all.csv`,
parity plot `results/part_b/gate_parity_plot.png`.

* 16 of 18 cases: median error 0.63 to 1.39 %, mean accuracy 98.3 to 99.2 %, bias about +0.3 to +0.7 %.
* Over all 3,600 runs: median error 0.88 %, 95th percentile 4.4 %.
* NOR2 10 (about 8.5e-13 A): 96.8 % mean accuracy.
* NOR2 11 (about 1e-14 to 1e-16 A): 75 % mean accuracy. With both PMOS OFF in series the leakage is at the
  simulator's numerical noise floor: even single-transistor SPICE and gate SPICE disagree by about 10 %
  here, so the percentage error is not meaningful. Its contribution to circuit leakage is negligible.

Mean accuracy = 100 % - mean of |ML - SPICE| / SPICE over the 200 corners of each case.
