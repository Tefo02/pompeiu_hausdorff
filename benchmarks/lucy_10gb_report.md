# Mass Benchmark Report: `best_first` vs `idastar_fixed` vs `idastar_bisection`

- **Date:** 2026-11-28 10:41:48
- **Pairs evaluated:** 1
- **Memory Limit (RLIMIT_AS):** 10240 MB
- **Per-run Timeout:** 300s

## Aggregate Summary per Engine

| Engine | OK | OOM | Timeout | Error | Mean RSS (MB) | Mean Time (ms) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `best_first` | 0 | 1 | 0 | 0 | 0.00 | 0.0 |
| `idastar_fixed` | 1 | 0 | 0 | 0 | 4982.99 | 165425.0 |
| `idastar_bisection` | 1 | 0 | 0 | 0 | 4983.05 | 159777.4 |

## Per-Pair Results

| Pair ID | Category | `best_first` RSS (MB) | `best_first` Time (ms) | `best_first` Status | `idastar_fixed` RSS (MB) | `idastar_fixed` Time (ms) | `idastar_fixed` Status | `idastar_bisection` RSS (MB) | `idastar_bisection` Time (ms) | `idastar_bisection` Status |
| :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | ---: | ---: | :--- |
| `existing_lucy_decimate05` | stress_memory | 5303.86 | 149724.2 | OOM | 4982.99 | 165425.0 | OK (No Base) | 4983.05 | 159777.4 | OK (No Base) |
