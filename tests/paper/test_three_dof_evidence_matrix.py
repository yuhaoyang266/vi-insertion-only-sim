import json
from pathlib import Path
import shutil
import tempfile
import time
import hashlib

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_MANIFEST_PATH = REPO_ROOT / "artifacts" / "main_benchmark" / "main_benchmark_manifest.json"
CANONICAL_BENCHMARK = (
    "artifacts/main_benchmark/"
    "three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json"
)
SCHEMA2_DIAGNOSTIC = (
    "artifacts/main_benchmark/"
    "three_dof_benchmark_schema2_paper_teacher_20260418_034230.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


PURE_RL_CONFIRM_ROWS = {
    "ppo_no_bc": {
        "label": "PPO w/o BC",
        "best_budget": 200_000,
        "best_final_distance_mm": 25.48,
    },
    "sac_no_bc": {
        "label": "SAC w/o BC",
        "best_budget": 200_000,
        "best_final_distance_mm": 16.67,
    },
    "td3_no_bc": {
        "label": "TD3 w/o BC",
        "best_budget": 200_000,
        "best_final_distance_mm": 25.56,
    },
}


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
                "method_name": method_name,
                "label": spec["label"],
                "best_budget": spec["best_budget"],
                "best_final_distance_mm": spec["best_final_distance_mm"],
                "entered_contact": False,
                "mean_success_across_budgets": 0.0,
                "mean_contact_steps_across_budgets": 0.0,
                "mean_jam_rate_across_budgets": 0.0,
                "mean_peak_force_across_budgets": 0.0,
                "max_success_across_budgets": 0.0,
            }
            for method_name, spec in PURE_RL_CONFIRM_ROWS.items()
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


def _build_matrix(tmp_path: Path) -> dict[str, object]:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    confirm_path = _write_json(
        tmp_path / "three_dof_cross_family_confirm_report.json",
        _confirm_report_payload(),
    )
    benchmark_path = _write_json(
        tmp_path / "three_dof_benchmark_schema2_paper_teacher.json",
        _benchmark_report_payload(),
    )
    return build_3dof_evidence_matrix(
        confirm_report_path=confirm_path,
        benchmark_report_path=benchmark_path,
    )


def test_evidence_matrix_requires_complete_branch_a_confirm_report(tmp_path: Path) -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    confirm = _confirm_report_payload()
    confirm["selected_branch"] = "branch_b"
    confirm["method_summaries"] = confirm["method_summaries"][:-1]
    confirm_path = _write_json(tmp_path / "confirm.json", confirm)
    benchmark_path = _write_json(tmp_path / "benchmark.json", _benchmark_report_payload())

    with pytest.raises(ValueError, match="complete Branch A confirm report"):
        build_3dof_evidence_matrix(
            confirm_report_path=confirm_path,
            benchmark_report_path=benchmark_path,
        )


def test_evidence_matrix_includes_all_three_pure_rl_families(tmp_path: Path) -> None:
    matrix = _build_matrix(tmp_path)

    pure_rl_rows = [row for row in matrix["rows"] if row["method_family"] == "pure_rl"]
    assert [row["method_name"] for row in pure_rl_rows] == [
        "ppo_no_bc",
        "sac_no_bc",
        "td3_no_bc",
    ]
    assert all(row["source_contract"] == "nominal-only pilot" for row in pure_rl_rows)
    assert all(row["entered_contact"] is False for row in pure_rl_rows)


def test_evidence_matrix_includes_demo_supported_anchors(tmp_path: Path) -> None:
    matrix = _build_matrix(tmp_path)
    rows_by_method = {row["method_name"]: row for row in matrix["rows"]}

    assert rows_by_method["bc_only_stable_r32_p32"]["method_family"] == "imitation_anchor"
    assert (
        rows_by_method["repaired_mainline_bc_to_ppo"]["method_family"]
        == "demo_augmented_rl"
    )
    assert (
        rows_by_method["dapg_lite_repaired_mainline"]["method_family"]
        == "demo_augmented_rl"
    )
    assert rows_by_method["bc_only_stable_r32_p32"]["entered_contact"] is True
    assert rows_by_method["repaired_mainline_bc_to_ppo"]["success_rate"] == pytest.approx(1.0)


