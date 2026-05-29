#!/usr/bin/env bash
set -euo pipefail

IMAGE="${NERFSTUDIO_IMAGE:-ghcr.io/nerfstudio-project/nerfstudio:latest}"
WORKSPACE="$(pwd)"
CACHE_DIR="${HOME}/.cache"

mkdir -p "$CACHE_DIR" results/metrics results/logs results/status exports

docker run \
  --gpus all \
  --rm \
  -u "$(id -u)" \
  -e HOME=/home/user \
  -e USER=user \
  -e LOGNAME=user \
  -e XDG_CACHE_HOME=/home/user/.cache \
  -e MPLCONFIGDIR=/home/user/.cache/matplotlib \
  -e TORCHINDUCTOR_CACHE_DIR=/home/user/.cache/torchinductor \
  -e MAX_ITERS \
  -e TRAIN_TIMEOUT_MIN \
  -e DATASET \
  -e EXPERIMENT \
  -e RUN_ID \
  -e EXPORT_MODELS \
  -v "${WORKSPACE}:/workspace" \
  -v "${CACHE_DIR}:/home/user/.cache" \
  --shm-size=12gb \
  -w /workspace \
  "$IMAGE" \
  bash scripts/run_splatfacto_inside.sh
