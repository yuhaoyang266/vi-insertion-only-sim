from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.three_dof_benchmark import DEFAULT_UNCERTAINTY_PROFILES
from vi_full.three_dof_motion_matched_main_protocol import (
    DEFAULT_MAIN_PROTOCOL_EPISODES_PER_SEED,
    DEFAULT_MAIN_PROTOCOL_SEEDS,
    DEFAULT_MAIN_PROTOCOL_TOTAL_TIMESTEPS,
    export_motion_matched_table,
    run_motion_matched_main_protocol,
    write_motion_matched_main_report,
)

from run_3dof_uncertainty_benchmark import _run_3dof_suite_across_profiles


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the main-contract 3DoF motion-matched teacher decoupling protocol."
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_MAIN_PROTOCOL_SEEDS))
    parser.add_argument(
        "--episodes-per-seed",
        type=int,
        default=DEFAULT_MAIN_PROTOCOL_EPISODES_PER_SEED,
    )
    parser.add_argument(
        "--profiles",
        type=str,
        nargs="+",
        default=list(DEFAULT_UNCERTAINTY_PROFILES),
    )
    parser.add_argument(
        "--total-timesteps",
        type=int,
        default=DEFAULT_MAIN_PROTOCOL_TOTAL_TIMESTEPS,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON artifact path.",
    )
    parser.add_argument(
        "--table-stem",
        type=Path,
        default=None,
        help="Output stem for the Markdown and CSV summary table.",
    )
    return parser.parse_args()


def _default_output_path() -> Path:
    date_stamp = datetime.now().strftime("%Y%m%d")
    return (
        Path("artifacts")
        / "main_benchmark"
        / f"three_dof_motion_matched_main_{date_stamp}.json"
    )


def _default_table_stem(output_path: Path) -> Path:
    stem = output_path.stem.replace(
        "three_dof_motion_matched_main",
        "table_3dof_motion_matched",
    )
    return output_path.with_name(stem)


def _generating_command(args: argparse.Namespace, output_path: Path) -> str:
    command_parts = [
        "python",
        "scripts/experiments/run_3dof_motion_matched_main_protocol.py",
        "--seeds",
        *[str(seed) for seed in args.seeds],
        "--episodes-per-seed",
        str(args.episodes_per_seed),
        "--profiles",
        *list(args.profiles),
        "--total-timesteps",
        str(args.total_timesteps),
        "--output",
        output_path.as_posix(),
    ]
    return " ".join(command_parts)


def main() -> None:
    args = parse_args()
    output_path = args.output if args.output is not None else _default_output_path()
    table_stem = args.table_stem if args.table_stem is not None else _default_table_stem(output_path)
    report = run_motion_matched_main_protocol(
        suite_runner=_run_3dof_suite_across_profiles,
        seeds=args.seeds,
        episodes_per_seed=args.episodes_per_seed,
        profiles=args.profiles,
        total_timesteps=args.total_timesteps,
        generating_command=_generating_command(args, output_path),
        source_artifacts={
            "protocol_runner": "scripts/experiments/run_3dof_motion_matched_main_protocol.py",
        },
        repo_root=REPO_ROOT,
    )
    json_path = write_motion_matched_main_report(output_path, report)
    table_paths = export_motion_matched_table(report, output_stem=table_stem)
    print(f"motion_matched_main_report {json_path}", flush=True)
    print(f"motion_matched_main_table_csv {table_paths['csv']}", flush=True)
    print(f"motion_matched_main_table_md {table_paths['markdown']}", flush=True)


if __name__ == "__main__":
    main()
