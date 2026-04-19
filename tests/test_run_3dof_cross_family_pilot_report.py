import json
from pathlib import Path
import subprocess
import sys


def _chunk_payload(
    *,
    method_name: str,
    algorithm: str,
    label: str,
    budget: int,
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
                                    "success_rate_mean": 0.0,
                                    "success_rate_std": 0.0,
                                    "mean_final_distance_mean": 0.02,
                                    "mean_final_distance_std": 0.0,
                                    "mean_first_contact_step_mean": 64.0,
                                    "mean_first_contact_step_std": 0.0,
                                    "mean_contact_steps_mean": 0.0,
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
                            "success_rate_mean_over_profiles": 0.0,
                            "success_rate_std_over_profiles": 0.0,
                            "mean_final_distance_mean_over_profiles": 0.02,
                            "mean_final_distance_std_over_profiles": 0.0,
                            "mean_first_contact_step_mean_over_profiles": 64.0,
                            "mean_first_contact_step_std_over_profiles": 0.0,
                            "mean_contact_steps_mean_over_profiles": 0.0,
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


def test_cross_family_pilot_report_cli_exports_json_and_figures(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = (
        repo_root / "scripts" / "experiments" / "export_3dof_cross_family_pilot_report.py"
    )
    chunk_dir = tmp_path / "pilot_chunks"
    chunk_dir.mkdir()
    chunk_path = chunk_dir / "three_dof_cross_family_pilot__ppo_no_bc__50000.json"
    chunk_path.write_text(
        json.dumps(
            _chunk_payload(
                method_name="ppo_no_bc",
                algorithm="ppo",
                label="PPO w/o BC",
                budget=50_000,
            )
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "exports"

    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--chunk-dir",
            str(chunk_dir),
            "--output-dir",
            str(output_dir),
            "--stem",
            "pilot_report",
            "--figure-stem-prefix",
            "pilot_internal",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert (output_dir / "pilot_report.json").exists()
    assert (output_dir / "pilot_internal_success_vs_budget.pdf").exists()
    assert (output_dir / "pilot_internal_success_vs_budget.png").exists()
    assert (output_dir / "pilot_internal_first_contact_step_vs_budget.pdf").exists()
    assert (output_dir / "pilot_internal_first_contact_step_vs_budget.png").exists()
