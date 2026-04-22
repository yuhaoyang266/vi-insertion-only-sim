import json
from pathlib import Path
import subprocess
import sys

import pytest


def _confirm_report_payload() -> dict[str, object]:
    return {
        "report_name": "three_dof_cross_family_confirm_report",
        "grid_complete": True,
        "selected_branch": "branch_a",
        "branch_rationale": "All pure-RL families stay outside useful contact.",
        "source_report": "outputs/pilot_report/three_dof_cross_family_pilot_report.json",
        "best_distance_proxy_method": "sac_no_bc",
        "method_summaries": [
            {
                "method_name": "ppo_no_bc",
                "label": "PPO w/o BC",
                "best_budget": 200_000,
                "best_final_distance_mm": 25.48,
                "entered_contact": False,
                "mean_success_across_budgets": 0.0,
                "mean_contact_steps_across_budgets": 0.0,
                "mean_jam_rate_across_budgets": 0.0,
                "mean_peak_force_across_budgets": 0.0,
                "max_success_across_budgets": 0.0,
            },
            {
                "method_name": "sac_no_bc",
                "label": "SAC w/o BC",
                "best_budget": 200_000,
                "best_final_distance_mm": 16.67,
                "entered_contact": False,
                "mean_success_across_budgets": 0.0,
                "mean_contact_steps_across_budgets": 0.0,
                "mean_jam_rate_across_budgets": 0.0,
                "mean_peak_force_across_budgets": 0.0,
                "max_success_across_budgets": 0.0,
            },
            {
                "method_name": "td3_no_bc",
                "label": "TD3 w/o BC",
                "best_budget": 200_000,
                "best_final_distance_mm": 25.56,
                "entered_contact": False,
                "mean_success_across_budgets": 0.0,
                "mean_contact_steps_across_budgets": 0.0,
                "mean_jam_rate_across_budgets": 0.0,
                "mean_peak_force_across_budgets": 0.0,
                "max_success_across_budgets": 0.0,
            },
        ],
    }


def _benchmark_suite_payload(
    *,
    success_rate: float,
    final_distance_mm: float,
    peak_force_n: float,
    contact_steps: float,
    jam_rate: float = 0.0,
) -> dict[str, object]:
    profiles = (
        "nominal",
        "tight_clearance",
        "high_friction",
        "offset_bias",
        "noisy_force",
    )
    aggregate = {
        "success_rate_mean": success_rate,
        "success_rate_std": 0.0,
        "jam_rate_mean": jam_rate,
        "jam_rate_std": 0.0,
        "mean_final_distance_mean": final_distance_mm / 1000.0,
        "mean_final_distance_std": 0.0,
        "mean_peak_contact_force_mean": peak_force_n,
        "mean_peak_contact_force_std": 0.0,
        "p95_peak_contact_force_mean": peak_force_n + 0.2,
        "p95_peak_contact_force_std": 0.0,
        "mean_contact_steps_mean": contact_steps,
        "mean_contact_steps_std": 0.0,
    }
    return {
        "five_profile_mean": {
            "success_rate_mean_over_profiles": success_rate,
            "success_rate_std_over_profiles": 0.0,
            "jam_rate_mean_over_profiles": jam_rate,
            "jam_rate_std_over_profiles": 0.0,
            "mean_final_distance_mean_over_profiles": final_distance_mm / 1000.0,
            "mean_final_distance_std_over_profiles": 0.0,
            "mean_peak_contact_force_mean_over_profiles": peak_force_n,
            "mean_peak_contact_force_std_over_profiles": 0.0,
            "p95_peak_contact_force_mean_over_profiles": peak_force_n + 0.2,
            "p95_peak_contact_force_std_over_profiles": 0.0,
            "mean_contact_steps_mean_over_profiles": contact_steps,
            "mean_contact_steps_std_over_profiles": 0.0,
        },
        "eval_results": {
            profile_name: {"aggregate": dict(aggregate)} for profile_name in profiles
        },
    }


