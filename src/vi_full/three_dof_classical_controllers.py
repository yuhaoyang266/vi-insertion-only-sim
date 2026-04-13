from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _cartesian_action_from_observation(observation: np.ndarray) -> np.ndarray:
    rel_pos = np.asarray(observation[:3], dtype=np.float32)
    normalization = np.array([0.004, 0.004, 0.006], dtype=np.float32)
    return np.clip(-rel_pos / normalization, -1.0, 1.0)


def _compose_action(
    cartesian: np.ndarray,
    *,
    stiffness_xy: float,
    stiffness_z: float,
) -> np.ndarray:
    return np.concatenate(
        [
            np.clip(np.asarray(cartesian, dtype=np.float32), -1.0, 1.0),
            np.array(
                [
                    np.clip(stiffness_xy, 0.0, 1.0),
                    np.clip(stiffness_z, 0.0, 1.0),
                ],
                dtype=np.float32,
            ),
        ],
        dtype=np.float32,
    )


def _unit_or_fallback(vector: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm <= 1e-6:
        return np.asarray(fallback, dtype=np.float32)
    return np.asarray(vector / norm, dtype=np.float32)


@dataclass(frozen=True, slots=True)
class ThreeDoFHybridPositionForceController:
    name: str = "three_dof_hybrid_position_force"
    contact_force_threshold: float = 0.12
    target_contact_force: float = 0.85
    alignment_threshold_m: float = 0.0012
    force_feedback_gain: float = 0.45

    def act(self, observation: np.ndarray) -> np.ndarray:
        rel_pos = np.asarray(observation[:3], dtype=np.float32)
        velocity = np.asarray(observation[3:6], dtype=np.float32)
        force = np.asarray(observation[6:9], dtype=np.float32)
        cartesian = _cartesian_action_from_observation(observation)
        xy_error = float(np.linalg.norm(rel_pos[:2]))
        force_norm = float(np.linalg.norm(force))
        in_contact = force_norm >= self.contact_force_threshold

        cartesian[:2] = np.clip(cartesian[:2] - 0.15 * velocity[:2], -1.0, 1.0)
        if not in_contact:
            cartesian[2] = np.clip(min(cartesian[2], -0.25), -1.0, 0.2)
            return _compose_action(
                cartesian,
                stiffness_xy=0.8 if xy_error > self.alignment_threshold_m else 0.55,
                stiffness_z=0.72 if float(rel_pos[2]) > 0.004 else 0.48,
            )

        cartesian[2] = np.clip(
            -self.force_feedback_gain * (self.target_contact_force - force_norm),
            -0.25,
            0.25,
        )
        if xy_error > self.alignment_threshold_m:
            cartesian[:2] = np.clip(cartesian[:2] * 1.2, -1.0, 1.0)
            return _compose_action(cartesian, stiffness_xy=0.42, stiffness_z=0.22)

        cartesian[:2] *= 0.4
        return _compose_action(cartesian, stiffness_xy=0.18, stiffness_z=0.26)


@dataclass(frozen=True, slots=True)
class ThreeDoFCompliantSearchController:
    name: str = "three_dof_compliant_search"
    contact_force_threshold: float = 0.1
    alignment_threshold_m: float = 0.001
    strong_contact_threshold: float = 0.9

    def act(self, observation: np.ndarray) -> np.ndarray:
        rel_pos = np.asarray(observation[:3], dtype=np.float32)
        force = np.asarray(observation[6:9], dtype=np.float32)
        previous_action = np.asarray(observation[9:14], dtype=np.float32)
        cartesian = _cartesian_action_from_observation(observation)
        xy_error = float(np.linalg.norm(rel_pos[:2]))
        force_norm = float(np.linalg.norm(force))

        if force_norm < self.contact_force_threshold:
            cartesian[:2] = np.clip(cartesian[:2] * 0.9, -1.0, 1.0)
            cartesian[2] = np.clip(min(cartesian[2], -0.3), -1.0, 0.15)
            return _compose_action(cartesian, stiffness_xy=0.62, stiffness_z=0.58)

        if xy_error <= self.alignment_threshold_m:
            cartesian[:2] *= 0.2
            cartesian[2] = np.clip(
                -0.08 if force_norm < self.strong_contact_threshold else 0.04,
                -0.2,
                0.2,
            )
            return _compose_action(cartesian, stiffness_xy=0.1, stiffness_z=0.18)

        search_direction = _unit_or_fallback(
            -rel_pos[:2],
            fallback=np.array(
                [
                    1.0 if previous_action[0] <= 0.0 else -1.0,
                    -1.0 if previous_action[1] >= 0.0 else 1.0,
                ],
                dtype=np.float32,
            ),
        )
        cartesian[:2] = np.clip(0.85 * search_direction, -1.0, 1.0)
        cartesian[2] = 0.08 if force_norm >= self.strong_contact_threshold else -0.03
        return _compose_action(cartesian, stiffness_xy=0.08, stiffness_z=0.14)


@dataclass(frozen=True, slots=True)
class ThreeDoFTunedImpedanceController:
    name: str = "three_dof_tuned_impedance"
    contact_force_threshold: float = 0.14
    near_contact_depth_m: float = 0.0045
    alignment_threshold_m: float = 0.0012
    strong_contact_threshold: float = 1.2

    def act(self, observation: np.ndarray) -> np.ndarray:
        rel_pos = np.asarray(observation[:3], dtype=np.float32)
        velocity = np.asarray(observation[3:6], dtype=np.float32)
        force = np.asarray(observation[6:9], dtype=np.float32)
        cartesian = _cartesian_action_from_observation(observation)
        xy_error = float(np.linalg.norm(rel_pos[:2]))
        force_norm = float(np.linalg.norm(force))
        near_contact = float(rel_pos[2]) <= self.near_contact_depth_m

        stiffness_xy = 0.78 if xy_error > 0.0018 else 0.42
        stiffness_z = 0.82 if float(rel_pos[2]) > self.near_contact_depth_m else 0.38
        if near_contact:
            cartesian[2] = np.clip(cartesian[2], -0.3, 0.18)

        if force_norm < self.contact_force_threshold:
            cartesian[:2] = np.clip(cartesian[:2] - 0.1 * velocity[:2], -1.0, 1.0)
            return _compose_action(
                cartesian,
                stiffness_xy=stiffness_xy,
                stiffness_z=stiffness_z,
            )

        cartesian[:2] = np.clip(cartesian[:2] * 1.2 - 0.18 * velocity[:2], -1.0, 1.0)
        if xy_error > self.alignment_threshold_m:
            cartesian[2] = 0.12 if force_norm >= self.strong_contact_threshold else 0.02
            return _compose_action(cartesian, stiffness_xy=0.12, stiffness_z=0.18)

        cartesian[:2] *= 0.3
        cartesian[2] = np.clip(cartesian[2], -0.12, 0.06)
        return _compose_action(
            cartesian,
            stiffness_xy=0.14,
            stiffness_z=0.22 if force_norm >= self.strong_contact_threshold else 0.28,
        )
