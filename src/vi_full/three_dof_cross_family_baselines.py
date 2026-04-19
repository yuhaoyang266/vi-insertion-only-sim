from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass, replace
import math
from typing import Any

import numpy as np
from stable_baselines3 import PPO, SAC, TD3
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.noise import NormalActionNoise
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from vi_full.training import VecNormalizePredictor
from vi_full.three_dof_benchmark import (
    THREE_DOF_NUMERIC_METRICS,
    evaluate_3dof_predictor,
    summarize_3dof_seed_runs,
)
from vi_full.three_dof_config import ThreeDoFResetConfig
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_env import ThreeDoFInsertionEnv
from vi_full.three_dof_profiles import build_3dof_profile_config
from vi_full.three_dof_training import build_3dof_default_train_reset_config


_CROSS_FAMILY_PILOT_BUDGET_POINTS = [50_000, 100_000, 200_000]
_DEFAULT_OFF_POLICY_WARMUP_STEPS = max(
    1000,
    DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps * 16,
)
_DEFAULT_OFF_POLICY_BUFFER_SIZE = max(_CROSS_FAMILY_PILOT_BUDGET_POINTS)


_COMMON_CONFIG_FIELDS = {
    "policy_name",
    "policy_kwargs",
    "n_envs",
    "batch_size",
    "learning_rate",
    "gamma",
    "norm_obs",
    "norm_reward",
    "verbose",
    "device",
    "base_env_overrides",
    "action_noise_std",
}


def build_3dof_cross_family_pilot_registry() -> dict[str, Any]:
    return {
        "experiment_name": "three_dof_cross_family_pilot",
        "budget_points": list(_CROSS_FAMILY_PILOT_BUDGET_POINTS),
        "default_profiles": ["nominal"],
        "methods": [
            {
                "method_name": "ppo_no_bc",
                "label": "PPO w/o BC",
                "algorithm": "ppo",
                "train_overrides": {
                    "n_envs": 4,
                    "n_steps": 256,
                    "batch_size": 256,
                    "n_epochs": 4,
                    "learning_rate": 3e-4,
                    "gamma": 0.99,
                    "gae_lambda": 0.95,
                    "ent_coef": 0.01,
                },
            },
            {
                "method_name": "sac_no_bc",
                "label": "SAC w/o BC",
                "algorithm": "sac",
                "train_overrides": {
                    "n_envs": 1,
                    "batch_size": 256,
                    "learning_rate": 3e-4,
                    "gamma": 0.99,
                    "buffer_size": _DEFAULT_OFF_POLICY_BUFFER_SIZE,
                    "learning_starts": _DEFAULT_OFF_POLICY_WARMUP_STEPS,
                    "train_freq": 1,
                    "gradient_steps": 1,
                    "tau": 0.005,
                    "ent_coef": "auto",
                },
            },
            {
                "method_name": "td3_no_bc",
                "label": "TD3 w/o BC",
                "algorithm": "td3",
                "train_overrides": {
                    "n_envs": 1,
                    "batch_size": 256,
                    "learning_rate": 3e-4,
                    "gamma": 0.99,
                    "buffer_size": _DEFAULT_OFF_POLICY_BUFFER_SIZE,
                    "learning_starts": _DEFAULT_OFF_POLICY_WARMUP_STEPS,
                    "train_freq": 1,
                    "gradient_steps": 1,
                    "tau": 0.005,
                    "policy_delay": 2,
                    "target_policy_noise": 0.2,
                    "target_noise_clip": 0.5,
                    "action_noise_std": 0.1,
                },
            },
        ],
    }


def _sanitize_3dof_serializable(value: object) -> object:
    if is_dataclass(value):
        return _sanitize_3dof_serializable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _sanitize_3dof_serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize_3dof_serializable(item) for item in value]
    if isinstance(value, float):
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
        if math.isnan(value):
            return "nan"
    return value


