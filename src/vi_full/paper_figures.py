from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402


@dataclass(frozen=True, slots=True)
class ContactWindowTrackSummary:
    label: str
    safe_window_mm: float
    first_jam_mm: float


@dataclass(frozen=True, slots=True)
class ContactWindowVariantSummary:
    variant_name: str
    panel_title: str
    transition_note: str
    safe_window_mm: float
    first_jam_mm: float
    min_stiffness: ContactWindowTrackSummary
    max_stiffness: ContactWindowTrackSummary


@dataclass(frozen=True, slots=True)
class Figure1ContactTransitionSummary:
    baseline: ContactWindowVariantSummary
    repaired: ContactWindowVariantSummary


@dataclass(frozen=True, slots=True)
class ResetCoverageStageSummary:
    label: str
    depth_fraction_range: tuple[float, float]
    xy_noise_mm: float
    weight: float


@dataclass(frozen=True, slots=True)
class ResetCoverageAuditSummary:
    reset_stage_count: int
    reset_stages: tuple[ResetCoverageStageSummary, ...]
    bc_reset_mean_contact_steps: float
    hard_eval_mean_contact_steps: float
    hard_eval_success_rate: float


@dataclass(frozen=True, slots=True)
class BudgetSweepEntrySummary:
    config_label: str
    bc_rollout_episodes: int
    bc_pretrain_steps: int
    bc_batch_size: int
    hard_eval_success_rate: float
    hard_eval_mean_contact_steps: float


@dataclass(frozen=True, slots=True)
class Figure2BCCoverageSummary:
    before: ResetCoverageAuditSummary
    after: ResetCoverageAuditSummary
    budgets: tuple[BudgetSweepEntrySummary, ...]
    default_budget: BudgetSweepEntrySummary
    best_budget: BudgetSweepEntrySummary


@dataclass(frozen=True, slots=True)
class CausalFactorPointSummary:
    point_name: str
    factor_value: str | int
    label: str
    display_label: str
    profile_mean_success: float
    profile_mean_contact_steps: float
    profile_mean_jam_rate: float
    train_reset_stage_count: int
    bc_reset_stage_count: int


@dataclass(frozen=True, slots=True)
class CausalBudgetSuiteSummary:
    suite_name: str
    label: str
    points: tuple[CausalFactorPointSummary, ...]


@dataclass(frozen=True, slots=True)
class Figure2CausalSummary:
    demonstration_coverage: tuple[CausalFactorPointSummary, ...]
    reset_coverage: tuple[CausalFactorPointSummary, ...]
    bc_optimization_depth: tuple[CausalFactorPointSummary, ...]
    best_bc_optimization_depth: CausalFactorPointSummary
    algorithm_budget_suites: tuple[CausalBudgetSuiteSummary, ...]
    bc_only_anchor: CausalFactorPointSummary


@dataclass(frozen=True, slots=True)
class AxialTolerancePointSummary:
    tolerance_mm: float
    success_rate: float


@dataclass(frozen=True, slots=True)
class AxialToleranceProfileSummary:
    profile_name: str
    points: tuple[AxialTolerancePointSummary, ...]


@dataclass(frozen=True, slots=True)
class FailureBucketProfileSummary:
    profile_name: str
    success_rate: float
    axial_failures: int
    lateral_failures: int
    speed_failures: int
    mixed_failures: int
    mean_failed_axial_mm: float
    mean_failed_lateral_mm: float


@dataclass(frozen=True, slots=True)
class Figure3CriterionDecompositionSummary:
    axial_profiles: tuple[AxialToleranceProfileSummary, ...]
    failure_profiles: tuple[FailureBucketProfileSummary, ...]
    total_axial_failures: int
    total_non_axial_failures: int


@dataclass(frozen=True, slots=True)
class AxialBandSuccessSummary:
    tolerance_mm: float
    success_rate: float


@dataclass(frozen=True, slots=True)
class PerProfileAxialBandSummary:
    profile_name: str
    bands: tuple[AxialBandSuccessSummary, ...]


@dataclass(frozen=True, slots=True)
class FigureA1PerProfileAxialBandSummary:
    profiles: tuple[PerProfileAxialBandSummary, ...]
    mean_bands: tuple[AxialBandSuccessSummary, ...]


@dataclass(frozen=True, slots=True)
class SweepPointSummary:
    x_value: float
    display_label: str
    success_rate: float


@dataclass(frozen=True, slots=True)
class SweepProfileSummary:
    profile_name: str
    points: tuple[SweepPointSummary, ...]


@dataclass(frozen=True, slots=True)
class FigureA2StrictCriterionDecompositionSummary:
    old_lateral_profiles: tuple[SweepProfileSummary, ...]
    axial_profiles: tuple[AxialToleranceProfileSummary, ...]
    speed_profiles: tuple[SweepProfileSummary, ...]
    strict_lateral_profiles: tuple[SweepProfileSummary, ...]
    failure_profiles: tuple[FailureBucketProfileSummary, ...]
    total_axial_failures: int
    total_non_axial_failures: int


@dataclass(frozen=True, slots=True)
class TeacherAblationProfileSummary:
    profile_name: str
    success_rate: float
    jam_rate: float
    mean_final_distance_mm: float
    mean_peak_contact_force_n: float
    mean_contact_steps: float


@dataclass(frozen=True, slots=True)
class TeacherAblationSuiteSummary:
    suite_name: str
    display_name: str
    teacher_motion_rule: str
    teacher_impedance_rule: str
    five_profile_success_rate: float
    five_profile_jam_rate: float
    mean_final_distance_mm: float
    mean_peak_contact_force_n: float
    mean_contact_steps: float
    per_profile: tuple[TeacherAblationProfileSummary, ...]


@dataclass(frozen=True, slots=True)
class FigureA3TeacherAblationSummary:
    suites: tuple[TeacherAblationSuiteSummary, ...]


@dataclass(frozen=True, slots=True)
class TerminationDiagnosticsSuiteSummary:
    suite_name: str
    display_name: str
    jam_rate: float
    force_threshold_termination_rate: float
    blocked_contact_termination_rate: float
    force_threshold_only_termination_rate: float
    blocked_contact_only_termination_rate: float
    force_and_blocked_termination_rate: float
    documented_force_jam_rate: float


@dataclass(frozen=True, slots=True)
class FigureA4TerminationDiagnosticsSummary:
    suites: tuple[TerminationDiagnosticsSuiteSummary, ...]


def _m_to_mm(value_m: float) -> float:
    return float(value_m) * 1000.0


def _load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _extract_track_summary(track: dict, label: str) -> ContactWindowTrackSummary:
    return ContactWindowTrackSummary(
        label=label,
        safe_window_mm=_m_to_mm(track["largest_safe_contact_window_width_m"]),
        first_jam_mm=_m_to_mm(track["first_jammed_xy_error_m"]),
    )


def _extract_variant_summary(variant: dict, panel_title: str, transition_note: str) -> ContactWindowVariantSummary:
    sweeps = variant["nominal_surface_extended_sweeps"]
    min_track = _extract_track_summary(sweeps["min_stiffness"], "min stiffness")
    max_track = _extract_track_summary(sweeps["max_stiffness"], "max stiffness")
    return ContactWindowVariantSummary(
        variant_name=str(variant["variant_name"]),
        panel_title=panel_title,
        transition_note=transition_note,
        safe_window_mm=max_track.safe_window_mm,
        first_jam_mm=max_track.first_jam_mm,
        min_stiffness=min_track,
        max_stiffness=max_track,
    )


def load_figure1_contact_transition_summary(audit_path: Path) -> Figure1ContactTransitionSummary:
    raw = _load_json(audit_path)
    baseline = _extract_variant_summary(
        raw["baseline_variant"],
        panel_title="Original analytical contact law",
        transition_note="no transition band",
    )
    repaired = _extract_variant_summary(
        raw["stiffness_aware_probe_variant"],
        panel_title="Repaired contact law",
        transition_note="1 mm band + stiffness-aware scaling",
    )
    return Figure1ContactTransitionSummary(baseline=baseline, repaired=repaired)


def _stage_label(stage: dict) -> str:
    start_depth = float(stage["start_depth_fraction_range"][0])
    if start_depth <= 0.2:
        return "far"
    if start_depth <= 0.6:
        return "mid"
    return "near"


def _extract_reset_stage_summary(stage: dict) -> ResetCoverageStageSummary:
    return ResetCoverageStageSummary(
        label=_stage_label(stage),
        depth_fraction_range=(
            float(stage["start_depth_fraction_range"][0]),
            float(stage["start_depth_fraction_range"][1]),
        ),
        xy_noise_mm=_m_to_mm(stage["start_xy_noise_m"]),
        weight=float(stage["weight"]),
    )


