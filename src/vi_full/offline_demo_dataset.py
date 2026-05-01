from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from vi_full.cross_paper_bridge import CONTRACT_SHA
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_env import ThreeDoFInsertionEnv
from vi_full.three_dof_policies import build_3dof_handcrafted_policy_registry
from vi_full.three_dof_profiles import DEFAULT_UNCERTAINTY_PROFILES, build_3dof_profile_config


OFFLINE_DEMO_DATASET_ARTIFACT_TYPE = "three_dof_offline_demo_dataset"


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


def compute_dataset_payload_sha256(dataset: dict[str, Any]) -> str:
    payload = {
        "artifact_type": dataset["artifact_type"],
        "schema_version": dataset["schema_version"],
        "metadata": {
            key: value
            for key, value in dict(dataset["metadata"]).items()
            if key != "dataset_payload_sha256"
        },
        "episodes": dataset["episodes"],
    }
    canonical = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _rollout_episode(
    *,
    profile: str,
    seed: int,
    episode_index: int,
    source_policy: str,
    max_episode_steps: int,
    paper_a_commit: str,
) -> dict[str, Any]:
    policy_registry = build_3dof_handcrafted_policy_registry()
    if source_policy not in policy_registry:
        raise ValueError(f"Unknown 3DoF handcrafted source policy: {source_policy}")
    policy = policy_registry[source_policy]()
    config = build_3dof_profile_config(
        profile,
        max_episode_steps=max_episode_steps,
    )
    env = ThreeDoFInsertionEnv(config)
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    rewards: list[float] = []
    try:
        observation, _ = env.reset(seed=int(seed) * 10_000 + int(episode_index))
        terminated = False
        truncated = False
        info: dict[str, Any] = {}
        while not (terminated or truncated):
            action = np.asarray(policy.act(observation), dtype=np.float32)
            observations.append(np.asarray(observation, dtype=np.float32).copy())
            actions.append(action.copy())
            observation, reward, terminated, truncated, info = env.step(action)
            rewards.append(float(reward))
    finally:
        env.close()
    return {
        "observations": np.stack(observations).astype(np.float32),
        "actions": np.stack(actions).astype(np.float32),
        "rewards": np.asarray(rewards, dtype=np.float32),
        "episode_id": (
            f"three_dof_offline_demo__{source_policy}__{profile}__"
            f"seed{int(seed):04d}__episode{int(episode_index):03d}"
        ),
        "profile": profile,
        "seed": int(seed),
        "success": bool(info.get("is_success", False)),
        "termination_reason": str(info.get("termination_reason", "unknown")),
        "source_policy": source_policy,
        "paper_a_commit": paper_a_commit,
        "contract_sha": CONTRACT_SHA,
    }


def build_offline_demo_dataset(
    *,
    profiles: list[str] | None = None,
    seeds: list[int] | None = None,
    episodes_per_seed: int = 1,
    source_policy: str = "variable_impedance",
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    paper_a_commit: str = "unknown",
    generation_command: str = "not_recorded",
) -> dict[str, Any]:
    if episodes_per_seed <= 0:
        raise ValueError("episodes_per_seed must be positive.")
    selected_profiles = list(profiles or DEFAULT_UNCERTAINTY_PROFILES)
    selected_seeds = [int(seed) for seed in (seeds or [0])]
    episodes: list[dict[str, Any]] = []
    for profile in selected_profiles:
        for seed in selected_seeds:
            for episode_index in range(int(episodes_per_seed)):
                episodes.append(
                    _rollout_episode(
                        profile=profile,
                        seed=seed,
                        episode_index=episode_index,
                        source_policy=source_policy,
                        max_episode_steps=max_episode_steps,
                        paper_a_commit=paper_a_commit,
                    )
                )
    sample_count = int(sum(len(record["rewards"]) for record in episodes))
    dataset = {
        "artifact_type": OFFLINE_DEMO_DATASET_ARTIFACT_TYPE,
        "schema_version": 1,
        "metadata": {
            "profiles": selected_profiles,
            "seeds": selected_seeds,
            "episodes_per_seed": int(episodes_per_seed),
            "source_policy": source_policy,
            "max_episode_steps": int(max_episode_steps),
            "paper_a_commit": paper_a_commit,
            "contract_sha": CONTRACT_SHA,
            "episode_count": len(episodes),
            "sample_count": sample_count,
            "generation_command": generation_command,
        },
        "episodes": episodes,
    }
    dataset["metadata"]["dataset_payload_sha256"] = compute_dataset_payload_sha256(dataset)
    return dataset


def flatten_offline_dataset_arrays(dataset: Any) -> tuple[np.ndarray, np.ndarray]:
    records = dataset["episodes"] if isinstance(dataset, dict) and "episodes" in dataset else dataset
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    for record in records:
        observations.append(np.asarray(record["observations"], dtype=np.float32))
        actions.append(np.asarray(record["actions"], dtype=np.float32))
    if not observations:
        raise ValueError("offline dataset must contain at least one episode")
    return (
        np.concatenate(observations, axis=0).astype(np.float32),
        np.concatenate(actions, axis=0).astype(np.float32),
    )


@dataclass(frozen=True, slots=True)
class NearestNeighborOfflinePolicy:
    observations: np.ndarray
    actions: np.ndarray
    name: str = "bc_offline_stub"

    def act(self, observation: np.ndarray) -> np.ndarray:
        query = np.asarray(observation, dtype=np.float32)
        distances = np.linalg.norm(self.observations - query[None, :], axis=1)
        return np.asarray(self.actions[int(np.argmin(distances))], dtype=np.float32)


def write_offline_demo_dataset_artifact(
    output_path: Path,
    dataset: dict[str, Any],
) -> dict[str, Path]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(_json_safe(dataset), indent=2), encoding="utf-8")
    return {"json": output_path}
