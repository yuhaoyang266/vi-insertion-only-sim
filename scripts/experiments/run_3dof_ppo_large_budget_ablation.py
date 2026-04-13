from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.three_dof_benchmark import (
    DEFAULT_UNCERTAINTY_PROFILES,
    build_3dof_ppo_large_budget_ablation_registry,
    run_3dof_condition_across_profiles,
)


def _parse_args() -> argparse.Namespace:
    registry = build_3dof_ppo_large_budget_ablation_registry()
    parser = argparse.ArgumentParser(
        description="Run PPO-only large-budget ablations for the 3DoF insertion paper."
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--budgets", type=int, nargs="+", default=registry["budget_points"])
    parser.add_argument(
        "--profiles",
        type=str,
        nargs="+",
        default=list(DEFAULT_UNCERTAINTY_PROFILES),
    )
    parser.add_argument("--max-episode-steps", type=int, default=64)
    parser.add_argument(
        "--conditions",
        type=str,
        nargs="+",
        default=None,
        help="Optional subset of condition names from the registry.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional explicit output path for the JSON artifact.",
    )
    return parser.parse_args()


def _default_output_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("outputs") / f"three_dof_ppo_large_budget_ablation_{timestamp}.json"


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _write_json(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_output_path = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temp_output_path.write_text(
        json.dumps(_json_safe(payload), indent=2),
        encoding="utf-8",
    )
    temp_output_path.replace(output_path)


def _selected_conditions(
    registry_conditions: list[dict[str, Any]],
    selected_names: list[str] | None,
) -> list[dict[str, Any]]:
    if selected_names is None:
        return list(registry_conditions)
    condition_by_name = {
        str(condition["condition_name"]): condition
        for condition in registry_conditions
    }
    missing = [name for name in selected_names if name not in condition_by_name]
    if missing:
        raise ValueError(f"Unknown PPO ablation condition(s): {missing}")
    return [condition_by_name[name] for name in selected_names]


def main() -> None:
    args = _parse_args()
    registry = build_3dof_ppo_large_budget_ablation_registry()
    budgets = [int(budget) for budget in args.budgets]
    conditions = _selected_conditions(registry["conditions"], args.conditions)

    condition_results: list[dict[str, Any]] = []
    for condition in conditions:
        points: list[dict[str, Any]] = []
        for budget in budgets:
            point = run_3dof_condition_across_profiles(
                condition_name=str(condition["condition_name"]),
                train_seeds=[int(seed) for seed in args.seeds],
                episodes_per_seed=int(args.episodes),
                max_episode_steps=int(args.max_episode_steps),
                uncertainty_profiles=list(args.profiles),
                total_timesteps=int(budget),
                train_uncertainty_profile="nominal",
                train_overrides=dict(condition["train_overrides"]),
            )
            points.append(point)
            mean_success = point["five_profile_mean"].get(
                "success_rate_mean_over_profiles",
                float("nan"),
            )
            print(
                f"{condition['condition_name']} budget={budget}: "
                f"success_mean_over_profiles={mean_success}"
            )
        condition_results.append(
            {
                "condition_name": condition["condition_name"],
                "label": condition["label"],
                "train_overrides": dict(condition["train_overrides"]),
                "points": points,
            }
        )

    output = {
        "experiment_name": registry["experiment_name"],
        "config": {
            "seed_list": [int(seed) for seed in args.seeds],
            "budget_points": budgets,
            "profiles": list(args.profiles),
            "episodes_per_seed": int(args.episodes),
            "max_episode_steps": int(args.max_episode_steps),
        },
        "conditions": condition_results,
    }
    output_path = args.output or _default_output_path()
    _write_json(output_path, output)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