def test_evidence_matrix_marks_sac_as_distance_proxy_not_success(tmp_path: Path) -> None:
    matrix = _build_matrix(tmp_path)
    rows_by_method = {row["method_name"]: row for row in matrix["rows"]}

    sac_row = rows_by_method["sac_no_bc"]
    assert sac_row["mean_final_distance_mm"] == pytest.approx(16.67)
    assert sac_row["entered_contact"] is False
    assert sac_row["evidence_role"] == "contact_gate_negative"
    assert "distance proxy" in sac_row["allowed_claim"].lower()
    assert "solves insertion" in sac_row["not_allowed_claim"].lower()


def test_evidence_matrix_uses_confirm_report_best_distance_proxy_method(
    tmp_path: Path,
) -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    confirm = _confirm_report_payload()
    confirm["best_distance_proxy_method"] = "ppo_no_bc"
    confirm["method_summaries"][0]["best_final_distance_mm"] = 15.25
    confirm["method_summaries"][1]["best_final_distance_mm"] = 16.67
    confirm_path = _write_json(tmp_path / "confirm.json", confirm)
    benchmark_path = _write_json(tmp_path / "benchmark.json", _benchmark_report_payload())

    matrix = build_3dof_evidence_matrix(
        confirm_report_path=confirm_path,
        benchmark_report_path=benchmark_path,
    )
    rows_by_method = {row["method_name"]: row for row in matrix["rows"]}

    assert "distance proxy" in rows_by_method["ppo_no_bc"]["allowed_claim"].lower()
    assert "distance proxy" not in rows_by_method["sac_no_bc"]["allowed_claim"].lower()


def test_evidence_matrix_separates_nominal_pilot_from_five_profile_benchmark(
    tmp_path: Path,
) -> None:
    matrix = _build_matrix(tmp_path)
    rows_by_method = {row["method_name"]: row for row in matrix["rows"]}

    assert rows_by_method["ppo_no_bc"]["source_contract"] == "nominal-only pilot"
    assert (
        rows_by_method["bc_only_stable_r32_p32"]["source_contract"]
        == "five-profile benchmark"
    )
    assert matrix["matrix_contract"]["mixed_contracts"] is True
    assert "contact-gate contrast" in matrix["matrix_contract"]["allowed"]


def test_evidence_matrix_rejects_leaderboard_claim_across_mixed_contracts(
    tmp_path: Path,
) -> None:
    matrix = _build_matrix(tmp_path)

    assert "leaderboard" in matrix["matrix_contract"]["not_allowed"].lower()
    assert "leaderboard" in matrix["rows"][0]["not_allowed_claim"].lower()
    assert matrix["row_count"] >= 7


def test_sprint2_main_table_groups_rows_into_three_evidence_layers(
    tmp_path: Path,
) -> None:
    from vi_full.three_dof_evidence_matrix import (
        build_sprint2_main_table_from_evidence_matrix,
        render_sprint2_main_table_markdown,
    )

    matrix = _build_matrix(tmp_path)
    table = build_sprint2_main_table_from_evidence_matrix(matrix)
    layers_by_name = {layer["layer_name"]: layer for layer in table["layers"]}

    assert table["report_name"] == "three_dof_sprint2_main_table"
    assert table["table_contract"]["not_a_leaderboard"] is True
    assert table["row_count"] == 7
    assert [
        row["method_name"]
        for row in layers_by_name["pure_rl_nominal_only_negative"]["rows"]
    ] == ["ppo_no_bc", "sac_no_bc", "td3_no_bc"]
    assert [
        row["method_name"]
        for row in layers_by_name["demo_supported_contact_reopening"]["rows"]
    ] == [
        "bc_only_stable_r32_p32",
        "repaired_mainline_bc_to_ppo",
        "dapg_lite_repaired_mainline",
    ]
    assert [
        row["method_name"]
        for row in layers_by_name["mechanics_fixed_impedance_anchor"]["rows"]
    ] == ["fixed_impedance_rl_stable_r32_p32"]

    markdown = render_sprint2_main_table_markdown(table)
    assert "## Pure-RL nominal-only negative rows" in markdown
    assert "## Demo-supported contact-reopening rows" in markdown
    assert "## Mechanics / fixed-impedance anchor rows" in markdown
    assert "SAC w/o BC" in markdown
    assert "distance proxy" in markdown
    assert "not a leaderboard" in markdown.lower()


