from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np


SUITE_DISPLAY_NAMES = {
    "ppo_no_bc": "PPO w/o BC",
    "bc_only_stable_r32_p32": "BC-only (stable 32/32)",
    "fixed_impedance_rl": "Fixed-impedance RL",
    "fixed_impedance_rl_stable_r32_p32": "Fixed-impedance RL (stable BC 32/32)",
    "repaired_mainline_bc_to_ppo": "BC -> PPO",
    "dapg_lite_repaired_mainline": "DAPG-lite",
    "teacher_variable_variable__repaired_mainline": "Teacher: variable motion + variable impedance",
    "teacher_variable_fixed__repaired_mainline": "Teacher: variable motion + fixed impedance",
    "teacher_pose_variable__repaired_mainline": "Teacher: pose motion + variable impedance",
    "teacher_pose_fixed__repaired_mainline": "Teacher: pose motion + fixed impedance",
    "dapg_lite_contact_old__reset_coverage_collapse": "DAPG-lite old reset (coverage collapse)",
    "dapg_lite_contact_old__reset_repaired": "DAPG-lite old reset (repaired)",
    "dapg_lite_contact_new__reset_coverage_collapse": "DAPG-lite new reset (coverage collapse)",
    "dapg_lite_contact_new__reset_repaired": "DAPG-lite new reset (repaired)",
}

HANDCRAFTED_DISPLAY_NAMES = {
    "pose_only": "Pose-only",
    "fixed_impedance": "Handcrafted fixed impedance",
    "variable_impedance": "Handcrafted variable impedance",
    "hybrid_position_force": "Hybrid position-force",
    "compliant_search": "Compliant search",
    "tuned_impedance": "Hand-tuned impedance",
}

PROFILE_EQUIVALENCE_CLASSES = (
    {
        "class_name": "baseline",
        "profiles": ("nominal", "tight_clearance", "offset_bias"),
        "pressure_source": "No extra active pressure under current 3DoF semantics.",
        "design_rationale": (
            "offset_bias is absorbed by the relative observation coordinate frame",
            "tight_clearance only activates under lateral overflow",
        ),
    },
    {
        "class_name": "high_friction",
        "profiles": ("high_friction",),
        "pressure_source": "Force-impedance coupling.",
        "design_rationale": (
            "higher wall friction changes the contact force response",
        ),
    },
    {
        "class_name": "noisy_force",
        "profiles": ("noisy_force",),
        "pressure_source": "Force-sensor uncertainty.",
        "design_rationale": (
            "force noise perturbs the observed contact signal",
        ),
    },
)

ANNOTATION_SUMMARY = (
    "Five nominal eval profiles collapse to three effective pressure classes "
    "in this 3DoF environment design."
)

TABLE_METRICS = {
    "success_rate": {
        "raw_key": "success_rate",
        "aggregate_mean_key": "success_rate_mean",
        "aggregate_std_key": "success_rate_std",
        "over_profile_mean_key": "success_rate_mean_over_profiles",
        "over_profile_std_key": "success_rate_std_over_profiles",
    },
    "jam_rate": {
        "raw_key": "jam_rate",
        "aggregate_mean_key": "jam_rate_mean",
        "aggregate_std_key": "jam_rate_std",
        "over_profile_mean_key": "jam_rate_mean_over_profiles",
        "over_profile_std_key": "jam_rate_std_over_profiles",
    },
    "mean_final_distance_mm": {
        "raw_key": "mean_final_distance",
        "aggregate_mean_key": "mean_final_distance_mean",
        "aggregate_std_key": "mean_final_distance_std",
        "over_profile_mean_key": "mean_final_distance_mean_over_profiles",
        "over_profile_std_key": "mean_final_distance_std_over_profiles",
        "scale": 1000.0,
    },
    "mean_peak_contact_force_n": {
        "raw_key": "mean_peak_contact_force",
        "aggregate_mean_key": "mean_peak_contact_force_mean",
        "aggregate_std_key": "mean_peak_contact_force_std",
        "over_profile_mean_key": "mean_peak_contact_force_mean_over_profiles",
        "over_profile_std_key": "mean_peak_contact_force_std_over_profiles",
    },
    "p95_peak_contact_force_n": {
        "raw_key": "p95_peak_contact_force",
        "aggregate_mean_key": "p95_peak_contact_force_mean",
        "aggregate_std_key": "p95_peak_contact_force_std",
        "over_profile_mean_key": "p95_peak_contact_force_mean_over_profiles",
        "over_profile_std_key": "p95_peak_contact_force_std_over_profiles",
    },
    "mean_contact_steps": {
        "raw_key": "mean_contact_steps",
        "aggregate_mean_key": "mean_contact_steps_mean",
        "aggregate_std_key": "mean_contact_steps_std",
        "over_profile_mean_key": "mean_contact_steps_mean_over_profiles",
        "over_profile_std_key": "mean_contact_steps_std_over_profiles",
    },
}

SUPPORT_STATISTICS_METRICS = {
    "support_coverage_index": {
        "display_name": "Support Coverage Index",
    },
    "support_cell_coverage": {
        "display_name": "Support Cell Coverage",
    },
}

APPENDIX_TEACHER_SUITE_ORDER = (
    "teacher_variable_variable__repaired_mainline",
    "teacher_variable_fixed__repaired_mainline",
    "teacher_pose_variable__repaired_mainline",
    "teacher_pose_fixed__repaired_mainline",
)

APPENDIX_TEACHER_TABLE_METRICS = {
    metric_name: TABLE_METRICS[metric_name]
    for metric_name in (
        "success_rate",
        "jam_rate",
        "mean_final_distance_mm",
        "mean_peak_contact_force_n",
        "mean_contact_steps",
    )
}