def _extract_reset_coverage_audit_summary(raw: dict) -> ResetCoverageAuditSummary:
    bc_reset = raw["evaluations"]["bc_reset"]
    hard_eval = raw["evaluations"]["hard_eval"]
    stages = tuple(
        _extract_reset_stage_summary(stage)
        for stage in bc_reset["reset_config"]["curriculum_stages"]
    )
    return ResetCoverageAuditSummary(
        reset_stage_count=int(bc_reset["reset_stage_count"]),
        reset_stages=stages,
        bc_reset_mean_contact_steps=float(bc_reset["summary"]["mean_contact_steps"]),
        hard_eval_mean_contact_steps=float(hard_eval["summary"]["mean_contact_steps"]),
        hard_eval_success_rate=float(hard_eval["summary"]["success_rate"]),
    )


def _extract_budget_entry_summary(entry: dict) -> BudgetSweepEntrySummary:
    config = entry["config"]
    return BudgetSweepEntrySummary(
        config_label=f'{config["bc_rollout_episodes"]} / {config["bc_pretrain_steps"]} / {config["bc_batch_size"]}',
        bc_rollout_episodes=int(config["bc_rollout_episodes"]),
        bc_pretrain_steps=int(config["bc_pretrain_steps"]),
        bc_batch_size=int(config["bc_batch_size"]),
        hard_eval_success_rate=float(entry["hard_eval_summary"]["success_rate"]),
        hard_eval_mean_contact_steps=float(entry["hard_eval_summary"]["mean_contact_steps"]),
    )


def load_figure2_bc_coverage_summary(
    before_audit_path: Path,
    after_audit_path: Path,
    budget_sweep_path: Path,
) -> Figure2BCCoverageSummary:
    before = _extract_reset_coverage_audit_summary(_load_json(before_audit_path))
    after = _extract_reset_coverage_audit_summary(_load_json(after_audit_path))
    budget_raw = _load_json(budget_sweep_path)
    budgets = tuple(_extract_budget_entry_summary(entry) for entry in budget_raw["budget_sweep"])
    default_budget = next(
        entry
        for entry in budgets
        if (
            entry.bc_rollout_episodes,
            entry.bc_pretrain_steps,
            entry.bc_batch_size,
        )
        == (8, 32, 64)
    )
    best_budget = max(
        budgets,
        key=lambda entry: (
            entry.hard_eval_success_rate,
            entry.hard_eval_mean_contact_steps,
        ),
    )
    return Figure2BCCoverageSummary(
        before=before,
        after=after,
        budgets=budgets,
        default_budget=default_budget,
        best_budget=best_budget,
    )


def _mean_per_profile_metric(per_profile_metrics: dict, key: str) -> float:
    aggregates = [
        profile_metrics["aggregate"] for profile_metrics in per_profile_metrics.values()
    ]
    return sum(float(aggregate[key]) for aggregate in aggregates) / float(len(aggregates))


def _display_label_from_point_name(point_name: str, factor_value: str | int) -> str:
    labels = {
        "reset_coverage_collapse": "collapse",
        "reset_repaired": "repaired",
        "bc_pretrain_steps_0": "0",
        "bc_pretrain_steps_8": "8",
        "bc_pretrain_steps_32": "32",
        "bc_pretrain_steps_64": "64",
    }
    if point_name in labels:
        return labels[point_name]
    if isinstance(factor_value, (int, float)):
        return f"{factor_value:g}"
    return str(factor_value).replace("_", " ")


def _extract_causal_factor_point_summary(point: dict) -> CausalFactorPointSummary:
    per_profile_metrics = point["per_profile_metrics"]
    first_aggregate = next(iter(per_profile_metrics.values()))["aggregate"]
    factor_value = point["factor_value"]
    point_name = str(
        point.get("point_name", point.get("suite_name", point.get("label", factor_value)))
    )
    label = str(point.get("label", point_name))
    return CausalFactorPointSummary(
        point_name=point_name,
        factor_value=factor_value,
        label=label,
        display_label=_display_label_from_point_name(point_name, factor_value),
        profile_mean_success=_mean_per_profile_metric(per_profile_metrics, "success_rate_mean"),
        profile_mean_contact_steps=_mean_per_profile_metric(
            per_profile_metrics,
            "mean_contact_steps_mean",
        ),
        profile_mean_jam_rate=_mean_per_profile_metric(per_profile_metrics, "jam_rate_mean"),
        train_reset_stage_count=int(first_aggregate.get("train_reset_stage_count", 0)),
        bc_reset_stage_count=int(first_aggregate.get("bc_reset_stage_count", 0)),
    )


def _load_factor_sweep_points(path: Path) -> tuple[CausalFactorPointSummary, ...]:
    raw = _load_json(path)
    return tuple(_extract_causal_factor_point_summary(point) for point in raw["points"])


def _load_algorithm_budget_suites(
    path: Path,
) -> tuple[tuple[CausalBudgetSuiteSummary, ...], CausalFactorPointSummary]:
    raw = _load_json(path)
    suites = tuple(
        CausalBudgetSuiteSummary(
            suite_name=str(suite["suite_name"]),
            label=str(suite["label"]),
            points=tuple(
                _extract_causal_factor_point_summary(point) for point in suite["points"]
            ),
        )
        for suite in raw["budgeted_suites"]
    )
    anchor = _extract_causal_factor_point_summary(raw["static_anchors"][0])
    return suites, anchor


def load_figure2_causal_summary(
    demonstration_coverage_path: Path,
    reset_coverage_path: Path,
    bc_optimization_depth_path: Path,
    algorithm_budget_comparison_path: Path,
) -> Figure2CausalSummary:
    demonstration_coverage = _load_factor_sweep_points(demonstration_coverage_path)
    reset_coverage = _load_factor_sweep_points(reset_coverage_path)
    bc_optimization_depth = _load_factor_sweep_points(bc_optimization_depth_path)
    algorithm_budget_suites, bc_only_anchor = _load_algorithm_budget_suites(
        algorithm_budget_comparison_path
    )
    best_bc_optimization_depth = max(
        bc_optimization_depth,
        key=lambda point: (
            point.profile_mean_success,
            point.profile_mean_contact_steps,
            -point.profile_mean_jam_rate,
        ),
    )
    return Figure2CausalSummary(
        demonstration_coverage=demonstration_coverage,
        reset_coverage=reset_coverage,
        bc_optimization_depth=bc_optimization_depth,
        best_bc_optimization_depth=best_bc_optimization_depth,
        algorithm_budget_suites=algorithm_budget_suites,
        bc_only_anchor=bc_only_anchor,
    )


def _profile_sort_key(profile_name: str) -> int:
    order = {
        "nominal": 0,
        "tight_clearance": 1,
        "high_friction": 2,
        "offset_bias": 3,
        "noisy_force": 4,
    }
    return order[profile_name]


def _profile_color(profile_name: str) -> str:
    palette = {
        "nominal": "#4F81BD",
        "tight_clearance": "#C0504D",
        "high_friction": "#9BBB59",
        "offset_bias": "#8064A2",
        "noisy_force": "#F79646",
    }
    return palette[profile_name]


def _extract_axial_profile_summary(profile_name: str, raw: dict) -> AxialToleranceProfileSummary:
    points = tuple(
        AxialTolerancePointSummary(
            tolerance_mm=float(tolerance_key.removesuffix("mm")),
            success_rate=float(tolerance_value["aggregate"]["success_rate_mean"]),
        )
        for tolerance_key, tolerance_value in sorted(
            raw.items(),
            key=lambda item: float(item[0].removesuffix("mm")),
        )
    )
    return AxialToleranceProfileSummary(profile_name=profile_name, points=points)


def _extract_failure_profile_summary(profile_name: str, raw: dict) -> FailureBucketProfileSummary:
    buckets = raw["failure_buckets"]
    mixed_failures = sum(
        int(value)
        for key, value in buckets.items()
        if key not in {"axial", "lateral", "speed"}
    )
    return FailureBucketProfileSummary(
        profile_name=profile_name,
        success_rate=float(raw["success_rate"]),
        axial_failures=int(buckets.get("axial", 0)),
        lateral_failures=int(buckets.get("lateral", 0)),
        speed_failures=int(buckets.get("speed", 0)),
        mixed_failures=mixed_failures,
        mean_failed_axial_mm=float(raw["mean_failed_axial_error_mm"]),
        mean_failed_lateral_mm=float(raw["mean_failed_lateral_error_mm"]),
    )


