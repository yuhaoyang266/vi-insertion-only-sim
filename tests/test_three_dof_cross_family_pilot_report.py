import importlib.util
import json
from pathlib import Path
import sys

import pytest


def _load_report_module():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "vi_full"
        / "three_dof_cross_family_pilot_report.py"
    )
    spec = importlib.util.spec_from_file_location(
        "three_dof_cross_family_pilot_report_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _chunk_payload(
    *,
    method_name: str,
    algorithm: str,
    label: str,
    budget: int,
    success_rate: float,
    first_contact_step: float,
    final_distance_m: float,
    contact_steps: float,
) -> dict[str, object]:
    return {
        "experiment_name": "three_dof_cross_family_pilot",
        "config": {
            "seed_list": [0, 1, 2],
            "budget_points": [budget],
            "train_profile": "nominal",
            "profiles": ["nominal"],
            "episodes_per_seed": 50,
            "max_episode_steps": 64,
            "method_names": [method_name],
        },
        "methods": [
            {
                "method_name": method_name,
                "label": label,
                "algorithm": algorithm,
                "train_overrides": {},
                "points": [
                    {
                        "method_name": method_name,
                        "algorithm": algorithm,
                        "factor_value": budget,
                        "training_budget": {"total_timesteps": budget},
                        "train_config_snapshot": {},
                        "train_configs": [],
                        "training_summaries": [],
                        "per_profile_metrics": {
                            "nominal": {
                                "per_seed": [],
                                "aggregate": {
                                    "policy_name": algorithm.upper(),
                                    "uncertainty_profile": "nominal",
                                    "num_seeds": 3,
                                    "seeds": [0, 1, 2],
                                    "success_rate_mean": success_rate,
                                    "success_rate_std": 0.0,
                                    "mean_final_distance_mean": final_distance_m,
                                    "mean_final_distance_std": 0.0,
                                    "mean_first_contact_step_mean": first_contact_step,
                                    "mean_first_contact_step_std": 0.0,
                                    "mean_contact_steps_mean": contact_steps,
                                    "mean_contact_steps_std": 0.0,
                                    "mean_peak_contact_force_mean": 0.0,
                                    "mean_peak_contact_force_std": 0.0,
                                    "jam_rate_mean": 0.0,
                                    "jam_rate_std": 0.0,
                                    "method_name": method_name,
                                    "algorithm": algorithm,
                                    "train_uncertainty_profile": "nominal",
                                    "eval_uncertainty_profile": "nominal",
                                },
                            }
                        },
                        "five_profile_mean": {
                            "success_rate_mean_over_profiles": success_rate,
                            "success_rate_std_over_profiles": 0.0,
                            "mean_final_distance_mean_over_profiles": final_distance_m,
                            "mean_final_distance_std_over_profiles": 0.0,
                            "mean_first_contact_step_mean_over_profiles": first_contact_step,
                            "mean_first_contact_step_std_over_profiles": 0.0,
                            "mean_contact_steps_mean_over_profiles": contact_steps,
                            "mean_contact_steps_std_over_profiles": 0.0,
                            "mean_peak_contact_force_mean_over_profiles": 0.0,
                            "mean_peak_contact_force_std_over_profiles": 0.0,
                            "jam_rate_mean_over_profiles": 0.0,
                            "jam_rate_std_over_profiles": 0.0,
                        },
                    }
                ],
            }
        ],
    }


