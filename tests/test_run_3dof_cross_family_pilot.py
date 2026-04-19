import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def _load_runner_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "experiments"
        / "run_3dof_cross_family_pilot.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_3dof_cross_family_pilot_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_cross_family_pilot_runner_writes_method_budget_grid(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    calls = []

    def _fake_run_method(**kwargs):
        calls.append(kwargs)
        return {
            "method_name": kwargs["method_name"],
            "algorithm": kwargs["algorithm"],
            "factor_value": kwargs["total_timesteps"],
            "train_config_snapshot": {},
            "train_configs": [],
            "training_summaries": [],
            "per_profile_metrics": {},
            "five_profile_mean": {"success_rate_mean_over_profiles": 0.0},
        }

    monkeypatch.setattr(
        module,
        "run_3dof_cross_family_method_across_profiles",
        _fake_run_method,
    )
    output_path = tmp_path / "cross_family_pilot.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_3dof_cross_family_pilot.py",
            "--seeds",
            "0",
            "1",
            "2",
            "--episodes",
            "1",
            "--budgets",
            "64",
            "128",
            "--train-profile",
            "high_friction",
            "--profiles",
            "nominal",
            "--output",
            str(output_path),
        ],
    )

    module.main()
    written = json.loads(output_path.read_text(encoding="utf-8"))

    assert written["experiment_name"] == "three_dof_cross_family_pilot"
    assert written["config"]["budget_points"] == [64, 128]
    assert written["config"]["seed_list"] == [0, 1, 2]
    assert written["config"]["train_profile"] == "high_friction"
    assert written["config"]["profiles"] == ["nominal"]
    assert written["config"]["method_names"] == ["ppo_no_bc", "sac_no_bc", "td3_no_bc"]
    assert [
        (method["method_name"], point["factor_value"])
        for method in written["methods"]
        for point in method["points"]
    ] == [
        ("ppo_no_bc", 64),
        ("ppo_no_bc", 128),
        ("sac_no_bc", 64),
        ("sac_no_bc", 128),
        ("td3_no_bc", 64),
        ("td3_no_bc", 128),
    ]
    assert len(calls) == 6
    assert calls[0]["method_name"] == "ppo_no_bc"
    assert calls[0]["algorithm"] == "ppo"
    assert calls[0]["train_uncertainty_profile"] == "high_friction"
    assert calls[0]["uncertainty_profiles"] == ["nominal"]
    assert "train_overrides" not in calls[0]


def test_cross_family_pilot_runner_help_works_from_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "experiments" / "run_3dof_cross_family_pilot.py"

    completed = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "cross-family pure-RL pilot" in completed.stdout