@dataclass(frozen=True, slots=True)
class ThreeDoFCrossFamilyTrainConfig:
    method_name: str
    algorithm: str
    total_timesteps: int = 2048
    seed: int = 0
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps
    train_uncertainty_profile: str = "nominal"
    eval_uncertainty_profile: str = "nominal"
    policy_name: str = "MlpPolicy"
    policy_kwargs: dict[str, Any] = field(default_factory=dict)
    n_envs: int = 1
    batch_size: int = 256
    learning_rate: float = 3e-4
    gamma: float = 0.99
    norm_obs: bool = True
    norm_reward: bool = True
    verbose: int = 0
    device: str = "cpu"
    base_env_overrides: dict[str, float] = field(default_factory=dict)
    train_reset_config: ThreeDoFResetConfig = field(
        default_factory=build_3dof_default_train_reset_config
    )
    algorithm_kwargs: dict[str, Any] = field(default_factory=dict)
    action_noise_std: float | None = None


def serialize_3dof_cross_family_train_config(
    config: ThreeDoFCrossFamilyTrainConfig,
) -> dict[str, object]:
    return _sanitize_3dof_serializable(asdict(config))


@dataclass(slots=True)
class ThreeDoFCrossFamilyArtifacts:
    model: BaseAlgorithm
    vec_normalize: VecNormalize
    train_config: ThreeDoFCrossFamilyTrainConfig
    training_summary: dict[str, object]

    def make_eval_env(
        self,
        seed: int | None = None,
        *,
        uncertainty_profile: str | None = None,
    ) -> ThreeDoFInsertionEnv:
        profile_name = uncertainty_profile or self.train_config.eval_uncertainty_profile
        replace_kwargs: dict[str, object] = {}
        if self.train_config.base_env_overrides:
            replace_kwargs.update(self.train_config.base_env_overrides)
        env = ThreeDoFInsertionEnv(
            replace(
                build_3dof_profile_config(
                    profile_name,
                    max_episode_steps=self.train_config.max_episode_steps,
                ),
                **replace_kwargs,
            )
        )
        if seed is not None:
            env.reset(seed=seed)
        return env


def _get_cross_family_method_spec(method_name: str) -> dict[str, Any]:
    registry = build_3dof_cross_family_pilot_registry()
    for method in registry["methods"]:
        if str(method["method_name"]) == method_name:
            return dict(method)
    raise ValueError(f"Unknown cross-family pilot method: {method_name}")


def build_3dof_cross_family_train_config(
    *,
    method_name: str,
    seed: int,
    total_timesteps: int,
    max_episode_steps: int,
    train_uncertainty_profile: str = "nominal",
    eval_uncertainty_profile: str | None = None,
    train_overrides: dict[str, Any] | None = None,
) -> ThreeDoFCrossFamilyTrainConfig:
    method_spec = _get_cross_family_method_spec(method_name)
    overrides = dict(method_spec["train_overrides"])
    if train_overrides:
        overrides.update(train_overrides)

    common_kwargs = {
        key: overrides.pop(key)
        for key in list(overrides)
        if key in _COMMON_CONFIG_FIELDS
    }
    if "base_env_overrides" in common_kwargs:
        common_kwargs["base_env_overrides"] = dict(common_kwargs["base_env_overrides"])
    if "policy_kwargs" in common_kwargs:
        common_kwargs["policy_kwargs"] = dict(common_kwargs["policy_kwargs"])
    if (
        str(method_spec["algorithm"]) != "td3"
        and common_kwargs.get("action_noise_std") is not None
    ):
        raise ValueError("action_noise_std is only supported for td3 baselines")

    return ThreeDoFCrossFamilyTrainConfig(
        method_name=str(method_spec["method_name"]),
        algorithm=str(method_spec["algorithm"]),
        total_timesteps=int(total_timesteps),
        seed=int(seed),
        max_episode_steps=int(max_episode_steps),
        train_uncertainty_profile=str(train_uncertainty_profile),
        eval_uncertainty_profile=str(
            eval_uncertainty_profile or train_uncertainty_profile
        ),
        algorithm_kwargs=overrides,
        **common_kwargs,
    )


