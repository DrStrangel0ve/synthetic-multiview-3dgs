# Run Notes

Last updated: 2026-05-29

The first synthetic object experiment uses 48 procedural views at 384 x 384 resolution with exact camera poses. Nerfstudio Splatfacto was trained twice:

- `700_iters`: quick sanity run, best PSNR/SSIM.
- `3000_iters`: longer run, better LPIPS but worse PSNR/SSIM and much larger export.

The first real gen-AI experiment uses one generated 4x4 contact sheet, split into 16 views with assigned circular poses:

- `genai_16_views_700`: reconstructs, but PSNR/SSIM/LPIPS are worse than the procedural control because the generated object is not perfectly consistent across views.

This suggests the next useful sweeps are not just "train longer":

- add alpha/mask supervision or flatter background;
- sweep view count and resolution;
- compare known-pose training against COLMAP-estimated poses from the same rendered images;
- try a model-native AI multiview generator while preserving the same camera-pose contract;
- add a geometry consistency score before training so obviously inconsistent view sets can be rejected early.