def load_figure3_criterion_decomposition_summary(
    axial_sweep_path: Path,
    failure_bucket_path: Path,
) -> Figure3CriterionDecompositionSummary:
    axial_raw = _load_json(axial_sweep_path)
    failure_raw = _load_json(failure_bucket_path)
    axial_profiles = tuple(
        _extract_axial_profile_summary(profile_name, axial_raw["results"][profile_name])
        for profile_name in sorted(axial_raw["results"].keys(), key=_profile_sort_key)
    )
    failure_profiles = tuple(
        _extract_failure_profile_summary(profile_name, failure_raw["results"][profile_name])
        for profile_name in sorted(failure_raw["results"].keys(), key=_profile_sort_key)
    )
    total_axial_failures = sum(profile.axial_failures for profile in failure_profiles)
    total_non_axial_failures = sum(
        profile.lateral_failures + profile.speed_failures + profile.mixed_failures
        for profile in failure_profiles
    )
    return Figure3CriterionDecompositionSummary(
        axial_profiles=axial_profiles,
        failure_profiles=failure_profiles,
        total_axial_failures=total_axial_failures,
        total_non_axial_failures=total_non_axial_failures,
    )


def _extract_selected_axial_bands(raw: dict, tolerance_keys: tuple[str, ...]) -> tuple[AxialBandSuccessSummary, ...]:
    return tuple(
        AxialBandSuccessSummary(
            tolerance_mm=float(tolerance_key.removesuffix("mm")),
            success_rate=float(raw[tolerance_key]["aggregate"]["success_rate_mean"]),
        )
        for tolerance_key in tolerance_keys
    )


def load_figurea1_per_profile_axial_band_summary(
    axial_tail_sweep_path: Path,
) -> FigureA1PerProfileAxialBandSummary:
    raw = _load_json(axial_tail_sweep_path)
    selected_tolerances = ("2.0mm", "3.0mm", "3.5mm")
    profiles = tuple(
        PerProfileAxialBandSummary(
            profile_name=profile_name,
            bands=_extract_selected_axial_bands(raw["results"][profile_name], selected_tolerances),
        )
        for profile_name in sorted(raw["results"].keys(), key=_profile_sort_key)
    )
    mean_bands = tuple(
        AxialBandSuccessSummary(
            tolerance_mm=float(tolerance_key.removesuffix("mm")),
            success_rate=sum(
                next(band.success_rate for band in profile.bands if band.tolerance_mm == float(tolerance_key.removesuffix("mm")))
                for profile in profiles
            )
            / len(profiles),
        )
        for tolerance_key in selected_tolerances
    )
    return FigureA1PerProfileAxialBandSummary(profiles=profiles, mean_bands=mean_bands)


def _extract_sweep_profile_summary(
    profile_name: str,
    raw: dict,
    ordered_keys: tuple[str, ...],
    parse_x_value,
) -> SweepProfileSummary:
    return SweepProfileSummary(
        profile_name=profile_name,
        points=tuple(
            SweepPointSummary(
                x_value=parse_x_value(key),
                display_label=key,
                success_rate=float(raw[key]["aggregate"]["success_rate_mean"]),
            )
            for key in ordered_keys
        ),
    )


def load_figurea2_strict_criterion_decomposition_summary(
    success_tolerance_path: Path,
    axial_sweep_path: Path,
    speed_sweep_path: Path,
    lateral_sweep_path: Path,
    failure_bucket_path: Path,
) -> FigureA2StrictCriterionDecompositionSummary:
    old_lateral_raw = _load_json(success_tolerance_path)
    speed_raw = _load_json(speed_sweep_path)
    strict_lateral_raw = _load_json(lateral_sweep_path)
    figure3_summary = load_figure3_criterion_decomposition_summary(
        axial_sweep_path=axial_sweep_path,
        failure_bucket_path=failure_bucket_path,
    )

    old_lateral_keys = ("0.8mm", "1.0mm", "1.2mm", "1.5mm")
    speed_keys = ("0.08mps", "0.10mps", "0.12mps", "0.15mps", "0.20mps")
    strict_lateral_keys = ("0.8mm", "1.0mm", "1.2mm", "1.5mm")

    old_lateral_profiles = tuple(
        _extract_sweep_profile_summary(
            profile_name,
            old_lateral_raw["results"][profile_name],
            old_lateral_keys,
            parse_x_value=lambda key: float(key.removesuffix("mm")),
        )
        for profile_name in sorted(old_lateral_raw["results"].keys(), key=_profile_sort_key)
    )
    speed_profiles = tuple(
        _extract_sweep_profile_summary(
            profile_name,
            speed_raw["results"][profile_name],
            speed_keys,
            parse_x_value=lambda key: float(key.removesuffix("mps")),
        )
        for profile_name in sorted(speed_raw["results"].keys(), key=_profile_sort_key)
    )
    strict_lateral_profiles = tuple(
        _extract_sweep_profile_summary(
            profile_name,
            strict_lateral_raw["results"][profile_name],
            strict_lateral_keys,
            parse_x_value=lambda key: float(key.removesuffix("mm")),
        )
        for profile_name in sorted(strict_lateral_raw["results"].keys(), key=_profile_sort_key)
    )
    return FigureA2StrictCriterionDecompositionSummary(
        old_lateral_profiles=old_lateral_profiles,
        axial_profiles=figure3_summary.axial_profiles,
        speed_profiles=speed_profiles,
        strict_lateral_profiles=strict_lateral_profiles,
        failure_profiles=figure3_summary.failure_profiles,
        total_axial_failures=figure3_summary.total_axial_failures,
        total_non_axial_failures=figure3_summary.total_non_axial_failures,
    )


def load_figurea3_teacher_ablation_summary(
    benchmark_report_path: Path,
    fixed_impedance_report_path: Path | None = None,
) -> FigureA3TeacherAblationSummary:
    from vi_full.paper_tables import build_3dof_appendix_table_export

    export_payload = build_3dof_appendix_table_export(
        benchmark_report_path=Path(benchmark_report_path),
        fixed_impedance_report_path=(
            Path(fixed_impedance_report_path)
            if fixed_impedance_report_path is not None
            else None
        ),
    )
    suites: list[TeacherAblationSuiteSummary] = []
    for row in export_payload["teacher_rows"]:
        per_profile = tuple(
            TeacherAblationProfileSummary(
                profile_name=str(profile_name),
                success_rate=float(metrics["success_rate"]),
                jam_rate=float(metrics["jam_rate"]),
                mean_final_distance_mm=float(metrics["mean_final_distance_mm"]),
                mean_peak_contact_force_n=float(metrics["mean_peak_contact_force_n"]),
                mean_contact_steps=float(metrics["mean_contact_steps"]),
            )
            for profile_name, metrics in row["per_profile"].items()
        )
        suites.append(
            TeacherAblationSuiteSummary(
                suite_name=str(row["suite_name"]),
                display_name=str(row["display_name"]),
                teacher_motion_rule=str(row["teacher_motion_rule"]),
                teacher_impedance_rule=str(row["teacher_impedance_rule"]),
                five_profile_success_rate=float(row["five_profile_mean"]["success_rate"]),
                five_profile_jam_rate=float(row["five_profile_mean"]["jam_rate"]),
                mean_final_distance_mm=float(
                    row["five_profile_mean"]["mean_final_distance_mm"]
                ),
                mean_peak_contact_force_n=float(
                    row["five_profile_mean"]["mean_peak_contact_force_n"]
                ),
                mean_contact_steps=float(row["five_profile_mean"]["mean_contact_steps"]),
                per_profile=per_profile,
            )
        )
    return FigureA3TeacherAblationSummary(suites=tuple(suites))


def load_figurea4_termination_diagnostics_summary(
    benchmark_report_path: Path,
    fixed_impedance_report_path: Path | None = None,
) -> FigureA4TerminationDiagnosticsSummary:
    from vi_full.paper_tables import build_3dof_appendix_table_export

    export_payload = build_3dof_appendix_table_export(
        benchmark_report_path=Path(benchmark_report_path),
        fixed_impedance_report_path=(
            Path(fixed_impedance_report_path)
            if fixed_impedance_report_path is not None
            else None
        ),
    )
    suites = tuple(
        TerminationDiagnosticsSuiteSummary(
            suite_name=str(row["suite_name"]),
            display_name=str(row["display_name"]),
            jam_rate=float(row["diagnostics"]["jam_rate"]),
            force_threshold_termination_rate=float(
                row["diagnostics"]["force_threshold_termination_rate"]
            ),
            blocked_contact_termination_rate=float(
                row["diagnostics"]["blocked_contact_termination_rate"]
            ),
            force_threshold_only_termination_rate=float(
                row["diagnostics"]["force_threshold_only_termination_rate"]
            ),
            blocked_contact_only_termination_rate=float(
                row["diagnostics"]["blocked_contact_only_termination_rate"]
            ),
            force_and_blocked_termination_rate=float(
                row["diagnostics"]["force_and_blocked_termination_rate"]
            ),
            documented_force_jam_rate=float(
                row["diagnostics"]["documented_force_jam_rate"]
            ),
        )
        for row in export_payload["diagnostic_rows"]
    )
    return FigureA4TerminationDiagnosticsSummary(suites=suites)


