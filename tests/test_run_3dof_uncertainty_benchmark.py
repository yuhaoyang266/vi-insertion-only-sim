import importlib.util
import json
from pathlib import Path
import sys

from vi_full.three_dof_config import ThreeDoFResetConfig, ThreeDoFResetStage
from vi_full.three_dof_benchmark import build_3dof_dapg_baseline_registry


def _load_runner_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "run_3dof_uncertainty_benchmark.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_3dof_uncertainty_benchmark_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_3dof_dapg_baseline_registry_exposes_explicit_stable_bc_suite() -> None:
    registry = build_3dof_dapg_baseline_registry()

    assert registry["bc_only_stable_r32_p32"] == {
        "total_timesteps": 0,
        "bc_rollout_episodes": 32,
        "bc_pretrain_steps": 32,
        "bc_batch_size": 64,
    }
    assert registry["fixed_impedance_rl_stable_r32_p32"] == {
        "bc_rollout_episodes": 32,
        "bc_pretrain_steps": 32,
        "bc_batch_size": 64,
        "base_env_overrides": {
            "min_k_xy": 65.0,
            "max_k_xy": 65.0,
            "min_k_z": 87.5,
            "max_k_z": 87.5,
        },
    }


def test_runner_paper_facing_nine_suite_uses_stable_bc_suite(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    called_suite_names: list[str] = []

    monkeypatch.setattr(module, "run_3dof_handcrafted_uncertainty_suite", lambda **_: {})

    def _fake_run_3dof_suite_across_profiles(suite_run_kwargs):
        called_suite_names.append(suite_run_kwargs["suite_name"])
        return {
            "suite_run_kwargs": {
                "suite_name": suite_run_kwargs["suite_name"],
                "total_timesteps": suite_run_kwargs["total_timesteps"],
            },
            "train_configs": [],
            "training_summaries": [],
            "eval_results": {},
            "five_profile_mean": {
                "success_rate_mean_over_profiles": 1.0,
                "success_rate_std_over_profiles": 0.0,
                "mean_episode_return_mean_over_profiles": 0.0,
                "mean_episode_return_std_over_profiles": 0.0,
                "mean_final_distance_mean_over_profiles": 0.001,
                "mean_final_distance_std_over_profiles": 0.0,
                "mean_episode_length_mean_over_profiles": 0.0,
                "mean_episode_length_std_over_profiles": 0.0,
                "mean_peak_contact_force_mean_over_profiles": 1.0,
                "mean_peak_contact_force_std_over_profiles": 0.0,
                "p95_peak_contact_force_mean_over_profiles": 1.2,
                "p95_peak_contact_force_std_over_profiles": 0.0,
                "mean_force_std_mean_over_profiles": 0.0,
                "mean_force_std_std_over_profiles": 0.0,
                "mean_first_contact_step_mean_over_profiles": 0.0,
                "mean_first_contact_step_std_over_profiles": 0.0,
                "mean_contact_steps_mean_over_profiles": 30.0,
                "mean_contact_steps_std_over_profiles": 0.0,
                "mean_settling_steps_after_contact_mean_over_profiles": 0.0,
                "mean_settling_steps_after_contact_std_over_profiles": 0.0,
                "jam_rate_mean_over_profiles": 0.0,
                "jam_rate_std_over_profiles": 0.0,
            },
        }

    monkeypatch.setattr(module, "_run_3dof_suite_across_profiles", _fake_run_3dof_suite_across_profiles)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_3dof_uncertainty_benchmark.py",
            "--include-paper-learned-block",
            "--include-dapg-mechanism-block",
            "--output",
            str(tmp_path / "benchmark.json"),
        ],
    )

    module.main()
    output_path = tmp_path / "benchmark.json"
    written = json.loads(output_path.read_text(encoding="utf-8"))

    assert called_suite_names == [
        "ppo_no_bc",
        "bc_only_stable_r32_p32",
        "fixed_impedance_rl_stable_r32_p32",
        "repaired_mainline_bc_to_ppo",
        "dapg_lite_repaired_mainline",
        "dapg_lite_contact_old__reset_coverage_collapse",
        "dapg_lite_contact_old__reset_repaired",
        "dapg_lite_contact_new__reset_coverage_collapse",
        "dapg_lite_contact_new__reset_repaired",
    ]
    assert written["config"]["seeds"] == [0, 1, 2, 3, 4]
    assert written["config"]["episodes_per_seed"] == 100
    assert written["config"]["suite_names"] == called_suite_names
    assert written["config"]["handcrafted_policy_names"] == [
        "pose_only",
        "fixed_impedance",
        "variable_impedance",
        "hybrid_position_force",
        "compliant_search",
        "tuned_impedance",
    ]
    assert set(written) == {"config", "handcrafted_results", "learned_results"}


def test_write_report_serializes_reset_config_checkpoint_metadata(tmp_path: Path) -> None:
    module = _load_runner_module()
    output_path = tmp_path / "benchmark.json"

    report = {
        "config": {"suite_names": ["dapg_suite"]},
        "handcrafted_results": {},
        "learned_results": {
            "dapg_suite": {
                "suite_run_kwargs": {
                    "contact_bc_reset_config": ThreeDoFResetConfig(
                        curriculum_stages=(
                            ThreeDoFResetStage(
                                start_xy_noise_m=0.0025,
                                start_depth_fraction_range=(0.1, 0.4),
                                weight=1.0,
                            ),
                        )
                    ),
                },
                "train_configs": [],
                "training_summaries": [],
                "eval_results": {},
                "five_profile_mean": {},
            }
        },
    }

    module._write_report(output_path, report)
    written = json.loads(output_path.read_text(encoding="utf-8"))

    assert (
        written["learned_results"]["dapg_suite"]["suite_run_kwargs"][
            "contact_bc_reset_config"
        ]
        == {
            "curriculum_stages": [
                {
                    "start_xy_noise_m": 0.0025,
                    "start_depth_fraction_range": [0.1, 0.4],
                    "weight": 1.0,
                }
            ]
        }
    )
