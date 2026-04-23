import json
from pathlib import Path

import pytest

from vi_full.three_dof_profiles import build_3dof_profile_config


def _aggregate(
    profile_name: str,
    *,
    success_rate: float,
    jam_rate: float,
    final_distance_mm: float,
    peak_force_n: float,
    contact_steps: float,
) -> dict[str, float | str]:
    return {
        "uncertainty_profile": profile_name,
        "success_rate_mean": success_rate,
        "jam_rate_mean": jam_rate,
        "mean_final_distance_mean": final_distance_mm / 1000.0,
        "mean_peak_contact_force_mean": peak_force_n,
        "mean_contact_steps_mean": contact_steps,
    }


def _suite_result(
    suite_name: str,
    *,
    easy_success: float,
    nominal_success: float,
    hard_success: float,
) -> dict[str, object]:
    return {
        "suite_name": suite_name,
        "training_budget": {
            "total_timesteps": 128,
            "bc_rollout_episodes": 32,
            "bc_pretrain_steps": 32,
        },
        "per_profile_metrics": {
            "clearance_easy": {
                "aggregate": _aggregate(
                    "clearance_easy",
                    success_rate=easy_success,
                    jam_rate=0.0,
                    final_distance_mm=0.8,
                    peak_force_n=1.0,
                    contact_steps=31.0,
                )
            },
            "nominal": {
                "aggregate": _aggregate(
                    "nominal",
                    success_rate=nominal_success,
                    jam_rate=0.0,
                    final_distance_mm=0.9,
                    peak_force_n=1.1,
                    contact_steps=29.0,
                )
            },
            "clearance_hard": {
                "aggregate": _aggregate(
                    "clearance_hard",
                    success_rate=hard_success,
                    jam_rate=0.1,
                    final_distance_mm=1.4,
                    peak_force_n=1.5,
                    contact_steps=24.0,
                )
            },
        },
    }


def test_clearance_shift_profiles_isolate_clearance_only() -> None:
    nominal = build_3dof_profile_config("nominal")
    easy = build_3dof_profile_config("clearance_easy")
    hard = build_3dof_profile_config("clearance_hard")

    assert easy.hole_xy_offset_range_m == nominal.hole_xy_offset_range_m
    assert hard.hole_xy_offset_range_m == nominal.hole_xy_offset_range_m
    assert easy.wall_friction_range == nominal.wall_friction_range
    assert hard.wall_friction_range == nominal.wall_friction_range
    assert easy.force_noise_std_range == nominal.force_noise_std_range
    assert hard.force_noise_std_range == nominal.force_noise_std_range
    assert easy.clearance_range_m[0] > nominal.clearance_range_m[0] > hard.clearance_range_m[0]
    assert easy.clearance_range_m[1] > nominal.clearance_range_m[1] > hard.clearance_range_m[1]


def test_contract_freezes_three_profile_four_suite_boundary() -> None:
    from vi_full.sprint4_clearance_shift import (
        CLEARANCE_SHIFT_PROFILES,
        SPRINT4_CLEARANCE_SHIFT_SUITE_ORDER,
        build_sprint4_clearance_shift_contract,
    )

    contract = build_sprint4_clearance_shift_contract()

    assert contract["export_name"] == "sprint4_clearance_shift"
    assert contract["profile_order"] == list(CLEARANCE_SHIFT_PROFILES)
    assert contract["suite_order"] == list(SPRINT4_CLEARANCE_SHIFT_SUITE_ORDER)
    assert contract["execution_boundary"]["mode"] == "train_once_eval_many_profiles"
    assert contract["required_metrics"] == [
        "success_rate",
        "mean_final_distance_mm",
        "mean_contact_steps",
        "jam_rate",
        "mean_peak_contact_force_n",
    ]
    assert "not a mixed-contract leaderboard" in contract["claim_boundary"]["not_allowed"]


def test_report_and_export_capture_per_profile_clearance_drop(tmp_path: Path) -> None:
    from vi_full.sprint4_clearance_shift import (
        build_sprint4_clearance_shift_report,
        export_sprint4_clearance_shift_artifacts,
        render_sprint4_clearance_shift_markdown,
    )

    report = build_sprint4_clearance_shift_report(
        suite_results={
            "bc_only_stable_r32_p32": _suite_result(
                "bc_only_stable_r32_p32",
                easy_success=1.0,
                nominal_success=0.98,
                hard_success=0.92,
            ),
            "repaired_mainline_bc_to_ppo": _suite_result(
                "repaired_mainline_bc_to_ppo",
                easy_success=0.98,
                nominal_success=0.96,
                hard_success=0.84,
            ),
            "dapg_lite_repaired_mainline": _suite_result(
                "dapg_lite_repaired_mainline",
                easy_success=0.86,
                nominal_success=0.78,
                hard_success=0.52,
            ),
            "fixed_impedance_rl_stable_r32_p32": _suite_result(
                "fixed_impedance_rl_stable_r32_p32",
                easy_success=0.94,
                nominal_success=0.91,
                hard_success=0.74,
            ),
        },
        source_contract="sprint4a clearance-shift stress sweep",
    )

    assert report["suite_order"] == [
        "bc_only_stable_r32_p32",
        "repaired_mainline_bc_to_ppo",
        "dapg_lite_repaired_mainline",
        "fixed_impedance_rl_stable_r32_p32",
    ]
    assert report["suite_rows"][0]["per_profile"]["clearance_hard"]["mean_final_distance_mm"] == pytest.approx(
        1.4
    )
    assert report["suite_rows"][1]["clearance_drop"]["success_rate_easy_to_hard"] == pytest.approx(
        0.14
    )

    markdown = render_sprint4_clearance_shift_markdown(report)
    assert "clearance_hard" in markdown
    assert "not a mixed-contract leaderboard" in markdown

    artifacts = export_sprint4_clearance_shift_artifacts(report, tmp_path)
    payload = json.loads(artifacts["json_path"].read_text(encoding="utf-8"))
    csv_text = artifacts["csv_path"].read_text(encoding="utf-8")

    assert payload["suite_rows"][2]["suite_name"] == "dapg_lite_repaired_mainline"
    assert "fixed_impedance_rl_stable_r32_p32" in csv_text
    assert "clearance_easy" in csv_text


def test_repo_docs_reference_sprint4_clearance_shift_boundary() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    task_plan = (repo_root / "task_plan.md").read_text(encoding="utf-8")
    docs = "\n".join(
        [
            (repo_root / "README.md").read_text(encoding="utf-8"),
            (repo_root / "docs" / "figure_asset_manifest.md").read_text(
                encoding="utf-8"
            ),
            (repo_root / "paper" / "main.tex").read_text(encoding="utf-8"),
            task_plan,
        ]
    )

    assert "outputs/sprint4_clearance_shift/sprint4_clearance_shift.json" in docs
    assert "export_sprint4_clearance_shift.py" in docs
    assert "clearance_easy" in docs
    assert "clearance_hard" in docs
    assert "not a replacement" in docs
    assert "frozen five-profile" in docs
    assert "Phase 3 complete" in task_plan
    assert "- [x] Sprint 4A: Clearance shift 鲁棒性扫描" in task_plan