def _render_variant_panel(ax, variant: ContactWindowVariantSummary, x_max_mm: float) -> None:
    tracks = [variant.min_stiffness, variant.max_stiffness]
    y_positions = [1.0, 0.0]
    bar_height = 0.34
    safe_color = "#6AA84F"
    jam_color = "#C94F4F"
    bg_jam_color = "#F4CCCC"

    ax.axvspan(variant.first_jam_mm, x_max_mm, color=bg_jam_color, alpha=0.28, zorder=0)

    for y, track in zip(y_positions, tracks):
        ax.broken_barh(
            [(0.0, track.safe_window_mm)],
            (y - bar_height / 2.0, bar_height),
            facecolors=safe_color,
            edgecolors="none",
            alpha=0.92,
            zorder=2,
        )
        ax.axvline(track.first_jam_mm, color=jam_color, linestyle="--", linewidth=1.5, zorder=3)
        ax.text(
            max(track.safe_window_mm * 0.5, 0.08),
            y,
            f"{track.safe_window_mm:.2f} mm",
            ha="center",
            va="center",
            fontsize=9,
            color="white",
            fontweight="bold",
            zorder=4,
        )

    ax.set_yticks(y_positions, [track.label for track in tracks])
    ax.set_xlim(0.0, x_max_mm)
    ax.set_ylim(-0.6, 1.6)
    ax.grid(axis="x", color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(variant.panel_title, fontsize=12, fontweight="bold", pad=10)
    ax.text(
        0.98,
        0.93,
        f"{variant.transition_note}\nfirst jam: {variant.first_jam_mm:.2f} mm",
        ha="right",
        va="top",
        fontsize=9,
        transform=ax.transAxes,
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": "#CCCCCC"},
    )


def _render_coverage_row(
    ax,
    y_center: float,
    audit: ResetCoverageAuditSummary,
    row_label: str,
    stage_colors: dict[str, str],
) -> None:
    bar_height = 0.34
    for stage in audit.reset_stages:
        start, end = stage.depth_fraction_range
        ax.add_patch(
            Rectangle(
                (start, y_center - bar_height / 2.0),
                end - start,
                bar_height,
                facecolor=stage_colors[stage.label],
                edgecolor="white",
                linewidth=1.2,
                alpha=0.94,
            )
        )
        ax.text(
            (start + end) / 2.0,
            y_center,
            f"{stage.label}\n{stage.xy_noise_mm:.1f} mm | {stage.weight * 100:.0f}%",
            ha="center",
            va="center",
            fontsize=8.5,
            color="white",
            fontweight="bold",
        )
    ax.text(
        -0.03,
        y_center,
        f"{row_label}\n{audit.reset_stage_count} stages",
        ha="right",
        va="center",
        fontsize=9,
        fontweight="bold",
        transform=ax.get_yaxis_transform(),
    )


def _render_figure2_coverage_panel(ax, summary: Figure2BCCoverageSummary) -> None:
    stage_colors = {
        "far": "#4F81BD",
        "mid": "#6AA84F",
        "near": "#C27BA0",
    }
    ax.axvspan(0.0, 0.2, color=stage_colors["far"], alpha=0.08, zorder=0)
    ax.axvspan(0.3, 0.6, color=stage_colors["mid"], alpha=0.08, zorder=0)
    ax.axvspan(0.75, 0.9, color=stage_colors["near"], alpha=0.08, zorder=0)
    _render_coverage_row(ax, y_center=1.0, audit=summary.before, row_label="before", stage_colors=stage_colors)
    _render_coverage_row(ax, y_center=0.0, audit=summary.after, row_label="after", stage_colors=stage_colors)
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(-0.6, 1.6)
    ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticks([])
    ax.grid(axis="x", color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title("Reset coverage repair", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("demonstration reset depth fraction")

    legend_handles = [
        Patch(facecolor=stage_colors["far"], edgecolor="none", label="far approach"),
        Patch(facecolor=stage_colors["mid"], edgecolor="none", label="mid approach"),
        Patch(facecolor=stage_colors["near"], edgecolor="none", label="near contact"),
    ]
    ax.legend(handles=legend_handles, loc="upper left", frameon=False, fontsize=9)


def _render_figure2_budget_panel(ax, summary: Figure2BCCoverageSummary) -> None:
    budgets = summary.budgets
    x_positions = list(range(len(budgets)))
    success_rates = [entry.hard_eval_success_rate for entry in budgets]
    contact_steps = [entry.hard_eval_mean_contact_steps for entry in budgets]

    bar_colors = []
    for entry in budgets:
        if entry == summary.default_budget:
            bar_colors.append("#4F81BD")
        elif entry == summary.best_budget:
            bar_colors.append("#6AA84F")
        else:
            bar_colors.append("#B7B7B7")

    bars = ax.bar(x_positions, success_rates, color=bar_colors, width=0.62, edgecolor="none")
    ax.set_ylim(0.0, 1.1)
    ax.set_ylabel("hard-eval success rate")
    ax.set_xticks(x_positions, [entry.config_label for entry in budgets], rotation=20, ha="right")
    ax.set_title("Expanded coverage + BC budget sweep", fontsize=12, fontweight="bold", pad=10)
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)

    ax2 = ax.twinx()
    ax2.plot(
        x_positions,
        contact_steps,
        color="#C94F4F",
        marker="o",
        linewidth=2.0,
        markersize=5.5,
    )
    ax2.set_ylim(0.0, max(contact_steps) + 6.0)
    ax2.set_ylabel("hard-eval contact steps")

    for idx, (entry, bar) in enumerate(zip(budgets, bars)):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + 0.04,
            f"{entry.hard_eval_success_rate:.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )
        ax2.text(
            idx,
            contact_steps[idx] + 1.0,
            f"{contact_steps[idx]:.1f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color="#C94F4F",
        )

    default_index = budgets.index(summary.default_budget)
    best_index = budgets.index(summary.best_budget)
    ax.annotate(
        "default mainline",
        xy=(default_index, success_rates[default_index]),
        xytext=(default_index + 0.18, 0.92),
        textcoords="data",
        arrowprops={"arrowstyle": "->", "color": "#4F81BD", "linewidth": 1.2},
        fontsize=9,
        color="#4F81BD",
        fontweight="bold",
    )
    ax.annotate(
        "best hard-eval success",
        xy=(best_index, success_rates[best_index]),
        xytext=(best_index - 0.7, 1.03),
        textcoords="data",
        arrowprops={"arrowstyle": "->", "color": "#6AA84F", "linewidth": 1.2},
        fontsize=9,
        color="#4F81BD",
        fontweight="bold",
    )

    legend_handles = [
        Patch(facecolor="#4F81BD", edgecolor="none", label="default 8 / 32 / 64"),
        Patch(facecolor="#6AA84F", edgecolor="none", label="best success in frozen sweep"),
        Line2D([0], [0], color="#C94F4F", marker="o", linewidth=2.0, label="mean contact steps"),
    ]
    ax.legend(handles=legend_handles, loc="upper left", frameon=False, fontsize=9)


def _render_figure2_causal_controls_panel(ax, summary: Figure2CausalSummary) -> None:
    group_specs = [
        ("demo support", summary.demonstration_coverage),
        ("train reset", summary.reset_coverage),
        ("BC steps", summary.bc_optimization_depth),
    ]
    success_colors = {
        "collapse": "#C0504D",
        "repaired": "#4F81BD",
        "0": "#B7B7B7",
        "8": "#F79646",
        "32": "#6AA84F",
        "64": "#7F7F7F",
    }

    x_positions: list[float] = []
    x_labels: list[str] = []
    heights: list[float] = []
    colors: list[str] = []
    point_summaries: list[CausalFactorPointSummary] = []
    group_centers: list[float] = []
    cursor = 0.0

    for group_label, points in group_specs:
        group_start = cursor
        for point in points:
            x_positions.append(cursor)
            x_labels.append(point.display_label)
            heights.append(point.profile_mean_success)
            colors.append(success_colors.get(point.display_label, "#4F81BD"))
            point_summaries.append(point)
            cursor += 1.0
        group_centers.append((group_start + cursor - 1.0) / 2.0)
        cursor += 0.8

    bars = ax.bar(x_positions, heights, color=colors, width=0.68, edgecolor="none")
    ax.set_ylim(0.0, 1.12)
    ax.set_ylabel("5-profile mean success")
    ax.set_xticks(x_positions, x_labels)
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title("Coverage and imitation depth move the task boundary", fontsize=12, fontweight="bold", pad=10)

    for center, (group_label, _) in zip(group_centers, group_specs):
        ax.text(
            center,
            -0.16,
            group_label,
            ha="center",
            va="top",
            fontsize=9,
            fontweight="bold",
            transform=ax.get_xaxis_transform(),
        )

    for bar, point in zip(bars, point_summaries):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + 0.035,
            f"{point.profile_mean_success:.2f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            min(1.02, bar.get_height() + 0.16),
            f"c={point.profile_mean_contact_steps:.1f}\nj={point.profile_mean_jam_rate:.2f}",
            ha="center",
            va="bottom",
            fontsize=7.8,
            color="#444444",
        )

    best_depth_index = point_summaries.index(summary.best_bc_optimization_depth)
    ax.annotate(
        "sweet spot",
        xy=(x_positions[best_depth_index], heights[best_depth_index]),
        xytext=(x_positions[best_depth_index] + 0.4, 0.93),
        textcoords="data",
        arrowprops={"arrowstyle": "->", "color": "#6AA84F", "linewidth": 1.2},
        fontsize=8.8,
        color="#3C7A3B",
        fontweight="bold",
    )
    ax.text(
        0.02,
        0.98,
        "demo support reopens useful contact\nreset effect is protocol-specific here",
        ha="left",
        va="top",
        fontsize=8.7,
        transform=ax.transAxes,
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": "#CCCCCC"},
    )


def _render_figure2_algorithm_budget_panel(ax, summary: Figure2CausalSummary) -> None:
    x_positions = list(range(len(summary.algorithm_budget_suites[0].points)))
    x_tick_labels = [
        str(point.factor_value) for point in summary.algorithm_budget_suites[0].points
    ]
    suite_colors = {
        "PPO-only": "#C0504D",
        "BC -> PPO": "#4F81BD",
        "DAPG-lite": "#6AA84F",
    }

    for suite in summary.algorithm_budget_suites:
        y_values = [point.profile_mean_success for point in suite.points]
        ax.plot(
            x_positions,
            y_values,
            marker="o",
            linewidth=2.1,
            markersize=5.2,
            color=suite_colors.get(suite.label, "#4F81BD"),
            label=suite.label,
        )

    ax.axhline(
        summary.bc_only_anchor.profile_mean_success,
        color="#7F6000",
        linestyle="--",
        linewidth=1.6,
        label=f"{summary.bc_only_anchor.label} anchor",
    )
    ax.set_ylim(0.0, 1.08)
    ax.set_xticks(x_positions, x_tick_labels)
    ax.set_xlabel("PPO fine-tune timesteps")
    ax.set_ylabel("5-profile mean success")
    ax.grid(color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title("Algorithm ranking is budget-sensitive, not fixed", fontsize=12, fontweight="bold", pad=10)
    ax.legend(loc="lower left", frameon=False, fontsize=8.8)

    ax.text(
        0.98,
        0.98,
        "PPO-only stays at 0.00\nBC-only anchor stays at 1.00",
        ha="right",
        va="top",
        fontsize=8.7,
        transform=ax.transAxes,
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": "#CCCCCC"},
    )

    bc_to_ppo_suite = next(
        suite for suite in summary.algorithm_budget_suites if suite.label == "BC -> PPO"
    )
    last_point = bc_to_ppo_suite.points[-1]
    ax.annotate(
        "large-budget regression",
        xy=(x_positions[-1], last_point.profile_mean_success),
        xytext=(x_positions[-1] - 1.3, 0.19),
        textcoords="data",
        arrowprops={"arrowstyle": "->", "color": "#4F81BD", "linewidth": 1.2},
        fontsize=8.8,
        color="#4F81BD",
        fontweight="bold",
    )


def _render_figure3_axial_sweep_panel(ax, summary: Figure3CriterionDecompositionSummary) -> None:
    for profile in summary.axial_profiles:
        x_values = [point.tolerance_mm for point in profile.points]
        y_values = [point.success_rate for point in profile.points]
        ax.plot(
            x_values,
            y_values,
            marker="o",
            linewidth=2.1,
            markersize=5.5,
            color=_profile_color(profile.profile_name),
            label=profile.profile_name.replace("_", " "),
        )

    ax.set_xlim(0.95, 2.05)
    ax.set_ylim(0.35, 1.02)
    ax.set_xticks([1.0, 1.2, 1.5, 2.0])
    ax.set_yticks([0.4, 0.6, 0.8, 1.0])
    ax.grid(color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel("axial settling tolerance (mm)")
    ax.set_ylabel("success rate")
    ax.set_title("Axial tolerance is the only strong residual lever", fontsize=12, fontweight="bold", pad=10)
    ax.legend(loc="lower right", frameon=False, fontsize=8.8)


def _render_figure3_failure_bucket_panel(ax, summary: Figure3CriterionDecompositionSummary) -> None:
    profiles = summary.failure_profiles
    x_positions = list(range(len(profiles)))
    axial = [profile.axial_failures for profile in profiles]
    lateral = [profile.lateral_failures for profile in profiles]
    speed = [profile.speed_failures for profile in profiles]
    mixed = [profile.mixed_failures for profile in profiles]

    ax.bar(x_positions, axial, color="#C0504D", width=0.6, edgecolor="none", label="axial-only")
    ax.bar(x_positions, lateral, bottom=axial, color="#4F81BD", width=0.6, edgecolor="none", label="lateral-only")
    bottom_speed = [a + l for a, l in zip(axial, lateral)]
    ax.bar(x_positions, speed, bottom=bottom_speed, color="#9BBB59", width=0.6, edgecolor="none", label="speed-only")
    bottom_mixed = [a + l + s for a, l, s in zip(axial, lateral, speed)]
    ax.bar(x_positions, mixed, bottom=bottom_mixed, color="#8064A2", width=0.6, edgecolor="none", label="mixed")

    ax.set_xticks(x_positions, [profile.profile_name.replace("_", "\n") for profile in profiles])
    ax.set_ylabel("number of strict-criterion failures")
    ax.set_ylim(0.0, max(axial) + 1.6)
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title("Residual failures localize to the axial-only tail", fontsize=12, fontweight="bold", pad=10)

    for idx, profile in enumerate(profiles):
        total_failures = (
            profile.axial_failures
            + profile.lateral_failures
            + profile.speed_failures
            + profile.mixed_failures
        )
        ax.text(
            idx,
            total_failures + 0.08,
            f"{profile.mean_failed_axial_mm:.2f} mm axial",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color="#C0504D",
            rotation=18,
        )
    ax.text(
        0.98,
        0.95,
        f"axial failures: {summary.total_axial_failures}\nnon-axial failures: {summary.total_non_axial_failures}",
        ha="right",
        va="top",
        fontsize=9,
        transform=ax.transAxes,
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": "#CCCCCC"},
    )
    ax.legend(loc="upper left", frameon=False, fontsize=8.8)


def _render_figurea1_per_profile_axial_band_panel(ax, summary: FigureA1PerProfileAxialBandSummary) -> None:
    tolerance_colors = {
        2.0: "#C0504D",
        3.0: "#4F81BD",
        3.5: "#9BBB59",
    }
    profiles = summary.profiles
    x_positions = list(range(len(profiles)))
    width = 0.22
    tolerance_order = [2.0, 3.0, 3.5]
    tolerance_offsets = {
        2.0: -width,
        3.0: 0.0,
        3.5: width,
    }

    for tolerance_mm in tolerance_order:
        heights = [
            next(band.success_rate for band in profile.bands if band.tolerance_mm == tolerance_mm)
            for profile in profiles
        ]
        ax.bar(
            [x + tolerance_offsets[tolerance_mm] for x in x_positions],
            heights,
            width=width,
            color=tolerance_colors[tolerance_mm],
            edgecolor="none",
            label=f"{tolerance_mm:.1f} mm",
        )

    ax.set_ylim(0.55, 1.05)
    ax.set_ylabel("success rate")
    ax.set_xticks(x_positions, [profile.profile_name.replace("_", "\n") for profile in profiles])
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title("Per-profile strict vs primary vs sanity axial bands", fontsize=12, fontweight="bold", pad=10)

    mean_text = "\n".join(
        f"{band.tolerance_mm:.1f} mm mean: {band.success_rate:.2f}"
        for band in summary.mean_bands
    )
    ax.text(
        0.98,
        0.95,
        mean_text,
        ha="right",
        va="top",
        fontsize=9,
        transform=ax.transAxes,
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": "#CCCCCC"},
    )
    ax.legend(title="axial band", loc="upper left", frameon=False, fontsize=9)


def _render_sweep_line_panel(
    ax,
    profiles: tuple[SweepProfileSummary, ...],
    title: str,
    xlabel: str,
    x_ticks: list[float],
    x_tick_labels: list[str],
    y_limits: tuple[float, float] = (0.35, 1.02),
) -> None:
    for profile in profiles:
        x_values = [point.x_value for point in profile.points]
        y_values = [point.success_rate for point in profile.points]
        ax.plot(
            x_values,
            y_values,
            marker="o",
            linewidth=2.0,
            markersize=5.0,
            color=_profile_color(profile.profile_name),
            label=profile.profile_name.replace("_", " "),
        )
    ax.set_ylim(*y_limits)
    ax.set_xticks(x_ticks, x_tick_labels)
    ax.set_yticks([0.4, 0.6, 0.8, 1.0])
    ax.grid(color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("success rate")
    ax.set_title(title, fontsize=11.5, fontweight="bold", pad=9)


def _render_figurea2_failure_inset(ax, summary: FigureA2StrictCriterionDecompositionSummary) -> None:
    inset = ax.inset_axes([0.57, 0.1, 0.38, 0.42])
    profiles = summary.failure_profiles
    x_positions = list(range(len(profiles)))
    axial = [profile.axial_failures for profile in profiles]
    lateral = [profile.lateral_failures for profile in profiles]
    speed = [profile.speed_failures for profile in profiles]
    mixed = [profile.mixed_failures for profile in profiles]

    inset.bar(x_positions, axial, color="#C0504D", width=0.58, edgecolor="none")
    inset.bar(x_positions, lateral, bottom=axial, color="#4F81BD", width=0.58, edgecolor="none")
    inset.bar(
        x_positions,
        speed,
        bottom=[a + l for a, l in zip(axial, lateral)],
        color="#9BBB59",
        width=0.58,
        edgecolor="none",
    )
    inset.bar(
        x_positions,
        mixed,
        bottom=[a + l + s for a, l, s in zip(axial, lateral, speed)],
        color="#8064A2",
        width=0.58,
        edgecolor="none",
    )
    inset.set_title("failure bucket", fontsize=8.5, pad=4)
    inset.set_xticks(x_positions, ["N", "TC", "HF", "OB", "NF"], fontsize=7)
    inset.set_yticks([0, 2, 4])
    inset.tick_params(axis="y", labelsize=7)
    inset.set_ylim(0, max(axial) + 0.8)
    inset.grid(axis="y", color="#E6E6E6", linewidth=0.6)
    inset.set_axisbelow(True)
    inset.text(
        0.98,
        0.95,
        f"axial: {summary.total_axial_failures}\nnon-axial: {summary.total_non_axial_failures}",
        ha="right",
        va="top",
        fontsize=7.2,
        transform=inset.transAxes,
        bbox={"boxstyle": "round,pad=0.18", "facecolor": "white", "edgecolor": "#CCCCCC"},
    )


def export_figure1_contact_transition_audit(
    audit_path: Path,
    output_dir: Path,
    stem: str = "fig1_contact_transition_audit",
) -> tuple[Path, Path]:
    summary = load_figure1_contact_transition_summary(Path(audit_path))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    x_max_mm = max(summary.baseline.first_jam_mm, summary.repaired.first_jam_mm) + 0.15
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8), sharex=True, sharey=True)
    _render_variant_panel(axes[0], summary.baseline, x_max_mm=x_max_mm)
    _render_variant_panel(axes[1], summary.repaired, x_max_mm=x_max_mm)
    axes[0].set_xlabel("XY error at surface contact (mm)")
    axes[1].set_xlabel("XY error at surface contact (mm)")
    axes[0].set_ylabel("audit slice")

    legend_handles = [
        Patch(facecolor="#6AA84F", edgecolor="none", label="safe-contact window"),
        Patch(facecolor="#F4CCCC", edgecolor="none", label="jam region after onset"),
        Line2D([0], [0], color="#C94F4F", linestyle="--", linewidth=1.5, label="first jam onset"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, 1.02),
    )
    fig.suptitle(
        "Nominal full-descent contact-transition audit",
        fontsize=13,
        fontweight="bold",
        y=1.08,
    )
    fig.tight_layout()

    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return pdf_path, png_path


def export_figure2_bc_coverage_repair(
    before_audit_path: Path,
    after_audit_path: Path,
    budget_sweep_path: Path,
    output_dir: Path,
    stem: str = "fig2_bc_coverage_repair",
) -> tuple[Path, Path]:
    summary = load_figure2_bc_coverage_summary(
        before_audit_path=Path(before_audit_path),
        after_audit_path=Path(after_audit_path),
        budget_sweep_path=Path(budget_sweep_path),
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.1), constrained_layout=True)
    _render_figure2_coverage_panel(axes[0], summary)
    _render_figure2_budget_panel(axes[1], summary)
    fig.suptitle(
        "BC coverage repair and reopening of hard-eval contact",
        fontsize=13,
        fontweight="bold",
    )

    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return pdf_path, png_path


def export_figure2_causal_summary(
    demonstration_coverage_path: Path,
    reset_coverage_path: Path,
    bc_optimization_depth_path: Path,
    algorithm_budget_comparison_path: Path,
    output_dir: Path,
    stem: str = "fig2_causal_factor_program",
) -> tuple[Path, Path]:
    summary = load_figure2_causal_summary(
        demonstration_coverage_path=Path(demonstration_coverage_path),
        reset_coverage_path=Path(reset_coverage_path),
        bc_optimization_depth_path=Path(bc_optimization_depth_path),
        algorithm_budget_comparison_path=Path(algorithm_budget_comparison_path),
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.5), constrained_layout=True)
    _render_figure2_causal_controls_panel(axes[0], summary)
    _render_figure2_algorithm_budget_panel(axes[1], summary)
    fig.suptitle(
        "Factorized causal program under the matched protocol",
        fontsize=13,
        fontweight="bold",
    )

    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return pdf_path, png_path


