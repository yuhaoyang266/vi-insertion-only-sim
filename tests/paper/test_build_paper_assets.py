from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_script(relative_path: str, module_name: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_paper_assets_default_commands_use_manifest_and_confirm_report() -> None:
    module = _load_script(
        "scripts/export/build_paper_assets.py",
        "build_paper_assets_under_test",
    )

    args = module.parse_args([])
    commands = module.build_commands(args)

    assert args.manifest == Path("artifacts/main_benchmark/main_benchmark_manifest.json")
    assert commands == [
        [
            sys.executable,
            "scripts/export/export_paper_only_sim_benchmark_table.py",
            "--manifest",
            "artifacts/main_benchmark/main_benchmark_manifest.json",
        ],
        [
            sys.executable,
            "scripts/export/export_paper_only_sim_figure2.py",
            "--manifest",
            "artifacts/main_benchmark/main_benchmark_manifest.json",
        ],
        [
            sys.executable,
            "scripts/experiments/export_3dof_evidence_matrix.py",
            "--confirm-report",
            "outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json",
            "--manifest",
            "artifacts/main_benchmark/main_benchmark_manifest.json",
            "--output-dir",
            "outputs/evidence_matrix",
        ],
    ]


def test_build_paper_assets_check_mode_passes_check_to_checkable_exporters() -> None:
    module = _load_script(
        "scripts/export/build_paper_assets.py",
        "build_paper_assets_check_under_test",
    )

    args = module.parse_args(["--check"])
    commands = module.build_commands(args)

    assert "--check" in commands[0]
    assert "--check" in commands[1]
    assert len(commands) == 2


def test_build_paper_assets_runs_commands_in_order(monkeypatch) -> None:
    module = _load_script(
        "scripts/export/build_paper_assets.py",
        "build_paper_assets_run_under_test",
    )
    calls: list[list[str]] = []

    def fake_run(command, *, cwd, check):
        calls.append(list(command))

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module, "run_evidence_check", lambda args: None)

    args = module.parse_args(["--check"])
    module.main(args)

    assert calls == module.build_commands(args)


def test_build_paper_assets_check_compares_evidence_outputs(monkeypatch, tmp_path: Path) -> None:
    module = _load_script(
        "scripts/export/build_paper_assets.py",
        "build_paper_assets_evidence_check_under_test",
    )
    expected_dir = tmp_path / "expected"
    generated_dir = tmp_path / "generated"
    expected_dir.mkdir()
    generated_dir.mkdir()
    for filename in module.EVIDENCE_OUTPUT_FILENAMES:
        (expected_dir / filename).write_bytes(b"same")
        (generated_dir / filename).write_bytes(b"same")
    sprint2_json = '{"source_artifacts": {"evidence_matrix": "same"}}'
    (expected_dir / "three_dof_sprint2_main_table.json").write_text(
        sprint2_json,
        encoding="utf-8",
    )
    (generated_dir / "three_dof_sprint2_main_table.json").write_text(
        sprint2_json,
        encoding="utf-8",
    )
    sprint2_markdown = "Evidence-matrix source: `same`\n"
    (expected_dir / "three_dof_sprint2_main_table.md").write_text(
        sprint2_markdown,
        encoding="utf-8",
    )
    (generated_dir / "three_dof_sprint2_main_table.md").write_text(
        sprint2_markdown,
        encoding="utf-8",
    )

    calls: list[list[str]] = []

    def fake_run(command, *, cwd, check):
        calls.append(list(command))

    class FakeTemporaryDirectory:
        def __enter__(self):
            return str(generated_dir)

        def __exit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module.tempfile, "TemporaryDirectory", FakeTemporaryDirectory)

    args = module.parse_args(["--check", "--evidence-output-dir", str(expected_dir)])
    module.run_evidence_check(args)

    assert calls == [module.build_evidence_command(args, output_dir=generated_dir)]


def test_build_paper_assets_check_resolves_relative_evidence_outputs_from_repo_root(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_script(
        "scripts/export/build_paper_assets.py",
        "build_paper_assets_repo_relative_evidence_under_test",
    )
    repo_root = tmp_path / "repo"
    expected_dir = repo_root / "outputs" / "evidence_matrix"
    generated_dir = tmp_path / "generated"
    outside_cwd = tmp_path / "outside"
    expected_dir.mkdir(parents=True)
    generated_dir.mkdir()
    outside_cwd.mkdir()
    for filename in module.EVIDENCE_OUTPUT_FILENAMES:
        (expected_dir / filename).write_bytes(b"same")
        (generated_dir / filename).write_bytes(b"same")
    sprint2_json = '{"source_artifacts": {"evidence_matrix": "same"}}'
    (expected_dir / "three_dof_sprint2_main_table.json").write_text(
        sprint2_json,
        encoding="utf-8",
    )
    (generated_dir / "three_dof_sprint2_main_table.json").write_text(
        sprint2_json,
        encoding="utf-8",
    )
    sprint2_markdown = "Evidence-matrix source: `same`\n"
    (expected_dir / "three_dof_sprint2_main_table.md").write_text(
        sprint2_markdown,
        encoding="utf-8",
    )
    (generated_dir / "three_dof_sprint2_main_table.md").write_text(
        sprint2_markdown,
        encoding="utf-8",
    )

    def fake_run(command, *, cwd, check):
        assert cwd == repo_root

    class FakeTemporaryDirectory:
        def __enter__(self):
            return str(generated_dir)

        def __exit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr(module, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module.tempfile, "TemporaryDirectory", FakeTemporaryDirectory)
    monkeypatch.chdir(outside_cwd)

    module.run_evidence_check(module.parse_args(["--check"]))
