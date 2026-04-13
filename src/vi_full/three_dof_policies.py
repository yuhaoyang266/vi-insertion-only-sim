from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

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
class ThreeDoFPoseOnlyPolicy:
    name: str = "three_dof_pose_only"

    def act(self, observation: np.ndarray) -> np.ndarray:
        cartesian = _cartesian_action_from_observation(observation)
        return np.concatenate(
            [cartesian, np.zeros(2, dtype=np.float32)], dtype=np.float32
        )


@dataclass(frozen=True, slots=True)
class ThreeDoFFixedImpedancePolicy:
    name: str = "three_dof_fixed_impedance"
    stiffness_xy: float = 0.6
    stiffness_z: float = 0.6

    def act(self, observation: np.ndarray) -> np.ndarray:
        cartesian = _cartesian_action_from_observation(observation)
        return np.concatenate(
            [
                cartesian,
                np.array([self.stiffness_xy, self.stiffness_z], dtype=np.float32),
            ],
            dtype=np.float32,
        )


@dataclass(frozen=True, slots=True)
class ThreeDoFVariableImpedancePolicy:
    name: str = "three_dof_variable_impedance"
    contact_force_threshold: float = 0.2
    near_contact_depth_m: float = 0.008

    def act(self, observation: np.ndarray) -> np.ndarray:
        cartesian = _cartesian_action_from_observation(observation)
        rel_pos = np.asarray(observation[:3], dtype=np.float32)
        force_norm = float(np.linalg.norm(np.asarray(observation[6:9], dtype=np.float32)))
        lateral_error = float(np.linalg.norm(rel_pos[:2]))
        contact = force_norm >= self.contact_force_threshold
        near_contact = float(rel_pos[2]) <= self.near_contact_depth_m

        stiffness_xy = 0.65 if lateral_error > 0.0015 else 0.4
        stiffness_z = 0.75 if float(rel_pos[2]) > self.near_contact_depth_m else 0.35
        if near_contact:
            cartesian[2] = np.clip(cartesian[2], -0.35, 0.25)

        if contact:
            cartesian[:2] = np.clip(cartesian[:2] * 1.15, -1.0, 1.0)
            cartesian[2] = np.clip(cartesian[2], -0.08, 0.25)
            stiffness_xy *= 0.35
            stiffness_z *= 0.25

        return np.concatenate(
            [cartesian, np.array([stiffness_xy, stiffness_z], dtype=np.float32)],
            dtype=np.float32,
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