def export_figure3_criterion_decomposition_axial_tail(
    axial_sweep_path: Path,
    failure_bucket_path: Path,
    output_dir: Path,
    stem: str = "fig3_criterion_decomposition_axial_tail",
) -> tuple[Path, Path]:
    summary = load_figure3_criterion_decomposition_summary(
        axial_sweep_path=Path(axial_sweep_path),
        failure_bucket_path=Path(failure_bucket_path),
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.2), constrained_layout=True)
    _render_figure3_axial_sweep_panel(axes[0], summary)
    _render_figure3_failure_bucket_panel(axes[1], summary)
    fig.suptitle(
        "Strict criterion decomposition and axial-only residual tail",
        fontsize=13,
        fontweight="bold",
    )

    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return pdf_path, png_path


def export_figurea1_per_profile_axial_band_comparison(
    axial_tail_sweep_path: Path,
    output_dir: Path,
    stem: str = "figA1_per_profile_axial_band_comparison",
) -> tuple[Path, Path]:
    summary = load_figurea1_per_profile_axial_band_summary(
        axial_tail_sweep_path=Path(axial_tail_sweep_path),
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(1, 1, figsize=(9.2, 4.2), constrained_layout=True)
    _render_figurea1_per_profile_axial_band_panel(ax, summary)
    fig.suptitle(
        "Per-profile success across strict, primary, and sanity axial bands",
        fontsize=13,
        fontweight="bold",
    )

    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return pdf_path, png_path


def export_figurea2_strict_criterion_decomposition(
    success_tolerance_path: Path,
    axial_sweep_path: Path,
    speed_sweep_path: Path,
    lateral_sweep_path: Path,
    failure_bucket_path: Path,
    output_dir: Path,
    stem: str = "figA2_strict_criterion_decomposition",
) -> tuple[Path, Path]:
    summary = load_figurea2_strict_criterion_decomposition_summary(
        success_tolerance_path=Path(success_tolerance_path),
        axial_sweep_path=Path(axial_sweep_path),
        speed_sweep_path=Path(speed_sweep_path),
        lateral_sweep_path=Path(lateral_sweep_path),
        failure_bucket_path=Path(failure_bucket_path),
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(11.2, 8.0), constrained_layout=True)
    _render_sweep_line_panel(
        axes[0, 0],
        summary.old_lateral_profiles,
        title="Old lateral sweep under the older strict axial gate",
        xlabel="lateral tolerance (mm)",
        x_ticks=[0.8, 1.0, 1.2, 1.5],
        x_tick_labels=["0.8", "1.0", "1.2", "1.5"],
        y_limits=(0.35, 0.86),
    )
    _render_figure3_axial_sweep_panel(axes[0, 1], summary)
    _render_sweep_line_panel(
        axes[1, 0],
        summary.speed_profiles,
        title="Speed sweep at axial = 2.0 mm",
        xlabel="speed threshold (m/s)",
        x_ticks=[0.08, 0.10, 0.12, 0.15, 0.20],
        x_tick_labels=["0.08", "0.10", "0.12", "0.15", "0.20"],
    )
    _render_sweep_line_panel(
        axes[1, 1],
        summary.strict_lateral_profiles,
        title="Lateral sweep at axial = 2.0 mm",
        xlabel="lateral tolerance (mm)",
        x_ticks=[0.8, 1.0, 1.2, 1.5],
        x_tick_labels=["0.8", "1.0", "1.2", "1.5"],
    )
    _render_figurea2_failure_inset(axes[1, 1], summary)
    axes[0, 0].legend(loc="lower right", frameon=False, fontsize=8)
    axes[0, 1].legend(loc="lower right", frameon=False, fontsize=8)

    fig.suptitle(
        "Strict appendix decomposition of the remaining axial-only gap",
        fontsize=13,
        fontweight="bold",
    )

    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return pdf_path, png_path


def _save_figure_bundle(fig, *, output_dir: Path, stem: str) -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{stem}.pdf"
    png_path = output_dir / f"{stem}.png"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return pdf_path, png_path


def export_figure1_task_policy_impedance_overview(
    output_dir: Path,
    stem: str = "fig1_task_policy_impedance_overview",
) -> tuple[Path, Path]:
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.8), constrained_layout=True)

    observation_blocks = [
        ("relative\nposition", "#D9E2F3"),
        ("relative\nvelocity", "#E2F0D9"),
        ("force\nsignal", "#FCE4D6"),
        ("previous\naction", "#FFF2CC"),
    ]
    y_start = 0.82
    for index, (label, color) in enumerate(observation_blocks):
        y_value = y_start - index * 0.18
        axes[0].add_patch(
            Rectangle((0.12, y_value - 0.08), 0.76, 0.12, facecolor=color, edgecolor="#666666")
        )
        axes[0].text(0.5, y_value - 0.02, label, ha="center", va="center", fontsize=10)
    axes[0].text(
        0.5,
        0.94,
        "Observation stack",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
    )
    axes[0].text(
        0.5,
        0.08,
        "Hole-centered relative frame:\nstate stays structured, not image-based.",
        ha="center",
        va="center",
        fontsize=9,
    )
    axes[0].set_axis_off()

    action_names = [r"$\Delta x$", r"$\Delta y$", r"$\Delta z$", r"$K_{xy}$", r"$K_z$"]
    action_values = [1.0, 1.0, 1.0, 0.78, 0.92]
    action_colors = ["#4F81BD", "#4F81BD", "#4F81BD", "#C0504D", "#9BBB59"]
    axes[1].bar(range(len(action_names)), action_values, color=action_colors, width=0.6)
    axes[1].set_ylim(0.0, 1.15)
    axes[1].set_xticks(range(len(action_names)), action_names)
    axes[1].set_yticks([0.0, 0.5, 1.0])
    axes[1].set_ylabel("normalized command")
    axes[1].set_title("Structured 5D action", fontsize=12, fontweight="bold", pad=10)
    axes[1].grid(axis="y", color="#DDDDDD", linewidth=0.8)
    axes[1].set_axisbelow(True)
    axes[1].text(
        0.5,
        1.08,
        "Motion and compliance stay explicit.",
        ha="center",
        va="bottom",
        fontsize=9,
        transform=axes[1].transAxes,
    )

    contact_phase = [0.0, 0.3, 0.55, 0.8, 1.0]
    fixed_schedule = [0.78, 0.78, 0.78, 0.78, 0.78]
    variable_schedule = [0.78, 0.78, 0.42, 0.34, 0.30]
    axial_schedule = [0.92, 0.92, 0.76, 0.68, 0.64]
    axes[2].plot(contact_phase, fixed_schedule, color="#C0504D", linewidth=2.2, label="fixed $K_{xy}$")
    axes[2].plot(contact_phase, variable_schedule, color="#4F81BD", linewidth=2.2, label="variable $K_{xy}$")
    axes[2].plot(contact_phase, axial_schedule, color="#9BBB59", linewidth=2.2, linestyle="--", label="variable $K_z$")
    axes[2].set_xlim(0.0, 1.0)
    axes[2].set_ylim(0.2, 1.05)
    axes[2].set_xticks([0.0, 0.3, 0.55, 0.8, 1.0], ["approach", "", "contact", "", "settle"])
    axes[2].set_ylabel("normalized stiffness")
    axes[2].set_title("Impedance meaning", fontsize=12, fontweight="bold", pad=10)
    axes[2].grid(color="#DDDDDD", linewidth=0.8)
    axes[2].set_axisbelow(True)
    axes[2].legend(loc="lower left", frameon=False, fontsize=8.8)

    fig.suptitle(
        "Task, policy, and impedance overview",
        fontsize=13,
        fontweight="bold",
    )
    return _save_figure_bundle(fig, output_dir=output_dir, stem=stem)


