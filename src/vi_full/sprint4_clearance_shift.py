from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from vi_full.three_dof_benchmark import (
    build_3dof_dapg_baseline_registry,
    run_3dof_condition_across_profiles,
)
from vi_full.three_dof_profiles import (
    CLEARANCE_SHIFT_PROFILES,
    build_3dof_profile_config,
)


SPRINT4_CLEARANCE_SHIFT_SUITE_ORDER = (
    "bc_only_stable_r32_p32",
    "repaired_mainline_bc_to_ppo",
    "dapg_lite_repaired_mainline",
    "fixed_impedance_rl_stable_r32_p32",
)

SUITE_DISPLAY_NAMES = {
    "bc_only_stable_r32_p32": "BC-only (stable 32/32)",
    "repaired_mainline_bc_to_ppo": "BC -> PPO",
    "dapg_lite_repaired_mainline": "DAPG-lite",
    "fixed_impedance_rl_stable_r32_p32": "Fixed-impedance RL (stable BC 32/32)",
}

REQUIRED_METRICS = [
    "success_rate",
    "mean_final_distance_mm",
    "mean_contact_steps",
    "jam_rate",
    "mean_peak_contact_force_n",
]

CLAIM_BOUNDARY = {
    "allowed": [
        "clearance-ladder robustness claims for the selected demo-supported 3DoF suites",
        "stating how success/contact degrades from easy to hard clearance under the nominal-train contract",
        "comparing the selected four suites within this single Sprint 4A clearance-shift contract",
    ],
    "not_allowed": [
        "not a mixed-contract leaderboard",
        "not a replacement for the frozen five-profile manuscript benchmark",
        "not evidence that clearance dominates every other pressure axis in the repository",
        "not a hardware or sim-to-real claim",
    ],
}


def _profile_ladder_row(profile_name: str) -> dict[str, Any]:
    nominal = build_3dof_profile_config("nominal")
    config = build_3dof_profile_config(profile_name)
    min_clearance, max_clearance = config.clearance_range_m
    return {
        "profile_name": profile_name,
        "clearance_range_mm": [float(min_clearance * 1000.0), float(max_clearance * 1000.0)],
        "hole_xy_offset_range_mm": float(config.hole_xy_offset_range_m * 1000.0),
        "is_pure_clearance_shift": (
            config.hole_xy_offset_range_m == nominal.hole_xy_offset_range_m
            and config.wall_friction_range == nominal.wall_friction_range
            and config.force_noise_std_range == nominal.force_noise_std_range
            and config.pose_target_bias_xy_m == nominal.pose_target_bias_xy_m
            and config.orientation_perturbation_deg == nominal.orientation_perturbation_deg
        ),
    }


def build_sprint4_clearance_shift_contract() -> dict[str, Any]:
    return {
        "export_name": "sprint4_clearance_shift",
        "artifact_schema_version": 1,
        "profile_order": list(CLEARANCE_SHIFT_PROFILES),
        "suite_order": list(SPRINT4_CLEARANCE_SHIFT_SUITE_ORDER),
        "profile_ladder": [
            _profile_ladder_row(profile_name) for profile_name in CLEARANCE_SHIFT_PROFILES
        ],
        "required_metrics": list(REQUIRED_METRICS),
        "execution_boundary": {
            "mode": "train_once_eval_many_profiles",
            "train_profile": "nominal",
            "checkpoint_note": (
                "Sprint 4A evaluates each seed once and reuses the in-memory predictor "
                "across the clearance ladder because this repository does not persist "
                "paper-ready checkpoints today."
            ),
        },
        "claim_boundary": {
            "allowed": list(CLAIM_BOUNDARY["allowed"]),
            "not_allowed": list(CLAIM_BOUNDARY["not_allowed"]),
        },
    }


