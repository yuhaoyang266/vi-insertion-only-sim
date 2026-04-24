from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys


def _load_evidence_matrix_module():
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "vi_full"
        / "three_dof_evidence_matrix.py"
    )
    spec = importlib.util.spec_from_file_location(
        "three_dof_evidence_matrix_cli",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load evidence-matrix module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the reviewer-facing 3DoF evidence matrix artifacts."
    )
    parser.add_argument(
        "--confirm-report",
        type=Path,
        required=True,
        help="Path to the Branch-A cross-family confirm report JSON.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("artifacts/main_benchmark/main_benchmark_manifest.json"),
        help="Canonical benchmark manifest used for demo-supported and mechanics-anchor rows.",
    )
    parser.add_argument(
        "--benchmark-report",
        type=Path,
        default=None,
        help="Optional benchmark JSON override. Defaults to --manifest canonical_main_benchmark.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/evidence_matrix"),
        help="Directory for exported evidence-matrix artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    module = _load_evidence_matrix_module()
    artifacts = module.export_3dof_evidence_matrix_artifacts(
        confirm_report_path=args.confirm_report,
        benchmark_report_path=args.benchmark_report,
        manifest_path=None if args.benchmark_report is not None else args.manifest,
        output_dir=args.output_dir,
    )
    print(artifacts["json"])
    print(artifacts["csv"])
    print(artifacts["markdown"])
    png_path, pdf_path = artifacts["contact_gate_matrix"]
    print(png_path)
    print(pdf_path)
    sprint2_main_table = artifacts["sprint2_main_table"]
    print(sprint2_main_table["json"])
    print(sprint2_main_table["csv"])
    print(sprint2_main_table["markdown"])


if __name__ == "__main__":
    main()
