from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.three_dof_impedance_mechanics import (
    build_success_matched_mechanics_report,
    export_force_work_pareto_csv,
    render_success_matched_mechanics_figure,
    write_success_matched_mechanics_report,
)


DEFAULT_TRACE_INPUT = Path(
    "artifacts/mechanics/latest_three_dof_high_friction_direct_mechanics_trace.json"
)
DEFAULT_OUTPUT_STEM = Path("outputs/revision/three_dof_impedance_mechanics_20260429")
DEFAULT_FIGURE_OUTPUT_DIR = Path("figures/main")
DEFAULT_APPENDIX_OUTPUT_DIR = Path("figures/appendix")
DEFAULT_FIGURE_STEM = "fig3_high_friction_impedance_mechanism"
LEGACY_STEM = "fig3_legacy_all_trace_high_friction_impedance_mechanism"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export success-matched 3DoF high-friction impedance mechanics."
    )
    parser.add_argument("--trace-input", type=Path, default=DEFAULT_TRACE_INPUT)
    parser.add_argument("--output-stem", type=Path, default=DEFAULT_OUTPUT_STEM)
    parser.add_argument("--figure-output-dir", type=Path, default=DEFAULT_FIGURE_OUTPUT_DIR)
    parser.add_argument("--figure-stem", type=str, default=DEFAULT_FIGURE_STEM)
    parser.add_argument("--appendix-output-dir", type=Path, default=DEFAULT_APPENDIX_OUTPUT_DIR)
    parser.add_argument("--num-points", type=int, default=120)
    return parser.parse_args()


def _repo_relative(path: Path) -> str:
    return Path(path).as_posix()


def _generating_command(args: argparse.Namespace) -> str:
    return " ".join(
        [
            "python",
            "scripts/experiments/export_3dof_impedance_mechanics.py",
            "--trace-input",
            _repo_relative(args.trace_input),
            "--output-stem",
            _repo_relative(args.output_stem),
            "--figure-output-dir",
            _repo_relative(args.figure_output_dir),
            "--figure-stem",
            args.figure_stem,
            "--appendix-output-dir",
            _repo_relative(args.appendix_output_dir),
            "--num-points",
            str(args.num_points),
        ]
    )


def _archive_legacy_main_figure(args: argparse.Namespace) -> list[Path]:
    archived: list[Path] = []
    args.appendix_output_dir.mkdir(parents=True, exist_ok=True)
    for suffix in (".pdf", ".png"):
        source = args.figure_output_dir / f"{args.figure_stem}{suffix}"
        destination = args.appendix_output_dir / f"{LEGACY_STEM}{suffix}"
        if source.exists() and not destination.exists():
            shutil.copy2(source, destination)
            archived.append(destination)
    return archived


def main() -> None:
    args = parse_args()
    trace_payload = json.loads(args.trace_input.read_text(encoding="utf-8"))
    report = build_success_matched_mechanics_report(
        trace_payload,
        source_trace_path=_repo_relative(args.trace_input),
        generating_command=_generating_command(args),
        repo_root=REPO_ROOT,
        num_points=args.num_points,
    )
    json_path = write_success_matched_mechanics_report(
        args.output_stem.with_suffix(".json"),
        report,
    )
    csv_path = export_force_work_pareto_csv(args.output_stem.with_suffix(".csv"), report)
    archived_paths = _archive_legacy_main_figure(args)
    pdf_path, png_path = render_success_matched_mechanics_figure(
        report,
        output_dir=args.figure_output_dir,
        stem=args.figure_stem,
    )
    print(f"mechanics_json {json_path}", flush=True)
    print(f"mechanics_csv {csv_path}", flush=True)
    print(f"figure_pdf {pdf_path}", flush=True)
    print(f"figure_png {png_path}", flush=True)
    for path in archived_paths:
        print(f"legacy_figure {path}", flush=True)


if __name__ == "__main__":
    main()
