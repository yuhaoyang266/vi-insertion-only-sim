import json
from pathlib import Path

import pytest


METHOD_SPECS = {
    "ppo_no_bc": {"label": "PPO w/o BC", "algorithm": "ppo"},
    "sac_no_bc": {"label": "SAC w/o BC", "algorithm": "sac"},
    "td3_no_bc": {"label": "TD3 w/o BC", "algorithm": "td3"},
}


DISTANCE_MM = {
    "ppo_no_bc": {50_000: 31.02, 100_000: 29.47, 200_000: 25.48},
    "sac_no_bc": {50_000: 23.27, 100_000: 17.58, 200_000: 16.67},
    "td3_no_bc": {50_000: 30.78, 100_000: 28.62, 200_000: 25.56},
}


def _complete_pilot_report(*, contact_steps: float = 0.0) -> dict[str, object]:
    summary_rows: list[dict[str, object]] = []
    methods: list[dict[str, object]] = []
    for method_name, spec in METHOD_SPECS.items():
        points: list[dict[str, object]] = []
        for budget, final_distance_mm in DISTANCE_MM[method_name].items():
            metrics = {
                "success_rate": 0.0,
                "mean_first_contact_step": 64.0,
                "mean_final_distance_mm": final_distance_mm,
                "mean_contact_steps": contact_steps,
                "mean_peak_contact_force_n": 0.0,
                "jam_rate": 0.0,
            }
            points.append(
                {
                    "budget": budget,
                    "source_chunk_path": (
                        f"outputs/pilot_chunks/"
                        f"three_dof_cross_family_pilot__{method_name}__{budget}.json"
                    ),
                    "five_profile_mean": metrics,
                    "nominal": metrics,
                }
            )
            summary_rows.append(
                {
                    "method_name": method_name,
                    "label": spec["label"],
                    "algorithm": spec["algorithm"],
                    "budget": budget,
                    **metrics,
                }
            )
        methods.append(
            {
                "method_name": method_name,
                "label": spec["label"],
                "algorithm": spec["algorithm"],
                "points": points,
            }
        )

    return {
        "experiment_name": "three_dof_cross_family_pilot",
        "generated_at": "2026-04-20T17:05:50",
        "expected_grid": {
            "method_names": list(METHOD_SPECS),
            "budget_points": [50_000, 100_000, 200_000],
            "expected_chunk_count": 9,
            "completed_chunk_count": 9,
            "missing_chunk_count": 0,
        },
        "completed_chunks": [
            {"method_name": row["method_name"], "budget": row["budget"]}
            for row in summary_rows
        ],
        "missing_chunks": [],
        "methods": methods,
        "summary_rows": summary_rows,
    }


def _write_report(tmp_path: Path, payload: dict[str, object]) -> Path:
    report_path = tmp_path / "three_dof_cross_family_pilot_report.json"
    report_path.write_text(json.dumps(payload), encoding="utf-8")
    return report_path


def test_confirm_report_requires_complete_9_chunk_grid(tmp_path: Path) -> None:
    from vi_full.three_dof_cross_family_confirm_report import build_confirm_report

    payload = _complete_pilot_report()
    payload["expected_grid"] = {
        **payload["expected_grid"],
        "completed_chunk_count": 8,
        "missing_chunk_count": 1,
    }
    pilot_report = _write_report(tmp_path, payload)

    with pytest.raises(ValueError, match="complete 9-chunk grid"):
        build_confirm_report(pilot_report)


def test_confirm_report_requires_complete_summary_row_grid(tmp_path: Path) -> None:
    from vi_full.three_dof_cross_family_confirm_report import build_confirm_report

    payload = _complete_pilot_report()
    payload["summary_rows"] = [
        row
        for row in payload["summary_rows"]
        if not (row["method_name"] == "td3_no_bc" and row["budget"] == 100_000)
    ]
    pilot_report = _write_report(tmp_path, payload)

    with pytest.raises(ValueError, match="summary_rows must cover"):
        build_confirm_report(pilot_report)


def test_confirm_report_selects_branch_a_when_all_methods_have_zero_contact(
    tmp_path: Path,
) -> None:
    from vi_full.three_dof_cross_family_confirm_report import build_confirm_report

    confirm = build_confirm_report(_write_report(tmp_path, _complete_pilot_report()))

    assert confirm["grid_complete"] is True
    assert confirm["selected_branch"] == "branch_a"
    assert "zero useful-contact steps" in confirm["branch_rationale"]
    assert all(
        summary["entered_contact"] is False
        for summary in confirm["method_summaries"]
    )


def test_confirm_report_marks_sac_as_best_distance_proxy(tmp_path: Path) -> None:
    from vi_full.three_dof_cross_family_confirm_report import build_confirm_report

    confirm = build_confirm_report(_write_report(tmp_path, _complete_pilot_report()))

    assert confirm["best_distance_proxy_method"] == "sac_no_bc"
    sac_summary = next(
        summary
        for summary in confirm["method_summaries"]
        if summary["method_name"] == "sac_no_bc"
    )
    assert sac_summary["best_budget"] == 200_000
    assert sac_summary["best_final_distance_mm"] == pytest.approx(16.67)
    assert sac_summary["distance_improvement_50k_to_200k_mm"] == pytest.approx(6.6)
    assert sac_summary["is_best_distance_proxy"] is True


def test_confirm_report_rejects_success_claim_when_contact_steps_are_zero(
    tmp_path: Path,
) -> None:
    from vi_full.three_dof_cross_family_confirm_report import build_confirm_report

    confirm = build_confirm_report(_write_report(tmp_path, _complete_pilot_report()))

    assert "pure RL remains outside useful contact" in confirm["paper_claim_boundary"]["allowed"]
    assert "sac_no_bc is the strongest distance proxy but still zero-contact" in confirm["paper_claim_boundary"]["allowed"]
    assert "sac_no_bc solves insertion or enters useful contact" in confirm["paper_claim_boundary"]["not_allowed"]
    assert "off-policy reaches useful contact" in confirm["paper_claim_boundary"]["not_allowed"]
    assert all(
        "success" not in allowed_claim.lower()
        for allowed_claim in confirm["paper_claim_boundary"]["allowed"]
    )


@pytest.mark.parametrize("missing_field", ["jam_rate", "mean_peak_contact_force_n"])
def test_confirm_report_rejects_missing_zero_contact_metrics(
    tmp_path: Path,
    missing_field: str,
) -> None:
    from vi_full.three_dof_cross_family_confirm_report import build_confirm_report

    payload = _complete_pilot_report()
    del payload["summary_rows"][0][missing_field]
    pilot_report = _write_report(tmp_path, payload)

    with pytest.raises(ValueError, match=missing_field):
        build_confirm_report(pilot_report)


def test_contact_gate_table_counts_zero_contact_cells(tmp_path: Path) -> None:
    from vi_full.three_dof_cross_family_confirm_report import (
        build_confirm_report,
        export_contact_gate_table,
    )

    payload = _complete_pilot_report()
    for row in payload["summary_rows"]:
        if row["method_name"] == "sac_no_bc" and row["budget"] == 100_000:
            row["mean_contact_steps"] = 2.0
            break
    confirm = build_confirm_report(_write_report(tmp_path, payload))

    table_path = export_contact_gate_table(confirm, tmp_path)
    table_text = table_path.read_text(encoding="utf-8")

    assert "8/9 zero-contact method-budget cells" in table_text
    assert "| SAC w/o BC | 100000 | 17.58 | yes |" in table_text
