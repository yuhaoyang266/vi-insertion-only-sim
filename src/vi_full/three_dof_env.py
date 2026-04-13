from __future__ import annotations

from collections import deque
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from vi_full.three_dof_config import ThreeDoFInsertionConfig


class ThreeDoFInsertionEnv(gym.Env[np.ndarray, np.ndarray]):
    metadata = {"render_modes": []}

    def __init__(
        self,
        config: ThreeDoFInsertionConfig | None = None,
        *,
        max_episode_steps: int | None = None,
    ) -> None:
        super().__init__()
        self.config = config or ThreeDoFInsertionConfig()
        self.max_episode_steps = max_episode_steps or self.config.max_episode_steps
        self.reset_config = self.config.reset_config

        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0, -1.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32,
        )
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(self.config.observation_dim,),
            dtype=np.float32,
        )

        self.position = np.zeros(3, dtype=np.float64)
        self.velocity = np.zeros(3, dtype=np.float64)
        self.force_sensor = np.zeros(3, dtype=np.float64)
        self.previous_action = np.zeros(self.config.action_dim, dtype=np.float64)
        self.target_position = np.zeros(3, dtype=np.float64)
        self.contact_target_position = np.zeros(3, dtype=np.float64)
        self.pose_target_bias_direction_xy = np.zeros(2, dtype=np.float64)
        self.orientation_perturbation_direction_xy = np.zeros(2, dtype=np.float64)
        self.contact_force_history: deque[float] = deque(maxlen=16)
        self.episode_step = 0
        self.peak_contact_force = 0.0
        self.blocked_contact_steps = 0
        self.cumulative_contact_work = 0.0
        self.cumulative_contact_impulse = 0.0
        self.uncertainty = {
            "hole_xy_offset_m": 0.0,
            "wall_friction": 0.0,
            "clearance_m": 0.0,
            "force_noise_std": 0.0,
            "pose_target_bias_xy_m": 0.0,
            "orientation_perturbation_deg": 0.0,
        }
        self.last_reward_breakdown = self._empty_reward_breakdown()
        self.last_action_modifiers = self._empty_action_modifiers()
        self.last_contact_debug = self._empty_contact_debug()

    def reset(
        self, *, seed: int | None = None, options: dict | None = None
    ) -> tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        del options

        self.episode_step = 0
        self.peak_contact_force = 0.0
        self.blocked_contact_steps = 0
        self.cumulative_contact_work = 0.0
        self.cumulative_contact_impulse = 0.0
        self.contact_force_history.clear()
        self.force_sensor[:] = 0.0
        self.velocity[:] = 0.0
        self.previous_action[:] = 0.0
        self.pose_target_bias_direction_xy[:] = 0.0
        self.orientation_perturbation_direction_xy[:] = 0.0
        self.last_reward_breakdown = self._empty_reward_breakdown()
        self.last_action_modifiers = self._empty_action_modifiers()
        self.last_contact_debug = self._empty_contact_debug()

        hole_offset_xy = self.np_random.uniform(
            -self.config.hole_xy_offset_range_m,
            self.config.hole_xy_offset_range_m,
            size=2,
        )
        self.uncertainty = {
            "hole_xy_offset_m": float(np.linalg.norm(hole_offset_xy)),
            "wall_friction": float(
                self.np_random.uniform(*self.config.wall_friction_range)
            ),
            "clearance_m": float(self.np_random.uniform(*self.config.clearance_range_m)),
            "force_noise_std": float(
                self.np_random.uniform(*self.config.force_noise_std_range)
            ),
            "pose_target_bias_xy_m": float(self.config.pose_target_bias_xy_m),
            "orientation_perturbation_deg": float(
                self.config.orientation_perturbation_deg
            ),
        }
        self.target_position = np.array(
            [
                hole_offset_xy[0],
                hole_offset_xy[1],
                -self.config.target_insertion_depth_m,
            ],
            dtype=np.float64,
        )
        if self.config.pose_target_bias_xy_m > 0.0:
            self.pose_target_bias_direction_xy = self._sample_unit_xy_direction()
        if self.config.orientation_perturbation_deg > 0.0:
            self.orientation_perturbation_direction_xy = self._sample_unit_xy_direction()
        self.contact_target_position = self.target_position.copy()
        self.contact_target_position[:2] += (
            self.config.pose_target_bias_xy_m * self.pose_target_bias_direction_xy
        )
        self.position = self._sample_start_position()
        observation = self._get_observation()
        info = self._get_info()
        return observation, info

    def step(
        self, action: np.ndarray
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        clipped_action = np.clip(
            np.asarray(action, dtype=np.float64),
            self.action_space.low,
            self.action_space.high,
        )
        self.last_action_modifiers = self._empty_action_modifiers()
        clipped_action = self._maybe_apply_phase_conditioned_action_bias(clipped_action)
        clipped_action = self._maybe_project_approach_alignment_action(clipped_action)
        clipped_action = self._maybe_project_contact_intent_action(clipped_action)
        previous_distance = self._distance_to_target()
        previous_force_std = self._force_std()
        previous_insertion_depth = self._insertion_depth()
        previous_surface_height = self._surface_height()

        cartesian_delta = np.array(
            [
                clipped_action[0] * self.config.step_scale_xy_m,
                clipped_action[1] * self.config.step_scale_xy_m,
                clipped_action[2] * self.config.step_scale_z_m,
            ],
            dtype=np.float64,
        )
        cartesian_delta = self._apply_orientation_perturbation(cartesian_delta)
        stiffness_xy = self._decode_stiffness(
            float(clipped_action[3]), self.config.min_k_xy, self.config.max_k_xy
        )
        stiffness_z = self._decode_stiffness(
            float(clipped_action[4]), self.config.min_k_z, self.config.max_k_z
        )
        previous_position = self.position.copy()

        proposed_position = self.position + cartesian_delta
        proposed_position[:2] = np.clip(
            proposed_position[:2],
            -self.config.workspace_xy_limit_m,
            self.config.workspace_xy_limit_m,
        )
        proposed_position[2] = float(
            np.clip(
                proposed_position[2],
                self.config.workspace_z_min_m,
                self.config.workspace_z_max_m,
            )
        )

        (
            new_position,
            contact_force,
            blocked_contact,
            contact_debug,
            analytical_contact_force,
        ) = self._apply_contact_dynamics(
            proposed_position=proposed_position,
            cartesian_delta=cartesian_delta,
            stiffness_xy=stiffness_xy,
            stiffness_z=stiffness_z,
        )
        actual_displacement = new_position - previous_position
        new_velocity = (new_position - self.position) / max(self.config.dt, 1e-6)
        new_velocity *= 1.0 - self.config.free_motion_damping

        self.position = new_position
        self.velocity = new_velocity
        self.force_sensor = contact_force
        force_norm = float(np.linalg.norm(self.force_sensor))
        self.contact_force_history.append(force_norm)
        self.peak_contact_force = max(self.peak_contact_force, force_norm)
        self.blocked_contact_steps = (
            self.blocked_contact_steps + 1 if blocked_contact else 0
        )
        self.episode_step += 1
        self.previous_action = np.array(
            [
                clipped_action[0],
                clipped_action[1],
                clipped_action[2],
                clipped_action[3],
                clipped_action[4],
            ],
            dtype=np.float64,
        )

        is_success = self._is_success()
        is_jammed = bool(
            force_norm >= self.config.jam_force_threshold_n
            or self.blocked_contact_steps >= self.config.jam_persistence_steps
        )
        contact_debug["decoded_k_xy"] = float(stiffness_xy)
        contact_debug["decoded_k_z"] = float(stiffness_z)
        contact_debug["contact_work_increment"] = self._compute_contact_work_increment(
            analytical_contact_force,
            actual_displacement,
        )
        self.cumulative_contact_work += float(contact_debug["contact_work_increment"])
        contact_debug["cumulative_contact_work"] = float(self.cumulative_contact_work)
        contact_debug["contact_impulse_increment"] = self._compute_contact_impulse_increment(
            analytical_contact_force
        )
        self.cumulative_contact_impulse += float(
            contact_debug["contact_impulse_increment"]
        )
        contact_debug["cumulative_contact_impulse"] = float(
            self.cumulative_contact_impulse
        )
        contact_debug["contact_phase_label"] = self._classify_contact_phase_label(
            contact_debug=contact_debug,
            is_jammed=is_jammed,
            surface_height=self._surface_height(),
        )
        self.last_contact_debug = contact_debug
        current_distance = self._distance_to_target()
        current_force_std = self._force_std()
        current_insertion_depth = self._insertion_depth()
        self.last_reward_breakdown = self._compute_reward_breakdown(
            previous_distance=previous_distance,
            current_distance=current_distance,
            previous_insertion_depth=previous_insertion_depth,
            current_insertion_depth=current_insertion_depth,
            previous_surface_height=previous_surface_height,
            current_surface_height=self._surface_height(),
            force_norm=force_norm,
            previous_force_std=previous_force_std,
            current_force_std=current_force_std,
            is_success=is_success,
            is_jammed=is_jammed,
        )

        observation = self._get_observation()
        terminated = bool(is_success or is_jammed)
        truncated = self.episode_step >= self.max_episode_steps
        info = self._get_info()
        return (
            observation,
            float(self.last_reward_breakdown["total_reward"]),
            terminated,
            truncated,
            info,
        )

    def close(self) -> None:
        return None

    def _sample_start_position(self) -> np.ndarray:
        base_start = np.array(
            [
                self.target_position[0] + self.config.initial_lateral_offset_m,
                self.target_position[1] - 0.5 * self.config.initial_lateral_offset_m,
                self.config.initial_height_m,
            ],
            dtype=np.float64,
        )
        if not self.reset_config.curriculum_stages:
            return base_start

        weights = np.asarray(
            [max(stage.weight, 0.0) for stage in self.reset_config.curriculum_stages],
            dtype=np.float64,
        )
        if float(np.sum(weights)) <= 0.0:
            weights = np.ones_like(weights) / max(len(weights), 1)
        else:
            weights = weights / np.sum(weights)
        stage_index = int(self.np_random.choice(len(self.reset_config.curriculum_stages), p=weights))
        stage = self.reset_config.curriculum_stages[stage_index]
        lower, upper = stage.start_depth_fraction_range
        depth_fraction = float(self.np_random.uniform(lower, upper))
        start_position = base_start + depth_fraction * (self.target_position - base_start)
        if stage.start_xy_noise_m > 0.0:
            start_position[:2] += self.np_random.uniform(
                -stage.start_xy_noise_m,
                stage.start_xy_noise_m,
                size=2,
            )
        return start_position

    def _apply_contact_dynamics(
        self,
        *,
        proposed_position: np.ndarray,
        cartesian_delta: np.ndarray,
        stiffness_xy: float,
        stiffness_z: float,
    ) -> tuple[np.ndarray, np.ndarray, bool, dict[str, float | bool | str], np.ndarray]:
        hole_xy = self.contact_target_position[:2]
        candidate_xy_error = proposed_position[:2] - hole_xy
        lateral_error = float(np.linalg.norm(candidate_xy_error))
        clearance = self.uncertainty["clearance_m"]
        contact_force = np.zeros(3, dtype=np.float64)
        wall_force = np.zeros(3, dtype=np.float64)
        bottom_force = np.zeros(3, dtype=np.float64)
        blocked_contact = False
        new_position = proposed_position.copy()
        contact_debug = self._empty_contact_debug()
        contact_debug["clearance_m"] = float(clearance)
        contact_debug["lateral_error_m"] = float(lateral_error)

        if proposed_position[2] < 0.0:
            if lateral_error > clearance:
                overflow = lateral_error - clearance
                contact_debug["overflow_m"] = float(overflow)
                (
                    hard_blocked_contact,
                    hard_blocked_force,
                    hard_blocked_position,
                    hard_blocked_z_direct,
                    hard_blocked_z_coupling,
                ) = self._compute_hard_blocked_contact_response(
                    proposed_position=proposed_position,
                    cartesian_delta=cartesian_delta,
                    candidate_xy_error=candidate_xy_error,
                    lateral_error=lateral_error,
                    overflow=overflow,
                    stiffness_xy=stiffness_xy,
                    stiffness_z=stiffness_z,
                )

                transition_band_m = max(self.config.contact_transition_band_m, 0.0)
                if transition_band_m > 0.0 and overflow < transition_band_m:
                    transition_ratio = np.clip(overflow / transition_band_m, 0.0, 1.0)
                    # A slow-start ramp softens the cliff without changing the
                    # hard-blocked law once overflow exits the probe band.
                    transition_blend = float(transition_ratio**3)
                    soft_force = self._compute_in_hole_contact_force(
                        candidate_xy_error=candidate_xy_error,
                        lateral_error=lateral_error,
                        cartesian_delta=cartesian_delta,
                        clearance=clearance,
                        stiffness_xy=stiffness_xy,
                        stiffness_z=stiffness_z,
                    )
                    wall_xy_force = (
                        (1.0 - transition_blend) * soft_force[:2]
                        + transition_blend * hard_blocked_force[:2]
                    )
                    soft_wall_z = float((1.0 - transition_blend) * soft_force[2])
                    hard_bottom_z = float(
                        transition_blend * hard_blocked_z_direct
                    )
                    hard_wall_z = float(
                        transition_blend * hard_blocked_z_coupling
                    )
                    direct_axial_ramp = 1.0
                    transition_force_scale = (1.0, 1.0)
                    scale_xy_force, scale_z_axial_force, scale_z_coupling_force = (
                        self.config.transition_stiffness_force_scaling_components()
                    )
                    if (
                        scale_xy_force
                        or scale_z_axial_force
                        or scale_z_coupling_force
                        or self.config.contact_transition_direct_axial_ramp_power > 0.0
                    ):
                        transition_force_scale = (
                            self._compute_transition_stiffness_force_scale(
                                stiffness_xy=stiffness_xy,
                                stiffness_z=stiffness_z,
                            )
                        )
                        if scale_xy_force:
                            wall_xy_force *= transition_force_scale[0]
                        if (
                            scale_z_axial_force
                            or scale_z_coupling_force
                            or self.config.contact_transition_direct_axial_ramp_power
                            > 0.0
                        ):
                            direct_axial_ramp = 1.0
                            if self.config.contact_transition_direct_axial_ramp_power > 0.0:
                                direct_axial_ramp = float(
                                    np.clip(transition_ratio, 0.0, 1.0)
                                    ** self.config.contact_transition_direct_axial_ramp_power
                                )
                            hard_bottom_z = float(
                                transition_blend
                                * direct_axial_ramp
                                * hard_blocked_z_direct
                            )
                            hard_wall_z = float(
                                transition_blend * hard_blocked_z_coupling
                            )
                            if scale_z_axial_force:
                                soft_wall_z *= transition_force_scale[1]
                                hard_bottom_z *= transition_force_scale[1]
                            if scale_z_coupling_force:
                                hard_wall_z *= transition_force_scale[1]
                    wall_force = np.array(
                        [wall_xy_force[0], wall_xy_force[1], soft_wall_z + hard_wall_z],
                        dtype=np.float64,
                    )
                    bottom_force = np.array([0.0, 0.0, hard_bottom_z], dtype=np.float64)
                    contact_force = wall_force + bottom_force
                    new_position = (
                        (1.0 - transition_blend) * proposed_position
                        + transition_blend * hard_blocked_position
                    )
                    blocked_contact = False
                    contact_debug.update(
                        {
                            "within_transition_band": True,
                            "overflow_ratio_in_band": float(transition_ratio),
                            "transition_blend": float(transition_blend),
                            "soft_contact_z_n": float(soft_wall_z),
                            "hard_blocked_direct_axial_z_n": float(
                                hard_blocked_z_direct
                            ),
                            "hard_blocked_z_coupling_n": float(
                                hard_blocked_z_coupling
                            ),
                            "direct_axial_z_n": float(hard_bottom_z),
                            "z_coupling_n": float(hard_wall_z),
                            "transition_force_scale_xy": float(
                                transition_force_scale[0]
                            ),
                            "transition_force_scale_z": float(
                                transition_force_scale[1]
                            ),
                            "direct_axial_ramp_multiplier": float(direct_axial_ramp),
                        }
                    )
                else:
                    blocked_contact = hard_blocked_contact
                    wall_force = hard_blocked_force.copy()
                    wall_force[2] = float(hard_blocked_z_coupling)
                    bottom_force = np.array(
                        [0.0, 0.0, float(hard_blocked_z_direct)],
                        dtype=np.float64,
                    )
                    contact_force = wall_force + bottom_force
                    new_position = hard_blocked_position
                    contact_debug.update(
                        {
                            "blocked_contact": bool(hard_blocked_contact),
                            "hard_blocked_direct_axial_z_n": float(
                                hard_blocked_z_direct
                            ),
                            "hard_blocked_z_coupling_n": float(
                                hard_blocked_z_coupling
                            ),
                            "direct_axial_z_n": float(hard_blocked_z_direct),
                            "z_coupling_n": float(hard_blocked_z_coupling),
                            "total_z_n": float(hard_blocked_force[2]),
                            "force_norm_n": float(
                                np.linalg.norm(hard_blocked_force)
                            ),
                        }
                    )
            else:
                contact_force = self._compute_in_hole_contact_force(
                    candidate_xy_error=candidate_xy_error,
                    lateral_error=lateral_error,
                    cartesian_delta=cartesian_delta,
                    clearance=clearance,
                    stiffness_xy=stiffness_xy,
                    stiffness_z=stiffness_z,
                )
                wall_force = contact_force.copy()
                contact_debug.update(
                    {
                        "within_hole_contact": True,
                        "soft_contact_z_n": float(contact_force[2]),
                    }
                )

        noisy_force = contact_force.copy()
        self._update_contact_component_debug(
            contact_debug,
            wall_force=wall_force,
            bottom_force=bottom_force,
        )
        contact_debug["total_z_n"] = float(contact_force[2])
        contact_debug["force_norm_n"] = float(np.linalg.norm(contact_force))
        if float(np.linalg.norm(contact_force)) > 0.0:
            noisy_force += self.np_random.normal(
                0.0, self.uncertainty["force_noise_std"], size=3
            )
        return new_position, noisy_force, blocked_contact, contact_debug, contact_force

    def _compute_in_hole_contact_force(
        self,
        *,
        candidate_xy_error: np.ndarray,
        lateral_error: float,
        cartesian_delta: np.ndarray,
        clearance: float,
        stiffness_xy: float,
        stiffness_z: float,
    ) -> np.ndarray:
        contact_force = np.zeros(3, dtype=np.float64)
        wall_proximity = max(lateral_error - 0.5 * clearance, 0.0)
        contact_force[:2] = (
            stiffness_xy
            * wall_proximity
            * self.config.in_hole_drag_scale
            * candidate_xy_error
            / max(lateral_error, 1e-6)
        )
        contact_force[2] = (
            self.uncertainty["wall_friction"]
            * stiffness_z
            * abs(min(cartesian_delta[2], 0.0))
            * self.config.in_hole_drag_scale
        )
        return contact_force

    def _compute_hard_blocked_contact_response(
        self,
        *,
        proposed_position: np.ndarray,
        cartesian_delta: np.ndarray,
        candidate_xy_error: np.ndarray,
        lateral_error: float,
        overflow: float,
        stiffness_xy: float,
        stiffness_z: float,
    ) -> tuple[bool, np.ndarray, np.ndarray, float, float]:
        lateral_dir = candidate_xy_error / max(lateral_error, 1e-6)
        contact_force = np.zeros(3, dtype=np.float64)
        contact_xy = (
            stiffness_xy * overflow * self.config.contact_xy_scale
        ) * lateral_dir
        contact_z = (
            stiffness_z
            * abs(min(cartesian_delta[2], 0.0))
            * self.config.contact_z_scale
        )
        friction_load = self.uncertainty["wall_friction"] * max(contact_z, 0.0)
        contact_force[:2] = contact_xy + 0.25 * friction_load * lateral_dir
        contact_z_coupling = 0.2 * np.linalg.norm(contact_xy)
        contact_force[2] = contact_z + contact_z_coupling

        new_position = proposed_position.copy()
        new_position[2] = max(self.position[2] - 0.00005, 0.00005)
        new_position[:2] = proposed_position[:2] - self.config.contact_lateral_relaxation * (
            candidate_xy_error
        )
        return (
            True,
            contact_force,
            new_position,
            float(contact_z),
            float(contact_z_coupling),
        )

    def _compute_transition_stiffness_force_scale(
        self,
        *,
        stiffness_xy: float,
        stiffness_z: float,
    ) -> tuple[float, float]:
        xy_scale = self.config.min_k_xy / max(stiffness_xy, self.config.min_k_xy)
        z_scale = self.config.min_k_z / max(stiffness_z, self.config.min_k_z)
        return float(np.clip(xy_scale, 0.0, 1.0)), float(np.clip(z_scale, 0.0, 1.0))

    def _get_observation(self) -> np.ndarray:
        rel_pos = self.position - self.target_position
        observation = np.concatenate(
            [
                rel_pos,
                self.velocity,
                self.force_sensor,
                self.previous_action,
            ]
        )
        return observation.astype(np.float32)

    def _get_info(self) -> dict[str, Any]:
        return {
            "distance_to_target": self._distance_to_target(),
            "perceived_distance_to_target": self._perceived_distance_to_target(),
            "contact_force_norm": float(np.linalg.norm(self.force_sensor)),
            "peak_contact_force": float(self.peak_contact_force),
            "force_std": self._force_std(),
            "uncertainty": dict(self.uncertainty),
            "reward_breakdown": dict(self.last_reward_breakdown),
            "action_modifiers": dict(self.last_action_modifiers),
            "contact_debug": dict(self.last_contact_debug),
            "wall_contact_force_norm": float(
                self.last_contact_debug["wall_contact_force_norm"]
            ),
            "bottom_contact_force_norm": float(
                self.last_contact_debug["bottom_contact_force_norm"]
            ),
            "approx_normal_force_norm": float(
                self.last_contact_debug["approx_normal_force_norm"]
            ),
            "approx_tangential_force_norm": float(
                self.last_contact_debug["approx_tangential_force_norm"]
            ),
            "decoded_k_xy": float(self.last_contact_debug["decoded_k_xy"]),
            "decoded_k_z": float(self.last_contact_debug["decoded_k_z"]),
            "contact_work_increment": float(
                self.last_contact_debug["contact_work_increment"]
            ),
            "cumulative_contact_work": float(
                self.last_contact_debug["cumulative_contact_work"]
            ),
            "contact_impulse_increment": float(
                self.last_contact_debug["contact_impulse_increment"]
            ),
            "cumulative_contact_impulse": float(
                self.last_contact_debug["cumulative_contact_impulse"]
            ),
            "contact_phase_label": str(self.last_contact_debug["contact_phase_label"]),
            "is_success": self._is_success(),
            "is_jammed": bool(
                self.blocked_contact_steps >= self.config.jam_persistence_steps
                or float(np.linalg.norm(self.force_sensor))
                >= self.config.jam_force_threshold_n
            ),
        }

    def _update_contact_component_debug(
        self,
        contact_debug: dict[str, float | bool | str],
        *,
        wall_force: np.ndarray,
        bottom_force: np.ndarray,
    ) -> None:
        wall_xy_norm = float(np.linalg.norm(wall_force[:2]))
        bottom_z_norm = abs(float(bottom_force[2]))
        tangential_components = np.array(
            [float(wall_force[2]), float(np.linalg.norm(bottom_force[:2]))],
            dtype=np.float64,
        )
        contact_debug["wall_contact_force_norm"] = float(np.linalg.norm(wall_force))
        contact_debug["bottom_contact_force_norm"] = float(np.linalg.norm(bottom_force))
        contact_debug["approx_normal_force_norm"] = float(
            np.linalg.norm(np.array([wall_xy_norm, bottom_z_norm], dtype=np.float64))
        )
        contact_debug["approx_tangential_force_norm"] = float(
            np.linalg.norm(tangential_components)
        )

    def _compute_contact_work_increment(
        self,
        contact_force: np.ndarray,
        displacement: np.ndarray,
    ) -> float:
        if not np.any(contact_force):
            return 0.0
        return float(max(0.0, -float(np.dot(contact_force, displacement))))

    def _compute_contact_impulse_increment(self, contact_force: np.ndarray) -> float:
        return float(np.linalg.norm(contact_force) * max(self.config.dt, 0.0))

    def _classify_contact_phase_label(
        self,
        *,
        contact_debug: dict[str, float | bool | str],
        is_jammed: bool,
        surface_height: float,
    ) -> str:
        force_norm = float(contact_debug["force_norm_n"])
        wall_force_norm = float(contact_debug["wall_contact_force_norm"])
        bottom_force_norm = float(contact_debug["bottom_contact_force_norm"])
        if is_jammed:
            return "jammed"
        if (
            bool(contact_debug["within_transition_band"])
            and force_norm >= self.config.contact_reward_force_threshold_n
        ):
            return "transition_band_contact"
        if bool(contact_debug["blocked_contact"]) and force_norm >= self.config.contact_reward_force_threshold_n:
            return "blocked_contact"
        if (
            wall_force_norm >= self.config.contact_reward_force_threshold_n
            and bottom_force_norm >= self.config.contact_reward_force_threshold_n
        ):
            return "wall_bottom_contact"
        if bottom_force_norm >= self.config.contact_reward_force_threshold_n:
            return "bottom_contact"
        if wall_force_norm >= self.config.contact_reward_force_threshold_n:
            return "wall_contact"
        if surface_height > 0.0:
            return "approach"
        return "free_insertion"

    def _is_success(self) -> bool:
        rel_pos = self.position - self.contact_target_position
        lateral_error = float(np.linalg.norm(rel_pos[:2]))
        axial_error = abs(float(rel_pos[2]))
        speed = float(np.linalg.norm(self.velocity))
        return (
            lateral_error <= self.config.success_lateral_tolerance_m
            and axial_error <= self.config.success_axial_tolerance_m
            and speed <= 0.08
        )

    def _distance_to_target(self) -> float:
        return float(np.linalg.norm(self.position - self.contact_target_position))

    def _perceived_distance_to_target(self) -> float:
        return float(np.linalg.norm(self.position - self.target_position))

    def _xy_error(self) -> float:
        return float(np.linalg.norm((self.position - self.contact_target_position)[:2]))

    def _perceived_xy_error(self) -> float:
        return float(np.linalg.norm((self.position - self.target_position)[:2]))

    def _insertion_depth(self) -> float:
        return float(np.clip(-self.position[2], 0.0, self.config.target_insertion_depth_m))

    def _surface_height(self) -> float:
        return float(max(self.position[2], 0.0))

    def _force_std(self) -> float:
        if not self.contact_force_history:
            return 0.0
        return float(np.std(np.asarray(self.contact_force_history, dtype=np.float64)))

    def _decode_stiffness(self, normalized: float, minimum: float, maximum: float) -> float:
        value = float(np.clip(normalized, 0.0, 1.0))
        return minimum + value * (maximum - minimum)

    def _sample_unit_xy_direction(self) -> np.ndarray:
        direction = self.np_random.normal(0.0, 1.0, size=2)
        norm = float(np.linalg.norm(direction))
        if norm <= 1e-9:
            return np.array([1.0, 0.0], dtype=np.float64)
        return np.asarray(direction / norm, dtype=np.float64)

    def _apply_orientation_perturbation(
        self, cartesian_delta: np.ndarray
    ) -> np.ndarray:
        if (
            self.config.orientation_perturbation_deg <= 0.0
            or cartesian_delta[2] >= 0.0
        ):
            return cartesian_delta
        perturbed_delta = np.array(cartesian_delta, dtype=np.float64, copy=True)
        lateral_drift = abs(float(cartesian_delta[2])) * float(
            np.tan(np.deg2rad(self.config.orientation_perturbation_deg))
        )
        perturbed_delta[:2] += (
            lateral_drift * self.orientation_perturbation_direction_xy
        )
        return perturbed_delta

    def _maybe_project_contact_intent_action(self, action: np.ndarray) -> np.ndarray:
        if not self.config.enable_contact_intent_projection:
            return action

        xy_error = self._perceived_xy_error()
        near_contact = 0.0 < self.position[2] <= self.config.contact_intent_trigger_height_m
        has_contact = float(np.linalg.norm(self.force_sensor)) >= self.config.contact_reward_force_threshold_n
        aligned = xy_error <= self.config.contact_intent_trigger_xy_threshold_m
        if not (aligned and near_contact and not has_contact):
            return action

        projected = np.array(action, dtype=np.float64, copy=True)
        projected[2] = min(projected[2], self.config.contact_intent_min_z_action)
        projected[3] = max(projected[3], self.config.contact_intent_min_k_xy_action)
        projected[4] = max(projected[4], self.config.contact_intent_min_k_z_action)
        max_xy_error_increase = self.config.contact_intent_max_xy_error_increase_m
        if np.isfinite(max_xy_error_increase):
            projected[:2] = self._project_xy_action_with_error_budget(
                projected[:2],
                max_xy_error=xy_error + max(0.0, max_xy_error_increase),
            )
        self.last_action_modifiers["contact_intent_projection_applied"] = True
        return np.clip(projected, self.action_space.low, self.action_space.high)

    def _maybe_project_approach_alignment_action(self, action: np.ndarray) -> np.ndarray:
        if not self.config.enable_approach_alignment_projection:
            return action

        xy_error = self._perceived_xy_error()
        surface_height = self._surface_height()
        has_contact = (
            float(np.linalg.norm(self.force_sensor))
            >= self.config.contact_reward_force_threshold_n
        )
        descending = float(action[2]) < 0.0
        aligned = xy_error <= self.config.approach_alignment_trigger_xy_threshold_m
        within_height_band = (
            self.config.contact_intent_trigger_height_m < surface_height
            <= self.config.approach_alignment_trigger_height_m
        )
        if not (descending and aligned and within_height_band and not has_contact):
            return action

        projected = np.array(action, dtype=np.float64, copy=True)
        max_xy_error_increase = self.config.approach_alignment_max_xy_error_increase_m
        if np.isfinite(max_xy_error_increase):
            projected[:2] = self._project_xy_action_with_error_budget(
                projected[:2],
                max_xy_error=xy_error + max(0.0, max_xy_error_increase),
            )
        self.last_action_modifiers["approach_alignment_projection_applied"] = True
        return np.clip(projected, self.action_space.low, self.action_space.high)

    def _maybe_apply_phase_conditioned_action_bias(self, action: np.ndarray) -> np.ndarray:
        if not self.config.enable_phase_conditioned_action_bias:
            return action

        xy_error = self._perceived_xy_error()
        surface_height = self._surface_height()
        has_contact = (
            float(np.linalg.norm(self.force_sensor))
            >= self.config.contact_reward_force_threshold_n
        )
        aligned = xy_error <= self.config.phase_action_bias_trigger_xy_threshold_m
        within_height_band = (
            self.config.contact_intent_trigger_height_m < surface_height
            <= self.config.phase_action_bias_trigger_height_m
        )
        if not (aligned and within_height_band and not has_contact):
            return action

        mix = float(np.clip(self.config.phase_action_bias_mix, 0.0, 1.0))
        biased = np.array(action, dtype=np.float64, copy=True)
        biased[2] = (1.0 - mix) * biased[2] + mix * self.config.phase_action_bias_dz_action
        biased[3] = (1.0 - mix) * biased[3] + mix * self.config.phase_action_bias_k_xy_action
        biased[4] = (1.0 - mix) * biased[4] + mix * self.config.phase_action_bias_k_z_action
        max_xy_error_increase = self.config.phase_action_bias_max_xy_error_increase_m
        if np.isfinite(max_xy_error_increase):
            biased[:2] = self._project_xy_action_with_error_budget(
                biased[:2],
                max_xy_error=xy_error + max(0.0, max_xy_error_increase),
            )
        self.last_action_modifiers["phase_action_bias_applied"] = True
        return np.clip(biased, self.action_space.low, self.action_space.high)

    def _project_xy_action_with_error_budget(
        self,
        action_xy: np.ndarray,
        *,
        max_xy_error: float,
    ) -> np.ndarray:
        current_xy = self.position[:2]
        proposed_xy = current_xy + np.asarray(action_xy, dtype=np.float64) * self.config.step_scale_xy_m
        target_xy = self.target_position[:2]
        proposed_error = float(np.linalg.norm(proposed_xy - target_xy))
        if proposed_error <= max_xy_error:
            return np.asarray(action_xy, dtype=np.float64)

        if max_xy_error <= 0.0:
            limited_xy = target_xy.copy()
        else:
            direction = (proposed_xy - target_xy) / max(proposed_error, 1e-9)
            limited_xy = target_xy + direction * max_xy_error
        return (limited_xy - current_xy) / max(self.config.step_scale_xy_m, 1e-9)

    def _compute_reward_breakdown(
        self,
        *,
        previous_distance: float,
        current_distance: float,
        previous_insertion_depth: float,
        current_insertion_depth: float,
        previous_surface_height: float,
        current_surface_height: float,
        force_norm: float,
        previous_force_std: float,
        current_force_std: float,
        is_success: bool,
        is_jammed: bool,
    ) -> dict[str, float]:
        xy_error = self._xy_error()
        aligned = xy_error <= self.config.aligned_xy_threshold_m
        near_contact = 0.0 < self.position[2] <= self.config.near_contact_height_m
        has_contact = force_norm >= self.config.contact_reward_force_threshold_n

        progress_reward = self.config.progress_reward_scale * (
            previous_distance - current_distance
        )
        force_penalty = self.config.force_penalty_scale * max(0.0, force_norm - 1.0)
        stability_penalty = self.config.stability_penalty_scale * max(
            0.0, current_force_std - previous_force_std
        )
        time_penalty = self.config.time_penalty
        contact_bonus = self.config.contact_bonus if has_contact and aligned else 0.0
        approach_bonus = (
            self.config.approach_bonus_scale
            * max(0.0, previous_surface_height - current_surface_height)
            if aligned and near_contact and not has_contact
            else 0.0
        )
        insertion_bonus = (
            self.config.insertion_bonus_scale
            * max(0.0, current_insertion_depth - previous_insertion_depth)
            if aligned
            else 0.0
        )
        hover_penalty = self.config.hover_penalty if near_contact and aligned and not has_contact else 0.0
        success_bonus = 6.0 if is_success else 0.0
        jam_penalty = 6.0 if is_jammed else 0.0
        total_reward = (
            progress_reward
            - force_penalty
            - stability_penalty
            - time_penalty
            + contact_bonus
            + approach_bonus
            + insertion_bonus
            - hover_penalty
            + success_bonus
            - jam_penalty
        )
        return {
            "progress_reward": float(progress_reward),
            "force_penalty": float(force_penalty),
            "stability_penalty": float(stability_penalty),
            "time_penalty": float(time_penalty),
            "contact_bonus": float(contact_bonus),
            "approach_bonus": float(approach_bonus),
            "insertion_bonus": float(insertion_bonus),
            "hover_penalty": float(hover_penalty),
            "success_bonus": float(success_bonus),
            "jam_penalty": float(jam_penalty),
            "total_reward": float(total_reward),
        }

    def _empty_reward_breakdown(self) -> dict[str, float]:
        return {
            "progress_reward": 0.0,
            "force_penalty": 0.0,
            "stability_penalty": 0.0,
            "time_penalty": 0.0,
            "contact_bonus": 0.0,
            "approach_bonus": 0.0,
            "insertion_bonus": 0.0,
            "hover_penalty": 0.0,
            "success_bonus": 0.0,
            "jam_penalty": 0.0,
            "total_reward": 0.0,
        }

    def _empty_action_modifiers(self) -> dict[str, bool]:
        return {
            "phase_action_bias_applied": False,
            "approach_alignment_projection_applied": False,
            "contact_intent_projection_applied": False,
        }

    def _empty_contact_debug(self) -> dict[str, float | bool | str]:
        return {
            "within_hole_contact": False,
            "within_transition_band": False,
            "blocked_contact": False,
            "clearance_m": 0.0,
            "lateral_error_m": 0.0,
            "overflow_m": 0.0,
            "overflow_ratio_in_band": 0.0,
            "transition_blend": 0.0,
            "soft_contact_z_n": 0.0,
            "hard_blocked_direct_axial_z_n": 0.0,
            "hard_blocked_z_coupling_n": 0.0,
            "direct_axial_z_n": 0.0,
            "z_coupling_n": 0.0,
            "total_z_n": 0.0,
            "force_norm_n": 0.0,
            "transition_force_scale_xy": 1.0,
            "transition_force_scale_z": 1.0,
            "direct_axial_ramp_multiplier": 1.0,
            "wall_contact_force_norm": 0.0,
            "bottom_contact_force_norm": 0.0,
            "approx_normal_force_norm": 0.0,
            "approx_tangential_force_norm": 0.0,
            "decoded_k_xy": float(self.config.min_k_xy),
            "decoded_k_z": float(self.config.min_k_z),
            "contact_work_increment": 0.0,
            "cumulative_contact_work": 0.0,
            "contact_impulse_increment": 0.0,
            "cumulative_contact_impulse": 0.0,
            "contact_phase_label": "approach",
        }
