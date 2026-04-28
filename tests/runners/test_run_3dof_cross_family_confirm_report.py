import json
from pathlib import Path
import subprocess
import sys

import pytest


METHOD_SPECS = {
    "ppo_no_bc": {"label": "PPO w/o BC", "algorithm": "ppo"},
    "sac_no_bc": {"label": "SAC w/o BC", "algorithm": "sac"},
    "td3_no_bc": {"label": "TD3 w/o BC", "algorithm": "td3"},
}


DISTANCE_MM = {
    "ppo_no_bc": {50_000: 31.02, 100_000: 29.47, 200_000: 25.48},
    "sac_no_bc": {50_000: 23.27, 100_000: 17.58, 200_000: 16.67},
    "td3_no_bc": {50_000: 30.78, 100_000: 28.62, 200_000: 25.56},
}


def _pilot_report_payload() -> dict[str, object]:
    summary_rows: list[dict[str, object]] = []
    for method_name, spec in METHOD_SPECS.items():
        for budget, final_distance_mm in DISTANCE_MM[method_name].items():
            summary_rows.append(
                {
                    "method_name": method_name,
                    "label": spec["label"],
                    "algorithm": spec["algorithm"],
                    "budget": budget,
                    "success_rate": 0.0,
                    "mean_first_contact_step": 64.0,
                    "mean_final_distance_mm": final_distance_mm,
                    "mean_contact_steps": 0.0,
                    "mean_peak_contact_force_n": 0.0,
                    "jam_rate": 0.0,
                }
            )
    return {
        "experiment_name": "three_dof_cross_family_pilot",
        "expected_grid": {
            "method_names": list(METHOD_SPECS),
            "budget_points": [50_000, 100_000, 200_000],
            "expected_chunk_count": 9,
            "completed_chunk_count": 9,
            "missing_chunk_count": 0,
        },
        "completed_chunks": [
            {"method_name": row["method_name"], "budget": row["budget"]}
            for row in summary_rows
        ],
        "missing_chunks": [],
        "summary_rows": summary_rows,
    }


def _write_pilot_report(tmp_path: Path) -> Path:
    pilot_report = tmp_path / "three_dof_cross_family_pilot_report.json"
    pilot_report.write_text(json.dumps(_pilot_report_payload()), encoding="utf-8")
    return pilot_report


def _run_cli(tmp_path: Path) -> tuple[subprocess.CompletedProcess[str], Path]:
    repo_root = Path(__file__).resolve().parents[2]
    script_path = (
        repo_root / "scripts" / "experiments" / "export_3dof_cross_family_confirm_report.py"
    )
    output_dir = tmp_path / "cross_family_confirm"
    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--pilot-report",
            str(_write_pilot_report(tmp_path)),
            "--output-dir",
            str(output_dir),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed, output_dir


def test_cli_writes_json_csv_markdown_and_figures(tmp_path: Path) -> None:
    completed, output_dir = _run_cli(tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert (output_dir / "three_dof_cross_family_confirm_report.json").exists()
    assert (output_dir / "three_dof_cross_family_confirm_distance_proxy.csv").exists()
    assert (output_dir / "three_dof_cross_family_confirm_contact_gate_table.md").exists()
    assert (
        output_dir / "three_dof_cross_family_confirm_distance_vs_budget.png"
    ).exists()
    assert (
        output_dir / "three_dof_cross_family_confirm_distance_vs_budget.pdf"
    ).exists()
    assert (
        output_dir / "three_dof_cross_family_confirm_learning_curve_summary.png"
    ).exists()
    assert (
        output_dir / "three_dof_cross_family_confirm_learning_curve_summary.pdf"
    ).exists()

    table_text = (
        output_dir / "three_dof_cross_family_confirm_contact_gate_table.md"
    ).read_text(encoding="utf-8")
    assert "9/9 zero-contact method-budget cells" in table_text
    assert "| SAC w/o BC | 200000 | 16.67 | no |" in table_text

    csv_text = (
        output_dir / "three_dof_cross_family_confirm_distance_proxy.csv"
    ).read_text(encoding="utf-8")
    assert "method_name,label,budget,mean_final_distance_mm,entered_contact,is_best_distance_proxy" in csv_text
    assert "sac_no_bc,SAC w/o BC,200000,16.67,false,true" in csv_text


def test_cli_preserves_paper_claim_boundary(tmp_path: Path) -> None:
    completed, output_dir = _run_cli(tmp_path)

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(
        (output_dir / "three_dof_cross_family_confirm_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["grid_complete"] is True
    assert payload["selected_branch"] == "branch_a"
    assert payload["best_distance_proxy_method"] == "sac_no_bc"
    assert "sac_no_bc is the strongest distance proxy but still zero-contact" in payload["paper_claim_boundary"]["allowed"]
    assert "sac_no_bc solves insertion or enters useful contact" in payload["paper_claim_boundary"]["not_allowed"]


@pytest.mark.parametrize("missing_field", ["jam_rate", "mean_peak_contact_force_n"])
def test_cli_fails_fast_when_pilot_report_omits_zero_contact_metrics(
    tmp_path: Path,
    missing_field: str,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script_path = (
        repo_root / "scripts" / "experiments" / "export_3dof_cross_family_confirm_report.py"
    )
    payload = _pilot_report_payload()
    del payload["summary_rows"][0][missing_field]
    pilot_report = tmp_path / "three_dof_cross_family_pilot_report.json"
    pilot_report.write_text(json.dumps(payload), encoding="utf-8")
    output_dir = tmp_path / "cross_family_confirm"

    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--pilot-report",
            str(pilot_report),
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
