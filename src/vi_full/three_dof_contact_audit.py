from __future__ import annotations

from collections import Counter

import numpy as np

from vi_full.three_dof_config import ThreeDoFInsertionConfig
from vi_full.three_dof_env import ThreeDoFInsertionEnv


def _resolve_transition_stiffness_force_scaling_components_from_snapshot(
    config_snapshot: dict[str, object],
) -> tuple[bool, bool, bool]:
    shared = bool(
        config_snapshot.get("contact_transition_stiffness_aware_force_scaling", False)
    )
    scale_xy = bool(
        shared
        or config_snapshot.get(
            "contact_transition_stiffness_aware_force_scaling_xy", False
        )
    )
    scale_z_shared = bool(
        shared
        or config_snapshot.get(
            "contact_transition_stiffness_aware_force_scaling_z", False
        )
    )
    scale_z_axial = bool(
        scale_z_shared
        or config_snapshot.get(
            "contact_transition_stiffness_aware_force_scaling_z_axial", False
        )
    )
    scale_z_coupling = bool(
        scale_z_shared
        or config_snapshot.get(
            "contact_transition_stiffness_aware_force_scaling_z_coupling", False
        )
    )
    return scale_xy, scale_z_axial, scale_z_coupling


def _transition_stiffness_force_scaling_mode(
    *,
    scale_xy: bool,
    scale_z_axial: bool,
    scale_z_coupling: bool,
) -> str:
    if scale_xy and scale_z_axial and scale_z_coupling:
        return "xy_z_full"
    if scale_xy and scale_z_axial:
        return "xy_z_axial"
    if scale_xy and scale_z_coupling:
        return "xy_z_coupling"
    if scale_xy:
        return "xy_only"
    if scale_z_axial and scale_z_coupling:
        return "z_only"
    if scale_z_axial:
        return "z_axial_only"
    if scale_z_coupling:
        return "z_coupling_only"
    return "fixed"


def classify_3dof_contact_regime(
    *,
    contact_force_norm: float,
    blocked_contact: bool,
    is_jammed: bool,
    contact_threshold_n: float,
) -> str:
    if is_jammed:
        return "jammed"
    if blocked_contact:
        return "blocked_contact"
    if contact_force_norm >= contact_threshold_n:
        return "safe_contact"
    return "no_contact"


def probe_3dof_contact_rollout(
    config: ThreeDoFInsertionConfig,
    *,
    xy_error_m: float,
    z_position_m: float,
    action_dz: float,
    stiffness_xy_action: float,
    stiffness_z_action: float,
    clearance_m: float,
    wall_friction: float,
    force_noise_std: float = 0.0,
    steps: int = 1,
    include_contact_debug: bool = False,
) -> dict[str, object]:
    if steps <= 0:
        raise ValueError("steps must be positive")

    env = ThreeDoFInsertionEnv(config)
    try:
        env.reset(seed=0)
        env.target_position = np.array(
            [0.0, 0.0, -config.target_insertion_depth_m],
            dtype=np.float64,
        )
        env.position = np.array([xy_error_m, 0.0, z_position_m], dtype=np.float64)
        env.velocity[:] = 0.0
        env.force_sensor[:] = 0.0
        env.previous_action[:] = 0.0
        env.episode_step = 0
        env.peak_contact_force = 0.0
        env.blocked_contact_steps = 0
        env.contact_force_history.clear()
        env.uncertainty = {
            "hole_xy_offset_m": 0.0,
            "wall_friction": float(wall_friction),
            "clearance_m": float(clearance_m),
            "force_noise_std": float(force_noise_std),
        }
        env.last_reward_breakdown = env._empty_reward_breakdown()
        env.last_action_modifiers = env._empty_action_modifiers()

        action = np.array(
            [0.0, 0.0, action_dz, stiffness_xy_action, stiffness_z_action],
            dtype=np.float32,
        )
        classifications: list[str] = []
        force_norms: list[float] = []
        max_blocked_contact_steps = 0
        first_jam_step: int | None = None
        first_blocked_step: int | None = None

        for step_index in range(steps):
            _, _, terminated, truncated, info = env.step(action)
            force_norm = float(info["contact_force_norm"])
            step_blocked = env.blocked_contact_steps > 0
            step_jammed = bool(info["is_jammed"])
            regime = classify_3dof_contact_regime(
                contact_force_norm=force_norm,
                blocked_contact=step_blocked,
                is_jammed=step_jammed,
                contact_threshold_n=config.contact_reward_force_threshold_n,
            )
            classifications.append(regime)
            force_norms.append(force_norm)
            max_blocked_contact_steps = max(
                max_blocked_contact_steps, env.blocked_contact_steps
            )
            if first_blocked_step is None and step_blocked:
                first_blocked_step = step_index + 1
            if first_jam_step is None and step_jammed:
                first_jam_step = step_index + 1
            if terminated or truncated:
                break
    finally:
        env.close()

    aggregate_regime = "no_contact"
    if any(item == "jammed" for item in classifications):
        aggregate_regime = "jammed"
    elif any(item == "blocked_contact" for item in classifications):
        aggregate_regime = "blocked_contact"
    elif any(item == "safe_contact" for item in classifications):
        aggregate_regime = "safe_contact"

    return {
        "xy_error_m": float(xy_error_m),
        "z_position_m": float(z_position_m),
        "action_dz": float(action_dz),
        "stiffness_xy_action": float(stiffness_xy_action),
        "stiffness_z_action": float(stiffness_z_action),
        "clearance_m": float(clearance_m),
        "wall_friction": float(wall_friction),
        "force_noise_std": float(force_noise_std),
        "steps_requested": int(steps),
        "steps_executed": len(classifications),
        "classifications": classifications,
        "regime": aggregate_regime,
        "jammed": aggregate_regime == "jammed",
        "first_jam_step": first_jam_step,
        "first_blocked_step": first_blocked_step,
        "blocked_contact_steps": int(max_blocked_contact_steps),
        "max_contact_force_norm": float(max(force_norms, default=0.0)),
        "min_contact_force_norm": float(min(force_norms, default=0.0)),
        "final_contact_force_norm": float(force_norms[-1] if force_norms else 0.0),
        "contact_debug": (
            dict(env.last_contact_debug) if include_contact_debug else None
        ),
    }


