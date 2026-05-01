from __future__ import annotations

import csv
import json
from pathlib import Path

from vi_full.cross_sim_ranking import (
    CROSS_SIM_RECORD_SCHEMA_VERSION,
    RANKING_METRICS,
    build_cross_sim_ranking,
    write_cross_sim_ranking_artifacts,
)


def _record(**overrides):
    record = {
        "schema_version": CROSS_SIM_RECORD_SCHEMA_VERSION,
        "suite_name": "bc_only_stable_r32_p32",
        "profile": "nominal",
        "seed": 0,
        "episode_count": 1,
        "status": "completed",
        "episode_status": "completed",
        "reason": "",
        "paper_a_policy_artifact": "stub_policy.json",
        "paper_b_env_config": "stub_env.json",
        "out_of_paper_a_scope": False,
        "mean_dropped_torque_norm_nm": 0.0,
        **{metric_name: 0.0 for metric_name in RANKING_METRICS},
    }
    record.update(overrides)
    return record


def test_cross_sim_ranking_orders_completed_rows_before_unavailable() -> None:
    records = [
        _record(
            suite_name="bc_only_stable_r32_p32",
            success_rate=1.0,
            mean_peak_contact_force=2.0,
            mean_final_distance=0.0005,
            mean_contact_steps=12.0,
            mean_contact_work=0.02,
        ),
        _record(
            suite_name="ppo_no_bc",
            success_rate=0.0,
            mean_peak_contact_force=0.0,
            mean_final_distance=0.01,
            mean_contact_steps=0.0,
            mean_contact_work=0.0,
        ),
        _record(
            suite_name="repaired_mainline_bc_to_ppo",
            status="not_available",
            episode_status="not_available",
            reason="policy artifact missing",
            paper_a_policy_artifact="not_available",
            paper_b_env_config="not_available",
            out_of_paper_a_scope=None,
            mean_dropped_torque_norm_nm=None,
            **{metric_name: None for metric_name in RANKING_METRICS},
        ),
    ]

    ranking = build_cross_sim_ranking(
        records,
        metadata={"contract_sha": "abc", "paper_b_checkout_commit": "def"},
    )

    assert [row["suite_name"] for row in ranking["rows"]] == [
        "bc_only_stable_r32_p32",
        "ppo_no_bc",
        "repaired_mainline_bc_to_ppo",
    ]
    assert ranking["rows"][0]["status"] == "completed"
    assert ranking["rows"][0]["success_rate"] == 1.0
    assert ranking["rows"][2]["status"] == "not_available"
    assert ranking["metadata"]["paper_b_checkout_commit"] == "def"


def test_cross_sim_ranking_marks_partial_suite_as_failed() -> None:
    ranking = build_cross_sim_ranking(
        [
            _record(
                suite_name="mixed_suite",
                success_rate=1.0,
                mean_peak_contact_force=2.0,
                mean_final_distance=0.0005,
            ),
            _record(
                suite_name="mixed_suite",
                profile="tight_clearance",
                status="failed",
                episode_status="failed",
                reason="Paper-B episode failed",
            ),
        ],
    )

    row = ranking["rows"][0]
    assert row["status"] == "failed"
    assert row["completed_record_count"] == 1
    assert row["success_rate"] == 1.0
    assert row["reason"] == "Paper-B episode failed"


def test_cross_sim_ranking_writes_json_csv_and_markdown(tmp_path: Path) -> None:
    ranking = build_cross_sim_ranking(
        [
            _record(
                suite_name="bc_only_stable_r32_p32",
                success_rate=1.0,
                mean_peak_contact_force=2.0,
                mean_final_distance=0.0005,
                mean_contact_steps=12.0,
                mean_contact_work=0.02,
            )
        ],
        metadata={"contract_sha": "abc"},
    )

    paths = write_cross_sim_ranking_artifacts(tmp_path / "cross_sim_ranking.json", ranking)

    assert set(paths) == {"json", "csv", "markdown"}
    assert json.loads(paths["json"].read_text(encoding="utf-8"))["artifact_type"] == "cross_sim_ranking"
    csv_rows = list(csv.DictReader(paths["csv"].read_text(encoding="utf-8").splitlines()))
    assert csv_rows[0]["suite_name"] == "bc_only_stable_r32_p32"
    assert "bc_only_stable_r32_p32" in paths["markdown"].read_text(encoding="utf-8")


def test_cross_sim_ranking_rejects_completed_records_without_real_metrics() -> None:
    records = [_record(success_rate=None)]

    try:
        build_cross_sim_ranking(records)
    except ValueError as exc:
        assert "completed cross-sim records must include real episode metrics" in str(exc)
    else:
        raise AssertionError("completed record without metrics should fail")


def test_cross_sim_ranking_rejects_not_available_records_with_metrics() -> None:
    records = [
        _record(
            status="not_available",
            episode_status="not_available",
            paper_a_policy_artifact="not_available",
            paper_b_env_config="not_available",
            out_of_paper_a_scope=None,
            mean_dropped_torque_norm_nm=None,
            success_rate=0.0,
            **{
                metric_name: None
                for metric_name in RANKING_METRICS
                if metric_name != "success_rate"
            },
        )
    ]

    try:
        build_cross_sim_ranking(records)
    except ValueError as exc:
        assert "not_available cross-sim records must keep metrics null" in str(exc)
    else:
        raise AssertionError("not_available record with metrics should fail")
