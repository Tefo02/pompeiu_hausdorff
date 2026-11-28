#!/usr/bin/env python3
"""
run_suite.py - Automated Batch Benchmark Runner for Pompeiu-Hausdorff Test Suites

Reads a JSON manifest (default: benchmarks/test_suite.json), executes one or more
search engines in isolated subprocesses with optional RAM limits (RLIMIT_AS) and
per-run timeouts, tracks Peak RSS, wall time, subdivided faces, and numerical
parity against the first (baseline) engine, and exports CSV and Markdown reports.
"""

import argparse
import csv
import datetime
import fnmatch
import json
import os
import resource
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from profile_runner import ProcStatusSampler, parse_binary_stdout  # noqa: E402


ENGINE_CHOICES = [
    "best_first",
    "idastar",
    "idastar_nocache",
    "idastar_fixed",
    "idastar_next_best",
    "idastar_bisection",
    "idastar_hybrid",
]


def _make_rlimit_preexec(memory_limit_mb: float):
    if memory_limit_mb <= 0.0:
        return None
    limit_bytes = int(memory_limit_mb * 1024 * 1024)

    def _apply_limit() -> None:
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))

    return _apply_limit


def run_timed_profile(
    executable: str,
    mesh_a: str,
    mesh_b: str,
    tol: str,
    max_factor: str,
    normalize: str,
    engine: str,
    timeout_sec: float,
    memory_limit_mb: float = 0.0,
    sample_interval_sec: float = 0.010,
) -> Dict[str, Any]:
    """
    Runs a single engine invocation in an isolated subprocess with Peak RSS sampling,
    optional RLIMIT_AS memory cap, and explicit wall-clock timeout.
    """
    cmd = [executable, mesh_a, mesh_b, tol, max_factor, normalize, engine]
    start_wall = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=_make_rlimit_preexec(memory_limit_mb),
    )

    sampler = ProcStatusSampler(proc.pid, sample_interval_sec=sample_interval_sec)
    sampler.start()

    timed_out = False
    stdout_text = ""
    stderr_text = ""
    try:
        stdout_text, stderr_text = proc.communicate(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        stdout_text, stderr_text = proc.communicate()
    finally:
        sampler.stop()
        sampler.join(timeout=1.0)

    wall_time_ms = (time.perf_counter() - start_wall) * 1000.0
    peak_rss_mb = max(sampler.peak_vmhwm_kb, sampler.peak_vmrss_kb) / 1024.0

    if timed_out:
        return {
            "status": "TIMEOUT",
            "engine": engine,
            "peak_rss_mb": peak_rss_mb,
            "wall_time_ms": wall_time_ms,
            "error": f"Exceeded {timeout_sec}s timeout",
        }

    combined_err = f"{stderr_text}\n{stdout_text}"
    if proc.returncode != 1:
        is_oom = (
            memory_limit_mb > 0.0
            and (
                "bad_alloc" in combined_err
                or "Cannot allocate memory" in combined_err
                or proc.returncode < 0
                or peak_rss_mb >= memory_limit_mb * 0.70
            )
        )
        return {
            "status": "OOM" if is_oom else "ERROR",
            "engine": engine,
            "peak_rss_mb": peak_rss_mb,
            "wall_time_ms": wall_time_ms,
            "error": combined_err.strip()[:200],
        }

    parsed = parse_binary_stdout(stdout_text)
    if "lower" not in parsed or "upper_max" not in parsed:
        return {
            "status": "ERROR",
            "engine": engine,
            "peak_rss_mb": peak_rss_mb,
            "wall_time_ms": wall_time_ms,
            "error": "Failed to parse lower/upper_max from stdout",
        }

    return {
        "status": "OK",
        "engine": engine,
        "peak_rss_mb": peak_rss_mb,
        "wall_time_ms": wall_time_ms,
        "dA": parsed.get("dA", float("nan")),
        "lower": parsed.get("lower", float("nan")),
        "upper_max": parsed.get("upper_max", float("nan")),
        "bvh_time_ms": parsed.get("bvh_time_ms", float("nan")),
        "bound_time_ms": parsed.get("bound_time_ms", float("nan")),
        "subdivided_faces": int(parsed.get("subdivided_faces", 0)),
        "u0_calls": int(parsed.get("u0_calls", 0)),
        "u1_calls": int(parsed.get("u1_calls", 0)),
        "u2_calls": int(parsed.get("u2_calls", 0)),
        "u3_calls": int(parsed.get("u3_calls", 0)),
        "u4_calls": int(parsed.get("u4_calls", 0)),
    }


def check_parity(
    base_res: Dict[str, Any],
    cand_res: Dict[str, Any],
    tol: str,
    normalize: str,
) -> str:
    """
    Validates numerical convergence parity between baseline and candidate intervals.
    """
    if cand_res["status"] != "OK":
        return cand_res["status"]
    if base_res["status"] != "OK":
        return "OK (No Base)"

    tol_float = float(tol)
    dA = cand_res.get("dA", 1.0)
    tol_scaled = tol_float * dA if int(normalize) else tol_float

    lower_diff = abs(base_res["lower"] - cand_res["lower"])
    upper_diff = abs(base_res["upper_max"] - cand_res["upper_max"])
    if lower_diff < 1e-8 and upper_diff < 1e-8:
        return "EXACT MATCH"

    cand_gap = cand_res["upper_max"] - cand_res["lower"]
    intervals_overlap = not (
        base_res["upper_max"] < cand_res["lower"]
        or cand_res["upper_max"] < base_res["lower"]
    )
    if cand_gap <= tol_scaled * 1.0001 and intervals_overlap:
        return "CONVERGED"
    return "DIVERGENCE"


def select_pairs(
    pairs: List[Dict[str, Any]],
    filter_pattern: Optional[str],
    exclude_filter: Optional[str],
    categories: Optional[List[str]],
    max_pairs: int,
    stratified: bool,
) -> List[Dict[str, Any]]:
    """
    Filters and optionally selects a stratified subset of pairs from the manifest.
    """
    selected = pairs
    if filter_pattern:
        selected = [
            p for p in selected
            if fnmatch.fnmatch(p["id"].lower(), filter_pattern.lower())
        ]
    if exclude_filter:
        selected = [
            p for p in selected
            if not fnmatch.fnmatch(p["id"].lower(), exclude_filter.lower())
        ]
    if categories:
        cat_set = {c.lower() for c in categories}
        selected = [p for p in selected if p.get("category", "").lower() in cat_set]

    if max_pairs > 0 and len(selected) > max_pairs:
        if stratified:
            by_cat: Dict[str, List[Dict[str, Any]]] = {}
            for p in selected:
                by_cat.setdefault(p.get("category", "other"), []).append(p)
            result: List[Dict[str, Any]] = []
            keys = sorted(by_cat.keys())
            idx = 0
            while len(result) < max_pairs:
                added = False
                for k in keys:
                    if idx < len(by_cat[k]) and len(result) < max_pairs:
                        result.append(by_cat[k][idx])
                        added = True
                if not added:
                    break
                idx += 1
            selected = result
        else:
            selected = selected[:max_pairs]

    return selected


def write_markdown_summary(
    md_path: str,
    pair_records: List[Dict[str, Any]],
    engines: List[str],
    memory_limit_mb: float,
    timeout_sec: float,
) -> None:
    """
    Writes a consolidated Markdown table summarizing all engines side by side.
    """
    os.makedirs(os.path.dirname(os.path.abspath(md_path)), exist_ok=True)
    mem_str = f"{memory_limit_mb:.0f} MB" if memory_limit_mb > 0 else "Unlimited"

    lines = [
        f"# Mass Benchmark Report: {' vs '.join(f'`{e}`' for e in engines)}",
        "",
        f"- **Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Pairs evaluated:** {len(pair_records)}",
        f"- **Memory Limit (RLIMIT_AS):** {mem_str}",
        f"- **Per-run Timeout:** {timeout_sec:.0f}s",
        "",
        "## Aggregate Summary per Engine",
        "",
        "| Engine | OK | OOM | Timeout | Error | Mean RSS (MB) | Mean Time (ms) |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for eng in engines:
        eng_rows = [rec["results"][eng] for rec in pair_records]
        ok = [r for r in eng_rows if r["status"] == "OK"]
        oom = sum(1 for r in eng_rows if r["status"] == "OOM")
        to = sum(1 for r in eng_rows if r["status"] == "TIMEOUT")
        err = sum(1 for r in eng_rows if r["status"] == "ERROR")
        mean_rss = (sum(r["peak_rss_mb"] for r in ok) / len(ok)) if ok else 0.0
        mean_time = (sum(r["wall_time_ms"] for r in ok) / len(ok)) if ok else 0.0
        lines.append(
            f"| `{eng}` | {len(ok)} | {oom} | {to} | {err} | {mean_rss:.2f} | {mean_time:.1f} |"
        )

    lines.append("")
    lines.append("## Per-Pair Results")
    lines.append("")

    header = "| Pair ID | Category |"
    sep = "| :--- | :--- |"
    for eng in engines:
        header += f" `{eng}` RSS (MB) | `{eng}` Time (ms) | `{eng}` Status |"
        sep += " ---: | ---: | :--- |"
    lines.append(header)
    lines.append(sep)

    for rec in pair_records:
        row_str = f"| `{rec['id']}` | {rec['category']} |"
        for eng in engines:
            res = rec["results"][eng]
            status_disp = res.get("parity", res["status"]) if res["status"] == "OK" else res["status"]
            row_str += f" {res['peak_rss_mb']:.2f} | {res['wall_time_ms']:.1f} | {status_disp} |"
        lines.append(row_str)

    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> None:
    default_exe = os.path.join(PROJECT_DIR, "build", "pompeiu_hausdorff")
    default_manifest = os.path.join(SCRIPT_DIR, "test_suite.json")
    default_csv = os.path.join(SCRIPT_DIR, "suite_results.csv")
    default_md = os.path.join(SCRIPT_DIR, "suite_report.md")

    parser = argparse.ArgumentParser(
        description="Run batch comparative benchmarks over test_suite.json."
    )
    parser.add_argument("--executable", default=default_exe)
    parser.add_argument("--manifest", default=default_manifest)
    parser.add_argument("--engines", nargs="+", default=None, choices=ENGINE_CHOICES)
    parser.add_argument("--baseline-engine", default="best_first", choices=ENGINE_CHOICES)
    parser.add_argument("--candidate-engine", default="idastar", choices=ENGINE_CHOICES)
    parser.add_argument("--tol", default=None)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--memory-limit-mb", type=float, default=0.0, help="RLIMIT_AS cap in MB (0 = unlimited)")
    parser.add_argument("--filter", default=None, help="Glob filter on pair id")
    parser.add_argument("--exclude-filter", default=None, help="Glob exclude filter on pair id")
    parser.add_argument("--categories", nargs="*", default=None)
    parser.add_argument("--max-pairs", type=int, default=0)
    parser.add_argument("--stratified", action="store_true")
    parser.add_argument("--output-csv", default=default_csv)
    parser.add_argument("--output-md", default=default_md)

    args = parser.parse_args()
    engines = args.engines if args.engines else [args.baseline_engine, args.candidate_engine]

    if not os.path.isfile(args.executable):
        sys.exit(f"Error: Executable not found at {args.executable}")
    if not os.path.isfile(args.manifest):
        sys.exit(f"Error: Manifest not found at {args.manifest}")

    with open(args.manifest, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    pairs = select_pairs(
        manifest.get("pairs", []),
        filter_pattern=args.filter,
        exclude_filter=args.exclude_filter,
        categories=args.categories,
        max_pairs=args.max_pairs,
        stratified=args.stratified,
    )
    if not pairs:
        sys.exit("Error: No pairs matched the selection criteria.")

    mem_label = f"{args.memory_limit_mb:.0f} MB" if args.memory_limit_mb > 0 else "Unlimited"
    print("=" * 84)
    print(f"BATCH BENCHMARK SUITE: {' vs '.join(engines)}")
    print(f"Selected pairs: {len(pairs)} | Memory limit: {mem_label} | Timeout: {args.timeout}s")
    print("=" * 84)

    csv_rows: List[Dict[str, Any]] = []
    pair_records: List[Dict[str, Any]] = []

    for idx, pair in enumerate(pairs, start=1):
        mesh_a = os.path.join(PROJECT_DIR, pair["mesh_a"])
        mesh_b = os.path.join(PROJECT_DIR, pair["mesh_b"])
        tol = args.tol if args.tol is not None else str(pair.get("tol", "1e-4"))
        max_factor = str(pair.get("max_factor", "1000000"))
        normalize = str(pair.get("normalize", "1"))

        if not (os.path.isfile(mesh_a) and os.path.isfile(mesh_b)):
            print(f"[{idx}/{len(pairs)}] [SKIP] Missing mesh file for {pair['id']}")
            continue

        print(f"[{idx}/{len(pairs)}] {pair['id']} ({pair.get('category', '')}, tol={tol})")
        results_by_eng: Dict[str, Dict[str, Any]] = {}
        base_eng = engines[0]

        for eng in engines:
            res = run_timed_profile(
                args.executable,
                mesh_a,
                mesh_b,
                tol,
                max_factor,
                normalize,
                eng,
                args.timeout,
                memory_limit_mb=args.memory_limit_mb,
            )
            if eng != base_eng and res["status"] == "OK":
                res["parity"] = check_parity(results_by_eng[base_eng], res, tol, normalize)
            elif res["status"] == "OK":
                res["parity"] = "OK"

            results_by_eng[eng] = res
            status_tag = res.get("parity", res["status"]) if res["status"] == "OK" else res["status"]
            print(
                f"    {eng:<18} | RSS={res['peak_rss_mb']:>7.2f} MB | "
                f"Time={res['wall_time_ms']:>8.1f} ms | {status_tag}"
            )

            csv_rows.append(
                {
                    "id": pair["id"],
                    "category": pair.get("category", ""),
                    "tol": tol,
                    "memory_limit_mb": args.memory_limit_mb,
                    "engine": eng,
                    "status": res["status"],
                    "parity": status_tag,
                    "peak_rss_mb": f"{res['peak_rss_mb']:.2f}",
                    "wall_time_ms": f"{res['wall_time_ms']:.2f}",
                    "subdivided_faces": res.get("subdivided_faces", 0),
                    "lower": res.get("lower", ""),
                    "upper_max": res.get("upper_max", ""),
                }
            )

        pair_records.append(
            {
                "id": pair["id"],
                "category": pair.get("category", ""),
                "results": results_by_eng,
            }
        )

    os.makedirs(os.path.dirname(os.path.abspath(args.output_csv)), exist_ok=True)
    if csv_rows:
        with open(args.output_csv, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(csv_rows)

    write_markdown_summary(
        args.output_md, pair_records, engines, args.memory_limit_mb, args.timeout
    )

    print("\n" + "=" * 84)
    print(f"[OK] CSV saved to:      {args.output_csv}")
    print(f"[OK] Markdown saved to: {args.output_md}")
    print("=" * 84)


if __name__ == "__main__":
    main()
