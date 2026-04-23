import importlib.util
from pathlib import Path
import subprocess
import sys


def _load_runner_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "export"
        / "build_submission_bundle.py"
    )
    spec = importlib.util.spec_from_file_location(
        "build_submission_bundle_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_runner_uses_default_submission_bundle_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    calls: dict[str, object] = {}

    def _fake_build_submission_bundle(
        *,
        source_root,
        output_dir,
        venue,
        paper_pdf,
        create_archives,
    ):
        output_dir.mkdir(parents=True, exist_ok=True)
        anonymous_snapshot_dir = output_dir / "anonymous_snapshot"
        editor_materials_dir = output_dir / "editor_materials"
        anonymous_snapshot_dir.mkdir()
        editor_materials_dir.mkdir()
        manifest_path = output_dir / "submission_bundle_manifest.json"
        summary_path = output_dir / "submission_bundle_summary.md"
        manifest_path.write_text("{}", encoding="utf-8")
        summary_path.write_text("# Summary\n", encoding="utf-8")
        calls["source_root"] = source_root
        calls["output_dir"] = output_dir
        calls["venue"] = venue
        calls["paper_pdf"] = paper_pdf
        calls["create_archives"] = create_archives
        return {
            "anonymous_snapshot_dir": anonymous_snapshot_dir,
            "editor_materials_dir": editor_materials_dir,
            "manifest_path": manifest_path,
            "summary_path": summary_path,
            "paper_pdf_path": None,
            "anonymous_snapshot_zip": None,
            "editor_materials_zip": None,
        }

    monkeypatch.setattr(module, "build_submission_bundle", _fake_build_submission_bundle)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_submission_bundle.py",
            "--output-dir",
            str(tmp_path / "submission_bundle"),
        ],
    )

    module.main()

    assert calls["source_root"] == module.REPO_ROOT
    assert calls["venue"] == "journal-double-blind"
    assert calls["paper_pdf"] is None
    assert calls["create_archives"] is True
    assert (
        tmp_path / "submission_bundle" / "submission_bundle_manifest.json"
    ).is_file()


def test_submission_bundle_cli_avoids_unrelated_gym_warning(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        "scripts/export/build_submission_bundle.py",
        "--output-dir",
        str(tmp_path / "submission_bundle"),
        "--skip-archives",
    ]

    completed = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    combined_output = completed.stdout + completed.stderr
    assert completed.returncode == 0, combined_output
    assert "Gym has been unmaintained since 2022" not in combined_output