def _extract_profile_metrics(aggregate: dict[str, Any]) -> dict[str, float]:
    return {
        "success_rate": float(aggregate["success_rate_mean"]),
        "mean_final_distance_mm": float(aggregate["mean_final_distance_mean"]) * 1000.0,
        "mean_contact_steps": float(aggregate["mean_contact_steps_mean"]),
        "jam_rate": float(aggregate["jam_rate_mean"]),
        "mean_peak_contact_force_n": float(aggregate["mean_peak_contact_force_mean"]),
    }


def _suite_row(suite_name: str, suite_payload: dict[str, Any]) -> dict[str, Any]:
    per_profile_metrics = dict(suite_payload["per_profile_metrics"])
    missing_profiles = [
        profile_name
        for profile_name in CLEARANCE_SHIFT_PROFILES
        if profile_name not in per_profile_metrics
    ]
    if missing_profiles:
        raise ValueError(
            f"Suite '{suite_name}' is missing clearance profiles: {', '.join(missing_profiles)}"
        )

    per_profile = {
        profile_name: _extract_profile_metrics(per_profile_metrics[profile_name]["aggregate"])
        for profile_name in CLEARANCE_SHIFT_PROFILES
    }
    return {
        "suite_name": suite_name,
        "display_name": SUITE_DISPLAY_NAMES.get(suite_name, suite_name),
        "training_budget": dict(suite_payload.get("training_budget", {})),
        "per_profile": per_profile,
        "clearance_drop": {
            "success_rate_easy_to_hard": (
                per_profile["clearance_easy"]["success_rate"]
                - per_profile["clearance_hard"]["success_rate"]
            ),
            "jam_rate_hard_minus_easy": (
                per_profile["clearance_hard"]["jam_rate"]
                - per_profile["clearance_easy"]["jam_rate"]
            ),
            "mean_final_distance_mm_hard_minus_easy": (
                per_profile["clearance_hard"]["mean_final_distance_mm"]
                - per_profile["clearance_easy"]["mean_final_distance_mm"]
            ),
            "mean_contact_steps_easy_to_hard": (
                per_profile["clearance_easy"]["mean_contact_steps"]
                - per_profile["clearance_hard"]["mean_contact_steps"]
            ),
        },
    }


def build_sprint4_clearance_shift_report(
    *,
    suite_results: dict[str, Any],
    source_contract: str,
) -> dict[str, Any]:
    contract = build_sprint4_clearance_shift_contract()
    missing_suites = [
        suite_name
        for suite_name in SPRINT4_CLEARANCE_SHIFT_SUITE_ORDER
        if suite_name not in suite_results
    ]
    if missing_suites:
        raise ValueError(
            f"Missing Sprint 4A suite results: {', '.join(missing_suites)}"
        )

    suite_rows = [
        _suite_row(suite_name, suite_results[suite_name])
        for suite_name in SPRINT4_CLEARANCE_SHIFT_SUITE_ORDER
    ]
    return {
        **contract,
        "source_contract": str(source_contract),
        "suite_rows": suite_rows,
    }


