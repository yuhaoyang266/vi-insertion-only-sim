from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from vi_full.three_dof_contact_parameter_sensitivity import (
    build_contact_parameter_grid,
    identify_most_sensitive_parameter,
    identify_most_sensitive_parameters_by_metric,
    run_contact_parameter_sensitivity,
    write_contact_parameter_sensitivity_artifacts,
)


def test_contact_parameter_grid_covers_default_parameters_and_levels() -> None:
    grid = build_contact_parameter_grid()
    names = {point["parameter_name"] for point in grid}
    levels = {point["level_name"] for point in grid}

    assert names == {
        "contact_xy_scale",
        "contact_z_scale",
        "wall_friction_range",
        "force_noise_std_range",
        "contact_transition_band_m",
    }
    assert levels == {"low", "nominal", "high"}
    assert len(grid) == 15


def test_contact_parameter_sensitivity_runs_small_real_sweep() -> None:
    report = run_contact_parameter_sensitivity(
        profiles=["nominal"],
        seeds=[0],
        episodes_per_seed=1,
        policy_names=["fixed_impedance"],
        parameter_names=["contact_xy_scale"],
        level_names=["low", "nominal"],
    )

    assert report["artifact_type"] == "three_dof_contact_parameter_sensitivity"
    assert len(report["rows"]) == 2
    assert report["most_sensitive_parameters_by_metric"]["mean_peak_contact_force"][
        "metric_name"
    ] == "mean_peak_contact_force"
    assert {row["level_name"] for row in report["rows"]} == {"low", "nominal"}
    assert all(row["profile"] == "nominal" for row in report["rows"])
    assert all(row["policy_name"] == "fixed_impedance" for row in report["rows"])
    assert all("success_rate" in row for row in report["rows"])


def test_contact_parameter_sensitivity_rejects_non_positive_episode_count() -> None:
    with pytest.raises(ValueError, match="episodes_per_seed"):
        run_contact_parameter_sensitivity(
            profiles=["nominal"],
            seeds=[0],
            episodes_per_seed=0,
            policy_names=["fixed_impedance"],
            parameter_names=["contact_xy_scale"],
            level_names=["nominal"],
        )


def test_contact_parameter_sensitivity_nominal_level_preserves_profile_baseline() -> None:
    report = run_contact_parameter_sensitivity(
        profiles=["high_friction"],
        seeds=[0],
        episodes_per_seed=1,
        policy_names=["fixed_impedance"],
        parameter_names=["wall_friction_range"],
        level_names=["nominal"],
    )

    assert report["rows"][0]["overrides"]["wall_friction_range"] == [0.28, 0.46]


def test_identify_most_sensitive_parameter_uses_success_delta() -> None:
    rows = [
        {"parameter_name": "a", "level_name": "nominal", "success_rate": 0.8},
        {"parameter_name": "a", "level_name": "low", "success_rate": 0.7},
        {"parameter_name": "b", "level_name": "nominal", "success_rate": 0.8},
        {"parameter_name": "b", "level_name": "high", "success_rate": 0.2},
    ]

    result = identify_most_sensitive_parameter(rows)

    assert result["parameter_name"] == "b"
    assert result["max_abs_success_delta"] == pytest.approx(0.6)


def test_identify_most_sensitive_parameter_compares_matching_profile_policy() -> None:
    rows = [
        {
            "parameter_name": "contact_xy_scale",
            "level_name": "nominal",
            "profile": "nominal",
            "policy_name": "fixed_impedance",
            "success_rate": 1.0,
        },
        {
            "parameter_name": "contact_xy_scale",
            "level_name": "high",
            "profile": "nominal",
            "policy_name": "fixed_impedance",
            "success_rate": 1.0,
        },
        {
            "parameter_name": "contact_xy_scale",
            "level_name": "nominal",
            "profile": "tight_clearance",
            "policy_name": "fixed_impedance",
            "success_rate": 0.0,
        },
        {
            "parameter_name": "contact_xy_scale",
            "level_name": "high",
            "profile": "tight_clearance",
            "policy_name": "fixed_impedance",
            "success_rate": 0.0,
        },
        {
            "parameter_name": "contact_z_scale",
            "level_name": "nominal",
            "profile": "nominal",
            "policy_name": "fixed_impedance",
            "success_rate": 0.5,
        },
        {
            "parameter_name": "contact_z_scale",
            "level_name": "high",
            "profile": "nominal",
            "policy_name": "fixed_impedance",
            "success_rate": 0.8,
        },
    ]

    result = identify_most_sensitive_parameter(rows)

    assert result["parameter_name"] == "contact_z_scale"
    assert result["max_abs_success_delta"] == pytest.approx(0.3)


