from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from vi_full.cross_paper_bridge import CONTRACT_SHA


MODERN_BASELINE_DECISION = {
    "chosen": "iql_offline",
    "compatible_fallbacks": ["cql_offline", "diffusion_policy_lerobot", "act_state_based"],
    "rationale": (
        "IQL/CQL can consume the existing Paper-A 14D observation and 5D action offline "
        "dataset contract without introducing vision, hardware, or action-space scope."
    ),
}


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def build_synthetic_offline_dataset(*, num_steps: int = 8) -> dict[str, Any]:
    if num_steps <= 0:
        raise ValueError("num_steps must be positive.")
    observations = np.zeros((num_steps, 14), dtype=np.float32)
    actions = np.zeros((num_steps, 5), dtype=np.float32)
    rewards = np.zeros((num_steps,), dtype=np.float32)
    observations[:, 0] = np.linspace(0.003, 0.0, num_steps, dtype=np.float32)
    observations[:, 2] = np.linspace(0.006, 0.0, num_steps, dtype=np.float32)
    actions[:, 2] = -0.25
    actions[:, 3] = 0.5
    actions[:, 4] = 0.6
    rewards[-1] = 1.0
    return {
        "observations": observations,
        "actions": actions,
        "rewards": rewards,
        "episode_boundaries": [0, int(num_steps)],
        "profiles": ["nominal"],
        "seed": 0,
        "source": "synthetic_schema_smoke",
        "contract_sha": CONTRACT_SHA,
    }


def _as_array(dataset: dict[str, Any], name: str, shape_tail: tuple[int, ...]) -> np.ndarray:
    if name not in dataset:
        raise ValueError(f"dataset is missing {name}")
    array = np.asarray(dataset[name], dtype=np.float32)
    if array.ndim != 1 + len(shape_tail) or tuple(array.shape[1:]) != shape_tail:
        raise ValueError(f"{name} must have shape [N, {', '.join(map(str, shape_tail))}]")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must contain only finite values")
    return array


def validate_offline_dataset_schema(dataset: dict[str, Any]) -> dict[str, Any]:
    observations = _as_array(dataset, "observations", (14,))
    actions = _as_array(dataset, "actions", (5,))
    rewards = _as_array(dataset, "rewards", ())
    if len(observations) != len(actions) or len(observations) != len(rewards):
        raise ValueError("observations, actions, and rewards must have matching first dimension")
    boundaries = [int(item) for item in dataset.get("episode_boundaries", [])]
    if not boundaries or boundaries[0] != 0 or boundaries[-1] != len(observations):
        raise ValueError("episode_boundaries must start at 0 and end at N")
    profiles = [str(item) for item in dataset.get("profiles", [])]
    if not profiles:
        raise ValueError("profiles must not be empty")
    return {
        "observation_shape": list(observations.shape),
        "action_shape": list(actions.shape),
        "reward_shape": list(rewards.shape),
        "episode_count": len(boundaries) - 1,
        "profile_count": len(set(profiles)),
        "sample_count": int(len(observations)),
        "contract_sha": str(dataset.get("contract_sha", "")),
    }


def run_modern_baseline_smoke(*, num_steps: int = 8) -> dict[str, Any]:
    dataset = build_synthetic_offline_dataset(num_steps=num_steps)
    dataset_summary = validate_offline_dataset_schema(dataset)
    return {
        "artifact_type": "modern_baseline_smoke",
        "schema_version": 1,
        "algorithm": MODERN_BASELINE_DECISION["chosen"],
        "status": "scaffold_only",
        "decision": dict(MODERN_BASELINE_DECISION),
        "dataset_summary": dataset_summary,
        "blocked_on": [
            "real Paper-A offline demonstration artifact path",
            "IQL/CQL training dependency and hyperparameter file",
            "comparison protocol against existing five-suite benchmark rows",
        ],
    }


def render_modern_baseline_smoke_markdown(report: dict[str, Any]) -> str:
    summary = report["dataset_summary"]
    lines = [
        "# Modern Baseline Smoke",
        "",
        f"- algorithm: {report['algorithm']}",
        f"- status: {report['status']}",
        f"- observation_shape: {summary['observation_shape']}",
        f"- action_shape: {summary['action_shape']}",
        f"- sample_count: {summary['sample_count']}",
        "",
        "## Blocked On",
        "",
    ]
    lines.extend(f"- {item}" for item in report["blocked_on"])
    lines.append("")
    return "\n".join(lines)


def write_modern_baseline_smoke_artifacts(
    output_path: Path,
    report: dict[str, Any],
) -> dict[str, Path]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_path
    markdown_path = output_path.with_suffix(".md")
    json_path.write_text(json.dumps(_json_safe(report), indent=2), encoding="utf-8")
    markdown_path.write_text(render_modern_baseline_smoke_markdown(report), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}
