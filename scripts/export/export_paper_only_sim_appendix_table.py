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
    spec = importlib.util.spec_from_file_location("paper_tables_appendix_cli", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load paper table module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export appendix tables for teacher ablation and termination diagnostics."
    )
    parser.add_argument(
        "--benchmark-input",
        type=Path,
        required=True,
        help="Path to a Phase C+ uncertainty benchmark JSON that includes diagnostics fields.",
    )
    parser.add_argument(
        "--fixed-impedance-input",
        type=Path,
        default=None,
        help="Optional stable fixed-impedance override JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/paper_only_sim_appendix"),
        help="Directory for the exported appendix table files.",
    )
    parser.add_argument(
        "--stem",
        type=str,
        default="table_3dof_appendix_stage4",
        help="Canonical output filename stem.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    module = _load_paper_tables_module()
    json_path, markdown_path = module.export_3dof_appendix_table(
        benchmark_report_path=args.benchmark_input,
        fixed_impedance_report_path=args.fixed_impedance_input,
        output_dir=args.output_dir,
        stem=args.stem,
    )
    print(json_path)
    print(markdown_path)


if __name__ == "__main__":
    main()
