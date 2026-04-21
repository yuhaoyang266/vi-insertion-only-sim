from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.three_dof_benchmark import (
    DEFAULT_UNCERTAINTY_PROFILES,
    run_3dof_bc_seed_factorization_suite,
)
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run BC-only init-seed/demo-seed factorization for the 3DoF pipeline."
    )
    parser.add_argument("--init-seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--demo-seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--eval-seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument(
        "--max-episode-steps",
        type=int,
        default=DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    )
    parser.add_argument(
        "--profiles",
        type=str,
        nargs="+",
        default=list(DEFAULT_UNCERTAINTY_PROFILES),
    )
    parser.add_argument("--bc-rollout-episodes", type=int, default=8)
    parser.add_argument("--bc-pretrain-steps", type=int, default=32)
    parser.add_argument("--bc-batch-size", type=int, default=64)
    parser.add_argument("--bc-demo-policy-name", type=str, default="variable_impedance")
    parser.add_argument(
        "--coverage-condition",
        type=str,
        choices=["reset_repaired", "reset_coverage_collapse"],
        default="reset_repaired",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional explicit output path for the JSON report.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_3dof_bc_seed_factorization_suite(
        init_seeds=args.init_seeds,
        demo_seeds=args.demo_seeds,
        eval_seeds=args.eval_seeds,
        episodes_per_eval_seed=args.episodes,
        max_episode_steps=args.max_episode_steps,
        uncertainty_profiles=args.profiles,
        coverage_condition=args.coverage_condition,
        bc_rollout_episodes=args.bc_rollout_episodes,
        bc_pretrain_steps=args.bc_pretrain_steps,
        bc_batch_size=args.bc_batch_size,
        bc_demo_policy_name=args.bc_demo_policy_name,
    )

    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = (
            Path("outputs")
            / f"three_dof_bc_seed_factorization_{args.coverage_condition}_{timestamp}.json"
        )
    else:
        output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("bc_seed_factorization_report", output_path)
    print("coverage_condition", report["config"]["coverage_condition"])
    print("training_budget", report["config"]["training_budget"])
    for condition_name, payload in report["results"].items():
        print(condition_name, payload["factor_values"], payload["demo_audit"]["num_rows"])


if __name__ == "__main__":
    main()
