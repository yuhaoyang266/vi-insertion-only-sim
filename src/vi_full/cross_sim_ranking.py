from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable


RANKING_METRICS = (
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
CROSS_SIM_RECORD_SCHEMA_VERSION = 1
CROSS_SIM_RECORD_STATUS_VALUES = ("completed", "failed", "not_available", "skipped")
CROSS_SIM_RECORD_REQUIRED_KEYS = (
    "schema_version",
    "suite_name",
    "profile",
    "seed",
    "episode_count",
    "status",
    "episode_status",
    "reason",
    "paper_a_policy_artifact",
    "paper_b_env_config",
    "out_of_paper_a_scope",
    "mean_dropped_torque_norm_nm",
)
NON_COMPLETED_STATUS_PRIORITY = ("failed", "not_available", "skipped")


def _mean(values: Iterable[float]) -> float | None:
    numeric = [float(value) for value in values if value is not None]
    if not numeric:
        return None
    return float(sum(numeric) / len(numeric))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _validate_metric_value(record: dict[str, Any], metric_name: str) -> None:
    metric_value = record.get(metric_name)
    if metric_value is None:
        return
    try:
        float(metric_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{metric_name} must be numeric or null.") from exc


def validate_cross_sim_record_schema(record: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(record)
    missing_keys = [key for key in CROSS_SIM_RECORD_REQUIRED_KEYS if key not in normalized]
    if missing_keys:
        raise ValueError(f"cross-sim record is missing required keys: {missing_keys}")
    if int(normalized["schema_version"]) != CROSS_SIM_RECORD_SCHEMA_VERSION:
        raise ValueError(
            f"schema_version must be {CROSS_SIM_RECORD_SCHEMA_VERSION} for cross-sim records."
        )
    status = str(normalized["status"])
    episode_status = str(normalized["episode_status"])
    if status not in CROSS_SIM_RECORD_STATUS_VALUES:
        raise ValueError(f"Unknown cross-sim record status: {status}")
    if episode_status not in CROSS_SIM_RECORD_STATUS_VALUES:
        raise ValueError(f"Unknown cross-sim episode_status: {episode_status}")
    if status != episode_status:
        raise ValueError("status and episode_status must match until per-episode records land.")
    if not str(normalized["suite_name"]):
        raise ValueError("suite_name must not be empty.")
    if not str(normalized["profile"]):
        raise ValueError("profile must not be empty.")
    if isinstance(normalized["seed"], bool):
        raise ValueError("seed must be an integer.")
    normalized["seed"] = int(normalized["seed"])
    normalized["episode_count"] = int(normalized["episode_count"])
    if normalized["episode_count"] <= 0:
        raise ValueError("episode_count must be positive.")
    if normalized["out_of_paper_a_scope"] is not None and not isinstance(
        normalized["out_of_paper_a_scope"],
        bool,
    ):
        raise ValueError("out_of_paper_a_scope must be boolean or null.")
    _validate_metric_value(normalized, "mean_dropped_torque_norm_nm")
    if not str(normalized["paper_a_policy_artifact"]):
        raise ValueError("paper_a_policy_artifact must not be empty.")
    if not str(normalized["paper_b_env_config"]):
        raise ValueError("paper_b_env_config must not be empty.")
    for metric_name in RANKING_METRICS:
        _validate_metric_value(normalized, metric_name)
    if status == "not_available":
        populated_metrics = [
            metric_name
            for metric_name in RANKING_METRICS
            if normalized.get(metric_name) is not None
        ]
        if populated_metrics:
            raise ValueError(
                "not_available cross-sim records must keep metrics null: "
                f"{populated_metrics}"
            )
    if status == "completed":
        missing_metrics = [
            metric_name
            for metric_name in RANKING_METRICS
            if normalized.get(metric_name) is None
        ]
        if missing_metrics:
            raise ValueError(
                "completed cross-sim records must include real episode metrics: "
                f"{missing_metrics}"
            )
    return normalized


def _row_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    completed = row["status"] == "completed"
    success_rate = row.get("success_rate")
    peak_force = row.get("mean_peak_contact_force")
    final_distance = row.get("mean_final_distance")
    return (
        0 if completed else 1,
        -float(success_rate) if success_rate is not None else 0.0,
        float(peak_force) if peak_force is not None else float("inf"),
        float(final_distance) if final_distance is not None else float("inf"),
        str(row["suite_name"]),
    )


def _suite_status(records: list[dict[str, Any]], completed_records: list[dict[str, Any]]) -> str:
    statuses = {str(record.get("status", "unknown")) for record in records}
    if statuses == {"completed"}:
        return "completed"
    for status in NON_COMPLETED_STATUS_PRIORITY:
        if status in statuses:
            return status
    if completed_records:
        return "failed"
    return sorted(statuses)[0] if statuses else "unknown"


def _summarize_suite(suite_name: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    completed_records = [record for record in records if record.get("status") == "completed"]
    status = _suite_status(records, completed_records)
    row: dict[str, Any] = {
        "suite_name": suite_name,
        "status": status,
        "profile_count": len({str(record.get("profile", "")) for record in records}),
        "seed_count": len({int(record.get("seed", 0)) for record in records}),
        "record_count": len(records),
        "completed_record_count": len(completed_records),
        "episode_count": int(sum(int(record.get("episode_count", 0)) for record in records)),
        "reason": "",
    }
    source_records = completed_records if completed_records else records
    for metric_name in RANKING_METRICS:
        row[metric_name] = _mean(record.get(metric_name) for record in source_records)
    reasons = [
        str(record.get("reason", ""))
        for record in records
        if record.get("status") != "completed" and record.get("reason")
    ]
    row["reason"] = "; ".join(sorted(set(reasons)))
    return row


def build_cross_sim_ranking(
    records: list[dict[str, Any]],
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    normalized_records: list[dict[str, Any]] = []
    for record in records:
        normalized_record = validate_cross_sim_record_schema(record)
        normalized_records.append(normalized_record)
        suite_name = str(normalized_record["suite_name"])
        grouped.setdefault(suite_name, []).append(normalized_record)
    rows = [_summarize_suite(suite_name, suite_records) for suite_name, suite_records in grouped.items()]
    rows.sort(key=_row_sort_key)
    return {
        "artifact_type": "cross_sim_ranking",
        "schema_version": 1,
        "metadata": _json_safe(metadata or {}),
        "rows": _json_safe(rows),
        "records": _json_safe(normalized_records),
    }


def render_cross_sim_ranking_csv(ranking: dict[str, Any]) -> str:
    fieldnames = [
        "suite_name",
        "status",
        "success_rate",
        "jam_rate",
        "mean_peak_contact_force",
        "mean_final_distance",
        "mean_contact_steps",
        "mean_contact_work",
        "episode_count",
        "completed_record_count",
        "reason",
    ]
    rows = ranking.get("rows", [])
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fieldnames})
    return buffer.getvalue()


def render_cross_sim_ranking_markdown(ranking: dict[str, Any]) -> str:
    lines = [
        "# Cross-Sim Ranking",
        "",
        "| Suite | Status | Success | Jam | Peak force | Final distance | Contact steps | Reason |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in ranking.get("rows", []):
        lines.append(
            "| {suite_name} | {status} | {success_rate} | {jam_rate} | "
            "{mean_peak_contact_force} | {mean_final_distance} | {mean_contact_steps} | {reason} |".format(
                suite_name=row.get("suite_name", ""),
                status=row.get("status", ""),
                success_rate="" if row.get("success_rate") is None else row["success_rate"],
                jam_rate="" if row.get("jam_rate") is None else row["jam_rate"],
                mean_peak_contact_force=(
                    "" if row.get("mean_peak_contact_force") is None else row["mean_peak_contact_force"]
                ),
                mean_final_distance=(
                    "" if row.get("mean_final_distance") is None else row["mean_final_distance"]
                ),
                mean_contact_steps=(
                    "" if row.get("mean_contact_steps") is None else row["mean_contact_steps"]
                ),
                reason=row.get("reason", ""),
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_cross_sim_ranking_artifacts(
    output_path: Path,
    ranking: dict[str, Any],
) -> dict[str, Path]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_path
    csv_path = output_path.with_suffix(".csv")
    markdown_path = output_path.with_suffix(".md")
    json_path.write_text(json.dumps(_json_safe(ranking), indent=2), encoding="utf-8")
    csv_path.write_text(render_cross_sim_ranking_csv(ranking), encoding="utf-8")
    markdown_path.write_text(render_cross_sim_ranking_markdown(ranking), encoding="utf-8")
    return {
        "json": json_path,
        "csv": csv_path,
        "markdown": markdown_path,
    }
