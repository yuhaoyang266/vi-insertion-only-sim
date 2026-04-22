from pathlib import Path


def test_sprint2_paper_docs_reference_current_frozen_outputs() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    manifest = (repo_root / "docs" / "figure_asset_manifest.md").read_text(
        encoding="utf-8"
    )
    benchmark_table_cli = (
        repo_root / "scripts" / "export" / "export_paper_only_sim_benchmark_table.py"
    ).read_text(encoding="utf-8")
    checked_text = "\n".join([readme, manifest, benchmark_table_cli])

    assert (
        "artifacts/main_benchmark/"
        "three_dof_benchmark_schema2_paper_teacher_20260418_034230.json"
    ) in checked_text
    assert "outputs/evidence_matrix/three_dof_sprint2_main_table.md" in checked_text
    assert (
        "outputs/cross_family_confirm/"
        "three_dof_cross_family_confirm_learning_curve_summary.png"
    ) in checked_text
    assert "three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json" not in checked_text
    assert "three_dof_statistics_report_stage3_20260412.json" not in checked_text
    assert "table_3dof_paper_benchmark_stage3_20260412" not in checked_text


def test_manuscript_names_sprint2_table_and_sac_claim_boundary() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    manuscript = (repo_root / "paper" / "main.tex").read_text(encoding="utf-8")

    assert "three_dof_sprint2_main_table.md" in manuscript
    assert "three_dof_cross_family_confirm_learning_curve_summary" in manuscript
    assert "SAC w/o BC" in manuscript
    assert "distance proxy" in manuscript
    assert "not a success baseline" in manuscript
    assert "SAC w/o BC} solves insertion" not in manuscript
    assert "SAC w/o BC} enters useful contact" not in manuscript
