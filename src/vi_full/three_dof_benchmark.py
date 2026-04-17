from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import numpy as np

from vi_full.training import VecNormalizePredictor
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_config import ThreeDoFInsertionConfig
from vi_full.three_dof_env import ThreeDoFInsertionEnv
from vi_full.three_dof_policies import (
    build_3dof_handcrafted_policy_registry,
    resolve_3dof_teacher_spec,
)
from vi_full.three_dof_profiles import (
    DEFAULT_UNCERTAINTY_PROFILES,
    build_3dof_profile_config,
)
from vi_full.three_dof_training import (
    ThreeDoFPPOTrainConfig,
    build_3dof_coverage_collapse_reset_config,
    build_3dof_factorized_train_config,
    build_3dof_fixed_impedance_env_overrides,
    build_3dof_mainline_train_config,
    build_3dof_old_contact_env_overrides,
    build_3dof_training_budget_snapshot,
    collect_3dof_bc_demo_dataset_audit,
    infer_3dof_reset_coverage_label,
    serialize_3dof_train_config,
    train_3dof_ppo_agent,
)

THREE_DOF_NUMERIC_METRICS = (
    "success_rate",
    "mean_episode_return",
    "mean_final_distance",
    "mean_episode_length",
    "mean_peak_contact_force",
    "p95_peak_contact_force",
    "mean_force_std",
    "mean_first_contact_step",
    "mean_contact_steps",
    "mean_settling_steps_after_contact",
    "jam_rate",
)

CONTACT_THRESHOLD_N = 0.05
SETTLING_FORCE_STD_THRESHOLD = 0.12
SETTLING_DISTANCE_THRESHOLD_M = 0.0015


def trace_3dof_policy_rollout(
    env: ThreeDoFInsertionEnv,
    policy,
    *,
    seed: int = 0,
) -> list[dict[str, float | bool | int]]:
    return _trace_3dof_rollout(
        env,
        act_fn=policy.act,
        seed=seed,
    )


def trace_3dof_predictor_rollout(
    env: ThreeDoFInsertionEnv,
    predictor,
    *,
    seed: int = 0,
) -> list[dict[str, float | bool | int]]:
    def _act(observation: np.ndarray) -> np.ndarray:
        action, _ = predictor.predict(observation, deterministic=True)
        return np.asarray(action, dtype=np.float32)

    return _trace_3dof_rollout(env, act_fn=_act, seed=seed)


def _trace_3dof_rollout(
    env: ThreeDoFInsertionEnv,
    *,
    act_fn: Callable[[np.ndarray], np.ndarray],
    seed: int,
) -> list[dict[str, float | bool | int]]:
    observation, _ = env.reset(seed=seed)
    terminated = False
    truncated = False
    trace: list[dict[str, float | bool | int]] = []

    while not (terminated or truncated):
        action = np.asarray(act_fn(observation), dtype=np.float32)
        observation, reward, terminated, truncated, info = env.step(action)
        xy_error = float(np.linalg.norm(np.asarray(observation[:2], dtype=np.float64)))
        surface_height = float(max(observation[2] + env.target_position[2], 0.0))
        trace.append(
            {
                "step": int(len(trace) + 1),
                "xy_error": xy_error,
                "surface_height": surface_height,
                "insertion_depth": float(env._insertion_depth()),
                "distance_to_target": float(info["distance_to_target"]),
                "contact_force_norm": float(info["contact_force_norm"]),
                "action_dx": float(action[0]),
                "action_dy": float(action[1]),
                "action_dz": float(action[2]),
                "action_k_xy": float(action[3]),
                "action_k_z": float(action[4]),
                "decoded_k_xy": float(info["decoded_k_xy"]),
                "decoded_k_z": float(info["decoded_k_z"]),
                "wall_contact_force_norm": float(info["wall_contact_force_norm"]),
                "bottom_contact_force_norm": float(info["bottom_contact_force_norm"]),
                "approx_normal_force_norm": float(info["approx_normal_force_norm"]),
                "approx_tangential_force_norm": float(
                    info["approx_tangential_force_norm"]
                ),
                "contact_work_increment": float(info["contact_work_increment"]),
                "cumulative_contact_work": float(info["cumulative_contact_work"]),
                "contact_impulse_increment": float(info["contact_impulse_increment"]),
                "cumulative_contact_impulse": float(
                    info["cumulative_contact_impulse"]
                ),
                "contact_phase_label": str(info["contact_phase_label"]),
                "phase_action_bias_applied": bool(
                    info["action_modifiers"]["phase_action_bias_applied"]
                ),
                "approach_alignment_projection_applied": bool(
                    info["action_modifiers"]["approach_alignment_projection_applied"]
                ),
                "contact_intent_projection_applied": bool(
                    info["action_modifiers"]["contact_intent_projection_applied"]
                ),
                "in_approach_alignment_corridor": bool(
                    env.config.contact_intent_trigger_height_m < surface_height
                    <= env.config.approach_alignment_trigger_height_m
                    and xy_error <= env.config.approach_alignment_trigger_xy_threshold_m
                    and float(info["contact_force_norm"]) <= CONTACT_THRESHOLD_N
                ),
                "in_contact_intent_corridor": bool(
                    surface_height <= env.config.contact_intent_trigger_height_m
                    and xy_error <= env.config.contact_intent_trigger_xy_threshold_m
                    and float(info["contact_force_norm"]) <= CONTACT_THRESHOLD_N
                ),
                "below_near_contact_height": bool(
                    surface_height <= env.config.near_contact_height_m
                ),
                "reward": float(reward),
                "terminated": bool(terminated),
                "truncated": bool(truncated),
                "is_success": bool(info["is_success"]),
                "is_jammed": bool(info["is_jammed"]),
            }
        )
    return trace


