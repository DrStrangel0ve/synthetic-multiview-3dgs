# Synthetic Multiview 3DGS

Can we make a Gaussian splat from generated/synthetic views of an object?

This repo tests that idea in three ways. First, it generates a controlled prompt-defined object from many known camera views and writes a Nerfstudio-compatible `transforms.json`. Second, it uses a real image-generation contact sheet, splits it into turntable views, assigns circular camera poses, and runs the same Splatfacto training path. Third, it uses [Zero123++](https://github.com/SUDO-AI-3D/zero123plus) to turn one prompt-generated image into a fixed six-view multiview set.

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

The generated-contact-sheet track is the first real gen-AI version of that idea. The Zero123++ track is the first model-native multiview version: it is still pure generation, but it is much more geometry-consistent than asking one image model for a contact sheet.

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

Generate Zero123++ views from the committed prompt-generated seed image:

```bash
bash scripts/run_zero123plus_with_docker.sh \
  --input datasets/zero123plus_seed/seed_front.png \
  --output datasets/zero123plus_seed/zero123plus_grid_seed123_steps36.png \
  --conditioning-output datasets/zero123plus_seed/conditioning_512.png \
  --steps 36 \
  --seed 123
```

Train the Zero123++ dataset with a tiny-dataset holdout:

```bash
python scripts/prepare_zero123plus_dataset.py \
  --sheet datasets/zero123plus_seed/zero123plus_grid_seed123_steps36.png \
  --output datasets/zero123plus_ceramic_idol_seed123_6

MAX_ITERS=700 \
DATASET=datasets/zero123plus_ceramic_idol_seed123_6 \
EXPERIMENT=zero123plus_seed123_6_700_interval3 \
RUN_ID=700 \
EVAL_MODE=interval \
EVAL_INTERVAL=3 \
./scripts/run_splatfacto_with_docker.sh
```

## Current Datasets

Procedural control:

![Synthetic turntable preview](datasets/ceramic_idol_turntable/preview_contact_sheet.jpg)

Generated contact sheet:

![Generated contact sheet preview](datasets/genai_ceramic_idol_16/preview_contact_sheet.jpg)

Zero123++ generated views:

![Zero123++ seed 123 preview](datasets/zero123plus_ceramic_idol_seed123_6/preview_contact_sheet.jpg)

| Dataset | Source | Views | Resolution | Pose Source |
| --- | --- | ---: | --- | --- |
| `datasets/ceramic_idol_turntable/` | procedural renderer | 48 | 384 x 384 | exact synthetic camera matrices |
| `datasets/genai_ceramic_idol_16/` | AI-generated 4x4 contact sheet | 16 | 384 x 384 | assigned circular turntable poses |
| `datasets/zero123plus_ceramic_idol_seed123_6/` | Zero123++ v1.2 | 6 | 384 x 384 | Zero123++ fixed azimuth/elevation set |

## Current Results

| Run | Source | Views | Eval | PSNR | SSIM | LPIPS | Export MB |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| `700_iters` | procedural | 48 | fraction | 22.7067 | 0.927445 | 0.351811 | 3.704 |
| `genai_16_views_700` | generated contact sheet | 16 | fraction | 17.3488 | 0.817609 | 0.432271 | 3.606 |
| `zero123plus_seed123_6_evalall` | Zero123++ seed 123 | 6 | all frames | 27.9129 | 0.924495 | 0.191879 | 3.060 |
| `zero123plus_seed123_6_holdout` | Zero123++ seed 123 | 6 | interval 3 | 19.2208 | 0.876730 | 0.473959 | 3.027 |
| `zero123plus_seed456_holdout` | Zero123++ seed 456 | 6 | interval 3 | 19.1784 | 0.877714 | 0.466039 | 2.990 |
| `zero123plus_seed456_masked_holdout` | Zero123++ seed 456, masks | 6 | interval 3 | 18.7063 | 0.874184 | 0.545769 | 3.231 |

The strongest pure-generation result so far is the Zero123++ path. Eval-all is an upper bound because it evaluates training views. The interval-3 rows are a fairer holdout test on tiny six-view datasets; even there, Zero123++ beats the one-shot generated contact sheet on PSNR and SSIM.

## Why This Should Beat The Earlier PSNR

The earlier open-video experiment had several quality traps: uncontrolled camera motion, low texture, water/blur, unknown intrinsics, and COLMAP failures. The procedural synthetic dataset removes those variables. The generated-contact-sheet dataset brings controlled inconsistency back in. Zero123++ improves that by generating a camera-conditioned multiview set, which is the first path here that looks plausibly portfolio-grade after one seed image.

## Repo Shape

- `scripts/render_prompt_turntable.py`: synthetic prompt-object renderer and Nerfstudio dataset writer.
- `scripts/prepare_genai_contact_sheet.py`: split a generated 4x4 contact sheet into a Nerfstudio dataset.
- `scripts/run_zero123plus_with_docker.sh`: run Zero123++ generation inside the CUDA Nerfstudio Docker image.
- `scripts/run_zero123plus_inside.py`: load the Zero123++ Diffusers pipeline and write a six-view sheet.
- `scripts/prepare_zero123plus_dataset.py`: split Zero123++ output into Nerfstudio frames with fixed camera poses.
- `scripts/add_background_masks.py`: make simple border-color masks for solid-background generated views.
- `scripts/run_splatfacto_with_docker.sh`: Docker wrapper for Nerfstudio.
- `scripts/run_splatfacto_inside.sh`: train/eval/export loop inside the Nerfstudio container.
- `scripts/summarize_metrics.py`: extract PSNR/SSIM/LPIPS from `ns-eval` JSON.
- `scripts/summarize_run_comparison.py`: compare multiple Splatfacto runs.
- `datasets/ceramic_idol_turntable/`: generated multiview images and camera poses.
- `datasets/genai_ceramic_idol_source/`: committed AI-generated source contact sheet.
- `datasets/genai_ceramic_idol_16/`: generated-view training crops and camera poses.
- `datasets/zero123plus_seed/`: prompt-generated seed image and Zero123++ view sheets.
- `datasets/zero123plus_ceramic_idol_*/`: Zero123++ Nerfstudio datasets.
- `results/`: metric summaries and run notes.
- `exports/`: exported Gaussian `.ply` splats.

## License

MIT for code and generated synthetic assets.
