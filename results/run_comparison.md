# Synthetic Splatfacto Run Comparison

| Run | Iterations | PSNR | SSIM | LPIPS | FPS | Export MB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `700_iters` | 700 | 22.7067 | 0.927445 | 0.351811 | 57.6329 | 3.70466 |
| `3000_iters` | 3000 | 18.7703 | 0.921359 | 0.324095 | 24.174 | 28.6729 |

In this first synthetic run, the shorter 700-iteration checkpoint has better PSNR/SSIM, while the 3,000-iteration checkpoint has better LPIPS but a much larger exported splat.
