from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from vi_full.three_dof_config import ThreeDoFInsertionConfig
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_env import ThreeDoFInsertionEnv
from vi_full.three_dof_policies import build_3dof_handcrafted_policy_registry
from vi_full.three_dof_profiles import DEFAULT_UNCERTAINTY_PROFILES, build_3dof_profile_config


DEFAULT_PARAMETER_NAMES = (
    "contact_xy_scale",
    "contact_z_scale",
    "wall_friction_range",
    "force_noise_std_range",
    "contact_transition_band_m",
)
DEFAULT_LEVEL_NAMES = ("low", "nominal", "high")
LEVEL_FACTORS = {
    "low": 0.75,
    "nominal": 1.0,
    "high": 1.25,
}
ROW_FIELDS = (
    "parameter_name",
    "level_name",
    "profile",
    "policy_name",
    "success_rate",
    "jam_rate",
    "documented_force_jam_rate",
    "blocked_contact_termination_rate",
    "mean_final_distance",
    "mean_peak_contact_force",
    "p95_peak_contact_force",
    "mean_contact_steps",
    "mean_contact_work",
)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _scale_value(value: float | tuple[float, float], factor: float) -> float | tuple[float, float]:
    if isinstance(value, tuple):
        return tuple(float(item) * factor for item in value)
    return float(value) * factor


def _parameter_override(
    parameter_name: str,
    level_name: str,
    *,
    base_config: ThreeDoFInsertionConfig | None = None,
) -> dict[str, Any]:
    if parameter_name not in DEFAULT_PARAMETER_NAMES:
        raise ValueError(f"Unknown contact parameter: {parameter_name}")
    if level_name not in LEVEL_FACTORS:
        raise ValueError(f"Unknown sensitivity level: {level_name}")
    config = base_config if base_config is not None else ThreeDoFInsertionConfig()
    factor = LEVEL_FACTORS[level_name]
    return {
        parameter_name: _scale_value(getattr(config, parameter_name), factor)
    }


def build_contact_parameter_grid(
    *,
    parameter_names: list[str] | None = None,
    level_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    selected_parameters = list(parameter_names or DEFAULT_PARAMETER_NAMES)
    selected_levels = list(level_names or DEFAULT_LEVEL_NAMES)
    return [
        {
            "parameter_name": parameter_name,
            "level_name": level_name,
            "overrides": _json_safe(_parameter_override(parameter_name, level_name)),
        }
        for parameter_name in selected_parameters
        for level_name in selected_levels
    ]


def _mean(values: list[float]) -> float:
    return float(np.mean(np.asarray(values, dtype=np.float64)))


def _percentile(values: list[float], percentile: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=np.float64), percentile))


def _evaluate_policy(
    *,
    config: ThreeDoFInsertionConfig,
    policy: Any,
    episodes: int,
    seed: int,
    profile: str,
) -> dict[str, Any]:
    env = ThreeDoFInsertionEnv(config)
    successes: list[float] = []
    final_distances: list[float] = []
    episode_lengths: list[float] = []
    peak_forces: list[float] = []
    contact_steps_per_episode: list[float] = []
    contact_work: list[float] = []
    jam_flags: list[float] = []
    documented_force_jam_flags: list[float] = []
    blocked_contact_flags: list[float] = []
    try:
        for episode_index in range(int(episodes)):
            observation, info = env.reset(seed=int(seed) * 10_000 + episode_index)
            episode_peak_force = 0.0
            episode_contact_steps = 0
            terminated = False
            truncated = False
            while not (terminated or truncated):
                action = policy.act(observation)
                observation, _, terminated, truncated, info = env.step(action)
                episode_peak_force = max(episode_peak_force, float(info["peak_contact_force"]))
                if float(info["contact_force_norm"]) >= config.contact_reward_force_threshold_n:
                    episode_contact_steps += 1
            termination_details = dict(info["termination_details"])
            successes.append(float(info["is_success"]))
            final_distances.append(float(info["distance_to_target"]))
            episode_lengths.append(float(env.episode_step))
            peak_forces.append(float(episode_peak_force))
            contact_steps_per_episode.append(float(episode_contact_steps))
            contact_work.append(float(info["cumulative_contact_work"]))
            jam_flags.append(float(info["is_jammed"]))
            documented_force_jam_flags.append(float(info["meets_documented_force_jam"]))
            blocked_contact_flags.append(float(termination_details["blocked_contact_failure"]))
    finally:
        env.close()
    return {
        "policy_name": getattr(policy, "name", policy.__class__.__name__),
        "uncertainty_profile": profile,
        "seed": int(seed),
        "success_rate": _mean(successes),
        "mean_final_distance": _mean(final_distances),
        "mean_episode_length": _mean(episode_lengths),
        "mean_peak_contact_force": _mean(peak_forces),
        "p95_peak_contact_force": _percentile(peak_forces, 95),
        "mean_contact_steps": _mean(contact_steps_per_episode),
        "mean_contact_work": _mean(contact_work),
        "jam_rate": _mean(jam_flags),
        "documented_force_jam_rate": _mean(documented_force_jam_flags),
        "blocked_contact_termination_rate": _mean(blocked_contact_flags),
    }


def _aggregate_seed_summaries(summaries: list[dict[str, Any]]) -> dict[str, float]:
    if not summaries:
        raise ValueError("summaries must not be empty")
    metrics = (
        "success_rate",
        "jam_rate",
        "documented_force_jam_rate",
        "blocked_contact_termination_rate",
        "mean_final_distance",
        "mean_peak_contact_force",
        "p95_peak_contact_force",
        "mean_contact_steps",
        "mean_contact_work",
    )
    return {
        metric: _mean([float(summary[metric]) for summary in summaries])
        for metric in metrics
    }