def test_sprint2_main_table_validates_evidence_matrix_alignment(
    tmp_path: Path,
) -> None:
    from vi_full.three_dof_evidence_matrix import (
        build_3dof_sprint2_main_table,
        export_3dof_evidence_matrix_json,
    )

    confirm_path = _write_json(tmp_path / "confirm.json", _confirm_report_payload())
    benchmark_path = _write_json(tmp_path / "benchmark.json", _benchmark_report_payload())
    evidence_path, _ = export_3dof_evidence_matrix_json(
        confirm_report_path=confirm_path,
        benchmark_report_path=benchmark_path,
        output_dir=tmp_path,
    )
    evidence_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence_payload["rows"][0]["success_rate"] = 1.0
    evidence_path.write_text(json.dumps(evidence_payload), encoding="utf-8")

    with pytest.raises(ValueError, match="does not match"):
        build_3dof_sprint2_main_table(
            confirm_report_path=confirm_path,
            benchmark_report_path=benchmark_path,
            evidence_matrix_path=evidence_path,
        )


def test_markdown_exposes_row_level_provenance_and_train_budget(tmp_path: Path) -> None:
    from vi_full.three_dof_evidence_matrix import render_3dof_evidence_matrix_markdown

    matrix = _build_matrix(tmp_path)
    markdown = render_3dof_evidence_matrix_markdown(matrix)

    assert "| Method | Family | Source contract | Train budget | Source report |" in markdown
    assert (
        "| PPO w/o BC | pure_rl | nominal-only pilot | 200000 | "
        f"{matrix['rows'][0]['source_report']} |"
    ) in markdown
    assert (
        "| BC-only (stable 32/32) | imitation_anchor | five-profile benchmark | "
        f"BC 32/32 | {matrix['rows'][3]['source_report']} |"
    ) in markdown


def test_evidence_matrix_prefers_suite_specific_train_budget_when_available(
    tmp_path: Path,
) -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    confirm_path = _write_json(tmp_path / "confirm.json", _confirm_report_payload())
    benchmark = _benchmark_report_payload()
    benchmark["learned_results"]["bc_only_stable_r32_p32"]["suite_run_kwargs"] = {
        "bc_rollout_episodes": 8,
        "bc_pretrain_steps": 16,
        "total_timesteps": 0,
    }
    benchmark["learned_results"]["fixed_impedance_rl_stable_r32_p32"][
        "suite_run_kwargs"
    ] = {
        "bc_rollout_episodes": 8,
        "bc_pretrain_steps": 16,
        "total_timesteps": 512,
    }
    benchmark_path = _write_json(tmp_path / "benchmark.json", benchmark)

    matrix = build_3dof_evidence_matrix(
        confirm_report_path=confirm_path,
        benchmark_report_path=benchmark_path,
    )
    rows_by_method = {row["method_name"]: row for row in matrix["rows"]}

    assert rows_by_method["bc_only_stable_r32_p32"]["train_budget"] == "BC 8/16"
    assert (
        rows_by_method["fixed_impedance_rl_stable_r32_p32"]["train_budget"]
        == "BC 8/16 + PPO 512"
    )


