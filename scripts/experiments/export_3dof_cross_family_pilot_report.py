from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.three_dof_cross_family_pilot_report import (
    export_3dof_cross_family_pilot_internal_figures,
    export_3dof_cross_family_pilot_report,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export merged JSON and internal figures for the 3DoF cross-family pilot."
    )
    parser.add_argument(
        "--chunk-dir",
        type=Path,
        default=Path("outputs/pilot_chunks"),
        help="Directory containing per-method per-budget pilot chunk JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/pilot_report"),
        help="Directory for the merged pilot report JSON and figures.",
    )
    parser.add_argument(
        "--stem",
        type=str,
        default="three_dof_cross_family_pilot_report",
        help="Output filename stem for the merged JSON report.",
    )
    parser.add_argument(
        "--figure-stem-prefix",
        type=str,
        default="three_dof_cross_family_pilot",
        help="Filename stem prefix for the exported internal figures.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    json_path = export_3dof_cross_family_pilot_report(
        chunk_dir=args.chunk_dir,
        output_dir=args.output_dir,
        stem=args.stem,
    )
    figure_paths = export_3dof_cross_family_pilot_internal_figures(
        chunk_dir=args.chunk_dir,
        output_dir=args.output_dir,
        stem_prefix=args.figure_stem_prefix,
    )
    print(json_path)
    for pdf_path, png_path in figure_paths.values():
        print(pdf_path)
        print(png_path)


if __name__ == "__main__":
    main()
