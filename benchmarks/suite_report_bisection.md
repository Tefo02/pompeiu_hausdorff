# Mass Benchmark Report: `best_first` vs `idastar_bisection`

- **Date:** 2026-11-28 10:01:42
- **Pairs evaluated:** 20 (`OK`: 19, `Non-OK`: 1)
- **Parity passed:** 19/19
- **Tolerance override:** per-manifest
- **Mean Peak RSS Delta:** -36.36%
- **Mean Wall-Time Delta:** -10.52%

| Pair ID | Category | Base RSS (MB) | Cand RSS (MB) | RSS Delta | Base Time (ms) | Cand Time (ms) | Time Delta | Parity |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| `107100_decimate_50` | decimation | 13.49 | 6.95 | -48.45% | 133.8 | 61.6 | -53.97% | CONVERGED (Within Tolerance) |
| `existing_848343_decimate` | high_density_decimation | 356.58 | 64.30 | -81.97% | 9930.8 | 14329.8 | +44.30% | EXACT MATCH |
| `107100_noise_005` | perturbation_noise | 14.24 | 7.85 | -44.86% | 153.3 | 102.3 | -33.27% | CONVERGED (Within Tolerance) |
| `107100_quant_010` | quantization | 12.35 | 7.68 | -37.77% | 122.8 | 81.7 | -33.46% | EXACT MATCH |
| `existing_107100_sf` | remeshing | 132.30 | 29.23 | -77.91% | 2518.6 | 5517.8 | +119.08% | EXACT MATCH |
| `synthetic_cube_translation` | sanity_analytical | 6.22 | 4.80 | -22.85% | 21.0 | 31.3 | +49.13% | EXACT MATCH |
| `107100_smooth_taubin` | smoothing | 14.41 | 7.97 | -44.69% | 133.7 | 71.7 | -46.38% | CONVERGED (Within Tolerance) |
| `existing_lucy_decimate05` | stress_memory | 447.74 | 698.66 | - | 20017.3 | 20048.0 | - | TIMEOUT/TIMEOUT |
| `107100_soup_jitter` | triangle_soup | 14.52 | 8.51 | -41.40% | 215.4 | 112.1 | -47.97% | EXACT MATCH |
| `107100_decimate_20` | decimation | 6.45 | 6.63 | +2.91% | 81.9 | 51.3 | -37.37% | CONVERGED (Within Tolerance) |
| `107100_noise_020` | perturbation_noise | 14.27 | 8.02 | -43.84% | 164.2 | 112.0 | -31.76% | CONVERGED (Within Tolerance) |
| `848343_quant_010` | quantization | 66.91 | 60.71 | -9.26% | 1034.6 | 880.1 | -14.93% | EXACT MATCH |
| `synthetic_icosphere_refinement` | sanity_analytical | 4.00 | 0.72 | -82.01% | 31.1 | 10.7 | -65.66% | EXACT MATCH |
| `848343_smooth_taubin` | smoothing | 143.23 | 88.22 | -38.41% | 2750.6 | 3512.2 | +27.69% | EXACT MATCH |
| `848343_soup_jitter` | triangle_soup | 131.16 | 104.08 | -20.65% | 2772.7 | 2185.7 | -21.17% | CONVERGED (Within Tolerance) |
| `848343_decimate_50` | decimation | 271.34 | 64.25 | -76.32% | 6092.8 | 11380.5 | +86.79% | EXACT MATCH |
| `848343_noise_005` | perturbation_noise | 103.65 | 76.60 | -26.09% | 1655.3 | 1530.6 | -7.53% | CONVERGED (Within Tolerance) |
| `alligator_quant_010` | quantization | 5.22 | 5.13 | -1.65% | 52.0 | 21.0 | -59.57% | EXACT MATCH |
| `alligator_smooth_taubin` | smoothing | 6.21 | 6.50 | +4.59% | 61.8 | 41.0 | -33.74% | EXACT MATCH |
| `alligator_soup_jitter` | triangle_soup | 7.03 | 7.02 | -0.22% | 102.8 | 61.6 | -40.05% | CONVERGED (Within Tolerance) |
