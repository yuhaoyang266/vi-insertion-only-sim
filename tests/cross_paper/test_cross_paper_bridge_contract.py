from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from vi_full import cross_paper_bridge


def test_action_mapping_clips_and_decodes_paper_a_action_for_paper_b() -> None:
    mapped = cross_paper_bridge.map_paper_a_action_to_paper_b(
        np.array([2.0, -2.0, 0.5, 0.25, 0.75], dtype=np.float32)
    )

    np.testing.assert_allclose(mapped.schema_p_action, [1.0, -1.0, 0.5, 0.25, 0.75])
    assert mapped.clipped is True
    assert mapped.dyaw == 0.0
    assert mapped.env_action["dx"] == pytest.approx(0.0012)
    assert mapped.env_action["dy"] == pytest.approx(-0.0012)
    assert mapped.env_action["dz"] == pytest.approx(0.0005)
    np.testing.assert_allclose(
        mapped.env_action["k_cart_diag"],
        [42.5, 42.5, 113.75, 0.0, 0.0, 0.0],
    )


@pytest.mark.parametrize(
    "bad_action",
    [
        np.zeros(4, dtype=np.float32),
        np.zeros((1, 5), dtype=np.float32),
        np.array([0.0, 0.0, 0.0, np.nan, 0.0], dtype=np.float32),
    ],
)
def test_action_mapping_rejects_invalid_action_shape_or_values(bad_action: np.ndarray) -> None:
    with pytest.raises(ValueError):
        cross_paper_bridge.map_paper_a_action_to_paper_b(bad_action)


def test_paper_b_observation_projects_to_paper_a_observation() -> None:
    paper_b_observation = SimpleNamespace(
        ee_pos=np.array([0.10, -0.04, 0.02], dtype=float),
        ee_twist=np.array([0.20, -0.10, 0.05, 1.0, 2.0, 3.0], dtype=float),
        wrench=np.array([1.0, 2.0, 3.0, 0.01, 0.02, 0.03], dtype=float),
        contact_count=2,
        contact_state="edge",
    )
    previous_action = np.array([0.5, 0.0, -0.5, 0.25, 0.75], dtype=float)

    projected = cross_paper_bridge.project_paper_b_observation_to_paper_a(
        paper_b_observation,
        hole_origin_world=np.array([0.08, -0.01, 0.01], dtype=float),
        previous_schema_p_action=previous_action,
    )

    assert projected.out_of_paper_a_scope is False
    assert projected.contact_state == "edge"
    assert projected.contact_count == 2
    assert projected.dropped_torque_norm_nm == pytest.approx(np.linalg.norm([0.01, 0.02, 0.03]))
    np.testing.assert_allclose(
        projected.observation,
        [0.02, -0.03, 0.01, 0.20, -0.10, 0.05, 1.0, 2.0, 3.0, 0.5, 0.0, -0.5, 0.25, 0.75],
    )


def test_paper_b_observation_can_finite_difference_velocity() -> None:
    paper_b_observation = {
        "ee_pos": [0.11, 0.0, 0.03],
        "wrench": [0.0, 0.0, 1.0],
    }

    projected = cross_paper_bridge.project_paper_b_observation_to_paper_a(
        paper_b_observation,
        hole_origin_world=np.array([0.10, 0.0, 0.01], dtype=float),
        previous_schema_p_action=np.zeros(5, dtype=float),
        previous_relative_position=np.array([0.0, 0.0, 0.01], dtype=float),
        dt_s=0.02,
    )

    np.testing.assert_allclose(projected.observation[3:6], [0.5, 0.0, 0.5])


def test_policy_stub_registry_covers_required_paper_a_suites() -> None:
    assert tuple(cross_paper_bridge.PAPER_A_POLICY_SUITE_NAMES) == (
        "ppo_no_bc",
        "bc_only_stable_r32_p32",
        "fixed_impedance_rl_stable_r32_p32",
        "repaired_mainline_bc_to_ppo",
        "dapg_lite_repaired_mainline",
    )

    wrapper = cross_paper_bridge.build_policy_stub("repaired_mainline_bc_to_ppo")

    assert wrapper.suite_name == "repaired_mainline_bc_to_ppo"
    assert wrapper.status == "not_available"
    with pytest.raises(RuntimeError, match="not available"):
        wrapper.act(np.zeros(14, dtype=np.float32))
