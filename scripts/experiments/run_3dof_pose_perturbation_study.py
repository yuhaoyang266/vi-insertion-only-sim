from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from vi_full.three_dof_benchmark import (
    _run_3dof_registry_suite_across_profiles,
    run_3dof_handcrafted_uncertainty_suite,
)
from vi_full.three_dof_policies import build_3dof_handcrafted_policy_registry
from vi_full.three_dof_profiles import (
    POSE_PERTURBATION_PROFILES,
    describe_3dof_pose_perturbation_profile,
)

POSE_PERTURBATION_SUITE_NAMES = [
    "ppo_no_bc",
    "bc_only_stable_r32_p32",
    "fixed_impedance_rl_stable_r32_p32",
    "repaired_mainline_bc_to_ppo",
    "dapg_lite_repaired_mainline",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the 3DoF pose-perturbation external-validity study."
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--max-episode-steps", type=int, default=64)
    parser.add_argument(
        "--profiles",
        type=str,
        nargs="+",
        default=list(POSE_PERTURBATION_PROFILES),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional explicit output path for the perturbation-study JSON.",
    )
    return parser.parse_args()


def _default_output_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("outputs") / f"three_dof_pose_perturbation_study_{timestamp}.json"


def _write_report(output_path: Path, report: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    output_path = args.output if args.output is not None else _default_output_path()
    perturbation_profiles = list(args.profiles)
    handcrafted_results = run_3dof_handcrafted_uncertainty_suite(
        seeds=list(args.seeds),
        episodes_per_seed=int(args.episodes),
        max_episode_steps=int(args.max_episode_steps),
        uncertainty_profiles=perturbation_profiles,
    )
    learned_results = {
        suite_name: _run_3dof_registry_suite_across_profiles(
            suite_name=suite_name,
            train_seeds=list(args.seeds),
            episodes_per_seed=int(args.episodes),
            max_episode_steps=int(args.max_episode_steps),
            uncertainty_profiles=perturbation_profiles,
            total_timesteps=128,
        )
        for suite_name in POSE_PERTURBATION_SUITE_NAMES
    }
    report = {
        "config": {
            "profile_family": "pose_perturbation",
            "perturbation_profiles": perturbation_profiles,
            "seeds": list(args.seeds),
            "episodes_per_seed": int(args.episodes),
            "max_episode_steps": int(args.max_episode_steps),
            "suite_names": list(POSE_PERTURBATION_SUITE_NAMES),
            "handcrafted_policy_names": list(
                build_3dof_handcrafted_policy_registry().keys()
            ),
        },
        "profile_definitions": [
            describe_3dof_pose_perturbation_profile(profile_name)
            for profile_name in perturbation_profiles
        ],
        "handcrafted_results": handcrafted_results,
        "learned_results": learned_results,
    }
    _write_report(output_path, report)
    print(output_path)


if __name__ == "__main__":
    main()
