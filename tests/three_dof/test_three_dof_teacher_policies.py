import numpy as np
import pytest

from vi_full.three_dof_policies import (
    ThreeDoFFixedImpedancePolicy,
    ThreeDoFVariableImpedancePolicy,
    build_3dof_teacher_metadata,
    compose_3dof_teacher_action,
    resolve_3dof_teacher_spec,
)


def _sample_observations() -> list[np.ndarray]:
    return [
        np.array(
            [
                0.0002,
                -0.0001,
                0.0120,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            dtype=np.float32,
        ),
        np.array(
            [
                0.0024,
                0.0,
                0.0075,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            dtype=np.float32,
        ),
        np.array(
            [
                0.0018,
                -0.0004,
                0.0065,
                0.0,
                0.0,
                0.0,
                0.24,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            dtype=np.float32,
        ),
        np.array(
            [
                0.0004,
                0.0003,
                0.0050,
                0.0,
                0.0,
                0.0,
                0.30,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            dtype=np.float32,
        ),
        np.array(
            [
                0.0016,
                0.0,
                0.0040,
                0.0,
                0.0,
                0.0,
                0.22,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            dtype=np.float32,
        ),
    ]


def _legacy_cartesian_action_from_observation(observation: np.ndarray) -> np.ndarray:
    rel_pos = np.asarray(observation[:3], dtype=np.float32)
    normalization = np.array([0.004, 0.004, 0.006], dtype=np.float32)
    return np.clip(-rel_pos / normalization, -1.0, 1.0)


def _legacy_fixed_impedance_action(observation: np.ndarray) -> np.ndarray:
    cartesian = _legacy_cartesian_action_from_observation(observation)
    return np.concatenate(
        [cartesian, np.array([0.6, 0.6], dtype=np.float32)],
        dtype=np.float32,
    )


def _legacy_variable_impedance_action(observation: np.ndarray) -> np.ndarray:
    cartesian = _legacy_cartesian_action_from_observation(observation)
    rel_pos = np.asarray(observation[:3], dtype=np.float32)
    force_norm = float(np.linalg.norm(np.asarray(observation[6:9], dtype=np.float32)))
    lateral_error = float(np.linalg.norm(rel_pos[:2]))
    contact = force_norm >= 0.2
    near_contact = float(rel_pos[2]) <= 0.008

    stiffness_xy = 0.65 if lateral_error > 0.0015 else 0.4
    stiffness_z = 0.75 if float(rel_pos[2]) > 0.008 else 0.35
    if near_contact:
        cartesian[2] = np.clip(cartesian[2], -0.35, 0.25)

    if contact:
        cartesian[:2] = np.clip(cartesian[:2] * 1.15, -1.0, 1.0)
        cartesian[2] = np.clip(cartesian[2], -0.08, 0.25)
        stiffness_xy *= 0.35
        stiffness_z *= 0.25

    return np.concatenate(
        [cartesian, np.array([stiffness_xy, stiffness_z], dtype=np.float32)],
        dtype=np.float32,
    )


def test_resolve_3dof_teacher_spec_legacy_aliases_to_expected_presets() -> None:
    variable_spec = resolve_3dof_teacher_spec(policy_name="variable_impedance")
    fixed_spec = resolve_3dof_teacher_spec(policy_name="fixed_impedance")
    pose_spec = resolve_3dof_teacher_spec(policy_name="pose_only")

    assert variable_spec.preset_name == "teacher_variable_variable"
    assert variable_spec.motion_rule == "contact_aware_variable_motion"
    assert variable_spec.impedance_rule == "contact_aware_variable_impedance"
    assert fixed_spec.preset_name == "teacher_pose_fixed"
    assert fixed_spec.motion_rule == "pose_feedback"
    assert fixed_spec.impedance_rule == "fixed"
    assert pose_spec.preset_name == "teacher_pose_zero"
    assert pose_spec.motion_rule == "pose_feedback"
    assert pose_spec.impedance_rule == "fixed"
    assert variable_spec.contact_force_threshold == 0.2
    assert variable_spec.near_contact_depth_m == 0.008
    assert variable_spec.lateral_error_switch_m == 0.0015
    assert variable_spec.contact_xy_gain == 1.15


def test_resolve_3dof_teacher_spec_prefers_explicit_teacher_spec() -> None:
    explicit_spec = resolve_3dof_teacher_spec(policy_name="teacher_pose_variable")

    resolved_spec = resolve_3dof_teacher_spec(
        policy_name="fixed_impedance",
        teacher_spec=explicit_spec,
    )

    assert resolved_spec == explicit_spec


def test_resolve_3dof_teacher_spec_rejects_unknown_preset() -> None:
    with pytest.raises(ValueError, match="Unknown 3DoF teacher preset"):
        resolve_3dof_teacher_spec(policy_name="teacher_unknown")


def test_build_3dof_teacher_metadata_prefers_explicit_teacher_spec() -> None:
    metadata = build_3dof_teacher_metadata(
        policy_name="fixed_impedance",
        teacher_spec=resolve_3dof_teacher_spec(policy_name="teacher_pose_variable"),
    )

    assert metadata["bc_demo_policy_name"] == "fixed_impedance"
    assert metadata["teacher_preset_name"] == "teacher_pose_variable"
    assert metadata["teacher_motion_rule"] == "pose_feedback"
    assert metadata["teacher_impedance_rule"] == "contact_aware_variable_impedance"
    assert metadata["bc_demo_teacher_spec"]["preset_name"] == "teacher_pose_variable"


def test_teacher_variable_variable_matches_legacy_variable_impedance_policy_actions() -> None:
    spec = resolve_3dof_teacher_spec(policy_name="variable_impedance")

    for observation in _sample_observations():
        expected = _legacy_variable_impedance_action(observation)
        actual = compose_3dof_teacher_action(spec, observation)
        np.testing.assert_allclose(actual, expected, rtol=0.0, atol=0.0)


def test_teacher_pose_fixed_matches_legacy_fixed_impedance_policy_actions() -> None:
    spec = resolve_3dof_teacher_spec(policy_name="fixed_impedance")

    for observation in _sample_observations():
        expected = _legacy_fixed_impedance_action(observation)
        actual = compose_3dof_teacher_action(spec, observation)
        np.testing.assert_allclose(actual, expected, rtol=0.0, atol=0.0)


def test_policy_wrappers_still_match_legacy_reference_actions() -> None:
    variable_policy = ThreeDoFVariableImpedancePolicy()
    fixed_policy = ThreeDoFFixedImpedancePolicy()

    for observation in _sample_observations():
        np.testing.assert_allclose(
            variable_policy.act(observation),
            _legacy_variable_impedance_action(observation),
            rtol=0.0,
            atol=0.0,
        )
        np.testing.assert_allclose(
            fixed_policy.act(observation),
            _legacy_fixed_impedance_action(observation),
            rtol=0.0,
            atol=0.0,
        )
