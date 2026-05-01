from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner_module():
    module_path = (
        REPO_ROOT
        / "scripts"
        / "experiments"
        / "run_3dof_alt_contact_model_sensitivity.py"
    )
    spec = importlib.util.spec_from_file_location(
        "run_3dof_alt_contact_model_sensitivity_under_test",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_alt_contact_model_sensitivity_runner_writes_artifacts(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = _load_runner_module()

    def _fake_run(**kwargs):
        return {
            "artifact_type": "three_dof_alt_contact_model_cross_check",
            "schema_version": 1,
            "claim_scope": "within-A fallback contact-law cross-check",
            "config": kwargs,
            "contact_models": [
                "within_a_base_contact_law",
                "within_a_soft_wall_contact_cross_check",
            ],
            "changed_fields": ["contact_xy_scale"],
            "contact_model_summaries": [],
            "rows": [
                {
                    "contact_model": "within_a_base_contact_law",
                    "profile": "nominal",
                    "policy_name": "fixed_impedance",
                    "seed_count": 1,
                    "episodes_per_seed": 1,
                    "success_rate": 1.0,
                    "jam_rate": 0.0,
                    "documented_force_jam_rate": 0.0,
                    "blocked_contact_termination_rate": 0.0,
                    "mean_final_distance": 0.0005,
                    "mean_peak_contact_force": 1.2,
                    "p95_peak_contact_force": 1.2,
                    "mean_contact_steps": 10.0,
                    "mean_contact_work": 0.01,
                }
            ],
            "paired_deltas": [],
        }

    output_path = tmp_path / "alt_contact_model.json"
    monkeypatch.setattr(module, "run_alt_contact_model_cross_check", _fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_3dof_alt_contact_model_sensitivity.py",
            "--profiles",
            "nominal",
            "--seeds",
            "0",
            "--episodes-per-seed",
            "1",
            "--policies",
            "fixed_impedance",
            "--output",
            str(output_path),
        ],
    )

    module.main()
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["config"]["profiles"] == ["nominal"]
    assert payload["config"]["policy_names"] == ["fixed_impedance"]
    assert output_path.with_suffix(".csv").exists()
    assert output_path.with_suffix(".md").exists()


def test_alt_contact_model_sensitivity_runner_help_works_from_repo_root() -> None:
    script_path = (
        REPO_ROOT
        / "scripts"
        / "experiments"
        / "run_3dof_alt_contact_model_sensitivity.py"
    )

    completed = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Run a 3DoF alternative contact-model cross-check" in completed.stdout
