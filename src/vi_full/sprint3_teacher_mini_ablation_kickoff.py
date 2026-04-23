from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from vi_full.three_dof_policies import resolve_3dof_teacher_spec


UNCERTAINTY_PROFILES = [
    "nominal",
    "tight_clearance",
    "high_friction",
    "offset_bias",
    "noisy_force",
]

REQUIRED_METRICS = [
    "success_rate",
    "mean_final_distance_mm",
    "mean_contact_steps",
    "jam_rate",
    "mean_peak_contact_force_n",
    "support_coverage_index",
    "support_cell_coverage",
]

EXCLUDED_AXES = [
    "BC pretrain-step sweep",
    "policy initialization sweep",
    "teacher/no-teacher pure-RL control",
    "full motion-rule x impedance-rule appendix sweep",
]


def _condition_row(
    *,
    condition_id: str,
    suite_name: str,
    teacher_preset_name: str,
    teacher_support_quality: str,
    demo_budget_label: str,
    bc_rollout_episodes: int,
) -> dict[str, Any]:
    teacher_spec = resolve_3dof_teacher_spec(policy_name=teacher_preset_name)
    return {
        "condition_id": condition_id,
        "suite_name": suite_name,
        "teacher_preset_name": teacher_preset_name,
        "teacher_motion_rule": teacher_spec.motion_rule,
        "teacher_impedance_rule": teacher_spec.impedance_rule,
        "teacher_support_quality": teacher_support_quality,
        "demo_budget_label": demo_budget_label,
        "bc_rollout_episodes": int(bc_rollout_episodes),
        "bc_pretrain_steps": 32,
        "bc_batch_size": 64,
        "total_timesteps": 128,
        "policy_init": "bc_to_ppo_from_scratch",
        "uncertainty_profiles": list(UNCERTAINTY_PROFILES),
        "source_contract": "five-profile 3DoF teacher-coupled benchmark",
    }


def build_sprint3_teacher_mini_ablation_kickoff() -> dict[str, Any]:
    rows = [
        _condition_row(
            condition_id="support_rich_many_demo",
            suite_name="teacher_variable_variable__sprint3_r32_p32",
            teacher_preset_name="teacher_variable_variable",
            teacher_support_quality="support_rich",
            demo_budget_label="many_demo",
            bc_rollout_episodes=32,
        ),
        _condition_row(
            condition_id="support_rich_few_demo",
            suite_name="teacher_variable_variable__sprint3_r8_p32",
            teacher_preset_name="teacher_variable_variable",
            teacher_support_quality="support_rich",
            demo_budget_label="few_demo",
            bc_rollout_episodes=8,
        ),
        _condition_row(
            condition_id="support_poor_many_demo",
            suite_name="teacher_pose_fixed__sprint3_r32_p32",
            teacher_preset_name="teacher_pose_fixed",
            teacher_support_quality="support_poor",
            demo_budget_label="many_demo",
            bc_rollout_episodes=32,
        ),
        _condition_row(
            condition_id="support_poor_few_demo",
            suite_name="teacher_pose_fixed__sprint3_r8_p32",
            teacher_preset_name="teacher_pose_fixed",
            teacher_support_quality="support_poor",
            demo_budget_label="few_demo",
            bc_rollout_episodes=8,
        ),
    ]
    return {
        "export_name": "sprint3_teacher_mini_ablation_kickoff",
        "artifact_schema_version": 1,
        "target_question": {
            "plain_text": (
                "Does support-rich teacher demonstration reopen the contact gate, "
                "and does that directional claim survive a reduced demo rollout budget?"
            ),
            "primary_axis": "teacher_support_quality",
            "secondary_axis": "demo_rollout_budget",
        },
        "condition_count": len(rows),
        "condition_matrix": rows,
        "frozen_controls": {
            "bc_pretrain_steps": 32,
            "bc_batch_size": 64,
            "total_timesteps": 128,
            "policy_init": "bc_to_ppo_from_scratch",
            "uncertainty_profiles": list(UNCERTAINTY_PROFILES),
        },
        "required_metrics": list(REQUIRED_METRICS),
        "excluded_axes": list(EXCLUDED_AXES),
        "closure_criteria": {
            "artifact_reproducible": True,
            "table_plot_claim_boundary_explicit": True,
            "contract_tests_required": True,
            "paper_facing_text_must_not_overclaim": True,
        },
        "claim_boundary": {
            "allowed": [
                "directional teacher-coupling evidence under the fixed 3DoF benchmark contract",
                "contact-gate contrast between support-rich and support-poor teacher demonstrations",
                "demo-budget sensitivity within the frozen BC-to-PPO initialization path",
            ],
            "not_allowed": [
                "teacher-independent causal claim",
                "general robotics or sim-to-real claim",
                "cross-contract leaderboard",
                "claim that training completion alone closes Sprint 3",
            ],
        },
    }


def render_sprint3_teacher_mini_ablation_kickoff_markdown(
    kickoff: dict[str, Any],
) -> str:
    lines = [
        "# Sprint 3 Teacher Mini-Ablation Kickoff",
        "",
        "Boundary: teacher support quality x demo rollout budget.",
        "",
        f"Target question: {kickoff['target_question']['plain_text']}",
        "",
        "## Condition Matrix",
        "",
        "| Condition | Teacher preset | Support quality | Demo budget | BC rollouts | BC steps | PPO steps |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in kickoff["condition_matrix"]:
        lines.append(
            "| "
            f"{row['condition_id']} | "
            f"{row['teacher_preset_name']} | "
            f"{row['teacher_support_quality']} | "
            f"{row['demo_budget_label']} | "
            f"{row['bc_rollout_episodes']} | "
            f"{row['bc_pretrain_steps']} | "
            f"{row['total_timesteps']} |"
        )

    lines.extend(
        [
            "",
            "## Fixed Metrics",
            "",
            ", ".join(f"`{metric}`" for metric in kickoff["required_metrics"]),
            "",
            "## Frozen Controls",
            "",
            "- BC pretrain steps: `32`",
            "- BC batch size: `64`",
            "- PPO fine-tune steps: `128`",
            "- Policy init: `bc_to_ppo_from_scratch`",
            "- Profiles: `nominal`, `tight_clearance`, `high_friction`, `offset_bias`, `noisy_force`",
            "",
            "## Closure Criteria",
            "",
            "- artifact reproducible",
            "- table/plot claim boundary explicit",
            "- contract tests required",
            "- paper-facing text must not overclaim",
            "",
            "## Claim Boundary",
            "",
            "Allowed:",
        ]
    )
    for item in kickoff["claim_boundary"]["allowed"]:
        lines.append(f"- {item}")
    lines.extend(["", "Not allowed:"])
    for item in kickoff["claim_boundary"]["not_allowed"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "This is not a leaderboard; it is a small teacher-coupled contact-gate check.",
        ]
    )
    return "\n".join(lines) + "\n"


def export_sprint3_teacher_mini_ablation_kickoff_artifacts(
    output_dir: Path,
) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    kickoff = build_sprint3_teacher_mini_ablation_kickoff()
    json_path = output_dir / "sprint3_teacher_mini_ablation_kickoff.json"
    markdown_path = output_dir / "sprint3_teacher_mini_ablation_kickoff.md"
    json_path.write_text(
        json.dumps(kickoff, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_sprint3_teacher_mini_ablation_kickoff_markdown(kickoff),
        encoding="utf-8",
    )
    return {
        "json_path": json_path,
        "markdown_path": markdown_path,
    }
