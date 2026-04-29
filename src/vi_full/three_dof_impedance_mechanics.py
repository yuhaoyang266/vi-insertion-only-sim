from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import is_dataclass, asdict
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from vi_full.artifact_provenance import calculate_sha256, git_commit, git_dirty


MECHANICS_SCHEMA_VERSION = 1
DEFAULT_NUM_POINTS = 120
DEFAULT_CONTACT_THRESHOLD_N = 0.05
METHOD_COLORS = {
    "Learned fixed": "#C0504D",
    "Learned variable": "#4F81BD",
    "Handcrafted fixed": "#DD8452",
    "Handcrafted variable": "#55A868",
    "fixed": "#C0504D",
    "variable": "#4F81BD",
}


def partition_traces_by_outcome(traces: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    partitions = {"success": [], "failure": []}
    for trace in traces:
        target = "success" if _is_success(trace) else "failure"
        partitions[target].append(dict(trace))
    return partitions


def compute_success_matched_force_curve(
    traces_by_method: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    num_points: int = DEFAULT_NUM_POINTS,
) -> dict[str, Any]:
    matched = _matched_success_runs(traces_by_method)
    x = np.linspace(0.0, 1.0, num=num_points, dtype=np.float64)
    curves: dict[str, Any] = {}
    for method, traces in matched["runs"].items():
        force = _stack_trace_channel(traces, "force", num_points)
        curves[method] = {
            "label": method,
            "trace_count_used": len(traces),
            "success_trace_count_total": matched["success_counts"][method],
            "normalized_contact_step": x.tolist(),
            "force_mean": np.mean(force, axis=0).tolist(),
            "force_std": np.std(force, axis=0).tolist(),
        }
    return {
        "curve_basis": "success_matched",
        "matched_success_count": matched["matched_success_count"],
        "curves": curves,
    }


def compute_success_matched_work_curve(
    traces_by_method: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    num_points: int = DEFAULT_NUM_POINTS,
) -> dict[str, Any]:
    matched = _matched_success_runs(traces_by_method)
    x = np.linspace(0.0, 1.0, num=num_points, dtype=np.float64)
    curves: dict[str, Any] = {}
    for method, traces in matched["runs"].items():
        work = _stack_trace_channel(traces, "work", num_points)
        curves[method] = {
            "label": method,
            "trace_count_used": len(traces),
            "success_trace_count_total": matched["success_counts"][method],
            "normalized_contact_step": x.tolist(),
            "work_mean": np.mean(work, axis=0).tolist(),
            "work_std": np.std(work, axis=0).tolist(),
        }
    return {
        "curve_basis": "success_matched",
        "matched_success_count": matched["matched_success_count"],
        "curves": curves,
    }


def compute_force_position_phase_portrait(
    traces_by_method: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    num_points: int = DEFAULT_NUM_POINTS,
    position_scale: float = 1.0,
) -> dict[str, Any]:
    matched = _matched_success_runs(traces_by_method)
    portraits: dict[str, Any] = {}
    for method, traces in matched["runs"].items():
        force = _stack_trace_channel(traces, "force", num_points)
        position = _stack_trace_channel(
            traces,
            "position",
            num_points,
            scale=position_scale,
        )
        portraits[method] = {
            "label": method,
            "trace_count_used": len(traces),
            "success_trace_count_total": matched["success_counts"][method],
            "position_mean": np.mean(position, axis=0).tolist(),
            "position_std": np.std(position, axis=0).tolist(),
            "force_mean": np.mean(force, axis=0).tolist(),
            "force_std": np.std(force, axis=0).tolist(),
        }
    return {
        "curve_basis": "success_matched",
        "matched_success_count": matched["matched_success_count"],
        "portraits": portraits,
    }


def compute_force_work_pareto_rows(
    traces_by_method: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    matched = _matched_success_runs(traces_by_method)
    rows: list[dict[str, Any]] = []
    for method, traces in matched["runs"].items():
        peak_forces = []
        final_work = []
        final_positions = []
        for run in traces:
            steps = _contact_segment(_trace_steps(run))
            force_values = [_step_channel(step, "force") for step in steps]
            work_values = _work_series(steps)
            position_values = [_step_channel(step, "position") for step in steps]
            peak_forces.append(float(np.max(np.asarray(force_values, dtype=np.float64))))
            final_work.append(float(work_values[-1]) if work_values else 0.0)
            final_positions.append(float(position_values[-1]) if position_values else 0.0)
        rows.append(
            {
                "method": method,
                "label": method,
                "trace_count_used": len(traces),
                "success_trace_count_total": matched["success_counts"][method],
                "mean_peak_force": float(np.mean(np.asarray(peak_forces, dtype=np.float64))),
                "std_peak_force": float(np.std(np.asarray(peak_forces, dtype=np.float64))),
                "mean_contact_work": float(np.mean(np.asarray(final_work, dtype=np.float64))),
                "std_contact_work": float(np.std(np.asarray(final_work, dtype=np.float64))),
                "mean_final_position": float(np.mean(np.asarray(final_positions, dtype=np.float64))),
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            float(row["mean_contact_work"]),
            float(row["mean_peak_force"]),
            str(row["method"]),
        ),
    )


def traces_by_method_from_payload(trace_payload: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    traces_by_method: dict[str, list[dict[str, Any]]] = {}
    for suite_name, suite_payload in trace_payload.get("suite_summaries", {}).items():
        method = str(suite_payload.get("display_name", suite_name))
        traces_by_method[method] = []
        for run in suite_payload.get("trace_runs", []):
            run_copy = dict(run)
            run_copy["method"] = method
            run_copy["suite_name"] = suite_name
            traces_by_method[method].append(run_copy)
    if not traces_by_method:
        raise ValueError("Trace payload does not contain suite_summaries trace runs.")
    return traces_by_method


def build_success_matched_mechanics_report(
    trace_payload: Mapping[str, Any],
    *,
    source_trace_path: str,
    generating_command: str,
    repo_root: Path | None = None,
    num_points: int = DEFAULT_NUM_POINTS,
) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2] if repo_root is None else Path(repo_root)
    traces_by_method = traces_by_method_from_payload(trace_payload)
    source_artifacts = {
        "trace_artifact": source_trace_path,
        "mechanics_module": "src/vi_full/three_dof_impedance_mechanics.py",
        "mechanics_exporter": "scripts/experiments/export_3dof_impedance_mechanics.py",
    }
    report = {
        "schema_version": MECHANICS_SCHEMA_VERSION,
        "export_name": "three_dof_success_matched_impedance_mechanics",
        "generated_at_utc": _utc_now(),
        "config": {
            "profile": trace_payload.get("config", {}).get("eval_profile", "unknown"),
            "curve_basis": "success_matched",
            "num_points": int(num_points),
            "method_names": list(traces_by_method),
            "source_config": trace_payload.get("config", {}),
        },
        "force_curve": compute_success_matched_force_curve(
            traces_by_method,
            num_points=num_points,
        ),
        "work_curve": compute_success_matched_work_curve(
            traces_by_method,
            num_points=num_points,
        ),
        "phase_portrait": compute_force_position_phase_portrait(
            traces_by_method,
            num_points=num_points,
            position_scale=1000.0,
        ),
        "pareto_rows": compute_force_work_pareto_rows(traces_by_method),
        "source_artifacts": source_artifacts,
        "source_hashes": _source_hashes(source_artifacts, repo_root=repo_root),
        "generating_command": generating_command,
        "git_commit": _git_commit_or_unknown(repo_root),
        "git_dirty": _git_dirty_or_true(repo_root),
    }
    return _json_safe(report)


def write_success_matched_mechanics_report(path: Path, report: Mapping[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_json_safe(report), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def export_force_work_pareto_csv(path: Path, report: Mapping[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "method",
        "label",
        "trace_count_used",
        "success_trace_count_total",
        "mean_peak_force",
        "std_peak_force",
        "mean_contact_work",
        "std_contact_work",
        "mean_final_position",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report["pareto_rows"])
    return path


def render_success_matched_mechanics_figure(
    report: Mapping[str, Any],
    *,
    output_dir: Path,
    stem: str = "fig3_high_friction_impedance_mechanism",
) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 8.0), constrained_layout=True)
    axes = axes.reshape(2, 2)

    force_curve = report["force_curve"]["curves"]
    work_curve = report["work_curve"]["curves"]
    phase_portrait = report["phase_portrait"]["portraits"]
    for method in report["config"]["method_names"]:
        color = METHOD_COLORS.get(method, "#666666")
        force = force_curve[method]
        x = np.asarray(force["normalized_contact_step"], dtype=np.float64)
        _plot_mean_std(
            axes[0, 0],
            x,
            force["force_mean"],
            force["force_std"],
            color=color,
            label=method,
        )
        work = work_curve[method]
        _plot_mean_std(
            axes[0, 1],
            np.asarray(work["normalized_contact_step"], dtype=np.float64),
            work["work_mean"],
            work["work_std"],
            color=color,
            label=method,
        )
        portrait = phase_portrait[method]
        axes[1, 0].plot(
            portrait["position_mean"],
            portrait["force_mean"],
            color=color,
            linewidth=2.2,
            label=method,
        )

    rows = list(report["pareto_rows"])
    x_positions = np.arange(len(rows), dtype=np.float64)
    colors = [METHOD_COLORS.get(str(row["method"]), "#666666") for row in rows]
    axes[1, 1].scatter(
        [float(row["mean_contact_work"]) for row in rows],
        [float(row["mean_peak_force"]) for row in rows],
        s=90,
        color=colors,
        edgecolor="white",
        linewidth=1.0,
        zorder=3,
    )
    for index, row in enumerate(rows):
        axes[1, 1].annotate(
            str(row["label"]),
            (
                float(row["mean_contact_work"]),
                float(row["mean_peak_force"]),
            ),
            xytext=(5, 5 + 4 * (index % 2)),
            textcoords="offset points",
            fontsize=8.2,
        )
    axes[1, 1].set_xlabel("mean final contact work")
    axes[1, 1].set_ylabel("mean peak force (N)")
    axes[1, 1].grid(color="#DDDDDD", linewidth=0.8)
    axes[1, 1].set_axisbelow(True)

    axes[0, 0].set_title("Success-matched force curve", fontsize=11.5, fontweight="bold")
    axes[0, 0].set_ylabel("contact force norm (N)")
    axes[0, 1].set_title("Success-matched work curve", fontsize=11.5, fontweight="bold")
    axes[0, 1].set_ylabel("cumulative contact work")
    axes[1, 0].set_title("Force-position phase portrait", fontsize=11.5, fontweight="bold")
    axes[1, 0].set_xlabel("insertion depth after contact onset (mm)")
    axes[1, 0].set_ylabel("contact force norm (N)")

    for ax in axes[0, :]:
        ax.set_xlabel("normalized successful contact step")
        ax.grid(color="#DDDDDD", linewidth=0.8)
        ax.set_axisbelow(True)
    axes[1, 0].grid(color="#DDDDDD", linewidth=0.8)
    axes[1, 0].set_axisbelow(True)
    axes[0, 0].legend(loc="upper left", frameon=False, fontsize=8.5)

    match_count = report["force_curve"]["matched_success_count"]
    fig.suptitle(
        f"High-friction success-matched impedance mechanics (n={match_count} successful traces per method)",
        fontsize=13,
        fontweight="bold",
    )
    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return pdf_path, png_path


def _matched_success_runs(
    traces_by_method: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    successes_by_method: dict[str, list[dict[str, Any]]] = {}
    for method, traces in traces_by_method.items():
        partitions = partition_traces_by_outcome(traces)
        successes_by_method[str(method)] = sorted(
            partitions["success"],
            key=_trace_sort_key,
        )
    if not successes_by_method:
        raise ValueError("At least one method is required.")
    matched_success_count = min(len(traces) for traces in successes_by_method.values())
    if matched_success_count <= 0:
        raise ValueError("Every method must contain at least one successful trace.")
    return {
        "matched_success_count": matched_success_count,
        "success_counts": {
            method: len(traces) for method, traces in successes_by_method.items()
        },
        "runs": {
            method: traces[:matched_success_count]
            for method, traces in successes_by_method.items()
        },
    }


def _trace_sort_key(trace: Mapping[str, Any]) -> tuple[int, int, int]:
    train_seed = trace.get("train_seed")
    return (
        -1 if train_seed is None else int(train_seed),
        int(trace.get("trace_episode_index", 0)),
        int(trace.get("rollout_seed", 0)),
    )


def _is_success(trace: Mapping[str, Any]) -> bool:
    if "is_success" in trace:
        return bool(trace["is_success"])
    if "success" in trace:
        return bool(trace["success"])
    return str(trace.get("outcome", "")).lower() == "success"


def _trace_steps(trace_run: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    steps = trace_run.get("trace", trace_run.get("steps", []))
    if not isinstance(steps, list) or not steps:
        raise ValueError("Trace run must contain a non-empty trace/steps list.")
    return steps


def _contact_segment(steps: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    for index, step in enumerate(steps):
        if _step_channel(step, "force") > DEFAULT_CONTACT_THRESHOLD_N:
            return steps[index:]
    return steps


def _stack_trace_channel(
    traces: Sequence[Mapping[str, Any]],
    channel: str,
    num_points: int,
    *,
    scale: float = 1.0,
) -> np.ndarray:
    return np.stack(
        [
            _interp_trace_channel(_trace_steps(trace), channel, num_points, scale=scale)
            for trace in traces
        ],
        axis=0,
    )


def _interp_trace_channel(
    steps: list[Mapping[str, Any]],
    channel: str,
    num_points: int,
    *,
    scale: float = 1.0,
) -> np.ndarray:
    segment = _contact_segment(steps)
    if channel == "work":
        values = np.asarray(_work_series(segment), dtype=np.float64)
    else:
        values = np.asarray(
            [_step_channel(step, channel) * scale for step in segment],
            dtype=np.float64,
        )
    if values.size == 0:
        return np.zeros(num_points, dtype=np.float64)
    if values.size == 1:
        return np.full(num_points, float(values[0]), dtype=np.float64)
    source_x = np.linspace(0.0, 1.0, num=values.size, dtype=np.float64)
    target_x = np.linspace(0.0, 1.0, num=num_points, dtype=np.float64)
    return np.interp(target_x, source_x, values)


def _work_series(steps: list[Mapping[str, Any]]) -> list[float]:
    if all("contact_work" in step for step in steps):
        return [float(step["contact_work"]) for step in steps]
    if all("cumulative_contact_work" in step for step in steps):
        return [float(step["cumulative_contact_work"]) for step in steps]
    positions = np.asarray([_step_channel(step, "position") for step in steps], dtype=np.float64)
    forces = np.asarray([_step_channel(step, "force") for step in steps], dtype=np.float64)
    increments = np.abs(np.diff(positions, prepend=positions[0])) * forces
    return np.cumsum(increments).tolist()


def _step_channel(step: Mapping[str, Any], channel: str) -> float:
    if channel == "force":
        return _first_float(step, ("force", "contact_force_norm"))
    if channel == "position":
        return _first_float(step, ("position", "insertion_depth", "surface_height"))
    raise KeyError(channel)


def _first_float(step: Mapping[str, Any], keys: Sequence[str]) -> float:
    for key in keys:
        if key in step:
            return float(step[key])
    raise KeyError(f"None of the fields are present: {keys}")


def _plot_mean_std(
    ax,
    x: np.ndarray,
    mean_values: Sequence[float],
    std_values: Sequence[float],
    *,
    color: str,
    label: str,
) -> None:
    mean = np.asarray(mean_values, dtype=np.float64)
    std = np.asarray(std_values, dtype=np.float64)
    ax.plot(x, mean, color=color, linewidth=2.1, label=label)
    ax.fill_between(x, mean - std, mean + std, color=color, alpha=0.12, linewidth=0.0)


def _source_hashes(source_artifacts: Mapping[str, str], *, repo_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for source_name, relative_path in source_artifacts.items():
        path = repo_root / relative_path
        if path.exists():
            hashes[source_name] = calculate_sha256(path)
    return hashes


def _git_commit_or_unknown(repo_root: Path) -> str:
    try:
        return git_commit(repo_root=repo_root)
    except Exception:
        return "unknown"


def _git_dirty_or_true(repo_root: Path) -> bool:
    try:
        return git_dirty(repo_root=repo_root)
    except Exception:
        return True


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
