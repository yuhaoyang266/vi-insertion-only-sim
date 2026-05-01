from __future__ import annotations

import csv
import json
from pathlib import Path

from vi_full.cross_sim_ranking import build_cross_sim_ranking, write_cross_sim_ranking_artifacts


def test_cross_sim_ranking_orders_completed_rows_before_unavailable() -> None:
    records = [
        {
            "suite_name": "bc_only_stable_r32_p32",
            "profile": "nominal",
            "seed": 0,
            "status": "completed",
            "success_rate": 1.0,
            "jam_rate": 0.0,
            "mean_peak_contact_force": 2.0,
            "mean_final_distance": 0.0005,
            "mean_contact_steps": 12.0,
            "mean_contact_work": 0.02,
        },
        {
            "suite_name": "ppo_no_bc",
            "profile": "nominal",
            "seed": 0,
            "status": "completed",
            "success_rate": 0.0,
            "jam_rate": 0.0,
            "mean_peak_contact_force": 0.0,
            "mean_final_distance": 0.01,
            "mean_contact_steps": 0.0,
            "mean_contact_work": 0.0,
        },
        {
            "suite_name": "repaired_mainline_bc_to_ppo",
            "profile": "nominal",
            "seed": 0,
            "status": "not_available",
            "reason": "policy artifact missing",
        },
    ]

    ranking = build_cross_sim_ranking(
        records,
        metadata={"contract_sha": "abc", "paper_b_commit": "def"},
    )

    assert [row["suite_name"] for row in ranking["rows"]] == [
        "bc_only_stable_r32_p32",
        "ppo_no_bc",
        "repaired_mainline_bc_to_ppo",
    ]
    assert ranking["rows"][0]["status"] == "completed"
    assert ranking["rows"][0]["success_rate"] == 1.0
    assert ranking["rows"][2]["status"] == "not_available"
    assert ranking["metadata"]["paper_b_commit"] == "def"


def test_cross_sim_ranking_writes_json_csv_and_markdown(tmp_path: Path) -> None:
    ranking = build_cross_sim_ranking(
        [
            {
                "suite_name": "bc_only_stable_r32_p32",
                "profile": "nominal",
                "seed": 0,
                "status": "completed",
                "success_rate": 1.0,
                "jam_rate": 0.0,
                "mean_peak_contact_force": 2.0,
                "mean_final_distance": 0.0005,
                "mean_contact_steps": 12.0,
                "mean_contact_work": 0.02,
            }
        ],
        metadata={"contract_sha": "abc"},
    )

    paths = write_cross_sim_ranking_artifacts(tmp_path / "cross_sim_ranking.json", ranking)

    assert set(paths) == {"json", "csv", "markdown"}
    assert json.loads(paths["json"].read_text(encoding="utf-8"))["artifact_type"] == "cross_sim_ranking"
    csv_rows = list(csv.DictReader(paths["csv"].read_text(encoding="utf-8").splitlines()))
    assert csv_rows[0]["suite_name"] == "bc_only_stable_r32_p32"
    assert "bc_only_stable_r32_p32" in paths["markdown"].read_text(encoding="utf-8")
