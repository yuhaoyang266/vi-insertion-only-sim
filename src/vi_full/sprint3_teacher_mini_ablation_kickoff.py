from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

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


def _save_figure_bundle(
    fig,
    *,
    output_dir: Path,
    stem: str,
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return pdf_path, png_path


def export_sprint3_teacher_mini_ablation_kickoff_matrix_figure(
    kickoff: dict[str, Any],
    output_dir: Path,
    *,
    stem: str = "sprint3_teacher_mini_ablation_kickoff_matrix",
) -> tuple[Path, Path]:
    row_order = ["support_rich", "support_poor"]
    col_order = ["many_demo", "few_demo"]
    row_labels = {
        "support_rich": "support rich",
        "support_poor": "support poor",
    }
    col_labels = {
        "many_demo": "many demo",
        "few_demo": "few demo",
    }
    fill_colors = {
        "support_rich": "#D9EAF7",
        "support_poor": "#F9DDDA",
    }
    matrix = {
        (row["teacher_support_quality"], row["demo_budget_label"]): row
        for row in kickoff["condition_matrix"]
    }

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.8), constrained_layout=True)
    matrix_ax, notes_ax = axes
    matrix_ax.set_xlim(0.0, 2.0)
    matrix_ax.set_ylim(0.0, 2.0)
    matrix_ax.set_xticks([0.5, 1.5], [col_labels[label] for label in col_order])
    matrix_ax.set_yticks([0.5, 1.5], [row_labels[label] for label in row_order])
    matrix_ax.set_xlabel("demo rollout budget")
    matrix_ax.set_ylabel("teacher support quality")
    matrix_ax.set_title("Sprint 3 kickoff boundary matrix", fontsize=12, fontweight="bold")
    matrix_ax.invert_yaxis()
    matrix_ax.set_aspect("equal")

    for row_index, row_key in enumerate(row_order):
        for col_index, col_key in enumerate(col_order):
            entry = matrix[(row_key, col_key)]
            x_pos = float(col_index)
            y_pos = float(row_index)
            matrix_ax.add_patch(
                Rectangle(
                    (x_pos, y_pos),
                    1.0,
                    1.0,
                    facecolor=fill_colors[row_key],
                    edgecolor="#555555",
                    linewidth=1.2,
                )
            )
            matrix_ax.text(
                x_pos + 0.5,
                y_pos + 0.30,
                entry["teacher_preset_name"].replace("teacher_", "").replace("_", "/"),
                ha="center",
                va="center",
                fontsize=9.0,
                fontweight="bold",
            )
            matrix_ax.text(
                x_pos + 0.5,
                y_pos + 0.54,
                f"rollouts={entry['bc_rollout_episodes']}",
                ha="center",
                va="center",
                fontsize=8.6,
            )
            matrix_ax.text(
                x_pos + 0.5,
                y_pos + 0.76,
                f"steps={entry['bc_pretrain_steps']} / {entry['total_timesteps']}",
                ha="center",
                va="center",
                fontsize=8.6,
            )

    for x_pos in [0.0, 1.0, 2.0]:
        matrix_ax.plot([x_pos, x_pos], [0.0, 2.0], color="#555555", linewidth=1.0)
    for y_pos in [0.0, 1.0, 2.0]:
        matrix_ax.plot([0.0, 2.0], [y_pos, y_pos], color="#555555", linewidth=1.0)

    notes_ax.set_axis_off()
    notes_ax.set_title("Frozen controls and claim boundary", fontsize=12, fontweight="bold")
    notes_ax.text(
        0.0,
        0.94,
        "Fixed controls",
        fontsize=10.5,
        fontweight="bold",
        transform=notes_ax.transAxes,
    )
    notes_ax.text(
        0.0,
        0.74,
        "BC steps: 32\nBC batch: 64\nPPO steps: 128\nProfiles: nominal + 4 stress profiles",
        fontsize=9.2,
        transform=notes_ax.transAxes,
        linespacing=1.35,
    )
    notes_ax.text(
        0.0,
        0.48,
        "Required metrics",
        fontsize=10.5,
        fontweight="bold",
        transform=notes_ax.transAxes,
    )
    notes_ax.text(
        0.0,
        0.24,
        "success_rate\nmean_final_distance_mm\nmean_contact_steps\njam_rate\nSCI / support_cell_coverage",
        fontsize=9.2,
        transform=notes_ax.transAxes,
        linespacing=1.35,
    )
    notes_ax.text(
        0.0,
        0.04,
        "Boundary only: not a leaderboard,\nnot a finished ablation result.",
        fontsize=9.0,
        transform=notes_ax.transAxes,
    )
    fig.suptitle(
        "Teacher support quality x demo budget boundary",
        fontsize=13,
        fontweight="bold",
    )
    return _save_figure_bundle(fig, output_dir=output_dir, stem=stem)


def export_sprint3_teacher_mini_ablation_kickoff_artifacts(
    output_dir: Path,
) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    kickoff = build_sprint3_teacher_mini_ablation_kickoff()
    json_path = output_dir / "sprint3_teacher_mini_ablation_kickoff.json"
    csv_path = output_dir / "sprint3_teacher_mini_ablation_kickoff.csv"
    markdown_path = output_dir / "sprint3_teacher_mini_ablation_kickoff.md"
    json_path.write_text(
        json.dumps(kickoff, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "condition_id",
                "suite_name",
                "teacher_preset_name",
                "teacher_motion_rule",
                "teacher_impedance_rule",
                "teacher_support_quality",
                "demo_budget_label",
                "bc_rollout_episodes",
                "bc_pretrain_steps",
                "bc_batch_size",
                "total_timesteps",
                "policy_init",
                "source_contract",
            ],
        )
        writer.writeheader()
        for row in kickoff["condition_matrix"]:
            writer.writerow(
                {
                    key: row[key]
                    for key in writer.fieldnames
                }
            )
    markdown_path.write_text(
        render_sprint3_teacher_mini_ablation_kickoff_markdown(kickoff),
        encoding="utf-8",
    )
    pdf_path, png_path = export_sprint3_teacher_mini_ablation_kickoff_matrix_figure(
        kickoff,
        output_dir,
    )
    return {
        "json_path": json_path,
        "csv_path": csv_path,
        "markdown_path": markdown_path,
        "pdf_path": pdf_path,
        "png_path": png_path,
    }
