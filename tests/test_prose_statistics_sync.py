from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STATISTICS_REPORT = (
    REPO_ROOT / "artifacts" / "main_benchmark" / "three_dof_statistics_report_stage3_20260412.json"
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


def test_main_text_statistics_match_canonical_report() -> None:
    report = _statistics_report()
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
