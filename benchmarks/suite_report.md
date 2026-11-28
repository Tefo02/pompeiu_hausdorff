# Mass Benchmark Report: `best_first` vs `idastar`

- **Date:** 2026-11-27 11:31:46
- **Pairs evaluated:** 20 (`OK`: 19, `Non-OK`: 1)
- **Parity passed:** 19/19
- **Tolerance override:** per-manifest
- **Mean Peak RSS Delta:** -35.82%
- **Mean Wall-Time Delta:** -17.44%

| Pair ID | Category | Base RSS (MB) | Cand RSS (MB) | RSS Delta | Base Time (ms) | Cand Time (ms) | Time Delta | Parity |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| `107100_decimate_50` | decimation | 13.50 | 7.06 | -47.73% | 328.8 | 61.5 | -81.28% | CONVERGED (Within Tolerance) |
| `existing_848343_decimate` | high_density_decimation | 359.50 | 64.25 | -82.13% | 10398.7 | 13435.3 | +29.20% | EXACT MATCH |
| `107100_noise_005` | perturbation_noise | 14.20 | 7.98 | -43.78% | 248.2 | 91.8 | -63.01% | CONVERGED (Within Tolerance) |
| `107100_quant_010` | quantization | 12.25 | 7.72 | -36.97% | 112.5 | 81.8 | -27.32% | EXACT MATCH |
| `existing_107100_sf` | remeshing | 126.59 | 29.26 | -76.89% | 2685.0 | 6901.5 | +157.04% | EXACT MATCH |
| `synthetic_cube_translation` | sanity_analytical | 6.18 | 4.79 | -22.39% | 20.9 | 31.1 | +48.44% | EXACT MATCH |
| `107100_smooth_taubin` | smoothing | 14.51 | 8.02 | -44.70% | 902.9 | 71.6 | -92.07% | CONVERGED (Within Tolerance) |
| `existing_lucy_decimate05` | stress_memory | 405.39 | 681.57 | - | 20118.4 | 20243.6 | - | TIMEOUT/TIMEOUT |
| `107100_soup_jitter` | triangle_soup | 14.48 | 8.45 | -41.65% | 235.0 | 122.2 | -47.99% | EXACT MATCH |
| `107100_decimate_20` | decimation | 6.64 | 6.67 | +0.41% | 93.0 | 51.4 | -44.72% | CONVERGED (Within Tolerance) |
| `107100_noise_020` | perturbation_noise | 14.28 | 8.06 | -43.57% | 164.3 | 112.9 | -31.29% | CONVERGED (Within Tolerance) |
| `848343_quant_010` | quantization | 60.78 | 60.71 | -0.10% | 1057.8 | 890.6 | -15.81% | EXACT MATCH |
| `synthetic_icosphere_refinement` | sanity_analytical | 3.99 | 0.78 | -80.51% | 42.1 | 10.9 | -74.10% | EXACT MATCH |
| `848343_smooth_taubin` | smoothing | 143.06 | 88.19 | -38.36% | 3198.2 | 4010.2 | +25.39% | EXACT MATCH |
| `848343_soup_jitter` | triangle_soup | 130.18 | 104.07 | -20.06% | 2963.1 | 2322.2 | -21.63% | CONVERGED (Within Tolerance) |
| `848343_decimate_50` | decimation | 269.51 | 64.25 | -76.16% | 6796.4 | 13466.1 | +98.14% | EXACT MATCH |
| `848343_noise_005` | perturbation_noise | 105.69 | 76.59 | -27.53% | 1959.6 | 1841.2 | -6.04% | CONVERGED (Within Tolerance) |
| `alligator_quant_010` | quantization | 5.13 | 5.21 | +1.45% | 186.1 | 31.2 | -83.25% | CONVERGED (Within Tolerance) |
| `alligator_smooth_taubin` | smoothing | 6.53 | 6.50 | -0.48% | 82.7 | 51.5 | -37.70% | EXACT MATCH |
| `alligator_soup_jitter` | triangle_soup | 6.94 | 6.98 | +0.62% | 195.4 | 71.7 | -63.30% | CONVERGED (Within Tolerance) |
