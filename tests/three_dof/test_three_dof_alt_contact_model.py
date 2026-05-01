from __future__ import annotations

from vi_full.three_dof_alt_contact_model import (
    ALT_CONTACT_MODEL_CHANGED_FIELDS,
    build_alt_contact_model_config,
    build_alt_contact_model_spec,
    summarize_alt_contact_model_spec,
)
from vi_full.three_dof_profiles import build_3dof_profile_config


def test_alt_contact_model_preserves_observation_action_and_metric_contracts() -> None:
    base = build_3dof_profile_config("nominal")
    alternative = build_alt_contact_model_config("nominal")

    assert alternative.action_dim == base.action_dim == 5
    assert alternative.observation_dim == base.observation_dim == 14
    assert alternative.max_episode_steps == base.max_episode_steps
    assert alternative.success_lateral_tolerance_m == base.success_lateral_tolerance_m
    assert alternative.success_axial_tolerance_m == base.success_axial_tolerance_m
    assert alternative.jam_force_threshold_n == base.jam_force_threshold_n
    assert alternative.jam_persistence_steps == base.jam_persistence_steps


def test_alt_contact_model_changes_only_contact_law_assumptions() -> None:
    base = build_3dof_profile_config("high_friction")
    alternative = build_alt_contact_model_config("high_friction")

    for field in ALT_CONTACT_MODEL_CHANGED_FIELDS:
        assert getattr(alternative, field) != getattr(base, field)

    assert alternative.wall_friction_range == base.wall_friction_range
    assert alternative.force_noise_std_range == base.force_noise_std_range
    assert alternative.clearance_range_m == base.clearance_range_m
    assert alternative.hole_xy_offset_range_m == base.hole_xy_offset_range_m


def test_alt_contact_model_summary_marks_within_a_fallback_scope() -> None:
    spec = build_alt_contact_model_spec("tight_clearance")
    summary = summarize_alt_contact_model_spec(spec)

    assert summary["base_profile"] == "tight_clearance"
    assert "within-A fallback" in summary["claim_scope"]
    assert "second-simulator" in summary["claim_scope"]
    assert summary["changed_fields"] == list(ALT_CONTACT_MODEL_CHANGED_FIELDS)
    assert "action_dim" in summary["invariant_fields"]
    assert summary["field_deltas"]["contact_xy_scale"]["base"] != summary["field_deltas"][
        "contact_xy_scale"
    ]["alternative"]
