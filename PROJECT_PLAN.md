# Project Plan

## Milestone 1: Controlled Synthetic Baseline

- Generate a consistent prompt-defined object from known camera poses.
- Train Nerfstudio Splatfacto without COLMAP.
- Export a Gaussian `.ply` and collect PSNR/SSIM/LPIPS.
- Use this to sanity-check the reconstruction pipeline.

## Milestone 2: AI Multiview Swap

- Add a generated contact-sheet input contract for multiview images. Done.
- Support fixed turntable camera assumptions for generated views. Done.
- Compare generated-view splats against the procedural ground-truth baseline. Done for the first 16-view contact sheet.
- Replace the contact-sheet prompt with a model-native multiview generator and keep the same Nerfstudio data contract. Done with Zero123++ v1.2.
- Next: improve the Zero123++ path with better seed-image background control, more seeds, and cleaner segmentation/matting.

## Milestone 3: Evaluation

- Sweep view count: 8, 16, 24, 48, 96.
- Sweep resolution: 256, 384, 512.
- Compare known poses vs COLMAP-estimated poses.
- Publish a table of quality, training time, and exported splat size.
- Track eval-all separately from holdout metrics so training-view reconstruction is not confused with generalization.