def test_evidence_matrix_rejects_incomplete_suite_specific_train_budget(
    tmp_path: Path,
) -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    confirm_path = _write_json(tmp_path / "confirm.json", _confirm_report_payload())
    benchmark = _benchmark_report_payload()
    benchmark["learned_results"]["fixed_impedance_rl_stable_r32_p32"][
        "suite_run_kwargs"
    ] = {
        "bc_rollout_episodes": 8,
        "total_timesteps": 512,
    }
    benchmark_path = _write_json(tmp_path / "benchmark.json", benchmark)

    with pytest.raises(ValueError, match="bc_pretrain_steps"):
        build_3dof_evidence_matrix(
            confirm_report_path=confirm_path,
            benchmark_report_path=benchmark_path,
        )


def test_contact_gate_figure_exposes_mixed_contract_boundary_and_train_budget(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import matplotlib.axes

    from vi_full.three_dof_evidence_matrix import export_contact_gate_matrix_figure

    matrix = _build_matrix(tmp_path)
    captured: dict[str, object] = {}

    original_set_title = matplotlib.axes.Axes.set_title
    original_set_yticks = matplotlib.axes.Axes.set_yticks

    def _capture_title(self, label, *args, **kwargs):
        captured["title"] = label
        return original_set_title(self, label, *args, **kwargs)

    def _capture_yticks(self, ticks, labels=None, *args, **kwargs):
        if labels is not None:
            captured["ytick_labels"] = list(labels)
        return original_set_yticks(self, ticks, labels, *args, **kwargs)

    monkeypatch.setattr(matplotlib.axes.Axes, "set_title", _capture_title)
    monkeypatch.setattr(matplotlib.axes.Axes, "set_yticks", _capture_yticks)

    export_contact_gate_matrix_figure(matrix, tmp_path)

    assert "mixed-contract contrast only" in str(captured["title"]).lower()
    assert "not a leaderboard" in str(captured["title"]).lower()
    ytick_labels = [str(label) for label in captured["ytick_labels"]]
    assert "nominal-only pilot; 200000" in ytick_labels[0]
    assert "five-profile benchmark; BC 32/32" in ytick_labels[3]


def test_evidence_matrix_rows_point_to_direct_input_artifacts(tmp_path: Path) -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    confirm_path = _write_json(
        tmp_path / "three_dof_cross_family_confirm_report.json",
        _confirm_report_payload(),
    )
    benchmark_path = _write_json(
        tmp_path / "three_dof_benchmark_schema2_paper_teacher.json",
        _benchmark_report_payload(),
    )

    matrix = build_3dof_evidence_matrix(
        confirm_report_path=confirm_path,
        benchmark_report_path=benchmark_path,
    )
    rows_by_method = {row["method_name"]: row for row in matrix["rows"]}
    expected_confirm = confirm_path.resolve().as_posix()
    expected_benchmark = benchmark_path.resolve().as_posix()

    for method_name in ("ppo_no_bc", "sac_no_bc", "td3_no_bc"):
        assert rows_by_method[method_name]["source_report"] == expected_confirm
    for method_name in (
        "bc_only_stable_r32_p32",
        "repaired_mainline_bc_to_ppo",
        "dapg_lite_repaired_mainline",
        "fixed_impedance_rl_stable_r32_p32",
    ):
        assert rows_by_method[method_name]["source_report"] == expected_benchmark
        assert rows_by_method[method_name]["source_artifact"] == expected_benchmark
        assert rows_by_method[method_name]["source_sha256"] == _sha256(benchmark_path)
        assert rows_by_method[method_name]["source_role"] == "benchmark_report_input"


def test_evidence_matrix_reads_benchmark_rows_from_manifest() -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    matrix = build_3dof_evidence_matrix(
        confirm_report_path=REPO_ROOT
        / "outputs"
        / "cross_family_confirm"
        / "three_dof_cross_family_confirm_report.json",
        manifest_path=CANONICAL_MANIFEST_PATH,
    )
    rows_by_method = {row["method_name"]: row for row in matrix["rows"]}
    manifest = json.loads(CANONICAL_MANIFEST_PATH.read_text(encoding="utf-8"))
    canonical = manifest["artifacts"]["canonical_main_benchmark"]
    canonical_report = json.loads((REPO_ROOT / canonical["path"]).read_text(encoding="utf-8"))

    assert matrix["source_artifacts"]["benchmark_manifest"] == (
        "artifacts/main_benchmark/main_benchmark_manifest.json"
    )
    assert matrix["source_artifacts"]["benchmark_report"] == CANONICAL_BENCHMARK

    for method_name in (
        "bc_only_stable_r32_p32",
        "repaired_mainline_bc_to_ppo",
        "dapg_lite_repaired_mainline",
        "fixed_impedance_rl_stable_r32_p32",
    ):
        row = rows_by_method[method_name]
        assert row["source_artifact"] == CANONICAL_BENCHMARK
        assert row["source_report"] == CANONICAL_BENCHMARK
        assert row["source_role"] == "canonical_main_benchmark"
        assert row["source_sha256"] == canonical["sha256"]
        assert SCHEMA2_DIAGNOSTIC not in row["source_artifact"]

    for method_name in ("dapg_lite_repaired_mainline", "fixed_impedance_rl_stable_r32_p32"):
        metrics = canonical_report["learned_results"][method_name]["five_profile_mean"]
        row = rows_by_method[method_name]
        assert row["success_rate"] == round(
            float(metrics["success_rate_mean_over_profiles"]), 3
        )
        assert row["mean_final_distance_mm"] == round(
            float(metrics["mean_final_distance_mean_over_profiles"]) * 1000.0,
            3,
        )


def test_sprint2_main_table_preserves_three_decimal_success_from_canonical_manifest() -> None:
    table = json.loads(
        (REPO_ROOT / "outputs" / "evidence_matrix" / "three_dof_sprint2_main_table.json").read_text(
            encoding="utf-8"
        )
    )
    rows_by_method = {row["method_name"]: row for row in table["rows"]}

    assert rows_by_method["fixed_impedance_rl_stable_r32_p32"]["success_rate"] == pytest.approx(0.947)
    assert rows_by_method["dapg_lite_repaired_mainline"]["success_rate"] == pytest.approx(1.000)


def test_evidence_matrix_uses_repo_relative_provenance_for_repo_local_inputs() -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    repo_root = Path(__file__).resolve().parents[2]
    staging_dir = Path(
        tempfile.mkdtemp(prefix="evidence-matrix-", dir=repo_root / "tmp")
    )
    try:
        confirm_path = _write_json(
            staging_dir / "confirm.json",
            _confirm_report_payload(),
        )
        benchmark_path = _write_json(
            staging_dir / "benchmark.json",
            _benchmark_report_payload(),
        )

        matrix = build_3dof_evidence_matrix(
            confirm_report_path=confirm_path,
            benchmark_report_path=benchmark_path,
        )
        rows_by_method = {row["method_name"]: row for row in matrix["rows"]}

        expected_confirm = confirm_path.relative_to(repo_root).as_posix()
        expected_benchmark = benchmark_path.relative_to(repo_root).as_posix()
        assert matrix["source_artifacts"]["confirm_report"] == expected_confirm
        assert matrix["source_artifacts"]["benchmark_report"] == expected_benchmark
        assert rows_by_method["ppo_no_bc"]["source_report"] == expected_confirm
        assert rows_by_method["bc_only_stable_r32_p32"]["source_report"] == expected_benchmark
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)


