# Run Notes

Last updated: 2026-05-29

The first synthetic object experiment uses 48 generated views at 384 x 384 resolution with exact camera poses. Nerfstudio Splatfacto was trained twice:

- `700_iters`: quick sanity run, best PSNR/SSIM.
- `3000_iters`: longer run, better LPIPS but worse PSNR/SSIM and much larger export.

This suggests the next useful sweeps are not just "train longer":

- add alpha/mask supervision or flatter background;
- sweep view count and resolution;
- compare known-pose training against COLMAP-estimated poses from the same rendered images;
- try a real AI multiview generator while preserving the same camera-pose contract.
