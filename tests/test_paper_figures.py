import importlib.util
from pathlib import Path
import sys

import pytest

def _contact_audit_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "latest_three_dof_contact_model_audit.json"
    )


def _phase2_demo_coverage_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "three_dof_factor_sweep_demonstration_coverage_20260411_172516.json"
    )


def _phase2_reset_coverage_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "three_dof_factor_sweep_reset_coverage_20260411_172635.json"
    )


def _phase2_bc_optimization_depth_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "three_dof_factor_sweep_bc_optimization_depth_20260411_172923.json"
    )


def _phase2_algorithm_budget_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "three_dof_algorithm_budget_comparison_20260411_175606.json"
    )


def _stage3_benchmark_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json"
    )


def _stage3_statistics_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "paper_only_sim_tables"
        / "three_dof_statistics_report_stage3_20260412.json"
    )


def _paper_manifest_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "paper_only_sim_figure_asset_manifest.md"
    )


def _paper_manuscript_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "paper_manuscript_only_sim_final.tex"
    )


def _axial_tolerance_sweep_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "latest_three_dof_axial_tolerance_sweep_seed012.json"
    )


def _failure_bucket_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "latest_three_dof_failure_bucket_axial2p0_lateral1p5_seed012.json"
    )


def _axial_tail_sweep_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "latest_three_dof_axial_tail_sweep_lateral1p5_seed012.json"
    )


def _success_tolerance_sweep_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "latest_three_dof_success_tolerance_sweep_seed012.json"
    )


def _speed_tolerance_sweep_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "latest_three_dof_speed_tolerance_sweep_axial2p0_seed012.json"
    )


def _lateral_tolerance_sweep_artifact_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "outputs"
        / "latest_three_dof_lateral_tolerance_sweep_axial2p0_seed012.json"
    )


def _load_paper_figures_module():
    module_path = (
        Path(__file__).resolve().parents[1] / "src" / "vi_full" / "paper_figures.py"
    )
    spec = importlib.util.spec_from_file_location("paper_figures_under_test", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
        benchmark_report_path=_stage3_benchmark_artifact_path(),
        statistics_report_path=_stage3_statistics_artifact_path(),
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
