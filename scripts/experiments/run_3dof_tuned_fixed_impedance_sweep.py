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
    run_3dof_condition_across_profiles,
    select_top_3dof_tuned_fixed_configs,
)
from vi_full.three_dof_training import build_3dof_fixed_impedance_env_overrides_for


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tuned fixed-impedance sweep for the 3DoF insertion paper."
    )
    parser.add_argument("--search-seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--confirm-seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--search-episodes", type=int, default=50)
    parser.add_argument("--confirm-episodes", type=int, default=100)
    parser.add_argument(
        "--k-xy-values",
        type=float,
        nargs="+",
        default=[30.0, 50.0, 65.0, 80.0, 100.0],
    )
    parser.add_argument(
        "--k-z-values",
        type=float,
        nargs="+",
        default=[50.0, 75.0, 87.5, 110.0, 130.0],
    )
    parser.add_argument("--top-k", type=int, default=1)
    parser.add_argument(
        "--profiles",
        type=str,
        nargs="+",
        default=list(DEFAULT_UNCERTAINTY_PROFILES),
    )
    parser.add_argument("--max-episode-steps", type=int, default=64)
    parser.add_argument("--total-timesteps", type=int, default=128)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional explicit output path for the JSON artifact.",
    )
    return parser.parse_args()


def _default_output_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("outputs") / f"three_dof_tuned_fixed_impedance_sweep_{timestamp}.json"


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


def _format_value_tag(value: float) -> str:
    return str(float(value)).replace("-", "m").replace(".", "p")


def _fixed_train_overrides(k_xy: float, k_z: float) -> dict[str, Any]:
    return {
        "bc_rollout_episodes": 32,
        "bc_pretrain_steps": 32,
        "bc_batch_size": 64,
        "base_env_overrides": build_3dof_fixed_impedance_env_overrides_for(
            k_xy=float(k_xy),
            k_z=float(k_z),
        ),
    }


def _run_fixed_config(
    *,
    k_xy: float,
    k_z: float,
    seeds: list[int],
    episodes: int,
    max_episode_steps: int,
    profiles: list[str],
    total_timesteps: int,
    stage_name: str,
) -> dict[str, Any]:
    condition_name = (
        f"tuned_fixed_{stage_name}_"
        f"kxy{_format_value_tag(k_xy)}_kz{_format_value_tag(k_z)}"
    )
    result = run_3dof_condition_across_profiles(
        condition_name=condition_name,
        train_seeds=seeds,
        episodes_per_seed=int(episodes),
        max_episode_steps=int(max_episode_steps),
        uncertainty_profiles=profiles,
        total_timesteps=int(total_timesteps),
        train_uncertainty_profile="nominal",
        train_overrides=_fixed_train_overrides(k_xy, k_z),
    )
    result["k_xy"] = float(k_xy)
    result["k_z"] = float(k_z)
    return result


def main() -> None:
    args = _parse_args()
    k_xy_values = [float(value) for value in args.k_xy_values]
    k_z_values = [float(value) for value in args.k_z_values]
    profiles = list(args.profiles)

    search_results: list[dict[str, Any]] = []
    for k_xy in k_xy_values:
        for k_z in k_z_values:
            result = _run_fixed_config(
                k_xy=k_xy,
                k_z=k_z,
                seeds=[int(seed) for seed in args.search_seeds],
                episodes=int(args.search_episodes),
                max_episode_steps=int(args.max_episode_steps),
                profiles=profiles,
                total_timesteps=int(args.total_timesteps),
                stage_name="search",
            )
            search_results.append(result)
            mean_success = result["five_profile_mean"].get(
                "success_rate_mean_over_profiles",
                float("nan"),
            )
            print(f"search k_xy={k_xy} k_z={k_z}: success_mean={mean_success}")

    selected_configs = select_top_3dof_tuned_fixed_configs(
        search_results,
        top_k=int(args.top_k),
    )

    confirm_results: list[dict[str, Any]] = []
    for selected in selected_configs:
        result = _run_fixed_config(
            k_xy=float(selected["k_xy"]),
            k_z=float(selected["k_z"]),
            seeds=[int(seed) for seed in args.confirm_seeds],
            episodes=int(args.confirm_episodes),
            max_episode_steps=int(args.max_episode_steps),
            profiles=profiles,
            total_timesteps=int(args.total_timesteps),
            stage_name="confirm",
        )
        result["selection_rank"] = int(selected["selection_rank"])
        confirm_results.append(result)
        mean_success = result["five_profile_mean"].get(
            "success_rate_mean_over_profiles",
            float("nan"),
        )
        print(
            f"confirm rank={selected['selection_rank']} "
            f"k_xy={selected['k_xy']} k_z={selected['k_z']}: "
            f"success_mean={mean_success}"
        )

    output = {
        "experiment_name": "three_dof_tuned_fixed_impedance_sweep",
        "grid": {
            "k_xy_values": k_xy_values,
            "k_z_values": k_z_values,
        },
        "search_contract": {
            "seed_list": [int(seed) for seed in args.search_seeds],
            "episodes_per_seed": int(args.search_episodes),
            "profiles": profiles,
            "max_episode_steps": int(args.max_episode_steps),
            "total_timesteps": int(args.total_timesteps),
            "train_overrides_template": {
                "bc_rollout_episodes": 32,
                "bc_pretrain_steps": 32,
                "bc_batch_size": 64,
            },
        },
        "confirm_contract": {
            "seed_list": [int(seed) for seed in args.confirm_seeds],
            "episodes_per_seed": int(args.confirm_episodes),
            "profiles": profiles,
            "max_episode_steps": int(args.max_episode_steps),
            "total_timesteps": int(args.total_timesteps),
        },
        "search_results": search_results,
        "selected_configs": selected_configs,
        "confirm_results": confirm_results,
    }
    output_path = args.output or _default_output_path()
    _write_json(output_path, output)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
