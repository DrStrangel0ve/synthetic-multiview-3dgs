# Run Notes

Last updated: 2026-05-29

The first synthetic object experiment uses 48 procedural views at 384 x 384 resolution with exact camera poses. Nerfstudio Splatfacto was trained twice:

- `700_iters`: quick sanity run, best PSNR/SSIM.
- `3000_iters`: longer run, better LPIPS but worse PSNR/SSIM and much larger export.

The first real gen-AI experiment uses one generated 4x4 contact sheet, split into 16 views with assigned circular poses:

- `genai_16_views_700`: reconstructs, but PSNR/SSIM/LPIPS are worse than the procedural control because the generated object is not perfectly consistent across views.

The first model-native multiview experiment uses a prompt-generated seed image and Zero123++ v1.2:

- `zero123plus_seed123_6_700_evalall`: 27.91 PSNR / 0.924 SSIM / 0.192 LPIPS. This is an upper bound because every generated view is also an eval view.
- `zero123plus_seed123_6_700_interval3`: 19.22 PSNR / 0.877 SSIM / 0.474 LPIPS. This is the fairer tiny-dataset holdout baseline.
- `zero123plus_seed123_steps75_6_700_interval3`: more diffusion steps did not help the holdout metric.
- `zero123plus_seed456_6_700_interval3`: similar PSNR, slightly better SSIM/LPIPS than seed 123.
- `zero123plus_seed456_6_masked_700_interval3`: crude masks hurt; the white ceramic object is too close to the gray background for simple threshold masks.

This suggests the next useful sweeps are not just "train longer":

- add alpha/mask supervision or flatter background;
- sweep view count and resolution;
- compare known-pose training against COLMAP-estimated poses from the same rendered images;
- try a model-native AI multiview generator while preserving the same camera-pose contract;
- add a geometry consistency score before training so obviously inconsistent view sets can be rejected early;
- try stronger background control before Zero123++ generation, because downstream masks are worse than generating cleaner source views.
