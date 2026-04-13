from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys


def _load_paper_figures_module():
    repo_root = Path(__file__).resolve().parents[1]
    src_root = repo_root / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    module_path = src_root / "vi_full" / "paper_figures.py"
    spec = importlib.util.spec_from_file_location("paper_figures_cli", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load paper figure module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export only-sim Figure A1 assets.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/paper_only_sim_figures"),
        help="Directory for the exported figure files.",
    )
    parser.add_argument(
        "--stem",
        type=str,
        default="figA1_evaluation_class_mapping",
        help="Canonical output filename stem.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    module = _load_paper_figures_module()
    pdf_path, png_path = module.export_figurea1_pressure_class_mapping(
        output_dir=args.output_dir,
        stem=args.stem,
    )
    print(pdf_path)
    print(png_path)


if __name__ == "__main__":
    main()
