## Review Repair Plan (2026-04-29)

> **Scope:** repair plan from the combined project review, with priority on recent Stage 4 artifact/export changes. The goal is to remove the reproducible exporter regression, strengthen checks around newly generated CSV outputs, and keep paper-facing artifacts synchronized without changing the scientific claims.
>
> **Companion task list:** `docs/plans/2026-04-29-review-repair-task-list.md`.

### 1. Review Inputs

**User review direction**

- Review the whole project, especially recent changes.
- Produce a concrete repair plan and task file rather than patching immediately.
- Keep the repair surface focused on current paper/export reliability.

**Agent review findings**

- Full project test run fails with one regression: `export_3dof_paper_table(..., statistics_report_path=None)` now crashes with `KeyError: 'five_profile_statistics'`.
- The regression is caused by the new CSV writer in `src/vi_full/paper_tables.py`, which assumes statistics are always attached while the existing Markdown path supports no-statistics exports.
- `python scripts/export/build_paper_assets.py --check` passes because the canonical manifest path includes statistics and because table check mode currently compares JSON, Markdown, and LaTeX only, not the newly written CSV.
- Focused recent-change tests passed, so the immediate repair should be surgical rather than a broad refactor.

### 2. Risk Ranking

#### P0: CSV export breaks override/no-statistics use

`src/vi_full/paper_tables.py` now writes `paper_table.csv` unconditionally, but `render_3dof_paper_table_csv()` indexes `row["five_profile_statistics"]`. Rows built without `statistics_report_path` only contain `five_profile_mean`, so legacy sample exports and CLI overrides can fail before JSON/Markdown are written.

**Desired behavior:** CSV export should behave like Markdown export. If statistics are attached, report mean/std values from `five_profile_statistics`. If statistics are absent, emit available means from `five_profile_mean` and leave uncertainty/std fields blank rather than inventing uncertainty.

#### P1: CSV stale-output checks are incomplete

`scripts/export/export_paper_only_sim_benchmark_table.py --check` writes CSV through `export_3dof_paper_table()`, but `_diff_outputs()` only compares `.json` and `.md`. This means checked-in CSV drift can pass CI even though CSV is now a first-class output.

**Desired behavior:** check mode compares `.json`, `.md`, `.csv`, and the generated LaTeX include. Tests should cover CSV drift.

#### P1: Regression coverage does not assert CSV output

The existing no-statistics export test only asserts JSON and Markdown behavior. It did not catch the CSV crash until full pytest reached the path.

**Desired behavior:** the no-statistics export test should assert the CSV file exists and contains valid fallback values. Canonical check-mode tests should assert CSV is included in stale-output comparisons.

#### P2: New paper-facing artifacts need provenance coverage

Stage 4 benchmark/statistics/table artifacts, motion-matched main artifacts, and mechanics exports are referenced by manuscript and docs. Current provenance tests cover broad text path leakage plus selected Stage 3/evidence artifacts, but they do not explicitly lock all new Stage 4 sidecar outputs.

**Desired behavior:** add targeted provenance tests for Stage 4 table/statistics and any paper-cited motion-matched/mechanics JSON paths. Keep this as a hardening pass after the exporter regression is fixed.

### 3. Repair Strategy

#### Phase A: Fix no-statistics CSV export

Implement small helper functions inside `src/vi_full/paper_tables.py`:

- `_csv_metric_mean(row, metric_name)` returns `five_profile_statistics[metric]["mean"]` when present, else `five_profile_mean[metric]` when present, else an empty string.
- `_csv_metric_std(row, metric_name)` returns `five_profile_statistics[metric]["std"]` when present, else an empty string.
- `_csv_class_success_mean(row, class_name)` returns `class_success_statistics[class]["mean"]` when `num_samples > 0`; otherwise it falls back to `effective_pressure_classes[class]["metrics"]["success_rate"]` when available.

Keep the public return contract of `export_3dof_paper_table()` unchanged: it should still return `(json_path, markdown_path)`.

#### Phase B: Add regression tests

Extend `tests/paper/test_paper_tables.py::test_export_3dof_paper_table_writes_json_and_markdown` to also assert:

- `paper_table.csv` exists.
- CSV has the expected header.
- no-statistics rows contain success/jam/final-distance means.
- std fields are blank when no statistics report is attached.

Add a focused test for `render_3dof_paper_table_csv()` with an attached statistics report to preserve canonical CSV values.

#### Phase C: Check CSV staleness

Update `scripts/export/export_paper_only_sim_benchmark_table.py`:

- Include `.csv` in `_diff_outputs()`.
- Keep text diff behavior for CSV/Markdown/JSON.
- Add or update a test in `tests/paper/test_exporter_defaults.py` or `tests/paper/test_paper_table_sync.py` that proves check mode fails when CSV differs.

#### Phase D: Provenance hardening

After P0/P1 pass, add explicit provenance tests for the current Stage 4 paper-facing artifacts:

- `artifacts/main_benchmark/table_3dof_paper_benchmark_stage4_20260429.json`
- `artifacts/main_benchmark/three_dof_statistics_report_stage4_20260429.json`
- `artifacts/main_benchmark/three_dof_motion_matched_main_20260429.json`
- `outputs/revision/three_dof_impedance_mechanics_20260429.json`

Only add checks that match existing artifact contracts. Do not invent manifest roles unless the project decides these sidecar artifacts are canonical.

### 4. Validation Gates

#### Gate R1: Local regression closure

Run:

```bash
python -m pytest -q tests/paper/test_paper_tables.py::test_export_3dof_paper_table_writes_json_and_markdown
python -m pytest -q tests/paper/test_exporter_defaults.py tests/paper/test_paper_table_sync.py
```

Pass condition: no no-statistics CSV crash; CSV stale-check behavior is covered.

#### Gate R2: Paper asset synchronization

Run:

```bash
python scripts/export/build_paper_assets.py --check
```

Pass condition: JSON, Markdown, CSV, LaTeX, Figure 2, and evidence matrix outputs are in sync.

#### Gate R3: Full project confidence

Run:

```bash
python -m pytest -q
```

Pass condition: full suite returns green, with only expected skips.

### 5. Non-Goals

- Do not rerun expensive benchmark protocols unless a repaired check proves artifacts are stale.
- Do not alter Stage 4 numerical claims while fixing exporter plumbing.
- Do not change `export_3dof_paper_table()` return shape unless a downstream caller audit justifies an API change.
- Do not add new artifact manifest roles for motion-matched/mechanics sidecars in this repair pass without a separate canonicalization decision.
