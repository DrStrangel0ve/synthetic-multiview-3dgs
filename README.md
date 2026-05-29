# Synthetic Multiview 3DGS

Can we make a Gaussian splat from generated/synthetic views of an object?

This repo tests that idea in a controlled way. Instead of starting with shaky internet video and hoping COLMAP finds good camera poses, it generates a prompt-defined object from many known camera views and writes a Nerfstudio-compatible `transforms.json`. Splatfacto can train directly on those views without COLMAP.

## Concept

Prompt:

> A small glossy ceramic sci-fi desk idol, somewhere between a toy robot and a crystal mushroom, with teal glass highlights, amber side fins, and tiny black eyes.

The current generator is procedural and deterministic, but it is structured like a text-to-multiview pipeline:

1. Prompt describes the object.
2. Renderer produces consistent views around the object.
3. Known camera poses are written to `transforms.json`.
4. Nerfstudio Splatfacto trains a Gaussian splat.
5. `ns-eval` produces PSNR/SSIM/LPIPS.

The next step is to swap the procedural renderer for a real multiview generative model such as Zero123++/Wonder3D-style view synthesis while keeping the same Nerfstudio data contract.

## Run

Generate the synthetic multiview dataset:

```bash
python scripts/render_prompt_turntable.py --views 48 --size 384
```

Train with Nerfstudio through Docker/WSL:

```bash
MAX_ITERS=700 ./scripts/run_splatfacto_with_docker.sh
```

## Current Dataset

![Synthetic turntable preview](datasets/ceramic_idol_turntable/preview_contact_sheet.jpg)

| Field | Value |
| --- | --- |
| Dataset path | `datasets/ceramic_idol_turntable/` |
| Views | 48 |
| Resolution | 384 x 384 |
| Camera path | circular turntable |
| Pose source | exact synthetic camera matrices |
| Reconstruction method | Nerfstudio `splatfacto` |

## Current Results

| Run | Iterations | PSNR | SSIM | LPIPS | Export MB |
| --- | ---: | ---: | ---: | ---: | ---: |
| `700_iters` | 700 | 22.7067 | 0.927445 | 0.351811 | 3.704 |
| `3000_iters` | 3000 | 18.7703 | 0.921359 | 0.324095 | 28.669 |

The first finding is already useful: longer training improved LPIPS but hurt PSNR/SSIM and created a much larger splat. This is exactly why the synthetic track is valuable; it gives us a clean place to tune iteration count, view count, and regularization.

## Why This Should Beat The Earlier PSNR

The earlier open-video experiment had several quality traps: uncontrolled camera motion, low texture, water/blur, unknown intrinsics, and COLMAP failures. This synthetic dataset removes those variables. If PSNR is still bad here, the issue is the training config or data contract, not the source video.

## Repo Shape

- `scripts/render_prompt_turntable.py`: synthetic prompt-object renderer and Nerfstudio dataset writer.
- `scripts/run_splatfacto_with_docker.sh`: Docker wrapper for Nerfstudio.
- `scripts/run_splatfacto_inside.sh`: train/eval/export loop inside the Nerfstudio container.
- `scripts/summarize_metrics.py`: extract PSNR/SSIM/LPIPS from `ns-eval` JSON.
- `scripts/summarize_run_comparison.py`: compare multiple Splatfacto runs.
- `datasets/ceramic_idol_turntable/`: generated multiview images and camera poses.
- `results/`: metric summaries and run notes.
- `exports/`: exported Gaussian `.ply` splats.

## License

MIT for code and generated synthetic assets.
