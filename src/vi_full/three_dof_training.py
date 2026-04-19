from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass, field, is_dataclass, replace
import hashlib
import json
import math

import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from vi_full.training import VecNormalizePredictor
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_env import ThreeDoFInsertionEnv
from vi_full.three_dof_policies import (
    ThreeDoFTeacherSpec,
    build_3dof_teacher_metadata,
    compose_3dof_teacher_action,
    resolve_3dof_teacher_spec,
)
from vi_full.three_dof_profiles import build_3dof_profile_config
from vi_full.three_dof_config import ThreeDoFResetConfig, ThreeDoFResetStage

FIXED_IMPEDANCE_K_XY = 65.0
FIXED_IMPEDANCE_K_Z = 87.5


def _default_3dof_train_reset_config() -> ThreeDoFResetConfig:
    return ThreeDoFResetConfig(
        curriculum_stages=(
            ThreeDoFResetStage(
                start_xy_noise_m=0.0008,
                start_depth_fraction_range=(0.0, 0.15),
                weight=0.35,
            ),
            ThreeDoFResetStage(
                start_xy_noise_m=0.0005,
                start_depth_fraction_range=(0.35, 0.65),
                weight=0.4,
            ),
            ThreeDoFResetStage(
                start_xy_noise_m=0.0002,
                start_depth_fraction_range=(0.75, 0.88),
                weight=0.25,
            ),
        )
    )


def build_3dof_default_train_reset_config() -> ThreeDoFResetConfig:
    return _default_3dof_train_reset_config()


def _default_3dof_bc_reset_config() -> ThreeDoFResetConfig:
    return ThreeDoFResetConfig(
        curriculum_stages=(
            ThreeDoFResetStage(
                start_xy_noise_m=0.0008,
                start_depth_fraction_range=(0.0, 0.2),
                weight=0.35,
            ),
            ThreeDoFResetStage(
                start_xy_noise_m=0.0005,
                start_depth_fraction_range=(0.3, 0.6),
                weight=0.35,
            ),
            ThreeDoFResetStage(
                start_xy_noise_m=0.0002,
                start_depth_fraction_range=(0.75, 0.9),
                weight=0.3,
            ),
        )
    )


def build_3dof_coverage_collapse_reset_config() -> ThreeDoFResetConfig:
    return ThreeDoFResetConfig(
        curriculum_stages=(
            ThreeDoFResetStage(
                start_xy_noise_m=0.0002,
                start_depth_fraction_range=(0.75, 0.9),
                weight=1.0,
            ),
        )
    )


def build_3dof_old_contact_env_overrides() -> dict[str, float]:
    return {
        "contact_transition_band_m": 0.0,
        "contact_transition_stiffness_aware_force_scaling": False,
        "contact_transition_stiffness_aware_force_scaling_xy": False,
        "contact_transition_stiffness_aware_force_scaling_z": False,
        "contact_transition_stiffness_aware_force_scaling_z_axial": False,
        "contact_transition_stiffness_aware_force_scaling_z_coupling": False,
    }


def build_3dof_fixed_impedance_env_overrides_for(
    *,
    k_xy: float,
    k_z: float,
) -> dict[str, float]:
    return {
        "min_k_xy": float(k_xy),
        "max_k_xy": float(k_xy),
        "min_k_z": float(k_z),
        "max_k_z": float(k_z),
    }


def build_3dof_fixed_impedance_env_overrides() -> dict[str, float]:
    return build_3dof_fixed_impedance_env_overrides_for(
        k_xy=FIXED_IMPEDANCE_K_XY,
        k_z=FIXED_IMPEDANCE_K_Z,
    )


def _default_3dof_approach_bc_reset_config() -> ThreeDoFResetConfig:
    return ThreeDoFResetConfig(
        curriculum_stages=(
            ThreeDoFResetStage(
                start_xy_noise_m=0.0008,
                start_depth_fraction_range=(0.0, 0.2),
                weight=0.6,
            ),
            ThreeDoFResetStage(
                start_xy_noise_m=0.0005,
                start_depth_fraction_range=(0.3, 0.6),
                weight=0.4,
            ),
        )
    )


def _default_3dof_contact_finetune_reset_config() -> ThreeDoFResetConfig:
    return ThreeDoFResetConfig(
        curriculum_stages=(
            ThreeDoFResetStage(
                start_xy_noise_m=0.0002,
                start_depth_fraction_range=(0.78, 0.9),
                weight=1.0,
            ),
        )
    )


def _default_3dof_contact_bc_reset_config() -> ThreeDoFResetConfig:
    return ThreeDoFResetConfig(
        curriculum_stages=(
            ThreeDoFResetStage(
                start_xy_noise_m=0.00015,
                start_depth_fraction_range=(0.82, 0.92),
                weight=1.0,
            ),
        )
    )


def _default_3dof_phase_bias_distill_reset_config() -> ThreeDoFResetConfig:
    return ThreeDoFResetConfig(
        curriculum_stages=(
            ThreeDoFResetStage(
                start_xy_noise_m=0.00005,
                start_depth_fraction_range=(0.6, 0.68),
                weight=1.0,
            ),
        )
    )


def _default_3dof_intent_lift_bc_reset_config() -> ThreeDoFResetConfig:
    return ThreeDoFResetConfig(
        curriculum_stages=(
            ThreeDoFResetStage(
                start_xy_noise_m=0.00015,
                start_depth_fraction_range=(0.62, 0.76),
                weight=1.0,
            ),
        )
    )


def _default_contact_bc_action_loss_weights() -> tuple[float, float, float, float, float]:
    return (0.25, 0.25, 0.1, 1.0, 1.0)


def _default_contact_finetune_env_overrides() -> dict[str, float]:
    return {
        "force_penalty_scale": 0.03,
        "stability_penalty_scale": 0.06,
        "contact_bonus": 0.08,
        "enable_contact_intent_projection": False,
        "contact_intent_trigger_height_m": 0.0025,
        "contact_intent_trigger_xy_threshold_m": 0.0015,
        "contact_intent_max_xy_error_increase_m": float("inf"),
    }


def _documented_softlate_phase_bias_env_overrides() -> dict[str, float]:
    return {
        "contact_intent_trigger_height_m": 0.0005,
        "enable_phase_conditioned_action_bias": True,
        "phase_action_bias_trigger_height_m": 0.006,
        "phase_action_bias_trigger_xy_threshold_m": 0.0015,
        "phase_action_bias_dz_action": -0.12,
        "phase_action_bias_k_xy_action": 0.16,
        "phase_action_bias_k_z_action": 0.16,
        "phase_action_bias_mix": 0.15,
        "phase_action_bias_max_xy_error_increase_m": 0.0,
    }


@dataclass(frozen=True, slots=True)
class ThreeDoFPPOTrainConfig:
    total_timesteps: int = 2048
    n_envs: int = 4
    n_steps: int = 128
    batch_size: int = 128
    n_epochs: int = 4
    learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    ent_coef: float = 0.0
    vf_coef: float = 0.5
    clip_range: float = 0.2
    seed: int = 0
    demo_seed: int | None = None
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps
    norm_obs: bool = True
    norm_reward: bool = True
    verbose: int = 0
    train_uncertainty_profile: str = "nominal"
    eval_uncertainty_profile: str = "nominal"
    bc_rollout_episodes: int = 2
    bc_pretrain_steps: int = 2
    bc_batch_size: int = 32
    bc_learning_rate: float = 1e-3
    bc_demo_policy_name: str = "variable_impedance"
    bc_demo_teacher_spec: ThreeDoFTeacherSpec | None = None
    dapg_enabled: bool = False
    dapg_mini_updates_per_chunk: int = 1
    dapg_demo_batch_size: int = 64
    dapg_log_demo_updates: bool = True
    base_env_overrides: dict[str, float] = field(default_factory=dict)
    train_reset_config: ThreeDoFResetConfig = field(default_factory=_default_3dof_train_reset_config)
    bc_reset_config: ThreeDoFResetConfig = field(default_factory=_default_3dof_bc_reset_config)
    approach_bc_rollout_episodes: int = 0
    approach_bc_pretrain_steps: int = 0
    approach_bc_reset_config: ThreeDoFResetConfig = field(
        default_factory=_default_3dof_approach_bc_reset_config
    )
    approach_bc_action_loss_weights: tuple[float, float, float, float, float] | None = None
    contact_bc_rollout_episodes: int = 0
    contact_bc_pretrain_steps: int = 0
    contact_bc_reset_config: ThreeDoFResetConfig = field(
        default_factory=_default_3dof_contact_bc_reset_config
    )
    contact_bc_action_loss_weights: tuple[float, float, float, float, float] = field(
        default_factory=_default_contact_bc_action_loss_weights
    )
    contact_bc_freeze_pose_head: bool = False
    contact_bc_after_finetune: bool = False
    contact_finetune_timesteps: int = 0
    contact_finetune_anchor_rollout_episodes: int = 0
    contact_finetune_anchor_bc_steps: int = 0
    contact_finetune_anchor_interval_timesteps: int = 0
    contact_finetune_env_overrides: dict[str, float] = field(
        default_factory=_default_contact_finetune_env_overrides
    )
    contact_finetune_reset_config: ThreeDoFResetConfig = field(
        default_factory=_default_3dof_contact_finetune_reset_config
    )
    phase_bias_distill_rollout_episodes: int = 0
    phase_bias_distill_pretrain_steps: int = 0
    phase_bias_distill_trigger_weight: float = 1.0
    phase_bias_distill_sample_selection: str = "all"
    phase_bias_distill_contact_onset_force_threshold_n: float = 2.0
    phase_bias_distill_contact_onset_max_steps: int = 3
    phase_bias_distill_env_overrides: dict[str, float] = field(default_factory=dict)
    phase_bias_distill_reset_config: ThreeDoFResetConfig = field(
        default_factory=_default_3dof_phase_bias_distill_reset_config
    )
    intent_lift_bc_rollout_episodes: int = 0
    intent_lift_bc_pretrain_steps: int = 0
    intent_lift_bc_force_threshold_n: float = 0.3
    intent_lift_bc_max_contact_steps: int = 8
    intent_lift_bc_reset_config: ThreeDoFResetConfig = field(
        default_factory=_default_3dof_intent_lift_bc_reset_config
    )
    intent_lift_bc_precontact_bridge_steps: int = 2
    intent_lift_bc_precontact_bridge_weight: float = 0.25
    intent_lift_bc_sample_selection: str = "contact_bridge"
    intent_lift_bc_late_descent_height_m: float = 0.0
    intent_lift_bc_late_descent_dz_scale: float = 1.0
    intent_lift_bc_late_descent_k_z_scale: float = 1.0
    intent_lift_bc_contact_handoff_force_threshold_n: float = 2.0
    intent_lift_bc_contact_handoff_max_steps: int = 0
    intent_lift_bc_contact_handoff_weight: float = 0.25
    intent_lift_bc_contact_handoff_xy_scale: float = 1.0
    intent_lift_bc_contact_handoff_dz_scale: float = 1.0
    intent_lift_bc_contact_handoff_k_z_scale: float = 1.0
    intent_lift_bc_contact_relief_force_threshold_n: float = 0.3
    intent_lift_bc_contact_relief_max_steps: int = 0
    intent_lift_bc_contact_relief_weight: float = 0.25
    intent_lift_bc_contact_relief_xy_scale: float = 1.0
    intent_lift_bc_contact_relief_dz_scale: float = 1.0
    intent_lift_bc_contact_relief_k_z_scale: float = 1.0
    intent_lift_bc_contact_relief_tail_start_step: int = 0
    intent_lift_bc_contact_relief_tail_xy_scale: float = 1.0
    intent_lift_bc_contact_relief_tail_dz_scale: float = 1.0
    intent_lift_bc_legacy_stabilization_semantics: bool = False
    intent_lift_bc_action_loss_weights: (
        tuple[float, float, float, float, float] | None
    ) = None
    intent_lift_bc_freeze_pose_head: bool = False
    intent_lift_bc_after_stabilization: bool = False
    stabilization_bc_rollout_episodes: int = 0
    stabilization_bc_pretrain_steps: int = 0
    stabilization_bc_force_threshold_n: float = 1.0
    stabilization_bc_max_contact_steps: int = 4
    stabilization_bc_onset_force_threshold_n: float = 0.0
    stabilization_bc_onset_max_steps: int = 0
    stabilization_bc_onset_weight: float = 0.5
    stabilization_bc_relief_force_threshold_n: float = 0.0
    stabilization_bc_relief_max_steps: int = 0
    stabilization_bc_relief_weight: float = 0.25
    stabilization_bc_relief_tail_start_step: int = 0
    stabilization_bc_relief_tail_weight: float = 0.25
    stabilization_bc_relief_tail_force_threshold_n: float = 0.0
    stabilization_bc_relief_tail_max_steps: int = 0
    stabilization_bc_relief_xy_scale: float = 1.0
    stabilization_bc_relief_dz_scale: float = 1.0
    stabilization_bc_relief_tail_xy_scale: float = 1.0
    stabilization_bc_relief_tail_dz_scale: float = 1.0
    stabilization_bc_reset_config: ThreeDoFResetConfig = field(
        default_factory=_default_3dof_contact_finetune_reset_config
    )
    stabilization_bc_precontact_bridge_steps: int = 0
    stabilization_bc_precontact_bridge_weight: float = 0.25
    stabilization_bc_action_loss_weights: (
        tuple[float, float, float, float, float] | None
    ) = None
    stabilization_bc_freeze_pose_head: bool = False


