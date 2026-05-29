#!/usr/bin/env bash
set -euo pipefail

mkdir -p results/metrics exports/ceramic_idol_turntable_700 exports/ceramic_idol_turntable_3000

ns-eval \
  --load-config outputs/ceramic_idol_turntable/splatfacto/20260529_053709/config.yml \
  --output-path results/metrics/ceramic_idol_turntable_700.json

ns-eval \
  --load-config outputs/ceramic_idol_turntable/splatfacto/long_3000/config.yml \
  --output-path results/metrics/ceramic_idol_turntable_3000.json

ns-export gaussian-splat \
  --load-config outputs/ceramic_idol_turntable/splatfacto/20260529_053709/config.yml \
  --output-dir exports/ceramic_idol_turntable_700 \
  --output-filename ceramic_idol_turntable_700.ply \
  --ply-color-mode rgb

ns-export gaussian-splat \
  --load-config outputs/ceramic_idol_turntable/splatfacto/long_3000/config.yml \
  --output-dir exports/ceramic_idol_turntable_3000 \
  --output-filename ceramic_idol_turntable_3000.ply \
  --ply-color-mode rgb
