#!/usr/bin/env bash
# Re-runs the improved pipeline end to end and prints a summary at the end.
# Usage (from the repo root, inside the Python environment):
#     bash run_all.sh                 # everything (data + training + Parts B and C), rail variant
#     bash run_all.sh --skip-data     # keep the existing datasets; re-train + Parts B and C
#     bash run_all.sh --no-rail       # ablation: train without data/rail; outputs go to */no_rail/
#     bash run_all.sh --compare       # print rail vs no-rail side by side (no recompute)
#     bash run_all.sh --fast          # quick check of the whole chain (OVERWRITES default outputs)
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
NO_RAIL=""
COMPARE=0
for arg in "$@"; do
  case "$arg" in
    --fast) FAST="--fast"; RAIL_N=3000 ;;
    --skip-data) SKIP_DATA=1 ;;
    --no-rail) NO_RAIL="--no-rail" ;;
    --compare) COMPARE=1 ;;
  esac
done
SUB=""; [[ -n "$NO_RAIL" ]] && SUB="/no_rail"
export SUB

if [[ $COMPARE -eq 1 ]]; then
python - <<'EOF'
import os
import pandas as pd
pd.set_option("display.width", 200)
variants = [("rail", "results/part_b", "results/part_c"),
            ("no_rail", "results/part_b/no_rail", "results/part_c/no_rail")]
rows = []
for name, b, c in variants:
    if not (os.path.exists(f"{b}/gate_all.csv") and os.path.exists(f"{c}/circuit_summary.csv")):
        print(f"[!] {name}: results not found in {b} / {c}, skipping")
        continue
    g = pd.read_csv(f"{b}/gate_all.csv", dtype={"inp": str})
    s = pd.read_csv(f"{c}/circuit_summary.csv").set_index("method")
    pl, ld = s.loc["ML plain sum (project method)"], s.loc["ML loading-aware"]
    rows.append({"variant": name,
                 "B median err %": g.err_pct.median(), "B mean acc %": 100 - g.err_pct.mean(),
                 "C plain median err %": pl.median_error_pct, "C plain mean acc %": pl.mean_accuracy_pct,
                 "C loading median err %": ld.median_error_pct, "C loading mean acc %": ld.mean_accuracy_pct})
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:.4g}"))
EOF
exit 0
fi

step() { echo; echo "==================== $(date +%H:%M:%S)  $*"; }
START=$(date +%s)
echo "Variant: ${NO_RAIL:---rail (default)}"

step "0. Check tools"
ngspice --version | head -2
python -c "import numpy, pandas, sklearn, lightgbm, xgboost, matplotlib, joblib; print('python packages OK')"
python -c "import torch; print('torch', torch.__version__, '| GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'not available (CPU will be used)')" || echo "torch not installed: scikit-learn MLP (CPU) will be used"

step "1. Part A datasets (uniform, 10,000 per case) - reuse if present"
need_data=0
for c in nmos_on nmos_off pmos_on pmos_off; do [[ -f data/$c.csv ]] || need_data=1; done
if [[ $need_data -eq 1 ]]; then python scripts/01_generate_transistor_data.py; fi
wc -l data/*.csv

step "1b. Part A extra rail-focused training data ($RAIL_N per case)"
if [[ -n "$NO_RAIL" ]]; then echo "skipped (--no-rail)"
elif [[ $SKIP_DATA -eq 1 && -f data/rail/pmos_off.csv ]]; then echo "skipped (--skip-data)"
else python scripts/01b_generate_rail_data.py --n "$RAIL_N"; fi

step "2. Part A data check"
python scripts/02_check_data.py

step "3. Part A model training (4 model types x 4 cases)"
python scripts/03_train_models.py $FAST $NO_RAIL

step "4. Part B gate validation (18 cases x 200 corners)"
python scripts/04_validate_gates.py $NO_RAIL

step "5. Part C 3-bit CLA (200 corners x 128 vectors; SPICE cached)"
python scripts/05_validate_circuit.py $NO_RAIL

step "SUMMARY"
python - <<'EOF'
import os
import pandas as pd
pd.set_option("display.width", 200)
f = lambda v: f"{v:.4g}"
sub = os.environ.get("SUB", "")
A, B, C = f"results/part_a{sub}", f"results/part_b{sub}", f"results/part_c{sub}"
print(f"\n--- Part A: validation median error % (mean over id, ig, is, ib)  [{A}]")
c = pd.read_csv(f"{A}/model_comparison.csv")
print(c.pivot_table(index="model", columns="case", values="median_err_%").round(2))
print("\n--- Part A: chosen models, test sets")
print(pd.read_csv(f"{A}/chosen_models_test.csv").round(3).to_string(index=False))
print(f"\n--- Part B: gate results  [{B}]")
print(pd.read_csv(f"{B}/gate_results_table.csv", dtype={"input": str}).to_string(index=False, float_format=f))
print(f"\n--- Part C: circuit summary  [{C}]")
print(pd.read_csv(f"{C}/circuit_summary.csv").to_string(index=False, float_format=f))
EOF
echo
echo "Total time: $(( ($(date +%s) - START) / 60 )) min.  Log: $LOG"