# Project Plan

## Milestone 1: Controlled Synthetic Baseline

- Generate a consistent prompt-defined object from known camera poses.
- Train Nerfstudio Splatfacto without COLMAP.
- Export a Gaussian `.ply` and collect PSNR/SSIM/LPIPS.
- Use this to sanity-check the reconstruction pipeline.

## Milestone 2: AI Multiview Swap

- Add an `ai_views/` input contract for generated multiview images.
- Support fixed turntable camera assumptions for generated views.
- Compare generated-view splats against the procedural ground-truth baseline.

## Milestone 3: Evaluation

- Sweep view count: 8, 16, 24, 48, 96.
- Sweep resolution: 256, 384, 512.
- Compare known poses vs COLMAP-estimated poses.
- Publish a table of quality, training time, and exported splat size.
