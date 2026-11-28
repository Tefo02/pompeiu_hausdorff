#!/usr/bin/env python3
"""
run_suite.py - Automated Batch Benchmark Runner for Pompeiu-Hausdorff Test Suites

Reads a JSON manifest (default: benchmarks/test_suite.json), executes baseline
and candidate search engines in isolated subprocesses with a per-run timeout,
tracks Peak RSS, wall/CPU time, subdivided faces, bound calls, and numerical
parity, and exports consolidated CSV and Markdown summary reports.
"""

import argparse
import csv
import datetime
import fnmatch
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from compare_engines import (  # noqa: E402
    calculate_percentage_change,
    compute_comparison_metrics,
)
from profile_runner import parse_binary_stdout, ProcStatusSampler  # noqa: E402
import subprocess  # noqa: E402


ENGINE_CHOICES = [
    "best_first",
    "idastar",
    "idastar_nocache",
    "idastar_fixed",
    "idastar_next_best",
    "idastar_bisection",
    "idastar_hybrid",
]


def run_timed_profile(
    executable: str,
    mesh_a: str,
    mesh_b: str,
    tol: str,
    max_factor: str,
    normalize: str,
    engine: str,
    timeout_sec: float,
    sample_interval_sec: float = 0.010,
) -> Dict[str, Any]:
    """
    Runs a single engine invocation in an isolated subprocess with Peak RSS sampling
    and an explicit wall-clock timeout.
    """
    cmd = [executable, mesh_a, mesh_b, tol, max_factor, normalize, engine]
    start_wall = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
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
            "cpu_time_ms": wall_time_ms,
            "error": f"Exceeded {timeout_sec}s timeout",
        }

    # Note: main.cpp returns 1 on success, 0 on error
    if proc.returncode != 1:
        return {
            "status": "ERROR",
            "engine": engine,
            "peak_rss_mb": peak_rss_mb,
            "wall_time_ms": wall_time_ms,
            "cpu_time_ms": wall_time_ms,
            "error": (stderr_text or stdout_text).strip()[:200],
        }

    parsed = parse_binary_stdout(stdout_text)
    if "lower" not in parsed or "upper_max" not in parsed:
        return {
            "status": "ERROR",
            "engine": engine,
            "peak_rss_mb": peak_rss_mb,
            "wall_time_ms": wall_time_ms,
            "cpu_time_ms": wall_time_ms,
            "error": "Failed to parse lower/upper_max from stdout",
        }

    return {
        "status": "OK",
        "engine": engine,
        "peak_rss_mb": peak_rss_mb,
        "wall_time_ms": wall_time_ms,
        "cpu_time_ms": wall_time_ms,
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


def select_pairs(
    pairs: List[Dict[str, Any]],
    filter_pattern: Optional[str],
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
    if categories:
        cat_set = {c.lower() for c in categories}
        selected = [p for p in selected if p.get("category", "").lower() in cat_set]

    if max_pairs > 0 and len(selected) > max_pairs:
        if stratified:
            # Round-robin across categories to preserve diversity
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
    rows: List[Dict[str, Any]],
    baseline_engine: str,
    candidate_engine: str,
    tol_override: Optional[str],
) -> None:
    """
    Writes a consolidated Markdown table summarizing all benchmarked pairs.
    """
    os.makedirs(os.path.dirname(os.path.abspath(md_path)), exist_ok=True)
    ok_rows = [r for r in rows if r["status"] == "OK"]
    avg_mem_pct = (
        sum(r["mem_delta_pct"] for r in ok_rows) / len(ok_rows)
        if ok_rows else 0.0
    )
    avg_wall_pct = (
        sum(r["wall_delta_pct"] for r in ok_rows) / len(ok_rows)
        if ok_rows else 0.0
    )
    parity_ok = sum(
        1 for r in ok_rows
        if r["parity"] in ("EXACT MATCH", "CONVERGED (Within Tolerance)")
    )

    lines = [
        f"# Mass Benchmark Report: `{baseline_engine}` vs `{candidate_engine}`",
        "",
        f"- **Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Pairs evaluated:** {len(rows)} (`OK`: {len(ok_rows)}, `Non-OK`: {len(rows) - len(ok_rows)})",
        f"- **Parity passed:** {parity_ok}/{len(ok_rows)}",
        f"- **Tolerance override:** {tol_override or 'per-manifest'}",
        f"- **Mean Peak RSS Delta:** {avg_mem_pct:+.2f}%",
        f"- **Mean Wall-Time Delta:** {avg_wall_pct:+.2f}%",
        "",
        "| Pair ID | Category | Base RSS (MB) | Cand RSS (MB) | RSS Delta | Base Time (ms) | Cand Time (ms) | Time Delta | Parity |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |",
    ]
    for r in rows:
        if r["status"] == "OK":
            lines.append(
                f"| `{r['id']}` | {r['category']} | {r['base_rss_mb']:.2f} | {r['cand_rss_mb']:.2f} | "
                f"{r['mem_delta_pct']:+.2f}% | {r['base_wall_ms']:.1f} | {r['cand_wall_ms']:.1f} | "
                f"{r['wall_delta_pct']:+.2f}% | {r['parity']} |"
            )
        else:
            lines.append(
                f"| `{r['id']}` | {r['category']} | {r['base_rss_mb']:.2f} | {r['cand_rss_mb']:.2f} | "
                f"- | {r['base_wall_ms']:.1f} | {r['cand_wall_ms']:.1f} | - | {r['status']} |"
            )

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
    parser.add_argument("--executable", default=default_exe, help="Path to pompeiu_hausdorff binary")
    parser.add_argument("--manifest", default=default_manifest, help="Path to test_suite.json")
    parser.add_argument("--baseline-engine", default="best_first", choices=ENGINE_CHOICES)
    parser.add_argument("--candidate-engine", default="idastar", choices=ENGINE_CHOICES)
    parser.add_argument("--tol", default=None, help="Override tolerance for all pairs (e.g., 1e-4)")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-run timeout in seconds (default: 30.0)")
    parser.add_argument("--filter", default=None, help="Glob filter on pair id (e.g., '*107100*')")
    parser.add_argument("--categories", nargs="*", default=None, help="Filter by category names")
    parser.add_argument("--max-pairs", type=int, default=0, help="Max pairs to run (0 = all)")
    parser.add_argument("--stratified", action="store_true", help="Sample round-robin across categories when --max-pairs > 0")
    parser.add_argument("--output-csv", default=default_csv, help="Output CSV path")
    parser.add_argument("--output-md", default=default_md, help="Output Markdown summary path")

    args = parser.parse_args()

    if not os.path.isfile(args.executable):
        sys.exit(f"Error: Executable not found at {args.executable}")
    if not os.path.isfile(args.manifest):
        sys.exit(f"Error: Manifest not found at {args.manifest}")

    with open(args.manifest, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    pairs = select_pairs(
        manifest.get("pairs", []),
        filter_pattern=args.filter,
        categories=args.categories,
        max_pairs=args.max_pairs,
        stratified=args.stratified,
    )
    if not pairs:
        sys.exit("Error: No pairs matched the selection criteria.")

    print("=" * 80)
    print(f"BATCH BENCHMARK SUITE: {args.baseline_engine} vs {args.candidate_engine}")
    print(f"Selected pairs: {len(pairs)} | Per-run timeout: {args.timeout}s")
    print("=" * 80)

    rows: List[Dict[str, Any]] = []
    for idx, pair in enumerate(pairs, start=1):
        mesh_a = os.path.join(PROJECT_DIR, pair["mesh_a"])
        mesh_b = os.path.join(PROJECT_DIR, pair["mesh_b"])
        tol = args.tol if args.tol is not None else str(pair.get("tol", "1e-4"))
        max_factor = str(pair.get("max_factor", "1000000"))
        normalize = str(pair.get("normalize", "1"))

        if not (os.path.isfile(mesh_a) and os.path.isfile(mesh_b)):
            print(f"[{idx}/{len(pairs)}] [SKIP] Missing mesh file for {pair['id']}")
            continue

        print(f"[{idx}/{len(pairs)}] Running {pair['id']} ({pair.get('category', '')}, tol={tol})...")
        base_res = run_timed_profile(
            args.executable, mesh_a, mesh_b, tol, max_factor, normalize,
            args.baseline_engine, args.timeout,
        )
        cand_res = run_timed_profile(
            args.executable, mesh_a, mesh_b, tol, max_factor, normalize,
            args.candidate_engine, args.timeout,
        )

        if base_res["status"] == "OK" and cand_res["status"] == "OK":
            cmp = compute_comparison_metrics(base_res, cand_res, tol=tol, normalize=normalize)
            row = {
                "id": pair["id"],
                "category": pair.get("category", ""),
                "tol": tol,
                "status": "OK",
                "base_rss_mb": base_res["peak_rss_mb"],
                "cand_rss_mb": cand_res["peak_rss_mb"],
                "mem_delta_pct": cmp["mem_pct"],
                "base_wall_ms": base_res["wall_time_ms"],
                "cand_wall_ms": cand_res["wall_time_ms"],
                "wall_delta_pct": cmp["wall_pct"],
                "base_faces": base_res["subdivided_faces"],
                "cand_faces": cand_res["subdivided_faces"],
                "base_lower": base_res["lower"],
                "base_upper": base_res["upper_max"],
                "cand_lower": cand_res["lower"],
                "cand_upper": cand_res["upper_max"],
                "parity": cmp["parity_summary"],
            }
            print(
                f"    RSS: {row['base_rss_mb']:.2f} -> {row['cand_rss_mb']:.2f} MB ({row['mem_delta_pct']:+.2f}%) | "
                f"Time: {row['base_wall_ms']:.1f} -> {row['cand_wall_ms']:.1f} ms ({row['wall_delta_pct']:+.2f}%) | "
                f"{row['parity']}"
            )
        else:
            status_label = f"{base_res['status']}/{cand_res['status']}"
            row = {
                "id": pair["id"],
                "category": pair.get("category", ""),
                "tol": tol,
                "status": status_label,
                "base_rss_mb": base_res["peak_rss_mb"],
                "cand_rss_mb": cand_res["peak_rss_mb"],
                "mem_delta_pct": 0.0,
                "base_wall_ms": base_res["wall_time_ms"],
                "cand_wall_ms": cand_res["wall_time_ms"],
                "wall_delta_pct": 0.0,
                "base_faces": 0,
                "cand_faces": 0,
                "base_lower": float("nan"),
                "base_upper": float("nan"),
                "cand_lower": float("nan"),
                "cand_upper": float("nan"),
                "parity": status_label,
            }
            print(f"    [WARN] Status={status_label}")

        rows.append(row)

    os.makedirs(os.path.dirname(os.path.abspath(args.output_csv)), exist_ok=True)
    if rows:
        fieldnames = list(rows[0].keys())
        with open(args.output_csv, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    write_markdown_summary(
        args.output_md, rows, args.baseline_engine, args.candidate_engine, args.tol
    )

    print("\n" + "=" * 80)
    print(f"[OK] CSV saved to:      {args.output_csv}")
    print(f"[OK] Markdown saved to: {args.output_md}")
    print("=" * 80)


if __name__ == "__main__":
    main()
