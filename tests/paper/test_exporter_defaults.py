from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path("artifacts/main_benchmark/main_benchmark_manifest.json")
STAGE3_BENCHMARK = Path(
    "artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json"
)
STAGE3_STATISTICS = Path("artifacts/main_benchmark/three_dof_statistics_report_stage3_20260412.json")
SCHEMA2_DIAGNOSTIC = Path(
    "artifacts/main_benchmark/three_dof_benchmark_schema2_paper_teacher_20260418_034230.json"
)


def _load_script(relative_path: str, module_name: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_benchmark_table_exporter_defaults_to_manifest_sources() -> None:
    module = _load_script(
        "scripts/export/export_paper_only_sim_benchmark_table.py",
        "benchmark_table_exporter_under_test",
    )

    args = module.parse_args([])
    resolved = module.resolve_export_inputs(args)

    assert args.manifest == MANIFEST_PATH
    assert resolved.benchmark_input == STAGE3_BENCHMARK
    assert resolved.statistics_report_input == STAGE3_STATISTICS
    assert resolved.provenance_label == "canonical_main_benchmark"
    assert args.benchmark_input is None
    assert "schema2" in module.build_parser().format_help()


def test_benchmark_table_exporter_marks_explicit_override() -> None:
    module = _load_script(
        "scripts/export/export_paper_only_sim_benchmark_table.py",
        "benchmark_table_exporter_override_under_test",
    )

    args = module.parse_args(["--benchmark-input", str(SCHEMA2_DIAGNOSTIC)])
    resolved = module.resolve_export_inputs(args)

    assert resolved.benchmark_input == SCHEMA2_DIAGNOSTIC
    assert resolved.provenance_label == "override_benchmark_input"
    assert resolved.statistics_report_input is None


def test_benchmark_table_override_does_not_load_manifest(tmp_path: Path) -> None:
    module = _load_script(
        "scripts/export/export_paper_only_sim_benchmark_table.py",
        "benchmark_table_exporter_override_manifest_under_test",
    )
    missing_manifest = tmp_path / "missing_manifest.json"

    args = module.parse_args(
        ["--manifest", str(missing_manifest), "--benchmark-input", str(SCHEMA2_DIAGNOSTIC)]
    )
    resolved = module.resolve_export_inputs(args)

    assert resolved.benchmark_input == SCHEMA2_DIAGNOSTIC
    assert resolved.provenance_label == "override_benchmark_input"


def test_figure2_exporter_defaults_to_manifest_sources() -> None:
    module = _load_script(
        "scripts/export/export_paper_only_sim_figure2.py",
        "figure2_exporter_under_test",
    )

    args = module.parse_args([])
    resolved = module.resolve_export_inputs(args)

    assert args.manifest == MANIFEST_PATH
    assert resolved.benchmark_input == STAGE3_BENCHMARK
    assert resolved.statistics_report_input == STAGE3_STATISTICS
    assert resolved.provenance_label == "canonical_main_benchmark"
    assert args.benchmark_input is None


def test_figure2_override_does_not_load_manifest(tmp_path: Path) -> None:
    module = _load_script(
        "scripts/export/export_paper_only_sim_figure2.py",
        "figure2_exporter_override_manifest_under_test",
    )
    missing_manifest = tmp_path / "missing_manifest.json"

    args = module.parse_args(
        ["--manifest", str(missing_manifest), "--benchmark-input", str(SCHEMA2_DIAGNOSTIC)]
    )
    resolved = module.resolve_export_inputs(args)

    assert resolved.benchmark_input == SCHEMA2_DIAGNOSTIC
    assert resolved.provenance_label == "override_benchmark_input"


def test_table_exporter_rejects_manifest_with_bad_artifact_sha(tmp_path: Path) -> None:
    module = _load_script(
        "scripts/export/export_paper_only_sim_benchmark_table.py",
        "benchmark_table_exporter_bad_sha_under_test",
    )
    manifest = json.loads((REPO_ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
    manifest["artifacts"]["canonical_main_benchmark"]["sha256"] = "0" * 64
    manifest_path = tmp_path / "bad_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    args = module.parse_args(["--manifest", str(manifest_path)])

    with pytest.raises(ValueError, match="sha256 does not match"):
        module.resolve_export_inputs(args)


def test_figure2_exporter_rejects_manifest_with_bad_artifact_sha(tmp_path: Path) -> None:
    module = _load_script(
        "scripts/export/export_paper_only_sim_figure2.py",
        "figure2_exporter_bad_sha_under_test",
    )
    manifest = json.loads((REPO_ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
    manifest["artifacts"]["canonical_main_benchmark"]["sha256"] = "0" * 64
    manifest_path = tmp_path / "bad_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    args = module.parse_args(["--manifest", str(manifest_path)])

    with pytest.raises(ValueError, match="sha256 does not match"):
        module.resolve_export_inputs(args)


def test_exporters_support_check_mode_without_rewriting_outputs() -> None:
    table_module = _load_script(
        "scripts/export/export_paper_only_sim_benchmark_table.py",
        "benchmark_table_exporter_check_under_test",
    )
    figure_module = _load_script(
        "scripts/export/export_paper_only_sim_figure2.py",
        "figure2_exporter_check_under_test",
    )

    assert table_module.parse_args(["--check"]).check is True
    assert figure_module.parse_args(["--check"]).check is True
    assert hasattr(table_module, "run_check")
    assert hasattr(figure_module, "run_check")
