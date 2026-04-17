import importlib.util
import json
from pathlib import Path
import sys

from vi_full.three_dof_config import ThreeDoFResetConfig, ThreeDoFResetStage
from vi_full.three_dof_benchmark import build_3dof_dapg_baseline_registry
from vi_full.three_dof_policies import resolve_3dof_teacher_spec


def _load_runner_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "experiments"
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


def test_run_suite_across_profiles_closes_vec_normalize(monkeypatch) -> None:
    module = _load_runner_module()
    close_events: list[str] = []

    class _FakeVecNormalize:
        def close(self) -> None:
            close_events.append("closed")

    class _FakeEnv:
        def close(self) -> None:
            return None

    class _FakeArtifacts:
        def __init__(self) -> None:
            self.model = object()
            self.vec_normalize = _FakeVecNormalize()
            self.training_summary = {}

        def make_eval_env(self, **kwargs):
            del kwargs
            return _FakeEnv()

    monkeypatch.setattr(module, "_build_train_config", lambda seed, suite_run_kwargs: object())
    monkeypatch.setattr(module, "train_3dof_ppo_agent", lambda config: _FakeArtifacts())
    monkeypatch.setattr(module, "VecNormalizePredictor", lambda model, vec_normalize: object())
    monkeypatch.setattr(module, "serialize_3dof_train_config", lambda config: {})
    monkeypatch.setattr(
        module,
        "evaluate_3dof_predictor",
        lambda env, predictor, episodes, seed, uncertainty_profile: {
            "policy_name": "ppo",
            "uncertainty_profile": uncertainty_profile,
            "seed": seed,
        },
    )
    monkeypatch.setattr(module, "summarize_3dof_seed_runs", lambda per_seed: {})
    monkeypatch.setattr(module, "_build_five_profile_mean", lambda eval_results: {})

    module._run_3dof_suite_across_profiles(
        {
            "suite_name": "learned_ppo_3dof_bc",
            "seeds": [0],
            "total_timesteps": 128,
            "episodes_per_seed": 1,
            "max_episode_steps": 64,
            "train_uncertainty_profile": "nominal",
            "eval_uncertainty_profile": "nominal",
            "uncertainty_profiles": ["nominal"],
        }
    )

    assert close_events == ["closed"]


def test_build_train_config_preserves_explicit_teacher_spec() -> None:
    module = _load_runner_module()
    explicit_spec = resolve_3dof_teacher_spec(policy_name="teacher_pose_variable")

    config = module._build_train_config(
        0,
        {
            "suite_name": "teacher_pose_variable__repaired_mainline",
            "seeds": [0],
            "total_timesteps": 128,
            "episodes_per_seed": 1,
            "max_episode_steps": 64,
            "train_uncertainty_profile": "nominal",
            "eval_uncertainty_profile": "nominal",
            "uncertainty_profiles": ["nominal"],
            "bc_rollout_episodes": 32,
            "bc_pretrain_steps": 32,
            "bc_batch_size": 64,
            "bc_demo_policy_name": "fixed_impedance",
            "bc_demo_teacher_spec": explicit_spec,
        },
    )

    assert config.bc_demo_policy_name == "fixed_impedance"
    assert config.bc_demo_teacher_spec == explicit_spec


