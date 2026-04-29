from __future__ import annotations

import csv
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np

from vi_full.artifact_provenance import calculate_sha256, git_commit, git_dirty
from vi_full.three_dof_benchmark import DEFAULT_UNCERTAINTY_PROFILES
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_teacher_coupling_ablation import (
    TeacherCouplingCondition,
    build_motion_matched_grid,
)


MOTION_MATCHED_MAIN_CONDITION_ORDER = (
    "vi_full",
    "vi_motion_fi_k",
    "fi_motion_vi_k",
    "fi_full",
)
DEFAULT_MAIN_PROTOCOL_SEEDS = tuple(range(5))
DEFAULT_MAIN_PROTOCOL_EPISODES_PER_SEED = 100
DEFAULT_MAIN_PROTOCOL_TOTAL_TIMESTEPS = 128
MOTION_MATCHED_MAIN_SCHEMA_VERSION = 1
BOOTSTRAP_CONFIDENCE = 0.95
BOOTSTRAP_RESAMPLES = 5000
SUITE_METADATA_KEYS = (
    "motion_rule",
    "impedance_rule",
    "fixed_stiffness_xy",
    "fixed_stiffness_z",
)

TABLE_METRICS = {
    "success_rate": {
        "raw_key": "success_rate",
        "label": "success",
        "digits": 3,
        "scale": 1.0,
    },
    "jam_rate": {
        "raw_key": "jam_rate",
        "label": "jam",
        "digits": 3,
        "scale": 1.0,
    },
    "mean_peak_contact_force_n": {
        "raw_key": "mean_peak_contact_force",
        "label": "peak force N",
        "digits": 3,
        "scale": 1.0,
    },
    "mean_contact_steps": {
        "raw_key": "mean_contact_steps",
        "label": "contact steps",
        "digits": 1,
        "scale": 1.0,
    },
    "mean_contact_work": {
        "raw_key": "mean_contact_work",
        "label": "contact work",
        "digits": 5,
        "scale": 1.0,
    },
}


@dataclass(frozen=True, slots=True)
class MotionMatchedMainCondition:
    base_condition: TeacherCouplingCondition
    episodes_per_seed: int
    profiles: tuple[str, ...]
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps

    @property
    def name(self) -> str:
        return self.base_condition.name

    @property
    def teacher_prior(self) -> str:
        return self.base_condition.teacher_prior

    @property
    def student_impedance_space(self) -> str:
        return self.base_condition.student_impedance_space

    @property
    def teacher_preset_name(self) -> str:
        return self.base_condition.teacher_preset_name

    @property
    def seeds(self) -> tuple[int, ...]:
        return self.base_condition.seeds

    @property
    def total_timesteps(self) -> int:
        return self.base_condition.total_timesteps

    @property
    def motion_rule(self) -> str | None:
        return self.base_condition.motion_rule

    @property
    def impedance_rule(self) -> str | None:
        return self.base_condition.impedance_rule

    @property
    def fixed_stiffness_xy(self) -> float | None:
        return self.base_condition.fixed_stiffness_xy

    @property
    def fixed_stiffness_z(self) -> float | None:
        return self.base_condition.fixed_stiffness_z

    def to_suite_run_kwargs(self) -> dict[str, Any]:
        kwargs = self.base_condition.to_suite_run_kwargs(
            episodes=int(self.episodes_per_seed),
            profiles=self.profiles,
        )
        kwargs["max_episode_steps"] = int(self.max_episode_steps)
        return kwargs

    def to_protocol_row(self) -> dict[str, Any]:
        return {
            "condition_name": self.name,
            "teacher_prior": self.teacher_prior,
            "student_impedance_space": self.student_impedance_space,
            "teacher_preset_name": self.teacher_preset_name,
            "teacher_motion_rule": self.base_condition.teacher_spec.motion_rule,
            "teacher_impedance_rule": self.base_condition.teacher_spec.impedance_rule,
            "motion_rule": self.motion_rule,
            "impedance_rule": self.impedance_rule,
            "fixed_stiffness_xy": self.fixed_stiffness_xy,
            "fixed_stiffness_z": self.fixed_stiffness_z,
            "seeds": list(self.seeds),
            "episodes_per_seed": int(self.episodes_per_seed),
            "profiles": list(self.profiles),
            "total_timesteps": int(self.total_timesteps),
            "max_episode_steps": int(self.max_episode_steps),
        }