APPENDIX_TERMINATION_DIAGNOSTIC_METRICS = {
    "jam_rate": TABLE_METRICS["jam_rate"],
    "force_threshold_termination_rate": {
        "raw_key": "force_threshold_exceeded",
        "aggregate_mean_key": "force_threshold_termination_rate_mean",
        "aggregate_std_key": "force_threshold_termination_rate_std",
        "over_profile_mean_key": "force_threshold_termination_rate_mean_over_profiles",
        "over_profile_std_key": "force_threshold_termination_rate_std_over_profiles",
    },
    "blocked_contact_termination_rate": {
        "raw_key": "blocked_contact_failure",
        "aggregate_mean_key": "blocked_contact_termination_rate_mean",
        "aggregate_std_key": "blocked_contact_termination_rate_std",
        "over_profile_mean_key": "blocked_contact_termination_rate_mean_over_profiles",
        "over_profile_std_key": "blocked_contact_termination_rate_std_over_profiles",
    },
    "force_threshold_only_termination_rate": {
        "raw_key": "force_threshold_only",
        "aggregate_mean_key": "force_threshold_only_termination_rate_mean",
        "aggregate_std_key": "force_threshold_only_termination_rate_std",
        "over_profile_mean_key": "force_threshold_only_termination_rate_mean_over_profiles",
        "over_profile_std_key": "force_threshold_only_termination_rate_std_over_profiles",
    },
    "blocked_contact_only_termination_rate": {
        "raw_key": "blocked_contact_only",
        "aggregate_mean_key": "blocked_contact_only_termination_rate_mean",
        "aggregate_std_key": "blocked_contact_only_termination_rate_std",
        "over_profile_mean_key": "blocked_contact_only_termination_rate_mean_over_profiles",
        "over_profile_std_key": "blocked_contact_only_termination_rate_std_over_profiles",
    },
    "force_and_blocked_termination_rate": {
        "raw_key": "force_and_blocked",
        "aggregate_mean_key": "force_and_blocked_termination_rate_mean",
        "aggregate_std_key": "force_and_blocked_termination_rate_std",
        "over_profile_mean_key": "force_and_blocked_termination_rate_mean_over_profiles",
        "over_profile_std_key": "force_and_blocked_termination_rate_std_over_profiles",
    },
    "documented_force_jam_rate": {
        "raw_key": "meets_documented_force_jam",
        "aggregate_mean_key": "documented_force_jam_rate_mean",
        "aggregate_std_key": "documented_force_jam_rate_std",
        "over_profile_mean_key": "documented_force_jam_rate_mean_over_profiles",
        "over_profile_std_key": "documented_force_jam_rate_std_over_profiles",
    },
}

APPENDIX_DIAGNOSTIC_SUITE_ORDER = (
    "bc_only_stable_r32_p32",
    "repaired_mainline_bc_to_ppo",
    "dapg_lite_repaired_mainline",
)

DEFAULT_SELECTED_COMPARISONS = (
    {
        "reference_suite": "bc_only_stable_r32_p32",
        "candidate_suite": "repaired_mainline_bc_to_ppo",
        "metric": "success_rate",
    },
    {
        "reference_suite": "bc_only_stable_r32_p32",
        "candidate_suite": "dapg_lite_repaired_mainline",
        "metric": "success_rate",
    },
    {
        "reference_suite": "repaired_mainline_bc_to_ppo",
        "candidate_suite": "fixed_impedance_rl_stable_r32_p32",
        "metric": "success_rate",
    },
)

BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_CONFIDENCE = 0.95
RECOMMENDED_TRAINING_SEED_MIN = 5
RECOMMENDED_TRAINING_SEED_MAX = 10
RECOMMENDED_EPISODES_PER_SEED_PROFILE_MIN = 100
CEILING_SATURATION_THRESHOLD = 0.98
CEILING_NEGLIGIBLE_GAP = 0.01
PRACTICALLY_SMALL_GAP = 0.03


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _m_to_mm(value_m: float) -> float:
    return float(value_m) * 1000.0


def _scaled_value(value: Any, spec: dict[str, Any]) -> float:
    return float(value) * float(spec.get("scale", 1.0))


def _extract_over_profile_metrics(raw: dict[str, Any]) -> dict[str, float]:
    return {
        metric_name: _scaled_value(raw[spec["over_profile_mean_key"]], spec)
        for metric_name, spec in TABLE_METRICS.items()
    }


def _extract_profile_metrics(raw: dict[str, Any]) -> dict[str, float]:
    return {
        metric_name: _scaled_value(raw[spec["aggregate_mean_key"]], spec)
        for metric_name, spec in TABLE_METRICS.items()
    }


def _extract_metric_values(
    raw: dict[str, Any],
    metric_specs: dict[str, dict[str, Any]],
    *,
    over_profile: bool,
    context_label: str,
) -> dict[str, float]:
    values: dict[str, float] = {}
    for metric_name, spec in metric_specs.items():
        key_name = (
            spec["over_profile_mean_key"] if over_profile else spec["aggregate_mean_key"]
        )
        if key_name not in raw:
            raise ValueError(f"Missing appendix metric '{metric_name}' in {context_label}.")
        values[metric_name] = _scaled_value(raw[key_name], spec)
    return values


def _mean_metric_dicts(metric_dicts: list[dict[str, float]]) -> dict[str, float]:
    if not metric_dicts:
        raise ValueError("Cannot average an empty metric set.")
    metric_names = metric_dicts[0].keys()
    return {
        metric_name: float(
            sum(metric[metric_name] for metric in metric_dicts) / len(metric_dicts)
        )
        for metric_name in metric_names
    }


