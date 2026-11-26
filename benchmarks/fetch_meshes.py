#!/usr/bin/env python3
"""
fetch_meshes.py - Automated Mesh Downloader from Alec Jacobson's Test Model Repository

Downloads standard Wavefront .obj triangle meshes from the official
`alecjacobson/common-3d-test-models` repository into `meshes/`, providing
curated presets for academic benchmarking of Pompeiu-Hausdorff engines.

Uses only the Python standard library (zero external dependencies).
"""

import argparse
import os
import sys
import urllib.error
import urllib.request
from typing import Dict, List, Sequence, Tuple


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DEFAULT_MESHES_DIR = os.path.join(PROJECT_DIR, "meshes")

RAW_BASE_URL = (
    "https://raw.githubusercontent.com/alecjacobson/common-3d-test-models/master/data"
)

# Verified catalog from alecjacobson/common-3d-test-models/data
AVAILABLE_MODELS: Dict[str, Tuple[str, str]] = {
    "alligator.obj": ("organic_small", "~0.2 MB"),
    "armadillo.obj": ("organic_medium", "~4.4 MB"),
    "beast.obj": ("organic_medium", "~3.2 MB"),
    "beetle-alt.obj": ("cad_medium", "~1.3 MB"),
    "beetle.obj": ("cad_small", "~0.1 MB"),
    "bimba.obj": ("organic_large", "~7.6 MB"),
    "cheburashka.obj": ("organic_small", "~0.4 MB"),
    "cow.obj": ("organic_small", "~0.2 MB"),
    "fandisk.obj": ("cad_sharp_features", "~0.4 MB"),
    "happy.obj": ("organic_medium", "~4.4 MB"),
    "homer.obj": ("organic_small", "~0.4 MB"),
    "horse.obj": ("organic_medium", "~4.6 MB"),
    "igea.obj": ("organic_large", "~9.1 MB"),
    "lucy.obj": ("organic_medium", "~4.4 MB"),
    "max-planck.obj": ("organic_medium", "~4.4 MB"),
    "nefertiti.obj": ("organic_medium", "~3.5 MB"),
    "ogre.obj": ("organic_medium", "~3.6 MB"),
    "rocker-arm.obj": ("cad_sharp_features", "~0.6 MB"),
    "spot.obj": ("organic_small", "~0.3 MB"),
    "stanford-bunny.obj": ("organic_medium", "~2.3 MB"),
    "suzanne.obj": ("organic_small", "~0.05 MB"),
    "teapot.obj": ("cad_small", "~0.2 MB"),
    "woody.obj": ("organic_small", "~0.04 MB"),
    "xyzrgb_dragon.obj": ("organic_large", "~11.3 MB"),
}

PRESETS: Dict[str, List[str]] = {
    "recommended": [
        "fandisk.obj",
        "rocker-arm.obj",
        "spot.obj",
        "stanford-bunny.obj",
        "armadillo.obj",
        "xyzrgb_dragon.obj",
    ],
    "light": [
        "suzanne.obj",
        "teapot.obj",
        "spot.obj",
        "fandisk.obj",
        "cow.obj",
    ],
    "all": sorted(AVAILABLE_MODELS.keys()),
}


def normalize_model_name(name: str) -> str:
    """
    Ensures a requested model identifier ends with .obj.
    """
    cleaned = name.strip()
    if not cleaned.lower().endswith(".obj"):
        cleaned = f"{cleaned}.obj"
    return cleaned


def resolve_target_models(
    preset: str,
    explicit_models: Sequence[str],
) -> List[str]:
    """
    Resolves the final deduplicated list of .obj filenames to download.
    """
    if explicit_models:
        resolved: List[str] = []
        for raw_name in explicit_models:
            model_name = normalize_model_name(raw_name)
            if model_name not in AVAILABLE_MODELS:
                valid = ", ".join(sorted(AVAILABLE_MODELS.keys()))
                raise ValueError(
                    f"Unknown model '{raw_name}'. Available models: {valid}"
                )
            if model_name not in resolved:
                resolved.append(model_name)
        return resolved

    return list(PRESETS[preset])


def download_model(
    model_name: str,
    output_dir: str,
    overwrite: bool = False,
    timeout_sec: int = 60,
) -> str:
    """
    Downloads a single .obj file from raw.githubusercontent.com into output_dir.

    Returns one of: 'downloaded', 'skipped', or 'failed'.
    """
    target_path = os.path.join(output_dir, model_name)
    if os.path.exists(target_path) and not overwrite:
        print(f"[skip] {model_name} already exists in {output_dir}")
        return "skipped"

    url = f"{RAW_BASE_URL}/{model_name}"
    tmp_path = f"{target_path}.part"
    print(f"[fetch] {model_name} <- {url}")

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "pompeiu-hausdorff-fetch-meshes/1.0"},
        )
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            with open(tmp_path, "wb") as out_handle:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    out_handle.write(chunk)

        os.replace(tmp_path, target_path)
        size_mb = os.path.getsize(target_path) / (1024.0 * 1024.0)
        print(f"[ok]   Saved {model_name} ({size_mb:.2f} MB)")
        return "downloaded"
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        print(f"[err]  Failed to download {model_name}: {exc}", file=sys.stderr)
        return "failed"


def print_catalog() -> None:
    """
    Prints all available models in the remote catalog with categories and sizes.
    """
    print("Available models in alecjacobson/common-3d-test-models:")
    print(f"{'Filename':<22} {'Category':<20} {'Approx. Size'}")
    print("-" * 58)
    for name in sorted(AVAILABLE_MODELS.keys()):
        category, size_str = AVAILABLE_MODELS[name]
        print(f"{name:<22} {category:<20} {size_str}")
    print("\nPresets:")
    for preset_name, items in PRESETS.items():
        print(f"  - {preset_name}: {', '.join(items)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download standard .obj test meshes from alecjacobson/common-3d-test-models."
    )
    parser.add_argument(
        "--preset",
        choices=sorted(PRESETS.keys()),
        default="recommended",
        help="Curated set of models to download if --models is not given (default: recommended)",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=[],
        help="Explicit model names to download (e.g., stanford-bunny fandisk armadillo)",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_MESHES_DIR,
        help=f"Destination directory (default: {DEFAULT_MESHES_DIR})",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files in --output-dir",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available models and presets without downloading",
    )

    args = parser.parse_args()

    if args.list:
        print_catalog()
        return

    try:
        target_models = resolve_target_models(args.preset, args.models)
    except ValueError as exc:
        sys.exit(f"Error: {exc}")

    os.makedirs(args.output_dir, exist_ok=True)

    counts = {"downloaded": 0, "skipped": 0, "failed": 0}
    for model_name in target_models:
        status = download_model(
            model_name=model_name,
            output_dir=args.output_dir,
            overwrite=args.overwrite,
        )
        counts[status] += 1

    print("\n" + "=" * 60)
    print(
        f"Summary: downloaded={counts['downloaded']}, "
        f"skipped={counts['skipped']}, failed={counts['failed']}"
    )
    print(
        "Next step: run 'python3 benchmarks/generate_test_suite.py' "
        "to generate variants and update benchmarks/test_suite.json."
    )
    print("=" * 60)

    if counts["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