def build_motion_matched_main_grid(
    seeds: Sequence[int] = DEFAULT_MAIN_PROTOCOL_SEEDS,
    *,
    episodes_per_seed: int = DEFAULT_MAIN_PROTOCOL_EPISODES_PER_SEED,
    profiles: Sequence[str] = DEFAULT_UNCERTAINTY_PROFILES,
    total_timesteps: int = DEFAULT_MAIN_PROTOCOL_TOTAL_TIMESTEPS,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
) -> list[MotionMatchedMainCondition]:
    diagnostic_grid = {
        condition.name: condition
        for condition in build_motion_matched_grid(
            seeds=tuple(int(seed) for seed in seeds),
            total_timesteps=int(total_timesteps),
        )
    }
    return [
        MotionMatchedMainCondition(
            base_condition=diagnostic_grid[name],
            episodes_per_seed=int(episodes_per_seed),
            profiles=tuple(str(profile) for profile in profiles),
            max_episode_steps=int(max_episode_steps),
        )
        for name in MOTION_MATCHED_MAIN_CONDITION_ORDER
    ]


def run_motion_matched_main_protocol(
    *,
    suite_runner: Callable[[dict[str, Any]], dict[str, Any]],
    seeds: Sequence[int] = DEFAULT_MAIN_PROTOCOL_SEEDS,
    episodes_per_seed: int = DEFAULT_MAIN_PROTOCOL_EPISODES_PER_SEED,
    profiles: Sequence[str] = DEFAULT_UNCERTAINTY_PROFILES,
    total_timesteps: int = DEFAULT_MAIN_PROTOCOL_TOTAL_TIMESTEPS,
    generating_command: str,
    source_artifacts: dict[str, str] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    grid = build_motion_matched_main_grid(
        seeds=seeds,
        episodes_per_seed=episodes_per_seed,
        profiles=profiles,
        total_timesteps=total_timesteps,
    )
    learned_results: dict[str, Any] = {}
    for condition in grid:
        suite_kwargs = condition.to_suite_run_kwargs()
        suite_metadata = _split_suite_metadata(suite_kwargs)
        result = suite_runner(suite_kwargs)
        result.update(suite_metadata)
        result["teacher_prior"] = condition.teacher_prior
        result["student_impedance_space"] = condition.student_impedance_space
        result["teacher_motion_rule"] = condition.base_condition.teacher_spec.motion_rule
        result["teacher_impedance_rule"] = condition.base_condition.teacher_spec.impedance_rule
        result["motion_rule"] = condition.motion_rule
        result["impedance_rule"] = condition.impedance_rule
        if condition.fixed_stiffness_xy is not None:
            result["fixed_stiffness_xy"] = float(condition.fixed_stiffness_xy)
        if condition.fixed_stiffness_z is not None:
            result["fixed_stiffness_z"] = float(condition.fixed_stiffness_z)
        learned_results[condition.name] = result
    return build_motion_matched_main_report(
        learned_results=learned_results,
        grid=grid,
        generating_command=generating_command,
        source_artifacts=source_artifacts,
        repo_root=repo_root,
    )


def _split_suite_metadata(suite_kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        key: suite_kwargs.pop(key)
        for key in SUITE_METADATA_KEYS
        if key in suite_kwargs
    }


def build_motion_matched_main_report(
    *,
    learned_results: dict[str, Any],
    grid: Sequence[MotionMatchedMainCondition],
    generating_command: str,
    source_artifacts: dict[str, str] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2] if repo_root is None else Path(repo_root)
    source_artifacts = _default_source_artifacts(source_artifacts)
    protocol = _build_protocol_payload(grid)
    report = {
        "schema_version": MOTION_MATCHED_MAIN_SCHEMA_VERSION,
        "artifact_schema_version": MOTION_MATCHED_MAIN_SCHEMA_VERSION,
        "export_name": "three_dof_motion_matched_main_protocol",
        "metadata": {
            "generated_at_utc": _utc_now(),
            "git_commit": _git_commit_or_unknown(repo_root),
            "git_dirty": _git_dirty_or_true(repo_root),
            "benchmark_contract": asdict(DEFAULT_3DOF_BENCHMARK_CONTRACT),
            "condition_order": list(MOTION_MATCHED_MAIN_CONDITION_ORDER),
        },
        "protocol": protocol,
        "conditions": [condition.to_protocol_row() for condition in grid],
        "learned_results": learned_results,
        "per_profile": _build_per_profile_rows(learned_results),
        "per_seed": _build_per_seed_rows(learned_results),
        "aggregate": summarize_motion_matched_results(learned_results),
        "source_artifacts": source_artifacts,
        "source_hashes": _source_hashes(source_artifacts, repo_root=repo_root),
        "generating_command": generating_command,
        "git_commit": _git_commit_or_unknown(repo_root),
        "git_dirty": _git_dirty_or_true(repo_root),
    }
    return _json_safe(report)


def summarize_motion_matched_results(learned_results: dict[str, Any]) -> dict[str, Any]:
    condition_statistics: dict[str, Any] = {}
    for condition_index, condition_name in enumerate(MOTION_MATCHED_MAIN_CONDITION_ORDER):
        if condition_name not in learned_results:
            continue
        eval_results = dict(learned_results[condition_name].get("eval_results", {}))
        five_profile_seed_samples: dict[str, list[float]] = {}
        five_profile_statistics: dict[str, Any] = {}
        for metric_index, metric_name in enumerate(TABLE_METRICS):
            _, samples = _collect_seed_metric_samples(eval_results, metric_name=metric_name)
            five_profile_seed_samples[metric_name] = samples
            if samples:
                five_profile_statistics[metric_name] = _build_metric_statistics(
                    samples,
                    rng_seed=condition_index * 100 + metric_index,
                )

        per_profile_statistics: dict[str, Any] = {}
        for profile_index, (profile_name, profile_payload) in enumerate(eval_results.items()):
            per_profile_statistics[profile_name] = {}
            for metric_index, metric_name in enumerate(TABLE_METRICS):
                samples = _collect_profile_metric_samples(
                    profile_payload,
                    metric_name=metric_name,
                )
                if samples:
                    per_profile_statistics[profile_name][metric_name] = (
                        _build_metric_statistics(
                            samples,
                            rng_seed=condition_index * 1000 + profile_index * 100 + metric_index,
                        )
                    )

        condition_statistics[condition_name] = {
            "five_profile_seed_samples": five_profile_seed_samples,
            "five_profile_statistics": five_profile_statistics,
            "per_profile_statistics": per_profile_statistics,
        }

    return {
        "condition_statistics": condition_statistics,
        "paired_tests": _build_paired_tests(condition_statistics),
        "interval_method": "bootstrap",
        "paired_test_method": "paired sign-flip permutation",
        "confidence_level": BOOTSTRAP_CONFIDENCE,
    }


def write_motion_matched_main_report(path: Path, report: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp")
    tmp_path.write_text(
        json.dumps(_json_safe(report), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)
    return path


def export_motion_matched_table(
    report: dict[str, Any],
    *,
    output_stem: Path,
) -> dict[str, Path]:
    output_stem = Path(output_stem)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    rows = _table_rows(report)
    csv_path = output_stem.with_suffix(".csv")
    md_path = output_stem.with_suffix(".md")
    fieldnames = [
        "condition_name",
        "profile",
        "success_rate_mean",
        "success_rate_ci_lower",
        "success_rate_ci_upper",
        "jam_rate_mean",
        "jam_rate_ci_lower",
        "jam_rate_ci_upper",
        "mean_peak_contact_force_n_mean",
        "mean_peak_contact_force_n_ci_lower",
        "mean_peak_contact_force_n_ci_upper",
        "mean_contact_steps_mean",
        "mean_contact_steps_ci_lower",
        "mean_contact_steps_ci_upper",
        "mean_contact_work_mean",
        "mean_contact_work_ci_lower",
        "mean_contact_work_ci_upper",
        "num_samples",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    md_path.write_text(_markdown_table(report, rows), encoding="utf-8")
    return {"csv": csv_path, "markdown": md_path}


def _build_protocol_payload(grid: Sequence[MotionMatchedMainCondition]) -> dict[str, Any]:
    first = grid[0]
    return {
        "name": "motion_matched_main_protocol",
        "profiles": list(first.profiles),
        "seeds": list(first.seeds),
        "episodes_per_seed": int(first.episodes_per_seed),
        "total_timesteps": int(first.total_timesteps),
        "ppo_budget": "paper_matched_128_steps",
        "max_episode_steps": int(first.max_episode_steps),
        "benchmark_contract": asdict(DEFAULT_3DOF_BENCHMARK_CONTRACT),
        "condition_names": [condition.name for condition in grid],
    }


def _build_per_profile_rows(learned_results: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for condition_name in MOTION_MATCHED_MAIN_CONDITION_ORDER:
        condition_payload = learned_results.get(condition_name, {})
        for profile_name, profile_payload in condition_payload.get("eval_results", {}).items():
            aggregate = dict(profile_payload.get("aggregate", {}))
            row = {
                "condition_name": condition_name,
                "profile": profile_name,
                "seed_count": len(profile_payload.get("per_seed", [])),
            }
            for metric_name, spec in TABLE_METRICS.items():
                aggregate_key = f"{spec['raw_key']}_mean"
                if aggregate_key in aggregate:
                    row[metric_name] = float(aggregate[aggregate_key]) * float(spec["scale"])
            rows.append(row)
    return rows


def _build_per_seed_rows(learned_results: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for condition_name in MOTION_MATCHED_MAIN_CONDITION_ORDER:
        condition_payload = learned_results.get(condition_name, {})
        for profile_name, profile_payload in condition_payload.get("eval_results", {}).items():
            for seed_payload in profile_payload.get("per_seed", []):
                row = {
                    "condition_name": condition_name,
                    "profile": profile_name,
                    "seed": int(seed_payload["seed"]),
                }
                for metric_name, spec in TABLE_METRICS.items():
                    raw_key = spec["raw_key"]
                    if raw_key in seed_payload:
                        row[metric_name] = (
                            float(seed_payload[raw_key]) * float(spec["scale"])
                        )
                rows.append(row)
    return rows


def _collect_seed_metric_samples(
    eval_results: dict[str, Any],
    *,
    metric_name: str,
) -> tuple[list[int], list[float]]:
    profile_names = list(eval_results)
    if not profile_names:
        return [], []
    seed_maps: list[dict[int, dict[str, Any]]] = []
    raw_key = str(TABLE_METRICS[metric_name]["raw_key"])
    for profile_name in profile_names:
        per_seed = eval_results[profile_name].get("per_seed", [])
        if not per_seed:
            return [], []
        seed_maps.append({int(item["seed"]): item for item in per_seed if raw_key in item})
    if not seed_maps:
        return [], []
    common_seeds = sorted(set.intersection(*(set(seed_map) for seed_map in seed_maps)))
    samples: list[float] = []
    scale = float(TABLE_METRICS[metric_name]["scale"])
    for seed in common_seeds:
        profile_values = [float(seed_map[seed][raw_key]) * scale for seed_map in seed_maps]
        samples.append(float(np.mean(np.asarray(profile_values, dtype=np.float64))))
    return common_seeds, samples


def _collect_profile_metric_samples(
    profile_payload: dict[str, Any],
    *,
    metric_name: str,
) -> list[float]:
    raw_key = str(TABLE_METRICS[metric_name]["raw_key"])
    scale = float(TABLE_METRICS[metric_name]["scale"])
    return [
        float(item[raw_key]) * scale
        for item in profile_payload.get("per_seed", [])
        if raw_key in item
    ]


def _bootstrap_ci(
    values: Sequence[float],
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


def _build_metric_statistics(values: Sequence[float], *, rng_seed: int) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(np.mean(array)),
        "std": float(np.std(array)),
        "ci": _bootstrap_ci(array, rng_seed=rng_seed),
        "num_samples": int(array.size),
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


def _paired_difference_ci(
    reference_values: Sequence[float],
    candidate_values: Sequence[float],
    *,
    rng_seed: int,
) -> dict[str, float]:
    reference = np.asarray(reference_values, dtype=np.float64)
    candidate = np.asarray(candidate_values, dtype=np.float64)
    if reference.shape != candidate.shape:
        raise ValueError("Paired comparisons require matching sample shapes.")
    differences = candidate - reference
    return _bootstrap_ci(differences, rng_seed=rng_seed)


def _build_paired_tests(condition_statistics: dict[str, Any]) -> list[dict[str, Any]]:
    reference_name = "vi_full"
    if reference_name not in condition_statistics:
        return []
    tests: list[dict[str, Any]] = []
    reference_stats = condition_statistics[reference_name]
    for condition_index, candidate_name in enumerate(MOTION_MATCHED_MAIN_CONDITION_ORDER):
        if candidate_name == reference_name or candidate_name not in condition_statistics:
            continue
        candidate_stats = condition_statistics[candidate_name]
        for metric_index, metric_name in enumerate(TABLE_METRICS):
            reference_values = reference_stats["five_profile_seed_samples"].get(metric_name, [])
            candidate_values = candidate_stats["five_profile_seed_samples"].get(metric_name, [])
            if len(reference_values) != len(candidate_values) or not reference_values:
                continue
            differences = (
                np.asarray(candidate_values, dtype=np.float64)
                - np.asarray(reference_values, dtype=np.float64)
            )
            tests.append(
                {
                    "comparison_id": f"{reference_name}__vs__{candidate_name}__{metric_name}",
                    "reference_condition": reference_name,
                    "candidate_condition": candidate_name,
                    "metric": metric_name,
                    "reference_mean": float(np.mean(reference_values)),
                    "candidate_mean": float(np.mean(candidate_values)),
                    "mean_difference": float(np.mean(differences)),
                    "ci": _paired_difference_ci(
                        reference_values,
                        candidate_values,
                        rng_seed=condition_index * 100 + metric_index,
                    ),
                    "p_value": _paired_sign_flip_p_value(differences),
                }
            )
    return tests


def _table_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    aggregate = report["aggregate"]["condition_statistics"]
    for condition_name in MOTION_MATCHED_MAIN_CONDITION_ORDER:
        stats = aggregate.get(condition_name, {})
        if stats:
            rows.append(_flatten_table_stats(condition_name, "five_profile_mean", stats))
        per_profile = stats.get("per_profile_statistics", {})
        for profile_name, profile_stats in per_profile.items():
            rows.append(_flatten_table_stats(condition_name, profile_name, profile_stats))
    return rows


def _flatten_table_stats(
    condition_name: str,
    profile_name: str,
    stats: dict[str, Any],
) -> dict[str, Any]:
    metric_stats = stats.get("five_profile_statistics", stats)
    row: dict[str, Any] = {
        "condition_name": condition_name,
        "profile": profile_name,
        "num_samples": "",
    }
    for metric_name in TABLE_METRICS:
        payload = metric_stats.get(metric_name)
        if not payload:
            continue
        row[f"{metric_name}_mean"] = payload["mean"]
        row[f"{metric_name}_ci_lower"] = payload["ci"]["lower"]
        row[f"{metric_name}_ci_upper"] = payload["ci"]["upper"]
        row["num_samples"] = payload["num_samples"]
    return row


def _markdown_table(report: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    protocol = report["protocol"]
    lines = [
        "# 3DoF Motion-Matched Main Protocol",
        "",
        f"Seeds: `{protocol['seeds']}`",
        f"Episodes per seed/profile: `{protocol['episodes_per_seed']}`",
        f"Profiles: `{protocol['profiles']}`",
        f"PPO budget: `{protocol['total_timesteps']}` steps",
        "",
        "| condition | profile | success | jam | peak force N | contact steps | contact work | n |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {condition} | {profile} | {success} | {jam} | {force} | {steps} | {work} | {n} |".format(
                condition=row["condition_name"],
                profile=row["profile"],
                success=_format_ci(row, "success_rate", 3),
                jam=_format_ci(row, "jam_rate", 3),
                force=_format_ci(row, "mean_peak_contact_force_n", 3),
                steps=_format_ci(row, "mean_contact_steps", 1),
                work=_format_ci(row, "mean_contact_work", 5),
                n=row.get("num_samples", ""),
            )
        )
    lines.extend(
        [
            "",
            "Statistics: bootstrap 95% CI over paired seed-level five-profile means; paired tests use sign-flip permutations against `vi_full`.",
        ]
    )
    return "\n".join(lines) + "\n"


def _format_ci(row: dict[str, Any], metric_name: str, digits: int) -> str:
    mean_key = f"{metric_name}_mean"
    if mean_key not in row:
        return ""
    lower_key = f"{metric_name}_ci_lower"
    upper_key = f"{metric_name}_ci_upper"
    return (
        f"{float(row[mean_key]):.{digits}f} "
        f"[{float(row[lower_key]):.{digits}f}, {float(row[upper_key]):.{digits}f}]"
    )


def _default_source_artifacts(source_artifacts: dict[str, str] | None) -> dict[str, str]:
    defaults = {
        "protocol_module": "src/vi_full/three_dof_motion_matched_main_protocol.py",
        "teacher_coupling_module": "src/vi_full/three_dof_teacher_coupling_ablation.py",
        "benchmark_runner": "scripts/experiments/run_3dof_uncertainty_benchmark.py",
    }
    if source_artifacts:
        defaults.update(source_artifacts)
    return defaults


def _source_hashes(source_artifacts: dict[str, str], *, repo_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for source_name, relative_path in source_artifacts.items():
        path = repo_root / relative_path
        if path.exists():
            hashes[source_name] = calculate_sha256(path)
    return hashes


def _git_commit_or_unknown(repo_root: Path) -> str:
    try:
        return git_commit(repo_root=repo_root)
    except Exception:
        return "unknown"


def _git_dirty_or_true(repo_root: Path) -> bool:
    try:
        return git_dirty(repo_root=repo_root)
    except Exception:
        return True


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
