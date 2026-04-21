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


@pytest.mark.parametrize(
    ("script_name", "extra_args", "expected_outputs"),
    [
        (
            "export_paper_only_sim_figure1.py",
            [],
            ("fig1_cli_probe.pdf", "fig1_cli_probe.png"),
        ),
        (
            "export_paper_only_sim_figure2.py",
            [],
            ("fig2_cli_probe.pdf", "fig2_cli_probe.png"),
        ),
        (
            "export_paper_only_sim_figureA1.py",
            [],
            ("figA1_cli_probe.pdf", "figA1_cli_probe.png"),
        ),
        (
            "export_paper_only_sim_figureA2.py",
            [],
            ("figA2_cli_probe.pdf", "figA2_cli_probe.png"),
        ),
        (
            "export_paper_only_sim_benchmark_table.py",
            [
                "--benchmark-input",
                "artifacts/main_benchmark/three_dof_benchmark_schema2_paper_teacher_20260418_034230.json",
                "--statistics-report-input",
                "artifacts/main_benchmark/three_dof_statistics_report_stage3_20260412.json",
            ],
            ("table_cli_probe.json", "table_cli_probe.md"),
        ),
    ],
)
def test_paper_export_entrypoints_run_from_repo_root(
    tmp_path: Path,
    script_name: str,
    extra_args: list[str],
    expected_outputs: tuple[str, str],
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "export" / script_name
    output_dir = tmp_path / script_name.replace(".py", "")
    stem = expected_outputs[0].rsplit(".", 1)[0]
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            *extra_args,
            "--output-dir",
            str(output_dir),
            "--stem",
            stem,
        ],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    for output_name in expected_outputs:
        assert (output_dir / output_name).is_file()


@pytest.mark.parametrize(
    ("script_name", "expected_outputs"),
    [
        (
            "export_paper_only_sim_appendix_table.py",
            ("appendix_cli_probe.json", "appendix_cli_probe.md"),
        ),
        (
            "export_paper_only_sim_figureA3.py",
            ("figA3_cli_probe.pdf", "figA3_cli_probe.png"),
        ),
        (
            "export_paper_only_sim_figureA4.py",
            ("figA4_cli_probe.pdf", "figA4_cli_probe.png"),
        ),
    ],
)
def test_appendix_export_entrypoints_run_from_repo_root(
    tmp_path: Path,
    script_name: str,
    expected_outputs: tuple[str, str],
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "export" / script_name
    output_dir = tmp_path / script_name.replace(".py", "")
    benchmark_path = (
        repo_root
        / "artifacts"
        / "main_benchmark"
        / "three_dof_benchmark_schema2_paper_teacher_20260418_034230.json"
    )
    stem = expected_outputs[0].rsplit(".", 1)[0]
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--benchmark-input",
            str(benchmark_path),
            "--output-dir",
            str(output_dir),
            "--stem",
            stem,
        ],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    for output_name in expected_outputs:
        assert (output_dir / output_name).is_file()
