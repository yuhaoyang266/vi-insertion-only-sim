from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from vi_full.three_dof_support_metrics import (
    ThreeDoFSupportMetricConfig,
    compute_3dof_support_coverage_index,
    project_3dof_support_signature,
    quantize_3dof_support_signature,
)


AUDIT_FIELDS = (
    "metric_name",
    "condition_name",
    "value",
    "success_rate",
    "contact_entry_rate",
    "jam_rate",
    "peak_force",
    "contact_work",
    "final_distance",
    "contact_steps",
)


def build_sci_sensitivity_configs() -> list[ThreeDoFSupportMetricConfig]:
    return [
        ThreeDoFSupportMetricConfig(2.5e-4, 5e-4, 0.125, 0.05, 0.05, 0.05, 0.05),
        ThreeDoFSupportMetricConfig(5e-4, 5e-4, 0.25, 0.1, 0.1, 0.1, 0.1),
        ThreeDoFSupportMetricConfig(1e-3, 1e-3, 0.5, 0.2, 0.2, 0.2, 0.2),
    ]


def _validate_2d(name: str, value: np.ndarray, min_cols: int) -> np.ndarray:
    array = np.asarray(value, dtype=np.float32)
    if array.ndim != 2:
        raise ValueError(f"{name} must be a 2D array")
    if array.shape[1] < min_cols:
        raise ValueError(f"{name} must expose at least {min_cols} columns")
    return array


def _mean_nearest_distance(reference: np.ndarray, query: np.ndarray) -> float:
    reference_array = np.asarray(reference, dtype=np.float32)
    query_array = np.asarray(query, dtype=np.float32)
    if reference_array.size == 0 or query_array.size == 0:
        return float("inf")
    distances: list[np.ndarray] = []
    batch_size = 512
    for start in range(0, query_array.shape[0], batch_size):
        batch = query_array[start : start + batch_size]
        diff = batch[:, None, :] - reference_array[None, :, :]
        distances.append(np.min(np.linalg.norm(diff, axis=2), axis=1))
    return float(np.mean(np.concatenate(distances)))


def compute_nearest_demo_distance(
    *,
    demo_observations: np.ndarray,
    demo_actions: np.ndarray,
    rollout_observations: np.ndarray,
    rollout_actions: np.ndarray,
) -> float:
    demo_signature = project_3dof_support_signature(demo_observations, demo_actions)
    rollout_signature = project_3dof_support_signature(
        rollout_observations,
        rollout_actions,
    )
    scale = np.maximum(np.std(demo_signature, axis=0), 1e-6)
    return _mean_nearest_distance(demo_signature / scale, rollout_signature / scale)


def _cell_set(signature: np.ndarray, config: ThreeDoFSupportMetricConfig) -> set[tuple[int, ...]]:
    return {
        tuple(row)
        for row in quantize_3dof_support_signature(signature, config=config).tolist()
    }


def compute_support_jaccard(
    *,
    demo_observations: np.ndarray,
    demo_actions: np.ndarray,
    rollout_observations: np.ndarray,
    rollout_actions: np.ndarray,
    config: ThreeDoFSupportMetricConfig = ThreeDoFSupportMetricConfig(),
) -> float:
    demo_cells = _cell_set(project_3dof_support_signature(demo_observations, demo_actions), config)
    rollout_cells = _cell_set(
        project_3dof_support_signature(rollout_observations, rollout_actions),
        config,
    )
    union = demo_cells | rollout_cells
    if not union:
        return 0.0
    return float(len(demo_cells & rollout_cells) / len(union))


