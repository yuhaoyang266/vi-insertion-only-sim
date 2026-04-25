from __future__ import annotations

from vi_full.three_dof_policies import resolve_3dof_teacher_spec
from vi_full.three_dof_teacher_coupling_ablation import (
    build_teacher_coupling_grid,
    summarize_teacher_coupling_results,
)


def test_teacher_coupling_grid_contains_minimal_cross() -> None:
    grid = build_teacher_coupling_grid(seeds=[0, 1, 2], total_timesteps=128)

    assert [condition.name for condition in grid] == [
        "vi_teacher_vi_student",
        "vi_teacher_fi_student",
        "fi_teacher_fi_student",
        "fi_teacher_vi_student",
    ]
    assert {tuple(condition.seeds) for condition in grid} == {(0, 1, 2)}
    assert {condition.total_timesteps for condition in grid} == {128}
    assert {
        (condition.teacher_prior, condition.student_impedance_space)
        for condition in grid
    } == {
        ("variable_impedance", "variable_impedance"),
        ("variable_impedance", "fixed_impedance"),
        ("fixed_impedance", "fixed_impedance"),
        ("fixed_impedance", "variable_impedance"),
    }


def test_teacher_coupling_grid_resolves_teacher_presets() -> None:
    by_name = {condition.name: condition for condition in build_teacher_coupling_grid()}

    vi_teacher = resolve_3dof_teacher_spec(policy_name="teacher_variable_variable")
    fi_teacher = resolve_3dof_teacher_spec(policy_name="teacher_pose_fixed")
    assert by_name["vi_teacher_vi_student"].teacher_spec == vi_teacher
    assert by_name["vi_teacher_fi_student"].teacher_spec == vi_teacher
    assert by_name["fi_teacher_fi_student"].teacher_spec == fi_teacher
    assert by_name["fi_teacher_vi_student"].teacher_spec == fi_teacher


def test_teacher_coupling_suite_kwargs_encode_student_controls() -> None:
    by_name = {condition.name: condition for condition in build_teacher_coupling_grid()}

    vi_kwargs = by_name["vi_teacher_vi_student"].to_suite_run_kwargs(
        episodes=16,
        profiles=["nominal"],
    )
    fi_kwargs = by_name["vi_teacher_fi_student"].to_suite_run_kwargs(
        episodes=16,
        profiles=["nominal"],
    )

    assert vi_kwargs["suite_name"] == "vi_teacher_vi_student"
    assert vi_kwargs["episodes_per_seed"] == 16
    assert vi_kwargs["uncertainty_profiles"] == ["nominal"]
    assert vi_kwargs["bc_demo_policy_name"] == "teacher_variable_variable"
    assert "base_env_overrides" not in vi_kwargs
    assert fi_kwargs["bc_demo_policy_name"] == "teacher_variable_variable"
    assert fi_kwargs["base_env_overrides"]["min_k_xy"] == fi_kwargs["base_env_overrides"]["max_k_xy"]
    assert fi_kwargs["base_env_overrides"]["min_k_z"] == fi_kwargs["base_env_overrides"]["max_k_z"]


def test_summarize_teacher_coupling_results_extracts_gate_metrics() -> None:
    report = {
        "learned_results": {
            "vi_teacher_vi_student": {
                "teacher_prior": "variable_impedance",
                "student_impedance_space": "variable_impedance",
                "teacher_motion_rule": "contact_aware_variable_motion",
                "teacher_impedance_rule": "contact_aware_variable_impedance",
                "five_profile_mean": {
                    "success_rate_mean_over_profiles": 0.75,
                    "jam_rate_mean_over_profiles": 0.10,
                    "mean_peak_contact_force_mean_over_profiles": 1.2,
                    "mean_contact_steps_mean_over_profiles": 12.0,
                    "mean_final_distance_mean_over_profiles": 0.001,
                },
                "support_metrics": {
                    "support_coverage_index_mean_over_profiles": 0.44,
                    "support_cell_coverage_mean_over_profiles": 0.55,
                },
            }
        }
    }

    summary = summarize_teacher_coupling_results(report)

    assert summary["condition_count"] == 1
    row = summary["conditions"][0]
    assert row["condition_name"] == "vi_teacher_vi_student"
    assert row["success_rate"] == 0.75
    assert row["mean_final_distance_mm"] == 1.0
    assert row["support_coverage_index"] == 0.44
    assert "Gate A" in summary["gate"]
