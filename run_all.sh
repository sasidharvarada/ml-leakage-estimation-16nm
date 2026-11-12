#!/usr/bin/env bash
# Re-runs the improved pipeline end to end and prints a summary at the end.
# Usage (from the repo root, inside the Python environment):
#     bash run_all.sh                 # everything (data + training + Parts B and C)
#     bash run_all.sh --skip-data     # keep the existing datasets; re-train + Parts B and C
#     bash run_all.sh --fast          # quick check of the whole chain
# Model training uses PyTorch on the GPU when torch + CUDA are installed.
# Everything is also written to logs/run_all_<date>.log
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs
LOG="logs/run_all_$(date +%Y%m%d_%H%M).log"
exec > >(tee -a "$LOG") 2>&1

FAST=""
RAIL_N=10000
SKIP_DATA=0
for arg in "$@"; do
  case "$arg" in
    --fast) FAST="--fast"; RAIL_N=3000 ;;
    --skip-data) SKIP_DATA=1 ;;
  esac
done

step() { echo; echo "==================== $(date +%H:%M:%S)  $*"; }
START=$(date +%s)

step "0. Check tools"
ngspice --version | head -2
python -c "import numpy, pandas, sklearn, lightgbm, xgboost, matplotlib, joblib; print('python packages OK')"
python -c "import torch; print('torch', torch.__version__, '| GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'not available (CPU will be used)')" || echo "torch not installed: scikit-learn MLP (CPU) will be used"

step "1. Part A datasets (uniform, 10,000 per case) - reuse if present"
if [[ $(wc -l < data/nmos_on.csv) -lt 10001 ]]; then python scripts/01_generate_transistor_data.py; fi
wc -l data/*.csv

step "1b. Part A extra rail-focused training data ($RAIL_N per case)"
if [[ $SKIP_DATA -eq 1 && -f data/rail/pmos_off.csv ]]; then echo "skipped (--skip-data)"; else python scripts/01b_generate_rail_data.py --n "$RAIL_N"; fi

step "2. Part A data check"
python scripts/02_check_data.py

step "3. Part A model training (4 model types x 4 cases)"
python scripts/03_train_models.py $FAST

step "4. Part B gate validation (18 cases x 200 corners)"
python scripts/04_validate_gates.py

step "5. Part C 3-bit CLA (200 corners x 128 vectors; SPICE cached)"
python scripts/05_validate_circuit.py

step "SUMMARY"
python - <<'EOF'
import pandas as pd
pd.set_option("display.width", 200)
f = lambda v: f"{v:.4g}"
print("\n--- Part A: validation median error % (mean over id, ig, is, ib)")
c = pd.read_csv("results/part_a/model_comparison.csv")
print(c.pivot_table(index="model", columns="case", values="median_err_%").round(2))
print("\n--- Part A: chosen models, test sets")
print(pd.read_csv("results/part_a/chosen_models_test.csv").round(3).to_string(index=False))
print("\n--- Part B: gate results")
print(pd.read_csv("results/part_b/gate_results_table.csv", dtype={"input": str}).to_string(index=False, float_format=f))
print("\n--- Part C: circuit summary")
print(pd.read_csv("results/part_c/circuit_summary.csv").to_string(index=False, float_format=f))
EOF
echo
echo "Total time: $(( ($(date +%s) - START) / 60 )) min.  Log: $LOG"
