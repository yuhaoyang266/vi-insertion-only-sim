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


def _summarize_suite(suite_name: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    completed_records = [record for record in records if record.get("status") == "completed"]
    status = "completed" if completed_records else str(records[0].get("status", "unknown"))
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
    if not completed_records:
        reasons = [str(record.get("reason", "")) for record in records if record.get("reason")]
        row["reason"] = "; ".join(sorted(set(reasons)))
    return row


def build_cross_sim_ranking(
    records: list[dict[str, Any]],
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        suite_name = str(record["suite_name"])
        grouped.setdefault(suite_name, []).append(dict(record))
    rows = [_summarize_suite(suite_name, suite_records) for suite_name, suite_records in grouped.items()]
    rows.sort(key=_row_sort_key)
    return {
        "artifact_type": "cross_sim_ranking",
        "schema_version": 1,
        "metadata": _json_safe(metadata or {}),
        "rows": _json_safe(rows),
        "records": _json_safe(records),
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