def export_figure2_main_benchmark_pressure_class_summary(
    benchmark_report_path: Path,
    statistics_report_path: Path | None,
    output_dir: Path,
    stem: str = "fig2_main_benchmark_evaluation_class_summary",
) -> tuple[Path, Path]:
    from vi_full.paper_tables import build_3dof_paper_table_export

    export_payload = build_3dof_paper_table_export(
        benchmark_report_path=Path(benchmark_report_path),
        statistics_report_path=(
            Path(statistics_report_path) if statistics_report_path is not None else None
        ),
    )
    main_suite_order = [
        "ppo_no_bc",
        "bc_only_stable_r32_p32",
        "fixed_impedance_rl_stable_r32_p32",
        "repaired_mainline_bc_to_ppo",
        "dapg_lite_repaired_mainline",
    ]
    suite_rows = [
        row
        for suite_name in main_suite_order
        for row in export_payload["suite_rows"]
        if row["suite_name"] == suite_name
    ]
    class_names = ["baseline", "high_friction", "noisy_force"]
    matrix = np.asarray(
        [
            [
                float(row["effective_pressure_classes"][class_name]["metrics"]["success_rate"])
                for class_name in class_names
            ]
            + [float(row["five_profile_mean"]["success_rate"])]
            for row in suite_rows
        ],
        dtype=np.float64,
    )
    column_labels = ["baseline", "high friction", "noisy force", "5-profile mean"]
    row_labels = [row["display_name"] for row in suite_rows]

    fig, ax = plt.subplots(1, 1, figsize=(8.8, 4.8), constrained_layout=True)
    heatmap = ax.imshow(matrix, vmin=0.0, vmax=1.0, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(range(len(column_labels)), column_labels, rotation=18, ha="right")
    ax.set_yticks(range(len(row_labels)), row_labels)
    ax.set_title("Success by evaluation class", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("evaluation class")
    ax.set_ylabel("method")
    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            value = matrix[row_index, col_index]
            ax.text(
                col_index,
                row_index,
                f"{value:.3f}",
                ha="center",
                va="center",
                fontsize=8.8,
                color="#0F243E" if value < 0.72 else "white",
                fontweight="bold",
            )
    colorbar = fig.colorbar(heatmap, ax=ax, fraction=0.046, pad=0.04)
    colorbar.set_label("success rate")
    return _save_figure_bundle(fig, output_dir=output_dir, stem=stem)


def export_figurea1_pressure_class_mapping(
    output_dir: Path,
    stem: str = "figA1_evaluation_class_mapping",
) -> tuple[Path, Path]:
    fig, ax = plt.subplots(1, 1, figsize=(9.6, 4.4), constrained_layout=True)
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_axis_off()

    class_boxes = [
        ("baseline", 0.12, "#D9E2F3"),
        ("high friction", 0.42, "#FCE4D6"),
        ("noisy force", 0.72, "#E2F0D9"),
    ]
    for label, x_pos, color in class_boxes:
        ax.add_patch(
            Rectangle((x_pos, 0.62), 0.18, 0.16, facecolor=color, edgecolor="#666666")
        )
        ax.text(x_pos + 0.09, 0.70, label, ha="center", va="center", fontsize=10, fontweight="bold")

    profile_labels = [
        ("nominal", 0.06, 0.18),
        ("tight_clearance", 0.22, 0.18),
        ("offset_bias", 0.38, 0.18),
        ("high_friction", 0.58, 0.18),
        ("noisy_force", 0.78, 0.18),
    ]
    for label, x_pos, y_pos in profile_labels:
        ax.add_patch(
            Rectangle((x_pos, y_pos), 0.14, 0.12, facecolor="#FFFFFF", edgecolor="#666666")
        )
        ax.text(x_pos + 0.07, y_pos + 0.06, label.replace("_", "\n"), ha="center", va="center", fontsize=9)

    arrow_targets = {
        "nominal": (0.21, 0.62),
        "tight_clearance": (0.21, 0.62),
        "offset_bias": (0.21, 0.62),
        "high_friction": (0.51, 0.62),
        "noisy_force": (0.81, 0.62),
    }
    for label, x_pos, y_pos in profile_labels:
        target_x, target_y = arrow_targets[label]
        ax.annotate(
            "",
            xy=(target_x, target_y),
            xytext=(x_pos + 0.07, y_pos + 0.12),
            arrowprops={"arrowstyle": "->", "linewidth": 1.4, "color": "#666666"},
        )

    ax.text(
        0.5,
        0.92,
        "Five nominal profiles collapse into three evaluation classes",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
    )
    ax.text(
        0.5,
        0.05,
        "Relative-frame semantics attenuate offset bias; high friction and force noise remain distinct.",
        ha="center",
        va="center",
        fontsize=9.5,
    )
    return _save_figure_bundle(fig, output_dir=output_dir, stem=stem)


def export_figurea3_teacher_ablation_summary(
    benchmark_report_path: Path,
    output_dir: Path,
    fixed_impedance_report_path: Path | None = None,
    stem: str = "figA3_teacher_ablation_summary",
) -> tuple[Path, Path]:
    summary = load_figurea3_teacher_ablation_summary(
        benchmark_report_path=benchmark_report_path,
        fixed_impedance_report_path=fixed_impedance_report_path,
    )
    x_positions = np.arange(len(summary.suites), dtype=np.float64)
    tick_labels = []
    success_rates = []
    peak_forces = []
    final_distances = []
    colors = []
    hatches = []
    for suite in summary.suites:
        tick_labels.append(
            "var/var"
            if suite.teacher_motion_rule == "contact_aware_variable_motion"
            and suite.teacher_impedance_rule == "contact_aware_variable_impedance"
            else "var/fixed"
            if suite.teacher_motion_rule == "contact_aware_variable_motion"
            else "pose/var"
            if suite.teacher_impedance_rule == "contact_aware_variable_impedance"
            else "pose/fixed"
        )
        success_rates.append(suite.five_profile_success_rate)
        peak_forces.append(suite.mean_peak_contact_force_n)
        final_distances.append(suite.mean_final_distance_mm)
        colors.append(
            "#4F81BD"
            if suite.teacher_motion_rule == "contact_aware_variable_motion"
            else "#C0504D"
        )
        hatches.append("//" if suite.teacher_impedance_rule == "fixed" else "")

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6), constrained_layout=True)
    success_bars = axes[0].bar(
        x_positions,
        success_rates,
        color=colors,
        edgecolor="#333333",
        linewidth=1.0,
    )
    for bar, hatch, value in zip(success_bars, hatches, success_rates, strict=True):
        bar.set_hatch(hatch)
        axes[0].text(
            bar.get_x() + bar.get_width() / 2.0,
            value + 0.015,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=8.8,
        )
    axes[0].set_xticks(x_positions, tick_labels)
    axes[0].set_ylim(0.0, 1.08)
    axes[0].set_ylabel("5-profile mean success rate")
    axes[0].set_title("Teacher 2x2 success summary", fontsize=12, fontweight="bold")
    axes[0].grid(axis="y", color="#DDDDDD", linewidth=0.8)
    axes[0].set_axisbelow(True)

    force_bars = axes[1].bar(
        x_positions,
        peak_forces,
        color=colors,
        edgecolor="#333333",
        linewidth=1.0,
        alpha=0.9,
    )
    for bar, hatch in zip(force_bars, hatches, strict=True):
        bar.set_hatch(hatch)
    axes[1].set_xticks(x_positions, tick_labels)
    axes[1].set_ylabel("mean peak contact force (N)")
    axes[1].set_title("Force and final-distance readout", fontsize=12, fontweight="bold")
    axes[1].grid(axis="y", color="#DDDDDD", linewidth=0.8)
    axes[1].set_axisbelow(True)
    distance_axis = axes[1].twinx()
    distance_axis.plot(
        x_positions,
        final_distances,
        color="#6A3D9A",
        marker="o",
        linewidth=2.0,
        label="mean final distance (mm)",
    )
    distance_axis.set_ylabel("mean final distance (mm)", color="#6A3D9A")
    distance_axis.tick_params(axis="y", colors="#6A3D9A")

    legend_handles = [
        Patch(facecolor="#4F81BD", edgecolor="#333333", label="motion: contact-aware"),
        Patch(facecolor="#C0504D", edgecolor="#333333", label="motion: pose feedback"),
        Patch(facecolor="white", edgecolor="#333333", hatch="", label="impedance: variable"),
        Patch(facecolor="white", edgecolor="#333333", hatch="//", label="impedance: fixed"),
        Line2D(
            [0],
            [0],
            color="#6A3D9A",
            marker="o",
            linewidth=2.0,
            label="final distance",
        ),
    ]
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.03),
        ncol=3,
        frameon=False,
        fontsize=8.8,
    )
    fig.suptitle(
        "Appendix teacher ablation: motion x impedance",
        fontsize=13,
        fontweight="bold",
    )
    return _save_figure_bundle(fig, output_dir=output_dir, stem=stem)


