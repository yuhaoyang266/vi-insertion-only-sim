from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from vi_full.three_dof_benchmark import (
    DEFAULT_UNCERTAINTY_PROFILES,
    build_3dof_algorithm_budget_comparison_registry,
    build_3dof_factor_sweep_registry,
    run_3dof_algorithm_budget_comparison,
    run_3dof_factor_sweep_suite,
)


def parse_args() -> argparse.Namespace:
    registry = build_3dof_factor_sweep_registry()
    parser = argparse.ArgumentParser(
        description="Run phase-2 causal factor sweeps for the 3DoF only-sim paper."
    )
    parser.add_argument(
        "--sweeps",
        type=str,
        nargs="+",
        default=list(registry),
        choices=list(registry),
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--max-episode-steps", type=int, default=64)
    parser.add_argument(
        "--profiles",
        type=str,
        nargs="+",
        default=list(DEFAULT_UNCERTAINTY_PROFILES),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory where one JSON artifact per sweep family will be written.",
    )
    algorithm_registry = build_3dof_algorithm_budget_comparison_registry()
    parser.add_argument(
        "--include-algorithm-budget-comparison",
        action="store_true",
    )
    parser.add_argument(
        "--algorithm-budget-points",
        type=int,
        nargs="+",
        default=algorithm_registry["budget_points"],
    )
    return parser.parse_args()


def _build_default_output_path(output_dir: Path, sweep_name: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"three_dof_factor_sweep_{sweep_name}_{timestamp}.json"


def _build_algorithm_budget_output_path(output_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"three_dof_algorithm_budget_comparison_{timestamp}.json"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for sweep_name in args.sweeps:
        report = run_3dof_factor_sweep_suite(
            sweep_name=sweep_name,
            train_seeds=args.seeds,
            episodes_per_seed=args.episodes,
            max_episode_steps=args.max_episode_steps,
            uncertainty_profiles=args.profiles,
        )
        output_path = _build_default_output_path(args.output_dir, sweep_name)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        print("factor_sweep_report", sweep_name, output_path)
        print("manipulated_factor", report["manipulated_factor"])
        print("fixed_controls", report["fixed_controls"])
        for point in report["points"]:
            nominal_metrics = point["per_profile_metrics"].get("nominal")
            nominal_success = None
            if nominal_metrics is not None:
                nominal_success = nominal_metrics["aggregate"]["success_rate_mean"]
            print(
                "point",
                point["point_name"],
                "factor_value",
                point["factor_value"],
                "nominal_success_rate_mean",
                nominal_success,
            )

    if args.include_algorithm_budget_comparison:
        comparison = run_3dof_algorithm_budget_comparison(
            train_seeds=args.seeds,
            episodes_per_seed=args.episodes,
            max_episode_steps=args.max_episode_steps,
            uncertainty_profiles=args.profiles,
            budget_points=args.algorithm_budget_points,
        )
        output_path = _build_algorithm_budget_output_path(args.output_dir)
        output_path.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
        print("algorithm_budget_comparison_report", output_path)
        for suite in comparison["budgeted_suites"]:
            nominal_curve = [
                point["per_profile_metrics"]["nominal"]["aggregate"]["success_rate_mean"]
                for point in suite["points"]
                if "nominal" in point["per_profile_metrics"]
            ]
            print("suite", suite["suite_name"], "nominal_curve", nominal_curve)
        for anchor in comparison["static_anchors"]:
            nominal_metrics = anchor["per_profile_metrics"].get("nominal")
            nominal_success = None
            if nominal_metrics is not None:
                nominal_success = nominal_metrics["aggregate"]["success_rate_mean"]
            print("anchor", anchor["suite_name"], "nominal_success_rate_mean", nominal_success)


if __name__ == "__main__":
    main()