def _build_effective_pressure_classes(
    eval_results: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    effective_classes: dict[str, dict[str, Any]] = {}
    for class_spec in PROFILE_EQUIVALENCE_CLASSES:
        profiles = list(class_spec["profiles"])
        profile_metrics = [
            _extract_profile_metrics(eval_results[profile_name]["aggregate"])
            for profile_name in profiles
        ]
        effective_classes[str(class_spec["class_name"])] = {
            "profiles": profiles,
            "pressure_source": str(class_spec["pressure_source"]),
            "design_rationale": list(class_spec["design_rationale"]),
            "metrics": _mean_metric_dicts(profile_metrics),
        }
    return effective_classes


def _build_profile_rows(eval_results: dict[str, Any]) -> dict[str, dict[str, Any]]:
    profile_to_class = {
        profile_name: str(class_spec["class_name"])
        for class_spec in PROFILE_EQUIVALENCE_CLASSES
        for profile_name in class_spec["profiles"]
    }
    profile_rows: dict[str, dict[str, Any]] = {}
    for profile_name, payload in eval_results.items():
        profile_rows[str(profile_name)] = {
            "equivalence_class": profile_to_class[str(profile_name)],
            "metrics": _extract_profile_metrics(payload["aggregate"]),
        }
    return profile_rows


def _annotation_payload() -> dict[str, Any]:
    return {
        "summary": ANNOTATION_SUMMARY,
        "equivalence_classes": [
            {
                "class_name": str(class_spec["class_name"]),
                "profiles": list(class_spec["profiles"]),
                "pressure_source": str(class_spec["pressure_source"]),
                "design_rationale": list(class_spec["design_rationale"]),
            }
            for class_spec in PROFILE_EQUIVALENCE_CLASSES
        ],
    }


def _resolve_suite_payloads(
    *,
    benchmark_report_path: Path,
    fixed_impedance_report_path: Path | None = None,
) -> tuple[list[str], list[dict[str, Any]], dict[str, Any]]:
    benchmark_report_path = Path(benchmark_report_path)
    raw_benchmark = _load_json(benchmark_report_path)
    raw_fixed_impedance = (
        _load_json(Path(fixed_impedance_report_path))
        if fixed_impedance_report_path is not None
        else None
    )

    raw_suite_order = list(raw_benchmark["config"]["suite_names"])
    suite_order: list[str] = []
    suite_payloads: list[dict[str, Any]] = []
    for original_suite_name in raw_suite_order:
        if original_suite_name == "fixed_impedance_rl" and raw_fixed_impedance is not None:
            suite_name = str(raw_fixed_impedance["config"]["suite_name"])
            suite_payload = raw_fixed_impedance
            source_artifact = Path(fixed_impedance_report_path)
            replaces_main_suite = original_suite_name
        else:
            suite_name = original_suite_name
            if original_suite_name not in raw_benchmark["learned_results"]:
                raise ValueError(
                    f"Missing learned suite '{original_suite_name}' in benchmark artifact."
                )
            suite_payload = raw_benchmark["learned_results"][original_suite_name]
            source_artifact = benchmark_report_path
            replaces_main_suite = None

        suite_order.append(suite_name)
        suite_payloads.append(
            {
                "suite_name": suite_name,
                "display_name": SUITE_DISPLAY_NAMES.get(suite_name, suite_name),
                "source_artifact": source_artifact,
                "suite_payload": suite_payload,
                "five_profile_mean": suite_payload["five_profile_mean"],
                "eval_results": suite_payload["eval_results"],
                "replaces_main_suite": replaces_main_suite,
            }
        )
    return suite_order, suite_payloads, raw_benchmark


def _build_five_profile_mean_from_eval_results(
    eval_results: dict[str, Any],
) -> dict[str, float]:
    five_profile_mean: dict[str, float] = {}
    for metric_spec in TABLE_METRICS.values():
        values = np.asarray(
            [
                float(profile_payload["aggregate"][metric_spec["aggregate_mean_key"]])
                for profile_payload in eval_results.values()
            ],
            dtype=np.float64,
        )
        five_profile_mean[metric_spec["over_profile_mean_key"]] = float(np.mean(values))
        five_profile_mean[metric_spec["over_profile_std_key"]] = float(np.std(values))
    return five_profile_mean


def _resolve_handcrafted_payloads(
    *,
    raw_benchmark: dict[str, Any],
    benchmark_report_path: Path,
) -> tuple[list[str], list[dict[str, Any]]]:
    raw_handcrafted_results = raw_benchmark.get("handcrafted_results", {})
    if not raw_handcrafted_results:
        return [], []

    configured_policy_order = list(
        raw_benchmark.get("config", {}).get("handcrafted_policy_names", [])
    )
    if configured_policy_order:
        handcrafted_policy_order = configured_policy_order
    else:
        first_profile_payload = next(iter(raw_handcrafted_results.values()), {})
        handcrafted_policy_order = list(first_profile_payload.keys())

    handcrafted_payloads: list[dict[str, Any]] = []
    for policy_name in handcrafted_policy_order:
        eval_results = {
            str(profile_name): profile_payload[policy_name]
            for profile_name, profile_payload in raw_handcrafted_results.items()
            if policy_name in profile_payload
        }
        if not eval_results:
            continue
        handcrafted_payloads.append(
            {
                "suite_name": policy_name,
                "display_name": HANDCRAFTED_DISPLAY_NAMES.get(policy_name, policy_name),
                "source_artifact": benchmark_report_path,
                "five_profile_mean": _build_five_profile_mean_from_eval_results(
                    eval_results
                ),
                "eval_results": eval_results,
                "replaces_main_suite": None,
            }
        )
    return handcrafted_policy_order, handcrafted_payloads


def _collect_seed_metric_samples(
    eval_results: dict[str, Any],
    *,
    metric_name: str,
) -> tuple[list[int], list[float]]:
    spec = TABLE_METRICS[metric_name]
    profile_names = list(eval_results.keys())
    seed_maps: list[dict[int, dict[str, Any]]] = []
    for profile_name in profile_names:
        seed_maps.append(
            {
                int(item["seed"]): item
                for item in eval_results[profile_name]["per_seed"]
            }
        )

    common_seeds = sorted(set.intersection(*(set(seed_map) for seed_map in seed_maps)))
    samples: list[float] = []
    for seed in common_seeds:
        profile_values = [
            _scaled_value(seed_map[seed][spec["raw_key"]], spec) for seed_map in seed_maps
        ]
        samples.append(float(np.mean(np.asarray(profile_values, dtype=np.float64))))
    return common_seeds, samples


def _collect_profile_metric_samples(
    profile_payload: dict[str, Any],
    *,
    metric_name: str,
) -> list[float]:
    spec = TABLE_METRICS[metric_name]
    return [
        _scaled_value(item[spec["raw_key"]], spec) for item in profile_payload["per_seed"]
    ]


def _collect_support_seed_metric_samples(
    eval_results: dict[str, Any],
    *,
    metric_name: str,
) -> tuple[list[int], list[float]] | None:
    profile_names = list(eval_results.keys())
    seed_maps: list[dict[int, dict[str, Any]]] = []
    for profile_name in profile_names:
        per_seed = eval_results[profile_name].get("per_seed", [])
        if not per_seed:
            return None
        if any(
            "support_metrics" not in item or metric_name not in item["support_metrics"]
            for item in per_seed
        ):
            return None
        seed_maps.append({int(item["seed"]): item for item in per_seed})

    common_seeds = sorted(set.intersection(*(set(seed_map) for seed_map in seed_maps)))
    samples: list[float] = []
    for seed in common_seeds:
        profile_values = [
            float(seed_map[seed]["support_metrics"][metric_name]) for seed_map in seed_maps
        ]
        samples.append(float(np.mean(np.asarray(profile_values, dtype=np.float64))))
    return common_seeds, samples


def _collect_support_profile_metric_samples(
    profile_payload: dict[str, Any],
    *,
    metric_name: str,
) -> list[float] | None:
    per_seed = profile_payload.get("per_seed", [])
    if not per_seed:
        return None
    if any(
        "support_metrics" not in item or metric_name not in item["support_metrics"]
        for item in per_seed
    ):
        return None
    return [float(item["support_metrics"][metric_name]) for item in per_seed]


def _bootstrap_ci(
    values: list[float] | np.ndarray,
    *,
    confidence: float = BOOTSTRAP_CONFIDENCE,
    resamples: int = BOOTSTRAP_RESAMPLES,
    rng_seed: int = 0,
) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0:
        raise ValueError("Cannot bootstrap an empty value set.")
    mean_value = float(np.mean(array))
    if array.size == 1:
        return {"lower": mean_value, "upper": mean_value}

    rng = np.random.default_rng(rng_seed)
    bootstrap_indices = rng.integers(0, array.size, size=(resamples, array.size))
    bootstrap_means = np.mean(array[bootstrap_indices], axis=1)
    alpha = 1.0 - confidence
    return {
        "lower": float(np.quantile(bootstrap_means, alpha / 2.0)),
        "upper": float(np.quantile(bootstrap_means, 1.0 - alpha / 2.0)),
    }


def _build_metric_statistics(
    values: list[float],
    *,
    rng_seed: int = 0,
) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(np.mean(array)),
        "std": float(np.std(array)),
        "ci": _bootstrap_ci(array, rng_seed=rng_seed),
        "num_samples": int(array.size),
    }


