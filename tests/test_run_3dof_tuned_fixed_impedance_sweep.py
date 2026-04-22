import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


def _load_runner_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_3dof_tuned_fixed_impedance_sweep.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_3dof_tuned_fixed_impedance_sweep_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_tuned_fixed_runner_writes_search_and_confirm_blocks(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    calls = []

    def _fake_run_condition(**kwargs):
        calls.append(kwargs)
        overrides = kwargs["train_overrides"]["base_env_overrides"]
        return {
            "condition_name": kwargs["condition_name"],
            "factor_value": kwargs["total_timesteps"],
            "k_xy": overrides["min_k_xy"],
            "k_z": overrides["min_k_z"],
            "train_configs": [],
            "training_summaries": [],
            "per_profile_metrics": {
                "nominal": {"aggregate": {"success_rate_mean": 1.0}},
            },
            "five_profile_mean": {
                "success_rate_mean_over_profiles": 1.0,
                "mean_peak_contact_force_mean_over_profiles": 1.0,
                "mean_final_distance_mean_over_profiles": 0.9,
            },
        }

    monkeypatch.setattr(module, "run_3dof_condition_across_profiles", _fake_run_condition)
    output_path = tmp_path / "fixed_sweep.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_3dof_tuned_fixed_impedance_sweep.py",
            "--search-seeds",
            "0",
            "--confirm-seeds",
            "0",
            "--search-episodes",
            "1",
            "--confirm-episodes",
            "1",
            "--k-xy-values",
            "65",
            "--k-z-values",
            "87.5",
            "--profiles",
            "nominal",
            "--output",
            str(output_path),
        ],
    )

    module.main()
    written = json.loads(output_path.read_text(encoding="utf-8"))

    assert written["experiment_name"] == "three_dof_tuned_fixed_impedance_sweep"
    assert written["grid"]["k_xy_values"] == [65.0]
    assert written["grid"]["k_z_values"] == [87.5]
    assert written["selected_configs"][0]["k_xy"] == 65.0
    assert len(written["search_results"]) == 1
    assert len(written["confirm_results"]) == 1
    assert len(calls) == 2


def test_tuned_fixed_runner_help_works_from_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_3dof_tuned_fixed_impedance_sweep.py"
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
    assert "tuned fixed-impedance sweep" in completed.stdout
