from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _cartesian_action_from_observation(
    observation: np.ndarray, step_scale_m: float = 0.01
) -> np.ndarray:
    target_delta = np.asarray(observation[6:9], dtype=np.float32)
    return np.clip(target_delta / step_scale_m, -1.0, 1.0)


@dataclass(frozen=True, slots=True)
class PoseOnlyPolicy:
    name: str = "pose_only"

    def act(self, observation: np.ndarray) -> np.ndarray:
        cartesian = _cartesian_action_from_observation(observation)
        return np.concatenate(
            [cartesian, np.zeros(2, dtype=np.float32)], dtype=np.float32
        )


@dataclass(frozen=True, slots=True)
class FixedImpedancePolicy:
    name: str = "fixed_impedance"
    stiffness_xy: float = 0.8
    stiffness_z: float = 0.8

    def act(self, observation: np.ndarray) -> np.ndarray:
        cartesian = _cartesian_action_from_observation(observation)
        impedance = np.array([self.stiffness_xy, self.stiffness_z], dtype=np.float32)
        return np.concatenate([cartesian, impedance], dtype=np.float32)


@dataclass(frozen=True, slots=True)
class VariableImpedanceHeuristicPolicy:
    name: str = "variable_impedance"

    def act(self, observation: np.ndarray) -> np.ndarray:
        cartesian = _cartesian_action_from_observation(observation)
        target_delta = np.asarray(observation[6:9], dtype=np.float32)
        xy_error = float(np.linalg.norm(target_delta[:2]))
        z_error = float(abs(target_delta[2]))
        contact_count_signal = float(observation[12]) if observation.shape[0] > 12 else 0.0
        contact_force_signal = float(observation[13]) if observation.shape[0] > 13 else 0.0
        contact_signal = max(contact_count_signal, contact_force_signal)

        stiffness_xy = 0.2 if xy_error < 0.003 else 0.8
        stiffness_z = 0.9 if z_error > 0.01 else 0.5
        if contact_signal > 0.0:
            cartesian[2] *= 0.2
            if xy_error > 0.0015:
                cartesian[:2] = np.clip(cartesian[:2] * 1.2, -1.0, 1.0)
                cartesian[2] = np.clip(cartesian[2], -0.2, 0.2)
            else:
                cartesian[:2] *= 0.5
            stiffness_xy *= 0.4
            stiffness_z *= 0.8
        impedance = np.array([stiffness_xy, stiffness_z], dtype=np.float32)
        return np.concatenate([cartesian, impedance], dtype=np.float32)


@dataclass(frozen=True, slots=True)
class JamAwareVariableImpedanceDemoPolicy:
    name: str = "variable_impedance_demo"
    misalignment_threshold_m: float = 0.0015
    strong_contact_threshold: float = 0.2
    alignment_threshold: float = 0.85

    def act(self, observation: np.ndarray) -> np.ndarray:
        cartesian = _cartesian_action_from_observation(observation)
        target_delta = np.asarray(observation[6:9], dtype=np.float32)
        xy_error = float(np.linalg.norm(target_delta[:2]))
        z_error = float(abs(target_delta[2]))
        contact_count_signal = float(observation[12]) if observation.shape[0] > 12 else 0.0
        contact_force_signal = float(observation[13]) if observation.shape[0] > 13 else 0.0
        xy_alignment = float(observation[14]) if observation.shape[0] > 14 else 0.0
        insertion_progress = float(observation[16]) if observation.shape[0] > 16 else 0.0
        has_contact = bool(observation[17]) if observation.shape[0] > 17 else False
        contact_signal = max(contact_count_signal, contact_force_signal)

        stiffness_xy = 0.2 if xy_error < 0.003 else 0.75
        stiffness_z = 0.85 if z_error > 0.01 else 0.45
        if not has_contact and contact_signal <= 0.0:
            return np.concatenate(
                [cartesian, np.array([stiffness_xy, stiffness_z], dtype=np.float32)],
                dtype=np.float32,
            )

        strong_contact = contact_signal >= self.strong_contact_threshold
        misaligned = (
            xy_error > self.misalignment_threshold_m
            or xy_alignment < self.alignment_threshold
        )
        if strong_contact and misaligned:
            cartesian[:2] = np.clip(cartesian[:2] * 1.5, -1.0, 1.0)
            cartesian[2] = 0.12
            stiffness_xy = 0.08
            stiffness_z = 0.18
        elif misaligned:
            cartesian[:2] = np.clip(cartesian[:2] * 1.35, -1.0, 1.0)
            cartesian[2] = np.clip(cartesian[2], -0.05, 0.02)
            stiffness_xy = 0.1
            stiffness_z = 0.22
        else:
            cartesian[:2] *= 0.25
            cartesian[2] = np.clip(cartesian[2], -0.08, -0.01)
            if strong_contact and insertion_progress > 0.8:
                cartesian[2] = max(cartesian[2], -0.04)
            stiffness_xy = 0.08
            stiffness_z = 0.28 if strong_contact else 0.32
        impedance = np.array([stiffness_xy, stiffness_z], dtype=np.float32)
        return np.concatenate([cartesian, impedance], dtype=np.float32)