def _paired_bootstrap_difference_ci(
    reference_values: list[float],
    candidate_values: list[float],
    *,
    confidence: float = BOOTSTRAP_CONFIDENCE,
    resamples: int = BOOTSTRAP_RESAMPLES,
    rng_seed: int = 0,
) -> dict[str, float]:
    reference = np.asarray(reference_values, dtype=np.float64)
    candidate = np.asarray(candidate_values, dtype=np.float64)
    if reference.shape != candidate.shape:
        raise ValueError("Paired comparisons require matching sample shapes.")
    differences = candidate - reference
    if differences.size == 1:
        mean_difference = float(np.mean(differences))
        return {"lower": mean_difference, "upper": mean_difference}

    rng = np.random.default_rng(rng_seed)
    bootstrap_indices = rng.integers(0, differences.size, size=(resamples, differences.size))
    bootstrap_means = np.mean(differences[bootstrap_indices], axis=1)
    alpha = 1.0 - confidence
    return {
        "lower": float(np.quantile(bootstrap_means, alpha / 2.0)),
        "upper": float(np.quantile(bootstrap_means, 1.0 - alpha / 2.0)),
    }


def _paired_sign_flip_p_value(differences: np.ndarray) -> float:
    if differences.size == 0 or np.allclose(differences, 0.0):
        return 1.0

    observed = abs(float(np.mean(differences)))
    if differences.size <= 12:
        signs = np.asarray(
            list(itertools.product((-1.0, 1.0), repeat=differences.size)),
            dtype=np.float64,
        )
    else:
        rng = np.random.default_rng(0)
        signs = rng.choice(
            np.asarray([-1.0, 1.0], dtype=np.float64),
            size=(20000, differences.size),
        )
    null_means = np.abs(np.mean(signs * differences, axis=1))
    return float(np.mean(null_means >= observed - 1e-12))


def _build_effect_size(
    metric_name: str,
    reference_values: list[float],
    candidate_values: list[float],
) -> dict[str, Any]:
    reference = np.asarray(reference_values, dtype=np.float64)
    candidate = np.asarray(candidate_values, dtype=np.float64)
    absolute_difference = float(np.mean(candidate) - np.mean(reference))
    pooled_variance = 0.0
    if reference.size + candidate.size > 2:
        pooled_variance = float(
            (
                (reference.size - 1) * np.var(reference)
                + (candidate.size - 1) * np.var(candidate)
            )
            / max(reference.size + candidate.size - 2, 1)
        )
    pooled_std = float(np.sqrt(max(pooled_variance, 0.0)))
    standardized_difference = (
        None if pooled_std <= 1e-12 else float(absolute_difference / pooled_std)
    )

    effect = {
        "effect_type": "paired_mean_difference",
        "absolute_mean_difference": absolute_difference,
        "standardized_mean_difference": standardized_difference,
    }
    if metric_name == "success_rate":
        reference_failure_rate = max(0.0, 1.0 - float(np.mean(reference)))
        candidate_failure_rate = max(0.0, 1.0 - float(np.mean(candidate)))
        effect.update(
            {
                "effect_type": "ceiling_aware_success_rate_gap",
                "reference_failure_rate": reference_failure_rate,
                "candidate_failure_rate": candidate_failure_rate,
                "failure_rate_difference": candidate_failure_rate - reference_failure_rate,
                "remaining_error_ratio": (
                    None
                    if reference_failure_rate <= 1e-12
                    else float(candidate_failure_rate / reference_failure_rate)
                ),
            }
        )
    return effect


def _classify_practical_difference(
    metric_name: str,
    reference_mean: float,
    candidate_mean: float,
    *,
    p_value: float,
) -> tuple[str, str]:
    absolute_gap = abs(candidate_mean - reference_mean)
    if metric_name == "success_rate" and max(reference_mean, candidate_mean) >= CEILING_SATURATION_THRESHOLD:
        if absolute_gap <= CEILING_NEGLIGIBLE_GAP:
            return (
                "negligible under ceiling saturation",
                "The success-rate gap stays within a 0.01 band on a ceiling-saturated protocol, so the difference is negligible under ceiling saturation.",
            )
        if absolute_gap <= PRACTICALLY_SMALL_GAP:
            if p_value < 0.05:
                return (
                    "statistically distinguishable but practically small",
                    "The success-rate gap is statistically detectable, but on a ceiling-saturated protocol its practical effect remains small.",
                )
            return (
                "negligible under this protocol",
                "The success-rate gap is small relative to the ceiling-saturated operating regime, so it is negligible under this protocol.",
            )
        return (
            "materially different",
            "The success-rate gap is too large to dismiss as a ceiling-saturation artifact and should be treated as materially different.",
        )

    if absolute_gap <= PRACTICALLY_SMALL_GAP:
        if p_value < 0.05:
            return (
                "statistically distinguishable but practically small",
                "The measured gap is statistically detectable, but its magnitude remains practically small under this protocol.",
            )
        return (
            "negligible under this protocol",
            "The measured gap is small enough to be negligible under this protocol.",
        )
    return (
        "materially different",
        "The measured gap is large enough to be treated as materially different under this protocol.",
    )


