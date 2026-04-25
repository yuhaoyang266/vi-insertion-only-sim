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
    build_teacher_coupling_grid,
    teacher_coupling_report_payload,
)

from run_3dof_uncertainty_benchmark import _run_3dof_suite_across_profiles


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the 3DoF teacher-coupling crossed ablation."
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--total-timesteps", type=int, default=128)
    parser.add_argument("--episodes", type=int, default=16)
    parser.add_argument("--profiles", type=str, nargs="+", default=list(DEFAULT_UNCERTAINTY_PROFILES))
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


def main() -> None:
    args = parse_args()
    learned_results: dict[str, Any] = {}
    grid = build_teacher_coupling_grid(
        seeds=args.seeds,
        total_timesteps=args.total_timesteps,
    )
    config = {
        "seeds": list(args.seeds),
        "total_timesteps": int(args.total_timesteps),
        "episodes": int(args.episodes),
        "profiles": list(args.profiles),
        "condition_names": [condition.name for condition in grid],
    }
    for condition in grid:
        print(f"running_condition {condition.name}", flush=True)
        suite_kwargs = condition.to_suite_run_kwargs(
            episodes=args.episodes,
            profiles=args.profiles,
        )
        result = _run_3dof_suite_across_profiles(suite_kwargs)
        result["teacher_prior"] = condition.teacher_prior
        result["student_impedance_space"] = condition.student_impedance_space
        learned_results[condition.name] = result
        _write_json(
            args.output,
            teacher_coupling_report_payload(
                learned_results=learned_results,
                config=config,
            ),
        )
    print(f"teacher_coupling_report {args.output}", flush=True)


if __name__ == "__main__":
    main()
