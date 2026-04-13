from __future__ import annotations

from dataclasses import dataclass

import mujoco
import numpy as np


@dataclass(frozen=True, slots=True)
class ControllerDiagnostics:
    contact_count: int
    contact_force_norm: float
    wall_contact_force_norm: float
    bottom_contact_force_norm: float
    peak_contact_force: float
    is_jammed: bool


@dataclass(frozen=True, slots=True)
class ControllerConfig:
    ik_iterations: int = 12
    convergence_tol: float = 5e-4
    orientation_convergence_tol: float = 2e-3
    free_xy_gain_range: tuple[float, float] = (0.18, 0.7)
    free_z_gain_range: tuple[float, float] = (0.18, 0.7)
    orientation_gain: float = 2.0
    desired_tool_axis: tuple[float, float, float] = (0.0, 0.0, -1.0)
    contact_step_scale: float = 0.75
    high_force_step_scale: float = 0.25
    step_scale_force_threshold: float = 150.0
    contact_xy_softening: float = 0.7
    high_force_xy_softening: float = 0.9
    contact_z_softening: float = 0.35
    high_force_z_softening: float = 0.15
    base_damping: float = 1e-4
    contact_damping_boost: float = 5e-3
    high_force_damping_boost: float = 8e-3
    high_force_threshold: float = 20.0
    jam_force_threshold: float = 25.0
    jam_progress_threshold: float = 5e-4


