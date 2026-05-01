from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.offline_demo_dataset import (
    build_offline_demo_dataset,
    write_offline_demo_dataset_artifact,
)
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_profiles import DEFAULT_UNCERTAINTY_PROFILES


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a contract-shaped 3DoF offline demonstration dataset."
    )
    parser.add_argument("--profiles", type=str, nargs="+", default=list(DEFAULT_UNCERTAINTY_PROFILES))
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--episodes-per-seed", type=int, default=2)
    parser.add_argument("--source-policy", type=str, default="variable_impedance")
    parser.add_argument(
        "--max-episode-steps",
        type=int,
        default=DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    )
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def _default_output_path() -> Path:
    date_stamp = datetime.now().strftime("%Y%m%d")
    return (
        Path("artifacts")
        / "main_benchmark"
        / f"three_dof_offline_demo_dataset_{date_stamp}.json"
    )


def main() -> None:
    args = _parse_args()
    output_path = args.output if args.output is not None else _default_output_path()
    command = "python " + " ".join(sys.argv)
    dataset = build_offline_demo_dataset(
        profiles=list(args.profiles),
        seeds=[int(seed) for seed in args.seeds],
        episodes_per_seed=int(args.episodes_per_seed),
        source_policy=str(args.source_policy),
        max_episode_steps=int(args.max_episode_steps),
        paper_a_commit=_git_commit(),
        generation_command=command,
    )
    paths = write_offline_demo_dataset_artifact(output_path, dataset)
    print(f"offline_demo_dataset_json {paths['json']}", flush=True)
    print(
        f"offline_demo_dataset_payload_sha256 {dataset['metadata']['dataset_payload_sha256']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
