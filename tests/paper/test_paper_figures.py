import importlib.util
import json
from pathlib import Path
import sys

import pytest


def _require_test_asset(path: Path, description: str) -> Path:
    if not path.exists():
        pytest.skip(f"missing {description}: {path}")
    return path

def _contact_audit_artifact_path() -> Path:
    return _require_test_asset(
        (
        Path(__file__).resolve().parents[2]
        / "outputs"
        / "latest_three_dof_contact_model_audit.json"
        ),
        "contact audit artifact",
    )


def _phase2_demo_coverage_artifact_path() -> Path:
    return _require_test_asset(
        (
        Path(__file__).resolve().parents[2]
        / "outputs"
        / "three_dof_factor_sweep_demonstration_coverage_20260411_172516.json"
        ),
        "phase2 demonstration coverage artifact",
    )


def _phase2_reset_coverage_artifact_path() -> Path:
    return _require_test_asset(
        (
        Path(__file__).resolve().parents[2]
        / "outputs"
        / "three_dof_factor_sweep_reset_coverage_20260411_172635.json"
        ),
        "phase2 reset coverage artifact",
    )


def _phase2_bc_optimization_depth_artifact_path() -> Path:
    return _require_test_asset(
        (
        Path(__file__).resolve().parents[2]
        / "outputs"
        / "three_dof_factor_sweep_bc_optimization_depth_20260411_172923.json"
        ),
        "phase2 BC optimization artifact",
    )


def _phase2_algorithm_budget_artifact_path() -> Path:
    return _require_test_asset(
        (
        Path(__file__).resolve().parents[2]
        / "outputs"
        / "three_dof_algorithm_budget_comparison_20260411_175606.json"
        ),
        "phase2 algorithm budget artifact",
    )


def _stage4_benchmark_artifact_path() -> Path:
    return _require_test_asset(
        (
        Path(__file__).resolve().parents[2]
        / "artifacts"
        / "main_benchmark"
        / "three_dof_benchmark_paper9suite_full5profile_bc32x32_stage4_20260429.json"
        ),
        "stage4 benchmark artifact",
    )


def _stage4_statistics_artifact_path() -> Path:
    return _require_test_asset(
        (
        Path(__file__).resolve().parents[2]
        / "artifacts"
        / "main_benchmark"
        / "three_dof_statistics_report_stage4_20260429.json"
        ),
        "stage4 statistics artifact",
    )


def _paper_manifest_path() -> Path:
    primary_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "paper_only_sim_figure_asset_manifest.md"
    )
    if primary_path.exists():
        return primary_path
    fallback_path = primary_path.with_name("figure_asset_manifest.md")
    return _require_test_asset(fallback_path, "paper figure asset manifest")


def _paper_manuscript_path() -> Path:
    return _require_test_asset(
        (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "paper_manuscript_only_sim_final.tex"
        ),
        "paper manuscript asset",
    )


def _axial_tolerance_sweep_artifact_path() -> Path:
    return _require_test_asset(
        (
        Path(__file__).resolve().parents[2]
        / "outputs"
        / "latest_three_dof_axial_tolerance_sweep_seed012.json"
        ),
        "axial tolerance sweep artifact",
    )


def _failure_bucket_artifact_path() -> Path:
    return _require_test_asset(
        (
        Path(__file__).resolve().parents[2]
        / "outputs"
        / "latest_three_dof_failure_bucket_axial2p0_lateral1p5_seed012.json"
        ),
        "failure bucket artifact",
    )


def _axial_tail_sweep_artifact_path() -> Path:
    return _require_test_asset(
        (
        Path(__file__).resolve().parents[2]
        / "outputs"
        / "latest_three_dof_axial_tail_sweep_lateral1p5_seed012.json"
        ),
        "axial tail sweep artifact",
    )


def _success_tolerance_sweep_artifact_path() -> Path:
    return _require_test_asset(
        (
        Path(__file__).resolve().parents[2]
        / "outputs"
        / "latest_three_dof_success_tolerance_sweep_seed012.json"
        ),
        "success tolerance sweep artifact",
    )