def create_3dof_baseline_training_vec_env(
    config: ThreeDoFCrossFamilyTrainConfig,
) -> VecNormalize:
    def _make_env(rank: int):
        def _factory():
            profile_config = build_3dof_profile_config(
                config.train_uncertainty_profile,
                max_episode_steps=config.max_episode_steps,
            )
            replace_kwargs: dict[str, object] = {
                "reset_config": config.train_reset_config,
            }
            if config.base_env_overrides:
                replace_kwargs.update(config.base_env_overrides)
            env = ThreeDoFInsertionEnv(replace(profile_config, **replace_kwargs))
            env.reset(seed=config.seed + rank)
            return env

        return _factory

    vec_env = DummyVecEnv([_make_env(rank) for rank in range(config.n_envs)])
    return VecNormalize(
        vec_env,
        norm_obs=config.norm_obs,
        norm_reward=config.norm_reward,
        clip_obs=10.0,
        gamma=config.gamma,
    )


def _build_td3_action_noise(
    config: ThreeDoFCrossFamilyTrainConfig,
    vec_env: VecNormalize,
) -> NormalActionNoise | None:
    if config.action_noise_std is None or config.action_noise_std <= 0.0:
        return None
    action_dim = int(np.prod(vec_env.action_space.shape))
    sigma = np.full(action_dim, float(config.action_noise_std), dtype=np.float32)
    return NormalActionNoise(
        mean=np.zeros(action_dim, dtype=np.float32),
        sigma=sigma,
    )


def _build_algorithm(
    config: ThreeDoFCrossFamilyTrainConfig,
    vec_env: VecNormalize,
) -> BaseAlgorithm:
    common_kwargs: dict[str, Any] = {
        "learning_rate": config.learning_rate,
        "gamma": config.gamma,
        "batch_size": config.batch_size,
        "seed": config.seed,
        "verbose": config.verbose,
        "device": config.device,
    }
    if config.policy_kwargs:
        common_kwargs["policy_kwargs"] = dict(config.policy_kwargs)

    if config.algorithm == "ppo":
        return PPO(
            config.policy_name,
            vec_env,
            **common_kwargs,
            **dict(config.algorithm_kwargs),
        )
    if config.algorithm == "sac":
        return SAC(
            config.policy_name,
            vec_env,
            **common_kwargs,
            **dict(config.algorithm_kwargs),
        )
    if config.algorithm == "td3":
        td3_kwargs = dict(config.algorithm_kwargs)
        action_noise = _build_td3_action_noise(config, vec_env)
        if action_noise is not None:
            td3_kwargs["action_noise"] = action_noise
        return TD3(
            config.policy_name,
            vec_env,
            **common_kwargs,
            **td3_kwargs,
        )
    raise ValueError(f"Unsupported cross-family algorithm: {config.algorithm}")


def train_3dof_family_baseline(
    config: ThreeDoFCrossFamilyTrainConfig,
) -> ThreeDoFCrossFamilyArtifacts:
    vec_env = create_3dof_baseline_training_vec_env(config)
    model = _build_algorithm(config, vec_env)
    model.learn(total_timesteps=config.total_timesteps)
    vec_env.training = False
    vec_env.norm_reward = False
    return ThreeDoFCrossFamilyArtifacts(
        model=model,
        vec_normalize=vec_env,
        train_config=config,
        training_summary={
            "method_name": config.method_name,
            "algorithm": config.algorithm,
            "seed": int(config.seed),
            "total_timesteps": int(config.total_timesteps),
            "train_uncertainty_profile": config.train_uncertainty_profile,
            "n_envs": int(config.n_envs),
        },
    )