def render_sprint4_clearance_shift_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Sprint 4 Clearance Shift",
        "",
        f"Source contract: {report['source_contract']}",
        "",
        report["execution_boundary"]["checkpoint_note"],
        "",
        "## Clearance Ladder",
        "",
        "| Profile | Clearance range (mm) | Pure clearance shift |",
        "| --- | --- | --- |",
    ]
    for row in report["profile_ladder"]:
        clearance_range = (
            f"{row['clearance_range_mm'][0]:.3f} - {row['clearance_range_mm'][1]:.3f}"
        )
        lines.append(
            f"| {row['profile_name']} | {clearance_range} | {str(row['is_pure_clearance_shift']).lower()} |"
        )

    lines.extend(
        [
            "",
            "## Suite Summary",
            "",
            "| Suite | easy success | nominal success | clearance_hard success | success drop | hard jam | hard final dist (mm) |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["suite_rows"]:
        lines.append(
            "| "
            f"{row['display_name']} | "
            f"{row['per_profile']['clearance_easy']['success_rate']:.3f} | "
            f"{row['per_profile']['nominal']['success_rate']:.3f} | "
            f"{row['per_profile']['clearance_hard']['success_rate']:.3f} | "
            f"{row['clearance_drop']['success_rate_easy_to_hard']:.3f} | "
            f"{row['per_profile']['clearance_hard']['jam_rate']:.3f} | "
            f"{row['per_profile']['clearance_hard']['mean_final_distance_mm']:.3f} |"
        )

    lines.extend(["", "## Claim Boundary", "", "Allowed:"])
    for item in report["claim_boundary"]["allowed"]:
        lines.append(f"- {item}")
    lines.extend(["", "Not allowed:"])
    for item in report["claim_boundary"]["not_allowed"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def export_sprint4_clearance_shift_artifacts(
    report: dict[str, Any],
    output_dir: Path,
) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "sprint4_clearance_shift.json"
    csv_path = output_dir / "sprint4_clearance_shift.csv"
    markdown_path = output_dir / "sprint4_clearance_shift.md"

    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "suite_name",
                "display_name",
                "profile_name",
                "success_rate",
                "mean_final_distance_mm",
                "mean_contact_steps",
                "jam_rate",
                "mean_peak_contact_force_n",
                "success_rate_easy_to_hard",
            ],
        )
        writer.writeheader()
        for row in report["suite_rows"]:
            for profile_name in report["profile_order"]:
                profile_metrics = row["per_profile"][profile_name]
                writer.writerow(
                    {
                        "suite_name": row["suite_name"],
                        "display_name": row["display_name"],
                        "profile_name": profile_name,
                        **profile_metrics,
                        "success_rate_easy_to_hard": row["clearance_drop"][
                            "success_rate_easy_to_hard"
                        ],
                    }
                )

    markdown_path.write_text(
        render_sprint4_clearance_shift_markdown(report),
        encoding="utf-8",
    )
    return {
        "json_path": json_path,
        "csv_path": csv_path,
        "markdown_path": markdown_path,
    }


def _run_registry_suite_across_clearance_profiles(
    *,
    suite_name: str,
    train_seeds: list[int],
    episodes_per_seed: int,
    max_episode_steps: int,
) -> dict[str, Any]:
    registry = build_3dof_dapg_baseline_registry()
    if suite_name not in registry:
        raise ValueError(f"Unknown Sprint 4A suite: {suite_name}")

    suite_overrides = dict(registry[suite_name])
    total_timesteps = int(suite_overrides.pop("total_timesteps", 128))
    result = run_3dof_condition_across_profiles(
        condition_name=suite_name,
        train_seeds=list(train_seeds),
        episodes_per_seed=int(episodes_per_seed),
        max_episode_steps=int(max_episode_steps),
        uncertainty_profiles=list(CLEARANCE_SHIFT_PROFILES),
        total_timesteps=total_timesteps,
        train_uncertainty_profile="nominal",
        train_overrides=suite_overrides,
    )
    return {
        "suite_name": suite_name,
        "training_budget": dict(result["training_budget"]),
        "per_profile_metrics": dict(result["per_profile_metrics"]),
    }


def run_sprint4_clearance_shift_sweep(
    *,
    train_seeds: list[int],
    episodes_per_seed: int = 100,
    max_episode_steps: int = 64,
) -> dict[str, Any]:
    suite_results = {
        suite_name: _run_registry_suite_across_clearance_profiles(
            suite_name=suite_name,
            train_seeds=list(train_seeds),
            episodes_per_seed=int(episodes_per_seed),
            max_episode_steps=int(max_episode_steps),
        )
        for suite_name in SPRINT4_CLEARANCE_SHIFT_SUITE_ORDER
    }
    return build_sprint4_clearance_shift_report(
        suite_results=suite_results,
        source_contract="3DoF nominal-train Sprint 4A clearance-shift stress sweep",
    )
