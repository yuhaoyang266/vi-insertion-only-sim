from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.three_dof_support_metric_sensitivity import (
    build_support_metric_sensitivity_report,
    write_support_metric_sensitivity_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export 3DoF SCI sensitivity audit artifacts.")
    parser.add_argument(
        "--input-artifacts",
        type=Path,
        nargs="+",
        default=[Path("outputs/evidence_matrix/three_dof_evidence_matrix.json")],
    )
    parser.add_argument(
        "--output-stem",
        type=Path,
        default=Path("outputs/revision/sci_sensitivity_20260425"),
    )
    parser.add_argument("--smoke-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifacts = []
    for path in args.input_artifacts:
        artifacts.append(json.loads(path.read_text(encoding="utf-8")))
    if args.smoke_only:
        artifacts = artifacts[:1]
    report = build_support_metric_sensitivity_report(artifacts)
    paths = write_support_metric_sensitivity_outputs(report, args.output_stem)
    print("sci_sensitivity_report", paths["json_path"])


if __name__ == "__main__":
    main()