def _build_selected_comparisons(
    suite_statistics: dict[str, Any],
) -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    for index, comparison_spec in enumerate(DEFAULT_SELECTED_COMPARISONS):
        reference_suite = comparison_spec["reference_suite"]
        candidate_suite = comparison_spec["candidate_suite"]
        metric_name = comparison_spec["metric"]
        if reference_suite not in suite_statistics or candidate_suite not in suite_statistics:
            continue

        reference_values = suite_statistics[reference_suite]["five_profile_seed_samples"][metric_name]
        candidate_values = suite_statistics[candidate_suite]["five_profile_seed_samples"][metric_name]
        if len(reference_values) != len(candidate_values):
            continue

        differences = np.asarray(candidate_values, dtype=np.float64) - np.asarray(
            reference_values, dtype=np.float64
        )
        reference_mean = float(np.mean(reference_values))
        candidate_mean = float(np.mean(candidate_values))
        p_value = _paired_sign_flip_p_value(differences)
        practical_interpretation, practical_note = _classify_practical_difference(
            metric_name,
            reference_mean,
            candidate_mean,
            p_value=p_value,
        )
        comparisons.append(
            {
                "comparison_id": f"{reference_suite}__vs__{candidate_suite}__{metric_name}",
                "reference_suite": reference_suite,
                "candidate_suite": candidate_suite,
                "metric": metric_name,
                "reference_mean": reference_mean,
                "candidate_mean": candidate_mean,
                "mean_difference": float(np.mean(differences)),
                "ci": _paired_bootstrap_difference_ci(
                    reference_values,
                    candidate_values,
                    rng_seed=index,
                ),
                "p_value": p_value,
                "effect_size": _build_effect_size(
                    metric_name,
                    reference_values,
                    candidate_values,
                ),
                "practical_interpretation": practical_interpretation,
                "practical_note": practical_note,
            }
        )
    return comparisons


def build_3dof_statistics_report(
    *,
    benchmark_report_path: Path,
    fixed_impedance_report_path: Path | None = None,
) -> dict[str, Any]:
    suite_order, suite_payloads, raw_benchmark = _resolve_suite_payloads(
        benchmark_report_path=benchmark_report_path,
        fixed_impedance_report_path=fixed_impedance_report_path,
    )

    suite_statistics: dict[str, Any] = {}
    for index, suite_payload in enumerate(suite_payloads):
        suite_name = suite_payload["suite_name"]
        eval_results = suite_payload["eval_results"]
        five_profile_seed_samples: dict[str, list[float]] = {}
        five_profile_statistics: dict[str, Any] = {}
        for metric_index, metric_name in enumerate(TABLE_METRICS):
            seed_order, samples = _collect_seed_metric_samples(
                eval_results,
                metric_name=metric_name,
            )
            five_profile_seed_samples[metric_name] = samples
            five_profile_statistics[metric_name] = _build_metric_statistics(
                samples,
                rng_seed=index * 100 + metric_index,
            )

        per_profile_statistics = {
            profile_name: {
                metric_name: _build_metric_statistics(
                    _collect_profile_metric_samples(profile_payload, metric_name=metric_name),
                    rng_seed=index * 1000 + profile_index * 100 + metric_index,
                )
                for metric_index, metric_name in enumerate(TABLE_METRICS)
            }
            for profile_index, (profile_name, profile_payload) in enumerate(eval_results.items())
        }

        suite_statistics[suite_name] = {
            "display_name": suite_payload["display_name"],
            "source_artifact": str(Path(suite_payload["source_artifact"]).resolve()),
            "seed_order": seed_order,
            "five_profile_seed_samples": five_profile_seed_samples,
            "five_profile_statistics": five_profile_statistics,
            "per_profile_statistics": per_profile_statistics,
        }
        five_profile_support_statistics: dict[str, Any] = {}
        per_profile_support_statistics: dict[str, Any] = {}
        support_metrics_available = True
        for metric_index, metric_name in enumerate(SUPPORT_STATISTICS_METRICS):
            seed_samples = _collect_support_seed_metric_samples(
                eval_results,
                metric_name=metric_name,
            )
            if seed_samples is None:
                support_metrics_available = False
                break
            _, samples = seed_samples
            five_profile_support_statistics[metric_name] = _build_metric_statistics(
                samples,
                rng_seed=index * 10_000 + metric_index,
            )

        if support_metrics_available:
            for profile_index, (profile_name, profile_payload) in enumerate(eval_results.items()):
                profile_stats: dict[str, Any] = {}
                for metric_index, metric_name in enumerate(SUPPORT_STATISTICS_METRICS):
                    samples = _collect_support_profile_metric_samples(
                        profile_payload,
                        metric_name=metric_name,
                    )
                    if samples is None:
                        support_metrics_available = False
                        break
                    profile_stats[metric_name] = _build_metric_statistics(
                        samples,
                        rng_seed=index * 100_000 + profile_index * 1_000 + metric_index,
                    )
                if not support_metrics_available:
                    break
                per_profile_support_statistics[profile_name] = profile_stats

        if support_metrics_available and five_profile_support_statistics:
            suite_statistics[suite_name]["five_profile_support_statistics"] = (
                five_profile_support_statistics
            )
            suite_statistics[suite_name]["per_profile_support_statistics"] = (
                per_profile_support_statistics
            )

    benchmark_config = raw_benchmark["config"]
    observed_seeds = benchmark_config.get("seeds", [])
    episodes_per_seed = int(benchmark_config.get("episodes_per_seed", 0))
    return {
        "report_name": "three_dof_statistics_report",
        "source_artifacts": {
            "benchmark_report": str(Path(benchmark_report_path).resolve()),
            "fixed_impedance_report": (
                str(Path(fixed_impedance_report_path).resolve())
                if fixed_impedance_report_path is not None
                else None
            ),
        },
        "sample_plan": {
            "recommended_training_seed_min": RECOMMENDED_TRAINING_SEED_MIN,
            "recommended_training_seed_max": RECOMMENDED_TRAINING_SEED_MAX,
            "recommended_episodes_per_seed_profile_min": RECOMMENDED_EPISODES_PER_SEED_PROFILE_MIN,
            "interval_method": "bootstrap",
            "paired_test_method": "paired sign-flip permutation",
            "confidence_level": BOOTSTRAP_CONFIDENCE,
        },
        "observed_sample_plan": {
            "num_training_seeds": len(observed_seeds),
            "episodes_per_seed": episodes_per_seed,
            "meets_recommended_seed_floor": len(observed_seeds) >= RECOMMENDED_TRAINING_SEED_MIN,
            "meets_recommended_episode_floor": (
                episodes_per_seed >= RECOMMENDED_EPISODES_PER_SEED_PROFILE_MIN
            ),
        },
        "suite_order": suite_order,
        "suite_statistics": suite_statistics,
        "selected_comparisons": _build_selected_comparisons(suite_statistics),
    }


