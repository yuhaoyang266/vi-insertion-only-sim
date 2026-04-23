import json
from pathlib import Path

from vi_full.sprint3_teacher_mini_ablation_kickoff import (
    build_sprint3_teacher_mini_ablation_kickoff,
    export_sprint3_teacher_mini_ablation_kickoff_artifacts,
    render_sprint3_teacher_mini_ablation_kickoff_markdown,
)
from vi_full.three_dof_policies import resolve_3dof_teacher_spec


def test_kickoff_freezes_four_condition_teacher_quality_budget_boundary() -> None:
    kickoff = build_sprint3_teacher_mini_ablation_kickoff()
    rows = kickoff["condition_matrix"]

    assert kickoff["export_name"] == "sprint3_teacher_mini_ablation_kickoff"
    assert kickoff["target_question"]["primary_axis"] == "teacher_support_quality"
    assert kickoff["target_question"]["secondary_axis"] == "demo_rollout_budget"
    assert len(rows) == 4
    assert {
        (row["teacher_support_quality"], row["demo_budget_label"]) for row in rows
    } == {
        ("support_rich", "many_demo"),
        ("support_rich", "few_demo"),
        ("support_poor", "many_demo"),
        ("support_poor", "few_demo"),
    }
    assert {row["bc_pretrain_steps"] for row in rows} == {32}
    assert {row["total_timesteps"] for row in rows} == {128}
    assert {row["bc_batch_size"] for row in rows} == {64}
    assert {row["policy_init"] for row in rows} == {"bc_to_ppo_from_scratch"}
    assert all(
        row["uncertainty_profiles"]
        == [
            "nominal",
            "tight_clearance",
            "high_friction",
            "offset_bias",
            "noisy_force",
        ]
        for row in rows
    )
    assert kickoff["required_metrics"] == [
        "success_rate",
        "mean_final_distance_mm",
        "mean_contact_steps",
        "jam_rate",
        "mean_peak_contact_force_n",
        "support_coverage_index",
        "support_cell_coverage",
    ]
    assert kickoff["excluded_axes"] == [
        "BC pretrain-step sweep",
        "policy initialization sweep",
        "teacher/no-teacher pure-RL control",
        "full motion-rule x impedance-rule appendix sweep",
    ]


def test_kickoff_condition_teacher_metadata_matches_registry() -> None:
    kickoff = build_sprint3_teacher_mini_ablation_kickoff()

    for row in kickoff["condition_matrix"]:
        teacher_spec = resolve_3dof_teacher_spec(
            policy_name=row["teacher_preset_name"]
        )
        assert row["teacher_motion_rule"] == teacher_spec.motion_rule
        assert row["teacher_impedance_rule"] == teacher_spec.impedance_rule


def test_markdown_exposes_closure_criteria_and_claim_boundary() -> None:
    markdown = render_sprint3_teacher_mini_ablation_kickoff_markdown(
        build_sprint3_teacher_mini_ablation_kickoff()
    )

    assert "# Sprint 3 Teacher Mini-Ablation Kickoff" in markdown
    assert "teacher support quality x demo rollout budget" in markdown
    assert "support_coverage_index" in markdown
    assert "artifact reproducible" in markdown
    assert "not a leaderboard" in markdown
    assert "teacher-independent causal claim" in markdown


def test_export_writes_deterministic_json_and_markdown(tmp_path) -> None:
    first = export_sprint3_teacher_mini_ablation_kickoff_artifacts(tmp_path)
    first_json = first["json_path"].read_bytes()
    first_csv = first["csv_path"].read_bytes()
    first_markdown = first["markdown_path"].read_bytes()

    second = export_sprint3_teacher_mini_ablation_kickoff_artifacts(tmp_path)

    assert first["json_path"].read_bytes() == first_json
    assert first["csv_path"].read_bytes() == first_csv
    assert second["markdown_path"].read_bytes() == first_markdown
    payload = json.loads(first["json_path"].read_text(encoding="utf-8"))
    assert payload["condition_count"] == 4
    assert payload["closure_criteria"]["contract_tests_required"] is True
    assert "teacher_support_quality" in first["csv_path"].read_text(encoding="utf-8")
    assert first["pdf_path"].suffix == ".pdf"
    assert first["png_path"].suffix == ".png"
    assert first["pdf_path"].exists()
    assert first["png_path"].stat().st_size > 0


def test_repo_docs_reference_frozen_sprint3_kickoff_boundary() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    task_plan = (repo_root / "task_plan.md").read_text(encoding="utf-8")
    docs = "\n".join(
        [
            (repo_root / "README.md").read_text(encoding="utf-8"),
            (repo_root / "docs" / "figure_asset_manifest.md").read_text(
                encoding="utf-8"
            ),
            task_plan,
        ]
    )

    assert "outputs/sprint3_teacher_mini_ablation/sprint3_teacher_mini_ablation_kickoff.json" in docs
    assert "outputs/sprint3_teacher_mini_ablation/sprint3_teacher_mini_ablation_kickoff_matrix.pdf" in docs
    assert "teacher support quality x demo rollout budget" in docs
    assert (
        "Phase 3 Sprint 3 kickoff complete" in task_plan
        or "Phase 3 complete" in task_plan
    )
    assert "- [x] Sprint 3: Teacher mini-ablation kickoff" in task_plan
    assert "next: Sprint 3 teacher mini-ablation" not in task_plan
    assert "2×2×2×2" not in docs
