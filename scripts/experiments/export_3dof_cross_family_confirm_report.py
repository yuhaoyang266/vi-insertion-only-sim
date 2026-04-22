from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.three_dof_cross_family_confirm_report import export_confirm_report_artifacts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export paper-facing 3DoF cross-family confirm report artifacts."
    )
    parser.add_argument(
        "--pilot-report",
        type=Path,
        default=Path("outputs/pilot_report/three_dof_cross_family_pilot_report.json"),
        help="Merged Sprint 1 pilot report JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/cross_family_confirm"),
        help="Directory for confirm JSON, CSV, Markdown, and figure artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    artifacts = export_confirm_report_artifacts(
        pilot_report=args.pilot_report,
        output_dir=args.output_dir,
    )
    print(artifacts["json"])
    print(artifacts["csv"])
    print(artifacts["markdown"])
    png_path, pdf_path = artifacts["distance_vs_budget"]
    print(png_path)
    print(pdf_path)
    learning_png_path, learning_pdf_path = artifacts["learning_curve_summary"]
    print(learning_png_path)
    print(learning_pdf_path)


if __name__ == "__main__":
    main()
