import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "artifacts" / "main_benchmark" / "main_benchmark_manifest.json"
CANONICAL_MAIN_KEY = "canonical_main_benchmark"


def test_reviewer_snapshot_has_core_release_layout() -> None:
    expected_paths = [
        "README.md",
        "paper/main.tex",
        "docs/figure_asset_manifest.md",
        "figures/main/fig1_task_policy_impedance_overview.pdf",
        "figures/main/fig2_main_benchmark_evaluation_class_summary.pdf",
        "figures/main/fig3_high_friction_impedance_mechanism.pdf",
        "scripts/export/build_paper_assets.py",
        "src/vi_full",
        "tests/reviewer",
    ]

    missing = [relative for relative in expected_paths if not (REPO_ROOT / relative).exists()]

    assert missing == []


def test_reviewer_snapshot_manifest_resolves_main_benchmark_artifact() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    canonical = manifest["artifacts"][CANONICAL_MAIN_KEY]
    benchmark_path = REPO_ROOT / canonical["path"]

    assert canonical["schema_version"] == 3
    assert canonical["source_role"] == "stage3_current_manuscript_claim"
    assert "main manuscript" in canonical["claim_scope"]
    assert benchmark_path.is_file()


def test_reviewer_snapshot_paper_and_figure_manifest_use_canonical_source() -> None:
    paper = (REPO_ROOT / "paper" / "main.tex").read_text(encoding="utf-8")
    figure_manifest = (REPO_ROOT / "docs" / "figure_asset_manifest.md").read_text(
        encoding="utf-8"
    )

    assert "artifacts/main_benchmark/main_benchmark_manifest.json" in paper
    assert "canonical_main_benchmark" in figure_manifest
    assert "three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json" in figure_manifest
