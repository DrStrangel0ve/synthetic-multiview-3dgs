# Synthetic Splatfacto Run Comparison

| Run | Source | Views | Iterations | PSNR | SSIM | LPIPS | FPS | Export MB |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `700_iters` | procedural | 48 | 700 | 22.7067 | 0.927445 | 0.351811 | 57.6329 | 3.70466 |
| `3000_iters` | procedural | 48 | 3000 | 18.7703 | 0.921359 | 0.324095 | 24.174 | 28.6729 |
| `genai_16_views_700` | generated contact sheet | 16 | 700 | 17.3488 | 0.817609 | 0.432271 | 0.210589 | 3.60563 |

In this first synthetic run, the controlled procedural 700-iteration checkpoint has the best PSNR/SSIM. The generated contact-sheet run reconstructs, but its lower scores reflect cross-view inconsistency and the smaller 16-view orbit.