def collect_3dof_transition_boundary_onset_points(
    config: ThreeDoFInsertionConfig,
    *,
    clearance_m: float,
    wall_friction: float,
    overflow_band_fractions: tuple[float, ...] = (0.1, 0.25, 0.5, 0.75, 0.9),
    z_position_m: float = 0.0,
    action_dz: float = -1.0,
    stiffness_xy_action: float = 1.0,
    stiffness_z_action: float = 1.0,
    force_noise_std: float = 0.0,
) -> list[dict[str, object]]:
    band_m = float(max(config.contact_transition_band_m, 0.0))
    if band_m <= 0.0:
        raise ValueError("contact_transition_band_m must be positive")

    points: list[dict[str, object]] = []
    for overflow_ratio_in_band in overflow_band_fractions:
        overflow_ratio = float(overflow_ratio_in_band)
        if not 0.0 < overflow_ratio < 1.0:
            raise ValueError("overflow_band_fractions must lie strictly within (0, 1)")
        overflow_m = overflow_ratio * band_m
        summary = probe_3dof_contact_rollout(
            config,
            xy_error_m=float(clearance_m + overflow_m),
            z_position_m=z_position_m,
            action_dz=action_dz,
            stiffness_xy_action=stiffness_xy_action,
            stiffness_z_action=stiffness_z_action,
            clearance_m=clearance_m,
            wall_friction=wall_friction,
            force_noise_std=force_noise_std,
            steps=1,
            include_contact_debug=True,
        )
        contact_debug = summary["contact_debug"]
        assert isinstance(contact_debug, dict)
        points.append(
            {
                "overflow_ratio_in_band": overflow_ratio,
                "overflow_m": float(overflow_m),
                "xy_error_m": float(summary["xy_error_m"]),
                "regime": str(summary["regime"]),
                "jammed": bool(summary["jammed"]),
                "first_jam_step": summary["first_jam_step"],
                "direct_axial_z_n": float(contact_debug["direct_axial_z_n"]),
                "z_coupling_n": float(contact_debug["z_coupling_n"]),
                "total_z_n": float(contact_debug["total_z_n"]),
                "force_norm_n": float(contact_debug["force_norm_n"]),
                "transition_blend": float(contact_debug["transition_blend"]),
                "transition_force_scale_z": float(
                    contact_debug["transition_force_scale_z"]
                ),
                "direct_axial_ramp_multiplier": float(
                    contact_debug["direct_axial_ramp_multiplier"]
                ),
            }
        )
    return points


def summarize_3dof_contact_slice(
    probe_results: list[dict[str, object]],
) -> dict[str, object]:
    if not probe_results:
        raise ValueError("probe_results must not be empty")

    sorted_results = sorted(
        probe_results,
        key=lambda item: float(item["xy_error_m"]),
    )
    windows: list[dict[str, object]] = []
    current_window: dict[str, object] | None = None
    first_jammed_xy_error_m: float | None = None
    last_safe_contact_xy_error_m: float | None = None
    regime_counts = Counter(str(item["regime"]) for item in sorted_results)

    for item in sorted_results:
        xy_error_m = float(item["xy_error_m"])
        regime = str(item["regime"])
        if regime == "safe_contact":
            last_safe_contact_xy_error_m = xy_error_m
            if current_window is None:
                current_window = {
                    "start_xy_error_m": xy_error_m,
                    "end_xy_error_m": xy_error_m,
                    "num_points": 1,
                }
            else:
                current_window["end_xy_error_m"] = xy_error_m
                current_window["num_points"] = int(current_window["num_points"]) + 1
        else:
            if regime == "jammed" and first_jammed_xy_error_m is None:
                first_jammed_xy_error_m = xy_error_m
            if current_window is not None:
                current_window["width_m"] = round(
                    float(current_window["end_xy_error_m"])
                    - float(current_window["start_xy_error_m"]),
                    10,
                )
                windows.append(current_window)
                current_window = None

    if current_window is not None:
        current_window["width_m"] = round(
            float(current_window["end_xy_error_m"])
            - float(current_window["start_xy_error_m"]),
            10,
        )
        windows.append(current_window)

    return {
        "num_points": len(sorted_results),
        "regime_counts": dict(regime_counts),
        "safe_contact_exists": bool(windows),
        "safe_contact_windows": windows,
        "largest_safe_contact_window_width_m": float(
            max((float(window["width_m"]) for window in windows), default=0.0)
        ),
        "first_jammed_xy_error_m": first_jammed_xy_error_m,
        "last_safe_contact_xy_error_m": last_safe_contact_xy_error_m,
    }