def test_identify_most_sensitive_parameters_reports_each_metric() -> None:
    rows = [
        {
            "parameter_name": "contact_xy_scale",
            "level_name": "nominal",
            "profile": "nominal",
            "policy_name": "fixed_impedance",
            "success_rate": 1.0,
            "jam_rate": 0.0,
            "mean_peak_contact_force": 2.0,
            "mean_final_distance": 0.001,
            "mean_contact_work": 0.01,
        },
        {
            "parameter_name": "contact_xy_scale",
            "level_name": "high",
            "profile": "nominal",
            "policy_name": "fixed_impedance",
            "success_rate": 1.0,
            "jam_rate": 0.0,
            "mean_peak_contact_force": 5.0,
            "mean_final_distance": 0.001,
            "mean_contact_work": 0.02,
        },
        {
            "parameter_name": "force_noise_std_range",
            "level_name": "nominal",
            "profile": "nominal",
            "policy_name": "fixed_impedance",
            "success_rate": 1.0,
            "jam_rate": 0.0,
            "mean_peak_contact_force": 2.0,
            "mean_final_distance": 0.001,
            "mean_contact_work": 0.01,
        },
        {
            "parameter_name": "force_noise_std_range",
            "level_name": "high",
            "profile": "nominal",
            "policy_name": "fixed_impedance",
            "success_rate": 1.0,
            "jam_rate": 0.25,
            "mean_peak_contact_force": 2.5,
            "mean_final_distance": 0.003,
            "mean_contact_work": 0.07,
        },
    ]

    summary = identify_most_sensitive_parameters_by_metric(
        rows,
        metric_names=(
            "success_rate",
            "jam_rate",
            "mean_peak_contact_force",
            "mean_final_distance",
            "mean_contact_work",
        ),
    )

    assert summary["success_rate"]["max_abs_delta"] == pytest.approx(0.0)
    assert summary["jam_rate"]["parameter_name"] == "force_noise_std_range"
    assert summary["mean_peak_contact_force"]["parameter_name"] == "contact_xy_scale"
    assert summary["mean_final_distance"]["parameter_name"] == "force_noise_std_range"
    assert summary["mean_contact_work"]["max_abs_delta"] == pytest.approx(0.06)


def test_contact_parameter_sensitivity_writes_artifacts(tmp_path: Path) -> None:
    report = {
        "artifact_type": "three_dof_contact_parameter_sensitivity",
        "schema_version": 1,
        "config": {},
        "most_sensitive_parameter": {"parameter_name": "contact_xy_scale"},
        "most_sensitive_parameters_by_metric": {
            "success_rate": {
                "parameter_name": "contact_xy_scale",
                "profile": "nominal",
                "policy_name": "fixed_impedance",
                "level_name": "nominal",
                "nominal_value": 1.0,
                "level_value": 1.0,
                "max_abs_delta": 0.0,
            }
        },
        "rows": [
            {
                "parameter_name": "contact_xy_scale",
                "level_name": "nominal",
                "profile": "nominal",
                "policy_name": "fixed_impedance",
                "success_rate": 1.0,
                "jam_rate": 0.0,
                "mean_peak_contact_force": 1.2,
                "mean_final_distance": 0.0005,
                "mean_contact_steps": 10.0,
                "mean_contact_work": 0.01,
            }
        ],
    }

    paths = write_contact_parameter_sensitivity_artifacts(
        tmp_path / "contact_parameter_sensitivity.json",
        report,
    )

    assert set(paths) == {"json", "csv", "markdown"}
    assert json.loads(paths["json"].read_text(encoding="utf-8"))["artifact_type"] == report["artifact_type"]
    csv_rows = list(csv.DictReader(paths["csv"].read_text(encoding="utf-8").splitlines()))
    assert csv_rows[0]["parameter_name"] == "contact_xy_scale"
    assert "contact_xy_scale" in paths["markdown"].read_text(encoding="utf-8")
