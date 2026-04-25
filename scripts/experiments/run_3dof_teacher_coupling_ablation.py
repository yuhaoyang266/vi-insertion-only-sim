from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.three_dof_benchmark import DEFAULT_UNCERTAINTY_PROFILES
from vi_full.three_dof_teacher_coupling_ablation import (
    build_motion_matched_grid,
    build_teacher_coupling_grid,
    teacher_coupling_report_payload,
)

from run_3dof_uncertainty_benchmark import _run_3dof_suite_across_profiles

_METADATA_KEYS = (
    "motion_rule",
    "impedance_rule",
    "fixed_stiffness_xy",
    "fixed_stiffness_z",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the 3DoF teacher-coupling crossed ablation."
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--total-timesteps", type=int, default=128)
    parser.add_argument("--episodes", type=int, default=16)
    parser.add_argument("--profiles", type=str, nargs="+", default=list(DEFAULT_UNCERTAINTY_PROFILES))
    parser.add_argument("--smoke-only", action="store_true")
    parser.add_argument("--include-motion-matched", action="store_true")
    parser.add_argument(
        "--motion-matched-output",
        type=Path,
        default=Path("outputs/revision/motion_matched_impedance_ablation_20260425.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/revision/teacher_coupling_ablation_20260425.json"),
    )
    return parser.parse_args()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def _split_suite_metadata(suite_kwargs: dict[str, Any]) -> dict[str, Any]:
    return {key: suite_kwargs.pop(key) for key in _METADATA_KEYS if key in suite_kwargs}


def _smoke_only_result(condition) -> dict[str, Any]:
    return {
        "teacher_prior": condition.teacher_prior,
        "student_impedance_space": condition.student_impedance_space,
        "teacher_motion_rule": condition.teacher_spec.motion_rule,
        "teacher_impedance_rule": condition.teacher_spec.impedance_rule,
        "training_summaries": [{"seed": int(seed)} for seed in condition.seeds],
        "five_profile_mean": {},
        "support_metrics": {},
    }


def _run_grid(
    *,
    grid,
    args: argparse.Namespace,
    output_path: Path,
    ablation_name: str,
) -> None:
    learned_results: dict[str, Any] = {}
    config = {
        "seeds": list(args.seeds),
        "total_timesteps": int(args.total_timesteps),
        "episodes": int(args.episodes),
        "profiles": list(args.profiles),
        "condition_names": [condition.name for condition in grid],
        "ablation_name": ablation_name,
        "smoke_only": bool(args.smoke_only),
    }
    if args.smoke_only:
        learned_results = {
            condition.name: _smoke_only_result(condition)
            for condition in grid
        }
        _write_json(
            output_path,
            teacher_coupling_report_payload(
                learned_results=learned_results,
                config=config,
            ),
        )
        print(f"{ablation_name}_report {output_path}", flush=True)
        return
    for condition in grid:
        print(f"running_condition {condition.name}", flush=True)
        suite_kwargs = condition.to_suite_run_kwargs(
            episodes=args.episodes,
            profiles=args.profiles,
        )
        metadata = _split_suite_metadata(suite_kwargs)
        result = _run_3dof_suite_across_profiles(suite_kwargs)
        result.update(metadata)
        result["teacher_prior"] = condition.teacher_prior
        result["student_impedance_space"] = condition.student_impedance_space
        learned_results[condition.name] = result
        _write_json(
            output_path,
            teacher_coupling_report_payload(
                learned_results=learned_results,
                config=config,
            ),
        )
    print(f"{ablation_name}_report {output_path}", flush=True)


def main() -> None:
    args = parse_args()
    _run_grid(
        grid=build_teacher_coupling_grid(
            seeds=args.seeds,
            total_timesteps=args.total_timesteps,
        ),
        args=args,
        output_path=args.output,
        ablation_name="teacher_coupling",
    )
    if args.include_motion_matched:
        _run_grid(
            grid=build_motion_matched_grid(
                seeds=args.seeds,
                total_timesteps=args.total_timesteps,
            ),
            args=args,
            output_path=args.motion_matched_output,
            ablation_name="motion_matched_impedance",
        )


if __name__ == "__main__":
    main()
