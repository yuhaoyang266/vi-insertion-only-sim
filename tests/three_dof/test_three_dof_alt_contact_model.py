from __future__ import annotations

import csv
from dataclasses import fields
import json
from pathlib import Path

from vi_full.three_dof_alt_contact_model import (
    ALT_CONTACT_MODEL_CHANGED_FIELDS,
    ALT_CONTACT_MODEL_NAME,
    BASE_CONTACT_MODEL_NAME,
    build_alt_contact_model_config,
    build_alt_contact_model_spec,
    run_alt_contact_model_cross_check,
    summarize_alt_contact_model_spec,
    write_alt_contact_model_cross_check_artifacts,
)
from vi_full.three_dof_contact_parameter_sensitivity import SENSITIVITY_SUMMARY_METRICS
from vi_full.three_dof_profiles import DEFAULT_UNCERTAINTY_PROFILES
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

    changed_fields = {
        field.name
        for field in fields(base)
        if getattr(alternative, field.name) != getattr(base, field.name)
    }

    assert changed_fields == set(ALT_CONTACT_MODEL_CHANGED_FIELDS)


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


def test_alt_contact_model_cross_check_runs_small_real_artifact() -> None:
    report = run_alt_contact_model_cross_check(
        profiles=["nominal"],
        seeds=[0],
        episodes_per_seed=1,
        policy_names=["fixed_impedance"],
    )

    assert report["artifact_type"] == "three_dof_alt_contact_model_cross_check"
    assert report["contact_models"] == [BASE_CONTACT_MODEL_NAME, ALT_CONTACT_MODEL_NAME]
    assert report["config"]["profiles"] == ["nominal"]
    assert report["config"]["policy_names"] == ["fixed_impedance"]
    assert {row["contact_model"] for row in report["rows"]} == {
        BASE_CONTACT_MODEL_NAME,
        ALT_CONTACT_MODEL_NAME,
    }
    assert len(report["rows"]) == 2
    assert len(report["paired_deltas"]) == 1
    for metric_name in SENSITIVITY_SUMMARY_METRICS:
        assert metric_name in report["rows"][0]
        assert metric_name in report["paired_deltas"][0]["alternative_minus_base"]


def test_alt_contact_model_cross_check_writes_artifacts(tmp_path: Path) -> None:
    report = run_alt_contact_model_cross_check(
        profiles=["nominal"],
        seeds=[0],
        episodes_per_seed=1,
        policy_names=["fixed_impedance"],
    )

    paths = write_alt_contact_model_cross_check_artifacts(
        tmp_path / "alt_contact_model_cross_check.json",
        report,
    )

    assert set(paths) == {"json", "csv", "markdown"}
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "three_dof_alt_contact_model_cross_check"
    csv_rows = list(csv.DictReader(paths["csv"].read_text(encoding="utf-8").splitlines()))
    assert {row["contact_model"] for row in csv_rows} == {
        BASE_CONTACT_MODEL_NAME,
        ALT_CONTACT_MODEL_NAME,
    }
    markdown = paths["markdown"].read_text(encoding="utf-8")
    assert "within-A fallback" in markdown
    assert ALT_CONTACT_MODEL_NAME in markdown


def test_committed_alt_contact_model_artifact_covers_week1_grid() -> None:
    artifact_path = (
        Path(__file__).resolve().parents[2]
        / "outputs"
        / "revision"
        / "alt_contact_model_cross_check_20260501.json"
    )

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert payload["config"]["profiles"] == list(DEFAULT_UNCERTAINTY_PROFILES)
    assert payload["config"]["seeds"] == [0, 1, 2]
    assert payload["config"]["policy_names"] == ["fixed_impedance", "variable_impedance"]
    assert payload["contact_models"] == [BASE_CONTACT_MODEL_NAME, ALT_CONTACT_MODEL_NAME]
    assert len(payload["rows"]) == 20
    assert len(payload["paired_deltas"]) == 10