def summarize_3dof_rollout_trace(
    trace: list[dict[str, float | bool | int]],
) -> dict[str, float | bool | int]:
    if not trace:
        raise ValueError("trace must not be empty")

    best_xy_step = min(trace, key=lambda item: float(item["xy_error"]))
    best_surface_step = min(trace, key=lambda item: float(item["surface_height"]))
    action_xy_norms = [
        float(np.linalg.norm([float(step["action_dx"]), float(step["action_dy"])]))
        for step in trace
    ]
    return {
        "num_steps": len(trace),
        "min_xy_error": float(best_xy_step["xy_error"]),
        "surface_height_at_best_xy_error": float(best_xy_step["surface_height"]),
        "min_surface_height": float(best_surface_step["surface_height"]),
        "xy_error_at_best_surface_height": float(best_surface_step["xy_error"]),
        "min_distance_to_target": float(
            min(float(step["distance_to_target"]) for step in trace)
        ),
        "steps_with_phase_action_bias": int(
            sum(bool(step["phase_action_bias_applied"]) for step in trace)
        ),
        "steps_with_approach_alignment_projection": int(
            sum(bool(step["approach_alignment_projection_applied"]) for step in trace)
        ),
        "steps_with_contact_intent_projection": int(
            sum(bool(step["contact_intent_projection_applied"]) for step in trace)
        ),
        "steps_in_approach_alignment_corridor": int(
            sum(bool(step["in_approach_alignment_corridor"]) for step in trace)
        ),
        "steps_in_contact_intent_corridor": int(
            sum(bool(step["in_contact_intent_corridor"]) for step in trace)
        ),
        "entered_contact_intent_corridor": bool(
            any(bool(step["in_contact_intent_corridor"]) for step in trace)
        ),
        "steps_below_near_contact_height": int(
            sum(bool(step["below_near_contact_height"]) for step in trace)
        ),
        "steps_with_contact": int(
            sum(float(step["contact_force_norm"]) > CONTACT_THRESHOLD_N for step in trace)
        ),
        "mean_action_xy_norm": float(np.mean(action_xy_norms)),
        "mean_action_dz": float(np.mean([float(step["action_dz"]) for step in trace])),
        "mean_action_k_xy": float(np.mean([float(step["action_k_xy"]) for step in trace])),
        "mean_action_k_z": float(np.mean([float(step["action_k_z"]) for step in trace])),
    }


