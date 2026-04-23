from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def _load_kickoff_module():
    module_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "vi_full"
        / "sprint3_teacher_mini_ablation_kickoff.py"
    )
    spec = importlib.util.spec_from_file_location(
        "sprint3_teacher_mini_ablation_kickoff_cli",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Sprint 3 kickoff module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the Sprint 3 teacher mini-ablation kickoff artifacts."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/sprint3_teacher_mini_ablation"),
        help="Directory for exported Sprint 3 kickoff artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    module = _load_kickoff_module()
    artifacts = module.export_sprint3_teacher_mini_ablation_kickoff_artifacts(
        args.output_dir
    )
    print("sprint3_teacher_mini_ablation_kickoff")
    print(artifacts["json_path"])
    print(artifacts["csv_path"])
    print(artifacts["markdown_path"])
    print(artifacts["pdf_path"])
    print(artifacts["png_path"])


if __name__ == "__main__":
    main()
