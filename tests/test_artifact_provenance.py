from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_STRINGS = (
    "F:\\",
    "C:\\",
    "D:\\",
    "/Users/",
    "/home/",
    "full_projects",
    "vi_insertion_full_only_sim",
)
TEXT_SUFFIXES = {".bib", ".csv", ".json", ".md", ".tex"}

CANONICAL_STAGE3 = (
    "artifacts/main_benchmark/"
    "three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json"
)
CANONICAL_STATISTICS = (
    "artifacts/main_benchmark/three_dof_statistics_report_stage3_20260412.json"
)
SCHEMA2_DIAGNOSTIC = (
    "artifacts/main_benchmark/"
    "three_dof_benchmark_schema2_paper_teacher_20260418_034230.json"
)
CANONICAL_MANIFEST = "artifacts/main_benchmark/main_benchmark_manifest.json"
CONFIRM_REPORT = "outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json"
EVIDENCE_MATRIX = "outputs/evidence_matrix/three_dof_evidence_matrix.json"


def _sha256(relative_path: str) -> str:
    return hashlib.sha256((REPO_ROOT / relative_path).read_bytes()).hexdigest()


def _paper_facing_text_paths() -> list[Path]:
    paths: list[Path] = [REPO_ROOT / "README.md", REPO_ROOT / "docs" / "figure_asset_manifest.md"]
    for directory in (
        REPO_ROOT / "paper",
        REPO_ROOT / "artifacts" / "main_benchmark",
        REPO_ROOT / "outputs" / "evidence_matrix",
    ):
        paths.extend(
            path
            for path in directory.rglob("*")
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
        )
    return sorted(set(paths))


def _load_json(relative_path: str) -> dict[str, Any]:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def _assert_common_provenance(payload: dict[str, Any]) -> None:
    assert isinstance(payload.get("source_artifacts"), dict)
    assert isinstance(payload.get("source_hashes"), dict)
    assert payload.get("generating_command")
    assert payload.get("git_commit")
    assert "schema_version" in payload or "export_name" in payload


def _assert_sources(
    payload: dict[str, Any], expected_sources: dict[str, str]
) -> None:
    source_artifacts = payload["source_artifacts"]
    source_hashes = payload["source_hashes"]
    for source_name, relative_path in expected_sources.items():
        assert source_artifacts[source_name] == relative_path
        assert source_hashes[source_name] == _sha256(relative_path)


def test_paper_facing_text_artifacts_do_not_leak_local_paths() -> None:
    violations: list[str] = []
    for path in _paper_facing_text_paths():
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(REPO_ROOT).as_posix()
        for line_number, line in enumerate(text.splitlines(), start=1):
            for forbidden in FORBIDDEN_STRINGS:
                if forbidden in line:
                    violations.append(f"{relative}:{line_number}: contains {forbidden!r}")
    assert violations == []


def test_stage3_table_and_statistics_have_source_provenance() -> None:
    table = _load_json("artifacts/main_benchmark/table_3dof_paper_benchmark_stage3_20260412.json")
    _assert_common_provenance(table)
    assert table["schema_version"] == 3
    _assert_sources(
        table,
        {
            "benchmark_report": CANONICAL_STAGE3,
            "statistics_report": CANONICAL_STATISTICS,
        },
    )

    statistics = _load_json(CANONICAL_STATISTICS)
    _assert_common_provenance(statistics)
    assert statistics["schema_version"] == 3
    _assert_sources(statistics, {"benchmark_report": CANONICAL_STAGE3})


def test_schema2_appendix_table_is_diagnostic_legacy_with_provenance() -> None:
    appendix_table = _load_json("artifacts/main_benchmark/table_3dof_appendix_schema2_20260418.json")
    _assert_common_provenance(appendix_table)
    assert appendix_table["role"] == "appendix_diagnostic_legacy"
    assert appendix_table["schema_version"] == 2
    assert "appendix" in appendix_table["claim_scope"]
    assert "main" not in appendix_table["claim_scope"]
    _assert_sources(appendix_table, {"benchmark_report": SCHEMA2_DIAGNOSTIC})


def test_evidence_artifacts_have_manifest_level_provenance() -> None:
    evidence = _load_json(EVIDENCE_MATRIX)
    _assert_common_provenance(evidence)
    _assert_sources(
        evidence,
        {
            "confirm_report": CONFIRM_REPORT,
            "benchmark_manifest": CANONICAL_MANIFEST,
            "benchmark_report": CANONICAL_STAGE3,
        },
    )

    sprint2_table = _load_json("outputs/evidence_matrix/three_dof_sprint2_main_table.json")
    _assert_common_provenance(sprint2_table)
    _assert_sources(
        sprint2_table,
        {
            "confirm_report": CONFIRM_REPORT,
            "benchmark_manifest": CANONICAL_MANIFEST,
            "benchmark_report": CANONICAL_STAGE3,
            "evidence_matrix": EVIDENCE_MATRIX,
        },
    )
