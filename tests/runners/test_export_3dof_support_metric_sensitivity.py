from __future__ import annotations

import subprocess
import sys


def test_support_metric_sensitivity_runner_help() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/experiments/export_3dof_support_metric_sensitivity.py",
            "--help",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "SCI sensitivity audit" in completed.stdout
    assert "--input-artifacts" in completed.stdout
    assert "--output-stem" in completed.stdout
    assert "--smoke-only" in completed.stdout