class PegCartesianImpedanceController:
    def __init__(self, config: ControllerConfig | None = None) -> None:
        self.config = config or ControllerConfig()

    def compute_axis_alignment_error(
        self,
        *,
        current_axis_world: np.ndarray,
        desired_axis_world: np.ndarray,
    ) -> np.ndarray:
        current_axis = np.asarray(current_axis_world, dtype=np.float64)
        desired_axis = np.asarray(desired_axis_world, dtype=np.float64)
        current_norm = float(np.linalg.norm(current_axis))
        desired_norm = float(np.linalg.norm(desired_axis))
        if current_norm < 1e-9 or desired_norm < 1e-9:
            return np.zeros(3, dtype=np.float64)
        current_axis = current_axis / current_norm
        desired_axis = desired_axis / desired_norm
        return np.cross(current_axis, desired_axis).astype(np.float64)

    def compute_axis_gains(
        self,
        impedance_command: np.ndarray,
        contact_count: int,
        contact_force_norm: float = 0.0,
    ) -> np.ndarray:
        xy_impedance = float(np.clip(impedance_command[0], 0.0, 1.0))
        z_impedance = float(np.clip(impedance_command[1], 0.0, 1.0))

        xy_gain = np.interp(
            xy_impedance, [0.0, 1.0], list(self.config.free_xy_gain_range)
        )
        z_gain = np.interp(
            z_impedance, [0.0, 1.0], list(self.config.free_z_gain_range)
        )
        if contact_count > 0:
            force_ratio = float(
                np.clip(
                    contact_force_norm / max(self.config.high_force_threshold, 1e-6),
                    0.0,
                    1.0,
                )
            )
            xy_softening = np.interp(
                force_ratio,
                [0.0, 1.0],
                [self.config.contact_xy_softening, self.config.high_force_xy_softening],
            )
            z_softening = np.interp(
                force_ratio,
                [0.0, 1.0],
                [self.config.contact_z_softening, self.config.high_force_z_softening],
            )
            xy_gain *= xy_softening
            z_gain *= z_softening
        return np.array([xy_gain, xy_gain, z_gain], dtype=np.float64)

    def compute_damping(
        self,
        impedance_command: np.ndarray,
        contact_count: int,
        contact_force_norm: float = 0.0,
    ) -> float:
        mean_impedance = float(np.mean(np.clip(impedance_command, 0.0, 1.0)))
        damping = self.config.base_damping + (1.0 - mean_impedance) * 5e-3
        if contact_count > 0:
            damping += self.config.contact_damping_boost
            force_ratio = float(
                np.clip(
                    contact_force_norm / max(self.config.high_force_threshold, 1e-6),
                    0.0,
                    1.0,
                )
            )
            damping += force_ratio * self.config.high_force_damping_boost
        return damping

    def compute_step_scale(
        self,
        *,
        contact_count: int,
        contact_force_norm: float = 0.0,
    ) -> float:
        if contact_count <= 0:
            return 1.0
        force_ratio = float(
            np.clip(
                contact_force_norm / max(self.config.step_scale_force_threshold, 1e-6),
                0.0,
                1.0,
            )
        )
        return float(
            np.interp(
                force_ratio,
                [0.0, 1.0],
                [self.config.contact_step_scale, self.config.high_force_step_scale],
            )
        )

    def measure_contact_force_components(
        self,
        model: mujoco.MjModel,
        data: mujoco.MjData,
        tracked_geom_ids: set[int],
        wall_geom_ids: set[int],
        bottom_geom_ids: set[int],
    ) -> tuple[float, float, float]:
        wrench = np.zeros(6, dtype=np.float64)
        total_force_norm = 0.0
        wall_force_norm = 0.0
        bottom_force_norm = 0.0
        for contact_index in range(data.ncon):
            contact = data.contact[contact_index]
            if contact.geom1 not in tracked_geom_ids and contact.geom2 not in tracked_geom_ids:
                continue
            mujoco.mj_contactForce(model, data, contact_index, wrench)
            contact_force_norm = float(np.linalg.norm(wrench[:3]))
            total_force_norm += contact_force_norm
            other_geom_id = (
                contact.geom2 if contact.geom1 in tracked_geom_ids else contact.geom1
            )
            if other_geom_id in wall_geom_ids:
                wall_force_norm += contact_force_norm
            if other_geom_id in bottom_geom_ids:
                bottom_force_norm += contact_force_norm
        return total_force_norm, wall_force_norm, bottom_force_norm

    def execute(
        self,
        *,
        model: mujoco.MjModel,
        data: mujoco.MjData,
        desired_position: np.ndarray,
        site_id: int,
        arm_joint_ids: np.ndarray,
        arm_qpos_indices: np.ndarray,
        arm_ctrl_indices: np.ndarray,
        finger_qpos_indices: np.ndarray,
        finger_ctrl_indices: np.ndarray,
        finger_home: np.ndarray,
        impedance_command: np.ndarray,
        tracked_geom_ids: set[int],
        wall_geom_ids: set[int],
        bottom_geom_ids: set[int],
        jacobian_position: np.ndarray,
        jacobian_rotation: np.ndarray,
        joint_limit_clipper,
    ) -> ControllerDiagnostics:
        mujoco.mj_forward(model, data)
        initial_error_norm = float(
            np.linalg.norm(desired_position - data.site_xpos[site_id].copy())
        )
        contact_force_norm, wall_force_norm, bottom_force_norm = (
            self.measure_contact_force_components(
                model,
                data,
                tracked_geom_ids,
                wall_geom_ids,
                bottom_geom_ids,
            )
        )
        peak_contact_force = contact_force_norm
        desired_axis_world = np.asarray(self.config.desired_tool_axis, dtype=np.float64)

        for _ in range(self.config.ik_iterations):
            mujoco.mj_forward(model, data)
            current_position = data.site_xpos[site_id].copy()
            position_error = desired_position - current_position
            current_rotation = data.site_xmat[site_id].reshape(3, 3)
            orientation_error = self.compute_axis_alignment_error(
                current_axis_world=current_rotation[:, 2],
                desired_axis_world=desired_axis_world,
            )
            orientation_error_norm = float(np.linalg.norm(orientation_error))
            if np.linalg.norm(position_error) < self.config.convergence_tol and (
                self.config.orientation_gain <= 0.0
                or orientation_error_norm < self.config.orientation_convergence_tol
            ):
                break

            contact_count = int(data.ncon)
            contact_force_norm, wall_force_norm, bottom_force_norm = (
                self.measure_contact_force_components(
                    model,
                    data,
                    tracked_geom_ids,
                    wall_geom_ids,
                    bottom_geom_ids,
                )
            )
            gains = self.compute_axis_gains(
                impedance_command,
                contact_count,
                contact_force_norm=contact_force_norm,
            )
            damping = self.compute_damping(
                impedance_command,
                contact_count,
                contact_force_norm=contact_force_norm,
            )

            jacobian_position.fill(0.0)
            jacobian_rotation.fill(0.0)
            mujoco.mj_jacSite(model, data, jacobian_position, jacobian_rotation, site_id)
            arm_jacobian_position = jacobian_position[:, : arm_qpos_indices.size]
            arm_jacobian_rotation = jacobian_rotation[:, : arm_qpos_indices.size]
            weighted_orientation_jacobian = (
                self.config.orientation_gain * arm_jacobian_rotation
            )
            task_jacobian = np.vstack(
                (arm_jacobian_position, weighted_orientation_jacobian)
            )
            task_error = np.concatenate(
                (
                    gains * position_error,
                    self.config.orientation_gain * orientation_error,
                )
            )
            regularized = task_jacobian @ task_jacobian.T + damping * np.eye(6)
            delta_q = task_jacobian.T @ np.linalg.solve(regularized, task_error)
            step_scale = self.compute_step_scale(
                contact_count=contact_count,
                contact_force_norm=contact_force_norm,
            )
            data.qpos[arm_qpos_indices] += step_scale * delta_q
            joint_limit_clipper()
            data.qpos[finger_qpos_indices] = finger_home
            data.ctrl[arm_ctrl_indices] = data.qpos[arm_qpos_indices]
            data.ctrl[finger_ctrl_indices] = finger_home
            mujoco.mj_forward(model, data)
            peak_contact_force = max(
                peak_contact_force,
                self.measure_contact_force_components(
                    model,
                    data,
                    tracked_geom_ids,
                    wall_geom_ids,
                    bottom_geom_ids,
                )[0],
            )

        mujoco.mj_forward(model, data)
        final_error_norm = float(
            np.linalg.norm(desired_position - data.site_xpos[site_id].copy())
        )
        contact_force_norm, wall_force_norm, bottom_force_norm = (
            self.measure_contact_force_components(
                model,
                data,
                tracked_geom_ids,
                wall_geom_ids,
                bottom_geom_ids,
            )
        )
        peak_contact_force = max(peak_contact_force, contact_force_norm)
        progress = initial_error_norm - final_error_norm
        contact_count = int(data.ncon)
        is_jammed = (
            contact_count > 0
            and peak_contact_force > self.config.jam_force_threshold
            and progress < self.config.jam_progress_threshold
        )
        return ControllerDiagnostics(
            contact_count=contact_count,
            contact_force_norm=contact_force_norm,
            wall_contact_force_norm=wall_force_norm,
            bottom_contact_force_norm=bottom_force_norm,
            peak_contact_force=peak_contact_force,
            is_jammed=is_jammed,
        )
