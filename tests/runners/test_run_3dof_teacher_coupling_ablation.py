from __future__ import annotations

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
    assert "--total-timesteps" in completed.stdout
    assert "--output" in completed.stdout