def _build_3dof_profile_mean(per_profile_metrics: dict[str, Any]) -> dict[str, float]:
    summary: dict[str, float] = {}
    for metric_name in THREE_DOF_NUMERIC_METRICS:
        values = [
            float(payload["aggregate"][f"{metric_name}_mean"])
            for payload in per_profile_metrics.values()
        ]
        mean_value = float(sum(values) / len(values))
        variance = sum((value - mean_value) ** 2 for value in values) / len(values)
        summary[f"{metric_name}_mean_over_profiles"] = mean_value
        summary[f"{metric_name}_std_over_profiles"] = float(variance**0.5)
    return summary


def run_3dof_cross_family_method_across_profiles(
    *,
    method_name: str,
    algorithm: str,
    train_seeds: list[int],
    episodes_per_seed: int,
    max_episode_steps: int,
    uncertainty_profiles: list[str],
    total_timesteps: int,
    train_uncertainty_profile: str = "nominal",
    train_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profiles = list(uncertainty_profiles)
    per_profile_metrics: dict[str, Any] = {
        profile_name: {"per_seed": []}
        for profile_name in profiles
    }
    train_configs: list[dict[str, Any]] = []
    training_summaries: list[dict[str, Any]] = []
    first_train_config: ThreeDoFCrossFamilyTrainConfig | None = None

    for seed in train_seeds:
        train_config = build_3dof_cross_family_train_config(
            method_name=method_name,
            seed=int(seed),
            total_timesteps=int(total_timesteps),
            max_episode_steps=int(max_episode_steps),
            train_uncertainty_profile=str(train_uncertainty_profile),
            train_overrides=train_overrides,
        )
        if train_config.algorithm != algorithm:
            raise ValueError(
                f"Method '{method_name}' resolves to algorithm '{train_config.algorithm}', "
                f"not '{algorithm}'"
            )
        if first_train_config is None:
            first_train_config = train_config
        artifacts = train_3dof_family_baseline(train_config)
        predictor = VecNormalizePredictor(
            model=artifacts.model,
            vec_normalize=artifacts.vec_normalize,
        )
        train_configs.append(serialize_3dof_cross_family_train_config(train_config))
        training_summaries.append({"seed": int(seed), **dict(artifacts.training_summary)})

        try:
            for profile_index, profile_name in enumerate(profiles):
                eval_seed = int(seed) + 10_000 + profile_index * 1_000
                env = artifacts.make_eval_env(
                    seed=eval_seed,
                    uncertainty_profile=profile_name,
                )
                try:
                    summary = evaluate_3dof_predictor(
                        env,
                        predictor,
                        episodes=int(episodes_per_seed),
                        seed=eval_seed,
                        uncertainty_profile=profile_name,
                    )
                finally:
                    env.close()
                summary["seed"] = int(seed)
                summary["training_summary"] = dict(artifacts.training_summary)
                per_profile_metrics[profile_name]["per_seed"].append(summary)
        finally:
            artifacts.vec_normalize.close()

    if first_train_config is None:
        raise ValueError("train_seeds must contain at least one seed")

    for profile_name, payload in per_profile_metrics.items():
        payload["aggregate"] = summarize_3dof_seed_runs(payload["per_seed"])
        payload["aggregate"]["method_name"] = method_name
        payload["aggregate"]["algorithm"] = algorithm
        payload["aggregate"]["train_uncertainty_profile"] = train_uncertainty_profile
        payload["aggregate"]["eval_uncertainty_profile"] = profile_name

    return {
        "method_name": method_name,
        "algorithm": algorithm,
        "factor_value": int(total_timesteps),
        "training_budget": {"total_timesteps": int(total_timesteps)},
        "train_config_snapshot": serialize_3dof_cross_family_train_config(
            first_train_config
        ),
        "train_configs": train_configs,
        "training_summaries": training_summaries,
        "per_profile_metrics": per_profile_metrics,
        "five_profile_mean": _build_3dof_profile_mean(per_profile_metrics),
    }