def render_3dof_statistics_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 3DoF Statistics Report",
        "",
        f"Benchmark source: `{report['source_artifacts']['benchmark_report']}`",
        "",
        "## Sample Plan",
        "",
        f"- recommended training seeds: {report['sample_plan']['recommended_training_seed_min']} to {report['sample_plan']['recommended_training_seed_max']}",
        f"- recommended episodes per seed/profile: >= {report['sample_plan']['recommended_episodes_per_seed_profile_min']}",
        f"- observed training seeds: {report['observed_sample_plan']['num_training_seeds']}",
        f"- observed episodes per seed: {report['observed_sample_plan']['episodes_per_seed']}",
        "",
        "## Selected Comparisons",
        "",
    ]
    for comparison in report["selected_comparisons"]:
        reference_name = SUITE_DISPLAY_NAMES.get(
            comparison["reference_suite"], comparison["reference_suite"]
        )
        candidate_name = SUITE_DISPLAY_NAMES.get(
            comparison["candidate_suite"], comparison["candidate_suite"]
        )
        ci = comparison["ci"]
        lines.append(
            f"- {candidate_name} vs {reference_name} on {comparison['metric']}: "
            f"delta = {comparison['mean_difference']:.3f}, "
            f"95% CI [{ci['lower']:.3f}, {ci['upper']:.3f}], "
            f"p = {comparison['p_value']:.3f}, "
            f"{comparison['practical_interpretation']}."
        )

    support_suite_rows = [
        (
            suite_name,
            report["suite_statistics"][suite_name],
        )
        for suite_name in report["suite_order"]
        if suite_name in report["suite_statistics"]
        and "five_profile_support_statistics" in report["suite_statistics"][suite_name]
    ]
    if support_suite_rows:
        lines.extend(
            [
                "",
                "## Support Diagnostics",
                "",
                "| Suite | Support Coverage Index | Support Cell Coverage |",
                "| --- | --- | --- |",
            ]
        )
        for suite_name, suite_payload in support_suite_rows:
            display_name = SUITE_DISPLAY_NAMES.get(suite_name, suite_name)
            support_cells: list[str] = []
            for metric_name in SUPPORT_STATISTICS_METRICS:
                stats = suite_payload["five_profile_support_statistics"][metric_name]
                ci = stats["ci"]
                support_cells.append(
                    f"{stats['mean']:.3f} +- {stats['std']:.3f} "
                    f"(95% CI [{ci['lower']:.3f}, {ci['upper']:.3f}])"
                )
            lines.append(
                f"| {display_name} | {support_cells[0]} | {support_cells[1]} |"
            )
    return "\n".join(lines) + "\n"


def export_3dof_statistics_report(
    *,
    benchmark_report_path: Path,
    fixed_impedance_report_path: Path | None = None,
    output_dir: Path,
    stem: str = "three_dof_statistics_report",
) -> tuple[Path, Path]:
    report = build_3dof_statistics_report(
        benchmark_report_path=benchmark_report_path,
        fixed_impedance_report_path=fixed_impedance_report_path,
    )
    markdown = render_3dof_statistics_report_markdown(report)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown, encoding="utf-8")
    return json_path, markdown_path


def _suite_comparison_notes(
    suite_name: str,
    statistics_report: dict[str, Any] | None,
) -> list[str]:
    if statistics_report is None:
        return []
    notes: list[str] = []
    for comparison in statistics_report["selected_comparisons"]:
        if comparison["candidate_suite"] != suite_name:
            continue
        reference_name = SUITE_DISPLAY_NAMES.get(
            comparison["reference_suite"], comparison["reference_suite"]
        )
        notes.append(
            f"vs {reference_name} on {comparison['metric']}: {comparison['practical_interpretation']}."
        )
    return notes


def _build_suite_row(
    *,
    suite_name: str,
    display_name: str,
    source_artifact: Path,
    five_profile_mean: dict[str, Any],
    eval_results: dict[str, Any],
    replaces_main_suite: str | None = None,
    statistics_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "suite_name": suite_name,
        "display_name": display_name,
        "source_artifact": str(source_artifact.resolve()),
        "five_profile_mean": _extract_over_profile_metrics(five_profile_mean),
        "effective_pressure_classes": _build_effective_pressure_classes(eval_results),
        "per_profile": _build_profile_rows(eval_results),
    }
    if statistics_report is not None and suite_name in statistics_report["suite_statistics"]:
        row["five_profile_statistics"] = statistics_report["suite_statistics"][suite_name][
            "five_profile_statistics"
        ]
        row["comparison_notes"] = _suite_comparison_notes(suite_name, statistics_report)
    if replaces_main_suite is not None:
        row["replaces_main_suite"] = replaces_main_suite
    return row


def _build_appendix_profile_rows(
    eval_results: dict[str, Any],
    metric_specs: dict[str, dict[str, Any]],
    *,
    suite_name: str,
) -> dict[str, dict[str, float]]:
    return {
        str(profile_name): _extract_metric_values(
            payload["aggregate"],
            metric_specs,
            over_profile=False,
            context_label=f"suite '{suite_name}' profile '{profile_name}'",
        )
        for profile_name, payload in eval_results.items()
    }


def _resolve_appendix_suite_payload(
    suite_payload_map: dict[str, dict[str, Any]],
    suite_name: str,
    *,
    section_name: str,
) -> dict[str, Any]:
    if suite_name not in suite_payload_map:
        raise ValueError(f"Missing {section_name} suite '{suite_name}' in benchmark artifact.")
    return suite_payload_map[suite_name]


def _build_appendix_teacher_row(suite_payload: dict[str, Any]) -> dict[str, Any]:
    raw_suite_payload = suite_payload["suite_payload"]
    suite_name = str(suite_payload["suite_name"])
    teacher_motion_rule = raw_suite_payload.get("teacher_motion_rule")
    teacher_impedance_rule = raw_suite_payload.get("teacher_impedance_rule")
    if teacher_motion_rule is None or teacher_impedance_rule is None:
        raise ValueError(
            f"Missing teacher metadata for appendix teacher suite '{suite_name}'."
        )

    row = {
        "suite_name": suite_name,
        "display_name": suite_payload["display_name"],
        "source_artifact": str(Path(suite_payload["source_artifact"]).resolve()),
        "teacher_preset_name": raw_suite_payload.get("teacher_preset_name"),
        "teacher_motion_rule": str(teacher_motion_rule),
        "teacher_impedance_rule": str(teacher_impedance_rule),
        "five_profile_mean": _extract_metric_values(
            suite_payload["five_profile_mean"],
            APPENDIX_TEACHER_TABLE_METRICS,
            over_profile=True,
            context_label=f"suite '{suite_name}' five-profile mean",
        ),
        "per_profile": _build_appendix_profile_rows(
            suite_payload["eval_results"],
            APPENDIX_TEACHER_TABLE_METRICS,
            suite_name=suite_name,
        ),
    }
    if suite_payload["replaces_main_suite"] is not None:
        row["replaces_main_suite"] = suite_payload["replaces_main_suite"]
    return row