def test_evidence_matrix_rejects_missing_confirm_metrics(tmp_path: Path) -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    confirm = _confirm_report_payload()
    del confirm["method_summaries"][1]["best_final_distance_mm"]
    confirm_path = _write_json(tmp_path / "confirm.json", confirm)
    benchmark_path = _write_json(tmp_path / "benchmark.json", _benchmark_report_payload())

    with pytest.raises(ValueError, match="best_final_distance_mm"):
        build_3dof_evidence_matrix(
            confirm_report_path=confirm_path,
            benchmark_report_path=benchmark_path,
        )


def test_evidence_matrix_rejects_null_confirm_metrics(tmp_path: Path) -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    confirm = _confirm_report_payload()
    confirm["method_summaries"][1]["best_final_distance_mm"] = None
    confirm_path = _write_json(tmp_path / "confirm.json", confirm)
    benchmark_path = _write_json(tmp_path / "benchmark.json", _benchmark_report_payload())

    with pytest.raises(ValueError, match="best_final_distance_mm"):
        build_3dof_evidence_matrix(
            confirm_report_path=confirm_path,
            benchmark_report_path=benchmark_path,
        )


@pytest.mark.parametrize(
    "missing_field",
    ["mean_jam_rate_across_budgets", "mean_peak_force_across_budgets"],
)
def test_evidence_matrix_rejects_missing_confirm_zero_contact_metrics(
    tmp_path: Path,
    missing_field: str,
) -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    confirm = _confirm_report_payload()
    del confirm["method_summaries"][1][missing_field]
    confirm_path = _write_json(tmp_path / "confirm.json", confirm)
    benchmark_path = _write_json(tmp_path / "benchmark.json", _benchmark_report_payload())

    with pytest.raises(ValueError, match=missing_field):
        build_3dof_evidence_matrix(
            confirm_report_path=confirm_path,
            benchmark_report_path=benchmark_path,
        )