def _benchmark_report_payload() -> dict[str, object]:
    return {
        "config": {
            "suite_names": [
                "ppo_no_bc",
                "bc_only_stable_r32_p32",
                "fixed_impedance_rl_stable_r32_p32",
                "repaired_mainline_bc_to_ppo",
                "dapg_lite_repaired_mainline",
            ],
            "timesteps": 128,
            "base_bc_rollout_episodes": 32,
            "base_bc_pretrain_steps": 32,
            "base_bc_batch_size": 64,
        },
        "handcrafted_results": {},
        "learned_results": {
            "ppo_no_bc": _benchmark_suite_payload(
                success_rate=0.0,
                final_distance_mm=25.48,
                peak_force_n=0.0,
                contact_steps=0.0,
            ),
            "bc_only_stable_r32_p32": _benchmark_suite_payload(
                success_rate=1.0,
                final_distance_mm=0.90,
                peak_force_n=0.93,
                contact_steps=29.97,
            ),
            "fixed_impedance_rl_stable_r32_p32": _benchmark_suite_payload(
                success_rate=0.80,
                final_distance_mm=1.10,
                peak_force_n=0.90,
                contact_steps=36.22,
            ),
            "repaired_mainline_bc_to_ppo": _benchmark_suite_payload(
                success_rate=1.0,
                final_distance_mm=0.94,
                peak_force_n=0.68,
                contact_steps=26.28,
            ),
            "dapg_lite_repaired_mainline": _benchmark_suite_payload(
                success_rate=0.60,
                final_distance_mm=1.17,
                peak_force_n=0.85,
                contact_steps=27.55,
            ),
        },
    }


def _write_json(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _run_cli(tmp_path: Path) -> tuple[subprocess.CompletedProcess[str], Path]:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = (
        repo_root / "scripts" / "experiments" / "export_3dof_evidence_matrix.py"
    )
    confirm_path = _write_json(tmp_path / "confirm.json", _confirm_report_payload())
    benchmark_path = _write_json(tmp_path / "benchmark.json", _benchmark_report_payload())
    output_dir = tmp_path / "evidence_matrix"
    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--confirm-report",
            str(confirm_path),
            "--benchmark-report",
            str(benchmark_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed, output_dir


def test_cli_exports_json_csv_markdown_and_figures(tmp_path: Path) -> None:
    completed, output_dir = _run_cli(tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert (output_dir / "three_dof_evidence_matrix.json").exists()
    assert (output_dir / "three_dof_evidence_matrix.csv").exists()
    assert (output_dir / "three_dof_evidence_matrix.md").exists()
    assert (output_dir / "three_dof_contact_gate_matrix.png").exists()
    assert (output_dir / "three_dof_contact_gate_matrix.pdf").exists()

    csv_text = (output_dir / "three_dof_evidence_matrix.csv").read_text(
        encoding="utf-8"
    )
    assert (
        "method_name,label,method_family,source_contract,benchmark,train_budget,"
        "entered_contact,success_rate,mean_final_distance_mm,mean_contact_steps,"
        "jam_rate,mean_peak_contact_force_n,evidence_role,allowed_claim,"
        "not_allowed_claim,source_report"
    ) in csv_text

    markdown_text = (output_dir / "three_dof_evidence_matrix.md").read_text(
        encoding="utf-8"
    )
    assert "mixed-contract" in markdown_text
    assert "leaderboard" in markdown_text

    payload = json.loads(
        (output_dir / "three_dof_evidence_matrix.json").read_text(encoding="utf-8")
    )
    assert payload["row_count"] == 7
    assert payload["matrix_contract"]["mixed_contracts"] is True
    sac_row = next(row for row in payload["rows"] if row["method_name"] == "sac_no_bc")
    assert sac_row["entered_contact"] is False
    assert "distance proxy" in sac_row["allowed_claim"].lower()


@pytest.mark.parametrize(
    "missing_field",
    ["mean_jam_rate_across_budgets", "mean_peak_force_across_budgets"],
)
def test_cli_fails_fast_when_confirm_report_omits_zero_contact_metrics(
    tmp_path: Path,
    missing_field: str,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = (
        repo_root / "scripts" / "experiments" / "export_3dof_evidence_matrix.py"
    )
    confirm = _confirm_report_payload()
    del confirm["method_summaries"][1][missing_field]
    confirm_path = _write_json(tmp_path / "confirm.json", confirm)
    benchmark_path = _write_json(tmp_path / "benchmark.json", _benchmark_report_payload())
    output_dir = tmp_path / "evidence_matrix"

    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--confirm-report",
            str(confirm_path),
            "--benchmark-report",
            str(benchmark_path),
            "--output-dir",
            str(output_dir),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode != 0
    assert missing_field in completed.stderr
