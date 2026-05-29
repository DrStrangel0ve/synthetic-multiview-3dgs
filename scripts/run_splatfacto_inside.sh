#!/usr/bin/env bash
set -u

MAX_ITERS="${MAX_ITERS:-700}"
TRAIN_TIMEOUT_MIN="${TRAIN_TIMEOUT_MIN:-90}"
DATASET="${DATASET:-datasets/ceramic_idol_turntable}"
EXPERIMENT="${EXPERIMENT:-ceramic_idol_turntable}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%d_%H%M%S)}"
EXPORT_MODELS="${EXPORT_MODELS:-1}"

mkdir -p results/metrics results/logs results/status exports outputs

status_path="results/status/${EXPERIMENT}.json"
metrics_path="results/metrics/${EXPERIMENT}.json"
train_log="results/logs/${EXPERIMENT}_train.log"
eval_log="results/logs/${EXPERIMENT}_eval.log"
export_dir="exports/${EXPERIMENT}"

python3 - <<PY
import json
from pathlib import Path

Path("results/run_config.json").write_text(json.dumps({
  "run_id": "$RUN_ID",
  "dataset": "$DATASET",
  "experiment": "$EXPERIMENT",
  "max_iters": int("$MAX_ITERS")
}, indent=2), encoding="utf-8")
PY

echo "train ${EXPERIMENT}"
if ! timeout "${TRAIN_TIMEOUT_MIN}m" ns-train splatfacto \
  --data "$DATASET" \
  --output-dir outputs \
  --experiment-name "$EXPERIMENT" \
  --timestamp "$RUN_ID" \
  --max-num-iterations "$MAX_ITERS" \
  --steps-per-save "$MAX_ITERS" \
  --steps-per-eval-all-images "$MAX_ITERS" \
  --vis tensorboard \
  >"$train_log" 2>&1; then
  python3 - <<PY
import json
from pathlib import Path
Path("$status_path").write_text(json.dumps({"status": "failed", "stage": "train", "log": "$train_log"}, indent=2), encoding="utf-8")
PY
  exit 1
fi

config_path="$(find "outputs/${EXPERIMENT}" -path "*/${RUN_ID}/config.yml" -print 2>/dev/null | sort | tail -n 1)"
if [[ -z "$config_path" ]]; then
  python3 - <<PY
import json
from pathlib import Path
Path("$status_path").write_text(json.dumps({"status": "failed", "stage": "config_lookup"}, indent=2), encoding="utf-8")
PY
  exit 1
fi

echo "eval ${EXPERIMENT}"
if ! ns-eval --load-config "$config_path" --output-path "$metrics_path" >"$eval_log" 2>&1; then
  python3 - <<PY
import json
from pathlib import Path
Path("$status_path").write_text(json.dumps({"status": "failed", "stage": "eval", "log": "$eval_log", "config": "$config_path"}, indent=2), encoding="utf-8")
PY
  exit 1
fi

if [[ "$EXPORT_MODELS" == "1" ]]; then
  mkdir -p "$export_dir"
  ns-export gaussian-splat \
    --load-config "$config_path" \
    --output-dir "$export_dir" \
    --output-filename "${EXPERIMENT}.ply" \
    --ply-color-mode rgb \
    >>"$eval_log" 2>&1 || true
fi

python3 scripts/summarize_metrics.py --metrics "$metrics_path" --dataset "$EXPERIMENT"

python3 - <<PY
import json
from pathlib import Path
Path("$status_path").write_text(json.dumps({"status": "ok", "stage": "done", "metrics": "$metrics_path", "config": "$config_path"}, indent=2), encoding="utf-8")
PY