def summarize_3dof_transition_band_sweep(
    variant_audits: list[dict[str, object]],
) -> dict[str, object]:
    if not variant_audits:
        raise ValueError("variant_audits must not be empty")

    band_sweep = []
    for item in variant_audits:
        config_snapshot = dict(item["config_snapshot"])
        scale_xy, scale_z_axial, scale_z_coupling = (
            _resolve_transition_stiffness_force_scaling_components_from_snapshot(
                config_snapshot
            )
        )
        band_sweep.append(
            {
                "variant_name": str(item["variant_name"]),
                "contact_transition_band_m": float(
                    config_snapshot["contact_transition_band_m"]
                ),
                "contact_transition_stiffness_aware_force_scaling": bool(
                    config_snapshot.get(
                        "contact_transition_stiffness_aware_force_scaling", False
                    )
                ),
                "contact_transition_stiffness_aware_force_scaling_xy": scale_xy,
                "contact_transition_stiffness_aware_force_scaling_z": bool(
                    scale_z_axial or scale_z_coupling
                ),
                "contact_transition_stiffness_aware_force_scaling_z_axial": scale_z_axial,
                "contact_transition_stiffness_aware_force_scaling_z_coupling": scale_z_coupling,
                "contact_transition_direct_axial_ramp_power": float(
                    config_snapshot.get("contact_transition_direct_axial_ramp_power", 0.0)
                ),
                "contact_transition_stiffness_aware_force_scaling_mode": _transition_stiffness_force_scaling_mode(
                    scale_xy=scale_xy,
                    scale_z_axial=scale_z_axial,
                    scale_z_coupling=scale_z_coupling,
                ),
                "nominal_min_stiffness_safe_window_width_m": float(
                    item["key_findings"][
                        "nominal_clearance_safe_window_width_m_at_surface_full_descent"
                    ]
                ),
                "nominal_min_stiffness_first_jammed_xy_error_m": item["key_findings"][
                    "nominal_clearance_first_jammed_xy_error_m_at_surface_full_descent"
                ],
                "nominal_max_stiffness_safe_window_width_m": float(
                    item["key_findings"][
                        "nominal_clearance_safe_window_width_m_at_surface_full_descent_max_stiffness"
                    ]
                ),
                "nominal_max_stiffness_first_jammed_xy_error_m": item["key_findings"][
                    "nominal_clearance_first_jammed_xy_error_m_at_surface_full_descent_max_stiffness"
                ],
            }
        )
    band_sweep = sorted(
        band_sweep,
        key=lambda item: (
            float(item["contact_transition_band_m"]),
            int(bool(item["contact_transition_stiffness_aware_force_scaling_xy"]))
            + int(bool(item["contact_transition_stiffness_aware_force_scaling_z_axial"]))
            + int(
                bool(item["contact_transition_stiffness_aware_force_scaling_z_coupling"])
            ),
            int(bool(item["contact_transition_stiffness_aware_force_scaling_z_axial"]))
            + int(
                bool(item["contact_transition_stiffness_aware_force_scaling_z_coupling"])
            ),
            int(bool(item["contact_transition_stiffness_aware_force_scaling_z_coupling"])),
            float(item["contact_transition_direct_axial_ramp_power"]),
            str(item["variant_name"]),
        ),
    )

    best_min_stiffness_variant = max(
        band_sweep,
        key=lambda item: (
            float(item["nominal_min_stiffness_safe_window_width_m"]),
            float(item["contact_transition_band_m"]),
        ),
    )["variant_name"]
    best_max_stiffness_variant = max(
        band_sweep,
        key=lambda item: (
            float(item["nominal_max_stiffness_safe_window_width_m"]),
            -(
                int(bool(item["contact_transition_stiffness_aware_force_scaling_xy"]))
                + int(bool(item["contact_transition_stiffness_aware_force_scaling_z_axial"]))
                + int(
                    bool(item["contact_transition_stiffness_aware_force_scaling_z_coupling"])
                )
            ),
            -float(item["contact_transition_band_m"]),
        ),
    )["variant_name"]

    return {
        "band_sweep": band_sweep,
        "best_min_stiffness_variant": best_min_stiffness_variant,
        "best_max_stiffness_variant": best_max_stiffness_variant,
    }