def test_evidence_matrix_rejects_branch_a_confirm_with_contact_entry(
    tmp_path: Path,
) -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    confirm = _confirm_report_payload()
    confirm["method_summaries"][1]["entered_contact"] = True
    confirm["method_summaries"][1]["mean_contact_steps_across_budgets"] = 3.0
    confirm_path = _write_json(tmp_path / "confirm.json", confirm)
    benchmark_path = _write_json(tmp_path / "benchmark.json", _benchmark_report_payload())

    with pytest.raises(ValueError, match="zero-contact and zero-success"):
        build_3dof_evidence_matrix(
            confirm_report_path=confirm_path,
            benchmark_report_path=benchmark_path,
        )


def test_evidence_matrix_rejects_branch_a_confirm_with_nonzero_success(
    tmp_path: Path,
) -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    confirm = _confirm_report_payload()
    confirm["method_summaries"][1]["mean_success_across_budgets"] = 0.05
    confirm_path = _write_json(tmp_path / "confirm.json", confirm)
    benchmark_path = _write_json(tmp_path / "benchmark.json", _benchmark_report_payload())

    with pytest.raises(ValueError, match="zero-contact and zero-success"):
        build_3dof_evidence_matrix(
            confirm_report_path=confirm_path,
            benchmark_report_path=benchmark_path,
        )


def test_evidence_matrix_rejects_missing_anchor_metrics(tmp_path: Path) -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    benchmark = _benchmark_report_payload()
    del benchmark["learned_results"]["bc_only_stable_r32_p32"]["five_profile_mean"][
        "mean_contact_steps_mean_over_profiles"
    ]
    confirm_path = _write_json(tmp_path / "confirm.json", _confirm_report_payload())
    benchmark_path = _write_json(tmp_path / "benchmark.json", benchmark)

    with pytest.raises(ValueError, match="mean_contact_steps_mean_over_profiles"):
        build_3dof_evidence_matrix(
            confirm_report_path=confirm_path,
            benchmark_report_path=benchmark_path,
        )


def test_evidence_matrix_rejects_null_anchor_metrics(tmp_path: Path) -> None:
    from vi_full.three_dof_evidence_matrix import build_3dof_evidence_matrix

    benchmark = _benchmark_report_payload()
    benchmark["learned_results"]["bc_only_stable_r32_p32"]["five_profile_mean"][
        "mean_contact_steps_mean_over_profiles"
    ] = None
    confirm_path = _write_json(tmp_path / "confirm.json", _confirm_report_payload())
    benchmark_path = _write_json(tmp_path / "benchmark.json", benchmark)

    with pytest.raises(ValueError, match="mean_contact_steps_mean_over_profiles"):
        build_3dof_evidence_matrix(
            confirm_report_path=confirm_path,
            benchmark_report_path=benchmark_path,
        )