def _write_chunk(
    chunk_dir: Path,
    *,
    method_name: str,
    algorithm: str,
    label: str,
    budget: int,
    success_rate: float,
    first_contact_step: float,
    final_distance_m: float,
    contact_steps: float,
) -> Path:
    payload = _chunk_payload(
        method_name=method_name,
        algorithm=algorithm,
        label=label,
        budget=budget,
        success_rate=success_rate,
        first_contact_step=first_contact_step,
        final_distance_m=final_distance_m,
        contact_steps=contact_steps,
    )
    path = chunk_dir / f"three_dof_cross_family_pilot__{method_name}__{budget}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_build_cross_family_pilot_report_merges_partial_grid(tmp_path: Path) -> None:
    module = _load_report_module()
    chunk_dir = tmp_path / "pilot_chunks"
    chunk_dir.mkdir()
    _write_chunk(
        chunk_dir,
        method_name="ppo_no_bc",
        algorithm="ppo",
        label="PPO w/o BC",
        budget=50_000,
        success_rate=0.0,
        first_contact_step=64.0,
        final_distance_m=0.031,
        contact_steps=0.0,
    )
    _write_chunk(
        chunk_dir,
        method_name="ppo_no_bc",
        algorithm="ppo",
        label="PPO w/o BC",
        budget=100_000,
        success_rate=0.0,
        first_contact_step=64.0,
        final_distance_m=0.029,
        contact_steps=0.0,
    )
    _write_chunk(
        chunk_dir,
        method_name="sac_no_bc",
        algorithm="sac",
        label="SAC w/o BC",
        budget=100_000,
        success_rate=0.0,
        first_contact_step=52.0,
        final_distance_m=0.012,
        contact_steps=4.0,
    )

    report = module.build_3dof_cross_family_pilot_report(chunk_dir)

    assert report["expected_grid"]["method_names"] == [
        "ppo_no_bc",
        "sac_no_bc",
        "td3_no_bc",
    ]
    assert report["expected_grid"]["budget_points"] == [50_000, 100_000, 200_000]
    assert report["expected_grid"]["expected_chunk_count"] == 9
    assert report["expected_grid"]["completed_chunk_count"] == 3
    assert report["expected_grid"]["missing_chunk_count"] == 6
    assert report["completed_chunks"] == [
        {"method_name": "ppo_no_bc", "budget": 50_000},
        {"method_name": "ppo_no_bc", "budget": 100_000},
        {"method_name": "sac_no_bc", "budget": 100_000},
    ]
    assert report["missing_chunks"][0] == {"method_name": "ppo_no_bc", "budget": 200_000}
    assert report["missing_chunks"][-1] == {"method_name": "td3_no_bc", "budget": 200_000}

    ppo_method = report["methods"][0]
    assert ppo_method["method_name"] == "ppo_no_bc"
    assert [point["budget"] for point in ppo_method["points"]] == [50_000, 100_000]
    assert ppo_method["points"][0]["five_profile_mean"]["success_rate"] == pytest.approx(0.0)

    sac_row = next(
        row
        for row in report["summary_rows"]
        if row["method_name"] == "sac_no_bc" and row["budget"] == 100_000
    )
    assert sac_row["mean_first_contact_step"] == pytest.approx(52.0)
    assert sac_row["mean_final_distance_mm"] == pytest.approx(12.0)
    assert sac_row["mean_contact_steps"] == pytest.approx(4.0)


def test_export_cross_family_pilot_report_and_figures_write_artifacts(
    tmp_path: Path,
) -> None:
    module = _load_report_module()
    chunk_dir = tmp_path / "pilot_chunks"
    chunk_dir.mkdir()
    _write_chunk(
        chunk_dir,
        method_name="ppo_no_bc",
        algorithm="ppo",
        label="PPO w/o BC",
        budget=50_000,
        success_rate=0.0,
        first_contact_step=64.0,
        final_distance_m=0.031,
        contact_steps=0.0,
    )
    _write_chunk(
        chunk_dir,
        method_name="sac_no_bc",
        algorithm="sac",
        label="SAC w/o BC",
        budget=100_000,
        success_rate=0.0,
        first_contact_step=52.0,
        final_distance_m=0.012,
        contact_steps=4.0,
    )
    _write_chunk(
        chunk_dir,
        method_name="td3_no_bc",
        algorithm="td3",
        label="TD3 w/o BC",
        budget=200_000,
        success_rate=0.2,
        first_contact_step=31.0,
        final_distance_m=0.004,
        contact_steps=14.0,
    )

    output_dir = tmp_path / "exports"
    json_path = module.export_3dof_cross_family_pilot_report(
        chunk_dir=chunk_dir,
        output_dir=output_dir,
        stem="pilot_report",
    )
    figures = module.export_3dof_cross_family_pilot_internal_figures(
        chunk_dir=chunk_dir,
        output_dir=output_dir,
        stem_prefix="pilot_internal",
    )

    exported = json.loads(json_path.read_text(encoding="utf-8"))
    assert json_path.name == "pilot_report.json"
    assert exported["expected_grid"]["completed_chunk_count"] == 3
    assert exported["summary_rows"][-1]["method_name"] == "td3_no_bc"
    assert set(figures.keys()) == {"success_vs_budget", "first_contact_step_vs_budget"}

    success_pdf, success_png = figures["success_vs_budget"]
    first_contact_pdf, first_contact_png = figures["first_contact_step_vs_budget"]

    assert success_pdf.name == "pilot_internal_success_vs_budget.pdf"
    assert success_png.name == "pilot_internal_success_vs_budget.png"
    assert first_contact_pdf.name == "pilot_internal_first_contact_step_vs_budget.pdf"
    assert first_contact_png.name == "pilot_internal_first_contact_step_vs_budget.png"
    for path in (success_pdf, success_png, first_contact_pdf, first_contact_png):
        assert path.exists()
        assert path.stat().st_size > 0
