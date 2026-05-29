# Synthetic Splatfacto Run Comparison

| Run | Source | Views | Iterations | Eval | PSNR | SSIM | LPIPS | FPS | Export MB |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `700_iters` | procedural | 48 | 700 | fraction | 22.7067 | 0.927445 | 0.351811 | 57.6329 | 3.70466 |
| `3000_iters` | procedural | 48 | 3000 | fraction | 18.7703 | 0.921359 | 0.324095 | 24.174 | 28.6729 |
| `genai_16_views_700` | generated contact sheet | 16 | 700 | fraction | 17.3488 | 0.817609 | 0.432271 | 0.210589 | 3.60563 |
| `zero123plus_seed123_6_evalall` | Zero123++ seed 123 | 6 | 700 | all frames | 27.9129 | 0.924495 | 0.191879 | 43.5671 | 3.06035 |
| `zero123plus_seed123_6_holdout` | Zero123++ seed 123 | 6 | 700 | interval 3 | 19.2208 | 0.87673 | 0.473959 | 16.7147 | 3.02665 |
| `zero123plus_seed123_steps75_holdout` | Zero123++ seed 123, 75 steps | 6 | 700 | interval 3 | 19.0156 | 0.871499 | 0.478934 | 26.0011 | 3.00813 |
| `zero123plus_seed456_holdout` | Zero123++ seed 456 | 6 | 700 | interval 3 | 19.1784 | 0.877714 | 0.466039 | 26.9901 | 2.98996 |
| `zero123plus_seed456_masked_holdout` | Zero123++ seed 456, masks | 6 | 700 | interval 3 | 18.7063 | 0.874184 | 0.545769 | 25.6305 | 3.23078 |

Zero123++ is the current best pure-generation path. Eval-all is an upper bound because it evaluates training views; interval-3 is the fairer tiny-dataset holdout.
