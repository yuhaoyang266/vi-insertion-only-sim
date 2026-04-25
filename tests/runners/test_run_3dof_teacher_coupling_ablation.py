from __future__ import annotations

import json
import subprocess
import sys


def test_teacher_coupling_runner_help() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/experiments/run_3dof_teacher_coupling_ablation.py",
            "--help",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "teacher-coupling crossed ablation" in completed.stdout
    assert "--smoke-only" in completed.stdout
    assert "--total-timesteps" in completed.stdout
    assert "--output" in completed.stdout


def test_teacher_coupling_runner_smoke_only_writes_metadata(tmp_path) -> None:
    output_path = tmp_path / "teacher_coupling_smoke.json"

    subprocess.run(
        [
            sys.executable,
            "scripts/experiments/run_3dof_teacher_coupling_ablation.py",
            "--smoke-only",
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["config"]["smoke_only"] is True
    assert payload["summary"]["condition_count"] == 4
    assert payload["summary"]["conditions"][0]["seed_count"] == 3
