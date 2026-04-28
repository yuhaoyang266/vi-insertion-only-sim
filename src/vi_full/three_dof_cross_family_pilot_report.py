from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from vi_full.three_dof_cross_family_baselines import build_3dof_cross_family_pilot_registry


def _safe_float(value: object, *, scale: float = 1.0) -> float | None:
    if value is None:
        return None
    return float(value) * scale


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _portable_path(path: Path) -> str:
    path = Path(path)
    if path.is_absolute():
        try:
            path = path.relative_to(Path.cwd())
        except ValueError:
            pass
    return path.as_posix()


def _method_specs() -> dict[str, dict[str, Any]]:
    registry = build_3dof_cross_family_pilot_registry()
    return {
        str(spec["method_name"]): dict(spec)
        for spec in registry["methods"]
    }


def _load_chunk(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    registry = build_3dof_cross_family_pilot_registry()
    if payload.get("experiment_name") != registry["experiment_name"]:
        raise ValueError(f"Unexpected experiment_name in {path}")

    rows: list[dict[str, Any]] = []
    for method_payload in payload.get("methods", []):
        method_name = str(method_payload["method_name"])
        label = str(method_payload["label"])
        algorithm = str(method_payload["algorithm"])
        for point in method_payload.get("points", []):
            budget = int(point["factor_value"])
            nominal_aggregate = (
                point.get("per_profile_metrics", {})
                .get("nominal", {})
                .get("aggregate", {})
            )
            five_profile_mean = point.get("five_profile_mean", {})
            rows.append(
                {
                    "method_name": method_name,
                    "label": label,
                    "algorithm": algorithm,
                    "budget": budget,
                    "source_chunk_path": _portable_path(path),
                    "five_profile_mean": {
                        "success_rate": _safe_float(
                            five_profile_mean.get("success_rate_mean_over_profiles")
                        ),
                        "mean_first_contact_step": _safe_float(
                            five_profile_mean.get("mean_first_contact_step_mean_over_profiles")
                        ),
                        "mean_final_distance_mm": _safe_float(
                            five_profile_mean.get("mean_final_distance_mean_over_profiles"),
                            scale=1000.0,
                        ),
                        "mean_contact_steps": _safe_float(
                            five_profile_mean.get("mean_contact_steps_mean_over_profiles")
                        ),
                        "mean_peak_contact_force_n": _safe_float(
                            five_profile_mean.get("mean_peak_contact_force_mean_over_profiles")
                        ),
                        "jam_rate": _safe_float(
                            five_profile_mean.get("jam_rate_mean_over_profiles")
                        ),
                    },
                    "nominal": {
                        "success_rate": _safe_float(
                            nominal_aggregate.get("success_rate_mean")
                        ),
                        "mean_first_contact_step": _safe_float(
                            nominal_aggregate.get("mean_first_contact_step_mean")
                        ),
                        "mean_final_distance_mm": _safe_float(
                            nominal_aggregate.get("mean_final_distance_mean"),
                            scale=1000.0,
                        ),
                        "mean_contact_steps": _safe_float(
                            nominal_aggregate.get("mean_contact_steps_mean")
                        ),
                        "mean_peak_contact_force_n": _safe_float(
                            nominal_aggregate.get("mean_peak_contact_force_mean")
                        ),
                        "jam_rate": _safe_float(
                            nominal_aggregate.get("jam_rate_mean")
                        ),
                    },
                }
            )
    return rows


def _sorted_chunk_paths(chunk_dir: Path) -> list[Path]:
    chunk_paths = sorted(chunk_dir.glob("*.json"))
    if not chunk_paths:
        raise ValueError(f"No pilot chunk JSON files found in {chunk_dir}")
    return chunk_paths


def build_3dof_cross_family_pilot_report(
    chunk_dir: Path,
) -> dict[str, object]:
    chunk_dir = Path(chunk_dir)
    registry = build_3dof_cross_family_pilot_registry()
    method_specs = _method_specs()
    method_names = [str(spec["method_name"]) for spec in registry["methods"]]
    budget_points = [int(budget) for budget in registry["budget_points"]]
    method_index = {name: index for index, name in enumerate(method_names)}

    point_by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for chunk_path in _sorted_chunk_paths(chunk_dir):
        for row in _load_chunk(chunk_path):
            key = (str(row["method_name"]), int(row["budget"]))
            if key in point_by_key:
                raise ValueError(f"Duplicate pilot chunk for {key} in {chunk_dir}")
            point_by_key[key] = row

    completed_keys = sorted(
        point_by_key,
        key=lambda key: (method_index.get(key[0], len(method_names)), key[1]),
    )
    missing_keys = [
        (method_name, budget)
        for method_name in method_names
        for budget in budget_points
        if (method_name, budget) not in point_by_key
    ]

    methods: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for method_name in method_names:
        method_points = [
            point_by_key[(method_name, budget)]
            for budget in budget_points
            if (method_name, budget) in point_by_key
        ]
        spec = method_specs[method_name]
        methods.append(
            {
                "method_name": method_name,
                "label": str(spec["label"]),
                "algorithm": str(spec["algorithm"]),
                "points": [
                    {
                        "budget": int(point["budget"]),
                        "source_chunk_path": str(point["source_chunk_path"]),
                        "five_profile_mean": dict(point["five_profile_mean"]),
                        "nominal": dict(point["nominal"]),
                    }
                    for point in method_points
                ],
            }
        )
        for point in method_points:
            summary_rows.append(
                {
                    "method_name": method_name,
                    "label": str(spec["label"]),
                    "algorithm": str(spec["algorithm"]),
                    "budget": int(point["budget"]),
                    "success_rate": point["five_profile_mean"]["success_rate"],
                    "mean_first_contact_step": point["five_profile_mean"][
                        "mean_first_contact_step"
                    ],
                    "mean_final_distance_mm": point["five_profile_mean"][
                        "mean_final_distance_mm"
                    ],
                    "mean_contact_steps": point["five_profile_mean"][
                        "mean_contact_steps"
                    ],
                    "mean_peak_contact_force_n": point["five_profile_mean"][
                        "mean_peak_contact_force_n"
                    ],
                    "jam_rate": point["five_profile_mean"]["jam_rate"],
                    "source_chunk_path": str(point["source_chunk_path"]),
                }
            )

    return {
        "experiment_name": registry["experiment_name"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "chunk_dir": _portable_path(chunk_dir),
        "expected_grid": {
            "method_names": method_names,
            "budget_points": budget_points,
            "expected_chunk_count": len(method_names) * len(budget_points),
            "completed_chunk_count": len(completed_keys),
            "missing_chunk_count": len(missing_keys),
        },
        "completed_chunks": [
            {"method_name": method_name, "budget": budget}
            for method_name, budget in completed_keys
        ],
        "missing_chunks": [
            {"method_name": method_name, "budget": budget}
            for method_name, budget in missing_keys
        ],
        "methods": methods,
        "summary_rows": summary_rows,
    }


def export_3dof_cross_family_pilot_report(
    *,
    chunk_dir: Path,
    output_dir: Path,
    stem: str = "three_dof_cross_family_pilot_report",
) -> Path:
    report = build_3dof_cross_family_pilot_report(chunk_dir)
    output_path = Path(output_dir) / f"{stem}.json"
    return _write_json(output_path, report)


def _plot_metric(
    report: dict[str, object],
    *,
    metric_key: str,
    ylabel: str,
    title: str,
    output_stem: Path,
) -> tuple[Path, Path]:
    fig, ax = plt.subplots(figsize=(6.0, 4.0), constrained_layout=True)
    for method in report["methods"]:
        points = method["points"]
        if not points:
            continue
        budgets = [int(point["budget"]) for point in points]
        values = [point["five_profile_mean"][metric_key] for point in points]
        ax.plot(
            budgets,
            values,
            marker="o",
            linewidth=2.0,
            label=str(method["label"]),
        )

    ax.set_title(title)
    ax.set_xlabel("Training budget (timesteps)")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.legend()

    pdf_path = output_stem.with_suffix(".pdf")
    png_path = output_stem.with_suffix(".png")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=200)
    plt.close(fig)
    return pdf_path, png_path


def export_3dof_cross_family_pilot_internal_figures(
    *,
    chunk_dir: Path,
    output_dir: Path,
    stem_prefix: str = "three_dof_cross_family_pilot",
) -> dict[str, tuple[Path, Path]]:
    report = build_3dof_cross_family_pilot_report(chunk_dir)
    output_dir = Path(output_dir)
    return {
        "success_vs_budget": _plot_metric(
            report,
            metric_key="success_rate",
            ylabel="Success rate",
            title="3DoF cross-family pilot: success vs budget",
            output_stem=output_dir / f"{stem_prefix}_success_vs_budget",
        ),
        "first_contact_step_vs_budget": _plot_metric(
            report,
            metric_key="mean_first_contact_step",
            ylabel="Mean first-contact step",
            title="3DoF cross-family pilot: first contact vs budget",
            output_stem=output_dir / f"{stem_prefix}_first_contact_step_vs_budget",
        ),
    }
