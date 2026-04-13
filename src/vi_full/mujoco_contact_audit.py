from __future__ import annotations

from collections import Counter

import mujoco
import numpy as np

from vi_full.controllers import ControllerConfig
from vi_full.env import PandaVariableImpedanceEnv, ResetConfig


def classify_mujoco_contact_regime(
    *,
    contact_count: int,
    peak_contact_force: float,
    is_jammed: bool,
    safe_contact_force_threshold_n: float,
) -> str:
    if is_jammed:
        return "jammed"
    if contact_count <= 0:
        return "no_contact"
    if peak_contact_force < safe_contact_force_threshold_n:
        return "safe_contact"
    return "high_force_contact"


class MujocoContactProbe:
    def __init__(
        self,
        *,
        target_xy_noise_m: float = 0.0,
        max_episode_steps: int = 8,
        safe_contact_force_threshold_n: float | None = None,
    ) -> None:
        if max_episode_steps <= 0:
            raise ValueError("max_episode_steps must be positive")
        self.env = PandaVariableImpedanceEnv(
            max_episode_steps=max_episode_steps,
            reset_config=ResetConfig(target_xy_noise_m=target_xy_noise_m),
        )
        self.safe_contact_force_threshold_n = (
            safe_contact_force_threshold_n
            if safe_contact_force_threshold_n is not None
            else ControllerConfig().jam_force_threshold
        )

    def close(self) -> None:
        self.env.close()

    def probe_rollout(
        self,
        *,
        xy_error_m: float,
        start_tip_height_offset_m: float,
        action_dz: float,
        impedance_action: float,
        steps: int = 3,
        seed: int = 0,
    ) -> dict[str, object]:
        if steps <= 0:
            raise ValueError("steps must be positive")

        env = self.env
        env.max_episode_steps = max(env.max_episode_steps, steps)
        env.reset(seed=seed)
        start_tip = env.target_position + np.array(
            [xy_error_m, 0.0, start_tip_height_offset_m],
            dtype=np.float64,
        )
        qpos = env._solve_qpos_for_tip_target(start_tip, initial_qpos=env.home_qpos)
        env.data.qpos[:] = 0.0
        env.data.qvel[:] = 0.0
        env.data.qpos[env.arm_qpos_indices] = qpos[:7]
        env.data.qpos[env.finger_qpos_indices] = qpos[7:]
        env.data.ctrl[env.arm_ctrl_indices] = qpos[:7]
        env.data.ctrl[env.finger_ctrl_indices] = qpos[7:]
        mujoco.mj_forward(env.model, env.data)
        env.episode_step = 0
        env.peak_contact_force = 0.0
        env.previous_reward_metrics = env._collect_reward_metrics()

        action = np.array(
            [0.0, 0.0, action_dz, impedance_action, impedance_action],
            dtype=np.float32,
        )
        peak_contact_forces: list[float] = []
        contact_counts: list[int] = []
        classifications: list[str] = []
        first_jam_step: int | None = None

        for step_index in range(steps):
            _, _, terminated, truncated, info = env.step(action)
            peak_force = float(info["peak_contact_force"])
            contact_count = int(info["contact_count"])
            is_jammed = bool(info["is_jammed"])
            peak_contact_forces.append(peak_force)
            contact_counts.append(contact_count)
            classifications.append(
                classify_mujoco_contact_regime(
                    contact_count=contact_count,
                    peak_contact_force=peak_force,
                    is_jammed=is_jammed,
                    safe_contact_force_threshold_n=self.safe_contact_force_threshold_n,
                )
            )
            if first_jam_step is None and is_jammed:
                first_jam_step = step_index + 1
            if terminated or truncated:
                break
        regime = "no_contact"
        if any(item == "jammed" for item in classifications):
            regime = "jammed"
        elif any(item == "high_force_contact" for item in classifications):
            regime = "high_force_contact"
        elif any(item == "safe_contact" for item in classifications):
            regime = "safe_contact"

        return {
            "xy_error_m": float(xy_error_m),
            "start_tip_height_offset_m": float(start_tip_height_offset_m),
            "action_dz": float(action_dz),
            "impedance_action": float(impedance_action),
            "safe_contact_force_threshold_n": float(
                self.safe_contact_force_threshold_n
            ),
            "max_episode_steps": int(env.max_episode_steps),
            "steps_requested": int(steps),
            "steps_executed": len(classifications),
            "peak_contact_force_trace_n": [float(value) for value in peak_contact_forces],
            "contact_count_trace": [int(value) for value in contact_counts],
            "jammed_trace": [item == "jammed" for item in classifications],
            "classifications": classifications,
            "regime": regime,
            "jammed": regime == "jammed",
            "first_jam_step": first_jam_step,
            "max_contact_count": int(max(contact_counts, default=0)),
            "max_peak_contact_force": float(max(peak_contact_forces, default=0.0)),
            "final_peak_contact_force": float(
                peak_contact_forces[-1] if peak_contact_forces else 0.0
            ),
        }


def probe_mujoco_contact_rollout(
    *,
    xy_error_m: float,
    start_tip_height_offset_m: float,
    action_dz: float,
    impedance_action: float,
    steps: int = 3,
    seed: int = 0,
    target_xy_noise_m: float = 0.0,
    max_episode_steps: int = 8,
    safe_contact_force_threshold_n: float | None = None,
) -> dict[str, object]:
    probe = MujocoContactProbe(
        target_xy_noise_m=target_xy_noise_m,
        max_episode_steps=max_episode_steps,
        safe_contact_force_threshold_n=safe_contact_force_threshold_n,
    )
    try:
        return probe.probe_rollout(
            xy_error_m=xy_error_m,
            start_tip_height_offset_m=start_tip_height_offset_m,
            action_dz=action_dz,
            impedance_action=impedance_action,
            steps=steps,
            seed=seed,
        )
    finally:
        probe.close()


def summarize_mujoco_contact_slice(
    probe_results: list[dict[str, object]],
) -> dict[str, object]:
    if not probe_results:
        raise ValueError("probe_results must not be empty")

    sorted_results = sorted(probe_results, key=lambda item: float(item["xy_error_m"]))
    regime_counts = Counter(str(item["regime"]) for item in sorted_results)
    first_high_force_xy_error_m: float | None = None
    first_jammed_xy_error_m: float | None = None
    last_safe_contact_xy_error_m: float | None = None

    for item in sorted_results:
        xy_error_m = float(item["xy_error_m"])
        regime = str(item["regime"])
        if regime == "safe_contact":
            last_safe_contact_xy_error_m = xy_error_m
        if regime == "high_force_contact" and first_high_force_xy_error_m is None:
            first_high_force_xy_error_m = xy_error_m
        if regime == "jammed" and first_jammed_xy_error_m is None:
            first_jammed_xy_error_m = xy_error_m

    return {
        "num_points": len(sorted_results),
        "regime_counts": dict(regime_counts),
        "safe_contact_exists": regime_counts.get("safe_contact", 0) > 0,
        "last_safe_contact_xy_error_m": last_safe_contact_xy_error_m,
        "first_high_force_xy_error_m": first_high_force_xy_error_m,
        "first_jammed_xy_error_m": first_jammed_xy_error_m,
    }