def compute_state_only_sci(
    *,
    demo_observations: np.ndarray,
    rollout_observations: np.ndarray,
    config: ThreeDoFSupportMetricConfig = ThreeDoFSupportMetricConfig(),
) -> float:
    demo = _validate_2d("demo_observations", demo_observations, 9)
    rollout = _validate_2d("rollout_observations", rollout_observations, 9)
    dummy_demo_actions = np.zeros((demo.shape[0], 5), dtype=np.float32)
    dummy_rollout_actions = np.zeros((rollout.shape[0], 5), dtype=np.float32)
    demo_signature = project_3dof_support_signature(demo, dummy_demo_actions)[:, :3]
    rollout_signature = project_3dof_support_signature(rollout, dummy_rollout_actions)[:, :3]
    widths = np.asarray(
        [config.obs_xy_norm_bin_m, config.obs_z_bin_m, config.force_norm_bin_n],
        dtype=np.float32,
    )
    demo_cells = {tuple(row) for row in np.rint(demo_signature / widths).astype(np.int32).tolist()}
    rollout_cells = [tuple(row) for row in np.rint(rollout_signature / widths).astype(np.int32).tolist()]
    if not rollout_cells:
        return 0.0
    return float(sum(cell in demo_cells for cell in rollout_cells) / len(rollout_cells))


def compute_action_only_sci(
    *,
    demo_actions: np.ndarray,
    rollout_actions: np.ndarray,
    config: ThreeDoFSupportMetricConfig = ThreeDoFSupportMetricConfig(),
) -> float:
    demo = _validate_2d("demo_actions", demo_actions, 5)
    rollout = _validate_2d("rollout_actions", rollout_actions, 5)
    demo_signature = np.column_stack(
        [np.linalg.norm(demo[:, :2], axis=1), demo[:, 2], demo[:, 3], demo[:, 4]]
    )
    rollout_signature = np.column_stack(
        [
            np.linalg.norm(rollout[:, :2], axis=1),
            rollout[:, 2],
            rollout[:, 3],
            rollout[:, 4],
        ]
    )
    widths = np.asarray(
        [
            config.action_xy_norm_bin,
            config.action_dz_bin,
            config.action_k_xy_bin,
            config.action_k_z_bin,
        ],
        dtype=np.float32,
    )
    demo_cells = {tuple(row) for row in np.rint(demo_signature / widths).astype(np.int32).tolist()}
    rollout_cells = [tuple(row) for row in np.rint(rollout_signature / widths).astype(np.int32).tolist()]
    if not rollout_cells:
        return 0.0
    return float(sum(cell in demo_cells for cell in rollout_cells) / len(rollout_cells))


def _as_float(row: dict[str, Any], *names: str, default: float = 0.0) -> float:
    for name in names:
        if name in row and row[name] is not None:
            return float(row[name])
    return float(default)


def _condition_name(row: dict[str, Any]) -> str:
    return str(row.get("condition_name") or row.get("method_name") or row.get("suite_name"))


