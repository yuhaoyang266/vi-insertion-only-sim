## Review Repair Task List (2026-04-29)

> Decomposes `docs/plans/2026-04-29-review-repair-plan.md` into execution-sized tasks. Complete P0/P1 before any provenance or documentation hardening.

### Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` complete
- `[!]` blocked / needs user decision
- `[-]` dropped

---

## P0: Repair No-Statistics CSV Export

### A.1 Reproduce and pin failing path

- [x] Run `python -m pytest -q tests/paper/test_paper_tables.py::test_export_3dof_paper_table_writes_json_and_markdown` and record the current `KeyError: 'five_profile_statistics'` in `docs/project/progress.md`.
- [x] Add assertions to `tests/paper/test_paper_tables.py::test_export_3dof_paper_table_writes_json_and_markdown` that require `paper_table.csv` to exist.
- [x] Assert no-statistics CSV rows keep success/jam/final-distance means populated and std/CI-only fields blank.

### A.2 Patch CSV fallback helpers

- [x] Add `_csv_metric_mean(row, metric_name)` in `src/vi_full/paper_tables.py`.
- [x] Add `_csv_metric_std(row, metric_name)` in `src/vi_full/paper_tables.py`.
- [x] Add `_csv_class_success_mean(row, class_name)` in `src/vi_full/paper_tables.py`.
- [x] Update `render_3dof_paper_table_csv()` to use helpers instead of direct `row["five_profile_statistics"]` indexing.
- [x] Keep `export_3dof_paper_table()` return value as `(json_path, markdown_path)`.

### A.3 Validate P0

- [x] Run `python -m pytest -q tests/paper/test_paper_tables.py::test_export_3dof_paper_table_writes_json_and_markdown`.
- [x] Run `python -m pytest -q tests/paper/test_paper_tables.py`.
- [x] Confirm no generated fixture files are left outside pytest temp directories.

---

## P1: Include CSV in Stale-Output Checks

### B.1 Patch table exporter check mode

- [x] Update `scripts/export/export_paper_only_sim_benchmark_table.py::_diff_outputs()` to compare `.json`, `.md`, and `.csv`.
- [x] Confirm `run_check()` still compares `paper/generated/main_benchmark_table.tex`.
- [x] Keep figure binary comparison behavior unchanged.

### B.2 Add stale-CSV regression test

- [x] Add a test that creates matching JSON/Markdown but mismatched CSV and asserts the table exporter check reports stale output.
- [x] Put the test in `tests/paper/test_exporter_defaults.py` if it can stay script-level, otherwise in `tests/paper/test_paper_table_sync.py`.
- [x] Keep the fixture small; do not regenerate real artifacts inside the unit test.

### B.3 Validate P1

- [x] Run `python -m pytest -q tests/paper/test_exporter_defaults.py tests/paper/test_paper_table_sync.py`.
- [x] Run `python scripts/export/build_paper_assets.py --check`.

---

## P1: Strengthen CSV Contract Coverage

### C.1 Canonical CSV value test

- [x] Add a test for `render_3dof_paper_table_csv()` when a statistics report is attached.
- [x] Assert canonical CSV uses `five_profile_statistics` means/stds, not raw `five_profile_mean` fallback.
- [x] Assert CSV line endings are stable with `lineterminator="\n"`.

### C.2 Override CLI smoke

- [x] Add a lightweight CLI-level test for `--benchmark-input <override>` with no `--statistics-report-input`.
- [x] Assert the override path writes JSON, Markdown, and CSV without loading the manifest.
- [x] Assert `provenance_label == "override_benchmark_input"` remains unchanged.

---

## P2: Provenance and Artifact Hardening

### D.1 Stage 4 paper table provenance

- [x] Extend `tests/artifacts/test_artifact_provenance.py` to check `artifacts/main_benchmark/table_3dof_paper_benchmark_stage4_20260429.json`.
- [x] Assert source artifacts include Stage 4 benchmark and Stage 4 statistics report.
- [x] Assert source hashes match current files.

### D.2 Motion-matched artifact provenance

- [x] Add explicit checks for `artifacts/main_benchmark/three_dof_motion_matched_main_20260429.json`.
- [x] Assert source hashes include `src/vi_full/three_dof_motion_matched_main_protocol.py` and the runner script when present.
- [x] Assert manuscript prose tests still reference the same artifact path.

### D.3 Mechanics artifact provenance

- [x] Add explicit checks for `outputs/revision/three_dof_impedance_mechanics_20260429.json`.
- [x] Assert source hashes include the mechanics trace artifact and `src/vi_full/three_dof_impedance_mechanics.py`.
- [x] Assert Figure 3 tests still distinguish success-matched main assets from legacy appendix assets.

### D.4 Validate P2

- [x] Run `python -m pytest -q tests/artifacts/test_artifact_provenance.py tests/paper/test_prose_statistics_sync.py tests/paper/test_paper_figures.py`.

---

## Final Verification

- [x] Run `python -m pytest -q`.
- [x] Run `python scripts/export/build_paper_assets.py --check`.
- [x] Run `git status --short` and confirm only intended code/test/doc changes are present.
- [x] Record final command outputs in `docs/project/progress.md`.

---

## Commit Recommendation

- [ ] Commit P0/P1 as one focused repair: `fix: repair paper table csv export checks`.
- [ ] Commit P2 provenance hardening separately: `test: harden stage4 artifact provenance checks`.
