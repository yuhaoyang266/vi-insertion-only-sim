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
        "export_sprint4_clearance_shift.py",
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


@pytest.mark.parametrize(
    "script_name",
    [
        "export_paper_only_sim_high_friction_trace_figure.py",
        "export_paper_only_sim_figure3.py",
        "build_submission_bundle.py",
    ],
)
def test_trace_export_entrypoint_help_works_from_repo_root(script_name: str) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "export" / script_name
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


def test_paper_table_entrypoint_runs_from_repo_root_with_matching_statistics_report(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    benchmark_path = (
        repo_root
        / "artifacts"
        / "main_benchmark"
        / "three_dof_benchmark_schema2_paper_teacher_20260418_034230.json"
    )
    stats_script_path = repo_root / "scripts" / "experiments" / "run_3dof_statistics_report.py"
    table_script_path = repo_root / "scripts" / "export" / "export_paper_only_sim_benchmark_table.py"
    stats_output_dir = tmp_path / "statistics_report"
    table_output_dir = tmp_path / "paper_table"
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)

    stats_completed = subprocess.run(
        [
            sys.executable,
            str(stats_script_path),
            "--input",
            str(benchmark_path),
            "--output-dir",
            str(stats_output_dir),
            "--stem",
            "cli_probe_stats",
        ],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert stats_completed.returncode == 0, stats_completed.stderr
    statistics_report_path = stats_output_dir / "cli_probe_stats.json"
    assert statistics_report_path.is_file()

    table_completed = subprocess.run(
        [
            sys.executable,
            str(table_script_path),
            "--benchmark-input",
            str(benchmark_path),
            "--statistics-report-input",
            str(statistics_report_path),
            "--output-dir",
            str(table_output_dir),
            "--stem",
            "table_cli_probe",
        ],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert table_completed.returncode == 0, table_completed.stderr
    assert (table_output_dir / "table_cli_probe.json").is_file()
    assert (table_output_dir / "table_cli_probe.md").is_file()


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
