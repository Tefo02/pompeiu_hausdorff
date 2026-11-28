# Mass Benchmark Report: `best_first` vs `idastar_fixed`

- **Date:** 2026-11-28 10:14:28
- **Pairs evaluated:** 20 (`OK`: 19, `Non-OK`: 1)
- **Parity passed:** 19/19
- **Tolerance override:** per-manifest
- **Mean Peak RSS Delta:** -29.71%
- **Mean Wall-Time Delta:** +40.16%

| Pair ID | Category | Base RSS (MB) | Cand RSS (MB) | RSS Delta | Base Time (ms) | Cand Time (ms) | Time Delta | Parity |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| `107100_decimate_50` | decimation | 6.92 | 6.96 | +0.51% | 61.8 | 61.5 | -0.53% | CONVERGED (Within Tolerance) |
| `existing_848343_decimate` | high_density_decimation | 362.50 | 64.25 | -82.27% | 7768.2 | 17012.8 | +119.01% | EXACT MATCH |
| `107100_noise_005` | perturbation_noise | 14.23 | 8.03 | -43.59% | 91.7 | 101.9 | +11.18% | CONVERGED (Within Tolerance) |
| `107100_quant_010` | quantization | 13.76 | 7.79 | -43.43% | 81.8 | 91.9 | +12.36% | EXACT MATCH |
| `existing_107100_sf` | remeshing | 132.30 | 29.27 | -77.88% | 2497.2 | 8064.1 | +222.92% | EXACT MATCH |
| `synthetic_cube_translation` | sanity_analytical | 6.18 | 4.85 | -21.60% | 21.2 | 41.0 | +93.50% | EXACT MATCH |
| `107100_smooth_taubin` | smoothing | 14.35 | 8.27 | -42.39% | 71.8 | 81.9 | +14.10% | CONVERGED (Within Tolerance) |
| `existing_lucy_decimate05` | stress_memory | 836.76 | 933.77 | - | 20025.9 | 20034.2 | - | TIMEOUT/TIMEOUT |
| `107100_soup_jitter` | triangle_soup | 14.49 | 8.69 | -40.03% | 112.2 | 122.3 | +9.02% | EXACT MATCH |
| `107100_decimate_20` | decimation | 6.67 | 6.39 | -4.10% | 51.4 | 51.3 | -0.18% | CONVERGED (Within Tolerance) |
| `107100_noise_020` | perturbation_noise | 14.29 | 8.03 | -43.82% | 112.4 | 112.9 | +0.47% | CONVERGED (Within Tolerance) |
| `848343_quant_010` | quantization | 66.90 | 60.80 | -9.12% | 910.8 | 891.3 | -2.15% | EXACT MATCH |
| `synthetic_icosphere_refinement` | sanity_analytical | 0.71 | 0.72 | +1.66% | 10.8 | 10.8 | -0.33% | EXACT MATCH |
| `848343_smooth_taubin` | smoothing | 143.27 | 88.18 | -38.45% | 2686.5 | 5048.9 | +87.93% | EXACT MATCH |
| `848343_soup_jitter` | triangle_soup | 131.86 | 104.07 | -21.07% | 2215.9 | 2205.8 | -0.45% | CONVERGED (Within Tolerance) |
| `848343_decimate_50` | decimation | 269.38 | 64.25 | -76.15% | 5945.5 | 13756.5 | +131.38% | EXACT MATCH |
| `848343_noise_005` | perturbation_noise | 105.67 | 76.60 | -27.51% | 1654.5 | 1938.6 | +17.17% | CONVERGED (Within Tolerance) |
| `alligator_quant_010` | quantization | 4.89 | 4.93 | +0.88% | 21.0 | 31.0 | +47.28% | CONVERGED (Within Tolerance) |
| `alligator_smooth_taubin` | smoothing | 6.07 | 6.29 | +3.73% | 41.0 | 41.5 | +1.03% | EXACT MATCH |
| `alligator_soup_jitter` | triangle_soup | 7.03 | 7.04 | +0.06% | 61.7 | 61.3 | -0.63% | CONVERGED (Within Tolerance) |
