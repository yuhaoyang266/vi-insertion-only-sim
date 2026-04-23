from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.sprint4_clearance_shift import (
    export_sprint4_clearance_shift_artifacts,
    run_sprint4_clearance_shift_sweep,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run and export the Sprint 4A clearance-shift sweep.",
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--max-episode-steps", type=int, default=64)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/sprint4_clearance_shift"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_sprint4_clearance_shift_sweep(
        train_seeds=list(args.seeds),
        episodes_per_seed=int(args.episodes),
        max_episode_steps=int(args.max_episode_steps),
    )
    artifacts = export_sprint4_clearance_shift_artifacts(report, args.output_dir)
    print("sprint4_clearance_shift")
    print("json_path", artifacts["json_path"])
    print("csv_path", artifacts["csv_path"])
    print("markdown_path", artifacts["markdown_path"])


if __name__ == "__main__":
    main()
