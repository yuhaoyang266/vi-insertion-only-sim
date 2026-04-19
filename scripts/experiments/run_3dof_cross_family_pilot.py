from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_cross_family_baselines import (
    build_3dof_cross_family_pilot_registry,
    run_3dof_cross_family_method_across_profiles,
)


def _parse_args() -> argparse.Namespace:
    registry = build_3dof_cross_family_pilot_registry()
    parser = argparse.ArgumentParser(
        description="Run the 3DoF cross-family pure-RL pilot."
    )
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--budgets", type=int, nargs="+", default=registry["budget_points"])
    parser.add_argument(
        "--profiles",
        type=str,
        nargs="+",
        default=list(registry["default_profiles"]),
    )
    parser.add_argument(
        "--train-profile",
        type=str,
        default="nominal",
        help="Training uncertainty profile for all pilot methods.",
    )
    parser.add_argument(
        "--max-episode-steps",
        type=int,
        default=DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    )
    parser.add_argument(
        "--methods",
        type=str,
        nargs="+",
        default=None,
        help="Optional subset of method names from the cross-family registry.",
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
    return Path("outputs") / f"three_dof_cross_family_pilot_{timestamp}.json"


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


def _selected_methods(
    registry_methods: list[dict[str, Any]],
    selected_names: list[str] | None,
) -> list[dict[str, Any]]:
    if selected_names is None:
        return list(registry_methods)
    method_by_name = {
        str(method["method_name"]): method
        for method in registry_methods
    }
    missing = [name for name in selected_names if name not in method_by_name]
    if missing:
        raise ValueError(f"Unknown cross-family pilot method(s): {missing}")
    return [method_by_name[name] for name in selected_names]


def main() -> None:
    args = _parse_args()
    registry = build_3dof_cross_family_pilot_registry()
    budgets = [int(budget) for budget in args.budgets]
    methods = _selected_methods(registry["methods"], args.methods)

    method_results: list[dict[str, Any]] = []
    for method in methods:
        points: list[dict[str, Any]] = []
        for budget in budgets:
            point = run_3dof_cross_family_method_across_profiles(
                method_name=str(method["method_name"]),
                algorithm=str(method["algorithm"]),
                train_seeds=[int(seed) for seed in args.seeds],
                episodes_per_seed=int(args.episodes),
                max_episode_steps=int(args.max_episode_steps),
                uncertainty_profiles=list(args.profiles),
                total_timesteps=int(budget),
                train_uncertainty_profile=str(args.train_profile),
            )
            points.append(point)
            mean_success = point["five_profile_mean"].get(
                "success_rate_mean_over_profiles",
                float("nan"),
            )
            print(
                f"{method['method_name']} budget={budget}: "
                f"success_mean_over_profiles={mean_success}"
            )
        method_results.append(
            {
                "method_name": method["method_name"],
                "label": method["label"],
                "algorithm": method["algorithm"],
                "train_overrides": dict(method["train_overrides"]),
                "points": points,
            }
        )

    output = {
        "experiment_name": registry["experiment_name"],
        "config": {
            "seed_list": [int(seed) for seed in args.seeds],
            "budget_points": budgets,
            "train_profile": str(args.train_profile),
            "profiles": list(args.profiles),
            "episodes_per_seed": int(args.episodes),
            "max_episode_steps": int(args.max_episode_steps),
            "method_names": [str(method["method_name"]) for method in methods],
            "benchmark_contract": asdict(DEFAULT_3DOF_BENCHMARK_CONTRACT),
        },
        "methods": method_results,
    }
    output_path = args.output or _default_output_path()
    _write_json(output_path, output)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
