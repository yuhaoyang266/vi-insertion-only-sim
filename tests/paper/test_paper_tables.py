import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest

APPENDIX_DIAGNOSTIC_METRICS = (
    "jam_rate",
    "force_threshold_termination_rate",
    "blocked_contact_termination_rate",
    "force_threshold_only_termination_rate",
    "blocked_contact_only_termination_rate",
    "force_and_blocked_termination_rate",
    "documented_force_jam_rate",
)


def _load_paper_tables_module():
    module_path = (
        Path(__file__).resolve().parents[2] / "src" / "vi_full" / "paper_tables.py"
    )
    spec = importlib.util.spec_from_file_location("paper_tables_under_test", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _require_test_asset(path: Path, description: str) -> Path:
    if not path.exists():
        pytest.skip(f"missing {description}: {path}")
    return path


def _five_profile_mean(
    *,
    success_rate: float,
    jam_rate: float,
    final_distance_m: float,
    peak_force_n: float,
    p95_force_n: float,
    contact_steps: float,
) -> dict[str, float]:
    return {
        "success_rate_mean_over_profiles": success_rate,
        "success_rate_std_over_profiles": 0.0,
        "mean_episode_return_mean_over_profiles": 0.0,
        "mean_episode_return_std_over_profiles": 0.0,
        "mean_final_distance_mean_over_profiles": final_distance_m,
        "mean_final_distance_std_over_profiles": 0.0,
        "mean_episode_length_mean_over_profiles": 0.0,
        "mean_episode_length_std_over_profiles": 0.0,
        "mean_peak_contact_force_mean_over_profiles": peak_force_n,
        "mean_peak_contact_force_std_over_profiles": 0.0,
        "p95_peak_contact_force_mean_over_profiles": p95_force_n,
        "p95_peak_contact_force_std_over_profiles": 0.0,
        "mean_force_std_mean_over_profiles": 0.0,
        "mean_force_std_std_over_profiles": 0.0,
        "mean_first_contact_step_mean_over_profiles": 0.0,
        "mean_first_contact_step_std_over_profiles": 0.0,
        "mean_contact_steps_mean_over_profiles": contact_steps,
        "mean_contact_steps_std_over_profiles": 0.0,
        "mean_settling_steps_after_contact_mean_over_profiles": 0.0,
        "mean_settling_steps_after_contact_std_over_profiles": 0.0,
        "jam_rate_mean_over_profiles": jam_rate,
        "jam_rate_std_over_profiles": 0.0,
    }


def _profile_aggregate(
    profile_name: str,
    *,
    policy_name: str = "PPO",
    success_rate: float,
    jam_rate: float,
    final_distance_m: float,
    peak_force_n: float,
    p95_force_n: float,
    contact_steps: float,
    suite_name: str,
) -> dict[str, float | str | list[int]]:
    return {
        "policy_name": policy_name,
        "uncertainty_profile": profile_name,
        "num_seeds": 3,
        "seeds": [0, 1, 2],
        "success_rate_mean": success_rate,
        "success_rate_std": 0.0,
        "mean_episode_return_mean": 0.0,
        "mean_episode_return_std": 0.0,
        "mean_final_distance_mean": final_distance_m,
        "mean_final_distance_std": 0.0,
        "mean_episode_length_mean": 0.0,
        "mean_episode_length_std": 0.0,
        "mean_peak_contact_force_mean": peak_force_n,
        "mean_peak_contact_force_std": 0.0,
        "p95_peak_contact_force_mean": p95_force_n,
        "p95_peak_contact_force_std": 0.0,
        "mean_force_std_mean": 0.0,
        "mean_force_std_std": 0.0,
        "mean_first_contact_step_mean": 0.0,
        "mean_first_contact_step_std": 0.0,
        "mean_contact_steps_mean": contact_steps,
        "mean_contact_steps_std": 0.0,
        "mean_settling_steps_after_contact_mean": 0.0,
        "mean_settling_steps_after_contact_std": 0.0,
        "jam_rate_mean": jam_rate,
        "jam_rate_std": 0.0,
        "suite_name": suite_name,
    }


def _suite_payload(
    suite_name: str,
    *,
    success_rate: float,
    jam_rate: float,
    final_distance_m: float,
    peak_force_n: float,
    p95_force_n: float,
    contact_steps: float,
    profile_overrides: dict[str, dict[str, float]] | None = None,
) -> dict[str, object]:
    profiles = ("nominal", "tight_clearance", "high_friction", "offset_bias", "noisy_force")
    eval_results = {}
    for profile_name in profiles:
        values = {
            "success_rate": success_rate,
            "jam_rate": jam_rate,
            "final_distance_m": final_distance_m,
            "peak_force_n": peak_force_n,
            "p95_force_n": p95_force_n,
            "contact_steps": contact_steps,
        }
        if profile_overrides and profile_name in profile_overrides:
            values.update(profile_overrides[profile_name])
        eval_results[profile_name] = {
            "aggregate": _profile_aggregate(
                profile_name,
                success_rate=float(values["success_rate"]),
                jam_rate=float(values["jam_rate"]),
                final_distance_m=float(values["final_distance_m"]),
                peak_force_n=float(values["peak_force_n"]),
                p95_force_n=float(values["p95_force_n"]),
                contact_steps=float(values["contact_steps"]),
                suite_name=suite_name,
            )
        }
    return {
        "suite_run_kwargs": {"suite_name": suite_name},
        "train_configs": [],
        "training_summaries": [],
        "eval_results": eval_results,
        "five_profile_mean": _five_profile_mean(
            success_rate=success_rate,
            jam_rate=jam_rate,
            final_distance_m=final_distance_m,
            peak_force_n=peak_force_n,
            p95_force_n=p95_force_n,
            contact_steps=contact_steps,
        ),
    }


def _appendix_suite_payload(
    suite_name: str,
    *,
    success_rate: float,
    jam_rate: float,
    final_distance_m: float,
    peak_force_n: float,
    p95_force_n: float,
    contact_steps: float,
    teacher_motion_rule: str | None = None,
    teacher_impedance_rule: str | None = None,
    teacher_preset_name: str | None = None,
    diagnostic_over_profile_rates: dict[str, float] | None = None,
) -> dict[str, object]:
    payload = _suite_payload(
        suite_name,
        success_rate=success_rate,
        jam_rate=jam_rate,
        final_distance_m=final_distance_m,
        peak_force_n=peak_force_n,
        p95_force_n=p95_force_n,
        contact_steps=contact_steps,
    )
    if teacher_motion_rule is not None:
        payload["teacher_motion_rule"] = teacher_motion_rule
    if teacher_impedance_rule is not None:
        payload["teacher_impedance_rule"] = teacher_impedance_rule
    if teacher_preset_name is not None:
        payload["teacher_preset_name"] = teacher_preset_name

    diagnostics = {
        metric_name: float(
            (diagnostic_over_profile_rates or {}).get(
                metric_name,
                0.0 if metric_name != "jam_rate" else jam_rate,
            )
        )
        for metric_name in APPENDIX_DIAGNOSTIC_METRICS
    }
    for metric_name, value in diagnostics.items():
        payload["five_profile_mean"][f"{metric_name}_mean_over_profiles"] = value
        payload["five_profile_mean"][f"{metric_name}_std_over_profiles"] = 0.0
        for profile_payload in payload["eval_results"].values():
            profile_payload["aggregate"][f"{metric_name}_mean"] = value
            profile_payload["aggregate"][f"{metric_name}_std"] = 0.0
    return payload


def _handcrafted_policy_payload(
    policy_name: str,
    profile_name: str,
    *,
    success_rate: float,
    jam_rate: float,
    final_distance_m: float,
    peak_force_n: float,
    p95_force_n: float,
    contact_steps: float,
) -> dict[str, object]:
    return {
        "per_seed": [],
        "aggregate": _profile_aggregate(
            profile_name,
            policy_name=policy_name,
            success_rate=success_rate,
            jam_rate=jam_rate,
            final_distance_m=final_distance_m,
            peak_force_n=peak_force_n,
            p95_force_n=p95_force_n,
            contact_steps=contact_steps,
            suite_name=policy_name,
        ),
    }


def _write_sample_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    main_report = {
        "config": {
            "suite_names": [
                "ppo_no_bc",
                "bc_only_stable_r32_p32",
                "fixed_impedance_rl",
            ],
            "uncertainty_profiles": [
                "nominal",
                "tight_clearance",
                "high_friction",
                "offset_bias",
                "noisy_force",
            ],
        },
        "handcrafted_results": {},
        "learned_results": {
            "ppo_no_bc": _suite_payload(
                "ppo_no_bc",
                success_rate=0.0,
                jam_rate=0.0,
                final_distance_m=0.0185,
                peak_force_n=0.0,
                p95_force_n=0.0,
                contact_steps=0.0,
            ),
            "bc_only_stable_r32_p32": _suite_payload(
                "bc_only_stable_r32_p32",
                success_rate=1.0,
                jam_rate=0.0,
                final_distance_m=0.0009,
                peak_force_n=1.0,
                p95_force_n=1.3,
                contact_steps=31.0,
            ),
            "fixed_impedance_rl": _suite_payload(
                "fixed_impedance_rl",
                success_rate=0.0,
                jam_rate=0.0,
                final_distance_m=0.0186,
                peak_force_n=0.0,
                p95_force_n=0.0,
                contact_steps=0.0,
            ),
        },
    }
    fixed_imp_report = {
        "config": {
            "suite_name": "fixed_impedance_rl_stable_r32_p32",
            "uncertainty_profiles": [
                "nominal",
                "tight_clearance",
                "high_friction",
                "offset_bias",
                "noisy_force",
            ],
        },
        "train_configs": [],
        "training_summaries": [],
        "eval_results": {
            "nominal": {
                "aggregate": _profile_aggregate(
                    "nominal",
                    success_rate=0.98,
                    jam_rate=0.0,
                    final_distance_m=0.000913655,
                    peak_force_n=0.996472,
                    p95_force_n=1.25,
                    contact_steps=36.286667,
                    suite_name="fixed_impedance_rl_stable_r32_p32",
                )
            },
            "tight_clearance": {
                "aggregate": _profile_aggregate(
                    "tight_clearance",
                    success_rate=0.98,
                    jam_rate=0.0,
                    final_distance_m=0.000913655,
                    peak_force_n=0.996472,
                    p95_force_n=1.25,
                    contact_steps=36.286667,
                    suite_name="fixed_impedance_rl_stable_r32_p32",
                )
            },
            "high_friction": {
                "aggregate": _profile_aggregate(
                    "high_friction",
                    success_rate=0.666667,
                    jam_rate=0.0,
                    final_distance_m=0.001052665,
                    peak_force_n=1.595784,
                    p95_force_n=1.9,
                    contact_steps=43.486667,
                    suite_name="fixed_impedance_rl_stable_r32_p32",
                )
            },
            "offset_bias": {
                "aggregate": _profile_aggregate(
                    "offset_bias",
                    success_rate=0.98,
                    jam_rate=0.0,
                    final_distance_m=0.000913655,
                    peak_force_n=0.996472,
                    p95_force_n=1.25,
                    contact_steps=36.286667,
                    suite_name="fixed_impedance_rl_stable_r32_p32",
                )
            },
            "noisy_force": {
                "aggregate": _profile_aggregate(
                    "noisy_force",
                    success_rate=0.96,
                    jam_rate=0.0,
                    final_distance_m=0.000921641,
                    peak_force_n=1.167105,
                    p95_force_n=1.55,
                    contact_steps=36.573333,
                    suite_name="fixed_impedance_rl_stable_r32_p32",
                )
            },
        },
        "five_profile_mean": _five_profile_mean(
            success_rate=0.9133333333333333,
            jam_rate=0.0,
            final_distance_m=0.0009430541400754262,
            peak_force_n=1.150460880956042,
            p95_force_n=1.4932526652268372,
            contact_steps=37.784,
        ),
    }
    main_path = tmp_path / "benchmark.json"
    fixed_path = tmp_path / "fixed_imp.json"
    main_path.write_text(json.dumps(main_report), encoding="utf-8")
    fixed_path.write_text(json.dumps(fixed_imp_report), encoding="utf-8")
    return main_path, fixed_path


def _per_seed_summary(
    profile_name: str,
    suite_name: str,
    seed: int,
    *,
    success_rate: float,
    jam_rate: float,
    final_distance_m: float,
    peak_force_n: float,
    p95_force_n: float,
    contact_steps: float,
) -> dict[str, float | int | str]:
    return {
        "policy_name": "PPO",
        "uncertainty_profile": profile_name,
        "episodes": 100,
        "success_rate": success_rate,
        "mean_episode_return": success_rate * 10.0,
        "mean_final_distance": final_distance_m,
        "mean_episode_length": 64.0,
        "mean_peak_contact_force": peak_force_n,
        "p95_peak_contact_force": p95_force_n,
        "mean_force_std": peak_force_n * 0.1,
        "mean_first_contact_step": 16.0,
        "mean_contact_steps": contact_steps,
        "mean_settling_steps_after_contact": contact_steps + 2.0,
        "jam_rate": jam_rate,
        "seed": seed,
        "training_summary": {"seed": seed},
    }


def _aggregate_seed_samples(
    suite_name: str,
    profile_name: str,
    per_seed: list[dict[str, float | int | str]],
) -> dict[str, float | int | str | list[int]]:
    metric_names = (
        "success_rate",
        "mean_episode_return",
        "mean_final_distance",
        "mean_episode_length",
        "mean_peak_contact_force",
        "p95_peak_contact_force",
        "mean_force_std",
        "mean_first_contact_step",
        "mean_contact_steps",
        "mean_settling_steps_after_contact",
        "jam_rate",
    )
    aggregate: dict[str, float | int | str | list[int]] = {
        "policy_name": "PPO",
        "uncertainty_profile": profile_name,
        "num_seeds": len(per_seed),
        "seeds": [int(item["seed"]) for item in per_seed],
        "suite_name": suite_name,
    }
    for metric_name in metric_names:
        values = np.asarray([float(item[metric_name]) for item in per_seed], dtype=np.float64)
        aggregate[f"{metric_name}_mean"] = float(np.mean(values))
        aggregate[f"{metric_name}_std"] = float(np.std(values))
    return aggregate


def _five_profile_mean_from_eval_results(
    eval_results: dict[str, dict[str, object]],
) -> dict[str, float]:
    metric_names = (
        "success_rate",
        "mean_episode_return",
        "mean_final_distance",
        "mean_episode_length",
        "mean_peak_contact_force",
        "p95_peak_contact_force",
        "mean_force_std",
        "mean_first_contact_step",
        "mean_contact_steps",
        "mean_settling_steps_after_contact",
        "jam_rate",
    )
    profile_aggregates = [payload["aggregate"] for payload in eval_results.values()]
    five_profile_mean: dict[str, float] = {}
    for metric_name in metric_names:
        values = np.asarray(
            [float(aggregate[f"{metric_name}_mean"]) for aggregate in profile_aggregates],
            dtype=np.float64,
        )
        five_profile_mean[f"{metric_name}_mean_over_profiles"] = float(np.mean(values))
        five_profile_mean[f"{metric_name}_std_over_profiles"] = float(np.std(values))
    return five_profile_mean


def _suite_payload_from_profile_seed_samples(
    suite_name: str,
    *,
    profile_seed_samples: dict[str, list[dict[str, float]]],
) -> dict[str, object]:
    eval_results: dict[str, dict[str, object]] = {}
    for profile_name, samples in profile_seed_samples.items():
        per_seed = [
            _per_seed_summary(
                profile_name,
                suite_name,
                seed=index,
                success_rate=float(sample["success_rate"]),
                jam_rate=float(sample.get("jam_rate", 0.0)),
                final_distance_m=float(sample["final_distance_m"]),
                peak_force_n=float(sample["peak_force_n"]),
                p95_force_n=float(sample["p95_force_n"]),
                contact_steps=float(sample["contact_steps"]),
            )
            for index, sample in enumerate(samples)
        ]
        eval_results[profile_name] = {
            "per_seed": per_seed,
            "aggregate": _aggregate_seed_samples(suite_name, profile_name, per_seed),
        }
    return {
        "suite_run_kwargs": {"suite_name": suite_name},
        "train_configs": [],
        "training_summaries": [],
        "eval_results": eval_results,
        "five_profile_mean": _five_profile_mean_from_eval_results(eval_results),
    }


def _make_profile_seed_samples(
    *,
    success_rates: list[float],
    final_distance_mm: list[float],
    peak_force_n: list[float],
    p95_force_n: list[float],
    contact_steps: list[float],
) -> list[dict[str, float]]:
    return [
        {
            "success_rate": success_rate,
            "final_distance_m": final_distance / 1000.0,
            "peak_force_n": peak_force,
            "p95_force_n": p95_force,
            "contact_steps": steps,
        }
        for success_rate, final_distance, peak_force, p95_force, steps in zip(
            success_rates,
            final_distance_mm,
            peak_force_n,
            p95_force_n,
            contact_steps,
            strict=True,
        )
    ]


def _write_statistics_sample_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    profiles = {
        "nominal": {
            "bc_only": _make_profile_seed_samples(
                success_rates=[1.0, 1.0, 1.0, 1.0, 1.0],
                final_distance_mm=[0.90, 0.91, 0.89, 0.90, 0.92],
                peak_force_n=[1.00, 1.02, 0.98, 1.01, 0.99],
                p95_force_n=[1.25, 1.28, 1.22, 1.26, 1.24],
                contact_steps=[31.0, 30.0, 32.0, 31.0, 30.0],
            ),
            "bc_to_ppo": _make_profile_seed_samples(
                success_rates=[1.0, 0.99, 1.0, 1.0, 0.99],
                final_distance_mm=[0.91, 0.92, 0.90, 0.91, 0.92],
                peak_force_n=[0.96, 0.97, 0.95, 0.96, 0.97],
                p95_force_n=[1.20, 1.22, 1.18, 1.21, 1.22],
                contact_steps=[30.0, 31.0, 31.0, 30.0, 31.0],
            ),
            "fixed": _make_profile_seed_samples(
                success_rates=[0.98, 0.97, 0.99, 0.98, 0.97],
                final_distance_mm=[0.96, 0.97, 0.95, 0.96, 0.97],
                peak_force_n=[1.20, 1.18, 1.21, 1.19, 1.20],
                p95_force_n=[1.48, 1.46, 1.49, 1.47, 1.48],
                contact_steps=[36.0, 35.0, 37.0, 36.0, 35.0],
            ),
        },
        "tight_clearance": {
            "bc_only": _make_profile_seed_samples(
                success_rates=[1.0, 1.0, 1.0, 1.0, 1.0],
                final_distance_mm=[0.91, 0.92, 0.90, 0.91, 0.92],
                peak_force_n=[1.01, 1.03, 0.99, 1.02, 1.00],
                p95_force_n=[1.27, 1.29, 1.25, 1.28, 1.26],
                contact_steps=[31.0, 31.0, 32.0, 31.0, 31.0],
            ),
            "bc_to_ppo": _make_profile_seed_samples(
                success_rates=[1.0, 1.0, 0.99, 1.0, 0.99],
                final_distance_mm=[0.92, 0.93, 0.91, 0.92, 0.93],
                peak_force_n=[0.97, 0.98, 0.96, 0.97, 0.98],
                p95_force_n=[1.21, 1.23, 1.20, 1.22, 1.23],
                contact_steps=[30.0, 31.0, 31.0, 30.0, 31.0],
            ),
            "fixed": _make_profile_seed_samples(
                success_rates=[0.98, 0.98, 0.97, 0.98, 0.97],
                final_distance_mm=[0.97, 0.98, 0.96, 0.97, 0.98],
                peak_force_n=[1.21, 1.19, 1.22, 1.20, 1.21],
                p95_force_n=[1.49, 1.47, 1.50, 1.48, 1.49],
                contact_steps=[36.0, 36.0, 37.0, 36.0, 36.0],
            ),
        },
        "high_friction": {
            "bc_only": _make_profile_seed_samples(
                success_rates=[1.0, 1.0, 1.0, 1.0, 1.0],
                final_distance_mm=[0.93, 0.94, 0.92, 0.93, 0.94],
                peak_force_n=[1.15, 1.18, 1.12, 1.16, 1.14],
                p95_force_n=[1.45, 1.48, 1.42, 1.46, 1.44],
                contact_steps=[33.0, 33.0, 34.0, 33.0, 33.0],
            ),
            "bc_to_ppo": _make_profile_seed_samples(
                success_rates=[1.0, 0.99, 1.0, 1.0, 0.99],
                final_distance_mm=[0.94, 0.95, 0.93, 0.94, 0.95],
                peak_force_n=[1.10, 1.12, 1.08, 1.11, 1.09],
                p95_force_n=[1.38, 1.40, 1.36, 1.39, 1.37],
                contact_steps=[32.0, 32.0, 33.0, 32.0, 32.0],
            ),
            "fixed": _make_profile_seed_samples(
                success_rates=[0.70, 0.68, 0.64, 0.72, 0.66],
                final_distance_mm=[1.08, 1.10, 1.12, 1.06, 1.09],
                peak_force_n=[1.58, 1.61, 1.64, 1.55, 1.60],
                p95_force_n=[1.88, 1.92, 1.96, 1.85, 1.90],
                contact_steps=[43.0, 44.0, 45.0, 42.0, 44.0],
            ),
        },
        "offset_bias": {
            "bc_only": _make_profile_seed_samples(
                success_rates=[1.0, 1.0, 1.0, 1.0, 1.0],
                final_distance_mm=[0.90, 0.91, 0.89, 0.90, 0.91],
                peak_force_n=[1.00, 1.01, 0.99, 1.00, 1.01],
                p95_force_n=[1.24, 1.26, 1.23, 1.24, 1.25],
                contact_steps=[31.0, 30.0, 31.0, 31.0, 30.0],
            ),
            "bc_to_ppo": _make_profile_seed_samples(
                success_rates=[1.0, 1.0, 0.99, 1.0, 0.99],
                final_distance_mm=[0.91, 0.92, 0.90, 0.91, 0.92],
                peak_force_n=[0.95, 0.97, 0.94, 0.95, 0.96],
                p95_force_n=[1.19, 1.21, 1.18, 1.19, 1.20],
                contact_steps=[30.0, 31.0, 30.0, 30.0, 31.0],
            ),
            "fixed": _make_profile_seed_samples(
                success_rates=[0.98, 0.97, 0.98, 0.97, 0.98],
                final_distance_mm=[0.95, 0.96, 0.95, 0.96, 0.95],
                peak_force_n=[1.19, 1.20, 1.18, 1.19, 1.20],
                p95_force_n=[1.47, 1.48, 1.46, 1.47, 1.48],
                contact_steps=[36.0, 35.0, 36.0, 35.0, 36.0],
            ),
        },
        "noisy_force": {
            "bc_only": _make_profile_seed_samples(
                success_rates=[1.0, 1.0, 1.0, 1.0, 1.0],
                final_distance_mm=[0.92, 0.93, 0.91, 0.92, 0.93],
                peak_force_n=[1.05, 1.07, 1.03, 1.06, 1.04],
                p95_force_n=[1.31, 1.33, 1.29, 1.32, 1.30],
                contact_steps=[31.0, 31.0, 32.0, 31.0, 31.0],
            ),
            "bc_to_ppo": _make_profile_seed_samples(
                success_rates=[0.99, 1.0, 0.99, 1.0, 0.99],
                final_distance_mm=[0.93, 0.94, 0.92, 0.93, 0.94],
                peak_force_n=[1.01, 1.03, 1.00, 1.02, 1.01],
                p95_force_n=[1.26, 1.28, 1.25, 1.27, 1.26],
                contact_steps=[30.0, 31.0, 30.0, 30.0, 31.0],
            ),
            "fixed": _make_profile_seed_samples(
                success_rates=[0.96, 0.95, 0.97, 0.96, 0.95],
                final_distance_mm=[0.97, 0.98, 0.96, 0.97, 0.98],
                peak_force_n=[1.24, 1.25, 1.23, 1.24, 1.25],
                p95_force_n=[1.53, 1.54, 1.52, 1.53, 1.54],
                contact_steps=[36.0, 36.0, 37.0, 36.0, 36.0],
            ),
        },
    }

    main_report = {
        "config": {
            "suite_names": [
                "bc_only_stable_r32_p32",
                "fixed_impedance_rl",
                "repaired_mainline_bc_to_ppo",
            ],
            "uncertainty_profiles": list(profiles),
            "seeds": [0, 1, 2, 3, 4],
            "episodes_per_seed": 100,
            "max_episode_steps": 64,
        },
        "handcrafted_results": {},
        "learned_results": {
            "bc_only_stable_r32_p32": _suite_payload_from_profile_seed_samples(
                "bc_only_stable_r32_p32",
                profile_seed_samples={
                    profile_name: spec["bc_only"] for profile_name, spec in profiles.items()
                },
            ),
            "fixed_impedance_rl": _suite_payload_from_profile_seed_samples(
                "fixed_impedance_rl",
                profile_seed_samples={
                    profile_name: spec["fixed"] for profile_name, spec in profiles.items()
                },
            ),
            "repaired_mainline_bc_to_ppo": _suite_payload_from_profile_seed_samples(
                "repaired_mainline_bc_to_ppo",
                profile_seed_samples={
                    profile_name: spec["bc_to_ppo"] for profile_name, spec in profiles.items()
                },
            ),
        },
    }
    fixed_impedance_report = {
        "config": {
            "suite_name": "fixed_impedance_rl_stable_r32_p32",
            "uncertainty_profiles": list(profiles),
            "seeds": [0, 1, 2, 3, 4],
            "episodes_per_seed": 100,
            "max_episode_steps": 64,
        },
        **_suite_payload_from_profile_seed_samples(
            "fixed_impedance_rl_stable_r32_p32",
            profile_seed_samples={
                profile_name: spec["fixed"] for profile_name, spec in profiles.items()
            },
        ),
    }
    main_path = tmp_path / "statistics_benchmark.json"
    fixed_path = tmp_path / "statistics_fixed.json"
    main_path.write_text(json.dumps(main_report), encoding="utf-8")
    fixed_path.write_text(json.dumps(fixed_impedance_report), encoding="utf-8")
    return main_path, fixed_path


def _inject_statistics_support_metrics(main_path: Path, fixed_path: Path) -> None:
    suite_support_values = {
        "bc_only_stable_r32_p32": {
            "support_coverage_index": 0.92,
            "support_cell_coverage": 0.78,
        },
        "repaired_mainline_bc_to_ppo": {
            "support_coverage_index": 0.95,
            "support_cell_coverage": 0.82,
        },
        "fixed_impedance_rl_stable_r32_p32": {
            "support_coverage_index": 0.41,
            "support_cell_coverage": 0.33,
        },
    }

    def _decorate_suite_payload(payload: dict[str, object], suite_name: str) -> None:
        suite_metrics = suite_support_values[suite_name]
        eval_results = payload["eval_results"]
        for profile_payload in eval_results.values():
            per_seed = profile_payload["per_seed"]
            for seed_payload in per_seed:
                seed_payload["support_metrics"] = {
                    **suite_metrics,
                    "covered_rollout_sample_count": 92,
                    "rollout_sample_count": 100,
                    "demo_unique_cell_count": 40,
                    "rollout_unique_cell_count": 25,
                    "shared_unique_cell_count": 20,
                }
            profile_payload["support_metrics"] = {
                "support_coverage_index_mean": suite_metrics["support_coverage_index"],
                "support_coverage_index_std": 0.0,
                "support_cell_coverage_mean": suite_metrics["support_cell_coverage"],
                "support_cell_coverage_std": 0.0,
            }
        payload["support_metrics"] = {
            "support_coverage_index_mean_over_profiles": suite_metrics["support_coverage_index"],
            "support_coverage_index_std_over_profiles": 0.0,
            "support_cell_coverage_mean_over_profiles": suite_metrics["support_cell_coverage"],
            "support_cell_coverage_std_over_profiles": 0.0,
        }

    main_report = json.loads(main_path.read_text(encoding="utf-8"))
    _decorate_suite_payload(
        main_report["learned_results"]["bc_only_stable_r32_p32"],
        "bc_only_stable_r32_p32",
    )
    _decorate_suite_payload(
        main_report["learned_results"]["repaired_mainline_bc_to_ppo"],
        "repaired_mainline_bc_to_ppo",
    )
    main_path.write_text(json.dumps(main_report), encoding="utf-8")

    fixed_report = json.loads(fixed_path.read_text(encoding="utf-8"))
    _decorate_suite_payload(fixed_report, "fixed_impedance_rl_stable_r32_p32")
    fixed_path.write_text(json.dumps(fixed_report), encoding="utf-8")


def test_build_3dof_paper_table_export_replaces_fixed_impedance_with_stable_override(
    tmp_path: Path,
) -> None:
    module = _load_paper_tables_module()
    main_path, fixed_path = _write_sample_artifacts(tmp_path)

    export = module.build_3dof_paper_table_export(
        benchmark_report_path=main_path,
        fixed_impedance_report_path=fixed_path,
    )

    assert export["suite_order"] == [
        "ppo_no_bc",
        "bc_only_stable_r32_p32",
        "fixed_impedance_rl_stable_r32_p32",
    ]
    fixed_row = next(
        row for row in export["suite_rows"] if row["suite_name"] == "fixed_impedance_rl_stable_r32_p32"
    )
    assert fixed_row["replaces_main_suite"] == "fixed_impedance_rl"
    assert fixed_row["source_artifact"].endswith("fixed_imp.json")
    assert fixed_row["five_profile_mean"]["success_rate"] == pytest.approx(0.9133333333333333)
    assert fixed_row["five_profile_mean"]["mean_final_distance_mm"] == pytest.approx(0.9430541400754262)
    assert fixed_row["effective_pressure_classes"]["baseline"]["profiles"] == [
        "nominal",
        "tight_clearance",
        "offset_bias",
    ]
    assert fixed_row["effective_pressure_classes"]["baseline"]["metrics"]["success_rate"] == pytest.approx(0.98)
    assert export["profile_equivalence_annotation"]["equivalence_classes"][0]["class_name"] == "baseline"


def test_build_3dof_paper_table_export_tolerates_partial_profile_benchmarks(
    tmp_path: Path,
) -> None:
    module = _load_paper_tables_module()
    main_path, _ = _write_sample_artifacts(tmp_path)
    main_report = json.loads(main_path.read_text(encoding="utf-8"))
    main_report["config"]["suite_names"] = ["bc_only_stable_r32_p32"]
    main_report["config"]["uncertainty_profiles"] = ["nominal"]
    suite_payload = main_report["learned_results"]["bc_only_stable_r32_p32"]
    suite_payload["eval_results"] = {
        "nominal": suite_payload["eval_results"]["nominal"],
    }
    main_report["learned_results"] = {
        "bc_only_stable_r32_p32": suite_payload,
    }
    main_path.write_text(json.dumps(main_report), encoding="utf-8")

    export = module.build_3dof_paper_table_export(benchmark_report_path=main_path)
    markdown = module.render_3dof_paper_table_markdown(export)

    assert export["suite_order"] == ["bc_only_stable_r32_p32"]
    assert len(export["suite_rows"]) == 1
    row = export["suite_rows"][0]
    assert list(row["effective_pressure_classes"]) == ["baseline"]
    assert row["effective_pressure_classes"]["baseline"]["profiles"] == ["nominal"]
    assert (
        row["effective_pressure_classes"]["baseline"]["metrics"]["success_rate"]
        == pytest.approx(1.0)
    )
    assert list(row["per_profile"]) == ["nominal"]
    assert [
        item["class_name"] for item in export["profile_equivalence_annotation"]["equivalence_classes"]
    ] == ["baseline"]
    assert (
        export["profile_equivalence_annotation"]["summary"]
        == "Current artifact includes a subset of the benchmark eval profiles: nominal."
    )
    assert (
        "Current artifact includes a subset of the benchmark eval profiles: nominal."
        in markdown
    )
    assert "- `baseline`: nominal." in markdown
    assert "`high_friction`" not in markdown


def test_export_3dof_paper_table_writes_json_and_markdown(tmp_path: Path) -> None:
    module = _load_paper_tables_module()
    main_path, fixed_path = _write_sample_artifacts(tmp_path)

    json_path, markdown_path = module.export_3dof_paper_table(
        benchmark_report_path=main_path,
        fixed_impedance_report_path=fixed_path,
        output_dir=tmp_path,
        stem="paper_table",
    )

    exported_json = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")

    assert json_path.name == "paper_table.json"
    assert markdown_path.name == "paper_table.md"
    assert exported_json["suite_rows"][2]["display_name"] == "Fixed-impedance RL (stable BC 32/32)"
    assert "PPO w/o BC" in markdown
    assert "Fixed-impedance RL (stable BC 32/32)" in markdown
    assert "Five nominal eval profiles collapse to three effective pressure classes" in markdown


def test_paper_table_export_includes_handcrafted_classical_anchor_rows(tmp_path: Path) -> None:
    module = _load_paper_tables_module()
    main_path, fixed_path = _write_sample_artifacts(tmp_path)
    main_report = json.loads(main_path.read_text(encoding="utf-8"))
    handcrafted_policy_names = [
        "hybrid_position_force",
        "compliant_search",
        "tuned_impedance",
    ]
    main_report["config"]["handcrafted_policy_names"] = handcrafted_policy_names
    main_report["handcrafted_results"] = {
        profile_name: {
            "hybrid_position_force": _handcrafted_policy_payload(
                "hybrid_position_force",
                profile_name,
                success_rate=0.94,
                jam_rate=0.0,
                final_distance_m=0.0012,
                peak_force_n=2.5,
                p95_force_n=2.9,
                contact_steps=35.0,
            ),
            "compliant_search": _handcrafted_policy_payload(
                "compliant_search",
                profile_name,
                success_rate=0.92,
                jam_rate=0.0,
                final_distance_m=0.0013,
                peak_force_n=2.2,
                p95_force_n=2.6,
                contact_steps=36.0,
            ),
            "tuned_impedance": _handcrafted_policy_payload(
                "tuned_impedance",
                profile_name,
                success_rate=0.96,
                jam_rate=0.0,
                final_distance_m=0.0011,
                peak_force_n=2.7,
                p95_force_n=3.1,
                contact_steps=38.0,
            ),
        }
        for profile_name in main_report["config"]["uncertainty_profiles"]
    }
    main_path.write_text(json.dumps(main_report), encoding="utf-8")

    export = module.build_3dof_paper_table_export(
        benchmark_report_path=main_path,
        fixed_impedance_report_path=fixed_path,
    )
    markdown = module.render_3dof_paper_table_markdown(export)

    assert export["handcrafted_policy_order"] == handcrafted_policy_names
    assert [row["suite_name"] for row in export["handcrafted_rows"]] == handcrafted_policy_names
    tuned_row = next(
        row for row in export["handcrafted_rows"] if row["suite_name"] == "tuned_impedance"
    )
    assert tuned_row["display_name"] == "Hand-tuned impedance"
    assert tuned_row["five_profile_mean"]["success_rate"] == pytest.approx(0.96)
    assert "## Handcrafted / Classical Anchors" in markdown
    assert "Hybrid position-force" in markdown
    assert "Compliant search" in markdown
    assert "Hand-tuned impedance" in markdown


def test_build_3dof_statistics_report_adds_ci_effect_size_and_ceiling_note(
    tmp_path: Path,
) -> None:
    module = _load_paper_tables_module()
    main_path, fixed_path = _write_statistics_sample_artifacts(tmp_path)

    report = module.build_3dof_statistics_report(
        benchmark_report_path=main_path,
        fixed_impedance_report_path=fixed_path,
    )

    assert report["sample_plan"]["recommended_training_seed_min"] == 5
    assert report["sample_plan"]["recommended_training_seed_max"] == 10
    assert report["sample_plan"]["recommended_episodes_per_seed_profile_min"] == 100
    assert report["observed_sample_plan"]["num_training_seeds"] == 5
    assert report["observed_sample_plan"]["episodes_per_seed"] == 100

    bc_only_stats = report["suite_statistics"]["bc_only_stable_r32_p32"]["five_profile_statistics"][
        "success_rate"
    ]
    assert bc_only_stats["mean"] == pytest.approx(1.0)
    assert "std" in bc_only_stats
    assert bc_only_stats["ci"]["lower"] <= bc_only_stats["mean"] <= bc_only_stats["ci"]["upper"]

    comparison = next(
        item
        for item in report["selected_comparisons"]
        if item["reference_suite"] == "bc_only_stable_r32_p32"
        and item["candidate_suite"] == "repaired_mainline_bc_to_ppo"
        and item["metric"] == "success_rate"
    )
    assert comparison["effect_size"]["effect_type"] == "ceiling_aware_success_rate_gap"
    assert "absolute_mean_difference" in comparison["effect_size"]
    assert comparison["practical_interpretation"] == "negligible under ceiling saturation"
    assert "ceiling-saturated" in comparison["practical_note"]


def test_build_3dof_statistics_report_exports_support_diagnostics_when_available(
    tmp_path: Path,
) -> None:
    module = _load_paper_tables_module()
    main_path, fixed_path = _write_statistics_sample_artifacts(tmp_path)
    _inject_statistics_support_metrics(main_path, fixed_path)

    report = module.build_3dof_statistics_report(
        benchmark_report_path=main_path,
        fixed_impedance_report_path=fixed_path,
    )
    markdown = module.render_3dof_statistics_report_markdown(report)

    repaired_support_stats = report["suite_statistics"]["repaired_mainline_bc_to_ppo"][
        "five_profile_support_statistics"
    ]["support_coverage_index"]
    assert repaired_support_stats["mean"] == pytest.approx(0.95)
    assert repaired_support_stats["std"] == pytest.approx(0.0)
    assert "per_profile_support_statistics" in report["suite_statistics"]["bc_only_stable_r32_p32"]
    assert "## Support Diagnostics" in markdown
    assert "Support Coverage Index" in markdown


def test_build_3dof_statistics_report_skips_support_diagnostics_for_legacy_artifacts(
    tmp_path: Path,
) -> None:
    module = _load_paper_tables_module()
    main_path, fixed_path = _write_statistics_sample_artifacts(tmp_path)

    report = module.build_3dof_statistics_report(
        benchmark_report_path=main_path,
        fixed_impedance_report_path=fixed_path,
    )
    markdown = module.render_3dof_statistics_report_markdown(report)

    assert "five_profile_support_statistics" not in report["suite_statistics"]["bc_only_stable_r32_p32"]
    assert "per_profile_support_statistics" not in report["suite_statistics"]["bc_only_stable_r32_p32"]
    assert "## Support Diagnostics" not in markdown


def test_paper_table_export_can_embed_statistics_report_and_render_notes(tmp_path: Path) -> None:
    module = _load_paper_tables_module()
    main_path, fixed_path = _write_statistics_sample_artifacts(tmp_path)

    statistics_json_path, _ = module.export_3dof_statistics_report(
        benchmark_report_path=main_path,
        fixed_impedance_report_path=fixed_path,
        output_dir=tmp_path,
        stem="three_dof_stats",
    )
    export = module.build_3dof_paper_table_export(
        benchmark_report_path=main_path,
        fixed_impedance_report_path=fixed_path,
        statistics_report_path=statistics_json_path,
    )
    markdown = module.render_3dof_paper_table_markdown(export)

    repaired_row = next(
        row for row in export["suite_rows"] if row["suite_name"] == "repaired_mainline_bc_to_ppo"
    )
    assert repaired_row["five_profile_statistics"]["success_rate"]["mean"] == pytest.approx(0.9956)
    assert repaired_row["comparison_notes"][0].endswith("negligible under ceiling saturation.")
    assert "selected_comparisons" in export["statistics_report"]
    assert "95% CI" in markdown
    assert "negligible under ceiling saturation" in markdown


def test_build_3dof_paper_table_export_rejects_mismatched_statistics_report(
    tmp_path: Path,
) -> None:
    module = _load_paper_tables_module()
    main_path, fixed_path = _write_statistics_sample_artifacts(tmp_path)
    other_benchmark_path = tmp_path / "other_benchmark.json"
    other_benchmark_path.write_text(main_path.read_text(encoding="utf-8"), encoding="utf-8")

    statistics_json_path, _ = module.export_3dof_statistics_report(
        benchmark_report_path=main_path,
        fixed_impedance_report_path=fixed_path,
        output_dir=tmp_path,
        stem="three_dof_stats",
    )

    with pytest.raises(ValueError, match="Statistics report benchmark source does not match"):
        module.build_3dof_paper_table_export(
            benchmark_report_path=other_benchmark_path,
            fixed_impedance_report_path=fixed_path,
            statistics_report_path=statistics_json_path,
        )


def _write_appendix_sample_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    teacher_suites = {
        "teacher_variable_variable__repaired_mainline": _appendix_suite_payload(
            "teacher_variable_variable__repaired_mainline",
            success_rate=0.99,
            jam_rate=0.01,
            final_distance_m=0.0009,
            peak_force_n=0.95,
            p95_force_n=1.20,
            contact_steps=30.0,
            teacher_preset_name="teacher_variable_variable",
            teacher_motion_rule="contact_aware_variable_motion",
            teacher_impedance_rule="contact_aware_variable_impedance",
            diagnostic_over_profile_rates={
                "jam_rate": 0.01,
                "force_threshold_termination_rate": 0.01,
                "blocked_contact_termination_rate": 0.00,
                "force_threshold_only_termination_rate": 0.01,
                "blocked_contact_only_termination_rate": 0.00,
                "force_and_blocked_termination_rate": 0.00,
                "documented_force_jam_rate": 0.00,
            },
        ),
        "teacher_variable_fixed__repaired_mainline": _appendix_suite_payload(
            "teacher_variable_fixed__repaired_mainline",
            success_rate=0.94,
            jam_rate=0.03,
            final_distance_m=0.0012,
            peak_force_n=1.08,
            p95_force_n=1.34,
            contact_steps=32.0,
            teacher_preset_name="teacher_variable_fixed",
            teacher_motion_rule="contact_aware_variable_motion",
            teacher_impedance_rule="fixed",
            diagnostic_over_profile_rates={
                "jam_rate": 0.03,
                "force_threshold_termination_rate": 0.01,
                "blocked_contact_termination_rate": 0.02,
                "force_threshold_only_termination_rate": 0.01,
                "blocked_contact_only_termination_rate": 0.02,
                "force_and_blocked_termination_rate": 0.00,
                "documented_force_jam_rate": 0.00,
            },
        ),
        "teacher_pose_variable__repaired_mainline": _appendix_suite_payload(
            "teacher_pose_variable__repaired_mainline",
            success_rate=0.92,
            jam_rate=0.05,
            final_distance_m=0.0015,
            peak_force_n=1.15,
            p95_force_n=1.42,
            contact_steps=35.0,
            teacher_preset_name="teacher_pose_variable",
            teacher_motion_rule="pose_feedback",
            teacher_impedance_rule="contact_aware_variable_impedance",
            diagnostic_over_profile_rates={
                "jam_rate": 0.05,
                "force_threshold_termination_rate": 0.02,
                "blocked_contact_termination_rate": 0.03,
                "force_threshold_only_termination_rate": 0.01,
                "blocked_contact_only_termination_rate": 0.02,
                "force_and_blocked_termination_rate": 0.01,
                "documented_force_jam_rate": 0.01,
            },
        ),
        "teacher_pose_fixed__repaired_mainline": _appendix_suite_payload(
            "teacher_pose_fixed__repaired_mainline",
            success_rate=0.88,
            jam_rate=0.09,
            final_distance_m=0.0018,
            peak_force_n=1.28,
            p95_force_n=1.60,
            contact_steps=38.0,
            teacher_preset_name="teacher_pose_fixed",
            teacher_motion_rule="pose_feedback",
            teacher_impedance_rule="fixed",
            diagnostic_over_profile_rates={
                "jam_rate": 0.09,
                "force_threshold_termination_rate": 0.04,
                "blocked_contact_termination_rate": 0.06,
                "force_threshold_only_termination_rate": 0.02,
                "blocked_contact_only_termination_rate": 0.04,
                "force_and_blocked_termination_rate": 0.02,
                "documented_force_jam_rate": 0.02,
            },
        ),
    }
    diagnostic_suites = {
        "bc_only_stable_r32_p32": _appendix_suite_payload(
            "bc_only_stable_r32_p32",
            success_rate=1.0,
            jam_rate=0.0,
            final_distance_m=0.0009,
            peak_force_n=1.0,
            p95_force_n=1.3,
            contact_steps=31.0,
            diagnostic_over_profile_rates={
                "jam_rate": 0.0,
                "force_threshold_termination_rate": 0.0,
                "blocked_contact_termination_rate": 0.0,
                "force_threshold_only_termination_rate": 0.0,
                "blocked_contact_only_termination_rate": 0.0,
                "force_and_blocked_termination_rate": 0.0,
                "documented_force_jam_rate": 0.0,
            },
        ),
        "fixed_impedance_rl": _appendix_suite_payload(
            "fixed_impedance_rl",
            success_rate=0.4,
            jam_rate=0.3,
            final_distance_m=0.0022,
            peak_force_n=1.6,
            p95_force_n=1.95,
            contact_steps=40.0,
            diagnostic_over_profile_rates={
                "jam_rate": 0.3,
                "force_threshold_termination_rate": 0.12,
                "blocked_contact_termination_rate": 0.20,
                "force_threshold_only_termination_rate": 0.07,
                "blocked_contact_only_termination_rate": 0.15,
                "force_and_blocked_termination_rate": 0.05,
                "documented_force_jam_rate": 0.04,
            },
        ),
        "repaired_mainline_bc_to_ppo": _appendix_suite_payload(
            "repaired_mainline_bc_to_ppo",
            success_rate=0.98,
            jam_rate=0.02,
            final_distance_m=0.0010,
            peak_force_n=0.98,
            p95_force_n=1.24,
            contact_steps=30.0,
            diagnostic_over_profile_rates={
                "jam_rate": 0.02,
                "force_threshold_termination_rate": 0.01,
                "blocked_contact_termination_rate": 0.01,
                "force_threshold_only_termination_rate": 0.01,
                "blocked_contact_only_termination_rate": 0.00,
                "force_and_blocked_termination_rate": 0.01,
                "documented_force_jam_rate": 0.01,
            },
        ),
        "dapg_lite_repaired_mainline": _appendix_suite_payload(
            "dapg_lite_repaired_mainline",
            success_rate=0.97,
            jam_rate=0.03,
            final_distance_m=0.0011,
            peak_force_n=1.02,
            p95_force_n=1.28,
            contact_steps=31.0,
            diagnostic_over_profile_rates={
                "jam_rate": 0.03,
                "force_threshold_termination_rate": 0.01,
                "blocked_contact_termination_rate": 0.02,
                "force_threshold_only_termination_rate": 0.01,
                "blocked_contact_only_termination_rate": 0.01,
                "force_and_blocked_termination_rate": 0.01,
                "documented_force_jam_rate": 0.01,
            },
        ),
    }
    benchmark_report = {
        "config": {
            "suite_names": [
                "bc_only_stable_r32_p32",
                "fixed_impedance_rl",
                "repaired_mainline_bc_to_ppo",
                "dapg_lite_repaired_mainline",
                "teacher_variable_variable__repaired_mainline",
                "teacher_variable_fixed__repaired_mainline",
                "teacher_pose_variable__repaired_mainline",
                "teacher_pose_fixed__repaired_mainline",
            ],
            "uncertainty_profiles": [
                "nominal",
                "tight_clearance",
                "high_friction",
                "offset_bias",
                "noisy_force",
            ],
        },
        "handcrafted_results": {},
        "learned_results": {**diagnostic_suites, **teacher_suites},
    }
    fixed_impedance_override = {
        "config": {"suite_name": "fixed_impedance_rl_stable_r32_p32"},
        **_appendix_suite_payload(
            "fixed_impedance_rl_stable_r32_p32",
            success_rate=0.91,
            jam_rate=0.08,
            final_distance_m=0.0014,
            peak_force_n=1.32,
            p95_force_n=1.66,
            contact_steps=37.0,
            diagnostic_over_profile_rates={
                "jam_rate": 0.08,
                "force_threshold_termination_rate": 0.03,
                "blocked_contact_termination_rate": 0.06,
                "force_threshold_only_termination_rate": 0.02,
                "blocked_contact_only_termination_rate": 0.05,
                "force_and_blocked_termination_rate": 0.01,
                "documented_force_jam_rate": 0.02,
            },
        ),
    }
    benchmark_path = tmp_path / "appendix_benchmark.json"
    fixed_override_path = tmp_path / "appendix_fixed.json"
    benchmark_path.write_text(json.dumps(benchmark_report), encoding="utf-8")
    fixed_override_path.write_text(json.dumps(fixed_impedance_override), encoding="utf-8")
    return benchmark_path, fixed_override_path


def test_build_3dof_appendix_table_export_includes_teacher_and_diagnostics(
    tmp_path: Path,
) -> None:
    module = _load_paper_tables_module()
    benchmark_path, fixed_override_path = _write_appendix_sample_artifacts(tmp_path)

    export = module.build_3dof_appendix_table_export(
        benchmark_report_path=benchmark_path,
        fixed_impedance_report_path=fixed_override_path,
    )

    assert export["teacher_suite_order"] == [
        "teacher_variable_variable__repaired_mainline",
        "teacher_variable_fixed__repaired_mainline",
        "teacher_pose_variable__repaired_mainline",
        "teacher_pose_fixed__repaired_mainline",
    ]
    assert export["diagnostic_suite_order"] == [
        "bc_only_stable_r32_p32",
        "repaired_mainline_bc_to_ppo",
        "dapg_lite_repaired_mainline",
        "fixed_impedance_rl_stable_r32_p32",
    ]
    teacher_row = export["teacher_rows"][0]
    assert teacher_row["teacher_motion_rule"] == "contact_aware_variable_motion"
    assert teacher_row["teacher_impedance_rule"] == "contact_aware_variable_impedance"
    assert teacher_row["five_profile_mean"]["success_rate"] == pytest.approx(0.99)

    diagnostic_row = next(
        row
        for row in export["diagnostic_rows"]
        if row["suite_name"] == "fixed_impedance_rl_stable_r32_p32"
    )
    assert diagnostic_row["diagnostics"]["force_threshold_termination_rate"] == pytest.approx(0.03)
    assert diagnostic_row["diagnostics"]["blocked_contact_termination_rate"] == pytest.approx(0.06)
    assert diagnostic_row["diagnostics"]["documented_force_jam_rate"] == pytest.approx(0.02)

    markdown = module.render_3dof_appendix_table_markdown(export)
    assert "## Teacher Ablation" in markdown
    assert "## Termination Diagnostics" in markdown
    assert "documented_force_jam_rate" in markdown


def test_build_3dof_appendix_table_export_rejects_missing_teacher_suite(
    tmp_path: Path,
) -> None:
    module = _load_paper_tables_module()
    benchmark_path, fixed_override_path = _write_appendix_sample_artifacts(tmp_path)
    benchmark_report = json.loads(benchmark_path.read_text(encoding="utf-8"))
    del benchmark_report["learned_results"]["teacher_pose_fixed__repaired_mainline"]
    benchmark_path.write_text(json.dumps(benchmark_report), encoding="utf-8")

    with pytest.raises(ValueError, match="teacher_pose_fixed__repaired_mainline"):
        module.build_3dof_appendix_table_export(
            benchmark_report_path=benchmark_path,
            fixed_impedance_report_path=fixed_override_path,
        )


def test_build_3dof_appendix_table_export_rejects_missing_diagnostic_metric(
    tmp_path: Path,
) -> None:
    module = _load_paper_tables_module()
    benchmark_path, fixed_override_path = _write_appendix_sample_artifacts(tmp_path)
    benchmark_report = json.loads(benchmark_path.read_text(encoding="utf-8"))
    del benchmark_report["learned_results"]["repaired_mainline_bc_to_ppo"]["five_profile_mean"][
        "force_threshold_termination_rate_mean_over_profiles"
    ]
    benchmark_path.write_text(json.dumps(benchmark_report), encoding="utf-8")

    with pytest.raises(ValueError, match="force_threshold_termination_rate"):
        module.build_3dof_appendix_table_export(
            benchmark_report_path=benchmark_path,
            fixed_impedance_report_path=fixed_override_path,
        )


def test_export_3dof_appendix_table_writes_json_and_markdown(tmp_path: Path) -> None:
    module = _load_paper_tables_module()
    benchmark_path, fixed_override_path = _write_appendix_sample_artifacts(tmp_path)

    json_path, markdown_path = module.export_3dof_appendix_table(
        benchmark_report_path=benchmark_path,
        fixed_impedance_report_path=fixed_override_path,
        output_dir=tmp_path,
        stem="appendix_table",
    )

    exported_json = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")

    assert json_path.name == "appendix_table.json"
    assert markdown_path.name == "appendix_table.md"
    assert exported_json["teacher_rows"][0]["suite_name"] == "teacher_variable_variable__repaired_mainline"
    assert "teacher_variable_fixed__repaired_mainline" in markdown
    assert "force_and_blocked_termination_rate" in markdown


def test_build_3dof_appendix_table_export_accepts_stable_fixed_suite_in_main_benchmark(
    tmp_path: Path,
) -> None:
    module = _load_paper_tables_module()
    benchmark_path, _ = _write_appendix_sample_artifacts(tmp_path)
    benchmark_report = json.loads(benchmark_path.read_text(encoding="utf-8"))
    benchmark_report["config"]["suite_names"] = [
        "bc_only_stable_r32_p32",
        "fixed_impedance_rl_stable_r32_p32",
        "repaired_mainline_bc_to_ppo",
        "dapg_lite_repaired_mainline",
        "teacher_variable_variable__repaired_mainline",
        "teacher_variable_fixed__repaired_mainline",
        "teacher_pose_variable__repaired_mainline",
        "teacher_pose_fixed__repaired_mainline",
    ]
    benchmark_report["learned_results"]["fixed_impedance_rl_stable_r32_p32"] = benchmark_report[
        "learned_results"
    ].pop("fixed_impedance_rl")
    benchmark_report["learned_results"]["fixed_impedance_rl_stable_r32_p32"][
        "suite_run_kwargs"
    ]["suite_name"] = "fixed_impedance_rl_stable_r32_p32"
    benchmark_path.write_text(json.dumps(benchmark_report), encoding="utf-8")

    export = module.build_3dof_appendix_table_export(
        benchmark_report_path=benchmark_path,
    )

    assert export["diagnostic_suite_order"] == [
        "bc_only_stable_r32_p32",
        "repaired_mainline_bc_to_ppo",
        "dapg_lite_repaired_mainline",
        "fixed_impedance_rl_stable_r32_p32",
    ]


def test_manuscript_section_order_matches_upgraded_evidence_hierarchy() -> None:
    manuscript = _require_test_asset(
        (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "paper_manuscript_only_sim_final.tex"
        ),
        "paper manuscript asset",
    ).read_text(encoding="utf-8")

    expected_sections = [
        "Learnability Question and Evidence Boundary",
        "Mechanics and Interface Formalization",
        "Main Benchmark: Coverage Matters More than Algorithm Choice",
        "Factorized Causal Study: Demonstration Support Reopens Contact, but Reset and Budget Effects Are Protocol-Sensitive",
        "High-Friction Role of Variable Impedance",
        "Classical Anchors and External Validity",
    ]
    positions = [manuscript.index(section_title) for section_title in expected_sections]
    assert positions == sorted(positions)


def test_external_validity_docs_reference_pose_perturbation_study() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    manuscript = _require_test_asset(
        repo_root / "docs" / "paper_manuscript_only_sim_final.tex",
        "paper manuscript asset",
    ).read_text(encoding="utf-8")
    freeze_note = _require_test_asset(
        repo_root / "docs" / "paper_results_freeze.md",
        "paper results freeze note",
    ).read_text(encoding="utf-8")
    readme = (repo_root / "README.md").read_text(encoding="utf-8")

    assert "dedicated pose-perturbation study" in manuscript
    assert "we do not yet include hardware validation, full 6D orientation perturbations, or a dedicated" not in manuscript
    assert "pose_perturbation_study" in freeze_note
    assert "pose_perturbation_study" in readme


def test_submission_main_table_references_stage4_statistics_artifacts() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    checked_paths = [
        repo_root / "README.md",
        repo_root / "docs" / "paper_results_freeze.md",
        repo_root / "docs" / "paper_only_sim_figure_asset_manifest.md",
        repo_root / "scripts" / "export_paper_only_sim_figure2.py",
    ]
    existing_paths = []
    for path in checked_paths:
        if path.name == "paper_only_sim_figure_asset_manifest.md":
            fallback_path = path.with_name("figure_asset_manifest.md")
            if fallback_path.exists():
                existing_paths.append(fallback_path)
                continue
        existing_paths.append(
            _require_test_asset(path, f"paper-facing asset '{path.name}'")
        )
    combined_text = "\n".join(path.read_text(encoding="utf-8") for path in existing_paths)

    assert "three_dof_benchmark_paper9suite_full5profile_bc32x32_stage4_20260429.json" in combined_text
    assert "three_dof_statistics_report_stage4_20260429.json" in combined_text
    assert "table_3dof_paper_benchmark_stage4_20260429" in combined_text
    assert "stage4_with_classical" not in combined_text
