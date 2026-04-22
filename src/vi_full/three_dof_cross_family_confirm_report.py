from __future__ import annotations

from datetime import datetime
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


EXPECTED_METHOD_COUNT = 3
EXPECTED_BUDGET_COUNT = 3
EXPECTED_CHUNK_COUNT = EXPECTED_METHOD_COUNT * EXPECTED_BUDGET_COUNT
SUMMARY_ROW_REQUIRED_FIELDS = (
    "success_rate",
    "mean_final_distance_mm",
    "mean_contact_steps",
    "jam_rate",
    "mean_peak_contact_force_n",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _as_float(value: object) -> float:
    if value is None:
        return 0.0
    return float(value)


def _validate_complete_grid(report: dict[str, Any]) -> dict[str, Any]:
    expected_grid = dict(report.get("expected_grid", {}))
    expected_count = int(expected_grid.get("expected_chunk_count", 0))
    completed_count = int(expected_grid.get("completed_chunk_count", 0))
    missing_count = int(expected_grid.get("missing_chunk_count", 0))
    if (
        expected_count != EXPECTED_CHUNK_COUNT
        or completed_count != EXPECTED_CHUNK_COUNT
        or missing_count != 0
    ):
        raise ValueError(
            "Confirm report requires a complete 9-chunk grid "
            f"(expected={expected_count}, completed={completed_count}, missing={missing_count})."
        )
    return expected_grid


def _rows_by_method(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["method_name"]), []).append(dict(row))
    for method_rows in grouped.values():
        method_rows.sort(key=lambda row: int(row["budget"]))
    return grouped


def _validate_summary_row_grid(
    rows: list[dict[str, Any]],
    expected_grid: dict[str, Any],
) -> None:
    method_names = [str(name) for name in expected_grid.get("method_names", [])]
    budget_points = [int(value) for value in expected_grid.get("budget_points", [])]
    expected_cells = {
        (method_name, budget)
        for method_name in method_names
        for budget in budget_points
    }
    actual_counts: dict[tuple[str, int], int] = {}
    for row in rows:
        key = (str(row["method_name"]), int(row["budget"]))
        actual_counts[key] = actual_counts.get(key, 0) + 1

    actual_cells = set(actual_counts)
    missing_cells = sorted(expected_cells - actual_cells)
    extra_cells = sorted(actual_cells - expected_cells)
    duplicate_cells = sorted(
        cell for cell, count in actual_counts.items() if count > 1
    )
    if missing_cells or extra_cells or duplicate_cells:
        raise ValueError(
            "summary_rows must cover the complete method-budget grid "
            f"(missing={missing_cells}, extra={extra_cells}, duplicates={duplicate_cells})."
        )