def export_figurea4_termination_diagnostics_summary(
    benchmark_report_path: Path,
    output_dir: Path,
    fixed_impedance_report_path: Path | None = None,
    stem: str = "figA4_termination_diagnostics_summary",
) -> tuple[Path, Path]:
    summary = load_figurea4_termination_diagnostics_summary(
        benchmark_report_path=benchmark_report_path,
        fixed_impedance_report_path=fixed_impedance_report_path,
    )
    x_positions = np.arange(len(summary.suites), dtype=np.float64)
    tick_labels = [suite.display_name for suite in summary.suites]
    force_only = np.asarray(
        [suite.force_threshold_only_termination_rate for suite in summary.suites],
        dtype=np.float64,
    )
    blocked_only = np.asarray(
        [suite.blocked_contact_only_termination_rate for suite in summary.suites],
        dtype=np.float64,
    )
    force_and_blocked = np.asarray(
        [suite.force_and_blocked_termination_rate for suite in summary.suites],
        dtype=np.float64,
    )
    jam_rates = np.asarray([suite.jam_rate for suite in summary.suites], dtype=np.float64)
    documented_rates = np.asarray(
        [suite.documented_force_jam_rate for suite in summary.suites],
        dtype=np.float64,
    )

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8), constrained_layout=True)
    axes[0].bar(x_positions, force_only, color="#F4A259", label="force only")
    axes[0].bar(
        x_positions,
        blocked_only,
        bottom=force_only,
        color="#5B8E7D",
        label="blocked only",
    )
    axes[0].bar(
        x_positions,
        force_and_blocked,
        bottom=force_only + blocked_only,
        color="#8C5E58",
        label="force + blocked",
    )
    axes[0].set_xticks(x_positions, tick_labels, rotation=18, ha="right")
    axes[0].set_ylabel("termination rate")
    axes[0].set_title("Termination attribution split", fontsize=12, fontweight="bold")
    axes[0].grid(axis="y", color="#DDDDDD", linewidth=0.8)
    axes[0].set_axisbelow(True)
    axes[0].legend(frameon=False, fontsize=8.8)

    jam_bars = axes[1].bar(
        x_positions,
        jam_rates,
        color="#AAB7C4",
        edgecolor="#333333",
        label="jam_rate",
    )
    axes[1].plot(
        x_positions,
        documented_rates,
        color="#C0504D",
        marker="o",
        linewidth=2.0,
        label="documented_force_jam_rate",
    )
    for bar, value in zip(jam_bars, jam_rates, strict=True):
        axes[1].text(
            bar.get_x() + bar.get_width() / 2.0,
            value + 0.01,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=8.6,
        )
    axes[1].set_xticks(x_positions, tick_labels, rotation=18, ha="right")
    axes[1].set_ylabel("rate")
    axes[1].set_title("Jam vs documented 3-step force jam", fontsize=12, fontweight="bold")
    axes[1].grid(axis="y", color="#DDDDDD", linewidth=0.8)
    axes[1].set_axisbelow(True)
    axes[1].legend(frameon=False, fontsize=8.8)

    fig.suptitle(
        "Appendix termination diagnostics across learned suites",
        fontsize=13,
        fontweight="bold",
    )
    return _save_figure_bundle(fig, output_dir=output_dir, stem=stem)
