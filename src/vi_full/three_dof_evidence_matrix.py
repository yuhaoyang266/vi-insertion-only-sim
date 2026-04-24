from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]

PURE_RL_METHOD_ORDER = (
    "ppo_no_bc",
    "sac_no_bc",
    "td3_no_bc",
)

ANCHOR_SPECS = {
    "bc_only_stable_r32_p32": {
        "label": "BC-only (stable 32/32)",
        "method_family": "imitation_anchor",
        "evidence_role": "support_reopens_contact",
    },
    "repaired_mainline_bc_to_ppo": {
        "label": "BC -> PPO",
        "method_family": "demo_augmented_rl",
        "evidence_role": "support_reopens_contact",
    },
    "dapg_lite_repaired_mainline": {
        "label": "DAPG-lite",
        "method_family": "demo_augmented_rl",
        "evidence_role": "support_reopens_contact",
    },
    "fixed_impedance_rl_stable_r32_p32": {
        "label": "Fixed-impedance RL (stable BC 32/32)",
        "method_family": "fixed_impedance",
        "evidence_role": "mechanics_anchor",
    },
}

ROW_FIELD_ORDER = [
    "method_name",
    "label",
    "method_family",
    "source_contract",
    "benchmark",
    "train_budget",
    "entered_contact",
    "success_rate",
    "mean_final_distance_mm",
    "mean_contact_steps",
    "jam_rate",
    "mean_peak_contact_force_n",
    "evidence_role",
    "allowed_claim",
    "not_allowed_claim",
    "source_report",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_hashes(source_artifacts: dict[str, str | None]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for source_name, source_path in source_artifacts.items():
        if source_path is None:
            continue
        path = Path(source_path)
        if not path.is_absolute():
            path = REPO_ROOT / path
        hashes[source_name] = _sha256(path)
    return hashes


def _git_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return completed.stdout.strip()

SPRINT2_MAIN_TABLE_LAYERS = (
    {
        "layer_name": "pure_rl_nominal_only_negative",
        "title": "Pure-RL nominal-only negative rows",
        "method_names": PURE_RL_METHOD_ORDER,
        "summary": (
            "Pure-RL rows from the nominal-only Branch-A confirm contract; "
            "these rows stay outside useful contact."
        ),
    },
    {
        "layer_name": "demo_supported_contact_reopening",
        "title": "Demo-supported contact-reopening rows",
        "method_names": (
            "bc_only_stable_r32_p32",
            "repaired_mainline_bc_to_ppo",
            "dapg_lite_repaired_mainline",
        ),
        "summary": (
            "Five-profile benchmark rows showing that demonstration support "
            "reopens contact and non-zero success."
        ),
    },
    {
        "layer_name": "mechanics_fixed_impedance_anchor",
        "title": "Mechanics / fixed-impedance anchor rows",
        "method_names": ("fixed_impedance_rl_stable_r32_p32",),
        "summary": (
            "Five-profile fixed-impedance row retained as a mechanics anchor, "
            "not as a leaderboard entry."
        ),
    },
)

SPRINT2_MAIN_TABLE_FIELD_ORDER = [
    "layer_name",
    "layer_title",
    *ROW_FIELD_ORDER,
]

PDF_METADATA = {
    "CreationDate": None,
    "ModDate": None,
}

CONTACT_GATE_FIGURE_TITLE = (
    "3DoF contact gate evidence matrix\n"
    "Mixed-contract contrast only; not a leaderboard."
)

CONFIRM_SUMMARY_REQUIRED_FIELDS = (
    "best_budget",
    "best_final_distance_mm",
    "entered_contact",
    "mean_success_across_budgets",
    "mean_contact_steps_across_budgets",
    "mean_jam_rate_across_budgets",
    "mean_peak_force_across_budgets",
)

BENCHMARK_CONFIG_REQUIRED_FIELDS = (
    "timesteps",
    "base_bc_rollout_episodes",
    "base_bc_pretrain_steps",
)

BENCHMARK_SUITE_RUN_BUDGET_REQUIRED_FIELDS = (
    "total_timesteps",
    "bc_rollout_episodes",
    "bc_pretrain_steps",
)

BENCHMARK_FIVE_PROFILE_REQUIRED_FIELDS = (
    "success_rate_mean_over_profiles",
    "mean_final_distance_mean_over_profiles",
    "jam_rate_mean_over_profiles",
    "mean_peak_contact_force_mean_over_profiles",
    "mean_contact_steps_mean_over_profiles",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _provenance_path(path: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def _as_float(value: object) -> float:
    if value is None:
        return 0.0
    return float(value)


def _round_metric(value: object) -> float:
    return round(_as_float(value), 2)


def _require_field(mapping: dict[str, Any], field_name: str, *, context: str) -> Any:
    if field_name not in mapping:
        raise ValueError(
            f"Evidence matrix missing required field '{field_name}' in {context}."
        )
    value = mapping[field_name]
    if value is None:
        raise ValueError(
            f"Evidence matrix missing required field '{field_name}' in {context}."
        )
    return value


def _validate_confirm_report(confirm: dict[str, Any]) -> None:
    if not bool(confirm.get("grid_complete")):
        raise ValueError("Evidence matrix requires a complete Branch A confirm report.")
    if str(confirm.get("selected_branch")) != "branch_a":
        raise ValueError("Evidence matrix requires a complete Branch A confirm report.")

    summaries = {
        str(row["method_name"]): row for row in confirm.get("method_summaries", [])
    }
    missing_methods = [
        method_name for method_name in PURE_RL_METHOD_ORDER if method_name not in summaries
    ]
    if missing_methods:
        raise ValueError("Evidence matrix requires a complete Branch A confirm report.")

    best_distance_proxy_method = str(
        _require_field(
            confirm,
            "best_distance_proxy_method",
            context="confirm report",
        )
    )
    if best_distance_proxy_method not in PURE_RL_METHOD_ORDER:
        raise ValueError(
            "Evidence matrix requires best_distance_proxy_method to name one of the pure-RL rows."
        )

    for method_name in PURE_RL_METHOD_ORDER:
        summary = summaries[method_name]
        for field_name in CONFIRM_SUMMARY_REQUIRED_FIELDS:
            _require_field(
                summary,
                field_name,
                context=f"confirm summary '{method_name}'",
            )
        entered_contact = bool(summary["entered_contact"])
        mean_success = _as_float(summary["mean_success_across_budgets"])
        mean_contact_steps = _as_float(summary["mean_contact_steps_across_budgets"])
        if entered_contact or mean_success != 0.0 or mean_contact_steps != 0.0:
            raise ValueError(
                "Evidence matrix requires Branch A confirm rows to remain "
                "zero-contact and zero-success, but "
                f"'{method_name}' reported entered_contact={entered_contact}, "
                f"mean_success_across_budgets={mean_success}, "
                f"mean_contact_steps_across_budgets={mean_contact_steps}."
            )


def _validate_benchmark_report(benchmark: dict[str, Any]) -> None:
    learned_results = dict(benchmark.get("learned_results", {}))
    missing_suites = [
        suite_name for suite_name in ANCHOR_SPECS if suite_name not in learned_results
    ]
    if missing_suites:
        raise ValueError(
            "Evidence matrix requires all demo-supported anchors in the benchmark report."
        )

    config = dict(benchmark.get("config", {}))
    for field_name in BENCHMARK_CONFIG_REQUIRED_FIELDS:
        _require_field(
            config,
            field_name,
            context="benchmark config",
        )

    for suite_name in ANCHOR_SPECS:
        suite_payload = dict(learned_results[suite_name])
        metrics = dict(
            _require_field(
                suite_payload,
                "five_profile_mean",
                context=f"benchmark suite '{suite_name}'",
            )
        )
        for field_name in BENCHMARK_FIVE_PROFILE_REQUIRED_FIELDS:
            _require_field(
                metrics,
                field_name,
                context=f"benchmark suite '{suite_name}'",
            )
        _benchmark_train_budget(suite_name, suite_payload, config)


def _pure_rl_allowed_claim(
    method_name: str,
    *,
    best_distance_proxy_method: str,
) -> str:
    if method_name == best_distance_proxy_method:
        return (
            "Best pure-RL distance proxy under the nominal-only pilot contract, but still zero-contact."
        )
    return "Pure RL stays outside the useful-contact gate under the nominal-only pilot contract."


def _pure_rl_not_allowed_claim(
    method_name: str,
    *,
    best_distance_proxy_method: str,
    label: str,
) -> str:
    if method_name == best_distance_proxy_method:
        return (
            f"Do not claim {label} solves insertion, enters useful contact, "
            "or wins a mixed-contract leaderboard."
        )
    return "Do not claim this method reaches useful contact or compare it as a mixed-contract leaderboard winner."


def _anchor_allowed_claim(method_name: str) -> str:
    if method_name == "bc_only_stable_r32_p32":
        return "Demonstration support alone reopens contact and near-ceiling success under the five-profile benchmark."
    if method_name == "fixed_impedance_rl_stable_r32_p32":
        return "Fixed impedance still enters contact and succeeds under support, so this row acts as a mechanics anchor."
    return "Demo-supported RL reopens contact and non-zero success under the five-profile benchmark."


def _anchor_not_allowed_claim(method_name: str) -> str:
    if method_name == "fixed_impedance_rl_stable_r32_p32":
        return "Do not read this row as proof that impedance type alone determines learnability or as a mixed-contract leaderboard winner."
    return "Do not compare this row as a mixed-contract leaderboard winner against nominal-only pure-RL pilot rows."


def _build_pure_rl_rows(
    confirm: dict[str, Any],
    *,
    confirm_report_path: Path,
) -> list[dict[str, Any]]:
    summaries = {
        str(row["method_name"]): row for row in confirm.get("method_summaries", [])
    }
    best_distance_proxy_method = str(confirm["best_distance_proxy_method"])
    direct_source = _provenance_path(confirm_report_path)
    rows: list[dict[str, Any]] = []
    for method_name in PURE_RL_METHOD_ORDER:
        summary = summaries[method_name]
        label = str(summary.get("label", method_name))

        jam_rate = _round_metric(
            _require_field(
                summary,
                "mean_jam_rate_across_budgets",
                context=f"confirm summary '{method_name}'",
            )
        )
        peak_force = _round_metric(
            _require_field(
                summary,
                "mean_peak_force_across_budgets",
                context=f"confirm summary '{method_name}'",
            )
        )
        if jam_rate != 0.0:
            raise ValueError(
                f"Branch A pure-RL row '{method_name}' reports jam_rate={jam_rate}, "
                "expected 0.0 under the zero-contact contract."
            )
        if peak_force != 0.0:
            raise ValueError(
                f"Branch A pure-RL row '{method_name}' reports peak_force={peak_force}, "
                "expected 0.0 under the zero-contact contract."
            )

        rows.append(
            {
                "method_name": method_name,
                "label": label,
                "method_family": "pure_rl",
                "source_contract": "nominal-only pilot",
                "benchmark": "3dof_cross_family_confirm",
                "train_budget": str(int(summary.get("best_budget", 0))),
                "entered_contact": bool(summary.get("entered_contact")),
                "success_rate": _round_metric(
                    summary.get("mean_success_across_budgets", 0.0)
                ),
                "mean_final_distance_mm": _round_metric(
                    summary.get("best_final_distance_mm", 0.0)
                ),
                "mean_contact_steps": _round_metric(
                    summary.get("mean_contact_steps_across_budgets", 0.0)
                ),
                "jam_rate": jam_rate,
                "mean_peak_contact_force_n": peak_force,
                "evidence_role": "contact_gate_negative",
                "allowed_claim": _pure_rl_allowed_claim(
                    method_name,
                    best_distance_proxy_method=best_distance_proxy_method,
                ),
                "not_allowed_claim": _pure_rl_not_allowed_claim(
                    method_name,
                    best_distance_proxy_method=best_distance_proxy_method,
                    label=label,
                ),
                "source_report": direct_source,
            }
        )
    return rows


def _extract_benchmark_metrics(suite_payload: dict[str, Any]) -> dict[str, float]:
    metrics = dict(
        _require_field(
            suite_payload,
            "five_profile_mean",
            context="benchmark suite payload",
        )
    )
    return {
        "success_rate": _round_metric(
            _require_field(
                metrics,
                "success_rate_mean_over_profiles",
                context="benchmark five_profile_mean",
            )
        ),
        "mean_final_distance_mm": _round_metric(
            1000.0
            * _as_float(
                _require_field(
                    metrics,
                    "mean_final_distance_mean_over_profiles",
                    context="benchmark five_profile_mean",
                )
            )
        ),
        "jam_rate": _round_metric(
            _require_field(
                metrics,
                "jam_rate_mean_over_profiles",
                context="benchmark five_profile_mean",
            )
        ),
        "mean_peak_contact_force_n": _round_metric(
            _require_field(
                metrics,
                "mean_peak_contact_force_mean_over_profiles",
                context="benchmark five_profile_mean",
            )
        ),
        "mean_contact_steps": _round_metric(
            _require_field(
                metrics,
                "mean_contact_steps_mean_over_profiles",
                context="benchmark five_profile_mean",
            )
        ),
    }


def _benchmark_budget_values(
    suite_name: str,
    suite_payload: dict[str, Any],
    config: dict[str, Any],
) -> tuple[int, int, int]:
    if "suite_run_kwargs" in suite_payload:
        suite_run_kwargs = dict(
            _require_field(
                suite_payload,
                "suite_run_kwargs",
                context=f"benchmark suite '{suite_name}'",
            )
        )
        for field_name in BENCHMARK_SUITE_RUN_BUDGET_REQUIRED_FIELDS:
            _require_field(
                suite_run_kwargs,
                field_name,
                context=f"benchmark suite '{suite_name}' suite_run_kwargs",
            )
        return (
            int(suite_run_kwargs["bc_rollout_episodes"]),
            int(suite_run_kwargs["bc_pretrain_steps"]),
            int(suite_run_kwargs["total_timesteps"]),
        )
    return (
        int(
            _require_field(
                config,
                "base_bc_rollout_episodes",
                context="benchmark config",
            )
        ),
        int(
            _require_field(
                config,
                "base_bc_pretrain_steps",
                context="benchmark config",
            )
        ),
        int(_require_field(config, "timesteps", context="benchmark config")),
    )


def _benchmark_train_budget(
    suite_name: str,
    suite_payload: dict[str, Any],
    config: dict[str, Any],
) -> str:
    bc_rollouts, bc_pretrain, timesteps = _benchmark_budget_values(
        suite_name,
        suite_payload,
        config,
    )
    bc_text = f"BC {bc_rollouts}/{bc_pretrain}"
    if suite_name == "bc_only_stable_r32_p32":
        return bc_text
    if suite_name == "dapg_lite_repaired_mainline":
        return f"{bc_text} + DAPG-lite {timesteps}"
    return f"{bc_text} + PPO {timesteps}"


def _build_anchor_rows(
    benchmark: dict[str, Any],
    *,
    benchmark_report_path: Path,
) -> list[dict[str, Any]]:
    learned_results = dict(benchmark.get("learned_results", {}))
    config = dict(benchmark.get("config", {}))
    rows: list[dict[str, Any]] = []
    for method_name, spec in ANCHOR_SPECS.items():
        suite_payload = dict(learned_results[method_name])
        metrics = _extract_benchmark_metrics(suite_payload)
        rows.append(
            {
                "method_name": method_name,
                "label": spec["label"],
                "method_family": spec["method_family"],
                "source_contract": "five-profile benchmark",
                "benchmark": "3dof_main_benchmark",
                "train_budget": _benchmark_train_budget(
                    method_name,
                    suite_payload,
                    config,
                ),
                "entered_contact": metrics["mean_contact_steps"] > 0.0
                or metrics["success_rate"] > 0.0,
                "success_rate": metrics["success_rate"],
                "mean_final_distance_mm": metrics["mean_final_distance_mm"],
                "mean_contact_steps": metrics["mean_contact_steps"],
                "jam_rate": metrics["jam_rate"],
                "mean_peak_contact_force_n": metrics["mean_peak_contact_force_n"],
                "evidence_role": spec["evidence_role"],
                "allowed_claim": _anchor_allowed_claim(method_name),
                "not_allowed_claim": _anchor_not_allowed_claim(method_name),
                "source_report": _provenance_path(benchmark_report_path),
            }
        )
    return rows


def build_3dof_evidence_matrix(
    *,
    confirm_report_path: Path,
    benchmark_report_path: Path,
) -> dict[str, Any]:
    confirm_report_path = Path(confirm_report_path)
    benchmark_report_path = Path(benchmark_report_path)
    confirm = _load_json(confirm_report_path)
    benchmark = _load_json(benchmark_report_path)

    _validate_confirm_report(confirm)
    _validate_benchmark_report(benchmark)

    rows = _build_pure_rl_rows(
        confirm,
        confirm_report_path=confirm_report_path,
    ) + _build_anchor_rows(
        benchmark,
        benchmark_report_path=benchmark_report_path,
    )
    source_artifacts = {
        "confirm_report": _provenance_path(confirm_report_path),
        "benchmark_report": _provenance_path(benchmark_report_path),
    }
    return {
        "report_name": "three_dof_evidence_matrix",
        "export_name": "three_dof_evidence_matrix",
        "schema_version": 1,
        "source_artifacts": source_artifacts,
        "source_hashes": _source_hashes(source_artifacts),
        "generating_command": "python scripts/experiments/export_3dof_evidence_matrix.py",
        "git_commit": _git_commit(),
        "matrix_contract": {
            "mixed_contracts": True,
            "allowed": (
                "Use only for contact-gate contrast across nominal-only pilot and five-profile benchmark evidence."
            ),
            "not_allowed": (
                "Do not read this matrix as a mixed-contract leaderboard or direct across-row ranking."
            ),
            "row_source_rule": (
                "Each row cites the direct confirm or benchmark JSON input passed to the exporter; "
                "do not infer row provenance from separate paper table exports."
            ),
        },
        "row_count": len(rows),
        "row_order": [row["method_name"] for row in rows],
        "rows": rows,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def export_3dof_evidence_matrix_json(
    *,
    confirm_report_path: Path,
    benchmark_report_path: Path,
    output_dir: Path,
    stem: str = "three_dof_evidence_matrix",
) -> tuple[Path, dict[str, Any]]:
    payload = build_3dof_evidence_matrix(
        confirm_report_path=confirm_report_path,
        benchmark_report_path=benchmark_report_path,
    )
    json_path = Path(output_dir) / f"{stem}.json"
    return _write_json(json_path, payload), payload


def export_3dof_evidence_matrix_csv(
    payload: dict[str, Any],
    output_dir: Path,
    filename: str = "three_dof_evidence_matrix.csv",
) -> Path:
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELD_ORDER)
        writer.writeheader()
        for row in payload["rows"]:
            writer.writerow({field: row[field] for field in ROW_FIELD_ORDER})
    return output_path


def render_3dof_evidence_matrix_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 3DoF Evidence Matrix",
        "",
        f"Confirm source: `{payload['source_artifacts']['confirm_report']}`",
        f"Benchmark source: `{payload['source_artifacts']['benchmark_report']}`",
        "",
        "## Mixed-Contract Boundary",
        "",
        f"- Allowed: {payload['matrix_contract']['allowed']}",
        f"- Not allowed: {payload['matrix_contract']['not_allowed']}",
        f"- Row sources: {payload['matrix_contract']['row_source_rule']}",
        "",
        "## Matrix",
        "",
        "| Method | Family | Source contract | Train budget | Source report | Contact? | Success | Final dist (mm) | Contact steps | Role |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| "
            f"{row['label']} | "
            f"{row['method_family']} | "
            f"{row['source_contract']} | "
            f"{row['train_budget']} | "
            f"{row['source_report']} | "
            f"{'yes' if row['entered_contact'] else 'no'} | "
            f"{row['success_rate']:.2f} | "
            f"{row['mean_final_distance_mm']:.2f} | "
            f"{row['mean_contact_steps']:.2f} | "
            f"{row['evidence_role']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for row in payload["rows"]:
        lines.append(f"- `{row['method_name']}` allowed: {row['allowed_claim']}")
        lines.append(f"- `{row['method_name']}` not allowed: {row['not_allowed_claim']}")
    return "\n".join(lines) + "\n"


def _validate_evidence_matrix_payload(payload: dict[str, Any]) -> None:
    if payload.get("report_name") != "three_dof_evidence_matrix":
        raise ValueError("Sprint 2 main table requires a 3DoF evidence matrix payload.")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("Sprint 2 main table requires evidence-matrix rows.")
    rows_by_method = {
        str(row.get("method_name")): row
        for row in rows
        if isinstance(row, dict) and row.get("method_name") is not None
    }
    missing_methods = [
        method_name
        for layer in SPRINT2_MAIN_TABLE_LAYERS
        for method_name in layer["method_names"]
        if method_name not in rows_by_method
    ]
    if missing_methods:
        raise ValueError(
            "Sprint 2 main table requires all evidence-layer rows; missing "
            + ", ".join(missing_methods)
            + "."
        )
    matrix_contract = payload.get("matrix_contract")
    if not isinstance(matrix_contract, dict) or not bool(
        matrix_contract.get("mixed_contracts")
    ):
        raise ValueError("Sprint 2 main table requires mixed-contract boundary metadata.")


def build_sprint2_main_table_from_evidence_matrix(
    payload: dict[str, Any],
    *,
    evidence_matrix_path: Path | None = None,
) -> dict[str, Any]:
    _validate_evidence_matrix_payload(payload)
    rows_by_method = {str(row["method_name"]): row for row in payload["rows"]}
    layers: list[dict[str, Any]] = []
    flat_rows: list[dict[str, Any]] = []
    for layer_spec in SPRINT2_MAIN_TABLE_LAYERS:
        layer_rows = [
            dict(rows_by_method[str(method_name)])
            for method_name in layer_spec["method_names"]
        ]
        layer_payload = {
            "layer_name": layer_spec["layer_name"],
            "title": layer_spec["title"],
            "summary": layer_spec["summary"],
            "row_order": [row["method_name"] for row in layer_rows],
            "rows": layer_rows,
        }
        layers.append(layer_payload)
        for row in layer_rows:
            flat_row = {
                "layer_name": layer_payload["layer_name"],
                "layer_title": layer_payload["title"],
                **row,
            }
            flat_rows.append(flat_row)

    source_artifacts = dict(payload.get("source_artifacts", {}))
    source_artifacts["evidence_matrix"] = (
        _provenance_path(Path(evidence_matrix_path))
        if evidence_matrix_path is not None
        else None
    )
    source_hashes = _source_hashes(source_artifacts)
    matrix_contract = dict(payload["matrix_contract"])
    return {
        "report_name": "three_dof_sprint2_main_table",
        "export_name": "three_dof_sprint2_main_table",
        "schema_version": 1,
        "source_artifacts": source_artifacts,
        "source_hashes": source_hashes,
        "generating_command": "python scripts/experiments/export_3dof_evidence_matrix.py",
        "git_commit": _git_commit(),
        "table_contract": {
            "three_layer_table": True,
            "not_a_leaderboard": True,
            "allowed": matrix_contract["allowed"],
            "not_allowed": matrix_contract["not_allowed"],
            "row_source_rule": matrix_contract["row_source_rule"],
            "summary": (
                "Use as a three-layer reviewer-facing main table: pure-RL "
                "nominal-only negatives, demo-supported contact reopening, "
                "and a mechanics fixed-impedance anchor."
            ),
        },
        "row_count": len(flat_rows),
        "layers": layers,
        "rows": flat_rows,
    }


def _require_evidence_matrix_alignment(
    *,
    loaded_payload: dict[str, Any],
    expected_payload: dict[str, Any],
) -> None:
    checked_fields = (
        "source_artifacts",
        "matrix_contract",
        "row_count",
        "row_order",
        "rows",
    )
    for field_name in checked_fields:
        if loaded_payload.get(field_name) != expected_payload.get(field_name):
            raise ValueError(
                "Sprint 2 evidence matrix input does not match the confirm "
                f"and benchmark inputs at '{field_name}'."
            )


def build_3dof_sprint2_main_table(
    *,
    confirm_report_path: Path,
    benchmark_report_path: Path,
    evidence_matrix_path: Path | None = None,
) -> dict[str, Any]:
    expected_payload = build_3dof_evidence_matrix(
        confirm_report_path=confirm_report_path,
        benchmark_report_path=benchmark_report_path,
    )
    if evidence_matrix_path is None:
        matrix_payload = expected_payload
    else:
        matrix_payload = _load_json(Path(evidence_matrix_path))
        _require_evidence_matrix_alignment(
            loaded_payload=matrix_payload,
            expected_payload=expected_payload,
        )
    return build_sprint2_main_table_from_evidence_matrix(
        matrix_payload,
        evidence_matrix_path=evidence_matrix_path,
    )


def render_sprint2_main_table_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Sprint 2 Main Table",
        "",
        f"Confirm source: `{payload['source_artifacts']['confirm_report']}`",
        f"Evidence-matrix source: `{payload['source_artifacts']['evidence_matrix']}`",
        f"Benchmark source: `{payload['source_artifacts']['benchmark_report']}`",
        "",
        "## Boundary",
        "",
        f"- Allowed: {payload['table_contract']['allowed']}",
        f"- Not allowed: {payload['table_contract']['not_allowed']}",
        "- Main-table reading: three evidence layers, not a leaderboard.",
        "",
    ]
    for layer in payload["layers"]:
        lines.extend(
            [
                f"## {layer['title']}",
                "",
                str(layer["summary"]),
                "",
                "| Method | Source contract | Train budget | Contact? | Success | Final dist (mm) | Contact steps | Role | Claim boundary |",
                "| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
            ]
        )
        for row in layer["rows"]:
            lines.append(
                "| "
                f"{row['label']} | "
                f"{row['source_contract']} | "
                f"{row['train_budget']} | "
                f"{'yes' if row['entered_contact'] else 'no'} | "
                f"{row['success_rate']:.2f} | "
                f"{row['mean_final_distance_mm']:.2f} | "
                f"{row['mean_contact_steps']:.2f} | "
                f"{row['evidence_role']} | "
                f"{row['allowed_claim']} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _contact_gate_figure_row_label(row: dict[str, Any]) -> str:
    return (
        f"{row['label']}\n"
        f"[{row['source_contract']}; {row['train_budget']}]"
    )


def export_3dof_evidence_matrix_markdown(
    payload: dict[str, Any],
    output_dir: Path,
    filename: str = "three_dof_evidence_matrix.md",
) -> Path:
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_3dof_evidence_matrix_markdown(payload),
        encoding="utf-8",
    )
    return output_path


def export_contact_gate_matrix_figure(
    payload: dict[str, Any],
    output_dir: Path,
    stem: str = "three_dof_contact_gate_matrix",
) -> tuple[Path, Path]:
    rows = list(payload["rows"])
    matrix = [
        [1.0 if row["entered_contact"] else 0.0, _as_float(row["success_rate"])]
        for row in rows
    ]
    fig_height = max(4.8, 0.8 * len(rows))
    fig, ax = plt.subplots(figsize=(7.8, fig_height), constrained_layout=True)
    image = ax.imshow(matrix, aspect="auto", cmap="YlGn", vmin=0.0, vmax=1.0)
    ax.set_title(CONTACT_GATE_FIGURE_TITLE)
    ax.set_xticks([0, 1], ["Entered contact", "Success rate"])
    ax.set_yticks(
        list(range(len(rows))),
        [_contact_gate_figure_row_label(row) for row in rows],
    )
    for row_index, row in enumerate(rows):
        ax.text(
            0,
            row_index,
            "yes" if row["entered_contact"] else "no",
            ha="center",
            va="center",
            color="black",
            fontsize=9,
        )
        ax.text(
            1,
            row_index,
            f"{row['success_rate']:.2f}",
            ha="center",
            va="center",
            color="black",
            fontsize=9,
        )
    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("0 to 1 scale")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / f"{stem}.png"
    pdf_path = output_dir / f"{stem}.pdf"
    fig.savefig(png_path, dpi=200)
    fig.savefig(pdf_path, metadata=PDF_METADATA)
    plt.close(fig)
    return png_path, pdf_path


def export_sprint2_main_table_json(
    payload: dict[str, Any],
    output_dir: Path,
    stem: str = "three_dof_sprint2_main_table",
) -> Path:
    return _write_json(Path(output_dir) / f"{stem}.json", payload)


def export_sprint2_main_table_csv(
    payload: dict[str, Any],
    output_dir: Path,
    filename: str = "three_dof_sprint2_main_table.csv",
) -> Path:
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SPRINT2_MAIN_TABLE_FIELD_ORDER)
        writer.writeheader()
        for row in payload["rows"]:
            writer.writerow(
                {field: row[field] for field in SPRINT2_MAIN_TABLE_FIELD_ORDER}
            )
    return output_path


def export_sprint2_main_table_markdown(
    payload: dict[str, Any],
    output_dir: Path,
    filename: str = "three_dof_sprint2_main_table.md",
) -> Path:
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_sprint2_main_table_markdown(payload),
        encoding="utf-8",
    )
    return output_path


def export_sprint2_main_table_artifacts(
    payload: dict[str, Any],
    output_dir: Path,
) -> dict[str, Path]:
    json_path = export_sprint2_main_table_json(payload, output_dir)
    csv_path = export_sprint2_main_table_csv(payload, output_dir)
    markdown_path = export_sprint2_main_table_markdown(payload, output_dir)
    return {
        "json": json_path,
        "csv": csv_path,
        "markdown": markdown_path,
    }


def export_3dof_sprint2_main_table(
    *,
    confirm_report_path: Path,
    benchmark_report_path: Path,
    output_dir: Path,
    evidence_matrix_path: Path | None = None,
) -> dict[str, Path]:
    payload = build_3dof_sprint2_main_table(
        confirm_report_path=confirm_report_path,
        benchmark_report_path=benchmark_report_path,
        evidence_matrix_path=evidence_matrix_path,
    )
    return export_sprint2_main_table_artifacts(payload, output_dir)


def export_3dof_evidence_matrix_artifacts(
    *,
    confirm_report_path: Path,
    benchmark_report_path: Path,
    output_dir: Path,
) -> dict[str, Path | tuple[Path, Path]]:
    json_path, payload = export_3dof_evidence_matrix_json(
        confirm_report_path=confirm_report_path,
        benchmark_report_path=benchmark_report_path,
        output_dir=output_dir,
    )
    csv_path = export_3dof_evidence_matrix_csv(payload, output_dir)
    markdown_path = export_3dof_evidence_matrix_markdown(payload, output_dir)
    figure_paths = export_contact_gate_matrix_figure(payload, output_dir)
    sprint2_main_table = export_sprint2_main_table_artifacts(
        build_sprint2_main_table_from_evidence_matrix(
            payload,
            evidence_matrix_path=json_path,
        ),
        output_dir,
    )
    return {
        "json": json_path,
        "csv": csv_path,
        "markdown": markdown_path,
        "contact_gate_matrix": figure_paths,
        "sprint2_main_table": sprint2_main_table,
    }
