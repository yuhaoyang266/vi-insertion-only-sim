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


def test_statistics_report_entrypoint_runs_from_repo_root(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "experiments" / "run_3dof_statistics_report.py"
    benchmark_path = (
        repo_root
        / "artifacts"
        / "main_benchmark"
        / "three_dof_benchmark_schema2_paper_teacher_20260418_034230.json"
    )
    output_dir = tmp_path / "statistics_report_cli"
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--input",
            str(benchmark_path),
            "--output-dir",
            str(output_dir),
            "--stem",
            "cli_probe",
        ],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert (output_dir / "cli_probe.json").is_file()
    assert (output_dir / "cli_probe.md").is_file()
