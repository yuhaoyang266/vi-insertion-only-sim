import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "script_name",
    [
        "run_3dof_bc_seed_factorization.py",
        "run_3dof_factor_sweeps.py",
        "run_3dof_pose_perturbation_study.py",
        "run_3dof_statistics_report.py",
        "run_3dof_uncertainty_benchmark.py",
    ],
)
def test_experiment_entrypoint_help_works_from_repo_root(script_name: str) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "experiments" / script_name
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "usage:" in completed.stdout
