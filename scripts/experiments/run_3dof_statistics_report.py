from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys


def _load_paper_tables_module():
    module_path = Path(__file__).resolve().parents[2] / "src" / "vi_full" / "paper_tables.py"
    spec = importlib.util.spec_from_file_location("paper_tables_statistics_cli", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load paper table module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute paper-facing statistical summaries for the 3DoF benchmark."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the main paper-facing 3DoF benchmark JSON artifact.",
    )
    parser.add_argument(
        "--fixed-impedance-input",
        type=Path,
        default=None,
        help="Optional stable fixed-impedance supplement artifact.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/paper_only_sim_tables"),
        help="Directory for the exported statistics report.",
    )
    parser.add_argument(
        "--stem",
        type=str,
        default="three_dof_statistics_report",
        help="Output filename stem for the statistics report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    module = _load_paper_tables_module()
    json_path, markdown_path = module.export_3dof_statistics_report(
        benchmark_report_path=args.input,
        fixed_impedance_report_path=args.fixed_impedance_input,
        output_dir=args.output_dir,
        stem=args.stem,
    )
    print(json_path)
    print(markdown_path)


if __name__ == "__main__":
    main()
