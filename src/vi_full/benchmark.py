from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

import numpy as np

from vi_full.env import PandaVariableImpedanceEnv, ResetConfig
from vi_full.evaluate import evaluate_policy
from vi_full.policies import (
    FixedImpedancePolicy,
    PoseOnlyPolicy,
    VariableImpedanceHeuristicPolicy,
)
from vi_full.training import PPOTrainConfig, VecNormalizePredictor, train_ppo_agent


NUMERIC_METRICS = (
    "success_rate",
    "mean_episode_return",
    "mean_final_distance",
    "mean_episode_length",
    "mean_peak_contact_force",
    "jam_rate",
)


def _default_policy_factories() -> dict[str, type]:
    return {
        "pose_only": PoseOnlyPolicy,
        "fixed_impedance": FixedImpedancePolicy,
        "variable_impedance": VariableImpedanceHeuristicPolicy,
    }


def summarize_seed_runs(run_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    if not run_summaries:
        raise ValueError("run_summaries must not be empty")

    aggregate: dict[str, Any] = {
        "policy_name": run_summaries[0]["policy_name"],
        "num_seeds": len(run_summaries),
        "seeds": [int(summary["seed"]) for summary in run_summaries],
    }
    for metric in NUMERIC_METRICS:
        values = np.asarray([summary[metric] for summary in run_summaries], dtype=np.float64)
        aggregate[f"{metric}_mean"] = float(np.mean(values))
        aggregate[f"{metric}_std"] = float(np.std(values))
    return aggregate


def evaluate_predictor(
    env,
    predictor,
    episodes: int = 5,
    seed: int = 0,
) -> dict[str, float | int | str]:
    class _PredictorPolicy:
        name = getattr(predictor, "name", predictor.__class__.__name__)

        def act(self, observation: np.ndarray) -> np.ndarray:
            action, _ = predictor.predict(observation, deterministic=True)
            return np.asarray(action, dtype=np.float32)

    return evaluate_policy(env, _PredictorPolicy(), episodes=episodes, seed=seed)


def run_handcrafted_suite(
    *,
    seeds: list[int],
    episodes_per_seed: int = 5,
    max_episode_steps: int = 32,
) -> dict[str, dict[str, Any]]:
    policy_factories = _default_policy_factories()
    results: dict[str, dict[str, Any]] = {}
    for policy_name, factory in policy_factories.items():
        per_seed: list[dict[str, Any]] = []
        for seed in seeds:
            env = PandaVariableImpedanceEnv(max_episode_steps=max_episode_steps)
            try:
                summary = evaluate_policy(env, factory(), episodes=episodes_per_seed, seed=seed)
            finally:
                env.close()
            summary["seed"] = seed
            per_seed.append(summary)
        results[policy_name] = {
            "per_seed": per_seed,
            "aggregate": summarize_seed_runs(per_seed),
        }
    return results


def run_handcrafted_reset_suite(
    *,
    seeds: list[int],
    eval_reset_configs: dict[str, ResetConfig],
    episodes_per_seed: int = 5,
    max_episode_steps: int = 32,
) -> dict[str, dict[str, dict[str, Any]]]:
    policy_factories = _default_policy_factories()
    results: dict[str, dict[str, dict[str, Any]]] = {}
    for eval_label, reset_config in eval_reset_configs.items():
        label_results: dict[str, dict[str, Any]] = {}
        for policy_name, factory in policy_factories.items():
            per_seed: list[dict[str, Any]] = []
            for seed in seeds:
                env = PandaVariableImpedanceEnv(
                    max_episode_steps=max_episode_steps,
                    reset_config=reset_config,
                )
                try:
                    summary = evaluate_policy(
                        env,
                        factory(),
                        episodes=episodes_per_seed,
                        seed=seed,
                    )
                finally:
                    env.close()
                summary["seed"] = seed
                per_seed.append(summary)
            label_results[policy_name] = {
                "per_seed": per_seed,
                "aggregate": summarize_seed_runs(per_seed),
            }
        results[eval_label] = label_results
    return results


def train_ppo_for_seed(
    *,
    seed: int,
    total_timesteps: int = 256,
    max_episode_steps: int = 32,
    bc_rollout_episodes: int = 0,
    bc_pretrain_steps: int = 0,
    bc_batch_size: int = 128,
    bc_demo_policy_name: str = "heuristic",
    contact_finetune_timesteps: int = 0,
    hard_reset_finetune_timesteps: int = 0,
):
    config = PPOTrainConfig(
        total_timesteps=total_timesteps,
        n_envs=1,
        n_steps=32,
        batch_size=32,
        n_epochs=1,
        learning_rate=1e-4,
        gamma=0.95,
        seed=seed,
        max_episode_steps=max_episode_steps,
        verbose=0,
        bc_rollout_episodes=bc_rollout_episodes,
        bc_pretrain_steps=bc_pretrain_steps,
        bc_batch_size=bc_batch_size,
        bc_demo_policy_name=bc_demo_policy_name,
        contact_finetune_timesteps=contact_finetune_timesteps,
        hard_reset_finetune_timesteps=hard_reset_finetune_timesteps,
    )
    return train_ppo_agent(config)


def run_learned_suite(
    *,
    seeds: list[int],
    total_timesteps: int = 256,
    episodes_per_seed: int = 5,
    max_episode_steps: int = 32,
    suite_name: str = "learned_ppo",
    bc_rollout_episodes: int = 0,
    bc_pretrain_steps: int = 0,
    bc_batch_size: int = 128,
    bc_demo_policy_name: str = "heuristic",
    contact_finetune_timesteps: int = 0,
    hard_reset_finetune_timesteps: int = 0,
) -> dict[str, Any]:
    per_seed: list[dict[str, Any]] = []
    for seed in seeds:
        artifacts = train_ppo_for_seed(
            seed=seed,
            total_timesteps=total_timesteps,
            max_episode_steps=max_episode_steps,
            bc_rollout_episodes=bc_rollout_episodes,
            bc_pretrain_steps=bc_pretrain_steps,
            bc_batch_size=bc_batch_size,
            bc_demo_policy_name=bc_demo_policy_name,
            contact_finetune_timesteps=contact_finetune_timesteps,
            hard_reset_finetune_timesteps=hard_reset_finetune_timesteps,
        )
        try:
            env = PandaVariableImpedanceEnv(max_episode_steps=max_episode_steps)
            try:
                predictor = VecNormalizePredictor(
                    model=artifacts.model,
                    vec_normalize=artifacts.vec_normalize,
                )
                summary = evaluate_predictor(
                    env,
                    predictor,
                    episodes=episodes_per_seed,
                    seed=seed + 10_000,
                )
            finally:
                env.close()
        finally:
            artifacts.close()
        summary["seed"] = seed
        per_seed.append(summary)
    aggregate = summarize_seed_runs(per_seed)
    aggregate["suite_name"] = suite_name
    return {
        "per_seed": per_seed,
        "aggregate": aggregate,
    }


def run_learned_reset_suite(
    *,
    seeds: list[int],
    eval_reset_configs: dict[str, ResetConfig],
    total_timesteps: int = 256,
    episodes_per_seed: int = 5,
    max_episode_steps: int = 32,
    suite_name: str = "learned_ppo",
    bc_rollout_episodes: int = 0,
    bc_pretrain_steps: int = 0,
    bc_batch_size: int = 128,
    bc_demo_policy_name: str = "heuristic",
    contact_finetune_timesteps: int = 0,
    hard_reset_finetune_timesteps: int = 0,
) -> dict[str, dict[str, Any]]:
    artifacts_by_seed: dict[int, Any] = {}
    try:
        artifacts_by_seed = {
            seed: train_ppo_for_seed(
                seed=seed,
                total_timesteps=total_timesteps,
                max_episode_steps=max_episode_steps,
                bc_rollout_episodes=bc_rollout_episodes,
                bc_pretrain_steps=bc_pretrain_steps,
                bc_batch_size=bc_batch_size,
                bc_demo_policy_name=bc_demo_policy_name,
                contact_finetune_timesteps=contact_finetune_timesteps,
                hard_reset_finetune_timesteps=hard_reset_finetune_timesteps,
            )
            for seed in seeds
        }

        results: dict[str, dict[str, Any]] = {}
        for eval_label, reset_config in eval_reset_configs.items():
            per_seed: list[dict[str, Any]] = []
            for seed in seeds:
                artifacts = artifacts_by_seed[seed]
                env = PandaVariableImpedanceEnv(
                    max_episode_steps=max_episode_steps,
                    reset_config=reset_config,
                )
                try:
                    predictor = VecNormalizePredictor(
                        model=artifacts.model,
                        vec_normalize=artifacts.vec_normalize,
                    )
                    summary = evaluate_predictor(
                        env,
                        predictor,
                        episodes=episodes_per_seed,
                        seed=seed + 10_000,
                    )
                finally:
                    env.close()
                summary["seed"] = seed
                per_seed.append(summary)
            aggregate = summarize_seed_runs(per_seed)
            aggregate["suite_name"] = suite_name
            results[eval_label] = {
                "per_seed": per_seed,
                "aggregate": aggregate,
            }
        return results
    finally:
        for artifacts in artifacts_by_seed.values():
            artifacts.close()


def build_benchmark_report(
    *,
    seeds: list[int],
    episodes_per_seed: int,
    total_timesteps: int,
    max_episode_steps: int,
    handcrafted_results: dict[str, Any],
    learned_results: dict[str, Any],
) -> dict[str, Any]:
    return {
        "config": {
            "seeds": seeds,
            "episodes_per_seed": episodes_per_seed,
            "total_timesteps": total_timesteps,
            "max_episode_steps": max_episode_steps,
        },
        "results": {
            "handcrafted": handcrafted_results,
            **learned_results,
        },
    }


def build_mujoco_minimal_closure_report(
    *,
    train_config: dict[str, Any],
    eval_reset_configs: dict[str, ResetConfig],
    handcrafted_results: dict[str, dict[str, Any]],
    learned_results: dict[str, dict[str, Any]],
    jam_config: dict[str, Any] | None = None,
    learned_policy_label: str = "learned_bc_ppo",
    oracle_policy_name: str = "variable_impedance",
    oracle_label: str = "oracle_reference",
) -> dict[str, Any]:
    results: dict[str, dict[str, Any]] = {}
    for eval_label, reset_config in eval_reset_configs.items():
        handcrafted_group = handcrafted_results[eval_label]
        if oracle_policy_name not in handcrafted_group:
            raise ValueError(
                f"Unknown oracle_policy_name '{oracle_policy_name}' for eval label '{eval_label}'"
            )
        results[eval_label] = {
            "pose_only": handcrafted_group["pose_only"],
            "fixed_impedance": handcrafted_group["fixed_impedance"],
            oracle_label: handcrafted_group[oracle_policy_name],
            learned_policy_label: learned_results[eval_label],
        }
    report = {
        "train_config": train_config,
        "eval_reset_suites": {
            label: asdict(reset_config) for label, reset_config in eval_reset_configs.items()
        },
        "results": results,
    }
    if jam_config is not None:
        report["jam_config"] = jam_config
    return report


def write_benchmark_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
