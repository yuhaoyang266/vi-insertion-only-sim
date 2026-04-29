from __future__ import annotations

import pytest

from vi_full.three_dof_impedance_mechanics import (
    compute_force_position_phase_portrait,
    compute_force_work_pareto_rows,
    compute_success_matched_force_curve,
    compute_success_matched_work_curve,
    partition_traces_by_outcome,
)


def _trace_run(
    method: str,
    *,
    success: bool,
    force_offset: float,
    work_scale: float,
) -> dict:
    return {
        "method": method,
        "profile": "high_friction",
        "is_success": success,
        "trace": [
            {
                "step": step,
                "position": float(step) * 0.1,
                "force": force_offset + float(step),
                "contact_work": work_scale * float(step),
            }
            for step in range(4)
        ],
    }


def _method_traces() -> dict[str, list[dict]]:
    return {
        "fixed": [
            _trace_run("fixed", success=True, force_offset=2.0, work_scale=0.02),
            _trace_run("fixed", success=False, force_offset=50.0, work_scale=5.0),
            _trace_run("fixed", success=True, force_offset=4.0, work_scale=0.03),
        ],
        "variable": [
            _trace_run("variable", success=True, force_offset=1.0, work_scale=0.01),
            _trace_run("variable", success=False, force_offset=80.0, work_scale=8.0),
        ],
    }


def test_success_failure_split_partitions_traces() -> None:
    partitions = partition_traces_by_outcome(
        [
            _trace_run("fixed", success=True, force_offset=1.0, work_scale=0.01),
            _trace_run("fixed", success=False, force_offset=9.0, work_scale=0.10),
            {"outcome": "success", "trace": []},
            {"success": False, "trace": []},
        ]
    )

    assert len(partitions["success"]) == 2
    assert len(partitions["failure"]) == 2


def test_success_matched_force_curve_is_deterministic() -> None:
    first = compute_success_matched_force_curve(_method_traces(), num_points=4)
    second = compute_success_matched_force_curve(_method_traces(), num_points=4)

    assert first == second
    assert first["matched_success_count"] == 1
    assert first["curves"]["fixed"]["trace_count_used"] == 1
    assert first["curves"]["fixed"]["force_mean"] == pytest.approx([2.0, 3.0, 4.0, 5.0])
    assert first["curves"]["variable"]["force_mean"] == pytest.approx([1.0, 2.0, 3.0, 4.0])


def test_success_matched_work_curve_is_deterministic() -> None:
    first = compute_success_matched_work_curve(_method_traces(), num_points=4)
    second = compute_success_matched_work_curve(_method_traces(), num_points=4)

    assert first == second
    assert first["curves"]["fixed"]["work_mean"] == pytest.approx([0.0, 0.02, 0.04, 0.06])
    assert first["curves"]["variable"]["work_mean"] == pytest.approx([0.0, 0.01, 0.02, 0.03])


def test_force_position_phase_portrait_uses_success_subset() -> None:
    portrait = compute_force_position_phase_portrait(_method_traces(), num_points=4)

    assert portrait["matched_success_count"] == 1
    assert max(portrait["portraits"]["fixed"]["force_mean"]) < 10.0
    assert max(portrait["portraits"]["variable"]["force_mean"]) < 10.0
    assert portrait["portraits"]["fixed"]["position_mean"] == pytest.approx([0.0, 0.1, 0.2, 0.3])


def test_force_work_pareto_rows_are_sorted_and_labeled() -> None:
    rows = compute_force_work_pareto_rows(_method_traces())

    assert [row["method"] for row in rows] == ["variable", "fixed"]
    assert [row["label"] for row in rows] == ["variable", "fixed"]
    assert rows[0]["mean_contact_work"] < rows[1]["mean_contact_work"]
    assert rows[0]["mean_peak_force"] < rows[1]["mean_peak_force"]
