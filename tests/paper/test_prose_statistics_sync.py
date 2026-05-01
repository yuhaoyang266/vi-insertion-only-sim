from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
STATISTICS_REPORT = (
    REPO_ROOT / "artifacts" / "main_benchmark" / "three_dof_statistics_report_stage4_20260429.json"
)
MOTION_MATCHED_REPORT = (
    REPO_ROOT / "artifacts" / "main_benchmark" / "three_dof_motion_matched_main_20260429.json"
)
MAIN_TEX = REPO_ROOT / "paper" / "main.tex"


def _statistics_report() -> dict:
    return json.loads(STATISTICS_REPORT.read_text(encoding="utf-8"))


def _metric_text(report: dict, suite_name: str, metric_name: str, *, digits: int = 3) -> str:
    stats = report["suite_statistics"][suite_name]["five_profile_statistics"][metric_name]
    return f"${stats['mean']:.{digits}f} \\pm {stats['std']:.{digits}f}$"


def _comparison(report: dict, comparison_id: str) -> dict:
    for comparison in report["selected_comparisons"]:
        if comparison["comparison_id"] == comparison_id:
            return comparison
    raise AssertionError(f"Missing selected comparison: {comparison_id}")


def _motion_success(report: dict, condition_name: str) -> str:
    stats = report["aggregate"]["condition_statistics"][condition_name]["five_profile_statistics"][
        "success_rate"
    ]
    return f"${stats['mean']:.3f}$"


def test_motion_matched_report_path_matches_main_text_source() -> None:
    main_tex = MAIN_TEX.read_text(encoding="utf-8")
    report = json.loads(MOTION_MATCHED_REPORT.read_text(encoding="utf-8"))

    assert report["source_artifacts"]["protocol_runner"] == "scripts/experiments/run_3dof_motion_matched_main_protocol.py"
    assert "three\\_dof\\_motion\\_matched\\_main\\_20260429.json" in main_tex


def test_main_text_statistics_match_canonical_report() -> None:
    report = _statistics_report()
    motion_report = json.loads(MOTION_MATCHED_REPORT.read_text(encoding="utf-8"))
    main_tex = MAIN_TEX.read_text(encoding="utf-8")

    expected_snippets = [
        _metric_text(report, "bc_only_stable_r32_p32", "mean_peak_contact_force_n"),
        _metric_text(report, "repaired_mainline_bc_to_ppo", "mean_peak_contact_force_n"),
        _metric_text(report, "bc_only_stable_r32_p32", "p95_peak_contact_force_n"),
        _metric_text(report, "repaired_mainline_bc_to_ppo", "p95_peak_contact_force_n"),
        _metric_text(report, "dapg_lite_repaired_mainline", "mean_peak_contact_force_n"),
        _metric_text(report, "dapg_lite_repaired_mainline", "p95_peak_contact_force_n"),
        _metric_text(report, "fixed_impedance_rl_stable_r32_p32", "success_rate"),
    ]

    fixed_vs_mainline = _comparison(
        report,
        "repaired_mainline_bc_to_ppo__vs__fixed_impedance_rl_stable_r32_p32__success_rate",
    )
    expected_snippets.extend(
        [
            f"mean gap ${fixed_vs_mainline['mean_difference']:.4f}$",
            (
                "bootstrap CI "
                f"$[{fixed_vs_mainline['ci']['lower']:.4f}, "
                f"{fixed_vs_mainline['ci']['upper']:.4f}]$"
            ),
            f"p-value is still ${fixed_vs_mainline['p_value']:.4f}$",
            "three\\_dof\\_benchmark\\_paper9suite\\_full5profile\\_bc32x32\\_stage4\\_20260429.json",
            "three\\_dof\\_motion\\_matched\\_main\\_20260429.json",
            (
                f"\\code{{fi\\_motion\\_vi\\_k}} reaches "
                f"{_motion_success(motion_report, 'fi_motion_vi_k')} five-profile success"
            ),
            (
                f"\\code{{vi\\_motion\\_fi\\_k}} and \\code{{fi\\_full}} remain at "
                f"{_motion_success(motion_report, 'vi_motion_fi_k')}"
            ),
        ]
    )

    high_friction_success = report["suite_statistics"][
        "fixed_impedance_rl_stable_r32_p32"
    ]["per_profile_statistics"]["high_friction"]["success_rate"]
    expected_snippets.append(
        f"where success falls to ${high_friction_success['mean']:.3f} \\pm {high_friction_success['std']:.3f}$"
    )

    missing = [snippet for snippet in expected_snippets if snippet not in main_tex]
    assert missing == []
