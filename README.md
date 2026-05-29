# Synthetic Multiview 3DGS

Can we make a Gaussian splat from generated/synthetic views of an object?

This repo tests that idea in two ways. First, it generates a controlled prompt-defined object from many known camera views and writes a Nerfstudio-compatible `transforms.json`. Second, it uses a real image-generation contact sheet, splits it into turntable views, assigns circular camera poses, and runs the same Splatfacto training path.

Both tracks avoid COLMAP so the benchmark isolates a different question: are the images themselves consistent enough for a Gaussian reconstruction?

## Concept

Prompt:

> A small glossy ceramic sci-fi desk idol, somewhere between a toy robot and a crystal mushroom, with teal glass highlights, amber side fins, and tiny black eyes.

The procedural generator is deterministic, but it is structured like a text-to-multiview pipeline:

1. Prompt describes the object.
2. Renderer produces consistent views around the object.
3. Known camera poses are written to `transforms.json`.
4. Nerfstudio Splatfacto trains a Gaussian splat.
5. `ns-eval` produces PSNR/SSIM/LPIPS.

The generated-contact-sheet track is the first real gen-AI version of that idea. It is less geometrically clean than the procedural track, but that is the useful stress test.

## Run

Generate the synthetic multiview dataset:

```bash
python scripts/render_prompt_turntable.py --views 48 --size 384
```

Train with Nerfstudio through Docker/WSL:

```bash
MAX_ITERS=700 ./scripts/run_splatfacto_with_docker.sh
```

Prepare the committed generated-view contact sheet:

```bash
python scripts/prepare_genai_contact_sheet.py
```

Train that generated-view dataset:

```bash
MAX_ITERS=700 DATASET=datasets/genai_ceramic_idol_16 EXPERIMENT=genai_ceramic_idol_16_700 RUN_ID=700 ./scripts/run_splatfacto_with_docker.sh
```

## Current Datasets

Procedural control:

![Synthetic turntable preview](datasets/ceramic_idol_turntable/preview_contact_sheet.jpg)

Generated contact sheet:

![Generated contact sheet preview](datasets/genai_ceramic_idol_16/preview_contact_sheet.jpg)

| Dataset | Source | Views | Resolution | Pose Source |
| --- | --- | ---: | --- | --- |
| `datasets/ceramic_idol_turntable/` | procedural renderer | 48 | 384 x 384 | exact synthetic camera matrices |
| `datasets/genai_ceramic_idol_16/` | AI-generated 4x4 contact sheet | 16 | 384 x 384 | assigned circular turntable poses |

## Current Results

| Run | Source | Views | Iterations | PSNR | SSIM | LPIPS | Export MB |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `700_iters` | procedural | 48 | 700 | 22.7067 | 0.927445 | 0.351811 | 3.704 |
| `3000_iters` | procedural | 48 | 3000 | 18.7703 | 0.921359 | 0.324095 | 28.669 |
| `genai_16_views_700` | generated contact sheet | 16 | 700 | 17.3488 | 0.817609 | 0.432271 | 3.606 |

The first finding is already useful: longer procedural training improved LPIPS but hurt PSNR/SSIM and created a much larger splat. The generated-contact-sheet run reconstructs, but it scores lower because the views are not perfectly geometry-consistent and there are only 16 of them.

## Why This Should Beat The Earlier PSNR

The earlier open-video experiment had several quality traps: uncontrolled camera motion, low texture, water/blur, unknown intrinsics, and COLMAP failures. The procedural synthetic dataset removes those variables. If PSNR is still bad there, the issue is the training config or data contract, not the source video. The generated-contact-sheet dataset brings controlled inconsistency back in, which makes it a good bridge toward real text-to-multiview models.

## Repo Shape

- `scripts/render_prompt_turntable.py`: synthetic prompt-object renderer and Nerfstudio dataset writer.
- `scripts/prepare_genai_contact_sheet.py`: split a generated 4x4 contact sheet into a Nerfstudio dataset.
- `scripts/run_splatfacto_with_docker.sh`: Docker wrapper for Nerfstudio.
- `scripts/run_splatfacto_inside.sh`: train/eval/export loop inside the Nerfstudio container.
- `scripts/summarize_metrics.py`: extract PSNR/SSIM/LPIPS from `ns-eval` JSON.
- `scripts/summarize_run_comparison.py`: compare multiple Splatfacto runs.
- `datasets/ceramic_idol_turntable/`: generated multiview images and camera poses.
- `datasets/genai_ceramic_idol_source/`: committed AI-generated source contact sheet.
- `datasets/genai_ceramic_idol_16/`: generated-view training crops and camera poses.
- `results/`: metric summaries and run notes.
- `exports/`: exported Gaussian `.ply` splats.

## License

MIT for code and generated synthetic assets.
