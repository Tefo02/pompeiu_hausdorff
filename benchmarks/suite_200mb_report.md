# Mass Benchmark Report: `best_first` vs `idastar_fixed` vs `idastar_bisection`

- **Date:** 2026-11-28 10:33:41
- **Pairs evaluated:** 40
- **Memory Limit (RLIMIT_AS):** 200 MB
- **Per-run Timeout:** 20s

## Aggregate Summary per Engine

| Engine | OK | OOM | Timeout | Error | Mean RSS (MB) | Mean Time (ms) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `best_first` | 28 | 9 | 0 | 3 | 21.51 | 402.3 |
| `idastar_fixed` | 37 | 0 | 0 | 3 | 27.61 | 1854.7 |
| `idastar_bisection` | 37 | 0 | 0 | 3 | 27.61 | 1545.7 |

## Per-Pair Results

| Pair ID | Category | `best_first` RSS (MB) | `best_first` Time (ms) | `best_first` Status | `idastar_fixed` RSS (MB) | `idastar_fixed` Time (ms) | `idastar_fixed` Status | `idastar_bisection` RSS (MB) | `idastar_bisection` Time (ms) | `idastar_bisection` Status |
| :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | ---: | ---: | :--- |
| `107100_decimate_50` | decimation | 6.96 | 63.6 | OK | 6.96 | 63.3 | CONVERGED | 7.19 | 73.1 | CONVERGED |
| `existing_848343_decimate` | high_density_decimation | 62.43 | 1615.2 | OOM | 64.25 | 17876.4 | OK (No Base) | 64.25 | 14751.4 | OK (No Base) |
| `107100_noise_005` | perturbation_noise | 14.29 | 104.0 | OK | 8.03 | 103.8 | CONVERGED | 7.92 | 93.2 | CONVERGED |
| `107100_quant_010` | quantization | 13.86 | 93.5 | OK | 7.74 | 93.4 | EXACT MATCH | 7.61 | 83.2 | EXACT MATCH |
| `existing_107100_sf` | remeshing | 114.21 | 2032.8 | OOM | 29.26 | 8345.9 | OK (No Base) | 29.25 | 5608.6 | OK (No Base) |
| `synthetic_cube_translation` | sanity_analytical | 6.17 | 22.4 | OK | 4.79 | 43.3 | EXACT MATCH | 4.80 | 32.6 | EXACT MATCH |
| `107100_smooth_taubin` | smoothing | 14.31 | 73.0 | OK | 8.35 | 83.0 | CONVERGED | 8.36 | 83.3 | CONVERGED |
| `107100_soup_jitter` | triangle_soup | 14.48 | 113.3 | OK | 8.63 | 123.8 | EXACT MATCH | 8.70 | 123.9 | EXACT MATCH |
| `107100_decimate_20` | decimation | 6.62 | 52.8 | OK | 6.63 | 53.4 | CONVERGED | 6.57 | 53.0 | CONVERGED |
| `107100_noise_020` | perturbation_noise | 14.32 | 123.8 | OK | 8.02 | 113.7 | CONVERGED | 8.03 | 113.4 | CONVERGED |
| `848343_quant_010` | quantization | 60.69 | 913.0 | OOM | 60.70 | 933.3 | OK (No Base) | 60.70 | 913.6 | OK (No Base) |
| `synthetic_icosphere_refinement` | sanity_analytical | 1.67 | 12.7 | OK | 1.75 | 12.9 | EXACT MATCH | 1.65 | 12.6 | EXACT MATCH |
| `848343_smooth_taubin` | smoothing | 88.85 | 1631.8 | OOM | 88.18 | 5752.3 | OK (No Base) | 88.19 | 3595.6 | OK (No Base) |
| `848343_soup_jitter` | triangle_soup | 112.84 | 2463.0 | OOM | 104.07 | 2392.9 | OK (No Base) | 104.05 | 2258.4 | OK (No Base) |
| `848343_decimate_50` | decimation | 62.85 | 1379.2 | OOM | 64.25 | 14047.6 | OK (No Base) | 64.20 | 11816.8 | OK (No Base) |
| `848343_noise_005` | perturbation_noise | 84.78 | 1604.3 | OOM | 76.60 | 1949.0 | OK (No Base) | 76.60 | 1859.4 | OK (No Base) |
| `alligator_quant_010` | quantization | 5.26 | 32.9 | OK | 5.25 | 32.8 | CONVERGED | 5.26 | 32.8 | EXACT MATCH |
| `alligator_smooth_taubin` | smoothing | 6.51 | 52.8 | OK | 6.54 | 53.2 | EXACT MATCH | 6.54 | 53.0 | EXACT MATCH |
| `alligator_soup_jitter` | triangle_soup | 6.96 | 73.4 | OK | 6.97 | 73.1 | CONVERGED | 6.97 | 73.5 | CONVERGED |
| `848343_decimate_20` | decimation | 60.70 | 1402.9 | OOM | 60.92 | 4039.2 | OK (No Base) | 60.70 | 3269.3 | OK (No Base) |
| `848343_noise_020` | perturbation_noise | 84.73 | 2785.8 | OOM | 76.62 | 4617.4 | OK (No Base) | 76.61 | 4634.9 | OK (No Base) |
| `armadillo_quant_010` | quantization | 29.25 | 1001.3 | OK | 19.65 | 337.1 | EXACT MATCH | 19.68 | 358.1 | EXACT MATCH |
| `armadillo_smooth_taubin` | smoothing | 68.12 | 1397.6 | OK | 49.66 | 1374.4 | EXACT MATCH | 49.71 | 1383.3 | EXACT MATCH |
| `armadillo_soup_jitter` | triangle_soup | 58.75 | 2232.7 | OK | 45.91 | 925.3 | CONVERGED | 45.87 | 944.0 | CONVERGED |
| `alligator_decimate_50` | decimation | 24.13 | 276.0 | OK | 18.57 | 285.7 | EXACT MATCH | 18.51 | 297.0 | EXACT MATCH |
| `alligator_noise_005` | perturbation_noise | 6.54 | 125.4 | OK | 5.81 | 54.6 | EXACT MATCH | 6.30 | 42.8 | EXACT MATCH |
| `beast_quant_010` | quantization | 12.17 | 433.5 | ERROR | 12.06 | 124.1 | ERROR | 12.06 | 123.5 | ERROR |
| `beast_smooth_taubin` | smoothing | 12.15 | 123.8 | ERROR | 12.25 | 134.0 | ERROR | 12.92 | 134.0 | ERROR |
| `beast_soup_jitter` | triangle_soup | 12.10 | 123.6 | ERROR | 12.04 | 134.9 | ERROR | 12.11 | 123.7 | ERROR |
| `alligator_decimate_20` | decimation | 11.16 | 113.9 | OK | 9.42 | 113.6 | EXACT MATCH | 9.36 | 103.2 | EXACT MATCH |
| `alligator_noise_020` | perturbation_noise | 6.29 | 114.6 | OK | 6.29 | 73.1 | EXACT MATCH | 6.27 | 73.1 | EXACT MATCH |
| `beetle-alt_quant_010` | quantization | 21.79 | 339.9 | OK | 10.31 | 153.9 | CONVERGED | 10.47 | 154.2 | EXACT MATCH |
| `beetle-alt_smooth_taubin` | smoothing | 29.87 | 318.0 | OK | 16.39 | 245.2 | EXACT MATCH | 16.43 | 235.6 | EXACT MATCH |
| `beetle-alt_soup_jitter` | triangle_soup | 35.54 | 789.4 | OK | 20.66 | 377.1 | CONVERGED | 20.64 | 356.7 | CONVERGED |
| `armadillo_decimate_50` | decimation | 81.65 | 1782.4 | OK | 39.76 | 2589.4 | EXACT MATCH | 39.76 | 2416.3 | EXACT MATCH |
| `armadillo_noise_005` | perturbation_noise | 53.01 | 1100.1 | OK | 34.64 | 601.9 | CONVERGED | 34.64 | 611.9 | CONVERGED |
| `beetle_quant_010` | quantization | 5.52 | 53.7 | OK | 5.48 | 32.5 | EXACT MATCH | 5.46 | 32.4 | EXACT MATCH |
| `beetle_smooth_taubin` | smoothing | 5.06 | 32.7 | OK | 4.91 | 22.6 | CONVERGED | 4.91 | 22.3 | CONVERGED |
| `beetle_soup_jitter` | triangle_soup | 5.66 | 63.3 | OK | 5.79 | 42.7 | EXACT MATCH | 5.71 | 42.9 | EXACT MATCH |
| `armadillo_decimate_20` | decimation | 48.45 | 703.9 | OK | 23.75 | 590.7 | CONVERGED | 23.82 | 579.9 | CONVERGED |