def _source_rows(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(artifact.get("rows"), list):
        return list(artifact["rows"])
    if isinstance(artifact.get("summary"), dict) and isinstance(
        artifact["summary"].get("conditions"),
        list,
    ):
        return list(artifact["summary"]["conditions"])
    learned = artifact.get("learned_results")
    if isinstance(learned, dict):
        return [
            {"condition_name": name, **dict(payload.get("five_profile_mean", {}))}
            for name, payload in learned.items()
            if isinstance(payload, dict)
        ]
    return []


def audit_support_metric_rows(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    audit_rows: list[dict[str, Any]] = []
    for row in _source_rows(artifact):
        condition_name = _condition_name(row)
        success_rate = _as_float(row, "success_rate", "success_rate_mean_over_profiles")
        contact_steps = _as_float(row, "mean_contact_steps", "mean_contact_steps_mean_over_profiles")
        contact_entry_rate = 1.0 if bool(row.get("entered_contact", contact_steps > 0.0)) else 0.0
        jam_rate = _as_float(row, "jam_rate", "jam_rate_mean_over_profiles")
        peak_force = _as_float(
            row,
            "mean_peak_contact_force_n",
            "mean_peak_contact_force_mean_over_profiles",
        )
        final_distance = _as_float(
            row,
            "mean_final_distance_mm",
            default=1000.0
            * _as_float(row, "mean_final_distance_mean_over_profiles"),
        )
        contact_work = _as_float(
            row,
            "contact_work",
            "mean_contact_work",
            default=peak_force * contact_steps,
        )
        metric_values = {
            "success_rate": success_rate,
            "contact_entry_rate": contact_entry_rate,
            "jam_rate": jam_rate,
            "peak_force": peak_force,
            "contact_work": contact_work,
            "final_distance": final_distance,
            "contact_steps": contact_steps,
        }
        for metric_name, value in metric_values.items():
            audit_rows.append(
                {
                    "metric_name": metric_name,
                    "condition_name": condition_name,
                    "value": float(value),
                    "success_rate": success_rate,
                    "contact_entry_rate": contact_entry_rate,
                    "jam_rate": jam_rate,
                    "peak_force": peak_force,
                    "contact_work": contact_work,
                    "final_distance": final_distance,
                    "contact_steps": contact_steps,
                }
            )
    return audit_rows


def compute_synthetic_bin_sensitivity() -> list[dict[str, Any]]:
    demo_observations = np.zeros((4, 9), dtype=np.float32)
    rollout_observations = np.zeros((4, 9), dtype=np.float32)
    demo_actions = np.zeros((4, 5), dtype=np.float32)
    rollout_actions = np.zeros((4, 5), dtype=np.float32)
    demo_observations[:, 0] = np.array([0.0, 0.0002, 0.0004, 0.0006], dtype=np.float32)
    rollout_observations[:, 0] = demo_observations[:, 0]
    demo_actions[:, 3:] = 0.5
    rollout_actions[:, 3:] = 0.5
    rows: list[dict[str, Any]] = []
    for label, config in zip(("fine", "default", "coarse"), build_sci_sensitivity_configs()):
        metrics = compute_3dof_support_coverage_index(
            demo_observations=demo_observations,
            demo_actions=demo_actions,
            rollout_observations=rollout_observations,
            rollout_actions=rollout_actions,
            config=config,
        )
        rows.append(
            {
                "bin_config": label,
                "support_coverage_index": float(metrics["support_coverage_index"]),
                "support_cell_coverage": float(metrics["support_cell_coverage"]),
                "obs_xy_norm_bin_m": config.obs_xy_norm_bin_m,
                "force_norm_bin_n": config.force_norm_bin_n,
                "action_xy_norm_bin": config.action_xy_norm_bin,
                "action_k_xy_bin": config.action_k_xy_bin,
            }
        )
    return rows


def build_support_metric_sensitivity_report(
    artifacts: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    audit_rows: list[dict[str, Any]] = []
    for artifact in artifacts:
        audit_rows.extend(audit_support_metric_rows(artifact))
    return {
        "schema_version": 1,
        "sci_bin_sensitivity": compute_synthetic_bin_sensitivity(),
        "predictive_audit_rows": audit_rows,
        "gate_c_interpretation": _interpret_gate_c(audit_rows),
    }


def _interpret_gate_c(audit_rows: list[dict[str, Any]]) -> str:
    if not audit_rows:
        return "No predictive rows available; demote SCI to appendix diagnostic until raw support traces are audited."
    return "Predictive audit schema is populated; use association trends conservatively and keep SCI diagnostic wording bounded."


def write_support_metric_sensitivity_outputs(
    report: dict[str, Any],
    output_stem: Path,
) -> dict[str, Path]:
    json_path = output_stem.with_suffix(".json")
    csv_path = output_stem.with_suffix(".csv")
    md_path = output_stem.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(AUDIT_FIELDS))
        writer.writeheader()
        writer.writerows(report["predictive_audit_rows"])
    lines = [
        "# SCI Sensitivity Audit 2026-04-25",
        "",
        "## Gate C Interpretation",
        "",
        f"- {report['gate_c_interpretation']}",
        "",
        "## Bin Sensitivity",
        "",
        "| bin_config | SCI | support_cell_coverage |",
        "| --- | ---: | ---: |",
    ]
    for row in report["sci_bin_sensitivity"]:
        lines.append(
            f"| {row['bin_config']} | {row['support_coverage_index']:.3f} | {row['support_cell_coverage']:.3f} |"
        )
    lines.extend(["", "## Predictive Audit Rows", "", f"- row_count: {len(report['predictive_audit_rows'])}"])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json_path": json_path, "csv_path": csv_path, "markdown_path": md_path}