def build_3dof_mainline_train_config(
    *,
    seed: int = 0,
    total_timesteps: int = 128,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    train_uncertainty_profile: str = "nominal",
    eval_uncertainty_profile: str = "nominal",
    n_envs: int = 1,
    n_steps: int = 64,
    batch_size: int = 64,
    n_epochs: int = 1,
    learning_rate: float = 1e-4,
    gamma: float = 0.95,
    verbose: int = 0,
    bc_rollout_episodes: int = 8,
    bc_pretrain_steps: int = 32,
    bc_batch_size: int = 64,
    bc_demo_policy_name: str = "variable_impedance",
    bc_demo_teacher_spec: ThreeDoFTeacherSpec | None = None,
) -> ThreeDoFPPOTrainConfig:
    return ThreeDoFPPOTrainConfig(
        total_timesteps=total_timesteps,
        n_envs=n_envs,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        learning_rate=learning_rate,
        gamma=gamma,
        seed=seed,
        max_episode_steps=max_episode_steps,
        verbose=verbose,
        train_uncertainty_profile=train_uncertainty_profile,
        eval_uncertainty_profile=eval_uncertainty_profile,
        bc_rollout_episodes=bc_rollout_episodes,
        bc_pretrain_steps=bc_pretrain_steps,
        bc_batch_size=bc_batch_size,
        bc_demo_policy_name=bc_demo_policy_name,
        bc_demo_teacher_spec=bc_demo_teacher_spec,
        approach_bc_rollout_episodes=0,
        approach_bc_pretrain_steps=0,
        contact_bc_rollout_episodes=0,
        contact_bc_pretrain_steps=0,
        contact_finetune_timesteps=0,
        phase_bias_distill_rollout_episodes=0,
        phase_bias_distill_pretrain_steps=0,
        intent_lift_bc_rollout_episodes=0,
        intent_lift_bc_pretrain_steps=0,
        stabilization_bc_rollout_episodes=0,
        stabilization_bc_pretrain_steps=0,
    )


def infer_3dof_reset_coverage_label(reset_config: ThreeDoFResetConfig) -> str:
    if reset_config == build_3dof_coverage_collapse_reset_config():
        return "reset_coverage_collapse"
    if reset_config in (
        _default_3dof_bc_reset_config(),
        _default_3dof_train_reset_config(),
    ):
        return "reset_repaired"
    return "reset_custom"


def build_3dof_reset_config_for_coverage(
    coverage_label: str,
    *,
    target: str,
) -> ThreeDoFResetConfig:
    if coverage_label == "reset_coverage_collapse":
        return build_3dof_coverage_collapse_reset_config()
    if coverage_label == "reset_repaired":
        if target == "bc":
            return _default_3dof_bc_reset_config()
        if target == "train":
            return _default_3dof_train_reset_config()
    raise ValueError(
        f"Unsupported 3DoF coverage label '{coverage_label}' for target '{target}'"
    )


def build_3dof_factorized_train_config(
    *,
    seed: int = 0,
    demo_seed: int | None = None,
    total_timesteps: int = 128,
    bc_rollout_episodes: int = 8,
    bc_pretrain_steps: int = 32,
    bc_batch_size: int = 64,
    demonstration_coverage: str = "reset_repaired",
    reset_coverage: str = "reset_repaired",
    train_uncertainty_profile: str = "nominal",
    eval_uncertainty_profile: str = "nominal",
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
    bc_demo_policy_name: str = "variable_impedance",
    bc_demo_teacher_spec: ThreeDoFTeacherSpec | None = None,
) -> ThreeDoFPPOTrainConfig:
    base_config = build_3dof_mainline_train_config(
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
        bc_demo_teacher_spec=bc_demo_teacher_spec,
    )
    return replace(
        base_config,
        demo_seed=demo_seed,
        train_reset_config=build_3dof_reset_config_for_coverage(
            reset_coverage,
            target="train",
        ),
        bc_reset_config=build_3dof_reset_config_for_coverage(
            demonstration_coverage,
            target="bc",
        ),
    )


def build_3dof_training_budget_snapshot(
    config: ThreeDoFPPOTrainConfig,
) -> dict[str, int]:
    return {
        "total_timesteps": int(config.total_timesteps),
        "bc_rollout_episodes": int(config.bc_rollout_episodes),
        "bc_pretrain_steps": int(config.bc_pretrain_steps),
        "bc_batch_size": int(config.bc_batch_size),
    }


def build_3dof_documented_recipe_config(
    recipe_name: str,
    *,
    seed: int = 0,
) -> ThreeDoFPPOTrainConfig:
    base_kwargs = dict(
        total_timesteps=128,
        n_envs=1,
        n_steps=64,
        batch_size=64,
        n_epochs=1,
        learning_rate=1e-4,
        gamma=0.95,
        seed=seed,
        # This documented recipe is an abridged debugging/probe configuration, not the
        # main 64-step benchmark contract used by the paper-facing benchmark runners.
        max_episode_steps=32,
        verbose=0,
        bc_rollout_episodes=2,
        bc_pretrain_steps=2,
        bc_batch_size=32,
        approach_bc_rollout_episodes=2,
        approach_bc_pretrain_steps=32,
        contact_bc_rollout_episodes=2,
        contact_bc_pretrain_steps=6,
        contact_finetune_timesteps=64,
    )
    if recipe_name == "contactbc6_baseline":
        return ThreeDoFPPOTrainConfig(**base_kwargs)
    if recipe_name == "softlate_p8_prefilter":
        return ThreeDoFPPOTrainConfig(
            **base_kwargs,
            phase_bias_distill_rollout_episodes=2,
            phase_bias_distill_pretrain_steps=8,
            phase_bias_distill_sample_selection="precontact_informative",
            phase_bias_distill_env_overrides=_documented_softlate_phase_bias_env_overrides(),
        )
    if recipe_name == "softlate_p8_prefilter_stab4":
        return ThreeDoFPPOTrainConfig(
            **base_kwargs,
            phase_bias_distill_rollout_episodes=2,
            phase_bias_distill_pretrain_steps=8,
            phase_bias_distill_sample_selection="precontact_informative",
            phase_bias_distill_env_overrides=_documented_softlate_phase_bias_env_overrides(),
            stabilization_bc_rollout_episodes=2,
            stabilization_bc_pretrain_steps=4,
        )
    if recipe_name == "softlate_p8_prefilter_stab8":
        return ThreeDoFPPOTrainConfig(
            **base_kwargs,
            phase_bias_distill_rollout_episodes=2,
            phase_bias_distill_pretrain_steps=8,
            phase_bias_distill_sample_selection="precontact_informative",
            phase_bias_distill_env_overrides=_documented_softlate_phase_bias_env_overrides(),
            stabilization_bc_rollout_episodes=2,
            stabilization_bc_pretrain_steps=8,
        )
    raise ValueError(f"Unknown documented 3DoF recipe: {recipe_name}")


def build_3dof_anchor_transition_probe_config(
    probe_name: str,
    *,
    seed: int = 0,
) -> ThreeDoFPPOTrainConfig:
    anchor_parent = build_3dof_documented_recipe_config(
        "softlate_p8_prefilter_stab8",
        seed=seed,
    )
    relief_window_parent = replace(
        anchor_parent,
        stabilization_bc_force_threshold_n=0.3,
        stabilization_bc_max_contact_steps=8,
    )
    if probe_name == "anchor_stab8":
        return anchor_parent
    if probe_name == "anchor_stab8_relief_window":
        return relief_window_parent
    if probe_name == "anchor_stab8_relief_window_p12":
        return replace(
            relief_window_parent,
            stabilization_bc_pretrain_steps=12,
        )
    if probe_name == "anchor_stab8_relief_window_p12_bridge1_w025":
        return replace(
            relief_window_parent,
            stabilization_bc_pretrain_steps=12,
            stabilization_bc_precontact_bridge_steps=1,
            stabilization_bc_precontact_bridge_weight=0.25,
        )
    if probe_name == "anchor_stab8_relief_window_onset2_t15_w10":
        return replace(
            relief_window_parent,
            stabilization_bc_onset_force_threshold_n=1.5,
            stabilization_bc_onset_max_steps=2,
            stabilization_bc_onset_weight=1.0,
        )
    raise ValueError(f"Unknown 3DoF anchor-transition probe: {probe_name}")


