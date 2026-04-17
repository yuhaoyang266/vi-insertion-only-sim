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
        / "run_3dof_ppo_large_budget_ablation.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_3dof_ppo_large_budget_ablation_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_ppo_large_budget_runner_writes_condition_budget_grid(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    calls = []

    def _fake_run_condition(**kwargs):
        calls.append(kwargs)
        return {
            "condition_name": kwargs["condition_name"],
            "factor_value": kwargs["total_timesteps"],
            "train_configs": [],
            "training_summaries": [],
            "per_profile_metrics": {},
            "five_profile_mean": {"success_rate_mean_over_profiles": 0.0},
        }

    monkeypatch.setattr(module, "run_3dof_condition_across_profiles", _fake_run_condition)
    output_path = tmp_path / "ppo_ablation.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_3dof_ppo_large_budget_ablation.py",
            "--seeds",
            "0",
            "--episodes",
            "1",
            "--budgets",
            "64",
            "--profiles",
            "nominal",
            "--output",
            str(output_path),
        ],
    )

    module.main()
    written = json.loads(output_path.read_text(encoding="utf-8"))

    assert written["experiment_name"] == "three_dof_ppo_large_budget_ablation"
    assert written["config"]["budget_points"] == [64]
    assert [condition["condition_name"] for condition in written["conditions"]] == [
        "ppo_only_paper_matched",
        "ppo_only_reviewer_fair",
    ]
    assert len(calls) == 2
    assert calls[0]["total_timesteps"] == 64
    assert calls[0]["uncertainty_profiles"] == ["nominal"]


def test_ppo_large_budget_runner_help_works_from_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = (
        repo_root / "scripts" / "experiments" / "run_3dof_ppo_large_budget_ablation.py"
    )

    completed = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "PPO-only large-budget ablations" in completed.stdout