def _build_appendix_diagnostic_row(suite_payload: dict[str, Any]) -> dict[str, Any]:
    suite_name = str(suite_payload["suite_name"])
    row = {
        "suite_name": suite_name,
        "display_name": suite_payload["display_name"],
        "source_artifact": str(Path(suite_payload["source_artifact"]).resolve()),
        "diagnostics": _extract_metric_values(
            suite_payload["five_profile_mean"],
            APPENDIX_TERMINATION_DIAGNOSTIC_METRICS,
            over_profile=True,
            context_label=f"suite '{suite_name}' five-profile diagnostics",
        ),
        "per_profile_diagnostics": _build_appendix_profile_rows(
            suite_payload["eval_results"],
            APPENDIX_TERMINATION_DIAGNOSTIC_METRICS,
            suite_name=suite_name,
        ),
    }
    if suite_payload["replaces_main_suite"] is not None:
        row["replaces_main_suite"] = suite_payload["replaces_main_suite"]
    return row


def build_3dof_paper_table_export(
    *,
    benchmark_report_path: Path,
    fixed_impedance_report_path: Path | None = None,
    statistics_report_path: Path | None = None,
) -> dict[str, Any]:
    suite_order, suite_payloads, raw_benchmark = _resolve_suite_payloads(
        benchmark_report_path=benchmark_report_path,
        fixed_impedance_report_path=fixed_impedance_report_path,
    )
    handcrafted_policy_order, handcrafted_payloads = _resolve_handcrafted_payloads(
        raw_benchmark=raw_benchmark,
        benchmark_report_path=Path(benchmark_report_path),
    )
    statistics_report = (
        _load_json(Path(statistics_report_path))
        if statistics_report_path is not None
        else None
    )

    suite_rows = [
        _build_suite_row(
            suite_name=suite_payload["suite_name"],
            display_name=suite_payload["display_name"],
            source_artifact=suite_payload["source_artifact"],
            five_profile_mean=suite_payload["five_profile_mean"],
            eval_results=suite_payload["eval_results"],
            replaces_main_suite=suite_payload["replaces_main_suite"],
            statistics_report=statistics_report,
        )
        for suite_payload in suite_payloads
    ]
    handcrafted_rows = [
        _build_suite_row(
            suite_name=handcrafted_payload["suite_name"],
            display_name=handcrafted_payload["display_name"],
            source_artifact=handcrafted_payload["source_artifact"],
            five_profile_mean=handcrafted_payload["five_profile_mean"],
            eval_results=handcrafted_payload["eval_results"],
            statistics_report=statistics_report,
        )
        for handcrafted_payload in handcrafted_payloads
    ]

    return {
        "export_name": "three_dof_paper_benchmark_table",
        "source_artifacts": {
            "benchmark_report": str(Path(benchmark_report_path).resolve()),
            "fixed_impedance_report": (
                str(Path(fixed_impedance_report_path).resolve())
                if fixed_impedance_report_path is not None
                else None
            ),
            "statistics_report": (
                str(Path(statistics_report_path).resolve())
                if statistics_report_path is not None
                else None
            ),
        },
        "suite_order": suite_order,
        "suite_rows": suite_rows,
        "handcrafted_policy_order": handcrafted_policy_order,
        "handcrafted_rows": handcrafted_rows,
        "profile_equivalence_annotation": _annotation_payload(),
        "statistics_report": statistics_report,
    }


def _format_metric_cell(row: dict[str, Any], metric_name: str) -> str:
    if "five_profile_statistics" not in row:
        return f"{row['five_profile_mean'][metric_name]:.3f}"
    stats = row["five_profile_statistics"][metric_name]
    ci = stats["ci"]
    return (
        f"{stats['mean']:.3f} +- {stats['std']:.3f} "
        f"(95% CI [{ci['lower']:.3f}, {ci['upper']:.3f}])"
    )