def build_3dof_reconstruction_probe_config(
    probe_name: str,
    *,
    seed: int = 0,
) -> ThreeDoFPPOTrainConfig:
    relief_parent = replace(
        build_3dof_documented_recipe_config("contactbc6_baseline", seed=seed),
        stabilization_bc_rollout_episodes=2,
        stabilization_bc_pretrain_steps=12,
        stabilization_bc_force_threshold_n=0.3,
        stabilization_bc_max_contact_steps=8,
        stabilization_bc_precontact_bridge_steps=1,
        stabilization_bc_precontact_bridge_weight=0.25,
    )
    softlate_relief_parent = replace(
        build_3dof_documented_recipe_config("softlate_p8_prefilter", seed=seed),
        stabilization_bc_rollout_episodes=2,
        stabilization_bc_pretrain_steps=12,
        stabilization_bc_force_threshold_n=0.3,
        stabilization_bc_max_contact_steps=8,
        stabilization_bc_precontact_bridge_steps=1,
        stabilization_bc_precontact_bridge_weight=0.25,
    )
    if probe_name == "intent_parent_relief_p12_bridge1_w025":
        return relief_parent
    if probe_name == "intent_after_stab_p2_full_from_relief_parent":
        return replace(
            relief_parent,
            intent_lift_bc_rollout_episodes=2,
            intent_lift_bc_pretrain_steps=2,
            intent_lift_bc_after_stabilization=True,
            intent_lift_bc_legacy_stabilization_semantics=True,
        )
    if probe_name == "intent_after_stab_p2_xydz_soft_from_relief_parent":
        return replace(
            relief_parent,
            intent_lift_bc_rollout_episodes=2,
            intent_lift_bc_pretrain_steps=2,
            intent_lift_bc_after_stabilization=True,
            intent_lift_bc_legacy_stabilization_semantics=True,
            intent_lift_bc_action_loss_weights=(0.5, 0.5, 0.25, 0.0, 0.0),
        )
    if probe_name == "intent_parent_softlate_relief_p12_bridge1_w025":
        return softlate_relief_parent
    if probe_name == "intent_after_stab_p2_full_from_softlate_relief_parent":
        return replace(
            softlate_relief_parent,
            intent_lift_bc_rollout_episodes=2,
            intent_lift_bc_pretrain_steps=2,
            intent_lift_bc_after_stabilization=True,
            intent_lift_bc_legacy_stabilization_semantics=True,
        )
    if probe_name == "intent_after_stab_p2_xydz_soft_from_softlate_relief_parent":
        return replace(
            softlate_relief_parent,
            intent_lift_bc_rollout_episodes=2,
            intent_lift_bc_pretrain_steps=2,
            intent_lift_bc_after_stabilization=True,
            intent_lift_bc_legacy_stabilization_semantics=True,
            intent_lift_bc_action_loss_weights=(0.5, 0.5, 0.25, 0.0, 0.0),
        )
    raise ValueError(f"Unknown 3DoF reconstruction probe: {probe_name}")


def build_3dof_stabilization_history_probe_config(
    probe_name: str,
    *,
    seed: int = 0,
) -> ThreeDoFPPOTrainConfig:
    contact_relief_parent = replace(
        build_3dof_documented_recipe_config("contactbc6_baseline", seed=seed),
        stabilization_bc_rollout_episodes=2,
        stabilization_bc_force_threshold_n=0.3,
        stabilization_bc_max_contact_steps=8,
    )
    softlate_relief_parent = replace(
        build_3dof_documented_recipe_config("softlate_p8_prefilter", seed=seed),
        stabilization_bc_rollout_episodes=2,
        stabilization_bc_force_threshold_n=0.3,
        stabilization_bc_max_contact_steps=8,
    )
    if probe_name == "contact_relief_p8":
        return replace(
            contact_relief_parent,
            stabilization_bc_pretrain_steps=8,
        )
    if probe_name == "contact_relief_p12":
        return replace(
            contact_relief_parent,
            stabilization_bc_pretrain_steps=12,
        )
    if probe_name == "contact_relief_p12_bridge1_w025":
        return replace(
            contact_relief_parent,
            stabilization_bc_pretrain_steps=12,
            stabilization_bc_precontact_bridge_steps=1,
            stabilization_bc_precontact_bridge_weight=0.25,
        )
    if probe_name == "softlate_relief_p8":
        return replace(
            softlate_relief_parent,
            stabilization_bc_pretrain_steps=8,
        )
    if probe_name == "softlate_relief_p12":
        return replace(
            softlate_relief_parent,
            stabilization_bc_pretrain_steps=12,
        )
    if probe_name == "softlate_relief_p12_bridge1_w025":
        return replace(
            softlate_relief_parent,
            stabilization_bc_pretrain_steps=12,
            stabilization_bc_precontact_bridge_steps=1,
            stabilization_bc_precontact_bridge_weight=0.25,
        )
    raise ValueError(f"Unknown 3DoF stabilization history probe: {probe_name}")


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


def serialize_3dof_train_config(config: ThreeDoFPPOTrainConfig) -> dict[str, object]:
    return _sanitize_3dof_serializable(asdict(config))


@dataclass(frozen=True, slots=True)
class ThreeDoFDemoDataset:
    observations: np.ndarray
    actions: np.ndarray
    dataset_id: str
    dataset_path: str
    dataset_hash: str


@dataclass(slots=True)
class ThreeDoFPPOArtifacts:
    model: PPO
    vec_normalize: VecNormalize
    train_config: ThreeDoFPPOTrainConfig
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


def create_3dof_training_vec_env(config: ThreeDoFPPOTrainConfig) -> VecNormalize:
    return _create_3dof_vec_env_with_reset_config(
        config,
        reset_config=config.train_reset_config,
        env_overrides=config.base_env_overrides,
    )


def _create_3dof_vec_env_with_reset_config(
    config: ThreeDoFPPOTrainConfig,
    *,
    reset_config: ThreeDoFResetConfig,
    env_overrides: dict[str, float] | None = None,
) -> VecNormalize:
    def _make_env(rank: int):
        def _factory():
            profile_config = build_3dof_profile_config(
                config.train_uncertainty_profile,
                max_episode_steps=config.max_episode_steps,
            )
            replace_kwargs: dict[str, object] = {"reset_config": reset_config}
            if config.base_env_overrides:
                replace_kwargs.update(config.base_env_overrides)
            if env_overrides:
                replace_kwargs.update(env_overrides)
            env = ThreeDoFInsertionEnv(
                replace(
                    profile_config,
                    **replace_kwargs,
                )
            )
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


def _transfer_vecnormalize_stats(source: VecNormalize, target: VecNormalize) -> None:
    if source.norm_obs and target.norm_obs:
        target.obs_rms = deepcopy(source.obs_rms)
    if source.norm_reward and target.norm_reward:
        target.ret_rms = deepcopy(source.ret_rms)
    target.returns = np.zeros_like(target.returns)


def _continue_3dof_training_with_reset_config(
    *,
    model: PPO,
    vec_env: VecNormalize,
    config: ThreeDoFPPOTrainConfig,
    reset_config: ThreeDoFResetConfig,
    total_timesteps: int,
    env_overrides: dict[str, float] | None = None,
) -> VecNormalize:
    if total_timesteps <= 0:
        return vec_env

    next_vec_env = _create_3dof_vec_env_with_reset_config(
        config,
        reset_config=reset_config,
        env_overrides=env_overrides,
    )
    _transfer_vecnormalize_stats(vec_env, next_vec_env)
    model.set_env(next_vec_env)
    model.learn(total_timesteps=total_timesteps, reset_num_timesteps=False)
    vec_env.close()
    return next_vec_env


def _run_3dof_contact_finetune_stage(
    *,
    model: PPO,
    vec_env: VecNormalize,
    config: ThreeDoFPPOTrainConfig,
) -> VecNormalize:
    if config.contact_finetune_timesteps <= 0:
        return vec_env

    anchor_enabled = (
        config.contact_finetune_anchor_rollout_episodes > 0
        and config.contact_finetune_anchor_bc_steps > 0
        and config.contact_finetune_anchor_interval_timesteps > 0
    )
    if not anchor_enabled:
        return _continue_3dof_training_with_reset_config(
            model=model,
            vec_env=vec_env,
            config=config,
            reset_config=config.contact_finetune_reset_config,
            total_timesteps=config.contact_finetune_timesteps,
            env_overrides=config.contact_finetune_env_overrides,
        )

    remaining_timesteps = config.contact_finetune_timesteps
    current_vec_env = vec_env
    while remaining_timesteps > 0:
        chunk_timesteps = min(
            config.contact_finetune_anchor_interval_timesteps,
            remaining_timesteps,
        )
        current_vec_env = _continue_3dof_training_with_reset_config(
            model=model,
            vec_env=current_vec_env,
            config=config,
            reset_config=config.contact_finetune_reset_config,
            total_timesteps=chunk_timesteps,
            env_overrides=config.contact_finetune_env_overrides,
        )
        _behavior_clone_3dof_stage(
            model=model,
            vec_env=current_vec_env,
            config=config,
            rollout_episodes=config.contact_finetune_anchor_rollout_episodes,
            pretrain_steps=config.contact_finetune_anchor_bc_steps,
            reset_config=config.contact_bc_reset_config,
            action_loss_weights=config.contact_bc_action_loss_weights,
            freeze_pose_head=config.contact_bc_freeze_pose_head,
        )
        remaining_timesteps -= chunk_timesteps
    return current_vec_env


@dataclass(frozen=True, slots=True)
class _ThreeDoFResolvedTeacherPolicy:
    spec: ThreeDoFTeacherSpec

    def act(self, observation: np.ndarray) -> np.ndarray:
        return compose_3dof_teacher_action(self.spec, observation)


def _resolve_3dof_bc_demo_teacher_spec(
    config: ThreeDoFPPOTrainConfig,
) -> ThreeDoFTeacherSpec:
    return resolve_3dof_teacher_spec(
        policy_name=config.bc_demo_policy_name,
        teacher_spec=config.bc_demo_teacher_spec,
    )


def _build_3dof_teacher_metadata(
    config: ThreeDoFPPOTrainConfig,
) -> dict[str, object]:
    return build_3dof_teacher_metadata(
        policy_name=config.bc_demo_policy_name,
        teacher_spec=config.bc_demo_teacher_spec,
    )


def _build_3dof_demo_policy(config: ThreeDoFPPOTrainConfig):
    return _ThreeDoFResolvedTeacherPolicy(_resolve_3dof_bc_demo_teacher_spec(config))


def _resolve_3dof_demo_seed(config: ThreeDoFPPOTrainConfig) -> int:
    return int(config.seed if config.demo_seed is None else config.demo_seed)