def test_runner_reruns_suite_when_run_signature_mismatches(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    output_path = tmp_path / "benchmark.json"
    suite_name = "learned_ppo_3dof_bc"
    output_path.write_text(
        json.dumps(
            {
                "config": {"suite_names": [suite_name]},
                "handcrafted_results": {},
                "learned_results": {
                    suite_name: {
                        "run_signature": "stale-signature",
                        "suite_run_kwargs": {"suite_name": suite_name},
                        "train_configs": [],
                        "training_summaries": [],
                        "eval_results": {},
                        "five_profile_mean": {
                            "success_rate_mean_over_profiles": 0.0,
                            "jam_rate_mean_over_profiles": 0.0,
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "run_3dof_handcrafted_uncertainty_suite", lambda **_: {})
    calls: list[dict[str, object]] = []

    def _fake_run_3dof_suite_across_profiles(suite_run_kwargs):
        calls.append(dict(suite_run_kwargs))
        return {
            "run_signature": "fresh-signature",
            "suite_run_kwargs": {"suite_name": suite_run_kwargs["suite_name"]},
            "train_configs": [],
            "training_summaries": [],
            "eval_results": {},
            "five_profile_mean": {
                "success_rate_mean_over_profiles": 1.0,
                "jam_rate_mean_over_profiles": 0.0,
            },
        }

    monkeypatch.setattr(module, "_run_3dof_suite_across_profiles", _fake_run_3dof_suite_across_profiles)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_3dof_uncertainty_benchmark.py",
            "--include-learned",
            "--output",
            str(output_path),
        ],
    )

    module.main()
    written = json.loads(output_path.read_text(encoding="utf-8"))

    assert [call["suite_name"] for call in calls] == [suite_name]
    assert written["learned_results"][suite_name]["run_signature"] == "fresh-signature"


def test_artifact_schema_version_changes_run_signature(monkeypatch) -> None:
    module = _load_runner_module()
    suite_run_kwargs = {
        "suite_name": "learned_ppo_3dof_bc",
        "seeds": [0],
        "total_timesteps": 128,
        "episodes_per_seed": 1,
        "max_episode_steps": 64,
        "train_uncertainty_profile": "nominal",
        "eval_uncertainty_profile": "nominal",
        "uncertainty_profiles": ["nominal"],
        "bc_rollout_episodes": 32,
        "bc_pretrain_steps": 32,
        "bc_batch_size": 64,
        "bc_demo_policy_name": "variable_impedance",
    }

    current_signature = module._build_run_signature(suite_run_kwargs)
    monkeypatch.setattr(module, "UNCERTAINTY_BENCHMARK_ARTIFACT_SCHEMA_VERSION", 0)
    previous_signature = module._build_run_signature(suite_run_kwargs)

    assert current_signature != previous_signature


def test_runner_reruns_suite_when_artifact_schema_version_changes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    output_path = tmp_path / "benchmark.json"
    suite_name = "learned_ppo_3dof_bc"
    suite_run_kwargs = {
        "suite_name": suite_name,
        "seeds": [0, 1, 2, 3, 4],
        "total_timesteps": 128,
        "episodes_per_seed": 100,
        "max_episode_steps": 64,
        "train_uncertainty_profile": "nominal",
        "eval_uncertainty_profile": "nominal",
        "uncertainty_profiles": ["nominal", "high_friction"],
        "bc_rollout_episodes": 32,
        "bc_pretrain_steps": 32,
        "bc_batch_size": 64,
        "bc_demo_policy_name": "variable_impedance",
        "approach_bc_rollout_episodes": 0,
        "approach_bc_pretrain_steps": 0,
        "contact_bc_rollout_episodes": 0,
        "contact_bc_pretrain_steps": 0,
        "contact_bc_freeze_pose_head": False,
        "contact_bc_after_finetune": False,
        "contact_finetune_timesteps": 0,
        "contact_finetune_anchor_rollout_episodes": 0,
        "contact_finetune_anchor_bc_steps": 0,
        "contact_finetune_anchor_interval_timesteps": 0,
    }
    monkeypatch.setattr(module, "UNCERTAINTY_BENCHMARK_ARTIFACT_SCHEMA_VERSION", 0)
    old_signature = module._build_run_signature(suite_run_kwargs)
    monkeypatch.setattr(module, "UNCERTAINTY_BENCHMARK_ARTIFACT_SCHEMA_VERSION", 1)
    output_path.write_text(
        json.dumps(
            {
                "config": {"suite_names": [suite_name]},
                "handcrafted_results": {},
                "learned_results": {
                    suite_name: {
                        "run_signature": old_signature,
                        "suite_run_kwargs": {"suite_name": suite_name},
                        "train_configs": [],
                        "training_summaries": [],
                        "eval_results": {},
                        "five_profile_mean": {
                            "success_rate_mean_over_profiles": 0.0,
                            "jam_rate_mean_over_profiles": 0.0,
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "run_3dof_handcrafted_uncertainty_suite", lambda **_: {})
    calls: list[dict[str, object]] = []

    def _fake_run_3dof_suite_across_profiles(run_kwargs):
        calls.append(dict(run_kwargs))
        return {
            "run_signature": "fresh-signature",
            "suite_run_kwargs": {"suite_name": run_kwargs["suite_name"]},
            "train_configs": [],
            "training_summaries": [],
            "eval_results": {},
            "five_profile_mean": {
                "success_rate_mean_over_profiles": 1.0,
                "jam_rate_mean_over_profiles": 0.0,
            },
        }

    monkeypatch.setattr(module, "_run_3dof_suite_across_profiles", _fake_run_3dof_suite_across_profiles)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_3dof_uncertainty_benchmark.py",
            "--include-learned",
            "--profiles",
            "nominal",
            "high_friction",
            "--output",
            str(output_path),
        ],
    )

    module.main()
    written = json.loads(output_path.read_text(encoding="utf-8"))

    assert [call["suite_name"] for call in calls] == [suite_name]
    assert (
        written["config"]["artifact_schema_version"]
        == module.UNCERTAINTY_BENCHMARK_ARTIFACT_SCHEMA_VERSION
    )


def test_runner_teacher_ablation_block_adds_expected_suites(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()
    called_suite_names: list[str] = []
    monkeypatch.setattr(module, "run_3dof_handcrafted_uncertainty_suite", lambda **_: {})

    def _fake_run_3dof_suite_across_profiles(suite_run_kwargs):
        called_suite_names.append(suite_run_kwargs["suite_name"])
        return {
            "run_signature": "teacher-ablation",
            "suite_run_kwargs": dict(suite_run_kwargs),
            "train_configs": [],
            "training_summaries": [],
            "eval_results": {},
            "five_profile_mean": {
                "success_rate_mean_over_profiles": 0.0,
                "jam_rate_mean_over_profiles": 0.0,
            },
        }

    monkeypatch.setattr(module, "_run_3dof_suite_across_profiles", _fake_run_3dof_suite_across_profiles)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_3dof_uncertainty_benchmark.py",
            "--include-teacher-ablation-block",
            "--output",
            str(tmp_path / "teacher_ablation.json"),
        ],
    )

    module.main()

    assert called_suite_names == [
        "teacher_variable_variable__repaired_mainline",
        "teacher_variable_fixed__repaired_mainline",
        "teacher_pose_variable__repaired_mainline",
        "teacher_pose_fixed__repaired_mainline",
    ]


def test_run_signature_changes_when_teacher_spec_changes() -> None:
    module = _load_runner_module()
    base_suite_run_kwargs = {
        "suite_name": "teacher_variable_variable__repaired_mainline",
        "seeds": [0],
        "total_timesteps": 128,
        "episodes_per_seed": 1,
        "max_episode_steps": 64,
        "train_uncertainty_profile": "nominal",
        "eval_uncertainty_profile": "nominal",
        "uncertainty_profiles": ["nominal"],
        "bc_demo_policy_name": "variable_impedance",
    }

    variable_signature = module._build_run_signature(
        {
            **base_suite_run_kwargs,
            "bc_demo_teacher_spec": resolve_3dof_teacher_spec(
                policy_name="variable_impedance"
            ),
        }
    )
    fixed_signature = module._build_run_signature(
        {
            **base_suite_run_kwargs,
            "bc_demo_teacher_spec": resolve_3dof_teacher_spec(
                policy_name="fixed_impedance"
            ),
        }
    )

    assert variable_signature != fixed_signature


def test_run_suite_across_profiles_exposes_teacher_metadata(monkeypatch) -> None:
    module = _load_runner_module()

    class _FakeVecNormalize:
        def close(self) -> None:
            return None

    class _FakeEnv:
        def close(self) -> None:
            return None

    class _FakeArtifacts:
        def __init__(self) -> None:
            self.model = object()
            self.vec_normalize = _FakeVecNormalize()
            self.training_summary = {
                "teacher_preset_name": "teacher_pose_variable",
                "teacher_motion_rule": "pose_feedback",
                "teacher_impedance_rule": "contact_aware_variable_impedance",
            }

        def make_eval_env(self, **kwargs):
            del kwargs
            return _FakeEnv()

    monkeypatch.setattr(module, "_build_train_config", lambda seed, suite_run_kwargs: object())
    monkeypatch.setattr(module, "train_3dof_ppo_agent", lambda config: _FakeArtifacts())
    monkeypatch.setattr(module, "VecNormalizePredictor", lambda model, vec_normalize: object())
    monkeypatch.setattr(module, "serialize_3dof_train_config", lambda config: {})
    monkeypatch.setattr(
        module,
        "evaluate_3dof_predictor",
        lambda env, predictor, episodes, seed, uncertainty_profile: {
            "policy_name": "ppo",
            "uncertainty_profile": uncertainty_profile,
            "seed": seed,
        },
    )
    monkeypatch.setattr(module, "summarize_3dof_seed_runs", lambda per_seed: {})
    monkeypatch.setattr(module, "_build_five_profile_mean", lambda eval_results: {})

    suite_result = module._run_3dof_suite_across_profiles(
        {
            "suite_name": "teacher_pose_variable__repaired_mainline",
            "seeds": [0],
            "total_timesteps": 128,
            "episodes_per_seed": 1,
            "max_episode_steps": 64,
            "train_uncertainty_profile": "nominal",
            "eval_uncertainty_profile": "nominal",
            "uncertainty_profiles": ["nominal"],
            "bc_rollout_episodes": 32,
            "bc_pretrain_steps": 32,
            "bc_batch_size": 64,
            "bc_demo_policy_name": "fixed_impedance",
            "bc_demo_teacher_spec": resolve_3dof_teacher_spec(
                policy_name="teacher_pose_variable"
            ),
        }
    )

    assert suite_result["teacher_preset_name"] == "teacher_pose_variable"
    assert suite_result["teacher_motion_rule"] == "pose_feedback"
    assert (
        suite_result["eval_results"]["nominal"]["aggregate"]["teacher_impedance_rule"]
        == "contact_aware_variable_impedance"
    )


def test_five_profile_mean_includes_termination_diagnostic_rates() -> None:
    module = _load_runner_module()
    aggregate_defaults = {
        f"{metric_name}_mean": 0.0 for metric_name in module.THREE_DOF_NUMERIC_METRICS
    }

    five_profile_mean = module._build_five_profile_mean(
        {
            "nominal": {
                "aggregate": {
                    **aggregate_defaults,
                    "force_threshold_termination_rate_mean": 0.5,
                    "blocked_contact_termination_rate_mean": 0.0,
                    "force_threshold_only_termination_rate_mean": 0.5,
                    "blocked_contact_only_termination_rate_mean": 0.0,
                    "force_and_blocked_termination_rate_mean": 0.0,
                    "documented_force_jam_rate_mean": 0.25,
                }
            },
            "high_friction": {
                "aggregate": {
                    **aggregate_defaults,
                    "force_threshold_termination_rate_mean": 0.0,
                    "blocked_contact_termination_rate_mean": 0.5,
                    "force_threshold_only_termination_rate_mean": 0.0,
                    "blocked_contact_only_termination_rate_mean": 0.25,
                    "force_and_blocked_termination_rate_mean": 0.25,
                    "documented_force_jam_rate_mean": 0.0,
                }
            },
        }
    )

    assert five_profile_mean["force_threshold_termination_rate_mean_over_profiles"] == 0.25
    assert five_profile_mean["blocked_contact_termination_rate_mean_over_profiles"] == 0.25
    assert (
        five_profile_mean["force_threshold_only_termination_rate_mean_over_profiles"]
        == 0.25
    )
    assert (
        five_profile_mean["blocked_contact_only_termination_rate_mean_over_profiles"]
        == 0.125
    )
    assert five_profile_mean["force_and_blocked_termination_rate_mean_over_profiles"] == 0.125
    assert five_profile_mean["documented_force_jam_rate_mean_over_profiles"] == 0.125
