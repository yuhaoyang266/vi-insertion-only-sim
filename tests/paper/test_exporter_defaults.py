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


def _write_valid_png(
    path: Path,
    *,
    width: int = 640,
    height: int = 480,
    marker: bytes = b"",
) -> None:
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\r"
        + b"IHDR"
        + width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + marker
    )


def _write_valid_pdf(path: Path, *, marker: bytes = b"") -> None:
    path.write_bytes(b"%PDF-1.4\n" + marker + b"\n%%EOF\n")


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


def test_figure2_check_accepts_platform_specific_figure_bytes(tmp_path: Path) -> None:
    module = _load_script(
        "scripts/export/export_paper_only_sim_figure2.py",
        "figure2_exporter_binary_check_under_test",
    )
    expected_png = tmp_path / "fig2_main_benchmark_evaluation_class_summary.png"
    generated_png = tmp_path / "generated.png"
    expected_pdf = tmp_path / "fig2_main_benchmark_evaluation_class_summary.pdf"
    generated_pdf = tmp_path / "generated.pdf"

    _write_valid_png(expected_png, width=640, height=480, marker=b"windows")
    _write_valid_png(generated_png, width=800, height=600, marker=b"linux")
    _write_valid_pdf(expected_pdf, marker=b"windows")
    _write_valid_pdf(generated_pdf, marker=b"linux")

    assert module._same_figure_output(expected_png, generated_png)
    assert module._same_figure_output(expected_pdf, generated_pdf)


def test_figure2_check_rejects_invalid_figure_outputs(tmp_path: Path) -> None:
    module = _load_script(
        "scripts/export/export_paper_only_sim_figure2.py",
        "figure2_exporter_invalid_binary_check_under_test",
    )
    expected_png = tmp_path / "fig2_main_benchmark_evaluation_class_summary.png"
    generated_png = tmp_path / "generated.png"
    expected_pdf = tmp_path / "fig2_main_benchmark_evaluation_class_summary.pdf"
    generated_pdf = tmp_path / "generated.pdf"

    _write_valid_png(expected_png)
    generated_png.write_bytes(b"not a png")
    _write_valid_pdf(expected_pdf)
    generated_pdf.write_bytes(b"not a pdf")

    assert not module._same_figure_output(expected_png, generated_png)
    assert not module._same_figure_output(expected_pdf, generated_pdf)
