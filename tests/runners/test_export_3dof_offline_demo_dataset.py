from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner_module():
    module_path = (
        REPO_ROOT
        / "scripts"
        / "experiments"
        / "export_3dof_offline_demo_dataset.py"
    )
    spec = importlib.util.spec_from_file_location(
        "export_3dof_offline_demo_dataset_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_offline_demo_dataset_runner_writes_artifact(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    output_path = tmp_path / "offline_demo_dataset.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "export_3dof_offline_demo_dataset.py",
            "--profiles",
            "nominal",
            "--seeds",
            "0",
            "--episodes-per-seed",
            "1",
            "--source-policy",
            "variable_impedance",
            "--output",
            str(output_path),
        ],
    )

    module.main()
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["artifact_type"] == "three_dof_offline_demo_dataset"
    assert payload["metadata"]["profiles"] == ["nominal"]
    assert payload["metadata"]["episodes_per_seed"] == 1
    assert payload["metadata"]["generation_command"].startswith("python")
    assert payload["metadata"]["dataset_payload_sha256"]


def test_offline_demo_dataset_runner_help_works_from_repo_root() -> None:
    script_path = (
        REPO_ROOT
        / "scripts"
        / "experiments"
        / "export_3dof_offline_demo_dataset.py"
    )

    completed = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Export a contract-shaped 3DoF offline demonstration dataset" in completed.stdout
