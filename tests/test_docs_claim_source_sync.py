from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = "artifacts/main_benchmark/main_benchmark_manifest.json"
CANONICAL_MAIN_BENCHMARK = (
    "artifacts/main_benchmark/"
    "three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json"
)
SCHEMA2_DIAGNOSTIC = (
    "artifacts/main_benchmark/three_dof_benchmark_schema2_paper_teacher_20260418_034230.json"
)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _manifest_table_row(markdown: str, row_label: str) -> str:
    for line in markdown.splitlines():
        if line.startswith(f"| {row_label} |"):
            return line
    raise AssertionError(f"Missing figure manifest row: {row_label}")


def test_readme_declares_stage3_manifest_as_main_source() -> None:
    readme = _read("README.md")

    assert MANIFEST_PATH in readme
    assert CANONICAL_MAIN_BENCHMARK in readme
    assert "schema-3\nstage3 artifact to the main manuscript Table 1 and Figure 2" in readme
    assert "schema-2 benchmark artifacts remain appendix / diagnostic legacy inputs only" in readme


def test_paper_points_to_manifest_without_schema2_main_source_language() -> None:
    paper = _read("paper/main.tex")

    assert MANIFEST_PATH in paper
    assert "schema2" not in paper.lower()
    assert "schema-2" not in paper.lower()


def test_figure_manifest_uses_stage3_for_main_figure2_and_schema2_only_for_appendix() -> None:
    manifest = _read("docs/figure_asset_manifest.md")

    figure2_row = _manifest_table_row(manifest, "Figure 2")
    assert MANIFEST_PATH in figure2_row
    assert "canonical_main_benchmark" in figure2_row
    assert CANONICAL_MAIN_BENCHMARK in figure2_row
    assert "stage3" in figure2_row
    assert "schema2" not in figure2_row.lower()
    assert "schema-2" not in figure2_row.lower()

    for appendix_label in ("Figure A3", "Figure A4"):
        appendix_row = _manifest_table_row(manifest, appendix_label)
        assert SCHEMA2_DIAGNOSTIC in appendix_row
        assert "appendix" in appendix_row.lower()
