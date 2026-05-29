#!/usr/bin/env bash
set -euo pipefail

IMAGE="${NERFSTUDIO_IMAGE:-ghcr.io/nerfstudio-project/nerfstudio:latest}"
WORKSPACE="$(pwd)"
CACHE_DIR="${HOME}/.cache"
DEPS_DIR="${ZERO123PLUS_DEPS_DIR:-/home/user/.cache/zero123plus_deps}"

mkdir -p "$CACHE_DIR" results/logs

docker run \
  --gpus all \
  --rm \
  -u "$(id -u):$(id -g)" \
  -e HOME=/home/user \
  -e USER=user \
  -e LOGNAME=user \
  -e XDG_CACHE_HOME=/home/user/.cache \
  -e HF_HOME=/home/user/.cache/huggingface \
  -e TRANSFORMERS_CACHE=/home/user/.cache/huggingface \
  -e DIFFUSERS_CACHE=/home/user/.cache/huggingface \
  -v "${WORKSPACE}:/workspace" \
  -v "${CACHE_DIR}:/home/user/.cache" \
  --shm-size=12gb \
  -w /workspace \
  "$IMAGE" \
  bash -lc "
    set -euo pipefail
    mkdir -p '$DEPS_DIR'
    if [[ ! -f '$DEPS_DIR/.zero123plus-ready' ]]; then
      python3 -m pip install --quiet --target '$DEPS_DIR' \
        diffusers==0.20.2 \
        transformers==4.29.2 \
        accelerate==0.21.0 \
        huggingface_hub==0.19.4 \
        safetensors==0.4.2
      touch '$DEPS_DIR/.zero123plus-ready'
    fi
    PYTHONPATH='$DEPS_DIR':\${PYTHONPATH:-} python3 scripts/run_zero123plus_inside.py \"\$@\"
  " zero123plus "$@"
