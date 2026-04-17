from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from typing import Literal

import numpy as np

from vi_full.three_dof_classical_controllers import (
    ThreeDoFCompliantSearchController,
    ThreeDoFHybridPositionForceController,
    ThreeDoFTunedImpedanceController,
)


def _cartesian_action_from_observation(observation: np.ndarray) -> np.ndarray:
    rel_pos = np.asarray(observation[:3], dtype=np.float32)
    normalization = np.array([0.004, 0.004, 0.006], dtype=np.float32)
    return np.clip(-rel_pos / normalization, -1.0, 1.0)


@dataclass(frozen=True, slots=True)
class ThreeDoFTeacherSpec:
    preset_name: str
    motion_rule: Literal["pose_feedback", "contact_aware_variable_motion"]
    impedance_rule: Literal["fixed", "contact_aware_variable_impedance"]
    contact_force_threshold: float
    near_contact_depth_m: float
    lateral_error_switch_m: float
    contact_xy_gain: float
    near_contact_dz_min: float
    contact_dz_min: float
    dz_max: float
    fixed_stiffness_xy: float
    fixed_stiffness_z: float
    high_xy_stiffness: float
    low_xy_stiffness: float
    high_z_stiffness: float
    low_z_stiffness: float
    contact_xy_stiffness_scale: float
    contact_z_stiffness_scale: float


def _build_3dof_teacher_spec_registry() -> dict[str, ThreeDoFTeacherSpec]:
    shared_kwargs = {
        "contact_force_threshold": 0.2,
        "near_contact_depth_m": 0.008,
        "lateral_error_switch_m": 0.0015,
        "contact_xy_gain": 1.15,
        "near_contact_dz_min": -0.35,
        "contact_dz_min": -0.08,
        "dz_max": 0.25,
        "fixed_stiffness_xy": 0.6,
        "fixed_stiffness_z": 0.6,
        "high_xy_stiffness": 0.65,
        "low_xy_stiffness": 0.4,
        "high_z_stiffness": 0.75,
        "low_z_stiffness": 0.35,
        "contact_xy_stiffness_scale": 0.35,
        "contact_z_stiffness_scale": 0.25,
    }
    return {
        "teacher_variable_variable": ThreeDoFTeacherSpec(
            preset_name="teacher_variable_variable",
            motion_rule="contact_aware_variable_motion",
            impedance_rule="contact_aware_variable_impedance",
            **shared_kwargs,
        ),
        "teacher_variable_fixed": ThreeDoFTeacherSpec(
            preset_name="teacher_variable_fixed",
            motion_rule="contact_aware_variable_motion",
            impedance_rule="fixed",
            **shared_kwargs,
        ),
        "teacher_pose_variable": ThreeDoFTeacherSpec(
            preset_name="teacher_pose_variable",
            motion_rule="pose_feedback",
            impedance_rule="contact_aware_variable_impedance",
            **shared_kwargs,
        ),
        "teacher_pose_fixed": ThreeDoFTeacherSpec(
            preset_name="teacher_pose_fixed",
            motion_rule="pose_feedback",
            impedance_rule="fixed",
            **shared_kwargs,
        ),
        "teacher_pose_zero": ThreeDoFTeacherSpec(
            preset_name="teacher_pose_zero",
            motion_rule="pose_feedback",
            impedance_rule="fixed",
            **{
                **shared_kwargs,
                "fixed_stiffness_xy": 0.0,
                "fixed_stiffness_z": 0.0,
            },
        ),
    }


def resolve_3dof_teacher_spec(
    *,
    policy_name: str | None = None,
    teacher_spec: ThreeDoFTeacherSpec | None = None,
) -> ThreeDoFTeacherSpec:
    if teacher_spec is not None:
        return teacher_spec

    resolved_policy_name = "variable_impedance" if policy_name is None else policy_name
    alias_map = {
        "variable_impedance": "teacher_variable_variable",
        "fixed_impedance": "teacher_pose_fixed",
        "pose_only": "teacher_pose_zero",
    }
    preset_name = alias_map.get(resolved_policy_name, resolved_policy_name)
    registry = _build_3dof_teacher_spec_registry()
    if preset_name not in registry:
        raise ValueError(f"Unknown 3DoF teacher preset: {resolved_policy_name}")
    return registry[preset_name]


def build_3dof_teacher_metadata(
    *,
    policy_name: str | None = None,
    teacher_spec: ThreeDoFTeacherSpec | None = None,
) -> dict[str, object]:
    resolved_policy_name = "variable_impedance" if policy_name is None else policy_name
    resolved_teacher_spec = resolve_3dof_teacher_spec(
        policy_name=resolved_policy_name,
        teacher_spec=teacher_spec,
    )
    return {
        "bc_demo_policy_name": resolved_policy_name,
        "bc_demo_teacher_spec": asdict(resolved_teacher_spec),
        "teacher_preset_name": resolved_teacher_spec.preset_name,
        "teacher_motion_rule": resolved_teacher_spec.motion_rule,
        "teacher_impedance_rule": resolved_teacher_spec.impedance_rule,
    }


