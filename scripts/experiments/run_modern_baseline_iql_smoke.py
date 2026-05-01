from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.modern_baseline_smoke import (
    run_modern_baseline_smoke,
    write_modern_baseline_smoke_artifacts,
)
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_profiles import DEFAULT_UNCERTAINTY_PROFILES


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the modern IQL/CQL baseline smoke scaffold."
    )
    parser.add_argument("--num-steps", type=int, default=8)
    parser.add_argument("--dataset-path", type=Path, default=None)
    parser.add_argument("--evaluate-bc-stub", action="store_true")
    parser.add_argument("--eval-profiles", type=str, nargs="+", default=list(DEFAULT_UNCERTAINTY_PROFILES))
    parser.add_argument("--eval-seeds", type=int, nargs="+", default=[0])
    parser.add_argument("--eval-episodes-per-seed", type=int, default=1)
    parser.add_argument(
        "--max-episode-steps",
        type=int,
        default=DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    )
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def _default_output_path() -> Path:
    date_stamp = datetime.now().strftime("%Y%m%d")
    return Path("outputs") / "revision" / f"modern_baseline_iql_smoke_{date_stamp}.json"


def main() -> None:
    args = _parse_args()
    report = run_modern_baseline_smoke(
        num_steps=int(args.num_steps),
        dataset_path=args.dataset_path,
        evaluate_bc_stub=bool(args.evaluate_bc_stub),
        eval_profiles=list(args.eval_profiles),
        eval_seeds=[int(seed) for seed in args.eval_seeds],
        eval_episodes_per_seed=int(args.eval_episodes_per_seed),
        max_episode_steps=int(args.max_episode_steps),
    )
    output_path = args.output if args.output is not None else _default_output_path()
    paths = write_modern_baseline_smoke_artifacts(output_path, report)
    print(f"modern_baseline_smoke_json {paths['json']}", flush=True)
    print(f"modern_baseline_smoke_md {paths['markdown']}", flush=True)


if __name__ == "__main__":
    main()
