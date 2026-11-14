#!/usr/bin/env bash
# Testing: train / validation / test errors + new random test cases (transistors, gates, CLA).
# Usage (from the repo root, Python environment active):
#     bash testing/run_tests.sh          # ~15-30 min
#     bash testing/run_tests.sh --full   # + learning curves (re-trains the MLP, ~2-3 h on the GPU)
# Results: testing/results/ (FINAL_TABLES.md = all tables)   Log: logs/tests_<date>.log
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
LOG="logs/tests_$(date +%Y%m%d_%H%M).log"
exec > >(tee -a "$LOG") 2>&1
step() { echo; echo "==================== $(date +%H:%M:%S)  $*"; }
START=$(date +%s)

step "1/3 Train vs validation vs test error of the saved models (over-fit / under-fit check)"
python testing/01_check_overfit.py || echo "[!] step 1 failed"

step "2/3 New random test cases (seed 2026): 300+300 transistor samples per case, 18 gate cases x 50 corners, CLA x 20 corners"
python testing/03_test_cases.py --n 300 --gate-corners 50 --cla-corners 20 || echo "[!] step 2 failed"
python testing/03_test_cases.py --point case=nmos_off,vdd=1.0,temp=85,w=48e-9,vd=1.0,vs=0 || true
python testing/03_test_cases.py --point case=pmos_on,vdd=0.95,temp=-20,w=96e-9,vd=0.0,vs=0.95 || true

if [[ "${1:-}" == "--full" ]]; then
  step "extra: learning curves (loss vs iteration and vs training-set size)"
  python testing/02_learning_curves.py || echo "[!] learning curves failed"
fi

step "3/3 FINAL TABLES"
python testing/summary_table.py
echo
echo "Total time: $(( ($(date +%s) - START) / 60 )) min.  Log: $LOG"
