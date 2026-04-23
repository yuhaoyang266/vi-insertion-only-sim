from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np

from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_config import ThreeDoFInsertionConfig


DEFAULT_UNCERTAINTY_PROFILES = (
    "nominal",
    "tight_clearance",
    "high_friction",
    "offset_bias",
    "noisy_force",
)

CLEARANCE_SHIFT_PROFILES = (
    "clearance_easy",
    "nominal",
    "clearance_hard",
)

POSE_PERTURBATION_PROFILES = (
    "pose_perturb_mild",
    "pose_perturb_moderate",
    "pose_perturb_severe",
)


def build_3dof_profile_config(
    profile_name: str,
    *,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
) -> ThreeDoFInsertionConfig:
    base = ThreeDoFInsertionConfig(max_episode_steps=max_episode_steps)
    if profile_name == "nominal":
        return base
    if profile_name == "clearance_easy":
        return replace(
            base,
            clearance_range_m=(0.00095, 0.00135),
        )
    if profile_name == "clearance_hard":
        return replace(
            base,
            clearance_range_m=(0.00045, 0.00075),
        )
    if profile_name == "tight_clearance":
        return replace(
            base,
            clearance_range_m=(0.00045, 0.00075),
            hole_xy_offset_range_m=0.0011,
        )
    if profile_name == "high_friction":
        return replace(
            base,
            wall_friction_range=(0.28, 0.46),
            force_noise_std_range=(0.03, 0.10),
        )
    if profile_name == "offset_bias":
        return replace(
            base,
            hole_xy_offset_range_m=0.0018,
            clearance_range_m=(0.00065, 0.0010),
        )
    if profile_name == "noisy_force":
        return replace(
            base,
            force_noise_std_range=(0.12, 0.25),
            wall_friction_range=(0.15, 0.30),
        )
    if profile_name == "pose_perturb_mild":
        return replace(
            base,
            pose_target_bias_xy_m=0.0002,
            orientation_perturbation_deg=1.5,
        )
    if profile_name == "pose_perturb_moderate":
        return replace(
            base,
            pose_target_bias_xy_m=0.0004,
            orientation_perturbation_deg=3.0,
        )
    if profile_name == "pose_perturb_severe":
        return replace(
            base,
            pose_target_bias_xy_m=0.0006,
            orientation_perturbation_deg=4.5,
        )
    raise ValueError(f"Unknown uncertainty profile: {profile_name}")


def describe_3dof_pose_perturbation_profile(profile_name: str) -> dict[str, Any]:
    config = build_3dof_profile_config(profile_name)
    min_clearance, max_clearance = config.clearance_range_m
    orientation_drift_per_m_descent = float(
        np.tan(np.deg2rad(config.orientation_perturbation_deg))
    )
    orientation_lateral_drift_at_target_depth_m = float(
        config.target_insertion_depth_m * orientation_drift_per_m_descent
    )
    worst_case_lateral_offset_at_target_depth_m = float(
        config.pose_target_bias_xy_m + orientation_lateral_drift_at_target_depth_m
    )
    return {
        "profile_name": profile_name,
        "pose_target_bias_xy_m": float(config.pose_target_bias_xy_m),
        "orientation_perturbation_deg": float(config.orientation_perturbation_deg),
        "observation_frame": "perceived_target_position",
        "contact_reward_frame": "hidden_contact_target_position",
        "nominal_clearance_range_m": [float(min_clearance), float(max_clearance)],
        "target_insertion_depth_m": float(config.target_insertion_depth_m),
        "orientation_lateral_drift_per_mm_descent_mm": orientation_drift_per_m_descent,
        "orientation_lateral_drift_at_target_depth_m": (
            orientation_lateral_drift_at_target_depth_m
        ),
        "pose_bias_to_min_clearance_ratio": float(
            config.pose_target_bias_xy_m / max(min_clearance, 1e-12)
        ),
        "worst_case_lateral_offset_at_target_depth_m": (
            worst_case_lateral_offset_at_target_depth_m
        ),
        "worst_case_offset_to_min_clearance_ratio": float(
            worst_case_lateral_offset_at_target_depth_m / max(min_clearance, 1e-12)
        ),
    }
