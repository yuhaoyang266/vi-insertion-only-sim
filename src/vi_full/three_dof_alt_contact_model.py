from __future__ import annotations

import csv
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from vi_full.three_dof_config import ThreeDoFInsertionConfig
from vi_full.three_dof_contact_parameter_sensitivity import (
    SENSITIVITY_SUMMARY_METRICS,
    _aggregate_seed_summaries,
    _evaluate_policy,
    _json_safe,
)
from vi_full.three_dof_contract import DEFAULT_3DOF_BENCHMARK_CONTRACT
from vi_full.three_dof_policies import build_3dof_handcrafted_policy_registry
from vi_full.three_dof_profiles import build_3dof_profile_config
from vi_full.three_dof_profiles import DEFAULT_UNCERTAINTY_PROFILES


BASE_CONTACT_MODEL_NAME = "within_a_base_contact_law"
ALT_CONTACT_MODEL_NAME = "within_a_soft_wall_contact_cross_check"
ALT_CONTACT_MODEL_CHANGED_FIELDS = (
    "contact_xy_scale",
    "contact_z_scale",
    "in_hole_drag_scale",
    "contact_transition_band_m",
)


@dataclass(frozen=True, slots=True)
class AltContactModelSpec:
    name: str
    claim_scope: str
    base_profile: str
    changed_fields: tuple[str, ...]
    config: ThreeDoFInsertionConfig


ALT_CONTACT_MODEL_ROW_FIELDS = (
    "contact_model",
    "profile",
    "policy_name",
    "seed_count",
    "episodes_per_seed",
    *SENSITIVITY_SUMMARY_METRICS,
)


def build_alt_contact_model_config(
    profile_name: str = "nominal",
    *,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
) -> ThreeDoFInsertionConfig:
    base = build_3dof_profile_config(
        profile_name,
        max_episode_steps=max_episode_steps,
    )
    return replace(
        base,
        contact_xy_scale=base.contact_xy_scale * 0.85,
        contact_z_scale=base.contact_z_scale * 1.15,
        in_hole_drag_scale=base.in_hole_drag_scale * 1.10,
        contact_transition_band_m=base.contact_transition_band_m * 1.25,
    )


def build_alt_contact_model_spec(
    profile_name: str = "nominal",
    *,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
) -> AltContactModelSpec:
    return AltContactModelSpec(
        name=ALT_CONTACT_MODEL_NAME,
        claim_scope=(
            "within-A fallback contact-law cross-check; not a second-simulator or "
            "hardware-validity claim"
        ),
        base_profile=profile_name,
        changed_fields=ALT_CONTACT_MODEL_CHANGED_FIELDS,
        config=build_alt_contact_model_config(
            profile_name,
            max_episode_steps=max_episode_steps,
        ),
    )


def summarize_alt_contact_model_spec(
    spec: AltContactModelSpec,
) -> dict[str, Any]:
    base = build_3dof_profile_config(
        spec.base_profile,
        max_episode_steps=spec.config.max_episode_steps,
    )
    return {
        "name": spec.name,
        "claim_scope": spec.claim_scope,
        "base_profile": spec.base_profile,
        "changed_fields": list(spec.changed_fields),
        "invariant_fields": [
            "action_dim",
            "observation_dim",
            "success_lateral_tolerance_m",
            "success_axial_tolerance_m",
            "jam_force_threshold_n",
            "jam_persistence_steps",
            "max_episode_steps",
        ],
        "field_deltas": {
            field: {
                "base": getattr(base, field),
                "alternative": getattr(spec.config, field),
            }
            for field in spec.changed_fields
        },
    }


def _evaluate_contact_model_row(
    *,
    contact_model: str,
    config: ThreeDoFInsertionConfig,
    policy_name: str,
    policy_factory: Any,
    profile: str,
    seeds: list[int],
    episodes_per_seed: int,
) -> dict[str, Any]:
    seed_summaries = [
        _evaluate_policy(
            config=config,
            policy=policy_factory(),
            episodes=int(episodes_per_seed),
            seed=seed,
            profile=profile,
        )
        for seed in seeds
    ]
    return {
        "contact_model": contact_model,
        "profile": profile,
        "policy_name": policy_name,
        "seed_count": len(seeds),
        "episodes_per_seed": int(episodes_per_seed),
        **_aggregate_seed_summaries(seed_summaries),
    }


def _paired_deltas(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (
            str(row["profile"]),
            str(row["policy_name"]),
            str(row["contact_model"]),
        ): row
        for row in rows
    }
    pairs: list[dict[str, Any]] = []
    profile_policy_pairs = sorted(
        {
            (str(row["profile"]), str(row["policy_name"]))
            for row in rows
        }
    )
    for profile, policy_name in profile_policy_pairs:
        base_row = by_key.get((profile, policy_name, BASE_CONTACT_MODEL_NAME))
        alternative_row = by_key.get((profile, policy_name, ALT_CONTACT_MODEL_NAME))
        if base_row is None or alternative_row is None:
            continue
        pairs.append(
            {
                "profile": profile,
                "policy_name": policy_name,
                "alternative_minus_base": {
                    metric_name: float(alternative_row[metric_name])
                    - float(base_row[metric_name])
                    for metric_name in SENSITIVITY_SUMMARY_METRICS
                },
            }
        )
    return pairs


