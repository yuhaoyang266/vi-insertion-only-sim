from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]

PURE_RL_METHOD_ORDER = (
    "ppo_no_bc",
    "sac_no_bc",
    "td3_no_bc",
)

ANCHOR_SPECS = {
    "bc_only_stable_r32_p32": {
        "label": "BC-only (stable 32/32)",
        "method_family": "imitation_anchor",
        "evidence_role": "support_reopens_contact",
    },
    "repaired_mainline_bc_to_ppo": {
        "label": "BC -> PPO",
        "method_family": "demo_augmented_rl",
        "evidence_role": "support_reopens_contact",
    },
    "dapg_lite_repaired_mainline": {
        "label": "DAPG-lite",
        "method_family": "demo_augmented_rl",
        "evidence_role": "support_reopens_contact",
    },
    "fixed_impedance_rl_stable_r32_p32": {
        "label": "Fixed-impedance RL (stable BC 32/32)",
        "method_family": "fixed_impedance",
        "evidence_role": "mechanics_anchor",
    },
}

ROW_FIELD_ORDER = [
    "method_name",
    "label",
    "method_family",
    "source_contract",
    "benchmark",
    "train_budget",
    "entered_contact",
    "success_rate",
    "mean_final_distance_mm",
    "mean_contact_steps",
    "jam_rate",
    "mean_peak_contact_force_n",
    "evidence_role",
    "allowed_claim",
    "not_allowed_claim",
    "source_report",
]

PDF_METADATA = {
    "CreationDate": None,
    "ModDate": None,
}

CONFIRM_SUMMARY_REQUIRED_FIELDS = (
    "best_budget",
    "best_final_distance_mm",
    "entered_contact",
    "mean_success_across_budgets",
    "mean_contact_steps_across_budgets",
)

BENCHMARK_CONFIG_REQUIRED_FIELDS = (
    "timesteps",
    "base_bc_rollout_episodes",
    "base_bc_pretrain_steps",
)

