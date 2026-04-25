from __future__ import annotations

from vi_full.three_dof_policies import resolve_3dof_teacher_spec
from vi_full.three_dof_teacher_coupling_ablation import build_motion_matched_grid


def test_motion_matched_grid_contains_required_conditions() -> None:
    grid = build_motion_matched_grid(seeds=[0, 1], total_timesteps=64)

    assert [condition.name for condition in grid] == [
        "vi_full",
        "fi_full",
        "vi_motion_fi_k",
        "fi_motion_vi_k",
        "tuned_fi_k",
    ]
    assert {tuple(condition.seeds) for condition in grid} == {(0, 1)}
    assert {condition.total_timesteps for condition in grid} == {64}
    assert {
        (condition.name, condition.motion_rule, condition.impedance_rule)
        for condition in grid
    } == {
        ("vi_full", "contact_aware_variable_motion", "contact_aware_variable_impedance"),
        ("fi_full", "pose_feedback", "fixed"),
        ("vi_motion_fi_k", "contact_aware_variable_motion", "fixed"),
        ("fi_motion_vi_k", "pose_feedback", "contact_aware_variable_impedance"),
        ("tuned_fi_k", "pose_feedback", "fixed"),
    }


def test_motion_matched_grid_resolves_crossed_teacher_specs() -> None:
    by_name = {condition.name: condition for condition in build_motion_matched_grid()}

    assert by_name["vi_full"].teacher_spec == resolve_3dof_teacher_spec(
        policy_name="teacher_variable_variable"
    )
    assert by_name["fi_full"].teacher_spec == resolve_3dof_teacher_spec(
        policy_name="teacher_pose_fixed"
    )
    assert by_name["vi_motion_fi_k"].teacher_spec == resolve_3dof_teacher_spec(
        policy_name="teacher_variable_fixed"
    )
    assert by_name["fi_motion_vi_k"].teacher_spec == resolve_3dof_teacher_spec(
        policy_name="teacher_pose_variable"
    )


def test_motion_matched_fixed_k_conditions_encode_stiffness() -> None:
    by_name = {condition.name: condition for condition in build_motion_matched_grid()}

    crossed_kwargs = by_name["vi_motion_fi_k"].to_suite_run_kwargs(
        episodes=8,
        profiles=["nominal"],
    )
    tuned_kwargs = by_name["tuned_fi_k"].to_suite_run_kwargs(
        episodes=8,
        profiles=["nominal"],
    )

    assert crossed_kwargs["base_env_overrides"]["min_k_xy"] == crossed_kwargs["fixed_stiffness_xy"]
    assert crossed_kwargs["base_env_overrides"]["min_k_z"] == crossed_kwargs["fixed_stiffness_z"]
    assert tuned_kwargs["base_env_overrides"]["min_k_xy"] == tuned_kwargs["fixed_stiffness_xy"]
    assert tuned_kwargs["base_env_overrides"]["min_k_z"] == tuned_kwargs["fixed_stiffness_z"]
