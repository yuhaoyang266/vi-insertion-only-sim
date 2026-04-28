import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys


def _load_runner_module():
    module_path = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "run_3dof_pose_perturbation_study.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_3dof_pose_perturbation_study_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_pose_perturbation_runner_exports_profile_metadata(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()

    monkeypatch.setattr(module, "run_3dof_handcrafted_uncertainty_suite", lambda **_: {})

    def _fake_run_registry_suite(**kwargs):
        return {
            "suite_name": kwargs["suite_name"],
            "factor_value": 128,
            "training_budget": {"total_timesteps": 128},
            "train_config_snapshot": {"suite_name": kwargs["suite_name"]},
            "per_profile_metrics": {
                profile_name: {
                    "aggregate": {"success_rate_mean": 1.0, "jam_rate_mean": 0.0},
                }
                for profile_name in kwargs["uncertainty_profiles"]
            },
        }

    monkeypatch.setattr(
        module,
        "_run_3dof_registry_suite_across_profiles",
        _fake_run_registry_suite,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_3dof_pose_perturbation_study.py",
            "--output",
            str(tmp_path / "pose_study.json"),
        ],
    )

    module.main()
    payload = json.loads((tmp_path / "pose_study.json").read_text(encoding="utf-8"))

    assert payload["config"]["profile_family"] == "pose_perturbation"
    assert payload["config"]["perturbation_profiles"] == [
        "pose_perturb_mild",
        "pose_perturb_moderate",
        "pose_perturb_severe",
    ]
    assert [item["profile_name"] for item in payload["profile_definitions"]] == [
        "pose_perturb_mild",
        "pose_perturb_moderate",
        "pose_perturb_severe",
    ]
    assert payload["profile_definitions"][1]["pose_target_bias_xy_m"] > 0.0
    assert payload["profile_definitions"][1]["orientation_perturbation_deg"] > 0.0
    assert payload["config"]["suite_names"] == [
        "ppo_no_bc",
        "bc_only_stable_r32_p32",
        "fixed_impedance_rl_stable_r32_p32",
        "repaired_mainline_bc_to_ppo",
        "dapg_lite_repaired_mainline",
    ]


def test_pose_perturbation_runner_help_works_from_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "run_3dof_pose_perturbation_study.py"
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
    assert "pose-perturbation external-validity study" in completed.stdout
