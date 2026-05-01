from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from vi_full.cross_paper_bridge import CONTRACT_SHA


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner_module():
    module_path = REPO_ROOT / "scripts" / "experiments" / "run_modern_baseline_iql_smoke.py"
    spec = importlib.util.spec_from_file_location(
        "run_modern_baseline_iql_smoke_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_modern_baseline_iql_smoke_runner_writes_artifact(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    output_path = tmp_path / "modern_baseline_iql_smoke.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_modern_baseline_iql_smoke.py",
            "--num-steps",
            "4",
            "--output",
            str(output_path),
        ],
    )

    module.main()
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["algorithm"] == "iql_offline"
    assert payload["status"] == "scaffold_only"
    assert output_path.with_suffix(".md").exists()


def test_modern_baseline_iql_smoke_runner_accepts_dataset_path(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    dataset_path = tmp_path / "offline_dataset.json"
    output_path = tmp_path / "modern_baseline_iql_smoke.json"
    dataset_path.write_text(
        json.dumps(
            [
                {
                    "observations": [[0.0] * 14, [0.1] * 14],
                    "actions": [[0.0] * 5, [0.0] * 5],
                    "rewards": [0.0, 1.0],
                    "episode_id": "dataset_path_smoke_0000",
                    "profile": "nominal",
                    "seed": 0,
                    "success": True,
                    "termination_reason": "synthetic_success",
                    "source_policy": "dataset_path_smoke",
                    "paper_a_commit": "dataset_path_smoke",
                    "contract_sha": CONTRACT_SHA,
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_modern_baseline_iql_smoke.py",
            "--dataset-path",
            str(dataset_path),
            "--output",
            str(output_path),
        ],
    )

    module.main()
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["status"] == "dataset_schema_verified"
    assert payload["dataset_source"] == "external_json_dataset:offline_dataset.json"
    assert str(tmp_path) not in payload["dataset_source"]


def test_modern_baseline_iql_smoke_runner_help_works_from_repo_root() -> None:
    script_path = REPO_ROOT / "scripts" / "experiments" / "run_modern_baseline_iql_smoke.py"

    completed = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Run the modern IQL/CQL baseline smoke scaffold" in completed.stdout