def _speed_tolerance_sweep_artifact_path() -> Path:
    return _require_test_asset(
        (
        Path(__file__).resolve().parents[2]
        / "outputs"
        / "latest_three_dof_speed_tolerance_sweep_axial2p0_seed012.json"
        ),
        "speed tolerance sweep artifact",
    )


def _lateral_tolerance_sweep_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "outputs"
        / "latest_three_dof_lateral_tolerance_sweep_axial2p0_seed012.json"
    )


def _load_paper_figures_module():
    module_path = (
        Path(__file__).resolve().parents[2] / "src" / "vi_full" / "paper_figures.py"
    )
    spec = importlib.util.spec_from_file_location("paper_figures_under_test", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _appendix_suite_payload(
    suite_name: str,
    *,
    success_rate: float,
    jam_rate: float,
    final_distance_m: float,
    peak_force_n: float,
    contact_steps: float,
    teacher_motion_rule: str | None = None,
    teacher_impedance_rule: str | None = None,
    diagnostic_rates: dict[str, float] | None = None,
) -> dict[str, object]:
    profiles = ("nominal", "tight_clearance", "high_friction", "offset_bias", "noisy_force")
    eval_results: dict[str, dict[str, object]] = {}
    diagnostics = {
        "jam_rate": jam_rate,
        "force_threshold_termination_rate": 0.0,
        "blocked_contact_termination_rate": 0.0,
        "force_threshold_only_termination_rate": 0.0,
        "blocked_contact_only_termination_rate": 0.0,
        "force_and_blocked_termination_rate": 0.0,
        "documented_force_jam_rate": 0.0,
    }
    diagnostics.update(diagnostic_rates or {})
    for profile_name in profiles:
        aggregate = {
            "policy_name": "PPO",
            "uncertainty_profile": profile_name,
            "num_seeds": 3,
            "seeds": [0, 1, 2],
            "suite_name": suite_name,
            "success_rate_mean": success_rate,
            "success_rate_std": 0.0,
            "jam_rate_mean": jam_rate,
            "jam_rate_std": 0.0,
            "mean_final_distance_mean": final_distance_m,
            "mean_final_distance_std": 0.0,
            "mean_peak_contact_force_mean": peak_force_n,
            "mean_peak_contact_force_std": 0.0,
            "mean_contact_steps_mean": contact_steps,
            "mean_contact_steps_std": 0.0,
        }
        for metric_name, metric_value in diagnostics.items():
            aggregate[f"{metric_name}_mean"] = float(metric_value)
            aggregate[f"{metric_name}_std"] = 0.0
        eval_results[profile_name] = {"aggregate": aggregate}

    payload: dict[str, object] = {
        "suite_run_kwargs": {"suite_name": suite_name},
        "train_configs": [],
        "training_summaries": [],
        "eval_results": eval_results,
        "five_profile_mean": {
            "success_rate_mean_over_profiles": success_rate,
            "success_rate_std_over_profiles": 0.0,
            "jam_rate_mean_over_profiles": jam_rate,
            "jam_rate_std_over_profiles": 0.0,
            "mean_final_distance_mean_over_profiles": final_distance_m,
            "mean_final_distance_std_over_profiles": 0.0,
            "mean_peak_contact_force_mean_over_profiles": peak_force_n,
            "mean_peak_contact_force_std_over_profiles": 0.0,
            "mean_contact_steps_mean_over_profiles": contact_steps,
            "mean_contact_steps_std_over_profiles": 0.0,
            "p95_peak_contact_force_mean_over_profiles": peak_force_n + 0.25,
            "p95_peak_contact_force_std_over_profiles": 0.0,
        },
    }
    for metric_name, metric_value in diagnostics.items():
        payload["five_profile_mean"][f"{metric_name}_mean_over_profiles"] = float(metric_value)
        payload["five_profile_mean"][f"{metric_name}_std_over_profiles"] = 0.0

    if teacher_motion_rule is not None:
        payload["teacher_motion_rule"] = teacher_motion_rule
    if teacher_impedance_rule is not None:
        payload["teacher_impedance_rule"] = teacher_impedance_rule
    return payload


def _write_appendix_figure_sample_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    benchmark_report = {
        "config": {
            "suite_names": [
                "bc_only_stable_r32_p32",
                "fixed_impedance_rl",
                "repaired_mainline_bc_to_ppo",
                "dapg_lite_repaired_mainline",
                "teacher_variable_variable__repaired_mainline",
                "teacher_variable_fixed__repaired_mainline",
                "teacher_pose_variable__repaired_mainline",
                "teacher_pose_fixed__repaired_mainline",
            ],
            "uncertainty_profiles": [
                "nominal",
                "tight_clearance",
                "high_friction",
                "offset_bias",
                "noisy_force",
            ],
        },
        "handcrafted_results": {},
        "learned_results": {
            "bc_only_stable_r32_p32": _appendix_suite_payload(
                "bc_only_stable_r32_p32",
                success_rate=1.0,
                jam_rate=0.0,
                final_distance_m=0.0009,
                peak_force_n=1.0,
                contact_steps=31.0,
            ),
            "fixed_impedance_rl": _appendix_suite_payload(
                "fixed_impedance_rl",
                success_rate=0.35,
                jam_rate=0.30,
                final_distance_m=0.0022,
                peak_force_n=1.60,
                contact_steps=41.0,
                diagnostic_rates={
                    "force_threshold_termination_rate": 0.12,
                    "blocked_contact_termination_rate": 0.20,
                    "force_threshold_only_termination_rate": 0.07,
                    "blocked_contact_only_termination_rate": 0.15,
                    "force_and_blocked_termination_rate": 0.05,
                    "documented_force_jam_rate": 0.04,
                },
            ),
            "repaired_mainline_bc_to_ppo": _appendix_suite_payload(
                "repaired_mainline_bc_to_ppo",
                success_rate=0.98,
                jam_rate=0.02,
                final_distance_m=0.0010,
                peak_force_n=0.98,
                contact_steps=30.0,
                diagnostic_rates={
                    "force_threshold_termination_rate": 0.01,
                    "blocked_contact_termination_rate": 0.01,
                    "force_threshold_only_termination_rate": 0.01,
                    "blocked_contact_only_termination_rate": 0.00,
                    "force_and_blocked_termination_rate": 0.01,
                    "documented_force_jam_rate": 0.01,
                },
            ),
            "dapg_lite_repaired_mainline": _appendix_suite_payload(
                "dapg_lite_repaired_mainline",
                success_rate=0.97,
                jam_rate=0.03,
                final_distance_m=0.0011,
                peak_force_n=1.02,
                contact_steps=31.0,
                diagnostic_rates={
                    "force_threshold_termination_rate": 0.01,
                    "blocked_contact_termination_rate": 0.02,
                    "force_threshold_only_termination_rate": 0.01,
                    "blocked_contact_only_termination_rate": 0.01,
                    "force_and_blocked_termination_rate": 0.01,
                    "documented_force_jam_rate": 0.01,
                },
            ),
            "teacher_variable_variable__repaired_mainline": _appendix_suite_payload(
                "teacher_variable_variable__repaired_mainline",
                success_rate=0.99,
                jam_rate=0.01,
                final_distance_m=0.0009,
                peak_force_n=0.95,
                contact_steps=30.0,
                teacher_motion_rule="contact_aware_variable_motion",
                teacher_impedance_rule="contact_aware_variable_impedance",
            ),
            "teacher_variable_fixed__repaired_mainline": _appendix_suite_payload(
                "teacher_variable_fixed__repaired_mainline",
                success_rate=0.94,
                jam_rate=0.03,
                final_distance_m=0.0012,
                peak_force_n=1.08,
                contact_steps=32.0,
                teacher_motion_rule="contact_aware_variable_motion",
                teacher_impedance_rule="fixed",
            ),
            "teacher_pose_variable__repaired_mainline": _appendix_suite_payload(
                "teacher_pose_variable__repaired_mainline",
                success_rate=0.92,
                jam_rate=0.05,
                final_distance_m=0.0015,
                peak_force_n=1.15,
                contact_steps=35.0,
                teacher_motion_rule="pose_feedback",
                teacher_impedance_rule="contact_aware_variable_impedance",
            ),
            "teacher_pose_fixed__repaired_mainline": _appendix_suite_payload(
                "teacher_pose_fixed__repaired_mainline",
                success_rate=0.88,
                jam_rate=0.09,
                final_distance_m=0.0018,
                peak_force_n=1.28,
                contact_steps=38.0,
                teacher_motion_rule="pose_feedback",
                teacher_impedance_rule="fixed",
            ),
        },
    }
    fixed_override = {
        "config": {"suite_name": "fixed_impedance_rl_stable_r32_p32"},
        **_appendix_suite_payload(
            "fixed_impedance_rl_stable_r32_p32",
            success_rate=0.91,
            jam_rate=0.08,
            final_distance_m=0.0014,
            peak_force_n=1.32,
            contact_steps=37.0,
            diagnostic_rates={
                "force_threshold_termination_rate": 0.03,
                "blocked_contact_termination_rate": 0.06,
                "force_threshold_only_termination_rate": 0.02,
                "blocked_contact_only_termination_rate": 0.05,
                "force_and_blocked_termination_rate": 0.01,
                "documented_force_jam_rate": 0.02,
            },
        ),
    }
    benchmark_path = tmp_path / "appendix_benchmark.json"
    fixed_override_path = tmp_path / "appendix_fixed_override.json"
    benchmark_path.write_text(json.dumps(benchmark_report), encoding="utf-8")
    fixed_override_path.write_text(json.dumps(fixed_override), encoding="utf-8")
    return benchmark_path, fixed_override_path


def test_load_figure1_contact_transition_summary_uses_paper_facing_variants() -> None:
    module = _load_paper_figures_module()
    summary = module.load_figure1_contact_transition_summary(_contact_audit_artifact_path())

    assert summary.baseline.variant_name == "baseline"
    assert summary.repaired.variant_name == "transition_band_1mm_stiffness_aware_probe"
    assert summary.baseline.safe_window_mm == pytest.approx(0.85)
    assert summary.repaired.safe_window_mm == pytest.approx(1.25)
    assert summary.baseline.first_jam_mm == pytest.approx(0.9)
    assert summary.repaired.first_jam_mm == pytest.approx(1.3)


def test_export_figure1_contact_transition_audit_writes_pdf_and_png(
    tmp_path: Path,
) -> None:
    module = _load_paper_figures_module()
    pdf_path, png_path = module.export_figure1_contact_transition_audit(
        _contact_audit_artifact_path(),
        tmp_path,
    )

    assert pdf_path.name == "fig1_contact_transition_audit.pdf"
    assert png_path.name == "fig1_contact_transition_audit.png"
    assert pdf_path.exists()
    assert png_path.exists()
    assert pdf_path.stat().st_size > 0
    assert png_path.stat().st_size > 0


def test_export_figure1_task_policy_impedance_overview_writes_pdf_and_png(
    tmp_path: Path,
) -> None:
    module = _load_paper_figures_module()
    pdf_path, png_path = module.export_figure1_task_policy_impedance_overview(tmp_path)

    assert pdf_path.name == "fig1_task_policy_impedance_overview.pdf"
    assert png_path.name == "fig1_task_policy_impedance_overview.png"
    assert pdf_path.exists()
    assert png_path.exists()
    assert pdf_path.stat().st_size > 0
    assert png_path.stat().st_size > 0


def test_load_figure2_causal_summary_uses_phase2_factorized_artifacts() -> None:
    module = _load_paper_figures_module()
    summary = module.load_figure2_causal_summary(
        demonstration_coverage_path=_phase2_demo_coverage_artifact_path(),
        reset_coverage_path=_phase2_reset_coverage_artifact_path(),
        bc_optimization_depth_path=_phase2_bc_optimization_depth_artifact_path(),
        algorithm_budget_comparison_path=_phase2_algorithm_budget_artifact_path(),
    )

    assert [point.point_name for point in summary.demonstration_coverage] == [
        "reset_coverage_collapse",
        "reset_repaired",
    ]
    assert summary.demonstration_coverage[0].profile_mean_success == pytest.approx(0.0)
    assert summary.demonstration_coverage[0].profile_mean_contact_steps == pytest.approx(15.8706666667)
    assert summary.demonstration_coverage[1].profile_mean_success == pytest.approx(0.5653333333)

    assert [point.point_name for point in summary.reset_coverage] == [
        "reset_coverage_collapse",
        "reset_repaired",
    ]
    assert summary.reset_coverage[0].profile_mean_success == pytest.approx(1.0)
    assert summary.reset_coverage[1].profile_mean_success == pytest.approx(0.5653333333)

    assert [point.factor_value for point in summary.bc_optimization_depth] == [0, 8, 32, 64]
    assert summary.best_bc_optimization_depth.factor_value == 32
    assert summary.best_bc_optimization_depth.profile_mean_success == pytest.approx(0.5653333333)

    assert [suite.label for suite in summary.algorithm_budget_suites] == [
        "PPO-only",
        "BC -> PPO",
        "DAPG-lite",
    ]
    assert summary.algorithm_budget_suites[0].points[-1].profile_mean_success == pytest.approx(0.0)
    assert summary.algorithm_budget_suites[1].points[-1].profile_mean_success == pytest.approx(0.012)
    assert summary.algorithm_budget_suites[2].points[1].profile_mean_success == pytest.approx(0.0613333333)
    assert summary.bc_only_anchor.label == "BC-only"
    assert summary.bc_only_anchor.profile_mean_success == pytest.approx(1.0)


def test_export_figure2_causal_summary_writes_pdf_and_png(
    tmp_path: Path,
) -> None:
    module = _load_paper_figures_module()
    pdf_path, png_path = module.export_figure2_causal_summary(
        demonstration_coverage_path=_phase2_demo_coverage_artifact_path(),
        reset_coverage_path=_phase2_reset_coverage_artifact_path(),
        bc_optimization_depth_path=_phase2_bc_optimization_depth_artifact_path(),
        algorithm_budget_comparison_path=_phase2_algorithm_budget_artifact_path(),
        output_dir=tmp_path,
    )

    assert pdf_path.name == "fig2_causal_factor_program.pdf"
    assert png_path.name == "fig2_causal_factor_program.png"
    assert pdf_path.exists()
    assert png_path.exists()
    assert pdf_path.stat().st_size > 0
    assert png_path.stat().st_size > 0


def test_export_figure2_main_benchmark_evaluation_class_summary_writes_pdf_and_png(
    tmp_path: Path,
) -> None:
    module = _load_paper_figures_module()
    pdf_path, png_path = module.export_figure2_main_benchmark_pressure_class_summary(
        benchmark_report_path=_stage4_benchmark_artifact_path(),
        statistics_report_path=_stage4_statistics_artifact_path(),
        output_dir=tmp_path,
    )

    assert pdf_path.name == "fig2_main_benchmark_evaluation_class_summary.pdf"
    assert png_path.name == "fig2_main_benchmark_evaluation_class_summary.png"
    assert pdf_path.exists()
    assert png_path.exists()
    assert pdf_path.stat().st_size > 0
    assert png_path.stat().st_size > 0


def test_load_figure3_criterion_decomposition_summary_uses_axial_only_tail() -> None:
    module = _load_paper_figures_module()
    summary = module.load_figure3_criterion_decomposition_summary(
        axial_sweep_path=_axial_tolerance_sweep_artifact_path(),
        failure_bucket_path=_failure_bucket_artifact_path(),
    )

    assert [profile.profile_name for profile in summary.axial_profiles] == [
        "nominal",
        "tight_clearance",
        "high_friction",
        "offset_bias",
        "noisy_force",
    ]
    assert [point.tolerance_mm for point in summary.axial_profiles[0].points] == [
        pytest.approx(1.0),
        pytest.approx(1.2),
        pytest.approx(1.5),
        pytest.approx(2.0),
    ]
    assert [point.success_rate for point in summary.axial_profiles[0].points] == pytest.approx(
        [0.8, 0.8, 0.8666666667, 0.9333333333]
    )
    assert [point.success_rate for point in summary.axial_profiles[1].points] == pytest.approx(
        [0.6666666667, 0.6666666667, 0.6666666667, 0.6666666667]
    )
    assert summary.total_axial_failures == 10
    assert summary.total_non_axial_failures == 0
    assert summary.failure_profiles[1].profile_name == "tight_clearance"
    assert summary.failure_profiles[1].mean_failed_axial_mm == pytest.approx(2.9435352422)


def test_export_figure3_criterion_decomposition_axial_tail_writes_pdf_and_png(
    tmp_path: Path,
) -> None:
    module = _load_paper_figures_module()
    pdf_path, png_path = module.export_figure3_criterion_decomposition_axial_tail(
        axial_sweep_path=_axial_tolerance_sweep_artifact_path(),
        failure_bucket_path=_failure_bucket_artifact_path(),
        output_dir=tmp_path,
    )

    assert pdf_path.name == "fig3_criterion_decomposition_axial_tail.pdf"
    assert png_path.name == "fig3_criterion_decomposition_axial_tail.png"
    assert pdf_path.exists()
    assert png_path.exists()
    assert pdf_path.stat().st_size > 0
    assert png_path.stat().st_size > 0


def test_load_figurea1_per_profile_axial_band_summary_matches_appendix_table_readout() -> None:
    module = _load_paper_figures_module()
    summary = module.load_figurea1_per_profile_axial_band_summary(
        axial_tail_sweep_path=_axial_tail_sweep_artifact_path(),
    )

    assert [profile.profile_name for profile in summary.profiles] == [
        "nominal",
        "tight_clearance",
        "high_friction",
        "offset_bias",
        "noisy_force",
    ]
    assert [band.tolerance_mm for band in summary.profiles[1].bands] == [
        pytest.approx(2.0),
        pytest.approx(3.0),
        pytest.approx(3.5),
    ]
    assert [band.success_rate for band in summary.profiles[1].bands] == pytest.approx(
        [0.6666666667, 0.8666666667, 1.0]
    )
    assert [band.success_rate for band in summary.mean_bands] == pytest.approx(
        [0.8666666667, 0.9733333333, 1.0]
    )


def test_export_figurea1_per_profile_axial_band_comparison_writes_pdf_and_png(
    tmp_path: Path,
) -> None:
    module = _load_paper_figures_module()
    pdf_path, png_path = module.export_figurea1_per_profile_axial_band_comparison(
        axial_tail_sweep_path=_axial_tail_sweep_artifact_path(),
        output_dir=tmp_path,
    )

    assert pdf_path.name == "figA1_per_profile_axial_band_comparison.pdf"
    assert png_path.name == "figA1_per_profile_axial_band_comparison.png"
    assert pdf_path.exists()
    assert png_path.exists()
    assert pdf_path.stat().st_size > 0
    assert png_path.stat().st_size > 0


def test_export_figurea1_evaluation_class_mapping_writes_pdf_and_png(
    tmp_path: Path,
) -> None:
    module = _load_paper_figures_module()
    pdf_path, png_path = module.export_figurea1_pressure_class_mapping(tmp_path)

    assert pdf_path.name == "figA1_evaluation_class_mapping.pdf"
    assert png_path.name == "figA1_evaluation_class_mapping.png"
    assert pdf_path.exists()
    assert png_path.exists()
    assert pdf_path.stat().st_size > 0
    assert png_path.stat().st_size > 0


def test_load_figurea2_strict_criterion_decomposition_summary_matches_appendix_claim() -> None:
    module = _load_paper_figures_module()
    summary = module.load_figurea2_strict_criterion_decomposition_summary(
        success_tolerance_path=_success_tolerance_sweep_artifact_path(),
        axial_sweep_path=_axial_tolerance_sweep_artifact_path(),
        speed_sweep_path=_speed_tolerance_sweep_artifact_path(),
        lateral_sweep_path=_lateral_tolerance_sweep_artifact_path(),
        failure_bucket_path=_failure_bucket_artifact_path(),
    )

    assert [profile.profile_name for profile in summary.old_lateral_profiles] == [
        "nominal",
        "tight_clearance",
        "high_friction",
        "offset_bias",
        "noisy_force",
    ]
    assert [point.success_rate for point in summary.old_lateral_profiles[2].points] == pytest.approx(
        [0.4666666667, 0.4666666667, 0.4666666667, 0.4666666667]
    )
    assert [point.success_rate for point in summary.axial_profiles[2].points] == pytest.approx(
        [0.4666666667, 0.7333333333, 0.8, 0.8666666667]
    )
    assert [point.success_rate for point in summary.speed_profiles[0].points] == pytest.approx(
        [0.9333333333, 0.9333333333, 0.9333333333, 0.9333333333, 0.9333333333]
    )
    assert [point.success_rate for point in summary.strict_lateral_profiles[3].points] == pytest.approx(
        [0.8666666667, 0.9333333333, 0.9333333333, 0.9333333333]
    )
    assert summary.total_axial_failures == 10
    assert summary.total_non_axial_failures == 0


def test_export_figurea2_strict_criterion_decomposition_writes_pdf_and_png(
    tmp_path: Path,
) -> None:
    module = _load_paper_figures_module()
    pdf_path, png_path = module.export_figurea2_strict_criterion_decomposition(
        success_tolerance_path=_success_tolerance_sweep_artifact_path(),
        axial_sweep_path=_axial_tolerance_sweep_artifact_path(),
        speed_sweep_path=_speed_tolerance_sweep_artifact_path(),
        lateral_sweep_path=_lateral_tolerance_sweep_artifact_path(),
        failure_bucket_path=_failure_bucket_artifact_path(),
        output_dir=tmp_path,
    )

    assert pdf_path.name == "figA2_strict_criterion_decomposition.pdf"
    assert png_path.name == "figA2_strict_criterion_decomposition.png"
    assert pdf_path.exists()
    assert png_path.exists()
    assert pdf_path.stat().st_size > 0
    assert png_path.stat().st_size > 0


def test_load_figurea3_teacher_ablation_summary_reads_teacher_block(tmp_path: Path) -> None:
    module = _load_paper_figures_module()
    benchmark_path, fixed_override_path = _write_appendix_figure_sample_artifacts(tmp_path)

    summary = module.load_figurea3_teacher_ablation_summary(
        benchmark_report_path=benchmark_path,
        fixed_impedance_report_path=fixed_override_path,
    )

    assert [suite.suite_name for suite in summary.suites] == [
        "teacher_variable_variable__repaired_mainline",
        "teacher_variable_fixed__repaired_mainline",
        "teacher_pose_variable__repaired_mainline",
        "teacher_pose_fixed__repaired_mainline",
    ]
    assert summary.suites[0].teacher_motion_rule == "contact_aware_variable_motion"
    assert summary.suites[0].teacher_impedance_rule == "contact_aware_variable_impedance"
    assert summary.suites[0].five_profile_success_rate == pytest.approx(0.99)
    assert summary.suites[0].per_profile[0].profile_name == "nominal"


def test_export_figurea3_teacher_ablation_summary_writes_pdf_and_png(
    tmp_path: Path,
) -> None:
    module = _load_paper_figures_module()
    benchmark_path, fixed_override_path = _write_appendix_figure_sample_artifacts(tmp_path)

    pdf_path, png_path = module.export_figurea3_teacher_ablation_summary(
        benchmark_report_path=benchmark_path,
        fixed_impedance_report_path=fixed_override_path,
        output_dir=tmp_path,
    )

    assert pdf_path.name == "figA3_teacher_ablation_summary.pdf"
    assert png_path.name == "figA3_teacher_ablation_summary.png"
    assert pdf_path.exists()
    assert png_path.exists()
    assert pdf_path.stat().st_size > 0
    assert png_path.stat().st_size > 0


def test_load_figurea4_termination_diagnostics_summary_reads_diagnostic_rates(
    tmp_path: Path,
) -> None:
    module = _load_paper_figures_module()
    benchmark_path, fixed_override_path = _write_appendix_figure_sample_artifacts(tmp_path)

    summary = module.load_figurea4_termination_diagnostics_summary(
        benchmark_report_path=benchmark_path,
        fixed_impedance_report_path=fixed_override_path,
    )

    assert [suite.suite_name for suite in summary.suites] == [
        "bc_only_stable_r32_p32",
        "repaired_mainline_bc_to_ppo",
        "dapg_lite_repaired_mainline",
        "fixed_impedance_rl_stable_r32_p32",
    ]
    fixed_suite = summary.suites[-1]
    assert fixed_suite.force_threshold_only_termination_rate == pytest.approx(0.02)
    assert fixed_suite.blocked_contact_only_termination_rate == pytest.approx(0.05)
    assert fixed_suite.force_and_blocked_termination_rate == pytest.approx(0.01)
    assert fixed_suite.documented_force_jam_rate == pytest.approx(0.02)


def test_export_figurea4_termination_diagnostics_summary_writes_pdf_and_png(
    tmp_path: Path,
) -> None:
    module = _load_paper_figures_module()
    benchmark_path, fixed_override_path = _write_appendix_figure_sample_artifacts(tmp_path)

    pdf_path, png_path = module.export_figurea4_termination_diagnostics_summary(
        benchmark_report_path=benchmark_path,
        fixed_impedance_report_path=fixed_override_path,
        output_dir=tmp_path,
    )

    assert pdf_path.name == "figA4_termination_diagnostics_summary.pdf"
    assert png_path.name == "figA4_termination_diagnostics_summary.png"
    assert pdf_path.exists()
    assert png_path.exists()
    assert pdf_path.stat().st_size > 0
    assert png_path.stat().st_size > 0


def test_manuscript_figure_stems_match_manifest_canonical_stems() -> None:
    manuscript = _paper_manuscript_path().read_text(encoding="utf-8")
    manifest = _paper_manifest_path().read_text(encoding="utf-8")

    expected_stems = [
        "fig1_task_policy_impedance_overview",
        "fig2_main_benchmark_evaluation_class_summary",
        "fig3_high_friction_impedance_mechanism",
        "figA1_evaluation_class_mapping",
        "fig1_contact_transition_audit",
    ]
    for stem in expected_stems:
        assert stem in manuscript
        assert f"`{stem}`" in manifest


def test_figure3_success_matched_and_legacy_assets_exist() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    expected_assets = [
        repo_root / "figures/main/fig3_high_friction_impedance_mechanism.pdf",
        repo_root / "figures/main/fig3_high_friction_impedance_mechanism.png",
        repo_root
        / "figures/appendix/fig3_legacy_all_trace_high_friction_impedance_mechanism.pdf",
        repo_root
        / "figures/appendix/fig3_legacy_all_trace_high_friction_impedance_mechanism.png",
    ]

    for path in expected_assets:
        assert path.is_file(), path
        assert path.stat().st_size > 0


def test_figure3_caption_uses_success_matched_framing() -> None:
    manuscript = (
        Path(__file__).resolve().parents[2] / "paper" / "main.tex"
    ).read_text(encoding="utf-8")
    figure_start = manuscript.index(r"\label{fig:high_friction_mechanism}")
    caption_start = manuscript.rfind(r"\caption{", 0, figure_start)
    caption_end = manuscript.index(r"\end{figure}", figure_start)
    caption_block = manuscript[caption_start:caption_end]

    caption_lower = caption_block.lower()
    assert "success-matched" in caption_lower
    assert "all-trace learned aggregates" not in caption_lower
