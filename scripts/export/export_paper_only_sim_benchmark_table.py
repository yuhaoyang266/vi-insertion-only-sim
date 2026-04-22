from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys


def _load_paper_tables_module():
    repo_root = Path(__file__).resolve().parents[2]
    src_root = repo_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    module_path = src_root / "vi_full" / "paper_tables.py"
    spec = importlib.util.spec_from_file_location("paper_tables_cli", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load paper table module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export the paper-facing 3DoF benchmark table.")
    parser.add_argument(
        "--benchmark-input",
        type=Path,
        default=Path(
            "artifacts/main_benchmark/three_dof_benchmark_schema2_paper_teacher_20260418_034230.json"
        ),
        help="Path to the main 9-suite 3DoF benchmark JSON.",
    )
    parser.add_argument(
        "--fixed-impedance-input",
        type=Path,
        default=None,
        help="Optional stable fixed-impedance supplement JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/paper_only_sim_tables"),
        help="Directory for the exported table files.",
    )
    parser.add_argument(
        "--statistics-report-input",
        type=Path,
        default=None,
        help="Optional paper-facing statistics report JSON for CI and comparison notes.",
    )
    parser.add_argument(
        "--stem",
        type=str,
        default="table_3dof_paper_benchmark_schema2_20260418",
        help="Canonical output filename stem.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    module = _load_paper_tables_module()
    json_path, markdown_path = module.export_3dof_paper_table(
        benchmark_report_path=args.benchmark_input,
        fixed_impedance_report_path=args.fixed_impedance_input,
        statistics_report_path=args.statistics_report_input,
        output_dir=args.output_dir,
        stem=args.stem,
    )
    print(json_path)
    print(markdown_path)


if __name__ == "__main__":
    main()