def compute_3dof_teacher_motion_action(
    spec: ThreeDoFTeacherSpec,
    observation: np.ndarray,
) -> np.ndarray:
    cartesian = _cartesian_action_from_observation(observation)
    if spec.motion_rule == "pose_feedback":
        return cartesian
    if spec.motion_rule != "contact_aware_variable_motion":
        raise ValueError(f"Unknown 3DoF teacher motion rule: {spec.motion_rule}")

    rel_pos = np.asarray(observation[:3], dtype=np.float32)
    force_norm = float(np.linalg.norm(np.asarray(observation[6:9], dtype=np.float32)))
    contact = force_norm >= spec.contact_force_threshold
    near_contact = float(rel_pos[2]) <= spec.near_contact_depth_m

    if near_contact:
        cartesian[2] = np.clip(cartesian[2], spec.near_contact_dz_min, spec.dz_max)

    if contact:
        cartesian[:2] = np.clip(cartesian[:2] * spec.contact_xy_gain, -1.0, 1.0)
        cartesian[2] = np.clip(cartesian[2], spec.contact_dz_min, spec.dz_max)
    return cartesian


def compute_3dof_teacher_impedance_action(
    spec: ThreeDoFTeacherSpec,
    observation: np.ndarray,
) -> np.ndarray:
    if spec.impedance_rule == "fixed":
        return np.array(
            [spec.fixed_stiffness_xy, spec.fixed_stiffness_z],
            dtype=np.float32,
        )
    if spec.impedance_rule != "contact_aware_variable_impedance":
        raise ValueError(f"Unknown 3DoF teacher impedance rule: {spec.impedance_rule}")

    rel_pos = np.asarray(observation[:3], dtype=np.float32)
    force_norm = float(np.linalg.norm(np.asarray(observation[6:9], dtype=np.float32)))
    lateral_error = float(np.linalg.norm(rel_pos[:2]))
    contact = force_norm >= spec.contact_force_threshold

    stiffness_xy = (
        spec.high_xy_stiffness
        if lateral_error > spec.lateral_error_switch_m
        else spec.low_xy_stiffness
    )
    stiffness_z = (
        spec.high_z_stiffness
        if float(rel_pos[2]) > spec.near_contact_depth_m
        else spec.low_z_stiffness
    )
    if contact:
        stiffness_xy *= spec.contact_xy_stiffness_scale
        stiffness_z *= spec.contact_z_stiffness_scale
    return np.array([stiffness_xy, stiffness_z], dtype=np.float32)


def compose_3dof_teacher_action(
    spec: ThreeDoFTeacherSpec,
    observation: np.ndarray,
) -> np.ndarray:
    cartesian = compute_3dof_teacher_motion_action(spec, observation)
    impedance = compute_3dof_teacher_impedance_action(spec, observation)
    return np.concatenate([cartesian, impedance], dtype=np.float32)


@dataclass(frozen=True, slots=True)
class ThreeDoFPoseOnlyPolicy:
    name: str = "three_dof_pose_only"

    def act(self, observation: np.ndarray) -> np.ndarray:
        return compose_3dof_teacher_action(
            resolve_3dof_teacher_spec(policy_name="pose_only"),
            observation,
        )


@dataclass(frozen=True, slots=True)
class ThreeDoFFixedImpedancePolicy:
    name: str = "three_dof_fixed_impedance"
    stiffness_xy: float = 0.6
    stiffness_z: float = 0.6

    def act(self, observation: np.ndarray) -> np.ndarray:
        return compose_3dof_teacher_action(
            replace(
                resolve_3dof_teacher_spec(policy_name="fixed_impedance"),
                fixed_stiffness_xy=self.stiffness_xy,
                fixed_stiffness_z=self.stiffness_z,
            ),
            observation,
        )


@dataclass(frozen=True, slots=True)
class ThreeDoFVariableImpedancePolicy:
    name: str = "three_dof_variable_impedance"
    contact_force_threshold: float = 0.2
    near_contact_depth_m: float = 0.008

    def act(self, observation: np.ndarray) -> np.ndarray:
        return compose_3dof_teacher_action(
            replace(
                resolve_3dof_teacher_spec(policy_name="variable_impedance"),
                contact_force_threshold=self.contact_force_threshold,
                near_contact_depth_m=self.near_contact_depth_m,
            ),
            observation,
        )


def build_3dof_handcrafted_policy_registry() -> dict[str, Callable[[], object]]:
    return {
        "pose_only": ThreeDoFPoseOnlyPolicy,
        "fixed_impedance": ThreeDoFFixedImpedancePolicy,
        "variable_impedance": ThreeDoFVariableImpedancePolicy,
        "hybrid_position_force": ThreeDoFHybridPositionForceController,
        "compliant_search": ThreeDoFCompliantSearchController,
        "tuned_impedance": ThreeDoFTunedImpedanceController,
    }