def run_alt_contact_model_cross_check(
    *,
    profiles: list[str] | None = None,
    seeds: list[int] | None = None,
    episodes_per_seed: int = 1,
    policy_names: list[str] | None = None,
    max_episode_steps: int = DEFAULT_3DOF_BENCHMARK_CONTRACT.max_episode_steps,
) -> dict[str, Any]:
    if episodes_per_seed <= 0:
        raise ValueError("episodes_per_seed must be positive.")
    selected_profiles = list(profiles or DEFAULT_UNCERTAINTY_PROFILES)
    selected_seeds = [int(seed) for seed in (seeds or [0, 1, 2])]
    selected_policy_names = list(policy_names or ["fixed_impedance", "variable_impedance"])
    policy_registry = build_3dof_handcrafted_policy_registry()
    missing_policies = [name for name in selected_policy_names if name not in policy_registry]
    if missing_policies:
        raise ValueError(f"Unknown 3DoF handcrafted policies: {missing_policies}")
    rows: list[dict[str, Any]] = []
    contact_model_summaries: list[dict[str, Any]] = []
    for profile in selected_profiles:
        base_config = build_3dof_profile_config(
            profile,
            max_episode_steps=max_episode_steps,
        )
        alternative_spec = build_alt_contact_model_spec(
            profile,
            max_episode_steps=max_episode_steps,
        )
        contact_model_summaries.append(summarize_alt_contact_model_spec(alternative_spec))
        for policy_name in selected_policy_names:
            policy_factory = policy_registry[policy_name]
            rows.append(
                _evaluate_contact_model_row(
                    contact_model=BASE_CONTACT_MODEL_NAME,
                    config=base_config,
                    policy_name=policy_name,
                    policy_factory=policy_factory,
                    profile=profile,
                    seeds=selected_seeds,
                    episodes_per_seed=episodes_per_seed,
                )
            )
            rows.append(
                _evaluate_contact_model_row(
                    contact_model=ALT_CONTACT_MODEL_NAME,
                    config=alternative_spec.config,
                    policy_name=policy_name,
                    policy_factory=policy_factory,
                    profile=profile,
                    seeds=selected_seeds,
                    episodes_per_seed=episodes_per_seed,
                )
            )
    return {
        "artifact_type": "three_dof_alt_contact_model_cross_check",
        "schema_version": 1,
        "claim_scope": build_alt_contact_model_spec().claim_scope,
        "config": {
            "profiles": selected_profiles,
            "seeds": selected_seeds,
            "episodes_per_seed": int(episodes_per_seed),
            "policy_names": selected_policy_names,
            "max_episode_steps": int(max_episode_steps),
        },
        "contact_models": [BASE_CONTACT_MODEL_NAME, ALT_CONTACT_MODEL_NAME],
        "changed_fields": list(ALT_CONTACT_MODEL_CHANGED_FIELDS),
        "contact_model_summaries": _json_safe(contact_model_summaries),
        "rows": _json_safe(rows),
        "paired_deltas": _json_safe(_paired_deltas(rows)),
    }


def render_alt_contact_model_cross_check_csv(report: dict[str, Any]) -> str:
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(ALT_CONTACT_MODEL_ROW_FIELDS),
        lineterminator="\n",
    )
    writer.writeheader()
    for row in report["rows"]:
        writer.writerow({field: row.get(field, "") for field in ALT_CONTACT_MODEL_ROW_FIELDS})
    return buffer.getvalue()


def render_alt_contact_model_cross_check_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 3DoF Alternative Contact-Model Cross-Check",
        "",
        f"- claim_scope: {report['claim_scope']}",
        f"- contact_models: {', '.join(report['contact_models'])}",
        f"- changed_fields: {', '.join(report['changed_fields'])}",
        "",
        "## Rows",
        "",
        "| Contact model | Profile | Policy | Success | Jam | Peak force | Final distance | Contact steps | Contact work |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["rows"]:
        lines.append(
            "| {contact_model} | {profile} | {policy_name} | {success_rate} | {jam_rate} | "
            "{mean_peak_contact_force} | {mean_final_distance} | {mean_contact_steps} | "
            "{mean_contact_work} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Paired Deltas",
            "",
            "| Profile | Policy | Success delta | Jam delta | Peak-force delta | Final-distance delta |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for delta in report["paired_deltas"]:
        metrics = delta["alternative_minus_base"]
        lines.append(
            "| {profile} | {policy_name} | {success_rate} | {jam_rate} | "
            "{mean_peak_contact_force} | {mean_final_distance} |".format(
                profile=delta["profile"],
                policy_name=delta["policy_name"],
                success_rate=metrics["success_rate"],
                jam_rate=metrics["jam_rate"],
                mean_peak_contact_force=metrics["mean_peak_contact_force"],
                mean_final_distance=metrics["mean_final_distance"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_alt_contact_model_cross_check_artifacts(
    output_path: Path,
    report: dict[str, Any],
) -> dict[str, Path]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_path
    csv_path = output_path.with_suffix(".csv")
    markdown_path = output_path.with_suffix(".md")
    json_path.write_text(json.dumps(_json_safe(report), indent=2), encoding="utf-8")
    csv_path.write_text(render_alt_contact_model_cross_check_csv(report), encoding="utf-8")
    markdown_path.write_text(
        render_alt_contact_model_cross_check_markdown(report),
        encoding="utf-8",
    )
    return {"json": json_path, "csv": csv_path, "markdown": markdown_path}