def _profile_config_and_overrides(
    profile: str,
    *,
    max_episode_steps: int,
    parameter_name: str,
    level_name: str,
) -> tuple[ThreeDoFInsertionConfig, dict[str, Any]]:
    config = build_3dof_profile_config(profile, max_episode_steps=max_episode_steps)
    overrides = _parameter_override(
        parameter_name,
        level_name,
        base_config=config,
    )
    return replace(config, **overrides), overrides


def run_contact_parameter_sensitivity(
    *,
    profiles: list[str] | None = None,
    seeds: list[int] | None = None,
    episodes_per_seed: int = 1,
    policy_names: list[str] | None = None,
    parameter_names: list[str] | None = None,
    level_names: list[str] | None = None,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
) -> dict[str, Any]:
    selected_profiles = list(profiles or DEFAULT_UNCERTAINTY_PROFILES)
    selected_seeds = [int(seed) for seed in (seeds or [0])]
    selected_policy_names = list(policy_names or ["fixed_impedance", "variable_impedance"])
    policy_registry = build_3dof_handcrafted_policy_registry()
    missing_policies = [name for name in selected_policy_names if name not in policy_registry]
    if missing_policies:
        raise ValueError(f"Unknown 3DoF handcrafted policies: {missing_policies}")
    grid = build_contact_parameter_grid(
        parameter_names=parameter_names,
        level_names=level_names,
    )
    rows: list[dict[str, Any]] = []
    for point in grid:
        for profile in selected_profiles:
            config, overrides = _profile_config_and_overrides(
                profile,
                max_episode_steps=max_episode_steps,
                parameter_name=point["parameter_name"],
                level_name=point["level_name"],
            )
            for policy_name in selected_policy_names:
                seed_summaries = [
                    _evaluate_policy(
                        config=config,
                        policy=policy_registry[policy_name](),
                        episodes=int(episodes_per_seed),
                        seed=seed,
                        profile=profile,
                    )
                    for seed in selected_seeds
                ]
                rows.append(
                    {
                        "parameter_name": point["parameter_name"],
                        "level_name": point["level_name"],
                        "profile": profile,
                        "policy_name": policy_name,
                        "overrides": _json_safe(overrides),
                        "seed_count": len(selected_seeds),
                        "episodes_per_seed": int(episodes_per_seed),
                        **_aggregate_seed_summaries(seed_summaries),
                    }
                )
    return {
        "artifact_type": "three_dof_contact_parameter_sensitivity",
        "schema_version": 1,
        "config": {
            "profiles": selected_profiles,
            "seeds": selected_seeds,
            "episodes_per_seed": int(episodes_per_seed),
            "policy_names": selected_policy_names,
            "parameter_names": list(parameter_names or DEFAULT_PARAMETER_NAMES),
            "level_names": list(level_names or DEFAULT_LEVEL_NAMES),
            "max_episode_steps": int(max_episode_steps),
        },
        "most_sensitive_parameter": identify_most_sensitive_parameter(rows),
        "rows": _json_safe(rows),
    }


def identify_most_sensitive_parameter(rows: list[dict[str, Any]]) -> dict[str, Any]:
    nominal_by_parameter: dict[str, list[float]] = {}
    values_by_parameter: dict[str, list[float]] = {}
    for row in rows:
        parameter_name = str(row["parameter_name"])
        success_rate = float(row["success_rate"])
        values_by_parameter.setdefault(parameter_name, []).append(success_rate)
        if row["level_name"] == "nominal":
            nominal_by_parameter.setdefault(parameter_name, []).append(success_rate)
    best: dict[str, Any] = {
        "parameter_name": None,
        "max_abs_success_delta": 0.0,
    }
    for parameter_name, values in values_by_parameter.items():
        nominal_values = nominal_by_parameter.get(parameter_name)
        if not nominal_values:
            continue
        nominal = _mean(nominal_values)
        max_delta = max(abs(float(value) - nominal) for value in values)
        if best["parameter_name"] is None or max_delta > float(best["max_abs_success_delta"]):
            best = {
                "parameter_name": parameter_name,
                "nominal_success_rate": nominal,
                "max_abs_success_delta": float(max_delta),
            }
    return best


def render_contact_parameter_sensitivity_csv(report: dict[str, Any]) -> str:
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(ROW_FIELDS), lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
        writer.writerow({field: row.get(field, "") for field in ROW_FIELDS})
    return buffer.getvalue()


def render_contact_parameter_sensitivity_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 3DoF Contact-Parameter Sensitivity",
        "",
        f"- most_sensitive_parameter: {report['most_sensitive_parameter'].get('parameter_name')}",
        "",
        "| Parameter | Level | Profile | Policy | Success | Jam | Peak force | Final distance |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in report["rows"]:
        lines.append(
            "| {parameter_name} | {level_name} | {profile} | {policy_name} | "
            "{success_rate} | {jam_rate} | {mean_peak_contact_force} | {mean_final_distance} |".format(
                **row
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_contact_parameter_sensitivity_artifacts(
    output_path: Path,
    report: dict[str, Any],
) -> dict[str, Path]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_path
    csv_path = output_path.with_suffix(".csv")
    markdown_path = output_path.with_suffix(".md")
    json_path.write_text(json.dumps(_json_safe(report), indent=2), encoding="utf-8")
    csv_path.write_text(render_contact_parameter_sensitivity_csv(report), encoding="utf-8")
    markdown_path.write_text(
        render_contact_parameter_sensitivity_markdown(report),
        encoding="utf-8",
    )
    return {"json": json_path, "csv": csv_path, "markdown": markdown_path}
