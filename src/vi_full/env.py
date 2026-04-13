from __future__ import annotations

from dataclasses import dataclass, field

import gymnasium as gym
import mujoco
import numpy as np
from gymnasium import spaces

from vi_full.assets import resolve_franka_asset_bundle
from vi_full.config import ActionSpec
from vi_full.controllers import ControllerDiagnostics, PegCartesianImpedanceController
from vi_full.rewards import PPOInsertionReward, RewardBreakdown, RewardMetrics
from vi_full.scene_builder import load_full_system_model


@dataclass(frozen=True, slots=True)
class ServoConfig:
    cartesian_step_m: np.ndarray = field(
        default_factory=lambda: np.array([0.01, 0.01, 0.01], dtype=np.float64)
    )
    workspace_low: np.ndarray = field(
        default_factory=lambda: np.array([0.53, -0.04, 0.47], dtype=np.float64)
    )
    workspace_high: np.ndarray = field(
        default_factory=lambda: np.array([0.63, 0.04, 0.58], dtype=np.float64)
    )
    ik_iterations: int = 12


@dataclass(frozen=True, slots=True)
class ResetConfig:
    target_xy_noise_m: float = 0.0015
    start_xy_noise_m: float = 0.0
    start_depth_fraction_range: tuple[float, float] = (0.0, 0.0)
    curriculum_stages: tuple["CurriculumStage", ...] = ()


@dataclass(frozen=True, slots=True)
class CurriculumStage:
    start_xy_noise_m: float = 0.0
    start_depth_fraction_range: tuple[float, float] = (0.0, 0.0)
    weight: float = 1.0