def test_evidence_matrix_exports_are_deterministic_across_identical_reruns(
    tmp_path: Path,
) -> None:
    from vi_full.three_dof_evidence_matrix import export_3dof_evidence_matrix_artifacts

    confirm_path = _write_json(
        tmp_path / "three_dof_cross_family_confirm_report.json",
        _confirm_report_payload(),
    )
    benchmark_path = _write_json(
        tmp_path / "three_dof_benchmark_schema2_paper_teacher.json",
        _benchmark_report_payload(),
    )
    output_dir = tmp_path / "evidence_matrix"

    export_3dof_evidence_matrix_artifacts(
        confirm_report_path=confirm_path,
        benchmark_report_path=benchmark_path,
        output_dir=output_dir,
    )
    first_json = (output_dir / "three_dof_evidence_matrix.json").read_bytes()
    first_pdf = (output_dir / "three_dof_contact_gate_matrix.pdf").read_bytes()
    first_main_table_json = (
        output_dir / "three_dof_sprint2_main_table.json"
    ).read_bytes()
    first_main_table_csv = (
        output_dir / "three_dof_sprint2_main_table.csv"
    ).read_bytes()
    first_main_table_markdown = (
        output_dir / "three_dof_sprint2_main_table.md"
    ).read_bytes()

    time.sleep(1.1)

    export_3dof_evidence_matrix_artifacts(
        confirm_report_path=confirm_path,
        benchmark_report_path=benchmark_path,
        output_dir=output_dir,
    )
    second_json = (output_dir / "three_dof_evidence_matrix.json").read_bytes()
    second_pdf = (output_dir / "three_dof_contact_gate_matrix.pdf").read_bytes()
    second_main_table_json = (
        output_dir / "three_dof_sprint2_main_table.json"
    ).read_bytes()
    second_main_table_csv = (
        output_dir / "three_dof_sprint2_main_table.csv"
    ).read_bytes()
    second_main_table_markdown = (
        output_dir / "three_dof_sprint2_main_table.md"
    ).read_bytes()

    assert second_json == first_json
    assert second_pdf == first_pdf
    assert second_main_table_json == first_main_table_json
    assert second_main_table_csv == first_main_table_csv
    assert second_main_table_markdown == first_main_table_markdown


def test_sprint2_main_table_uses_portable_evidence_reference_for_external_output(
    tmp_path: Path,
) -> None:
    from vi_full.three_dof_evidence_matrix import export_3dof_evidence_matrix_artifacts

    confirm_path = _write_json(
        tmp_path / "three_dof_cross_family_confirm_report.json",
        _confirm_report_payload(),
    )
    benchmark_path = _write_json(
        tmp_path / "three_dof_benchmark_schema2_paper_teacher.json",
        _benchmark_report_payload(),
    )
    output_dir = tmp_path / "external_evidence_matrix"

    artifacts = export_3dof_evidence_matrix_artifacts(
        confirm_report_path=confirm_path,
        benchmark_report_path=benchmark_path,
        output_dir=output_dir,
    )
    sprint2_paths = artifacts["sprint2_main_table"]
    table = json.loads(sprint2_paths["json"].read_text(encoding="utf-8"))
    evidence_source = table["source_artifacts"]["evidence_matrix"]

    assert evidence_source == "three_dof_evidence_matrix.json"
    assert not Path(evidence_source).is_absolute()
    assert table["source_hashes"]["evidence_matrix"] == _sha256(artifacts["json"])
    markdown = sprint2_paths["markdown"].read_text(encoding="utf-8")
    assert f"Evidence-matrix source: `{evidence_source}`" in markdown
    assert artifacts["json"].resolve().as_posix() not in markdown