BENCHMARK_FIVE_PROFILE_REQUIRED_FIELDS = (
    "success_rate_mean_over_profiles",
    "mean_final_distance_mean_over_profiles",
    "jam_rate_mean_over_profiles",
    "mean_peak_contact_force_mean_over_profiles",
    "mean_contact_steps_mean_over_profiles",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _provenance_path(path: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def _as_float(value: object) -> float:
    if value is None:
        return 0.0
    return float(value)


def _round_metric(value: object) -> float:
    return round(_as_float(value), 2)


def _require_field(mapping: dict[str, Any], field_name: str, *, context: str) -> Any:
    if field_name not in mapping:
        raise ValueError(
            f"Evidence matrix missing required field '{field_name}' in {context}."
        )
    value = mapping[field_name]
    if value is None:
        raise ValueError(
            f"Evidence matrix missing required field '{field_name}' in {context}."
        )
    return value


def _validate_confirm_report(confirm: dict[str, Any]) -> None:
    if not bool(confirm.get("grid_complete")):
        raise ValueError("Evidence matrix requires a complete Branch A confirm report.")
    if str(confirm.get("selected_branch")) != "branch_a":
        raise ValueError("Evidence matrix requires a complete Branch A confirm report.")

    summaries = {
        str(row["method_name"]): row for row in confirm.get("method_summaries", [])
    }
    missing_methods = [
        method_name for method_name in PURE_RL_METHOD_ORDER if method_name not in summaries
    ]
    if missing_methods:
        raise ValueError("Evidence matrix requires a complete Branch A confirm report.")

    best_distance_proxy_method = str(
        _require_field(
            confirm,
            "best_distance_proxy_method",
            context="confirm report",
        )
    )
    if best_distance_proxy_method not in PURE_RL_METHOD_ORDER:
        raise ValueError(
            "Evidence matrix requires best_distance_proxy_method to name one of the pure-RL rows."
        )

    for method_name in PURE_RL_METHOD_ORDER:
        summary = summaries[method_name]
        for field_name in CONFIRM_SUMMARY_REQUIRED_FIELDS:
            _require_field(
                summary,
                field_name,
                context=f"confirm summary '{method_name}'",
            )


def _validate_benchmark_report(benchmark: dict[str, Any]) -> None:
    learned_results = dict(benchmark.get("learned_results", {}))
    missing_suites = [
        suite_name for suite_name in ANCHOR_SPECS if suite_name not in learned_results
    ]
    if missing_suites:
        raise ValueError(
            "Evidence matrix requires all demo-supported anchors in the benchmark report."
        )

    config = dict(benchmark.get("config", {}))
    for field_name in BENCHMARK_CONFIG_REQUIRED_FIELDS:
        _require_field(
            config,
            field_name,
            context="benchmark config",
        )

    for suite_name in ANCHOR_SPECS:
        suite_payload = dict(learned_results[suite_name])
        metrics = dict(
            _require_field(
                suite_payload,
                "five_profile_mean",
                context=f"benchmark suite '{suite_name}'",
            )
        )
        for field_name in BENCHMARK_FIVE_PROFILE_REQUIRED_FIELDS:
            _require_field(
                metrics,
                field_name,
                context=f"benchmark suite '{suite_name}'",
            )


def _pure_rl_allowed_claim(
    method_name: str,
    *,
    best_distance_proxy_method: str,
) -> str:
    if method_name == best_distance_proxy_method:
        return (
            "Best pure-RL distance proxy under the nominal-only pilot contract, but still zero-contact."
        )
    return "Pure RL stays outside the useful-contact gate under the nominal-only pilot contract."


def _pure_rl_not_allowed_claim(
    method_name: str,
    *,
    best_distance_proxy_method: str,
    label: str,
) -> str:
    if method_name == best_distance_proxy_method:
        return (
            f"Do not claim {label} solves insertion, enters useful contact, "
            "or wins a mixed-contract leaderboard."
        )
    return "Do not claim this method reaches useful contact or compare it as a mixed-contract leaderboard winner."


def _anchor_allowed_claim(method_name: str) -> str:
    if method_name == "bc_only_stable_r32_p32":
        return "Demonstration support alone reopens contact and near-ceiling success under the five-profile benchmark."
    if method_name == "fixed_impedance_rl_stable_r32_p32":
        return "Fixed impedance still enters contact and succeeds under support, so this row acts as a mechanics anchor."
    return "Demo-supported RL reopens contact and non-zero success under the five-profile benchmark."


def _anchor_not_allowed_claim(method_name: str) -> str:
    if method_name == "fixed_impedance_rl_stable_r32_p32":
        return "Do not read this row as proof that impedance type alone determines learnability or as a mixed-contract leaderboard winner."
    return "Do not compare this row as a mixed-contract leaderboard winner against nominal-only pure-RL pilot rows."


def _build_pure_rl_rows(
    confirm: dict[str, Any],
    *,
    confirm_report_path: Path,
) -> list[dict[str, Any]]:
    summaries = {
        str(row["method_name"]): row for row in confirm.get("method_summaries", [])
    }
    best_distance_proxy_method = str(confirm["best_distance_proxy_method"])
    direct_source = _provenance_path(confirm_report_path)
    rows: list[dict[str, Any]] = []
    for method_name in PURE_RL_METHOD_ORDER:
        summary = summaries[method_name]
        label = str(summary.get("label", method_name))
        rows.append(
            {
                "method_name": method_name,
                "label": label,
                "method_family": "pure_rl",
                "source_contract": "nominal-only pilot",
                "benchmark": "3dof_cross_family_confirm",
                "train_budget": str(int(summary.get("best_budget", 0))),
                "entered_contact": bool(summary.get("entered_contact")),
                "success_rate": _round_metric(
                    summary.get("mean_success_across_budgets", 0.0)
                ),
                "mean_final_distance_mm": _round_metric(
                    summary.get("best_final_distance_mm", 0.0)
                ),
                "mean_contact_steps": _round_metric(
                    summary.get("mean_contact_steps_across_budgets", 0.0)
                ),
                "jam_rate": 0.0,
                "mean_peak_contact_force_n": 0.0,
                "evidence_role": "contact_gate_negative",
                "allowed_claim": _pure_rl_allowed_claim(
                    method_name,
                    best_distance_proxy_method=best_distance_proxy_method,
                ),
                "not_allowed_claim": _pure_rl_not_allowed_claim(
                    method_name,
                    best_distance_proxy_method=best_distance_proxy_method,
                    label=label,
                ),
                "source_report": direct_source,
            }
        )
    return rows


def _extract_benchmark_metrics(suite_payload: dict[str, Any]) -> dict[str, float]:
    metrics = dict(
        _require_field(
            suite_payload,
            "five_profile_mean",
            context="benchmark suite payload",
        )
    )
    return {
        "success_rate": _round_metric(
            _require_field(
                metrics,
                "success_rate_mean_over_profiles",
                context="benchmark five_profile_mean",
            )
        ),
        "mean_final_distance_mm": _round_metric(
            1000.0
            * _as_float(
                _require_field(
                    metrics,
                    "mean_final_distance_mean_over_profiles",
                    context="benchmark five_profile_mean",
                )
            )
        ),
        "jam_rate": _round_metric(
            _require_field(
                metrics,
                "jam_rate_mean_over_profiles",
                context="benchmark five_profile_mean",
            )
        ),
        "mean_peak_contact_force_n": _round_metric(
            _require_field(
                metrics,
                "mean_peak_contact_force_mean_over_profiles",
                context="benchmark five_profile_mean",
            )
        ),
        "mean_contact_steps": _round_metric(
            _require_field(
                metrics,
                "mean_contact_steps_mean_over_profiles",
                context="benchmark five_profile_mean",
            )
        ),
    }


def _benchmark_train_budget(suite_name: str, config: dict[str, Any]) -> str:
    bc_rollouts = int(
        _require_field(
            config,
            "base_bc_rollout_episodes",
            context="benchmark config",
        )
    )
    bc_pretrain = int(
        _require_field(
            config,
            "base_bc_pretrain_steps",
            context="benchmark config",
        )
    )
    timesteps = int(_require_field(config, "timesteps", context="benchmark config"))
    bc_text = f"BC {bc_rollouts}/{bc_pretrain}"
    if suite_name == "bc_only_stable_r32_p32":
        return bc_text
    if suite_name == "dapg_lite_repaired_mainline":
        return f"{bc_text} + DAPG-lite {timesteps}"
    return f"{bc_text} + PPO {timesteps}"


def _build_anchor_rows(
    benchmark: dict[str, Any],
    *,
    benchmark_report_path: Path,
) -> list[dict[str, Any]]:
    learned_results = dict(benchmark.get("learned_results", {}))
    config = dict(benchmark.get("config", {}))
    rows: list[dict[str, Any]] = []
    for method_name, spec in ANCHOR_SPECS.items():
        metrics = _extract_benchmark_metrics(learned_results[method_name])
        rows.append(
            {
                "method_name": method_name,
                "label": spec["label"],
                "method_family": spec["method_family"],
                "source_contract": "five-profile benchmark",
                "benchmark": "3dof_main_benchmark",
                "train_budget": _benchmark_train_budget(method_name, config),
                "entered_contact": metrics["mean_contact_steps"] > 0.0
                or metrics["success_rate"] > 0.0,
                "success_rate": metrics["success_rate"],
                "mean_final_distance_mm": metrics["mean_final_distance_mm"],
                "mean_contact_steps": metrics["mean_contact_steps"],
                "jam_rate": metrics["jam_rate"],
                "mean_peak_contact_force_n": metrics["mean_peak_contact_force_n"],
                "evidence_role": spec["evidence_role"],
                "allowed_claim": _anchor_allowed_claim(method_name),
                "not_allowed_claim": _anchor_not_allowed_claim(method_name),
                "source_report": _provenance_path(benchmark_report_path),
            }
        )
    return rows


def build_3dof_evidence_matrix(
    *,
    confirm_report_path: Path,
    benchmark_report_path: Path,
) -> dict[str, Any]:
    confirm_report_path = Path(confirm_report_path)
    benchmark_report_path = Path(benchmark_report_path)
    confirm = _load_json(confirm_report_path)
    benchmark = _load_json(benchmark_report_path)

    _validate_confirm_report(confirm)
    _validate_benchmark_report(benchmark)

    rows = _build_pure_rl_rows(
        confirm,
        confirm_report_path=confirm_report_path,
    ) + _build_anchor_rows(
        benchmark,
        benchmark_report_path=benchmark_report_path,
    )
    return {
        "report_name": "three_dof_evidence_matrix",
        "source_artifacts": {
            "confirm_report": _provenance_path(confirm_report_path),
            "benchmark_report": _provenance_path(benchmark_report_path),
        },
        "matrix_contract": {
            "mixed_contracts": True,
            "allowed": (
                "Use only for contact-gate contrast across nominal-only pilot and five-profile benchmark evidence."
            ),
            "not_allowed": (
                "Do not read this matrix as a mixed-contract leaderboard or direct across-row ranking."
            ),
            "row_source_rule": (
                "Each row cites the direct confirm or benchmark JSON input passed to the exporter; "
                "do not infer row provenance from separate paper table exports."
            ),
        },
        "row_count": len(rows),
        "row_order": [row["method_name"] for row in rows],
        "rows": rows,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def export_3dof_evidence_matrix_json(
    *,
    confirm_report_path: Path,
    benchmark_report_path: Path,
    output_dir: Path,
    stem: str = "three_dof_evidence_matrix",
) -> tuple[Path, dict[str, Any]]:
    payload = build_3dof_evidence_matrix(
        confirm_report_path=confirm_report_path,
        benchmark_report_path=benchmark_report_path,
    )
    json_path = Path(output_dir) / f"{stem}.json"
    return _write_json(json_path, payload), payload


def export_3dof_evidence_matrix_csv(
    payload: dict[str, Any],
    output_dir: Path,
    filename: str = "three_dof_evidence_matrix.csv",
) -> Path:
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELD_ORDER)
        writer.writeheader()
        for row in payload["rows"]:
            writer.writerow({field: row[field] for field in ROW_FIELD_ORDER})
    return output_path


def render_3dof_evidence_matrix_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 3DoF Evidence Matrix",
        "",
        f"Confirm source: `{payload['source_artifacts']['confirm_report']}`",
        f"Benchmark source: `{payload['source_artifacts']['benchmark_report']}`",
        "",
        "## Mixed-Contract Boundary",
        "",
        f"- Allowed: {payload['matrix_contract']['allowed']}",
        f"- Not allowed: {payload['matrix_contract']['not_allowed']}",
        f"- Row sources: {payload['matrix_contract']['row_source_rule']}",
        "",
        "## Matrix",
        "",
        "| Method | Family | Source contract | Contact? | Success | Final dist (mm) | Contact steps | Role |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| "
            f"{row['label']} | "
            f"{row['method_family']} | "
            f"{row['source_contract']} | "
            f"{'yes' if row['entered_contact'] else 'no'} | "
            f"{row['success_rate']:.2f} | "
            f"{row['mean_final_distance_mm']:.2f} | "
            f"{row['mean_contact_steps']:.2f} | "
            f"{row['evidence_role']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for row in payload["rows"]:
        lines.append(f"- `{row['method_name']}` allowed: {row['allowed_claim']}")
        lines.append(f"- `{row['method_name']}` not allowed: {row['not_allowed_claim']}")
    return "\n".join(lines) + "\n"


def export_3dof_evidence_matrix_markdown(
    payload: dict[str, Any],
    output_dir: Path,
    filename: str = "three_dof_evidence_matrix.md",
) -> Path:
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_3dof_evidence_matrix_markdown(payload),
        encoding="utf-8",
    )
    return output_path


def export_contact_gate_matrix_figure(
    payload: dict[str, Any],
    output_dir: Path,
    stem: str = "three_dof_contact_gate_matrix",
) -> tuple[Path, Path]:
    rows = list(payload["rows"])
    matrix = [
        [1.0 if row["entered_contact"] else 0.0, _as_float(row["success_rate"])]
        for row in rows
    ]
    fig_height = max(4.0, 0.6 * len(rows))
    fig, ax = plt.subplots(figsize=(7.5, fig_height), constrained_layout=True)
    image = ax.imshow(matrix, aspect="auto", cmap="YlGn", vmin=0.0, vmax=1.0)
    ax.set_title("3DoF contact gate evidence matrix")
    ax.set_xticks([0, 1], ["Entered contact", "Success rate"])
    ax.set_yticks(
        list(range(len(rows))),
        [f"{row['label']} [{row['source_contract']}]" for row in rows],
    )
    for row_index, row in enumerate(rows):
        ax.text(
            0,
            row_index,
            "yes" if row["entered_contact"] else "no",
            ha="center",
            va="center",
            color="black",
            fontsize=9,
        )
        ax.text(
            1,
            row_index,
            f"{row['success_rate']:.2f}",
            ha="center",
            va="center",
            color="black",
            fontsize=9,
        )
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("0 to 1 scale")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / f"{stem}.png"
    pdf_path = output_dir / f"{stem}.pdf"
    fig.savefig(png_path, dpi=200)
    fig.savefig(pdf_path, metadata=PDF_METADATA)
    plt.close(fig)
    return png_path, pdf_path


def export_3dof_evidence_matrix_artifacts(
    *,
    confirm_report_path: Path,
    benchmark_report_path: Path,
    output_dir: Path,
) -> dict[str, Path | tuple[Path, Path]]:
    json_path, payload = export_3dof_evidence_matrix_json(
        confirm_report_path=confirm_report_path,
        benchmark_report_path=benchmark_report_path,
        output_dir=output_dir,
    )
    csv_path = export_3dof_evidence_matrix_csv(payload, output_dir)
    markdown_path = export_3dof_evidence_matrix_markdown(payload, output_dir)
    figure_paths = export_contact_gate_matrix_figure(payload, output_dir)
    return {
        "json": json_path,
        "csv": csv_path,
        "markdown": markdown_path,
        "contact_gate_matrix": figure_paths,
    }