def _validate_summary_row_metrics(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        context = f"summary row '{row['method_name']}@{int(row['budget'])}'"
        for field_name in SUMMARY_ROW_REQUIRED_FIELDS:
            if field_name not in row or row[field_name] is None:
                raise ValueError(
                    f"Confirm report missing required field '{field_name}' in {context}."
                )


def _budget_value(rows: list[dict[str, Any]], budget: int, metric: str) -> float | None:
    for row in rows:
        if int(row["budget"]) == budget:
            return _as_float(row.get(metric))
    return None


def _method_summary(method_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    best_row = min(rows, key=lambda row: _as_float(row.get("mean_final_distance_mm")))
    first_distance = _budget_value(rows, 50_000, "mean_final_distance_mm")
    final_distance = _budget_value(rows, 200_000, "mean_final_distance_mm")
    if first_distance is None or final_distance is None:
        distance_improvement = None
    else:
        distance_improvement = first_distance - final_distance

    contact_steps = [_as_float(row.get("mean_contact_steps")) for row in rows]
    success_rates = [_as_float(row.get("success_rate")) for row in rows]
    jam_rates = [_as_float(row.get("jam_rate")) for row in rows]
    peak_forces = [_as_float(row.get("mean_peak_contact_force_n")) for row in rows]
    entered_contact = any(value > 0.0 for value in contact_steps)

    return {
        "method_name": method_name,
        "label": str(rows[0].get("label", method_name)),
        "algorithm": str(rows[0].get("algorithm", "")),
        "best_budget": int(best_row["budget"]),
        "best_final_distance_mm": _as_float(best_row.get("mean_final_distance_mm")),
        "distance_improvement_50k_to_200k_mm": distance_improvement,
        "entered_contact": entered_contact,
        "mean_success_across_budgets": mean(success_rates),
        "mean_contact_steps_across_budgets": mean(contact_steps),
        "mean_jam_rate_across_budgets": mean(jam_rates),
        "mean_peak_force_across_budgets": mean(peak_forces),
        "max_success_across_budgets": max(success_rates),
        "final_distance_by_budget_mm": {
            str(int(row["budget"])): _as_float(row.get("mean_final_distance_mm"))
            for row in rows
        },
        "contact_steps_by_budget": {
            str(int(row["budget"])): _as_float(row.get("mean_contact_steps"))
            for row in rows
        },
        "is_best_distance_proxy": False,
    }


def _select_branch(method_summaries: list[dict[str, Any]]) -> tuple[str, str]:
    all_zero_success = all(
        _as_float(summary["mean_success_across_budgets"]) == 0.0
        for summary in method_summaries
    )
    all_zero_contact = all(
        _as_float(summary["mean_contact_steps_across_budgets"]) == 0.0
        for summary in method_summaries
    )
    any_contact = any(bool(summary["entered_contact"]) for summary in method_summaries)
    max_success = max(
        _as_float(summary["max_success_across_budgets"])
        for summary in method_summaries
    )

    if all_zero_success and all_zero_contact:
        return (
            "branch_a",
            "All pure-RL families have zero success and zero useful-contact steps under the frozen grid.",
        )
    if any_contact and max_success < 0.5:
        return (
            "branch_b",
            "At least one off-policy family reaches contact, but success remains low.",
        )
    return (
        "branch_c_candidate",
        "At least one pure-RL family has non-trivial success and should be compared against demo-supported anchors.",
    )


def _mark_best_distance_proxy(method_summaries: list[dict[str, Any]]) -> str:
    best_summary = min(
        method_summaries,
        key=lambda summary: _as_float(summary["best_final_distance_mm"]),
    )
    best_method = str(best_summary["method_name"])
    for summary in method_summaries:
        summary["is_best_distance_proxy"] = summary["method_name"] == best_method
    return best_method


def build_confirm_report(pilot_report: Path) -> dict[str, Any]:
    pilot_report = Path(pilot_report)
    source = _load_json(pilot_report)
    expected_grid = _validate_complete_grid(source)
    summary_rows = [dict(row) for row in source.get("summary_rows", [])]
    _validate_summary_row_grid(summary_rows, expected_grid)
    _validate_summary_row_metrics(summary_rows)
    grouped_rows = _rows_by_method(summary_rows)

    method_names = [str(name) for name in expected_grid.get("method_names", [])]
    method_summaries = [
        _method_summary(method_name, grouped_rows[method_name])
        for method_name in method_names
    ]
    best_distance_proxy_method = _mark_best_distance_proxy(method_summaries)
    selected_branch, branch_rationale = _select_branch(method_summaries)

    return {
        "report_name": "three_dof_cross_family_confirm_report",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_report": str(pilot_report).replace("\\", "/"),
        "grid_complete": True,
        "expected_grid": {
            "method_names": method_names,
            "budget_points": [int(value) for value in expected_grid.get("budget_points", [])],
            "expected_chunk_count": int(expected_grid["expected_chunk_count"]),
            "completed_chunk_count": int(expected_grid["completed_chunk_count"]),
            "missing_chunk_count": int(expected_grid["missing_chunk_count"]),
        },
        "selected_branch": selected_branch,
        "branch_rationale": branch_rationale,
        "best_distance_proxy_method": best_distance_proxy_method,
        "method_summaries": method_summaries,
        "paper_claim_boundary": {
            "allowed": [
                "pure RL remains outside useful contact",
                (
                    f"{best_distance_proxy_method} is the strongest distance proxy "
                    "but still zero-contact"
                ),
            ],
            "not_allowed": [
                (
                    f"{best_distance_proxy_method} solves insertion "
                    "or enters useful contact"
                ),
                "off-policy reaches useful contact",
                "pure RL can never solve insertion",
            ],
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _format_float(value: object) -> str:
    return f"{_as_float(value):.2f}"


def export_confirm_report_json(
    *,
    pilot_report: Path,
    output_dir: Path,
    stem: str = "three_dof_cross_family_confirm_report",
) -> tuple[Path, dict[str, Any]]:
    confirm = build_confirm_report(pilot_report)
    json_path = Path(output_dir) / f"{stem}.json"
    return _write_json(json_path, confirm), confirm


def export_distance_proxy_csv(
    confirm: dict[str, Any],
    output_dir: Path,
    filename: str = "three_dof_cross_family_confirm_distance_proxy.csv",
) -> Path:
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "method_name",
                "label",
                "budget",
                "mean_final_distance_mm",
                "entered_contact",
                "is_best_distance_proxy",
            ]
        )
        for summary in confirm["method_summaries"]:
            best_budget = int(summary["best_budget"])
            for budget_text, distance_mm in summary["final_distance_by_budget_mm"].items():
                budget = int(budget_text)
                is_best_proxy_cell = (
                    bool(summary["is_best_distance_proxy"]) and budget == best_budget
                )
                entered_contact_cell = _as_float(
                    summary["contact_steps_by_budget"][budget_text]
                ) > 0.0
                writer.writerow(
                    [
                        summary["method_name"],
                        summary["label"],
                        budget,
                        _format_float(distance_mm),
                        str(entered_contact_cell).lower(),
                        str(is_best_proxy_cell).lower(),
                    ]
                )
    return output_path


def export_contact_gate_table(
    confirm: dict[str, Any],
    output_dir: Path,
    filename: str = "three_dof_cross_family_confirm_contact_gate_table.md",
) -> Path:
    output_path = Path(output_dir) / filename
    contact_rows: list[tuple[dict[str, Any], str, object, bool]] = []
    for summary in confirm["method_summaries"]:
        for budget_text, distance_mm in summary["final_distance_by_budget_mm"].items():
            entered_contact_cell = _as_float(
                summary["contact_steps_by_budget"][budget_text]
            ) > 0.0
            contact_rows.append(
                (summary, budget_text, distance_mm, entered_contact_cell)
            )
    zero_contact_count = sum(
        1 for _, _, _, entered_contact in contact_rows if not entered_contact
    )
    rows: list[str] = [
        "# 3DoF Cross-Family Confirm Contact Gate",
        "",
        f"{zero_contact_count}/{len(contact_rows)} zero-contact method-budget cells.",
        "",
        "| method | budget | final_distance_mm | contact? |",
        "| --- | ---: | ---: | --- |",
    ]
    for summary, budget_text, distance_mm, entered_contact_cell in contact_rows:
        contact_text = "yes" if entered_contact_cell else "no"
        rows.append(
            "| "
            f"{summary['label']} | "
            f"{int(budget_text)} | "
            f"{_format_float(distance_mm)} | "
            f"{contact_text} |"
        )
    rows.extend(
        [
            "",
            "Interpretation: distance-to-contact is a secondary diagnostic proxy, not a success metric.",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return output_path


def export_distance_vs_budget_figure(
    confirm: dict[str, Any],
    output_dir: Path,
    stem: str = "three_dof_cross_family_confirm_distance_vs_budget",
) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(6.0, 4.0), constrained_layout=True)
    for summary in confirm["method_summaries"]:
        points = sorted(
            (
                (int(budget_text), _as_float(distance_mm))
                for budget_text, distance_mm in summary["final_distance_by_budget_mm"].items()
            ),
            key=lambda item: item[0],
        )
        budgets = [budget for budget, _ in points]
        distances = [distance for _, distance in points]
        ax.plot(
            budgets,
            distances,
            marker="o",
            linewidth=2.0,
            label=str(summary["label"]),
        )

    ax.set_title("3DoF cross-family confirm: distance proxy")
    ax.set_xlabel("Training budget (timesteps)")
    ax.set_ylabel("Mean final distance to contact (mm)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / f"{stem}.png"
    pdf_path = output_dir / f"{stem}.pdf"
    fig.savefig(png_path, dpi=200)
    fig.savefig(pdf_path)
    plt.close(fig)
    return png_path, pdf_path


def export_confirm_report_artifacts(
    *,
    pilot_report: Path,
    output_dir: Path,
) -> dict[str, Path | tuple[Path, Path]]:
    json_path, confirm = export_confirm_report_json(
        pilot_report=pilot_report,
        output_dir=output_dir,
    )
    csv_path = export_distance_proxy_csv(confirm, output_dir)
    markdown_path = export_contact_gate_table(confirm, output_dir)
    figure_paths = export_distance_vs_budget_figure(confirm, output_dir)
    return {
        "json": json_path,
        "csv": csv_path,
        "markdown": markdown_path,
        "distance_vs_budget": figure_paths,
    }