def summarize_3dof_seed_runs(run_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    if not run_summaries:
        raise ValueError("run_summaries must not be empty")

    aggregate: dict[str, Any] = {
        "policy_name": run_summaries[0]["policy_name"],
        "uncertainty_profile": run_summaries[0]["uncertainty_profile"],
        "num_seeds": len(run_summaries),
        "seeds": [int(summary["seed"]) for summary in run_summaries],
    }
    for metric in THREE_DOF_NUMERIC_METRICS:
        values = np.asarray([summary[metric] for summary in run_summaries], dtype=np.float64)
        aggregate[f"{metric}_mean"] = float(np.mean(values))
        aggregate[f"{metric}_std"] = float(np.std(values))
    return aggregate


def evaluate_3dof_policy(
    env: ThreeDoFInsertionEnv,
    policy,
    *,
    episodes: int = 5,
    seed: int = 0,
    uncertainty_profile: str = "nominal",
) -> dict[str, float | int | str]:
    episode_returns: list[float] = []
    final_distances: list[float] = []
    successes: list[float] = []
    episode_lengths: list[int] = []
    peak_contact_forces: list[float] = []
    mean_force_stds: list[float] = []
    first_contact_steps: list[float] = []
    contact_steps_per_episode: list[float] = []
    settling_steps_after_contact: list[float] = []
    jam_flags: list[float] = []

    for episode_index in range(episodes):
        observation, _ = env.reset(seed=seed + episode_index)
        terminated = False
        truncated = False
        total_return = 0.0
        step_count = 0
        final_info: dict[str, Any] = {}
        episode_peak_contact_force = 0.0
        jammed = False
        force_std_trace: list[float] = []
        first_contact_step: int | None = None
        settling_delay: int | None = None
        contact_steps = 0

        while not (terminated or truncated):
            action = policy.act(observation)
            observation, reward, terminated, truncated, final_info = env.step(action)
            total_return += float(reward)
            step_count += 1

            force_norm = float(final_info["contact_force_norm"])
            force_std = float(final_info["force_std"])
            distance_to_target = float(final_info["distance_to_target"])
            episode_peak_contact_force = max(
                episode_peak_contact_force, float(final_info["peak_contact_force"])
            )
            jammed = jammed or bool(final_info["is_jammed"])

            if force_norm > CONTACT_THRESHOLD_N:
                contact_steps += 1
                force_std_trace.append(force_std)
                if first_contact_step is None:
                    first_contact_step = step_count
            if (
                first_contact_step is not None
                and settling_delay is None
                and force_std <= SETTLING_FORCE_STD_THRESHOLD
                and distance_to_target <= SETTLING_DISTANCE_THRESHOLD_M
                and not bool(final_info["is_jammed"])
            ):
                settling_delay = step_count - first_contact_step

        episode_returns.append(total_return)
        episode_lengths.append(step_count)
        final_distances.append(float(final_info["distance_to_target"]))
        successes.append(float(bool(final_info["is_success"])))
        peak_contact_forces.append(episode_peak_contact_force)
        jam_flags.append(float(jammed))
        mean_force_stds.append(
            float(np.mean(force_std_trace)) if force_std_trace else 0.0
        )
        first_contact_steps.append(
            float(first_contact_step) if first_contact_step is not None else float(step_count)
        )
        contact_steps_per_episode.append(float(contact_steps))
        settling_steps_after_contact.append(
            float(settling_delay)
            if settling_delay is not None
            else float(max(step_count - (first_contact_step or step_count), 0))
        )

    return {
        "policy_name": getattr(policy, "name", policy.__class__.__name__),
        "uncertainty_profile": uncertainty_profile,
        "episodes": episodes,
        "success_rate": float(np.mean(successes)),
        "mean_episode_return": float(np.mean(episode_returns)),
        "mean_final_distance": float(np.mean(final_distances)),
        "mean_episode_length": float(np.mean(episode_lengths)),
        "mean_peak_contact_force": float(np.mean(peak_contact_forces)),
        "p95_peak_contact_force": float(np.percentile(peak_contact_forces, 95)),
        "mean_force_std": float(np.mean(mean_force_stds)),
        "mean_first_contact_step": float(np.mean(first_contact_steps)),
        "mean_contact_steps": float(np.mean(contact_steps_per_episode)),
        "mean_settling_steps_after_contact": float(np.mean(settling_steps_after_contact)),
        "jam_rate": float(np.mean(jam_flags)),
    }


def run_3dof_handcrafted_uncertainty_suite(
    *,
    seeds: list[int],
    episodes_per_seed: int = 5,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    uncertainty_profiles: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    profiles = uncertainty_profiles or list(DEFAULT_UNCERTAINTY_PROFILES)
    policy_factories = build_3dof_handcrafted_policy_registry()
    results: dict[str, dict[str, Any]] = {}
    for profile_name in profiles:
        config = build_3dof_profile_config(
            profile_name,
            max_episode_steps=max_episode_steps,
        )
        profile_results: dict[str, Any] = {}
        for policy_name, factory in policy_factories.items():
            per_seed: list[dict[str, Any]] = []
            for seed in seeds:
                env = ThreeDoFInsertionEnv(config)
                try:
                    summary = evaluate_3dof_policy(
                        env,
                        factory(),
                        episodes=episodes_per_seed,
                        seed=seed,
                        uncertainty_profile=profile_name,
                    )
                finally:
                    env.close()
                summary["seed"] = seed
                per_seed.append(summary)
            profile_results[policy_name] = {
                "per_seed": per_seed,
                "aggregate": summarize_3dof_seed_runs(per_seed),
            }
        results[profile_name] = profile_results
    return results


def evaluate_3dof_predictor(
    env: ThreeDoFInsertionEnv,
    predictor,
    *,
    episodes: int = 5,
    seed: int = 0,
    uncertainty_profile: str = "nominal",
) -> dict[str, float | int | str]:
    class _PredictorPolicy:
        name = getattr(predictor, "name", predictor.__class__.__name__)

        def act(self, observation: np.ndarray) -> np.ndarray:
            action, _ = predictor.predict(observation, deterministic=True)
            return np.asarray(action, dtype=np.float32)

    return evaluate_3dof_policy(
        env,
        _PredictorPolicy(),
        episodes=episodes,
        seed=seed,
        uncertainty_profile=uncertainty_profile,
    )


def _make_3dof_eval_env_with_reset_config(
    train_config: ThreeDoFPPOTrainConfig,
    *,
    reset_config,
    uncertainty_profile: str,
) -> ThreeDoFInsertionEnv:
    return ThreeDoFInsertionEnv(
        replace(
            build_3dof_profile_config(
                uncertainty_profile,
                max_episode_steps=train_config.max_episode_steps,
            ),
            **train_config.base_env_overrides,
            reset_config=reset_config,
        )
    )


def run_3dof_bc_reset_gap_audit(
    *,
    seed: int = 0,
    total_timesteps: int = 0,
    episodes: int = 5,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    train_uncertainty_profile: str = "nominal",
    eval_uncertainty_profile: str = "nominal",
    bc_rollout_episodes: int = 2,
    bc_pretrain_steps: int = 2,
    bc_batch_size: int = 32,
    bc_demo_policy_name: str = "variable_impedance",
) -> dict[str, Any]:
    train_config = build_3dof_mainline_train_config(
        seed=seed,
        total_timesteps=total_timesteps,
        max_episode_steps=max_episode_steps,
        train_uncertainty_profile=train_uncertainty_profile,
        eval_uncertainty_profile=eval_uncertainty_profile,
        n_envs=1,
        n_steps=min(64, max(total_timesteps, 16)),
        batch_size=min(64, max(total_timesteps, 16)),
        n_epochs=1,
        learning_rate=1e-4,
        gamma=0.95,
        verbose=0,
        bc_rollout_episodes=bc_rollout_episodes,
        bc_pretrain_steps=bc_pretrain_steps,
        bc_batch_size=bc_batch_size,
        bc_demo_policy_name=bc_demo_policy_name,
    )
    artifacts = train_3dof_ppo_agent(train_config)
    predictor = VecNormalizePredictor(
        model=artifacts.model,
        vec_normalize=artifacts.vec_normalize,
    )
    eval_conditions = {
        "bc_reset": train_config.bc_reset_config,
        "hard_eval": ThreeDoFInsertionConfig().reset_config,
    }
    evaluations: dict[str, Any] = {}
    for condition_name, reset_config in eval_conditions.items():
        env = _make_3dof_eval_env_with_reset_config(
            train_config,
            reset_config=reset_config,
            uncertainty_profile=eval_uncertainty_profile,
        )
        try:
            summary = evaluate_3dof_predictor(
                env,
                predictor,
                episodes=episodes,
                seed=seed + 10_000,
                uncertainty_profile=eval_uncertainty_profile,
            )
        finally:
            env.close()

        trace_env = _make_3dof_eval_env_with_reset_config(
            train_config,
            reset_config=reset_config,
            uncertainty_profile=eval_uncertainty_profile,
        )
        try:
            trace = trace_3dof_predictor_rollout(
                trace_env,
                predictor,
                seed=seed + 20_000,
            )
            trace_summary = summarize_3dof_rollout_trace(trace)
        finally:
            trace_env.close()

        evaluations[condition_name] = {
            "reset_config": asdict(reset_config),
            "reset_stage_count": len(reset_config.curriculum_stages),
            "touches_contact": bool(float(summary["mean_contact_steps"]) > 0.0),
            "summary": summary,
            "trace_summary": trace_summary,
        }

    bc_reset_summary = evaluations["bc_reset"]["summary"]
    hard_eval_summary = evaluations["hard_eval"]["summary"]
    bc_reset_trace_summary = evaluations["bc_reset"]["trace_summary"]
    hard_eval_trace_summary = evaluations["hard_eval"]["trace_summary"]
    return {
        "train_config": {
            "seed": seed,
            "total_timesteps": total_timesteps,
            "episodes": episodes,
            "max_episode_steps": max_episode_steps,
            "train_uncertainty_profile": train_uncertainty_profile,
            "eval_uncertainty_profile": eval_uncertainty_profile,
            "bc_rollout_episodes": bc_rollout_episodes,
            "bc_pretrain_steps": bc_pretrain_steps,
            "bc_batch_size": bc_batch_size,
            "bc_demo_policy_name": bc_demo_policy_name,
        },
        "evaluations": evaluations,
        "gap_summary": {
            "mean_contact_steps_delta_bc_reset_minus_hard_eval": float(
                bc_reset_summary["mean_contact_steps"] - hard_eval_summary["mean_contact_steps"]
            ),
            "mean_final_distance_delta_bc_reset_minus_hard_eval": float(
                bc_reset_summary["mean_final_distance"]
                - hard_eval_summary["mean_final_distance"]
            ),
            "mean_first_contact_step_delta_bc_reset_minus_hard_eval": float(
                bc_reset_summary["mean_first_contact_step"]
                - hard_eval_summary["mean_first_contact_step"]
            ),
            "trace_steps_with_contact_delta_bc_reset_minus_hard_eval": int(
                bc_reset_trace_summary["steps_with_contact"]
                - hard_eval_trace_summary["steps_with_contact"]
            ),
            "trace_steps_below_near_contact_height_delta_bc_reset_minus_hard_eval": int(
                bc_reset_trace_summary["steps_below_near_contact_height"]
                - hard_eval_trace_summary["steps_below_near_contact_height"]
            ),
            "trace_entered_contact_intent_corridor_bc_reset": bool(
                bc_reset_trace_summary["entered_contact_intent_corridor"]
            ),
            "trace_entered_contact_intent_corridor_hard_eval": bool(
                hard_eval_trace_summary["entered_contact_intent_corridor"]
            ),
        },
    }


def build_3dof_dapg_baseline_registry() -> dict[str, dict[str, Any]]:
    coverage_collapse_reset = build_3dof_coverage_collapse_reset_config()
    old_contact_overrides = build_3dof_old_contact_env_overrides()
    fixed_impedance_overrides = build_3dof_fixed_impedance_env_overrides()
    return {
        "ppo_no_bc": {
            "bc_rollout_episodes": 0,
            "bc_pretrain_steps": 0,
        },
        "bc_only": {
            "total_timesteps": 0,
            "bc_rollout_episodes": 8,
            "bc_pretrain_steps": 32,
            "bc_batch_size": 64,
        },
        "bc_only_stable_r32_p32": {
            "total_timesteps": 0,
            "bc_rollout_episodes": 32,
            "bc_pretrain_steps": 32,
            "bc_batch_size": 64,
        },
        "fixed_impedance_rl": {
            "bc_rollout_episodes": 0,
            "bc_pretrain_steps": 0,
            "base_env_overrides": fixed_impedance_overrides,
        },
        "fixed_impedance_rl_stable_r32_p32": {
            "bc_rollout_episodes": 32,
            "bc_pretrain_steps": 32,
            "bc_batch_size": 64,
            "base_env_overrides": fixed_impedance_overrides,
        },
        "repaired_mainline_bc_to_ppo": {},
        "teacher_variable_variable__repaired_mainline": {
            "bc_demo_policy_name": "teacher_variable_variable",
            "bc_demo_teacher_spec": resolve_3dof_teacher_spec(
                policy_name="teacher_variable_variable"
            ),
        },
        "teacher_variable_fixed__repaired_mainline": {
            "bc_demo_policy_name": "teacher_variable_fixed",
            "bc_demo_teacher_spec": resolve_3dof_teacher_spec(
                policy_name="teacher_variable_fixed"
            ),
        },
        "teacher_pose_variable__repaired_mainline": {
            "bc_demo_policy_name": "teacher_pose_variable",
            "bc_demo_teacher_spec": resolve_3dof_teacher_spec(
                policy_name="teacher_pose_variable"
            ),
        },
        "teacher_pose_fixed__repaired_mainline": {
            "bc_demo_policy_name": "teacher_pose_fixed",
            "bc_demo_teacher_spec": resolve_3dof_teacher_spec(
                policy_name="teacher_pose_fixed"
            ),
        },
        "dapg_lite_repaired_mainline": {
            "dapg_enabled": True,
        },
        "dapg_lite_contact_old__reset_coverage_collapse": {
            "dapg_enabled": True,
            "base_env_overrides": old_contact_overrides,
            "train_reset_config": coverage_collapse_reset,
            "bc_reset_config": coverage_collapse_reset,
        },
        "dapg_lite_contact_old__reset_repaired": {
            "dapg_enabled": True,
            "base_env_overrides": old_contact_overrides,
        },
        "dapg_lite_contact_new__reset_coverage_collapse": {
            "dapg_enabled": True,
            "train_reset_config": coverage_collapse_reset,
            "bc_reset_config": coverage_collapse_reset,
        },
        "dapg_lite_contact_new__reset_repaired": {
            "dapg_enabled": True,
        },
    }


def build_3dof_factor_sweep_registry() -> dict[str, dict[str, Any]]:
    return {
        "demonstration_coverage": {
            "manipulated_factor": "demonstration_coverage",
            "fixed_controls": {
                "reset_coverage": "reset_repaired",
                "bc_optimization_depth": 32,
                "bc_rollout_episodes": 8,
                "bc_batch_size": 64,
                "ppo_fine_tune_budget": 128,
            },
            "points": [
                {
                    "point_name": "reset_coverage_collapse",
                    "factor_value": "reset_coverage_collapse",
                    "demonstration_coverage": "reset_coverage_collapse",
                },
                {
                    "point_name": "reset_repaired",
                    "factor_value": "reset_repaired",
                    "demonstration_coverage": "reset_repaired",
                },
            ],
        },
        "reset_coverage": {
            "manipulated_factor": "reset_coverage",
            "fixed_controls": {
                "demonstration_coverage": "reset_repaired",
                "bc_optimization_depth": 32,
                "bc_rollout_episodes": 8,
                "bc_batch_size": 64,
                "ppo_fine_tune_budget": 128,
            },
            "points": [
                {
                    "point_name": "reset_coverage_collapse",
                    "factor_value": "reset_coverage_collapse",
                    "reset_coverage": "reset_coverage_collapse",
                },
                {
                    "point_name": "reset_repaired",
                    "factor_value": "reset_repaired",
                    "reset_coverage": "reset_repaired",
                },
            ],
        },
        "bc_optimization_depth": {
            "manipulated_factor": "bc_optimization_depth",
            "fixed_controls": {
                "demonstration_coverage": "reset_repaired",
                "reset_coverage": "reset_repaired",
                "bc_rollout_episodes": 8,
                "bc_batch_size": 64,
                "ppo_fine_tune_budget": 128,
            },
            "points": [
                {
                    "point_name": "bc_pretrain_steps_0",
                    "factor_value": 0,
                    "bc_pretrain_steps": 0,
                },
                {
                    "point_name": "bc_pretrain_steps_8",
                    "factor_value": 8,
                    "bc_pretrain_steps": 8,
                },
                {
                    "point_name": "bc_pretrain_steps_32",
                    "factor_value": 32,
                    "bc_pretrain_steps": 32,
                },
                {
                    "point_name": "bc_pretrain_steps_64",
                    "factor_value": 64,
                    "bc_pretrain_steps": 64,
                },
            ],
        },
        "ppo_fine_tune_budget": {
            "manipulated_factor": "ppo_fine_tune_budget",
            "fixed_controls": {
                "demonstration_coverage": "reset_repaired",
                "reset_coverage": "reset_repaired",
                "bc_optimization_depth": 32,
                "bc_rollout_episodes": 8,
                "bc_batch_size": 64,
            },
            "points": [
                {
                    "point_name": "ppo_total_timesteps_0",
                    "factor_value": 0,
                    "total_timesteps": 0,
                },
                {
                    "point_name": "ppo_total_timesteps_32",
                    "factor_value": 32,
                    "total_timesteps": 32,
                },
                {
                    "point_name": "ppo_total_timesteps_128",
                    "factor_value": 128,
                    "total_timesteps": 128,
                },
                {
                    "point_name": "ppo_total_timesteps_512",
                    "factor_value": 512,
                    "total_timesteps": 512,
                },
            ],
        },
    }


def build_3dof_algorithm_budget_comparison_registry() -> dict[str, Any]:
    return {
        "manipulated_factor": "ppo_fine_tune_budget",
        "budget_points": [0, 32, 128, 512],
        "budgeted_suites": [
            {"suite_name": "ppo_no_bc", "label": "PPO-only"},
            {
                "suite_name": "repaired_mainline_bc_to_ppo",
                "label": "BC -> PPO",
            },
            {
                "suite_name": "dapg_lite_repaired_mainline",
                "label": "DAPG-lite",
            },
        ],
        "static_anchors": [
            {
                "suite_name": "bc_only_stable_r32_p32",
                "label": "BC-only",
            },
        ],
    }


def build_3dof_ppo_large_budget_ablation_registry() -> dict[str, Any]:
    return {
        "experiment_name": "three_dof_ppo_large_budget_ablation",
        "budget_points": [50_000, 100_000, 200_000],
        "conditions": [
            {
                "condition_name": "ppo_only_paper_matched",
                "label": "PPO-only paper-matched",
                "train_overrides": {
                    "bc_rollout_episodes": 0,
                    "bc_pretrain_steps": 0,
                    "bc_batch_size": 64,
                    "n_envs": 1,
                    "n_steps": 64,
                    "batch_size": 64,
                    "n_epochs": 1,
                    "learning_rate": 1e-4,
                    "gamma": 0.95,
                    "gae_lambda": 0.95,
                    "ent_coef": 0.0,
                },
            },
            {
                "condition_name": "ppo_only_reviewer_fair",
                "label": "PPO-only reviewer-fair",
                "train_overrides": {
                    "bc_rollout_episodes": 0,
                    "bc_pretrain_steps": 0,
                    "bc_batch_size": 64,
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
        ],
    }


def _build_3dof_condition_train_config(
    *,
    seed: int,
    total_timesteps: int,
    max_episode_steps: int,
    train_uncertainty_profile: str,
    train_overrides: dict[str, Any] | None,
) -> ThreeDoFPPOTrainConfig:
    overrides = dict(train_overrides or {})
    base_config = build_3dof_mainline_train_config(
        seed=int(seed),
        total_timesteps=int(total_timesteps),
        max_episode_steps=int(max_episode_steps),
        train_uncertainty_profile=str(train_uncertainty_profile),
        eval_uncertainty_profile=str(train_uncertainty_profile),
        n_envs=int(overrides.pop("n_envs", 1)),
        n_steps=int(overrides.pop("n_steps", 64)),
        batch_size=int(overrides.pop("batch_size", 64)),
        n_epochs=int(overrides.pop("n_epochs", 1)),
        learning_rate=float(overrides.pop("learning_rate", 1e-4)),
        gamma=float(overrides.pop("gamma", 0.95)),
        verbose=int(overrides.pop("verbose", 0)),
        bc_rollout_episodes=int(overrides.pop("bc_rollout_episodes", 8)),
        bc_pretrain_steps=int(overrides.pop("bc_pretrain_steps", 32)),
        bc_batch_size=int(overrides.pop("bc_batch_size", 64)),
        bc_demo_policy_name=str(overrides.pop("bc_demo_policy_name", "variable_impedance")),
        bc_demo_teacher_spec=overrides.pop("bc_demo_teacher_spec", None),
    )
    if "base_env_overrides" in overrides:
        overrides["base_env_overrides"] = dict(overrides["base_env_overrides"])
    return replace(base_config, **overrides)


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


def run_3dof_condition_across_profiles(
    *,
    condition_name: str,
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
    first_train_config: ThreeDoFPPOTrainConfig | None = None

    for seed in train_seeds:
        train_config = _build_3dof_condition_train_config(
            seed=int(seed),
            total_timesteps=int(total_timesteps),
            max_episode_steps=int(max_episode_steps),
            train_uncertainty_profile=str(train_uncertainty_profile),
            train_overrides=train_overrides,
        )
        if first_train_config is None:
            first_train_config = train_config
        artifacts = train_3dof_ppo_agent(train_config)
        predictor = VecNormalizePredictor(
            model=artifacts.model,
            vec_normalize=artifacts.vec_normalize,
        )
        train_configs.append(serialize_3dof_train_config(train_config))
        training_summary = {"seed": int(seed), **dict(artifacts.training_summary)}
        training_summaries.append(training_summary)

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

    for profile_name, payload in per_profile_metrics.items():
        payload["aggregate"] = summarize_3dof_seed_runs(payload["per_seed"])
        payload["aggregate"]["condition_name"] = condition_name
        payload["aggregate"]["train_uncertainty_profile"] = train_uncertainty_profile
        payload["aggregate"]["eval_uncertainty_profile"] = profile_name

    if first_train_config is None:
        raise ValueError("train_seeds must contain at least one seed")

    return {
        "condition_name": condition_name,
        "factor_value": int(total_timesteps),
        "training_budget": build_3dof_training_budget_snapshot(first_train_config),
        "train_config_snapshot": serialize_3dof_train_config(first_train_config),
        "train_configs": train_configs,
        "training_summaries": training_summaries,
        "per_profile_metrics": per_profile_metrics,
        "five_profile_mean": _build_3dof_profile_mean(per_profile_metrics),
    }


def select_top_3dof_tuned_fixed_configs(
    candidates: list[dict[str, Any]],
    *,
    top_k: int = 1,
) -> list[dict[str, Any]]:
    def _selection_key(candidate: dict[str, Any]) -> tuple[float, float, float, float]:
        five_profile_mean = candidate.get("five_profile_mean", {})
        high_friction = (
            candidate.get("per_profile_metrics", {})
            .get("high_friction", {})
            .get("aggregate", {})
        )
        return (
            -float(five_profile_mean.get("success_rate_mean_over_profiles", 0.0)),
            -float(high_friction.get("success_rate_mean", 0.0)),
            float(
                five_profile_mean.get(
                    "mean_peak_contact_force_mean_over_profiles",
                    float("inf"),
                )
            ),
            float(
                five_profile_mean.get(
                    "mean_final_distance_mean_over_profiles",
                    float("inf"),
                )
            ),
        )

    selected: list[dict[str, Any]] = []
    for rank, candidate in enumerate(sorted(candidates, key=_selection_key)[:top_k], start=1):
        ranked_candidate = dict(candidate)
        ranked_candidate["selection_rank"] = int(rank)
        selected.append(ranked_candidate)
    return selected


def _build_3dof_registry_suite_train_config(
    *,
    suite_name: str,
    seed: int,
    total_timesteps: int,
    max_episode_steps: int,
    train_uncertainty_profile: str = "nominal",
    eval_uncertainty_profile: str = "nominal",
    bc_rollout_episodes: int = 8,
    bc_pretrain_steps: int = 32,
    bc_batch_size: int = 64,
    bc_demo_policy_name: str = "variable_impedance",
) -> ThreeDoFPPOTrainConfig:
    registry = build_3dof_dapg_baseline_registry()
    if suite_name not in registry:
        raise ValueError(f"Unknown 3DoF registry suite: {suite_name}")

    suite_overrides = dict(registry[suite_name])
    effective_total_timesteps = int(suite_overrides.pop("total_timesteps", total_timesteps))
    base_config = build_3dof_mainline_train_config(
        seed=seed,
        total_timesteps=effective_total_timesteps,
        max_episode_steps=max_episode_steps,
        train_uncertainty_profile=train_uncertainty_profile,
        eval_uncertainty_profile=eval_uncertainty_profile,
        n_envs=1,
        n_steps=min(64, max(effective_total_timesteps, 16)),
        batch_size=min(64, max(effective_total_timesteps, 16)),
        n_epochs=1,
        learning_rate=1e-4,
        gamma=0.95,
        verbose=0,
        bc_rollout_episodes=bc_rollout_episodes,
        bc_pretrain_steps=bc_pretrain_steps,
        bc_batch_size=bc_batch_size,
        bc_demo_policy_name=bc_demo_policy_name,
    )
    if "base_env_overrides" in suite_overrides:
        suite_overrides["base_env_overrides"] = dict(suite_overrides["base_env_overrides"])
    return replace(base_config, **suite_overrides)


def _run_3dof_registry_suite_across_profiles(
    *,
    suite_name: str,
    train_seeds: list[int],
    episodes_per_seed: int,
    max_episode_steps: int,
    uncertainty_profiles: list[str],
    total_timesteps: int,
) -> dict[str, Any]:
    registry = build_3dof_dapg_baseline_registry()
    suite_kwargs = dict(registry[suite_name])
    effective_total_timesteps = int(suite_kwargs.pop("total_timesteps", total_timesteps))
    train_config = _build_3dof_registry_suite_train_config(
        suite_name=suite_name,
        seed=train_seeds[0],
        total_timesteps=total_timesteps,
        max_episode_steps=max_episode_steps,
    )
    per_profile_metrics: dict[str, Any] = {}
    for profile_name in uncertainty_profiles:
        run_kwargs = {
            "seeds": train_seeds,
            "total_timesteps": effective_total_timesteps,
            "episodes_per_seed": episodes_per_seed,
            "max_episode_steps": max_episode_steps,
            "suite_name": suite_name,
            "train_uncertainty_profile": "nominal",
            "eval_uncertainty_profile": profile_name,
        }
        run_kwargs.update(suite_kwargs)
        per_profile_metrics[profile_name] = run_3dof_learned_suite(**run_kwargs)
    return {
        "suite_name": suite_name,
        "factor_value": int(effective_total_timesteps),
        "training_budget": build_3dof_training_budget_snapshot(train_config),
        "train_config_snapshot": serialize_3dof_train_config(train_config),
        "per_profile_metrics": per_profile_metrics,
    }


def run_3dof_algorithm_budget_comparison(
    *,
    train_seeds: list[int],
    episodes_per_seed: int = 5,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    uncertainty_profiles: list[str] | None = None,
    budget_points: list[int] | None = None,
) -> dict[str, Any]:
    registry = build_3dof_algorithm_budget_comparison_registry()
    profiles = uncertainty_profiles or list(DEFAULT_UNCERTAINTY_PROFILES)
    budgets = list(budget_points or registry["budget_points"])
    budgeted_suites: list[dict[str, Any]] = []

    for suite_spec in registry["budgeted_suites"]:
        suite_points = [
            {
                "point_name": f"ppo_total_timesteps_{budget}",
                **_run_3dof_registry_suite_across_profiles(
                    suite_name=suite_spec["suite_name"],
                    train_seeds=train_seeds,
                    episodes_per_seed=episodes_per_seed,
                    max_episode_steps=max_episode_steps,
                    uncertainty_profiles=profiles,
                    total_timesteps=int(budget),
                ),
            }
            for budget in budgets
        ]
        budgeted_suites.append(
            {
                "suite_name": suite_spec["suite_name"],
                "label": suite_spec["label"],
                "points": suite_points,
            }
        )

    static_anchors = [
        {
            "label": suite_spec["label"],
            **_run_3dof_registry_suite_across_profiles(
                suite_name=suite_spec["suite_name"],
                train_seeds=train_seeds,
                episodes_per_seed=episodes_per_seed,
                max_episode_steps=max_episode_steps,
                uncertainty_profiles=profiles,
                total_timesteps=0,
            ),
        }
        for suite_spec in registry["static_anchors"]
    ]

    return {
        "comparison_name": "three_dof_algorithm_budget_comparison",
        "manipulated_factor": registry["manipulated_factor"],
        "budget_points": budgets,
        "seed_list": list(train_seeds),
        "uncertainty_profiles": profiles,
        "episodes_per_seed": int(episodes_per_seed),
        "max_episode_steps": int(max_episode_steps),
        "budgeted_suites": budgeted_suites,
        "static_anchors": static_anchors,
    }


def run_3dof_factor_sweep_suite(
    *,
    sweep_name: str,
    train_seeds: list[int],
    episodes_per_seed: int = 5,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    uncertainty_profiles: list[str] | None = None,
) -> dict[str, Any]:
    registry = build_3dof_factor_sweep_registry()
    if sweep_name not in registry:
        raise ValueError(f"Unknown 3DoF factor sweep: {sweep_name}")

    sweep_spec = registry[sweep_name]
    profiles = uncertainty_profiles or list(DEFAULT_UNCERTAINTY_PROFILES)
    fixed_controls = dict(sweep_spec["fixed_controls"])
    points: list[dict[str, Any]] = []

    for point in sweep_spec["points"]:
        demonstration_coverage = point.get(
            "demonstration_coverage",
            fixed_controls.get("demonstration_coverage", "reset_repaired"),
        )
        reset_coverage = point.get(
            "reset_coverage",
            fixed_controls.get("reset_coverage", "reset_repaired"),
        )
        bc_rollout_episodes = int(
            point.get("bc_rollout_episodes", fixed_controls["bc_rollout_episodes"])
        )
        bc_pretrain_steps = int(
            point.get(
                "bc_pretrain_steps",
                fixed_controls.get("bc_optimization_depth", 32),
            )
        )
        bc_batch_size = int(point.get("bc_batch_size", fixed_controls["bc_batch_size"]))
        total_timesteps = int(
            point.get(
                "total_timesteps",
                fixed_controls.get("ppo_fine_tune_budget", 128),
            )
        )
        train_config = build_3dof_factorized_train_config(
            seed=train_seeds[0],
            total_timesteps=total_timesteps,
            bc_rollout_episodes=bc_rollout_episodes,
            bc_pretrain_steps=bc_pretrain_steps,
            bc_batch_size=bc_batch_size,
            demonstration_coverage=str(demonstration_coverage),
            reset_coverage=str(reset_coverage),
            max_episode_steps=max_episode_steps,
        )
        train_config_snapshot = serialize_3dof_train_config(train_config)
        per_profile_metrics: dict[str, Any] = {}
        for profile_name in profiles:
            per_profile_metrics[profile_name] = run_3dof_learned_suite(
                seeds=train_seeds,
                total_timesteps=total_timesteps,
                episodes_per_seed=episodes_per_seed,
                max_episode_steps=max_episode_steps,
                suite_name=f"factor_sweep__{sweep_name}__{point['point_name']}",
                train_uncertainty_profile="nominal",
                eval_uncertainty_profile=profile_name,
                bc_rollout_episodes=bc_rollout_episodes,
                bc_pretrain_steps=bc_pretrain_steps,
                bc_batch_size=bc_batch_size,
                train_reset_config=train_config.train_reset_config,
                bc_reset_config=train_config.bc_reset_config,
            )
        points.append(
            {
                "point_name": point["point_name"],
                "factor_value": point["factor_value"],
                "demonstration_coverage": infer_3dof_reset_coverage_label(
                    train_config.bc_reset_config
                ),
                "reset_coverage": infer_3dof_reset_coverage_label(
                    train_config.train_reset_config
                ),
                "training_budget": build_3dof_training_budget_snapshot(train_config),
                "train_config_snapshot": train_config_snapshot,
                "per_profile_metrics": per_profile_metrics,
            }
        )

    return {
        "sweep_name": sweep_name,
        "manipulated_factor": sweep_spec["manipulated_factor"],
        "fixed_controls": fixed_controls,
        "seed_list": list(train_seeds),
        "uncertainty_profiles": profiles,
        "episodes_per_seed": int(episodes_per_seed),
        "max_episode_steps": int(max_episode_steps),
        "points": points,
    }


def run_3dof_bc_seed_factorization_suite(
    *,
    init_seeds: list[int],
    demo_seeds: list[int],
    eval_seeds: list[int],
    episodes_per_eval_seed: int = 50,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    uncertainty_profiles: list[str] | None = None,
    coverage_condition: str = "reset_repaired",
    bc_rollout_episodes: int = 8,
    bc_pretrain_steps: int = 32,
    bc_batch_size: int = 64,
    bc_demo_policy_name: str = "variable_impedance",
) -> dict[str, Any]:
    profiles = uncertainty_profiles or list(DEFAULT_UNCERTAINTY_PROFILES)
    results: dict[str, Any] = {}

    for init_seed in init_seeds:
        for demo_seed in demo_seeds:
            condition_name = f"init_{init_seed}__demo_{demo_seed}"
            train_config = build_3dof_factorized_train_config(
                seed=init_seed,
                demo_seed=demo_seed,
                total_timesteps=0,
                max_episode_steps=max_episode_steps,
                bc_rollout_episodes=bc_rollout_episodes,
                bc_pretrain_steps=bc_pretrain_steps,
                bc_batch_size=bc_batch_size,
                demonstration_coverage=coverage_condition,
                reset_coverage="reset_repaired",
                bc_demo_policy_name=bc_demo_policy_name,
            )
            demo_audit = collect_3dof_bc_demo_dataset_audit(
                train_config,
                episodes=bc_rollout_episodes,
            )
            artifacts = train_3dof_ppo_agent(train_config)
            predictor = VecNormalizePredictor(
                model=artifacts.model,
                vec_normalize=artifacts.vec_normalize,
            )
            condition_eval_results: dict[str, Any] = {}
            for profile_name in profiles:
                per_seed: list[dict[str, Any]] = []
                for eval_seed in eval_seeds:
                    env = artifacts.make_eval_env(uncertainty_profile=profile_name)
                    try:
                        summary = evaluate_3dof_predictor(
                            env,
                            predictor,
                            episodes=episodes_per_eval_seed,
                            seed=eval_seed,
                            uncertainty_profile=profile_name,
                        )
                    finally:
                        env.close()
                    summary["seed"] = eval_seed
                    per_seed.append(summary)
                condition_eval_results[profile_name] = {
                    "per_seed": per_seed,
                    "aggregate": summarize_3dof_seed_runs(per_seed),
                }
            results[condition_name] = {
                "factor_values": {
                    "init_seed": int(init_seed),
                    "demo_seed": int(demo_seed),
                    "coverage_condition": infer_3dof_reset_coverage_label(
                        train_config.bc_reset_config
                    ),
                    "training_budget": build_3dof_training_budget_snapshot(train_config),
                },
                "train_config": serialize_3dof_train_config(train_config),
                "training_summary": dict(artifacts.training_summary),
                "demo_audit": demo_audit,
                "eval_results": condition_eval_results,
            }

    return {
        "config": {
            "train_mode": "bc_only",
            "init_seeds": init_seeds,
            "demo_seeds": demo_seeds,
            "eval_seeds": eval_seeds,
            "episodes_per_eval_seed": episodes_per_eval_seed,
            "max_episode_steps": max_episode_steps,
            "uncertainty_profiles": profiles,
            "coverage_condition": coverage_condition,
            "training_budget": {
                "total_timesteps": 0,
                "bc_rollout_episodes": bc_rollout_episodes,
                "bc_pretrain_steps": bc_pretrain_steps,
                "bc_batch_size": bc_batch_size,
            },
            "bc_rollout_episodes": bc_rollout_episodes,
            "bc_pretrain_steps": bc_pretrain_steps,
            "bc_batch_size": bc_batch_size,
            "bc_demo_policy_name": bc_demo_policy_name,
        },
        "results": results,
    }


def run_3dof_learned_suite(
    *,
    seeds: list[int],
    total_timesteps: int = 256,
    episodes_per_seed: int = 5,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    suite_name: str = "learned_ppo_3dof",
    train_uncertainty_profile: str = "nominal",
    eval_uncertainty_profile: str = "nominal",
    bc_rollout_episodes: int = 8,
    bc_pretrain_steps: int = 32,
    bc_batch_size: int = 64,
    bc_demo_policy_name: str = "variable_impedance",
    approach_bc_rollout_episodes: int = 0,
    approach_bc_pretrain_steps: int = 0,
    contact_bc_rollout_episodes: int = 0,
    contact_bc_pretrain_steps: int = 0,
    contact_bc_freeze_pose_head: bool = False,
    contact_bc_after_finetune: bool = False,
    contact_finetune_timesteps: int = 0,
    contact_finetune_anchor_rollout_episodes: int = 0,
    contact_finetune_anchor_bc_steps: int = 0,
    contact_finetune_anchor_interval_timesteps: int = 0,
    base_env_overrides: dict[str, Any] | None = None,
    train_reset_config=None,
    bc_reset_config=None,
    dapg_enabled: bool = False,
    dapg_mini_updates_per_chunk: int = 1,
    dapg_demo_batch_size: int = 64,
) -> dict[str, Any]:
    per_seed: list[dict[str, Any]] = []
    for seed in seeds:
        train_config = build_3dof_mainline_train_config(
            seed=seed,
            total_timesteps=total_timesteps,
            max_episode_steps=max_episode_steps,
            train_uncertainty_profile=train_uncertainty_profile,
            eval_uncertainty_profile=eval_uncertainty_profile,
            n_envs=1,
            n_steps=min(64, max(total_timesteps, 16)),
            batch_size=min(64, max(total_timesteps, 16)),
            n_epochs=1,
            learning_rate=1e-4,
            gamma=0.95,
            verbose=0,
            bc_rollout_episodes=bc_rollout_episodes,
            bc_pretrain_steps=bc_pretrain_steps,
            bc_batch_size=bc_batch_size,
            bc_demo_policy_name=bc_demo_policy_name,
        )
        train_config = replace(
            train_config,
            approach_bc_rollout_episodes=approach_bc_rollout_episodes,
            approach_bc_pretrain_steps=approach_bc_pretrain_steps,
            contact_bc_rollout_episodes=contact_bc_rollout_episodes,
            contact_bc_pretrain_steps=contact_bc_pretrain_steps,
            contact_bc_freeze_pose_head=contact_bc_freeze_pose_head,
            contact_bc_after_finetune=contact_bc_after_finetune,
            contact_finetune_timesteps=contact_finetune_timesteps,
            contact_finetune_anchor_rollout_episodes=(
                contact_finetune_anchor_rollout_episodes
            ),
            contact_finetune_anchor_bc_steps=contact_finetune_anchor_bc_steps,
            contact_finetune_anchor_interval_timesteps=(
                contact_finetune_anchor_interval_timesteps
            ),
            base_env_overrides=dict(base_env_overrides or {}),
            dapg_enabled=dapg_enabled,
            dapg_mini_updates_per_chunk=dapg_mini_updates_per_chunk,
            dapg_demo_batch_size=dapg_demo_batch_size,
            train_reset_config=(
                train_reset_config
                if train_reset_config is not None
                else train_config.train_reset_config
            ),
            bc_reset_config=(
                bc_reset_config if bc_reset_config is not None else train_config.bc_reset_config
            ),
        )
        artifacts = train_3dof_ppo_agent(train_config)
        env = artifacts.make_eval_env(
            seed=seed + 10_000,
            uncertainty_profile=eval_uncertainty_profile,
        )
        try:
            predictor = VecNormalizePredictor(
                model=artifacts.model,
                vec_normalize=artifacts.vec_normalize,
            )
            summary = evaluate_3dof_predictor(
                env,
                predictor,
                episodes=episodes_per_seed,
                seed=seed + 10_000,
                uncertainty_profile=eval_uncertainty_profile,
            )
        finally:
            env.close()
        summary["seed"] = seed
        summary["training_summary"] = dict(artifacts.training_summary)
        per_seed.append(summary)
    aggregate = summarize_3dof_seed_runs(per_seed)
    aggregate["suite_name"] = suite_name
    aggregate["train_uncertainty_profile"] = train_uncertainty_profile
    aggregate["eval_uncertainty_profile"] = eval_uncertainty_profile
    aggregate["bc_rollout_episodes"] = bc_rollout_episodes
    aggregate["bc_pretrain_steps"] = bc_pretrain_steps
    aggregate["bc_batch_size"] = bc_batch_size
    aggregate["bc_demo_policy_name"] = bc_demo_policy_name
    aggregate["approach_bc_pretrain_steps"] = approach_bc_pretrain_steps
    aggregate["contact_bc_pretrain_steps"] = contact_bc_pretrain_steps
    aggregate["contact_bc_freeze_pose_head"] = contact_bc_freeze_pose_head
    aggregate["contact_bc_after_finetune"] = contact_bc_after_finetune
    aggregate["contact_finetune_timesteps"] = contact_finetune_timesteps
    aggregate["contact_finetune_anchor_rollout_episodes"] = (
        contact_finetune_anchor_rollout_episodes
    )
    aggregate["contact_finetune_anchor_bc_steps"] = contact_finetune_anchor_bc_steps
    aggregate["contact_finetune_anchor_interval_timesteps"] = (
        contact_finetune_anchor_interval_timesteps
    )
    aggregate["base_env_overrides"] = dict(base_env_overrides or {})
    aggregate["train_reset_stage_count"] = len(train_config.train_reset_config.curriculum_stages)
    aggregate["bc_reset_stage_count"] = len(train_config.bc_reset_config.curriculum_stages)
    aggregate.update(per_seed[0]["training_summary"])
    return {
        "per_seed": per_seed,
        "aggregate": aggregate,
    }


def build_3dof_benchmark_report(
    *,
    seeds: list[int],
    episodes_per_seed: int,
    max_episode_steps: int,
    uncertainty_profiles: list[str],
    handcrafted_results: dict[str, Any],
    learned_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "config": {
            "seeds": seeds,
            "episodes_per_seed": episodes_per_seed,
            "max_episode_steps": max_episode_steps,
            "uncertainty_profiles": uncertainty_profiles,
        },
        "results": {
            **handcrafted_results,
            **(learned_results or {}),
        },
    }


def write_3dof_benchmark_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