def collect_3dof_demonstrations(
    config: ThreeDoFPPOTrainConfig,
    episodes: int,
    *,
    reset_config: ThreeDoFResetConfig | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    policy = _build_3dof_demo_policy(config)
    env = ThreeDoFInsertionEnv(
        replace(
            build_3dof_profile_config(
                config.train_uncertainty_profile,
                max_episode_steps=config.max_episode_steps,
            ),
            **config.base_env_overrides,
            reset_config=reset_config or config.bc_reset_config,
        )
    )
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    try:
        for episode_index in range(episodes):
            observation, _ = env.reset(
                seed=_resolve_3dof_demo_seed(config) + 50_000 + episode_index
            )
            terminated = False
            truncated = False
            while not (terminated or truncated):
                action = policy.act(observation)
                observations.append(np.asarray(observation, dtype=np.float32).copy())
                actions.append(np.asarray(action, dtype=np.float32).copy())
                observation, _, terminated, truncated, _ = env.step(action)
    finally:
        env.close()

    if not observations:
        obs_dim = env.observation_space.shape[0]
        act_dim = env.action_space.shape[0]
        return (
            np.zeros((0, obs_dim), dtype=np.float32),
            np.zeros((0, act_dim), dtype=np.float32),
        )
    return np.stack(observations).astype(np.float32), np.stack(actions).astype(np.float32)


def _infer_3dof_contact_law_label(base_env_overrides: dict[str, float]) -> str:
    old_contact_overrides = build_3dof_old_contact_env_overrides()
    if all(
        base_env_overrides.get(key, value) == value
        for key, value in old_contact_overrides.items()
    ):
        if any(key in base_env_overrides for key in old_contact_overrides):
            return "contact_old"
    if any(key in base_env_overrides for key in old_contact_overrides):
        return "contact_custom"
    return "contact_new"


def _build_3dof_demo_dataset_metadata(
    config: ThreeDoFPPOTrainConfig,
    *,
    reset_config: ThreeDoFResetConfig,
) -> dict[str, object]:
    dataset_id = (
        f"{_infer_3dof_contact_law_label(config.base_env_overrides)}__"
        f"{infer_3dof_reset_coverage_label(reset_config)}"
    )
    hash_payload = _sanitize_3dof_serializable(
        {
            "train_uncertainty_profile": config.train_uncertainty_profile,
            "bc_demo_teacher_spec": _resolve_3dof_bc_demo_teacher_spec(config),
            "demo_seed": _resolve_3dof_demo_seed(config),
            "base_env_overrides": config.base_env_overrides,
            "bc_reset_config": asdict(reset_config),
        }
    )
    dataset_hash = hashlib.sha256(
        json.dumps(hash_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    teacher_metadata = _build_3dof_teacher_metadata(config)
    return {
        "dataset_id": dataset_id,
        "dataset_path": f"generated://three_dof/{dataset_id}/{dataset_hash}",
        "dataset_hash": dataset_hash,
        **teacher_metadata,
    }


def _collect_3dof_demo_dataset(
    config: ThreeDoFPPOTrainConfig,
    *,
    episodes: int,
    reset_config: ThreeDoFResetConfig,
) -> ThreeDoFDemoDataset:
    observations, actions = collect_3dof_demonstrations(
        config,
        episodes=episodes,
        reset_config=reset_config,
    )
    metadata = _build_3dof_demo_dataset_metadata(config, reset_config=reset_config)
    return ThreeDoFDemoDataset(
        observations=observations,
        actions=actions,
        dataset_id=metadata["dataset_id"],
        dataset_path=metadata["dataset_path"],
        dataset_hash=metadata["dataset_hash"],
    )


def _collect_3dof_actor_parameters(policy) -> list[torch.nn.Parameter]:
    params: list[torch.nn.Parameter] = []
    seen: set[int] = set()
    modules = [
        getattr(policy, "features_extractor", None),
        policy.mlp_extractor.policy_net,
        policy.action_net,
    ]
    for module in modules:
        if module is None:
            continue
        for parameter in module.parameters():
            if parameter.requires_grad and id(parameter) not in seen:
                params.append(parameter)
                seen.add(id(parameter))
    if hasattr(policy, "log_std") and policy.log_std.requires_grad:
        params.append(policy.log_std)
    return params


def collect_3dof_bc_demo_dataset_audit(
    config: ThreeDoFPPOTrainConfig,
    episodes: int,
    *,
    reset_config: ThreeDoFResetConfig | None = None,
    low_force_onset_threshold_n: float = 2.0,
    low_force_onset_max_contact_steps: int = 3,
) -> dict[str, object]:
    policy = _build_3dof_demo_policy(config)
    env = ThreeDoFInsertionEnv(
        replace(
            build_3dof_profile_config(
                config.train_uncertainty_profile,
                max_episode_steps=config.max_episode_steps,
            ),
            **config.base_env_overrides,
            reset_config=reset_config or config.bc_reset_config,
        )
    )
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    has_contact_rows: list[bool] = []
    is_jammed_rows: list[bool] = []
    contact_force_norm_rows: list[float] = []
    contact_step_index_rows: list[int] = []
    first_contact_steps: list[int] = []
    try:
        for episode_index in range(episodes):
            observation, _ = env.reset(
                seed=_resolve_3dof_demo_seed(config) + 50_000 + episode_index
            )
            terminated = False
            truncated = False
            current_contact_step_index = 0
            first_contact_step: int | None = None
            step_count = 0
            while not (terminated or truncated):
                action = policy.act(observation)
                observations.append(np.asarray(observation, dtype=np.float32).copy())
                actions.append(np.asarray(action, dtype=np.float32).copy())
                observation, _, terminated, truncated, info = env.step(action)
                step_count += 1
                step_has_contact = (
                    float(info["contact_force_norm"])
                    >= env.config.contact_reward_force_threshold_n
                )
                current_contact_step_index = (
                    current_contact_step_index + 1 if step_has_contact else 0
                )
                if first_contact_step is None and step_has_contact:
                    first_contact_step = step_count
                has_contact_rows.append(step_has_contact)
                is_jammed_rows.append(bool(info["is_jammed"]))
                contact_force_norm_rows.append(float(info["contact_force_norm"]))
                contact_step_index_rows.append(current_contact_step_index)
            if first_contact_step is not None:
                first_contact_steps.append(first_contact_step)
    finally:
        env.close()

    teacher_metadata = _build_3dof_teacher_metadata(config)

    if not observations:
        return {
            "episodes": int(episodes),
            "num_rows": 0,
            "contact_sample_count": 0,
            "contact_sample_ratio": 0.0,
            "contact_episode_count": 0,
            "contact_episode_ratio": 0.0,
            "first_contact_step_histogram": {},
            "first_contact_step_mean": None,
            "low_force_onset_threshold_n": float(low_force_onset_threshold_n),
            "low_force_onset_max_contact_steps": int(low_force_onset_max_contact_steps),
            "low_force_onset_sample_count": 0,
            "low_force_onset_sample_ratio": 0.0,
            "teacher_dataset_summary": summarize_3dof_teacher_dataset(
                observations=np.zeros((0, env.observation_space.shape[0]), dtype=np.float32),
                actions=np.zeros((0, env.action_space.shape[0]), dtype=np.float32),
            ),
            **teacher_metadata,
        }

    observations_array = np.stack(observations).astype(np.float32)
    actions_array = np.stack(actions).astype(np.float32)
    has_contact = np.asarray(has_contact_rows, dtype=bool)
    is_jammed = np.asarray(is_jammed_rows, dtype=bool)
    contact_force_norm = np.asarray(contact_force_norm_rows, dtype=np.float32)
    contact_step_index = np.asarray(contact_step_index_rows, dtype=np.int32)
    low_force_onset_mask = (
        has_contact
        & ~is_jammed
        & (contact_force_norm <= low_force_onset_threshold_n)
        & (contact_step_index > 0)
        & (contact_step_index <= low_force_onset_max_contact_steps)
    )
    first_contact_histogram = {
        str(step): int(count)
        for step, count in sorted(Counter(first_contact_steps).items())
    }
    return {
        "episodes": int(episodes),
        "num_rows": int(observations_array.shape[0]),
        "contact_sample_count": int(np.sum(has_contact)),
        "contact_sample_ratio": float(np.mean(has_contact)),
        "contact_episode_count": int(len(first_contact_steps)),
        "contact_episode_ratio": float(len(first_contact_steps) / max(episodes, 1)),
        "first_contact_step_histogram": first_contact_histogram,
        "first_contact_step_mean": None
        if not first_contact_steps
        else float(np.mean(np.asarray(first_contact_steps, dtype=np.float32))),
        "low_force_onset_threshold_n": float(low_force_onset_threshold_n),
        "low_force_onset_max_contact_steps": int(low_force_onset_max_contact_steps),
        "low_force_onset_sample_count": int(np.sum(low_force_onset_mask)),
        "low_force_onset_sample_ratio": float(np.mean(low_force_onset_mask)),
        "teacher_dataset_summary": summarize_3dof_teacher_dataset(
            observations=observations_array,
            actions=actions_array,
        ),
        **teacher_metadata,
    }


def _filter_phase_bias_distill_dataset(
    *,
    observations: np.ndarray,
    actions: np.ndarray,
    sample_weights: np.ndarray,
    phase_bias_applied: np.ndarray,
    has_contact: np.ndarray,
    is_jammed: np.ndarray,
    in_approach_alignment_corridor: np.ndarray,
    in_contact_intent_corridor: np.ndarray,
    contact_force_norm: np.ndarray,
    contact_step_index: np.ndarray,
    sample_selection: str,
    contact_onset_force_threshold_n: float,
    contact_onset_max_steps: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if sample_selection == "all":
        return observations, actions, sample_weights
    if sample_selection not in {"precontact_informative", "precontact_plus_onset"}:
        raise ValueError(f"Unsupported phase-bias distill sample selection: {sample_selection}")

    precontact_mask = (
        ~has_contact
        & (
            phase_bias_applied
            | in_approach_alignment_corridor
            | in_contact_intent_corridor
        )
    )
    if sample_selection == "precontact_informative":
        keep_mask = precontact_mask
    else:
        onset_mask = (
            has_contact
            & ~is_jammed
            & (contact_force_norm <= contact_onset_force_threshold_n)
            & (contact_step_index > 0)
            & (contact_step_index <= contact_onset_max_steps)
        )
        keep_mask = precontact_mask | onset_mask
    return observations[keep_mask], actions[keep_mask], sample_weights[keep_mask]


def _filter_stabilization_bc_demo_dataset(
    *,
    observations: np.ndarray,
    actions: np.ndarray,
    has_contact: np.ndarray,
    is_jammed: np.ndarray,
    contact_force_norm: np.ndarray,
    contact_step_index: np.ndarray,
    episode_index: np.ndarray,
    force_threshold_n: float,
    max_contact_steps: int,
    precontact_bridge_steps: int,
    precontact_bridge_weight: float,
    onset_force_threshold_n: float = 0.0,
    onset_max_steps: int = 0,
    onset_weight: float = 0.5,
    relief_force_threshold_n: float = 0.0,
    relief_max_steps: int = 0,
    relief_weight: float = 0.25,
    relief_tail_start_step: int = 0,
    relief_tail_weight: float = 0.25,
    relief_tail_force_threshold_n: float = 0.0,
    relief_tail_max_steps: int = 0,
    relief_xy_scale: float = 1.0,
    relief_dz_scale: float = 1.0,
    relief_tail_xy_scale: float = 1.0,
    relief_tail_dz_scale: float = 1.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    low_force_mask = (
        has_contact
        & ~is_jammed
        & (contact_force_norm <= force_threshold_n)
        & (contact_step_index > 0)
        & (contact_step_index <= max_contact_steps)
    )
    keep_mask = low_force_mask.copy()
    sample_weights = np.ones(observations.shape[0], dtype=np.float32)
    filtered_actions = actions.copy()
    onset_mask = np.zeros(observations.shape[0], dtype=bool)

    if onset_max_steps > 0 and onset_force_threshold_n > 0.0:
        onset_mask = (
            has_contact
            & ~is_jammed
            & (contact_force_norm <= onset_force_threshold_n)
            & (contact_step_index > 0)
            & (contact_step_index <= onset_max_steps)
        )
        keep_mask |= onset_mask
        onset_only_mask = onset_mask & ~low_force_mask
        sample_weights[onset_only_mask] = np.float32(onset_weight)

    if relief_max_steps > 0 and (
        relief_force_threshold_n > 0.0 or relief_tail_force_threshold_n > 0.0
    ):
        relief_start_step = max(2, onset_max_steps + 1)
        relief_mask = np.zeros(observations.shape[0], dtype=bool)
        if relief_force_threshold_n > 0.0:
            relief_mask = (
                has_contact
                & ~is_jammed
                & (contact_force_norm <= relief_force_threshold_n)
                & (contact_step_index >= relief_start_step)
                & (contact_step_index <= relief_max_steps)
            )
        relief_tail_mask = np.zeros(observations.shape[0], dtype=bool)
        if relief_tail_start_step > 0 and relief_tail_force_threshold_n > 0.0:
            relief_tail_max_step = (
                relief_tail_max_steps if relief_tail_max_steps > 0 else relief_max_steps
            )
            relief_tail_mask = (
                has_contact
                & ~is_jammed
                & (contact_force_norm <= relief_tail_force_threshold_n)
                & (
                    contact_step_index
                    >= max(relief_start_step, relief_tail_start_step)
                )
                & (contact_step_index <= relief_tail_max_step)
            )
        combined_relief_mask = relief_mask | relief_tail_mask
        keep_mask |= combined_relief_mask
        relief_only_mask = combined_relief_mask & ~low_force_mask & ~onset_mask
        sample_weights[relief_only_mask] = np.float32(relief_weight)
        late_relief_only_mask = np.zeros(observations.shape[0], dtype=bool)
        if relief_tail_start_step > 0:
            late_relief_only_mask = relief_only_mask & (
                contact_step_index >= max(relief_start_step, relief_tail_start_step)
            )
            sample_weights[late_relief_only_mask] = np.float32(relief_tail_weight)
        if not np.isclose(relief_xy_scale, 1.0):
            filtered_actions[relief_only_mask, :2] *= np.float32(relief_xy_scale)
        if not np.isclose(relief_dz_scale, 1.0):
            filtered_actions[relief_only_mask, 2] *= np.float32(relief_dz_scale)
        if not np.isclose(relief_tail_xy_scale, 1.0):
            filtered_actions[late_relief_only_mask, :2] *= np.float32(relief_tail_xy_scale)
        if not np.isclose(relief_tail_dz_scale, 1.0):
            filtered_actions[late_relief_only_mask, 2] *= np.float32(relief_tail_dz_scale)

    if precontact_bridge_steps > 0:
        onset_indices = np.flatnonzero(has_contact & (contact_step_index == 1))
        for onset_index in onset_indices:
            onset_episode = episode_index[onset_index]
            for bridge_offset in range(1, precontact_bridge_steps + 1):
                candidate_index = onset_index - bridge_offset
                if candidate_index < 0:
                    break
                if episode_index[candidate_index] != onset_episode:
                    break
                if has_contact[candidate_index] or is_jammed[candidate_index]:
                    continue
                keep_mask[candidate_index] = True
                sample_weights[candidate_index] = np.float32(precontact_bridge_weight)

    return observations[keep_mask], filtered_actions[keep_mask], sample_weights[keep_mask]


def _filter_intent_lift_bc_demo_dataset(
    *,
    observations: np.ndarray,
    actions: np.ndarray,
    has_contact: np.ndarray,
    is_jammed: np.ndarray,
    contact_force_norm: np.ndarray,
    contact_step_index: np.ndarray,
    episode_index: np.ndarray,
    in_approach_alignment_corridor: np.ndarray,
    in_contact_intent_corridor: np.ndarray,
    force_threshold_n: float,
    max_contact_steps: int,
    precontact_bridge_steps: int,
    precontact_bridge_weight: float,
    sample_selection: str,
    contact_handoff_force_threshold_n: float = 2.0,
    contact_handoff_max_steps: int = 0,
    contact_handoff_weight: float = 0.25,
    contact_relief_force_threshold_n: float = 0.3,
    contact_relief_max_steps: int = 0,
    contact_relief_weight: float = 0.25,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if sample_selection == "contact_bridge":
        return _filter_stabilization_bc_demo_dataset(
            observations=observations,
            actions=actions,
            has_contact=has_contact,
            is_jammed=is_jammed,
            contact_force_norm=contact_force_norm,
            contact_step_index=contact_step_index,
            episode_index=episode_index,
            force_threshold_n=force_threshold_n,
            max_contact_steps=max_contact_steps,
            precontact_bridge_steps=precontact_bridge_steps,
            precontact_bridge_weight=precontact_bridge_weight,
            onset_force_threshold_n=0.0,
            onset_max_steps=0,
            onset_weight=0.5,
            relief_force_threshold_n=0.0,
            relief_max_steps=0,
            relief_weight=0.25,
        )

    if sample_selection != "precontact_corridor":
        if sample_selection not in {
            "precontact_plus_handoff",
            "precontact_plus_handoff_relief",
        }:
            raise ValueError(
                f"Unsupported intent-lift BC sample selection: {sample_selection}"
            )

    precontact_mask = (
        ~has_contact
        & ~is_jammed
        & (in_approach_alignment_corridor | in_contact_intent_corridor)
    )
    sample_weights = np.ones(observations.shape[0], dtype=np.float32)

    if sample_selection == "precontact_corridor":
        return observations[precontact_mask], actions[precontact_mask], sample_weights[precontact_mask]

    handoff_mask = (
        has_contact
        & ~is_jammed
        & (contact_force_norm <= contact_handoff_force_threshold_n)
        & (contact_step_index > 0)
        & (contact_step_index <= contact_handoff_max_steps)
    )
    keep_mask = precontact_mask | handoff_mask
    sample_weights[handoff_mask] = np.float32(contact_handoff_weight)

    if sample_selection == "precontact_plus_handoff_relief" and contact_relief_max_steps > 0:
        relief_start_step = max(2, contact_handoff_max_steps + 1)
        relief_mask = (
            has_contact
            & ~is_jammed
            & (contact_force_norm <= contact_relief_force_threshold_n)
            & (contact_step_index >= relief_start_step)
            & (contact_step_index <= contact_relief_max_steps)
        )
        keep_mask |= relief_mask
        sample_weights[relief_mask] = np.float32(contact_relief_weight)
    return observations[keep_mask], actions[keep_mask], sample_weights[keep_mask]


def summarize_3dof_teacher_dataset(
    *,
    observations: np.ndarray,
    actions: np.ndarray,
    sample_weights: np.ndarray | None = None,
) -> dict[str, float | int]:
    if observations.shape[0] != actions.shape[0]:
        raise ValueError("observations and actions must have the same row count")
    if sample_weights is not None and sample_weights.shape[0] != observations.shape[0]:
        raise ValueError("sample_weights must match observation count")
    if observations.shape[0] == 0:
        return {
            "num_rows": 0,
            "weight_sum": 0.0,
            "mean_obs_xy_norm": 0.0,
            "mean_obs_z": 0.0,
            "mean_action_dx": 0.0,
            "mean_action_dy": 0.0,
            "mean_action_dz": 0.0,
            "mean_action_k_xy": 0.0,
            "mean_action_k_z": 0.0,
            "std_action_dx": 0.0,
            "std_action_dy": 0.0,
            "std_action_dz": 0.0,
            "std_action_k_xy": 0.0,
            "std_action_k_z": 0.0,
            "num_unique_action_rows": 0,
            "num_unique_descent_impedance_rows": 0,
        }

    xy_norm = np.linalg.norm(observations[:, :2], axis=1)
    rounded_actions = np.round(actions.astype(np.float64), decimals=6)
    rounded_descent_impedance = np.round(actions[:, 2:].astype(np.float64), decimals=6)
    return {
        "num_rows": int(observations.shape[0]),
        "weight_sum": float(sample_weights.sum()) if sample_weights is not None else float(observations.shape[0]),
        "mean_obs_xy_norm": float(np.mean(xy_norm)),
        "mean_obs_z": float(np.mean(observations[:, 2])),
        "mean_action_dx": float(np.mean(actions[:, 0])),
        "mean_action_dy": float(np.mean(actions[:, 1])),
        "mean_action_dz": float(np.mean(actions[:, 2])),
        "mean_action_k_xy": float(np.mean(actions[:, 3])),
        "mean_action_k_z": float(np.mean(actions[:, 4])),
        "std_action_dx": float(np.std(actions[:, 0])),
        "std_action_dy": float(np.std(actions[:, 1])),
        "std_action_dz": float(np.std(actions[:, 2])),
        "std_action_k_xy": float(np.std(actions[:, 3])),
        "std_action_k_z": float(np.std(actions[:, 4])),
        "num_unique_action_rows": int(np.unique(rounded_actions, axis=0).shape[0]),
        "num_unique_descent_impedance_rows": int(
            np.unique(rounded_descent_impedance, axis=0).shape[0]
        ),
    }


def _attenuate_intent_lift_teacher_actions(
    *,
    actions: np.ndarray,
    surface_height: np.ndarray,
    has_contact: np.ndarray,
    in_contact_intent_corridor: np.ndarray,
    late_descent_height_m: float,
    late_descent_dz_scale: float,
    late_descent_k_z_scale: float,
) -> np.ndarray:
    if (
        actions.shape[0] == 0
        or late_descent_height_m <= 0.0
        or (
            np.isclose(late_descent_dz_scale, 1.0)
            and np.isclose(late_descent_k_z_scale, 1.0)
        )
    ):
        return actions

    attenuated = np.asarray(actions, dtype=np.float32).copy()
    late_mask = (
        ~has_contact
        & in_contact_intent_corridor
        & (surface_height <= late_descent_height_m)
    )
    if np.any(late_mask):
        attenuated[late_mask, 2] *= np.float32(late_descent_dz_scale)
        attenuated[late_mask, 4] *= np.float32(late_descent_k_z_scale)
    return attenuated


def _attenuate_intent_lift_handoff_actions(
    *,
    actions: np.ndarray,
    has_contact: np.ndarray,
    contact_step_index: np.ndarray,
    contact_handoff_max_steps: int,
    contact_handoff_xy_scale: float,
    contact_handoff_dz_scale: float,
    contact_handoff_k_z_scale: float,
) -> np.ndarray:
    if (
        actions.shape[0] == 0
        or contact_handoff_max_steps <= 0
        or (
            np.isclose(contact_handoff_xy_scale, 1.0)
            and
            np.isclose(contact_handoff_dz_scale, 1.0)
            and np.isclose(contact_handoff_k_z_scale, 1.0)
        )
    ):
        return actions

    attenuated = np.asarray(actions, dtype=np.float32).copy()
    handoff_mask = (
        has_contact
        & (contact_step_index > 0)
        & (contact_step_index <= contact_handoff_max_steps)
    )
    if np.any(handoff_mask):
        attenuated[handoff_mask, :2] *= np.float32(contact_handoff_xy_scale)
        attenuated[handoff_mask, 2] *= np.float32(contact_handoff_dz_scale)
        attenuated[handoff_mask, 4] *= np.float32(contact_handoff_k_z_scale)
    return attenuated


def _attenuate_intent_lift_relief_actions(
    *,
    actions: np.ndarray,
    has_contact: np.ndarray,
    contact_force_norm: np.ndarray,
    contact_step_index: np.ndarray,
    contact_handoff_max_steps: int,
    contact_relief_force_threshold_n: float,
    contact_relief_max_steps: int,
    contact_relief_xy_scale: float,
    contact_relief_dz_scale: float,
    contact_relief_k_z_scale: float,
) -> np.ndarray:
    if (
        actions.shape[0] == 0
        or contact_relief_max_steps <= 0
        or (
            np.isclose(contact_relief_xy_scale, 1.0)
            and
            np.isclose(contact_relief_dz_scale, 1.0)
            and np.isclose(contact_relief_k_z_scale, 1.0)
        )
    ):
        return actions

    attenuated = np.asarray(actions, dtype=np.float32).copy()
    relief_start_step = max(2, contact_handoff_max_steps + 1)
    relief_mask = (
        has_contact
        & (contact_force_norm <= contact_relief_force_threshold_n)
        & (contact_step_index >= relief_start_step)
        & (contact_step_index <= contact_relief_max_steps)
    )
    if np.any(relief_mask):
        attenuated[relief_mask, :2] *= np.float32(contact_relief_xy_scale)
        attenuated[relief_mask, 2] *= np.float32(contact_relief_dz_scale)
        attenuated[relief_mask, 4] *= np.float32(contact_relief_k_z_scale)
    return attenuated


def _attenuate_intent_lift_relief_tail_actions(
    *,
    actions: np.ndarray,
    has_contact: np.ndarray,
    contact_force_norm: np.ndarray,
    contact_step_index: np.ndarray,
    contact_handoff_max_steps: int,
    contact_relief_force_threshold_n: float,
    contact_relief_max_steps: int,
    contact_relief_tail_start_step: int,
    contact_relief_tail_xy_scale: float,
    contact_relief_tail_dz_scale: float,
) -> np.ndarray:
    if (
        actions.shape[0] == 0
        or contact_relief_max_steps <= 0
        or contact_relief_tail_start_step <= 0
        or (
            np.isclose(contact_relief_tail_xy_scale, 1.0)
            and np.isclose(contact_relief_tail_dz_scale, 1.0)
        )
    ):
        return actions

    attenuated = np.asarray(actions, dtype=np.float32).copy()
    relief_start_step = max(2, contact_handoff_max_steps + 1, contact_relief_tail_start_step)
    relief_tail_mask = (
        has_contact
        & (contact_force_norm <= contact_relief_force_threshold_n)
        & (contact_step_index >= relief_start_step)
        & (contact_step_index <= contact_relief_max_steps)
    )
    if np.any(relief_tail_mask):
        attenuated[relief_tail_mask, :2] *= np.float32(contact_relief_tail_xy_scale)
        attenuated[relief_tail_mask, 2] *= np.float32(contact_relief_tail_dz_scale)
    return attenuated


def collect_3dof_predictor_demonstrations(
    config: ThreeDoFPPOTrainConfig,
    predictor: VecNormalizePredictor,
    episodes: int,
    *,
    reset_config: ThreeDoFResetConfig,
    env_overrides: dict[str, float] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    env = ThreeDoFInsertionEnv(
        replace(
            build_3dof_profile_config(
                config.train_uncertainty_profile,
                max_episode_steps=config.max_episode_steps,
            ),
            **config.base_env_overrides,
            **(env_overrides or {}),
            reset_config=reset_config,
        )
    )
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    sample_weights: list[float] = []
    phase_bias_applied: list[bool] = []
    has_contact: list[bool] = []
    is_jammed: list[bool] = []
    in_approach_alignment_corridor: list[bool] = []
    in_contact_intent_corridor: list[bool] = []
    contact_force_norm: list[float] = []
    contact_step_index: list[int] = []
    try:
        for episode_index in range(episodes):
            observation, _ = env.reset(seed=config.seed + 80_000 + episode_index)
            terminated = False
            truncated = False
            current_contact_step_index = 0
            while not (terminated or truncated):
                action, _ = predictor.predict(observation, deterministic=True)
                observations.append(np.asarray(observation, dtype=np.float32).copy())
                observation, _, terminated, truncated, info = env.step(action)
                actions.append(np.asarray(env.previous_action, dtype=np.float32).copy())
                step_phase_bias_applied = bool(
                    env.last_action_modifiers.get("phase_action_bias_applied", False)
                )
                step_has_contact = (
                    float(info["contact_force_norm"])
                    >= env.config.contact_reward_force_threshold_n
                )
                current_contact_step_index = (
                    current_contact_step_index + 1 if step_has_contact else 0
                )
                xy_error = float(np.linalg.norm(env.position[:2] - env.target_position[:2]))
                surface_height = float(max(env.position[2], 0.0))
                phase_bias_applied.append(step_phase_bias_applied)
                has_contact.append(step_has_contact)
                is_jammed.append(bool(info["is_jammed"]))
                in_approach_alignment_corridor.append(
                    (
                        env.config.contact_intent_trigger_height_m
                        < surface_height
                        <= env.config.approach_alignment_trigger_height_m
                    )
                    and xy_error <= env.config.approach_alignment_trigger_xy_threshold_m
                    and not step_has_contact
                )
                in_contact_intent_corridor.append(
                    surface_height <= env.config.contact_intent_trigger_height_m
                    and xy_error <= env.config.contact_intent_trigger_xy_threshold_m
                    and not step_has_contact
                )
                contact_force_norm.append(float(info["contact_force_norm"]))
                contact_step_index.append(current_contact_step_index)
                sample_weights.append(
                    float(config.phase_bias_distill_trigger_weight)
                    if step_phase_bias_applied
                    else 1.0
                )
    finally:
        env.close()

    if not observations:
        obs_dim = env.observation_space.shape[0]
        act_dim = env.action_space.shape[0]
        return (
            np.zeros((0, obs_dim), dtype=np.float32),
            np.zeros((0, act_dim), dtype=np.float32),
            np.zeros((0,), dtype=np.float32),
        )
    filtered_observations, filtered_actions, filtered_weights = _filter_phase_bias_distill_dataset(
        observations=np.stack(observations).astype(np.float32),
        actions=np.stack(actions).astype(np.float32),
        sample_weights=np.asarray(sample_weights, dtype=np.float32),
        phase_bias_applied=np.asarray(phase_bias_applied, dtype=bool),
        has_contact=np.asarray(has_contact, dtype=bool),
        is_jammed=np.asarray(is_jammed, dtype=bool),
        in_approach_alignment_corridor=np.asarray(in_approach_alignment_corridor, dtype=bool),
        in_contact_intent_corridor=np.asarray(in_contact_intent_corridor, dtype=bool),
        contact_force_norm=np.asarray(contact_force_norm, dtype=np.float32),
        contact_step_index=np.asarray(contact_step_index, dtype=np.int32),
        sample_selection=config.phase_bias_distill_sample_selection,
        contact_onset_force_threshold_n=config.phase_bias_distill_contact_onset_force_threshold_n,
        contact_onset_max_steps=config.phase_bias_distill_contact_onset_max_steps,
    )
    return filtered_observations, filtered_actions, filtered_weights


def collect_3dof_intent_lift_demonstrations(
    config: ThreeDoFPPOTrainConfig,
    episodes: int,
    *,
    reset_config: ThreeDoFResetConfig | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    policy = _build_3dof_demo_policy(config)
    env = ThreeDoFInsertionEnv(
        replace(
            build_3dof_profile_config(
                config.train_uncertainty_profile,
                max_episode_steps=config.max_episode_steps,
            ),
            **config.base_env_overrides,
            reset_config=reset_config or config.intent_lift_bc_reset_config,
        )
    )
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    has_contact: list[bool] = []
    is_jammed: list[bool] = []
    contact_force_norm: list[float] = []
    contact_step_index: list[int] = []
    episode_indices: list[int] = []
    in_approach_alignment_corridor: list[bool] = []
    in_contact_intent_corridor: list[bool] = []
    surface_heights: list[float] = []
    try:
        for episode_id in range(episodes):
            observation, _ = env.reset(seed=config.seed + 95_000 + episode_id)
            terminated = False
            truncated = False
            current_contact_step_index = 0
            while not (terminated or truncated):
                action = policy.act(observation)
                observations.append(np.asarray(observation, dtype=np.float32).copy())
                actions.append(np.asarray(action, dtype=np.float32).copy())
                observation, _, terminated, truncated, info = env.step(action)
                step_has_contact = (
                    float(info["contact_force_norm"])
                    >= env.config.contact_reward_force_threshold_n
                )
                current_contact_step_index = (
                    current_contact_step_index + 1 if step_has_contact else 0
                )
                xy_error = float(np.linalg.norm(env.position[:2] - env.target_position[:2]))
                surface_height = float(max(env.position[2], 0.0))
                has_contact.append(step_has_contact)
                is_jammed.append(bool(info["is_jammed"]))
                contact_force_norm.append(float(info["contact_force_norm"]))
                contact_step_index.append(current_contact_step_index)
                episode_indices.append(episode_id)
                surface_heights.append(surface_height)
                in_approach_alignment_corridor.append(
                    (
                        env.config.contact_intent_trigger_height_m
                        < surface_height
                        <= env.config.approach_alignment_trigger_height_m
                    )
                    and xy_error <= env.config.approach_alignment_trigger_xy_threshold_m
                    and not step_has_contact
                )
                in_contact_intent_corridor.append(
                    surface_height <= env.config.contact_intent_trigger_height_m
                    and xy_error <= env.config.contact_intent_trigger_xy_threshold_m
                    and not step_has_contact
                )
    finally:
        env.close()

    if not observations:
        obs_dim = env.observation_space.shape[0]
        act_dim = env.action_space.shape[0]
        return (
            np.zeros((0, obs_dim), dtype=np.float32),
            np.zeros((0, act_dim), dtype=np.float32),
            np.zeros((0,), dtype=np.float32),
        )
    stacked_actions = _attenuate_intent_lift_teacher_actions(
        actions=np.stack(actions).astype(np.float32),
        surface_height=np.asarray(surface_heights, dtype=np.float32),
        has_contact=np.asarray(has_contact, dtype=bool),
        in_contact_intent_corridor=np.asarray(in_contact_intent_corridor, dtype=bool),
        late_descent_height_m=config.intent_lift_bc_late_descent_height_m,
        late_descent_dz_scale=config.intent_lift_bc_late_descent_dz_scale,
        late_descent_k_z_scale=config.intent_lift_bc_late_descent_k_z_scale,
    )
    stacked_actions = _attenuate_intent_lift_handoff_actions(
        actions=stacked_actions,
        has_contact=np.asarray(has_contact, dtype=bool),
        contact_step_index=np.asarray(contact_step_index, dtype=np.int32),
        contact_handoff_max_steps=config.intent_lift_bc_contact_handoff_max_steps,
        contact_handoff_xy_scale=config.intent_lift_bc_contact_handoff_xy_scale,
        contact_handoff_dz_scale=config.intent_lift_bc_contact_handoff_dz_scale,
        contact_handoff_k_z_scale=config.intent_lift_bc_contact_handoff_k_z_scale,
    )
    stacked_actions = _attenuate_intent_lift_relief_actions(
        actions=stacked_actions,
        has_contact=np.asarray(has_contact, dtype=bool),
        contact_force_norm=np.asarray(contact_force_norm, dtype=np.float32),
        contact_step_index=np.asarray(contact_step_index, dtype=np.int32),
        contact_handoff_max_steps=config.intent_lift_bc_contact_handoff_max_steps,
        contact_relief_force_threshold_n=config.intent_lift_bc_contact_relief_force_threshold_n,
        contact_relief_max_steps=config.intent_lift_bc_contact_relief_max_steps,
        contact_relief_xy_scale=config.intent_lift_bc_contact_relief_xy_scale,
        contact_relief_dz_scale=config.intent_lift_bc_contact_relief_dz_scale,
        contact_relief_k_z_scale=config.intent_lift_bc_contact_relief_k_z_scale,
    )
    stacked_actions = _attenuate_intent_lift_relief_tail_actions(
        actions=stacked_actions,
        has_contact=np.asarray(has_contact, dtype=bool),
        contact_force_norm=np.asarray(contact_force_norm, dtype=np.float32),
        contact_step_index=np.asarray(contact_step_index, dtype=np.int32),
        contact_handoff_max_steps=config.intent_lift_bc_contact_handoff_max_steps,
        contact_relief_force_threshold_n=config.intent_lift_bc_contact_relief_force_threshold_n,
        contact_relief_max_steps=config.intent_lift_bc_contact_relief_max_steps,
        contact_relief_tail_start_step=config.intent_lift_bc_contact_relief_tail_start_step,
        contact_relief_tail_xy_scale=config.intent_lift_bc_contact_relief_tail_xy_scale,
        contact_relief_tail_dz_scale=config.intent_lift_bc_contact_relief_tail_dz_scale,
    )
    return _filter_intent_lift_bc_demo_dataset(
        observations=np.stack(observations).astype(np.float32),
        actions=stacked_actions,
        has_contact=np.asarray(has_contact, dtype=bool),
        is_jammed=np.asarray(is_jammed, dtype=bool),
        contact_force_norm=np.asarray(contact_force_norm, dtype=np.float32),
        contact_step_index=np.asarray(contact_step_index, dtype=np.int32),
        episode_index=np.asarray(episode_indices, dtype=np.int32),
        in_approach_alignment_corridor=np.asarray(
            in_approach_alignment_corridor, dtype=bool
        ),
        in_contact_intent_corridor=np.asarray(in_contact_intent_corridor, dtype=bool),
        force_threshold_n=config.intent_lift_bc_force_threshold_n,
        max_contact_steps=config.intent_lift_bc_max_contact_steps,
        precontact_bridge_steps=config.intent_lift_bc_precontact_bridge_steps,
        precontact_bridge_weight=config.intent_lift_bc_precontact_bridge_weight,
        sample_selection=config.intent_lift_bc_sample_selection,
        contact_handoff_force_threshold_n=config.intent_lift_bc_contact_handoff_force_threshold_n,
        contact_handoff_max_steps=config.intent_lift_bc_contact_handoff_max_steps,
        contact_handoff_weight=config.intent_lift_bc_contact_handoff_weight,
        contact_relief_force_threshold_n=config.intent_lift_bc_contact_relief_force_threshold_n,
        contact_relief_max_steps=config.intent_lift_bc_contact_relief_max_steps,
        contact_relief_weight=config.intent_lift_bc_contact_relief_weight,
    )


def collect_3dof_contact_stabilization_demonstrations(
    config: ThreeDoFPPOTrainConfig,
    episodes: int,
    *,
    reset_config: ThreeDoFResetConfig | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    policy = _build_3dof_demo_policy(config)
    env = ThreeDoFInsertionEnv(
        replace(
            build_3dof_profile_config(
                config.train_uncertainty_profile,
                max_episode_steps=config.max_episode_steps,
            ),
            **config.base_env_overrides,
            reset_config=reset_config or config.contact_finetune_reset_config,
        )
    )
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    has_contact: list[bool] = []
    is_jammed: list[bool] = []
    contact_force_norm: list[float] = []
    contact_step_index: list[int] = []
    episode_indices: list[int] = []
    try:
        for episode_id in range(episodes):
            observation, _ = env.reset(seed=config.seed + 90_000 + episode_id)
            terminated = False
            truncated = False
            current_contact_step_index = 0
            while not (terminated or truncated):
                action = policy.act(observation)
                observations.append(np.asarray(observation, dtype=np.float32).copy())
                actions.append(np.asarray(action, dtype=np.float32).copy())
                observation, _, terminated, truncated, info = env.step(action)
                step_has_contact = (
                    float(info["contact_force_norm"])
                    >= env.config.contact_reward_force_threshold_n
                )
                current_contact_step_index = (
                    current_contact_step_index + 1 if step_has_contact else 0
                )
                has_contact.append(step_has_contact)
                is_jammed.append(bool(info["is_jammed"]))
                contact_force_norm.append(float(info["contact_force_norm"]))
                contact_step_index.append(current_contact_step_index)
                episode_indices.append(episode_id)
    finally:
        env.close()

    if not observations:
        obs_dim = env.observation_space.shape[0]
        act_dim = env.action_space.shape[0]
        return (
            np.zeros((0, obs_dim), dtype=np.float32),
            np.zeros((0, act_dim), dtype=np.float32),
            np.zeros((0,), dtype=np.float32),
        )
    return _filter_stabilization_bc_demo_dataset(
        observations=np.stack(observations).astype(np.float32),
        actions=np.stack(actions).astype(np.float32),
        has_contact=np.asarray(has_contact, dtype=bool),
        is_jammed=np.asarray(is_jammed, dtype=bool),
        contact_force_norm=np.asarray(contact_force_norm, dtype=np.float32),
        contact_step_index=np.asarray(contact_step_index, dtype=np.int32),
        episode_index=np.asarray(episode_indices, dtype=np.int32),
        force_threshold_n=config.stabilization_bc_force_threshold_n,
        max_contact_steps=config.stabilization_bc_max_contact_steps,
        precontact_bridge_steps=config.stabilization_bc_precontact_bridge_steps,
        precontact_bridge_weight=config.stabilization_bc_precontact_bridge_weight,
        onset_force_threshold_n=config.stabilization_bc_onset_force_threshold_n,
        onset_max_steps=config.stabilization_bc_onset_max_steps,
        onset_weight=config.stabilization_bc_onset_weight,
        relief_force_threshold_n=config.stabilization_bc_relief_force_threshold_n,
        relief_max_steps=config.stabilization_bc_relief_max_steps,
        relief_weight=config.stabilization_bc_relief_weight,
        relief_tail_start_step=config.stabilization_bc_relief_tail_start_step,
        relief_tail_weight=config.stabilization_bc_relief_tail_weight,
        relief_tail_force_threshold_n=(
            config.stabilization_bc_relief_tail_force_threshold_n
        ),
        relief_tail_max_steps=config.stabilization_bc_relief_tail_max_steps,
        relief_xy_scale=config.stabilization_bc_relief_xy_scale,
        relief_dz_scale=config.stabilization_bc_relief_dz_scale,
        relief_tail_xy_scale=config.stabilization_bc_relief_tail_xy_scale,
        relief_tail_dz_scale=config.stabilization_bc_relief_tail_dz_scale,
    )


def _behavior_clone_3dof_stage(
    *,
    model: PPO,
    vec_env: VecNormalize,
    config: ThreeDoFPPOTrainConfig,
    rollout_episodes: int,
    pretrain_steps: int,
    reset_config: ThreeDoFResetConfig,
    action_loss_weights: tuple[float, float, float, float, float] | None = None,
    freeze_pose_head: bool = False,
    demo_dataset: ThreeDoFDemoDataset | None = None,
    actor_only: bool = False,
    update_obs_stats: bool = True,
    batch_size: int | None = None,
) -> None:
    if demo_dataset is None:
        demo_dataset = _collect_3dof_demo_dataset(
            config,
            episodes=rollout_episodes,
            reset_config=reset_config,
        )
    _behavior_clone_3dof_dataset(
        model=model,
        vec_env=vec_env,
        config=config,
        observations=demo_dataset.observations,
        actions=demo_dataset.actions,
        action_loss_weights=action_loss_weights,
        freeze_pose_head=freeze_pose_head,
        pretrain_steps=pretrain_steps,
        actor_only=actor_only,
        update_obs_stats=update_obs_stats,
        batch_size=batch_size,
    )


def _behavior_clone_3dof_dataset(
    *,
    model: PPO,
    vec_env: VecNormalize,
    config: ThreeDoFPPOTrainConfig,
    observations: np.ndarray,
    actions: np.ndarray,
    pretrain_steps: int,
    sample_weights: np.ndarray | None = None,
    action_loss_weights: tuple[float, float, float, float, float] | None = None,
    freeze_pose_head: bool = False,
    actor_only: bool = False,
    update_obs_stats: bool = True,
    batch_size: int | None = None,
) -> None:
    if pretrain_steps <= 0 or observations.shape[0] == 0:
        return

    if config.norm_obs:
        if update_obs_stats:
            vec_env.obs_rms.update(observations)
        observations = vec_env.normalize_obs(observations)

    policy = model.policy
    policy.set_training_mode(True)
    obs_tensor = torch.as_tensor(observations, device=policy.device, dtype=torch.float32)
    action_tensor = torch.as_tensor(actions, device=policy.device, dtype=torch.float32)
    sample_weight_tensor = None
    if sample_weights is not None:
        if sample_weights.shape[0] != observations.shape[0]:
            raise ValueError("sample_weights must match observation count")
        sample_weight_tensor = torch.as_tensor(
            sample_weights,
            device=policy.device,
            dtype=torch.float32,
        )
    use_weighted_mse = action_loss_weights is not None
    weight_tensor = None
    if use_weighted_mse:
        weight_tensor = torch.as_tensor(
            action_loss_weights,
            device=policy.device,
            dtype=torch.float32,
        ).view(1, -1)
        if weight_tensor.shape[1] != action_tensor.shape[1]:
            raise ValueError("action_loss_weights must match action dimension")
    gradient_hooks: list[torch.utils.hooks.RemovableHandle] = []
    original_requires_grad: dict[torch.nn.Parameter, bool] = {}
    if freeze_pose_head:
        for parameter in policy.parameters():
            original_requires_grad[parameter] = parameter.requires_grad
            parameter.requires_grad = False
        policy.action_net.weight.requires_grad = True
        if policy.action_net.bias is not None:
            policy.action_net.bias.requires_grad = True
        if hasattr(policy, "log_std"):
            policy.log_std.requires_grad = True

        stiffness_rows = torch.tensor([0.0, 0.0, 0.0, 1.0, 1.0], device=policy.device).view(-1, 1)
        gradient_hooks.append(
            policy.action_net.weight.register_hook(lambda grad: grad * stiffness_rows)
        )
        if policy.action_net.bias is not None:
            stiffness_dims = torch.tensor([0.0, 0.0, 0.0, 1.0, 1.0], device=policy.device)
            gradient_hooks.append(
                policy.action_net.bias.register_hook(lambda grad: grad * stiffness_dims)
            )
        if hasattr(policy, "log_std"):
            std_dims = torch.tensor([0.0, 0.0, 0.0, 1.0, 1.0], device=policy.device)
            gradient_hooks.append(
                policy.log_std.register_hook(lambda grad: grad * std_dims)
            )
    if actor_only:
        optimizer_params = _collect_3dof_actor_parameters(policy)
    else:
        optimizer_params = [parameter for parameter in policy.parameters() if parameter.requires_grad]
    optimizer = torch.optim.Adam(optimizer_params, lr=config.bc_learning_rate)
    effective_batch_size = max(1, int(batch_size or config.bc_batch_size))

    try:
        for _ in range(pretrain_steps):
            permutation = torch.randperm(obs_tensor.shape[0], device=policy.device)
            for start in range(0, obs_tensor.shape[0], effective_batch_size):
                batch_indices = permutation[start : start + effective_batch_size]
                batch_obs = obs_tensor[batch_indices]
                batch_actions = action_tensor[batch_indices]
                batch_sample_weights = None
                if sample_weight_tensor is not None:
                    batch_sample_weights = sample_weight_tensor[batch_indices]
                distribution = policy.get_distribution(batch_obs)
                if use_weighted_mse:
                    predicted_actions = distribution.distribution.mean
                    squared_error = (predicted_actions - batch_actions) ** 2
                    per_sample_loss = (squared_error * weight_tensor).mean(dim=1)
                else:
                    per_sample_loss = -distribution.log_prob(batch_actions)
                if batch_sample_weights is not None:
                    normalizer = batch_sample_weights.sum().clamp_min(1e-6)
                    loss = (per_sample_loss * batch_sample_weights).sum() / normalizer
                else:
                    loss = per_sample_loss.mean()
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
    finally:
        for hook in gradient_hooks:
            hook.remove()
        for parameter, requires_grad in original_requires_grad.items():
            parameter.requires_grad = requires_grad


def _run_3dof_dapg_stage(
    *,
    model: PPO,
    vec_env: VecNormalize,
    config: ThreeDoFPPOTrainConfig,
    demo_dataset: ThreeDoFDemoDataset,
) -> dict[str, object]:
    chunk_timesteps = max(int(config.n_steps * config.n_envs), 1)
    remaining_timesteps = int(config.total_timesteps)
    num_chunks = 0
    num_demo_updates = 0

    while remaining_timesteps > 0:
        current_chunk_timesteps = min(chunk_timesteps, remaining_timesteps)
        model.learn(total_timesteps=current_chunk_timesteps, reset_num_timesteps=False)
        remaining_timesteps -= current_chunk_timesteps
        num_chunks += 1
        if current_chunk_timesteps != chunk_timesteps:
            continue
        if config.dapg_mini_updates_per_chunk <= 0:
            continue
        _behavior_clone_3dof_stage(
            model=model,
            vec_env=vec_env,
            config=config,
            rollout_episodes=0,
            pretrain_steps=config.dapg_mini_updates_per_chunk,
            reset_config=config.bc_reset_config,
            demo_dataset=demo_dataset,
            actor_only=True,
            update_obs_stats=False,
            batch_size=config.dapg_demo_batch_size,
        )
        if demo_dataset.observations.shape[0] > 0:
            num_demo_updates += int(config.dapg_mini_updates_per_chunk)

    return {
        "num_chunks": num_chunks,
        "num_demo_updates": num_demo_updates,
        "demo_updates_per_chunk": int(config.dapg_mini_updates_per_chunk),
        "demo_batch_size": int(config.dapg_demo_batch_size),
    }


def _build_3dof_training_summary(
    *,
    config: ThreeDoFPPOTrainConfig,
    demo_dataset: ThreeDoFDemoDataset,
    dapg_summary: dict[str, object] | None = None,
) -> dict[str, object]:
    summary = {
        "dapg_enabled": bool(config.dapg_enabled),
        "num_chunks": 0,
        "num_demo_updates": 0,
        "demo_updates_per_chunk": int(config.dapg_mini_updates_per_chunk),
        "demo_batch_size": int(config.dapg_demo_batch_size),
        "demo_dataset_id": demo_dataset.dataset_id,
        "demo_dataset_path": demo_dataset.dataset_path,
        "demo_dataset_hash": demo_dataset.dataset_hash,
        **_build_3dof_teacher_metadata(config),
    }
    if dapg_summary:
        summary.update(dapg_summary)
    return summary


def _phase_bias_distill_3dof_stage(
    *,
    model: PPO,
    vec_env: VecNormalize,
    config: ThreeDoFPPOTrainConfig,
) -> None:
    if (
        config.phase_bias_distill_rollout_episodes <= 0
        or config.phase_bias_distill_pretrain_steps <= 0
        or not config.phase_bias_distill_env_overrides
    ):
        return

    predictor = VecNormalizePredictor(model=model, vec_normalize=vec_env)
    observations, actions, sample_weights = collect_3dof_predictor_demonstrations(
        config,
        predictor,
        episodes=config.phase_bias_distill_rollout_episodes,
        reset_config=config.phase_bias_distill_reset_config,
        env_overrides=config.phase_bias_distill_env_overrides,
    )
    _behavior_clone_3dof_dataset(
        model=model,
        vec_env=vec_env,
        config=config,
        observations=observations,
        actions=actions,
        pretrain_steps=config.phase_bias_distill_pretrain_steps,
        sample_weights=sample_weights,
    )


def _contact_stabilization_bc_3dof_stage(
    *,
    model: PPO,
    vec_env: VecNormalize,
    config: ThreeDoFPPOTrainConfig,
) -> None:
    if (
        config.stabilization_bc_rollout_episodes <= 0
        or config.stabilization_bc_pretrain_steps <= 0
    ):
        return

    observations, actions, sample_weights = collect_3dof_contact_stabilization_demonstrations(
        config,
        episodes=config.stabilization_bc_rollout_episodes,
        reset_config=config.stabilization_bc_reset_config,
    )
    _behavior_clone_3dof_dataset(
        model=model,
        vec_env=vec_env,
        config=config,
        observations=observations,
        actions=actions,
        pretrain_steps=config.stabilization_bc_pretrain_steps,
        sample_weights=sample_weights,
        action_loss_weights=config.stabilization_bc_action_loss_weights,
        freeze_pose_head=config.stabilization_bc_freeze_pose_head,
    )


def _intent_lift_bc_3dof_stage(
    *,
    model: PPO,
    vec_env: VecNormalize,
    config: ThreeDoFPPOTrainConfig,
) -> None:
    if config.intent_lift_bc_rollout_episodes <= 0 or config.intent_lift_bc_pretrain_steps <= 0:
        return
    if config.intent_lift_bc_legacy_stabilization_semantics:
        intent_config = replace(
            config,
            stabilization_bc_rollout_episodes=config.intent_lift_bc_rollout_episodes,
            stabilization_bc_pretrain_steps=config.intent_lift_bc_pretrain_steps,
            stabilization_bc_force_threshold_n=config.intent_lift_bc_force_threshold_n,
            stabilization_bc_max_contact_steps=config.intent_lift_bc_max_contact_steps,
            stabilization_bc_reset_config=config.intent_lift_bc_reset_config,
            stabilization_bc_precontact_bridge_steps=config.intent_lift_bc_precontact_bridge_steps,
            stabilization_bc_precontact_bridge_weight=config.intent_lift_bc_precontact_bridge_weight,
            stabilization_bc_action_loss_weights=config.intent_lift_bc_action_loss_weights,
            stabilization_bc_freeze_pose_head=config.intent_lift_bc_freeze_pose_head,
        )
        _contact_stabilization_bc_3dof_stage(
            model=model,
            vec_env=vec_env,
            config=intent_config,
        )
        return
    observations, actions, sample_weights = collect_3dof_intent_lift_demonstrations(
        config,
        episodes=config.intent_lift_bc_rollout_episodes,
        reset_config=config.intent_lift_bc_reset_config,
    )
    _behavior_clone_3dof_dataset(
        model=model,
        vec_env=vec_env,
        config=config,
        observations=observations,
        actions=actions,
        sample_weights=sample_weights,
        pretrain_steps=config.intent_lift_bc_pretrain_steps,
        action_loss_weights=config.intent_lift_bc_action_loss_weights,
        freeze_pose_head=config.intent_lift_bc_freeze_pose_head,
    )


def train_3dof_ppo_agent(config: ThreeDoFPPOTrainConfig) -> ThreeDoFPPOArtifacts:
    vec_env = create_3dof_training_vec_env(config)
    model = PPO(
        "MlpPolicy",
        vec_env,
        n_steps=config.n_steps,
        batch_size=config.batch_size,
        n_epochs=config.n_epochs,
        learning_rate=config.learning_rate,
        gamma=config.gamma,
        gae_lambda=config.gae_lambda,
        ent_coef=config.ent_coef,
        vf_coef=config.vf_coef,
        clip_range=config.clip_range,
        seed=config.seed,
        verbose=config.verbose,
    )
    bc_demo_dataset = _collect_3dof_demo_dataset(
        config,
        episodes=config.bc_rollout_episodes,
        reset_config=config.bc_reset_config,
    )
    _behavior_clone_3dof_stage(
        model=model,
        vec_env=vec_env,
        config=config,
        rollout_episodes=config.bc_rollout_episodes,
        pretrain_steps=config.bc_pretrain_steps,
        reset_config=config.bc_reset_config,
        demo_dataset=bc_demo_dataset,
    )
    if config.dapg_enabled:
        training_summary = _build_3dof_training_summary(
            config=config,
            demo_dataset=bc_demo_dataset,
            dapg_summary=_run_3dof_dapg_stage(
                model=model,
                vec_env=vec_env,
                config=config,
                demo_dataset=bc_demo_dataset,
            ),
        )
    else:
        model.learn(total_timesteps=config.total_timesteps)
        training_summary = _build_3dof_training_summary(
            config=config,
            demo_dataset=bc_demo_dataset,
        )
    _behavior_clone_3dof_stage(
        model=model,
        vec_env=vec_env,
        config=config,
        rollout_episodes=config.approach_bc_rollout_episodes,
        pretrain_steps=config.approach_bc_pretrain_steps,
        reset_config=config.approach_bc_reset_config,
        action_loss_weights=config.approach_bc_action_loss_weights,
    )
    if config.contact_bc_after_finetune:
        vec_env = _run_3dof_contact_finetune_stage(
            model=model,
            vec_env=vec_env,
            config=config,
        )
        _behavior_clone_3dof_stage(
            model=model,
            vec_env=vec_env,
            config=config,
            rollout_episodes=config.contact_bc_rollout_episodes,
            pretrain_steps=config.contact_bc_pretrain_steps,
            reset_config=config.contact_bc_reset_config,
            action_loss_weights=config.contact_bc_action_loss_weights,
            freeze_pose_head=config.contact_bc_freeze_pose_head,
        )
    else:
        _behavior_clone_3dof_stage(
            model=model,
            vec_env=vec_env,
            config=config,
            rollout_episodes=config.contact_bc_rollout_episodes,
            pretrain_steps=config.contact_bc_pretrain_steps,
            reset_config=config.contact_bc_reset_config,
            action_loss_weights=config.contact_bc_action_loss_weights,
            freeze_pose_head=config.contact_bc_freeze_pose_head,
        )
        vec_env = _run_3dof_contact_finetune_stage(
            model=model,
            vec_env=vec_env,
            config=config,
        )
    _phase_bias_distill_3dof_stage(
        model=model,
        vec_env=vec_env,
        config=config,
    )
    if not config.intent_lift_bc_after_stabilization:
        _intent_lift_bc_3dof_stage(
            model=model,
            vec_env=vec_env,
            config=config,
        )
    _contact_stabilization_bc_3dof_stage(
        model=model,
        vec_env=vec_env,
        config=config,
    )
    if config.intent_lift_bc_after_stabilization:
        _intent_lift_bc_3dof_stage(
            model=model,
            vec_env=vec_env,
            config=config,
    )
    vec_env.training = False
    vec_env.norm_reward = False
    return ThreeDoFPPOArtifacts(
        model=model,
        vec_normalize=vec_env,
        train_config=config,
        training_summary=training_summary,
    )
