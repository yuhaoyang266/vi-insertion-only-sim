from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class ThreeDoFSupportMetricConfig:
    obs_xy_norm_bin_m: float = 5e-4
    obs_z_bin_m: float = 5e-4
    force_norm_bin_n: float = 0.25
    action_xy_norm_bin: float = 0.1
    action_dz_bin: float = 0.1
    action_k_xy_bin: float = 0.1
    action_k_z_bin: float = 0.1


def _validate_state_action_arrays(
    observations: np.ndarray,
    actions: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    observations_array = np.asarray(observations, dtype=np.float32)
    actions_array = np.asarray(actions, dtype=np.float32)
    if observations_array.ndim != 2:
        raise ValueError("observations must be a 2D array")
    if actions_array.ndim != 2:
        raise ValueError("actions must be a 2D array")
    if observations_array.shape[0] != actions_array.shape[0]:
        raise ValueError("observations and actions must have the same row count")
    if observations_array.shape[1] < 9:
        raise ValueError("observations must expose at least 9 columns")
    if actions_array.shape[1] < 5:
        raise ValueError("actions must expose at least 5 columns")
    return observations_array, actions_array


def _support_bin_widths(config: ThreeDoFSupportMetricConfig) -> np.ndarray:
    widths = np.asarray(
        [
            config.obs_xy_norm_bin_m,
            config.obs_z_bin_m,
            config.force_norm_bin_n,
            config.action_xy_norm_bin,
            config.action_dz_bin,
            config.action_k_xy_bin,
            config.action_k_z_bin,
        ],
        dtype=np.float32,
    )
    if np.any(widths <= 0.0):
        raise ValueError("all support bin widths must be positive")
    return widths


def project_3dof_support_signature(
    observations: np.ndarray,
    actions: np.ndarray,
) -> np.ndarray:
    observations_array, actions_array = _validate_state_action_arrays(
        observations,
        actions,
    )
    obs_xy_norm = np.linalg.norm(observations_array[:, :2], axis=1)
    force_norm = np.linalg.norm(observations_array[:, 6:9], axis=1)
    action_xy_norm = np.linalg.norm(actions_array[:, :2], axis=1)
    return np.column_stack(
        [
            obs_xy_norm,
            observations_array[:, 2],
            force_norm,
            action_xy_norm,
            actions_array[:, 2],
            actions_array[:, 3],
            actions_array[:, 4],
        ]
    ).astype(np.float32)


def quantize_3dof_support_signature(
    signature: np.ndarray,
    *,
    config: ThreeDoFSupportMetricConfig = ThreeDoFSupportMetricConfig(),
) -> np.ndarray:
    signature_array = np.asarray(signature, dtype=np.float32)
    if signature_array.ndim != 2:
        raise ValueError("signature must be a 2D array")
    if signature_array.shape[1] != 7:
        raise ValueError("signature must have exactly 7 columns")
    widths = _support_bin_widths(config)
    return np.rint(signature_array / widths).astype(np.int32)


def compute_3dof_support_coverage_index(
    *,
    demo_observations: np.ndarray,
    demo_actions: np.ndarray,
    rollout_observations: np.ndarray,
    rollout_actions: np.ndarray,
    config: ThreeDoFSupportMetricConfig = ThreeDoFSupportMetricConfig(),
) -> dict[str, float | int]:
    demo_signature = project_3dof_support_signature(demo_observations, demo_actions)
    rollout_signature = project_3dof_support_signature(
        rollout_observations,
        rollout_actions,
    )
    demo_cells = {
        tuple(row)
        for row in quantize_3dof_support_signature(demo_signature, config=config).tolist()
    }
    rollout_cells = [
        tuple(row)
        for row in quantize_3dof_support_signature(rollout_signature, config=config).tolist()
    ]
    covered_rollout_cells = [cell for cell in rollout_cells if cell in demo_cells]
    unique_rollout_cells = set(rollout_cells)
    shared_unique_cells = unique_rollout_cells & demo_cells
    rollout_sample_count = len(rollout_cells)
    rollout_unique_cell_count = len(unique_rollout_cells)
    return {
        "support_coverage_index": 0.0
        if rollout_sample_count == 0
        else float(len(covered_rollout_cells) / rollout_sample_count),
        "covered_rollout_sample_count": int(len(covered_rollout_cells)),
        "rollout_sample_count": int(rollout_sample_count),
        "demo_unique_cell_count": int(len(demo_cells)),
        "rollout_unique_cell_count": int(rollout_unique_cell_count),
        "shared_unique_cell_count": int(len(shared_unique_cells)),
        "support_cell_coverage": 0.0
        if rollout_unique_cell_count == 0
        else float(len(shared_unique_cells) / rollout_unique_cell_count),
    }
