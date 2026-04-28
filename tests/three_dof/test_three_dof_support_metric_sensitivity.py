from __future__ import annotations

import numpy as np

from vi_full.three_dof_support_metric_sensitivity import (
    audit_support_metric_rows,
    build_support_metric_sensitivity_report,
    build_sci_sensitivity_configs,
    compute_action_only_sci,
    compute_nearest_demo_distance,
    compute_state_only_sci,
    compute_support_jaccard,
)


def _observations(offset: float = 0.0) -> np.ndarray:
    rows = np.zeros((4, 9), dtype=np.float32)
    rows[:, 0] = np.array([0.0, 0.0002, 0.0004, 0.0006], dtype=np.float32) + offset
    rows[:, 2] = np.array([0.0, -0.0002, -0.0004, -0.0006], dtype=np.float32)
    rows[:, 6] = np.array([0.0, 0.1, 0.2, 0.3], dtype=np.float32)
    return rows


def _actions(offset: float = 0.0) -> np.ndarray:
    rows = np.zeros((4, 5), dtype=np.float32)
    rows[:, 0] = np.array([0.0, 0.05, 0.1, 0.15], dtype=np.float32) + offset
    rows[:, 2] = np.array([-0.1, -0.05, 0.0, 0.05], dtype=np.float32)
    rows[:, 3] = np.array([0.3, 0.4, 0.5, 0.6], dtype=np.float32)
    rows[:, 4] = np.array([0.7, 0.6, 0.5, 0.4], dtype=np.float32)
    return rows


def test_sci_sensitivity_configs_cover_fine_default_coarse() -> None:
    configs = build_sci_sensitivity_configs()
    triples = {
        (cfg.obs_xy_norm_bin_m, cfg.force_norm_bin_n, cfg.action_xy_norm_bin, cfg.action_k_xy_bin)
        for cfg in configs
    }

    assert len(configs) >= 9
    assert {cfg.obs_xy_norm_bin_m for cfg in configs} >= {2.5e-4, 5e-4, 1e-3}
    assert {cfg.force_norm_bin_n for cfg in configs} >= {0.125, 0.25, 0.5}
    assert {cfg.action_xy_norm_bin for cfg in configs} >= {0.05, 0.1, 0.2}
    assert (2.5e-4, 0.125, 0.05, 0.05) in triples
    assert (5e-4, 0.25, 0.1, 0.1) in triples
    assert (1e-3, 0.5, 0.2, 0.2) in triples


def test_alternative_metrics_prefer_identical_rollout() -> None:
    demo_obs = _observations()
    demo_actions = _actions()
    same_obs = _observations()
    same_actions = _actions()
    shifted_obs = _observations(offset=0.01)
    shifted_actions = _actions(offset=1.0)

    assert compute_nearest_demo_distance(
        demo_observations=demo_obs,
        demo_actions=demo_actions,
        rollout_observations=same_obs,
        rollout_actions=same_actions,
    ) < compute_nearest_demo_distance(
        demo_observations=demo_obs,
        demo_actions=demo_actions,
        rollout_observations=shifted_obs,
        rollout_actions=shifted_actions,
    )
    assert compute_support_jaccard(
        demo_observations=demo_obs,
        demo_actions=demo_actions,
        rollout_observations=same_obs,
        rollout_actions=same_actions,
    ) > compute_support_jaccard(
        demo_observations=demo_obs,
        demo_actions=demo_actions,
        rollout_observations=shifted_obs,
        rollout_actions=shifted_actions,
    )
    assert compute_state_only_sci(
        demo_observations=demo_obs,
        rollout_observations=same_obs,
    ) > compute_state_only_sci(
        demo_observations=demo_obs,
        rollout_observations=shifted_obs,
    )
    assert compute_action_only_sci(
        demo_actions=demo_actions,
        rollout_actions=same_actions,
    ) > compute_action_only_sci(
        demo_actions=demo_actions,
        rollout_actions=shifted_actions,
    )


def test_sci_rank_stability_prefers_supported_rollout_for_all_bin_configs() -> None:
    report = build_support_metric_sensitivity_report([])
    rows = report["sci_rank_stability"]

    assert len(rows) == 9
    assert {row["bin_config"] for row in rows} == {
        "fine_state_fine_action",
        "fine_state_default_action",
        "fine_state_coarse_action",
        "default_state_fine_action",
        "default_state_default_action",
        "default_state_coarse_action",
        "coarse_state_fine_action",
        "coarse_state_default_action",
        "coarse_state_coarse_action",
    }
    assert all(row["supported_sci"] > row["shifted_sci"] for row in rows)
    assert all(row["rank_stable"] is True for row in rows)


def test_predictive_audit_rows_include_required_schema() -> None:
    artifact = {
        "rows": [
            {
                "method_name": "demo_supported",
                "success_rate": 0.8,
                "entered_contact": True,
                "jam_rate": 0.1,
                "mean_peak_contact_force_n": 1.5,
                "mean_final_distance_mm": 0.9,
                "mean_contact_steps": 20.0,
            }
        ]
    }

    rows = audit_support_metric_rows(artifact)

    assert rows
    required = {
        "metric_name",
        "condition_name",
        "value",
        "success_rate",
        "contact_entry_rate",
        "jam_rate",
        "peak_force",
        "contact_work",
        "final_distance",
        "contact_steps",
    }
    assert required <= set(rows[0])