class PandaVariableImpedanceEnv(gym.Env[np.ndarray, np.ndarray]):
    metadata = {"render_modes": []}

    def __init__(
        self,
        max_episode_steps: int = 64,
        reset_config: ResetConfig | None = None,
    ) -> None:
        super().__init__()
        self.action_spec = ActionSpec()
        self.servo = ServoConfig()
        self.reset_config = reset_config or ResetConfig()
        self.max_episode_steps = max_episode_steps

        bundle = resolve_franka_asset_bundle()
        self.model = load_full_system_model(bundle)
        self.data = mujoco.MjData(self.model)

        self.ee_site_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SITE, "end_effector"
        )
        self.peg_base_site_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SITE, "peg_base"
        )
        self.peg_tip_site_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SITE, "peg_tip"
        )
        self.hole_site_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SITE, "hole_target"
        )
        self.approach_site_id = mujoco.mj_name2id(
            self.model, mujoco.mjtObj.mjOBJ_SITE, "peg_approach"
        )

        self.arm_joint_names = (
            "robot:panda0_joint1",
            "robot:panda0_joint2",
            "robot:panda0_joint3",
            "robot:panda0_joint4",
            "robot:panda0_joint5",
            "robot:panda0_joint6",
            "robot:panda0_joint7",
        )
        self.arm_actuator_names = (
            "panda0_joint1",
            "panda0_joint2",
            "panda0_joint3",
            "panda0_joint4",
            "panda0_joint5",
            "panda0_joint6",
            "panda0_joint7",
        )
        self.finger_joint_names = (
            "robot:panda0_finger_joint1",
            "robot:panda0_finger_joint2",
        )
        self.finger_actuator_names = (
            "r_gripper_finger_joint",
            "l_gripper_finger_joint",
        )

        self.arm_joint_ids = np.array(
            [
                mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, name)
                for name in self.arm_joint_names
            ],
            dtype=np.int32,
        )
        self.arm_qpos_indices = np.array(
            [self.model.jnt_qposadr[joint_id] for joint_id in self.arm_joint_ids],
            dtype=np.int32,
        )
        self.arm_ctrl_indices = np.array(
            [
                mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
                for name in self.arm_actuator_names
            ],
            dtype=np.int32,
        )
        self.finger_joint_ids = np.array(
            [
                mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, name)
                for name in self.finger_joint_names
            ],
            dtype=np.int32,
        )
        self.finger_qpos_indices = np.array(
            [self.model.jnt_qposadr[joint_id] for joint_id in self.finger_joint_ids],
            dtype=np.int32,
        )
        self.finger_ctrl_indices = np.array(
            [
                mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
                for name in self.finger_actuator_names
            ],
            dtype=np.int32,
        )

        self.base_target_position = np.zeros(3, dtype=np.float64)
        self.base_approach_position = np.zeros(3, dtype=np.float64)
        self.target_position = np.zeros(3, dtype=np.float64)
        self.approach_position = np.zeros(3, dtype=np.float64)
        self.impedance_command = np.array([0.5, 0.5], dtype=np.float64)
        self.jacobian_position = np.zeros((3, self.model.nv), dtype=np.float64)
        self.jacobian_rotation = np.zeros((3, self.model.nv), dtype=np.float64)
        self.episode_step = 0
        self.peak_contact_force = 0.0
        self.last_controller_diagnostics = ControllerDiagnostics(
            contact_count=0,
            contact_force_norm=0.0,
            wall_contact_force_norm=0.0,
            bottom_contact_force_norm=0.0,
            peak_contact_force=0.0,
            is_jammed=False,
        )
        self.reward_fn = PPOInsertionReward()
        self.last_reward_breakdown = RewardBreakdown(
            progress_reward=0.0,
            excess_force_penalty=0.0,
            action_penalty=0.0,
            time_penalty=0.0,
            stall_penalty=0.0,
            state_cost_penalty=0.0,
            contact_bonus=0.0,
            insertion_bonus=0.0,
            hover_penalty=0.0,
            drift_penalty=0.0,
            success_bonus=0.0,
            jam_penalty=0.0,
            total_reward=0.0,
        )
        self.previous_reward_metrics: RewardMetrics | None = None
        self.target_insertion_depth = 0.0
        self.controller = PegCartesianImpedanceController()
        self.home_qpos = self._solve_home_qpos()
        self.peg_geom_ids = {
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "peg_shaft")
        }
        self.socket_wall_geom_ids = {
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, f"socket_wall_{index}")
            for index in range(8)
        }
        self.base_plate_geom_ids = {
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "base_plate")
        }

        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(self.action_spec.action_dim,),
            dtype=np.float32,
        )
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(18,),
            dtype=np.float32,
        )

    def reset(
        self, *, seed: int | None = None, options: dict | None = None
    ) -> tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        del options

        mujoco.mj_resetData(self.model, self.data)
        self.data.qpos[:] = 0.0
        self.data.qvel[:] = 0.0
        mujoco.mj_forward(self.model, self.data)

        self.base_target_position = self.data.site_xpos[self.hole_site_id].copy()
        self.base_approach_position = self.data.site_xpos[self.approach_site_id].copy()

        target_noise = np.zeros(3, dtype=np.float64)
        target_noise[:2] = self.np_random.uniform(
            -self.reset_config.target_xy_noise_m,
            self.reset_config.target_xy_noise_m,
            size=2,
        )
        self.target_position = self.base_target_position + target_noise
        self.approach_position = self.base_approach_position + target_noise
        start_qpos = self.home_qpos
        if self._uses_reset_curriculum():
            start_tip_position = self._sample_curriculum_tip_position()
            start_qpos = self._solve_qpos_for_tip_target(
                start_tip_position,
                initial_qpos=self.home_qpos,
            )

        self.data.qpos[:] = 0.0
        self.data.qvel[:] = 0.0
        self.data.qpos[self.arm_qpos_indices] = start_qpos[:7]
        self.data.qpos[self.finger_qpos_indices] = start_qpos[7:]
        self.data.ctrl[self.arm_ctrl_indices] = start_qpos[:7]
        self.data.ctrl[self.finger_ctrl_indices] = start_qpos[7:]
        mujoco.mj_forward(self.model, self.data)
        self.impedance_command[:] = 0.5
        self.episode_step = 0
        self.peak_contact_force = 0.0
        self.last_controller_diagnostics = ControllerDiagnostics(
            contact_count=0,
            contact_force_norm=0.0,
            wall_contact_force_norm=0.0,
            bottom_contact_force_norm=0.0,
            peak_contact_force=0.0,
            is_jammed=False,
        )
        self.last_reward_breakdown = RewardBreakdown(
            progress_reward=0.0,
            excess_force_penalty=0.0,
            action_penalty=0.0,
            time_penalty=0.0,
            stall_penalty=0.0,
            state_cost_penalty=0.0,
            contact_bonus=0.0,
            insertion_bonus=0.0,
            hover_penalty=0.0,
            drift_penalty=0.0,
            success_bonus=0.0,
            jam_penalty=0.0,
            total_reward=0.0,
        )
        self.target_insertion_depth = max(
            float(self.approach_position[2] - self.target_position[2]), 1e-6
        )
        self.previous_reward_metrics = self._collect_reward_metrics()

        observation = self._get_observation()
        info = self._get_info()
        return observation, info

    def step(
        self, action: np.ndarray
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, np.ndarray | float | bool]]:
        clipped_action = np.clip(
            np.asarray(action, dtype=np.float64), self.action_space.low, self.action_space.high
        )
        cartesian_delta = clipped_action[:3] * self.servo.cartesian_step_m
        self.impedance_command = 0.5 * (clipped_action[3:] + 1.0)

        desired_position = self._peg_base_position() + cartesian_delta
        desired_position = np.clip(
            desired_position, self.servo.workspace_low, self.servo.workspace_high
        )
        self._servo_end_effector(desired_position)

        self.episode_step += 1
        observation = self._get_observation()
        tip_distance = float(np.linalg.norm(self.target_position - self._peg_tip_position()))
        base_distance = float(
            np.linalg.norm(self.approach_position - self._peg_base_position())
        )
        xy_distance = float(
            np.linalg.norm((self.target_position - self._peg_tip_position())[:2])
        )
        is_success = tip_distance < 0.006 and xy_distance < 0.004
        current_metrics = self._collect_reward_metrics(is_success=is_success)
        if self.previous_reward_metrics is None:
            self.previous_reward_metrics = current_metrics
        remaining_steps = self.max_episode_steps - self.episode_step
        self.last_reward_breakdown = self.reward_fn.compute(
            previous_metrics=self.previous_reward_metrics,
            current_metrics=current_metrics,
            action_norm=float(np.linalg.norm(clipped_action)),
            remaining_steps=remaining_steps,
            target_insertion_depth=self.target_insertion_depth,
        )
        reward = self.last_reward_breakdown.total_reward
        self.previous_reward_metrics = current_metrics
        terminated = bool(is_success or current_metrics.is_jammed)
        truncated = self.episode_step >= self.max_episode_steps
        info = self._get_info()
        return observation, reward, terminated, truncated, info

    def close(self) -> None:
        return None

    def _servo_end_effector(self, desired_position: np.ndarray) -> None:
        self.last_controller_diagnostics = self.controller.execute(
            model=self.model,
            data=self.data,
            desired_position=desired_position,
            site_id=self.peg_base_site_id,
            arm_joint_ids=self.arm_joint_ids,
            arm_qpos_indices=self.arm_qpos_indices,
            arm_ctrl_indices=self.arm_ctrl_indices,
            finger_qpos_indices=self.finger_qpos_indices,
            finger_ctrl_indices=self.finger_ctrl_indices,
            finger_home=self.home_qpos[7:],
            impedance_command=self.impedance_command,
            tracked_geom_ids=self.peg_geom_ids,
            wall_geom_ids=self.socket_wall_geom_ids,
            bottom_geom_ids=self.base_plate_geom_ids,
            jacobian_position=self.jacobian_position,
            jacobian_rotation=self.jacobian_rotation,
            joint_limit_clipper=self._clip_arm_joint_limits,
        )
        self.peak_contact_force = max(
            self.peak_contact_force, self.last_controller_diagnostics.peak_contact_force
        )

    def _solve_home_qpos(self) -> np.ndarray:
        mujoco.mj_resetData(self.model, self.data)
        self.data.qpos[:] = 0.0
        self.data.qvel[:] = 0.0
        mujoco.mj_forward(self.model, self.data)
        target_position = self.data.site_xpos[self.approach_site_id].copy()
        return self._solve_qpos_for_tip_target(target_position)

    def _solve_qpos_for_tip_target(
        self,
        target_position: np.ndarray,
        *,
        initial_qpos: np.ndarray | None = None,
    ) -> np.ndarray:
        mujoco.mj_resetData(self.model, self.data)
        self.data.qvel[:] = 0.0
        if initial_qpos is None:
            self.data.qpos[:] = 0.0
        else:
            self.data.qpos[:] = initial_qpos
        mujoco.mj_forward(self.model, self.data)
        desired_axis_world = np.asarray(
            self.controller.config.desired_tool_axis, dtype=np.float64
        )
        orientation_gain = max(self.controller.config.orientation_gain, 2.0)

        for _ in range(200):
            mujoco.mj_forward(self.model, self.data)
            position_error = target_position - self._peg_tip_position()
            current_rotation = self.data.site_xmat[self.peg_tip_site_id].reshape(3, 3)
            orientation_error = self.controller.compute_axis_alignment_error(
                current_axis_world=current_rotation[:, 2],
                desired_axis_world=desired_axis_world,
            )
            if np.linalg.norm(position_error) < 1e-4 and np.linalg.norm(
                orientation_error
            ) < self.controller.config.orientation_convergence_tol:
                break

            self.jacobian_position.fill(0.0)
            self.jacobian_rotation.fill(0.0)
            mujoco.mj_jacSite(
                self.model,
                self.data,
                self.jacobian_position,
                self.jacobian_rotation,
                self.peg_tip_site_id,
            )
            arm_jacobian_position = self.jacobian_position[:, : self.arm_qpos_indices.size]
            arm_jacobian_rotation = self.jacobian_rotation[:, : self.arm_qpos_indices.size]
            weighted_orientation_jacobian = orientation_gain * arm_jacobian_rotation
            task_jacobian = np.vstack(
                (arm_jacobian_position, weighted_orientation_jacobian)
            )
            task_error = np.concatenate(
                (position_error, orientation_gain * orientation_error)
            )
            regularized = task_jacobian @ task_jacobian.T + 1e-4 * np.eye(6)
            delta_q = task_jacobian.T @ np.linalg.solve(regularized, task_error)
            self.data.qpos[self.arm_qpos_indices] += 0.5 * delta_q
            self._clip_arm_joint_limits()

        self.data.qpos[self.finger_qpos_indices] = 0.02
        mujoco.mj_forward(self.model, self.data)
        return self.data.qpos.copy()

    def _uses_reset_curriculum(self) -> bool:
        if self.reset_config.curriculum_stages:
            return True
        lower, upper = self.reset_config.start_depth_fraction_range
        return bool(upper > 0.0 or lower > 0.0 or self.reset_config.start_xy_noise_m > 0.0)

    def _sample_curriculum_tip_position(self) -> np.ndarray:
        stage = self._sample_curriculum_stage()
        lower, upper = stage.start_depth_fraction_range
        start_depth_fraction = float(self.np_random.uniform(lower, upper))
        start_tip_position = self.approach_position + start_depth_fraction * (
            self.target_position - self.approach_position
        )
        if stage.start_xy_noise_m > 0.0:
            start_tip_position[:2] += self.np_random.uniform(
                -stage.start_xy_noise_m,
                stage.start_xy_noise_m,
                size=2,
            )
        return start_tip_position

    def _sample_curriculum_stage(self) -> CurriculumStage:
        if not self.reset_config.curriculum_stages:
            return CurriculumStage(
                start_xy_noise_m=self.reset_config.start_xy_noise_m,
                start_depth_fraction_range=self.reset_config.start_depth_fraction_range,
            )

        weights = np.asarray(
            [max(stage.weight, 0.0) for stage in self.reset_config.curriculum_stages],
            dtype=np.float64,
        )
        if float(np.sum(weights)) <= 0.0:
            weights = np.ones_like(weights) / max(weights.size, 1)
        else:
            weights = weights / np.sum(weights)
        stage_index = int(self.np_random.choice(len(self.reset_config.curriculum_stages), p=weights))
        return self.reset_config.curriculum_stages[stage_index]

    def _clip_arm_joint_limits(self) -> None:
        for joint_id, qpos_index in zip(self.arm_joint_ids, self.arm_qpos_indices, strict=True):
            lower, upper = self.model.jnt_range[joint_id]
            self.data.qpos[qpos_index] = np.clip(self.data.qpos[qpos_index], lower, upper)

    def _ee_position(self) -> np.ndarray:
        return self.data.site_xpos[self.ee_site_id].copy()

    def _peg_base_position(self) -> np.ndarray:
        return self.data.site_xpos[self.peg_base_site_id].copy()

    def _peg_tip_position(self) -> np.ndarray:
        return self.data.site_xpos[self.peg_tip_site_id].copy()

    def _get_observation(self) -> np.ndarray:
        peg_tip_position = self._peg_tip_position()
        target_delta = self.target_position - peg_tip_position
        progress = np.array(
            [self.episode_step / max(self.max_episode_steps, 1)], dtype=np.float64
        )
        contact_features = np.array(
            [
                min(self.last_controller_diagnostics.contact_count / 4.0, 1.0),
                min(self.last_controller_diagnostics.contact_force_norm / 300.0, 1.0),
            ],
            dtype=np.float64,
        )
        phase_features = self._get_phase_features()
        observation = np.concatenate(
            [
                peg_tip_position,
                self.target_position,
                target_delta,
                self.impedance_command,
                progress,
                contact_features,
                phase_features,
            ]
        )
        return observation.astype(np.float32)

    def _get_phase_features(self) -> np.ndarray:
        peg_tip_position = self._peg_tip_position()
        xy_distance = float(np.linalg.norm((self.target_position - peg_tip_position)[:2]))
        insertion_depth = float(
            np.clip(self.approach_position[2] - peg_tip_position[2], 0.0, self.target_insertion_depth)
        )
        depth_remaining_ratio = float(
            np.clip(
                max(self.target_insertion_depth - insertion_depth, 0.0)
                / max(self.target_insertion_depth, 1e-6),
                0.0,
                1.0,
            )
        )
        insertion_progress_ratio = float(
            np.clip(insertion_depth / max(self.target_insertion_depth, 1e-6), 0.0, 1.0)
        )
        xy_alignment = float(np.clip(1.0 - xy_distance / 0.02, 0.0, 1.0))
        has_contact = float(self.last_controller_diagnostics.contact_count > 0)
        return np.array(
            [xy_alignment, depth_remaining_ratio, insertion_progress_ratio, has_contact],
            dtype=np.float64,
        )

    def _collect_reward_metrics(self, *, is_success: bool | None = None) -> RewardMetrics:
        peg_tip_position = self._peg_tip_position()
        peg_base_position = self._peg_base_position()
        xy_distance = float(np.linalg.norm((self.target_position - peg_tip_position)[:2]))
        z_distance = float(abs(self.target_position[2] - peg_tip_position[2]))
        insertion_depth = float(
            np.clip(self.approach_position[2] - peg_tip_position[2], 0.0, self.target_insertion_depth)
        )
        if is_success is None:
            tip_distance = float(np.linalg.norm(self.target_position - peg_tip_position))
            is_success = tip_distance < 0.006 and xy_distance < 0.004
        return RewardMetrics(
            tip_distance=float(np.linalg.norm(self.target_position - peg_tip_position)),
            xy_distance=xy_distance,
            z_distance=z_distance,
            base_distance=float(np.linalg.norm(self.approach_position - peg_base_position)),
            insertion_depth=insertion_depth,
            contact_force_norm=self.last_controller_diagnostics.contact_force_norm,
            is_success=is_success,
            is_jammed=self.last_controller_diagnostics.is_jammed,
        )

    def _get_info(self) -> dict[str, np.ndarray | float | bool]:
        ee_position = self._ee_position()
        peg_base_position = self._peg_base_position()
        peg_tip_position = self._peg_tip_position()
        distance = float(np.linalg.norm(self.target_position - peg_tip_position))
        xy_distance = float(np.linalg.norm((self.target_position - peg_tip_position)[:2]))
        base_distance = float(np.linalg.norm(self.approach_position - peg_base_position))
        return {
            "ee_position": ee_position.astype(np.float32),
            "peg_base_position": peg_base_position.astype(np.float32),
            "peg_tip_position": peg_tip_position.astype(np.float32),
            "target_position": self.target_position.astype(np.float32),
            "approach_position": self.approach_position.astype(np.float32),
            "distance_to_target": distance,
            "base_distance_to_approach": base_distance,
            "impedance_command": self.impedance_command.astype(np.float32),
            "contact_count": self.last_controller_diagnostics.contact_count,
            "contact_force_norm": self.last_controller_diagnostics.contact_force_norm,
            "wall_contact_force_norm": self.last_controller_diagnostics.wall_contact_force_norm,
            "bottom_contact_force_norm": self.last_controller_diagnostics.bottom_contact_force_norm,
            "peak_contact_force": self.peak_contact_force,
            "is_jammed": self.last_controller_diagnostics.is_jammed,
            "is_success": distance < 0.006 and xy_distance < 0.004,
            "phase_features": {
                "xy_alignment": float(self._get_phase_features()[0]),
                "depth_remaining_ratio": float(self._get_phase_features()[1]),
                "insertion_progress_ratio": float(self._get_phase_features()[2]),
                "has_contact": bool(self._get_phase_features()[3]),
            },
            "reward_breakdown": self.last_reward_breakdown.as_dict(),
        }