def render_3dof_paper_table_markdown(export_payload: dict[str, Any]) -> str:
    lines = [
        "# 3DoF Paper Benchmark Table",
        "",
        f"Main benchmark source: `{export_payload['source_artifacts']['benchmark_report']}`",
    ]
    fixed_source = export_payload["source_artifacts"]["fixed_impedance_report"]
    if fixed_source is not None:
        lines.append(f"Fixed-impedance override source: `{fixed_source}`")
    statistics_source = export_payload["source_artifacts"]["statistics_report"]
    if statistics_source is not None:
        lines.extend(
            [
                f"Statistics source: `{statistics_source}`",
                "",
                "Entries report mean +- std with 95% CI where a statistics report is attached.",
            ]
        )
    lines.extend(
        [
            "",
            "## Main Table",
            "",
            "| Suite | Success | Jam | Final Dist (mm) | Mean Peak Force (N) | P95 Force (N) | Contact Steps |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in export_payload["suite_rows"]:
        lines.append(
            "| "
            f"{row['display_name']} | "
            f"{_format_metric_cell(row, 'success_rate')} | "
            f"{_format_metric_cell(row, 'jam_rate')} | "
            f"{_format_metric_cell(row, 'mean_final_distance_mm')} | "
            f"{_format_metric_cell(row, 'mean_peak_contact_force_n')} | "
            f"{_format_metric_cell(row, 'p95_peak_contact_force_n')} | "
            f"{_format_metric_cell(row, 'mean_contact_steps')} |"
        )

    handcrafted_rows = export_payload.get("handcrafted_rows", [])
    if handcrafted_rows:
        lines.extend(
            [
                "",
                "## Handcrafted / Classical Anchors",
                "",
                "| Suite | Success | Jam | Final Dist (mm) | Mean Peak Force (N) | P95 Force (N) | Contact Steps |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in handcrafted_rows:
            lines.append(
                "| "
                f"{row['display_name']} | "
                f"{_format_metric_cell(row, 'success_rate')} | "
                f"{_format_metric_cell(row, 'jam_rate')} | "
                f"{_format_metric_cell(row, 'mean_final_distance_mm')} | "
                f"{_format_metric_cell(row, 'mean_peak_contact_force_n')} | "
                f"{_format_metric_cell(row, 'p95_peak_contact_force_n')} | "
                f"{_format_metric_cell(row, 'mean_contact_steps')} |"
            )

    if export_payload.get("statistics_report") is not None:
        lines.extend(["", "## Comparison Notes", ""])
        for row in export_payload["suite_rows"]:
            for note in row.get("comparison_notes", []):
                lines.append(f"- {row['display_name']}: {note}")

    lines.extend(
        [
            "",
            "## Annotation",
            "",
            ANNOTATION_SUMMARY,
            "",
        ]
    )
    for class_spec in export_payload["profile_equivalence_annotation"]["equivalence_classes"]:
        profile_names = ", ".join(class_spec["profiles"])
        rationale = "; ".join(class_spec["design_rationale"])
        lines.append(
            f"- `{class_spec['class_name']}`: {profile_names}. "
            f"{class_spec['pressure_source']} {rationale}."
        )
    return "\n".join(lines) + "\n"


def export_3dof_paper_table(
    *,
    benchmark_report_path: Path,
    fixed_impedance_report_path: Path | None = None,
    statistics_report_path: Path | None = None,
    output_dir: Path,
    stem: str = "table_3dof_paper_benchmark",
) -> tuple[Path, Path]:
    export_payload = build_3dof_paper_table_export(
        benchmark_report_path=benchmark_report_path,
        fixed_impedance_report_path=fixed_impedance_report_path,
        statistics_report_path=statistics_report_path,
    )
    markdown = render_3dof_paper_table_markdown(export_payload)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    json_path.write_text(
        json.dumps(export_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown, encoding="utf-8")
    return json_path, markdown_path


def build_3dof_appendix_table_export(
    *,
    benchmark_report_path: Path,
    fixed_impedance_report_path: Path | None = None,
) -> dict[str, Any]:
    suite_order, suite_payloads, _ = _resolve_suite_payloads(
        benchmark_report_path=benchmark_report_path,
        fixed_impedance_report_path=fixed_impedance_report_path,
    )
    suite_payload_map = {
        str(suite_payload["suite_name"]): suite_payload for suite_payload in suite_payloads
    }

    teacher_rows = [
        _build_appendix_teacher_row(
            _resolve_appendix_suite_payload(
                suite_payload_map,
                suite_name,
                section_name="teacher ablation",
            )
        )
        for suite_name in APPENDIX_TEACHER_SUITE_ORDER
    ]

    diagnostic_suite_order = list(APPENDIX_DIAGNOSTIC_SUITE_ORDER)
    if fixed_impedance_report_path is not None:
        fixed_impedance_suite_name = "fixed_impedance_rl_stable_r32_p32"
    elif "fixed_impedance_rl_stable_r32_p32" in suite_payload_map:
        fixed_impedance_suite_name = "fixed_impedance_rl_stable_r32_p32"
    else:
        fixed_impedance_suite_name = "fixed_impedance_rl"
    diagnostic_suite_order.append(fixed_impedance_suite_name)
    diagnostic_rows = [
        _build_appendix_diagnostic_row(
            _resolve_appendix_suite_payload(
                suite_payload_map,
                suite_name,
                section_name="termination diagnostics",
            )
        )
        for suite_name in diagnostic_suite_order
    ]

    return {
        "export_name": "three_dof_appendix_benchmark_table",
        "source_artifacts": {
            "benchmark_report": str(Path(benchmark_report_path).resolve()),
            "fixed_impedance_report": (
                str(Path(fixed_impedance_report_path).resolve())
                if fixed_impedance_report_path is not None
                else None
            ),
        },
        "suite_order": suite_order,
        "teacher_suite_order": list(APPENDIX_TEACHER_SUITE_ORDER),
        "teacher_rows": teacher_rows,
        "diagnostic_suite_order": diagnostic_suite_order,
        "diagnostic_rows": diagnostic_rows,
    }


def render_3dof_appendix_table_markdown(export_payload: dict[str, Any]) -> str:
    lines = [
        "# 3DoF Appendix Benchmark Tables",
        "",
        f"Benchmark source: `{export_payload['source_artifacts']['benchmark_report']}`",
    ]
    fixed_source = export_payload["source_artifacts"]["fixed_impedance_report"]
    if fixed_source is not None:
        lines.append(f"Fixed-impedance override source: `{fixed_source}`")

    lines.extend(
        [
            "",
            "## Teacher Ablation",
            "",
            "| Suite | teacher_motion_rule | teacher_impedance_rule | success_rate | jam_rate | mean_final_distance_mm | mean_peak_contact_force_n | mean_contact_steps |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in export_payload["teacher_rows"]:
        lines.append(
            "| "
            f"{row['display_name']} (`{row['suite_name']}`) | "
            f"{row['teacher_motion_rule']} | "
            f"{row['teacher_impedance_rule']} | "
            f"{row['five_profile_mean']['success_rate']:.3f} | "
            f"{row['five_profile_mean']['jam_rate']:.3f} | "
            f"{row['five_profile_mean']['mean_final_distance_mm']:.3f} | "
            f"{row['five_profile_mean']['mean_peak_contact_force_n']:.3f} | "
            f"{row['five_profile_mean']['mean_contact_steps']:.3f} |"
        )

    lines.extend(["", "### Teacher Per-Profile Readout", ""])
    for row in export_payload["teacher_rows"]:
        lines.extend(
            [
                f"#### {row['display_name']} (`{row['suite_name']}`)",
                "",
                "| Profile | success_rate | jam_rate | mean_final_distance_mm | mean_peak_contact_force_n | mean_contact_steps |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for profile_name, profile_metrics in row["per_profile"].items():
            lines.append(
                "| "
                f"{profile_name} | "
                f"{profile_metrics['success_rate']:.3f} | "
                f"{profile_metrics['jam_rate']:.3f} | "
                f"{profile_metrics['mean_final_distance_mm']:.3f} | "
                f"{profile_metrics['mean_peak_contact_force_n']:.3f} | "
                f"{profile_metrics['mean_contact_steps']:.3f} |"
            )
        lines.append("")

    diagnostic_headers = list(APPENDIX_TERMINATION_DIAGNOSTIC_METRICS)
    lines.extend(
        [
            "## Termination Diagnostics",
            "",
            "| Suite | "
            + " | ".join(diagnostic_headers)
            + " |",
            "| --- | "
            + " | ".join("---" for _ in diagnostic_headers)
            + " |",
        ]
    )
    for row in export_payload["diagnostic_rows"]:
        diagnostic_values = " | ".join(
            f"{row['diagnostics'][metric_name]:.3f}" for metric_name in diagnostic_headers
        )
        lines.append(f"| {row['display_name']} | {diagnostic_values} |")

    return "\n".join(lines) + "\n"


def export_3dof_appendix_table(
    *,
    benchmark_report_path: Path,
    fixed_impedance_report_path: Path | None = None,
    output_dir: Path,
    stem: str = "table_3dof_appendix_benchmark",
) -> tuple[Path, Path]:
    export_payload = build_3dof_appendix_table_export(
        benchmark_report_path=benchmark_report_path,
        fixed_impedance_report_path=fixed_impedance_report_path,
    )
    markdown = render_3dof_appendix_table_markdown(export_payload)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    json_path.write_text(
        json.dumps(export_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(markdown, encoding="utf-8")
    return json_path, markdown_path
