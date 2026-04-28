# Canonical Paper Artifact Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade this repository into a reviewer-trustworthy reproducible paper package where the manuscript table, Figure 2, evidence matrix, README commands, manifests, and tests all derive from one canonical provenance chain.

**Architecture:** Add a canonical benchmark manifest as the single paper-facing entry point. All exported paper tables, figures, evidence matrices, README commands, reviewer smoke tests, and provenance checks must read from that manifest instead of hard-coded artifact paths. Existing stage3 and schema2 artifacts remain tracked, but stage3 is declared as the current canonical main benchmark while schema2 is demoted to appendix / diagnostic legacy use only.

**Tech Stack:** Python, pytest, JSON/Markdown/LaTeX artifacts, SHA256 provenance, LaTeX/MiKTeX build wrapper, optional CI, optional later benchmark expansion.

---

## Product Spec

### Problem

- The largest submission risk is not the model result itself, but provenance drift: `paper/main.tex` and the checked-in Figure 2 use stage3 values, while default export scripts, README commands, and evidence-matrix rows still point to schema2 in places.
- Reviewers can see conflicting values such as Fixed-impedance RL success `0.947` versus `0.80`, and DAPG-lite success `1.000` versus `0.60`; this can be interpreted as cherry-picking or unreliable result versioning.
- Paper-facing artifacts include local absolute paths and old working-tree paths, which weakens reproducibility.
- `vi_full.__init__` imports heavy MuJoCo/SB3/training paths at package import time, anonymous snapshots exclude tests entirely, and README TeX build commands assume local PATH state.

### Success Metrics

- `paper table == Figure 2 == default export == evidence selected benchmark rows` for the benchmark-derived rows, all from the same canonical source hash.
- schema2 no longer appears as a main-paper default source; it only appears in explicit appendix / diagnostic whitelists.
- Paper-facing artifacts contain no local paths such as `F:\`, `C:\`, `full_projects`, `/Users/`, or `/home/`.
- Canonical paper-facing artifacts can be traced to repo-relative source path, SHA256, generation command, and git commit; appendix and legacy artifacts follow the graded provenance requirements below.
- `python -m pytest tests/reviewer -q` runs in the anonymous snapshot.
- `python -c "import vi_full"` is lightweight and does not trigger unrelated MuJoCo/SB3/Gym warnings.
- README provides one-command paper asset build and paper PDF build, with clear diagnostics when TeX tools are missing.

### Primary Users

- **Paper authors:** need stable paper table/figure generation without manual synchronization.
- **Reviewers:** need quick provenance and smoke verification without running expensive training.
- **Maintainers:** need a clear answer to which artifact is the main result and which artifacts are appendix or legacy references.

### Non-Goals

- Do not rerun all training in the P0 provenance closure phase.
- Do not delete schema2; demote it to non-main diagnostic use.
- Do not claim stage3 is scientifically 鈥渢ruer鈥?than schema2; declare it as the current manuscript-canonical source.
- Do not force pure-RL confirm rows to match the main benchmark; evidence matrix must preserve separate contracts.

---

## Final Priority Stack

### P0-A: Canonical And Provenance

1. canonical manifest
2. exporter default-source switch
3. evidence-matrix layered sync
4. generated main table
5. absolute-path provenance cleanup
6. numeric-consistency hard-fail tests

### P0-B: Reviewer Reproducibility

7. unified `build_paper_assets.py`
8. `build_paper_pdf.py`
9. reviewer smoke tests in anonymous bundle
10. README / paper / manifest synchronization

### P1: Engineering Trust

11. `vi_full.__init__` import boundary
12. no-training CI gate

### P1-Optional: Post-Closure Refactor

13. targeted paper table / figure module split

### P2: Scientific Strengthening

14. 10-20 seed canonical v2
15. sensitivity matrix
16. pose / 6D proxy strengthening
17. MuJoCo cross-check
18. stronger baselines

---

## Task 1: Canonical Manifest Spine

**Goal:** Establish exactly one canonical paper-facing benchmark source and eliminate stage3/schema2 ambiguity.

**Files:**
- Create: `artifacts/main_benchmark/main_benchmark_manifest.json`
- Create: `src/vi_full/artifact_provenance.py`
- Create: `src/vi_full/artifact_registry.py`
- Create: `tests/artifacts/test_canonical_manifest.py`
- Modify: `README.md:19`
- Modify: `docs/figure_asset_manifest.md:49`

**Specification:**
- Declare stage3 as the current canonical main benchmark.
- Declare schema2 as appendix / diagnostic / legacy, not as a main-paper default.
- Manifest records:
  - `role`
  - `path`
  - `sha256`
  - `schema_version`
  - `claim_scope`
  - `source_role`
  - `generating_command`
  - `git_commit`
  - `git_dirty`
  - `generated_at_utc`

**Manifest Skeleton:**

```json
{
  "manifest_version": 1,
  "artifacts": {
    "canonical_main_benchmark": {
      "role": "canonical_main_benchmark",
      "path": "artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json",
      "sha256": "...",
      "schema_version": 3,
      "claim_scope": "main manuscript Table 1 and Figure 2",
      "source_role": "stage3_current_manuscript_claim",
      "generating_command": "...",
      "git_commit": "...",
      "git_dirty": false,
      "generated_at_utc": "..."
    },
    "canonical_statistics_report": {
      "role": "canonical_statistics_report",
      "path": "artifacts/main_benchmark/three_dof_statistics_report_stage3_20260412.json",
      "sha256": "...",
      "schema_version": 3,
      "claim_scope": "main manuscript benchmark statistics"
    },
    "schema2_diagnostic": {
      "role": "appendix_diagnostic_legacy",
      "path": "artifacts/main_benchmark/three_dof_benchmark_schema2_paper_teacher_20260418_034230.json",
      "sha256": "...",
      "schema_version": 2,
      "claim_scope": "appendix teacher/termination diagnostics only"
    }
  }
}
```

**Important Rule:**
- Do not copy stage3 JSON to a new 鈥渃anonical鈥?filename unless it is an explicitly versioned derived snapshot. The safer default is to keep the original raw artifact file and let the manifest assign the canonical role.

- [ ] **Step 1: Write the failing manifest test**

  Create `tests/artifacts/test_canonical_manifest.py` asserting that `artifacts/main_benchmark/main_benchmark_manifest.json` exists, has the required top-level roles, and uses repo-relative paths.

- [ ] **Step 2: Assert stage3 is canonical**

  In the same test, assert `canonical_main_benchmark` points to `artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json`.

- [ ] **Step 3: Assert schema2 is diagnostic-only**

  Assert schema2 appears only under appendix / diagnostic roles, never under main-paper roles.

- [ ] **Step 4: Implement provenance helpers**

  Add `src/vi_full/artifact_provenance.py` with SHA256 calculation, repo-relative path conversion, git commit lookup, and dirty-state lookup.

- [ ] **Step 5: Implement registry helpers**

  Add `src/vi_full/artifact_registry.py` with `load_manifest()`, `get_artifact(role)`, and `validate_manifest()`.

- [ ] **Step 6: Generate the manifest**

  Create `artifacts/main_benchmark/main_benchmark_manifest.json` with stage3 as canonical and schema2 as appendix diagnostic.

- [ ] **Step 7: Update top-level docs**

  Update `README.md` and `docs/figure_asset_manifest.md` so they no longer imply schema2 is the main benchmark.

**Validation:**

```bash
python -m pytest -q tests/artifacts/test_canonical_manifest.py
```

---

## Task 2: Provenance Schema And No-Absolute-Path Gate

**Goal:** Ensure paper-facing artifacts do not leak local machine paths and have traceable provenance.

**Files:**
- Create: `tests/artifacts/test_artifact_provenance.py`
- Modify: `artifacts/main_benchmark/table_3dof_paper_benchmark_stage3_20260412.json:4`
- Modify: `artifacts/main_benchmark/table_3dof_paper_benchmark_stage3_20260412.md:3`
- Modify: `artifacts/main_benchmark/table_3dof_appendix_schema2_20260418.json:4`
- Modify: `artifacts/main_benchmark/table_3dof_appendix_schema2_20260418.md:3`
- Modify: `outputs/evidence_matrix/three_dof_sprint2_main_table.json:5`
- Modify: `outputs/evidence_matrix/three_dof_sprint2_main_table.md:5`

**Scan Scope:**
- `README.md`
- `paper/`
- `docs/figure_asset_manifest.md`
- `artifacts/main_benchmark/`
- `outputs/evidence_matrix/`
- figure metadata files if present

**Forbidden Strings:**
- `F:\`
- `C:\`
- `D:\`
- `/Users/`
- `/home/`
- `full_projects`
- `vi_insertion_full_only_sim`

**Important Rule:**
- Do not write an artifact's own SHA256 inside that same artifact. That creates a self-referential hash problem. Store artifact self-hashes in `main_benchmark_manifest.json`; artifact internals should record source hashes only.

**Graded Provenance Requirements:**
- **Canonical artifacts:** must include repo-relative source path, source SHA256, generating command, git commit, and `schema_version` or `export_name`.
- **Appendix / diagnostic artifacts:** must include repo-relative source path, source SHA256 or manifest hash, and explicit `role = appendix / diagnostic / legacy`.
- **Legacy tracked artifacts:** must contain no local absolute paths and must not be used by the default paper-facing pipeline.

- [ ] **Step 1: Write the failing provenance scan**

  Create `tests/artifacts/test_artifact_provenance.py` to scan paper-facing paths for forbidden local paths.

- [ ] **Step 2: Require provenance metadata**

  Add test assertions that paper-facing JSON artifacts include source paths, source hashes or manifest-level hashes, generation command, and git commit.

- [ ] **Step 3: Clean stage3 table metadata**

  Replace old `F:\...\full_projects...` paths in stage3 table JSON/MD with repo-relative artifact paths.

- [ ] **Step 4: Clean schema2 appendix metadata**

  Replace current-machine absolute paths in schema2 appendix table JSON/MD with repo-relative paths.

- [ ] **Step 5: Clean evidence metadata**

  Replace schema2-as-main metadata with canonical manifest paths where appropriate.

- [ ] **Step 6: Add source hashes and commands**

  Record source artifact hashes and generation commands in regenerated artifacts or in the manifest.

**Validation:**

```bash
python -m pytest -q tests/artifacts/test_artifact_provenance.py
```

---

## Task 3: Exporter Defaults Read Manifest

**Goal:** Make paper-facing exporters read canonical inputs from the manifest instead of hard-coding schema2.

**Files:**
- Modify: `scripts/export/export_paper_only_sim_figure2.py:24`
- Modify: `scripts/export/export_paper_only_sim_benchmark_table.py:24`
- Modify: `src/vi_full/paper_figures.py`
- Modify: `src/vi_full/paper_tables.py`
- Create: `tests/paper/test_exporter_defaults.py`

**Specification:**
- Add `--manifest artifacts/main_benchmark/main_benchmark_manifest.json` to both exporters.
- Default behavior:
  - `benchmark_input = manifest["canonical_main_benchmark"]`
  - `statistics_report_input = manifest["canonical_statistics_report"]`
- Keep explicit `--benchmark-input` overrides.
- If override is used, exported artifacts must record override provenance and must not be labeled canonical.

- [ ] **Step 1: Write default-source tests**

  Add `tests/paper/test_exporter_defaults.py` asserting Figure 2 and benchmark-table exporters default to the manifest canonical source.

- [ ] **Step 2: Add manifest CLI argument**

  Update both export scripts to accept `--manifest` with the default manifest path.

- [ ] **Step 3: Remove schema2 default**

  Delete the hard-coded schema2 path as the default benchmark input.

- [ ] **Step 4: Keep override behavior**

  Preserve `--benchmark-input` but mark outputs as override-derived when used.

- [ ] **Step 5: Update help text**

  Make CLI help explicit that schema2 is appendix diagnostic only.

- [ ] **Step 6: Add exporter check mode**

  Add `--check` to both exporters. It must generate into memory or a temporary directory, compare against checked-in outputs, avoid rewriting files, and fail with a diff summary if outputs would change.

**Validation:**

```bash
python -m pytest -q tests/paper/test_exporter_defaults.py
python scripts/export/export_paper_only_sim_figure2.py --check
python scripts/export/export_paper_only_sim_benchmark_table.py --check
```

`--check` must generate into memory or a temporary directory, compare against checked-in outputs, avoid rewriting files, and fail with a diff summary if outputs would change.

---

## Task 4: Generated Main Table

**Goal:** Remove hand-written benchmark values from `paper/main.tex`.

**Files:**
- Create: `paper/generated/main_benchmark_table.tex`
- Create: `tests/paper/test_paper_table_sync.py`
- Modify: `paper/main.tex:520`
- Modify: `src/vi_full/paper_tables.py`
- Modify: `scripts/export/export_paper_only_sim_benchmark_table.py`

**Specification:**
- `paper/main.tex` keeps the table environment, caption, and label.
- The table body is replaced with:

```tex
\input{generated/main_benchmark_table.tex}
```

- The exporter emits JSON, Markdown, and a LaTeX include.
- The generated LaTeX include starts with:

```tex
% Generated by scripts/export/export_paper_only_sim_benchmark_table.py; do not edit manually.
```

**Sync Test Requirements:**
- Parse canonical benchmark/table JSON.
- Parse generated LaTeX table.
- Compare values after documented display rounding.
- Explicitly test meter-to-millimeter conversion for final distance.

- [ ] **Step 1: Write hardcoded-row failing test**

  Assert `paper/main.tex` does not directly contain main benchmark rows such as `Fixed-impedance RL &`.

- [ ] **Step 2: Write numeric sync test**

  Assert `paper/generated/main_benchmark_table.tex` matches canonical JSON values after rounding and unit conversion.

- [ ] **Step 3: Add LaTeX output support**

  Update `export_paper_only_sim_benchmark_table.py` with `--latex-output paper/generated/main_benchmark_table.tex`.

- [ ] **Step 4: Replace manuscript table body**

  Modify `paper/main.tex` to include the generated table body.

- [ ] **Step 5: Regenerate table outputs**

  Export JSON/MD/LaTeX table artifacts from the canonical manifest.

**Validation:**

```bash
python scripts/export/export_paper_only_sim_benchmark_table.py
python -m pytest -q tests/paper/test_paper_table_sync.py
```

---

## Task 5: Evidence Matrix Layered Source Refactor

**Goal:** Keep evidence matrix claim-control layering while sourcing benchmark rows from the canonical main benchmark.

**Files:**
- Modify: `scripts/experiments/export_3dof_evidence_matrix.py`
- Modify: `outputs/evidence_matrix/three_dof_sprint2_main_table.json`
- Modify: `outputs/evidence_matrix/three_dof_sprint2_main_table.md`
- Modify: `outputs/evidence_matrix/three_dof_evidence_matrix.json`
- Modify: `outputs/evidence_matrix/three_dof_evidence_matrix.md`
- Modify: `tests/paper/test_three_dof_evidence_matrix.py`
- Modify: `tests/paper/test_sprint2_paper_sync.py:15`

**Layer Contract:**
- `pure_rl_contact_gate_negatives`: source = confirm report.
- `demo_supported_main_benchmark`: source = canonical manifest.
- `mechanics_anchor`: source = canonical manifest.

**Rules:**
- Pure-RL rows do not need to equal main benchmark rows.
- Main benchmark selected rows must equal canonical source:
  - BC-only
  - BC -> PPO
  - DAPG-lite
  - Fixed-impedance RL
- Every row includes:
  - `source_contract`
  - `source_role`
  - `source_artifact`
  - `source_sha256`

- [ ] **Step 1: Fix the reverse test**

  Rewrite `tests/paper/test_sprint2_paper_sync.py` so it no longer requires schema2 and rejects stage3.

- [ ] **Step 2: Add schema2 whitelist test**

  Assert schema2 cannot be the source for evidence main-benchmark rows.

- [ ] **Step 3: Add selected-row numeric tests**

  Assert evidence rows for DAPG-lite and Fixed-impedance RL match canonical benchmark values after documented rounding.

- [ ] **Step 4: Modify evidence exporter**

  Read benchmark-derived rows from the canonical manifest.

- [ ] **Step 5: Regenerate evidence outputs**

  Regenerate JSON/CSV/MD outputs from the updated exporter.

- [ ] **Step 6: Update manuscript prose**

  Update `paper/main.tex` near the evidence matrix provenance sentence to reference the canonical manifest/source hash instead of schema2.

**Validation:**

```bash
python scripts/experiments/export_3dof_evidence_matrix.py --confirm-report outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json
python -m pytest -q tests/paper/test_three_dof_evidence_matrix.py tests/paper/test_sprint2_paper_sync.py
```

---

## Task 6: Unified Paper Assets Builder

**Goal:** Provide one primary command for paper-facing asset generation and checking.

**Files:**
- Create: `scripts/export/build_paper_assets.py`
- Create: `tests/paper/test_build_paper_assets.py`
- Modify: `README.md:116`
- Modify: `docs/figure_asset_manifest.md:44`

**Command:**

```bash
python scripts/export/build_paper_assets.py
python scripts/export/build_paper_assets.py --check
python scripts/export/build_paper_assets.py --manifest artifacts/main_benchmark/main_benchmark_manifest.json
```

**Responsibilities:**
- Validate manifest.
- Validate hashes.
- Export main table.
- Export Figure 2.
- Export evidence matrix.
- Optionally export appendix diagnostics.
- Update or check the figure/table manifest.

**Important:**
- `--check` must not rewrite files.
- `--check` must fail if generated outputs would differ.

- [ ] **Step 1: Write builder tests**

  Assert the default manifest path is correct and `--check` triggers manifest validation without writing outputs.

- [ ] **Step 2: Implement orchestration**

  Add `scripts/export/build_paper_assets.py` that calls or imports the existing exporters.

- [ ] **Step 3: Add check mode**

  Compare would-be generated content to checked-in files without writing.

- [ ] **Step 4: Update README**

  Make the unified builder the primary reproduction command.

- [ ] **Step 5: Keep advanced manual commands**

  Preserve individual exporter commands as advanced usage, each with `--manifest`.

**Validation:**

```bash
python scripts/export/build_paper_assets.py --check
python scripts/export/build_paper_assets.py
python -m pytest -q tests/paper/test_build_paper_assets.py
```

---

## Task 7: README And Paper Text Synchronization

**Goal:** Ensure documentation does not imply schema2 is the main benchmark source.

**Files:**
- Modify: `README.md:19`
- Modify: `README.md:116`
- Modify: `README.md:143`
- Modify: `README.md:151`
- Modify: `paper/main.tex:472`
- Modify: `paper/main.tex:561`
- Modify: `docs/figure_asset_manifest.md:49`
- Modify: `protocol_freeze.md:247` if still paper-facing
- Create: `tests/paper/test_docs_claim_source_sync.py`

**Specification:**
- README top section says:
  - canonical main benchmark = stage3 via manifest
  - schema2 = appendix teacher/termination diagnostic
- README reproduction section:
  - primary command = `build_paper_assets.py`
  - manual commands use `--manifest`
- Paper text:
  - Replace 鈥渟chema2 benchmark JSON passed to the exporter鈥?with canonical main benchmark manifest/source hash.
- Figure manifest:
  - Figure 2 source = canonical manifest / stage3 source.
  - Evidence matrix source = confirm report + canonical manifest.

- [ ] **Step 1: Write docs sync test**

  Add `tests/paper/test_docs_claim_source_sync.py` to catch schema2 being described as the main benchmark.

- [ ] **Step 2: Update README top matter**

  Replace the schema2 鈥渢racked frozen main benchmark鈥?wording.

- [ ] **Step 3: Update reproduction commands**

  Replace placeholder `<phase_c_benchmark.json>` for main paper reproduction with manifest-based commands.

- [ ] **Step 4: Update manuscript evidence prose**

  Align `paper/main.tex` with the new evidence matrix source contract.

- [ ] **Step 5: Update figure manifest**

  Change Figure 2 and evidence-matrix source rows to the canonical manifest contract.

**Validation:**

```bash
python -m pytest -q tests/paper/test_docs_claim_source_sync.py
```

---

## Task 8: Paper PDF Build Wrapper

**Goal:** Make PDF build reproducible and diagnosable on new machines.

**Files:**
- Create: `scripts/export/build_paper_pdf.py`
- Create: `tests/test_build_paper_pdf.py`
- Modify: `README.md:66`
- Modify: `docs/submission/submission_package_checklist.md:63`

**Features:**
- Detect `pdflatex`.
- Detect `bibtex`.
- Print versions.
- Run:
  - `pdflatex`
  - `bibtex`
  - `pdflatex`
  - `pdflatex`
- Support:
  - `--pdflatex`
  - `--bibtex`
  - `--paper-dir`
  - `--output`
- Windows diagnostics:
  - MiKTeX PATH hint
  - `where pdflatex`
  - `where bibtex`

- [ ] **Step 1: Write missing-tool tests**

  Assert missing `pdflatex` exits non-zero and prints a Windows/MiKTeX PATH hint.

- [ ] **Step 2: Write command-order test**

  Mock executables and assert the four build commands run in the expected order.

- [ ] **Step 3: Implement wrapper**

  Add `scripts/export/build_paper_pdf.py` with clear error reporting.

- [ ] **Step 4: Update README**

  Make the wrapper the preferred paper build command.

- [ ] **Step 5: Keep manual fallback**

  Retain raw `pdflatex` / `bibtex` commands as a fallback section.

**Validation:**

```bash
python -m pytest -q tests/test_build_paper_pdf.py
python scripts/export/build_paper_pdf.py --help
```

---

## Task 9: Reviewer Smoke Tests In Anonymous Snapshot

**Goal:** Let reviewers run minimal verification from the anonymous package.

**Files:**
- Create: `tests/reviewer/test_manifest_hashes.py`
- Create: `tests/reviewer/test_paper_assets_exist.py`
- Create: `tests/reviewer/test_no_absolute_paths.py`
- Create: `tests/reviewer/test_import_lightweight.py`
- Modify: `src/vi_full/submission_bundle.py:10`
- Modify: `tests/packaging/test_submission_bundle.py:109`
- Modify: `docs/submission/submission_package_checklist.md:95`
- Modify: `README.md`

**Specification:**
- Complete internal tests remain available in the public repository.
- Anonymous snapshot includes `tests/reviewer/`.
- Reviewer tests do not run training.
- Reviewer tests check:
  - manifest hash
  - canonical source
  - paper assets existence
  - no absolute paths
  - lightweight import

- [ ] **Step 1: Add reviewer smoke tests**

  Create minimal no-training tests under `tests/reviewer/`.

- [ ] **Step 2: Modify bundle builder**

  Explicitly copy `tests/reviewer/` into the anonymous snapshot while still excluding full tests.

- [ ] **Step 3: Update bundle tests**

  Change assertions so the snapshot is expected to contain `tests/reviewer/`, not zero tests.

- [ ] **Step 4: Update snapshot docs**

  Add instructions for `python -m pytest -q tests/reviewer`.

- [ ] **Step 5: Build and verify bundle**

  Generate the anonymous snapshot and run reviewer tests inside it.

**Validation:**

```bash
python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind
cd tmp/submission_bundle/journal_double_blind/anonymous_snapshot
python -m pytest -q tests/reviewer
```

`--paper-pdf` is optional for the first snapshot build. If an anonymous PDF already exists, run the second packaging pass with `--paper-pdf <anonymous_manuscript.pdf>` from outside `--output-dir`.

---

## Task 10: Lightweight Import Boundary

**Goal:** Make `import vi_full` lightweight and free of unrelated MuJoCo/SB3/training side effects.

**Files:**
- Modify: `src/vi_full/__init__.py:1`
- Create: `tests/core/test_import_boundaries.py`
- Optionally create: `src/vi_full/three_dof_api.py`
- Optionally create: `src/vi_full/training_api.py`
- Optionally create: `src/vi_full/mujoco_api.py`

**Specification:**
- `src/vi_full/__init__.py` keeps only:
  - docstring
  - `__version__`
  - lightweight registry helpers if needed
- Top-level import must not import:
  - `mujoco`
  - `stable_baselines3`
  - legacy Panda env
  - training modules
- Scripts must use explicit submodule imports.

- [x] **Step 1: Write import warning test**

  Assert `python -c "import vi_full"` does not emit Gym deprecation warnings.

- [x] **Step 2: Write module-load test**

  Assert `stable_baselines3` and `mujoco` are not in `sys.modules` after `import vi_full`.

- [x] **Step 3: Slim `__init__.py`**

  Remove top-level imports of env, training, benchmark, MuJoCo, and SB3 modules.

- [x] **Step 4: Fix call sites**

  Replace `from vi_full import ...` with explicit submodule imports where needed.

- [x] **Step 5: Document the import contract**

  Update README with explicit import examples.

**Validation:**

```bash
python -m pytest -q tests/core/test_import_boundaries.py
python -c "import vi_full; print(vi_full.__version__)"
```

---

## Task 11: No-Training CI Gate

**Goal:** Prevent future provenance drift without running expensive training.

**Files:**
- Create: `.github/workflows/reviewer-smoke.yml`
- Create: `.github/workflows/paper-assets-check.yml`
- Modify: `README.md`

**CI Jobs:**
- manifest validation
- artifact provenance scan
- paper table sync
- Figure 2 source sync
- evidence selected rows sync
- import boundary
- reviewer tests
- `build_paper_assets.py --check`

**Excluded From CI:**
- full benchmark training
- expensive sensitivity runs
- mandatory TeX build unless TeX environment is available

- [x] **Step 1: Add reviewer smoke workflow**

  Run reviewer tests and import-boundary checks.

- [x] **Step 2: Add paper assets check workflow**

  Run manifest validation, provenance scan, sync tests, and `build_paper_assets.py --check`.

- [x] **Step 3: Document CI expectations**

  Update README with local equivalents and CI purpose.

**Validation:**

```bash
python -m pytest -q tests/artifacts/test_canonical_manifest.py tests/artifacts/test_artifact_provenance.py tests/paper/test_paper_table_sync.py tests/core/test_import_boundaries.py tests/reviewer
python scripts/export/build_paper_assets.py --check
```

---

## Task 12: Targeted Module Split

**Goal:** Improve maintainability where it supports reproducibility, without unrelated rewrites.

**Split Order:**
1. `src/vi_full/paper_tables.py`
2. `src/vi_full/paper_figures.py`
3. `src/vi_full/three_dof_benchmark.py`
4. `src/vi_full/three_dof_training.py`

**Files:**
- Create: `src/vi_full/paper_tables/main_benchmark.py`
- Create: `src/vi_full/paper_tables/appendix.py`
- Create: `src/vi_full/paper_tables/formatting.py`
- Create: `src/vi_full/paper_tables/provenance.py`
- Create: `src/vi_full/paper_figures/figure2.py`
- Create: `src/vi_full/paper_figures/appendix.py`
- Create: `src/vi_full/paper_figures/common.py`
- Optionally create: `src/vi_full/benchmarking/evaluation.py`
- Optionally create: `src/vi_full/benchmarking/aggregation.py`
- Optionally create: `src/vi_full/benchmarking/serialization.py`

**Rules:**
- Add characterization tests before moving behavior.
- Move one functional cluster at a time.
- Keep old modules as thin wrappers during migration.
- Validate exported artifact values remain unchanged after each split.

- [ ] **Step 1: Add characterization tests for table export**

  Lock current expected table output from canonical source.

- [ ] **Step 2: Split main benchmark table logic**

  Move main-table construction into `src/vi_full/paper_tables/main_benchmark.py`.

- [ ] **Step 3: Split formatting/provenance helpers**

  Move formatting and provenance code into focused modules.

- [ ] **Step 4: Split Figure 2 logic**

  Move Figure 2 generation into `src/vi_full/paper_figures/figure2.py`.

- [ ] **Step 5: Keep wrappers stable**

  Preserve legacy import paths until all scripts are updated.

- [ ] **Step 6: Validate no artifact drift**

  Run paper table and figure tests after each move.

**Validation:**

```bash
python -m pytest -q tests/paper/test_paper_tables.py tests/paper/test_paper_figures.py
python scripts/export/build_paper_assets.py --check
```

---

## Task 13: Claim Boundary Cleanup

**Goal:** Align manuscript language with artifact roles and avoid overclaiming.

**Files:**
- Modify: `paper/main.tex`
- Create: `tests/paper/test_paper_claim_boundaries.py`

**Rules:**
- SG-VI = benchmark-local methodology, not a universal method.
- SCI = support coverage diagnostic, not proof of generalization.
- DAPG-lite = matched-protocol mechanism control, not faithful prior reproduction.
- PPO w/o BC = did not reach useful contact under tested contracts, not all PPO failure.
- Near-ceiling success = avoid success-rate ranking; emphasize force/contact work/Pareto.

- [x] **Step 1: Add claim-boundary grep tests**

  Prevent problematic phrases such as `PPO fails`, `proves generalization`, `DAPG reproduction`, `universal SCI`, and `state-of-the-art` unless intentionally whitelisted.

- [x] **Step 2: Review SG-VI / SCI wording**

  Ensure every broad concept is scoped to this benchmark.

- [x] **Step 3: Review DAPG-lite wording**

  Keep the matched-protocol mechanism-control boundary.

- [x] **Step 4: Review PPO negative wording**

  Keep negative claims limited to tested contracts and budgets.

- [x] **Step 5: Defer PDF rebuild to external/editor environment**

  Do not require local LaTeX/PDF deployment for Milestone 3 closure. Confirm wording with claim-boundary tests locally; if PDF inspection is needed, use an external/editor build or an already generated anonymous PDF.

**Validation:**

```bash
python -m pytest -q tests/paper/test_paper_claim_boundaries.py
```

---

## Task 14: Canonical v2 Seed Expansion

**Goal:** Improve statistical power and Q2-level credibility without overwriting stage3.

**Files:**
- Create: `configs/benchmark/canonical_main_v2.yaml`
- Create: `artifacts/main_benchmark/canonical_main_v2.json`
- Create: `artifacts/main_benchmark/canonical_statistics_v2.json`
- Create: `docs/result_delta_report.md`
- Modify: `artifacts/main_benchmark/main_benchmark_manifest.json` only after explicit promotion decision
- Modify: paper tables/figures only if v2 is promoted

**Design:**
- Seeds: 10 minimum, 20 ideal.
- Episodes: 100 or 200 per seed/profile.
- Methods:
  - PPO w/o BC
  - BC-only
  - Fixed-impedance RL
  - BC -> PPO
  - DAPG-lite
- Additional metrics:
  - contact work
  - p95 force
  - first contact step
  - success-force Pareto
  - SCI

**Important:**
- v2 must not overwrite stage3.
- v2 is a new canonical candidate.
- Generate `docs/result_delta_report.md` comparing v2 against stage3 before promotion.
- Promote v2 only if manuscript claims remain valid and all paper-facing artifacts are regenerated from v2.

- [ ] **Step 1: Freeze v2 config**

  Add `configs/benchmark/canonical_main_v2.yaml` with seeds, profiles, methods, and metrics.

- [ ] **Step 2: Run smoke benchmark**

  Run a small seed/episode subset to validate pipeline behavior.

- [ ] **Step 3: Run full v2 benchmark**

  Generate `artifacts/main_benchmark/canonical_main_v2.json`.

- [ ] **Step 4: Generate v2 statistics**

  Produce `canonical_statistics_v2.json` and summary markdown.

- [ ] **Step 5: Write delta report**

  Compare stage3 and v2 values, including claim-level implications.

- [ ] **Step 6: Decide promotion**

  Only after review, update manifest canonical role to v2 and regenerate all paper-facing assets.

**Validation:**
- Full sync tests.
- Statistics report review.
- Manual `docs/result_delta_report.md` review.

---

## Task 15: Sensitivity Matrix

**Goal:** Strengthen mechanism robustness and external-validity support.

**Files:**
- Create: `configs/benchmark/sensitivity_v1.yaml`
- Create: `scripts/experiments/run_3dof_sensitivity_matrix.py`
- Create: `src/vi_full/sensitivity.py`
- Create: `outputs/sensitivity/`
- Create: `paper/generated/sensitivity_summary.tex`

**Axes:**
- Contact parameters:
  - `alpha_xy`
  - `alpha_z`
  - wall friction
  - jam threshold
- Stiffness:
  - stiffness range
  - fixed vs variable
- Reward:
  - force penalty
  - distance reward
  - success tolerance
- Reset:
  - train reset coverage
  - eval perturbation
- Teacher:
  - demo count
  - teacher quality
  - fixed vs variable teacher

- [ ] **Step 1: Freeze sensitivity config**

  Define a minimal but meaningful axis design; avoid uncontrolled full-factorial explosion.

- [ ] **Step 2: Implement runner**

  Add `scripts/experiments/run_3dof_sensitivity_matrix.py`.

- [ ] **Step 3: Add provenance metadata**

  Record config hash, command, commit, and output hash.

- [ ] **Step 4: Generate summary table**

  Create `paper/generated/sensitivity_summary.tex` as a generated include.

- [ ] **Step 5: Update manuscript carefully**

  Present sensitivity as robustness evidence, not as a replacement main benchmark.

**Validation:**
- Sensitivity summary artifact contains config hash, command, and commit.
- Paper uses it as sensitivity evidence only.

---

## Task 16: Pose / 6D Proxy And MuJoCo Cross-Check

**Goal:** Maximize Q2 external-validity credibility if time and compute are available.

**Files:**
- Create: `configs/benchmark/pose_perturbation_v2.yaml`
- Create: `configs/benchmark/mujoco_crosscheck_v1.yaml`
- Create: `scripts/experiments/run_mujoco_crosscheck.py`
- Create: `src/vi_full/mujoco_crosscheck.py`
- Create: `outputs/mujoco_crosscheck/`
- Create: `paper/generated/mujoco_crosscheck.tex`

**Pose Proxy:**
- systematic lateral offset
- roll/pitch/yaw proxy
- noisy force
- reset distribution shift

**MuJoCo Cross-Check:**
- Evaluate selected policies or policy families under a higher-fidelity contact proxy.
- Report qualitative trend agreement, not exact numeric equality.
- Explicitly state that this is not a real-robot claim unless hardware is added.

- [ ] **Step 1: Freeze pose perturbation config**

  Define perturbation magnitudes and evaluation-only protocol.

- [ ] **Step 2: Freeze MuJoCo cross-check config**

  Define observation/action contracts and policy adapters.

- [ ] **Step 3: Add shape and dtype tests**

  Check observation shape, action shape, force dtype, and frame convention.

- [ ] **Step 4: Run smoke rollout**

  Validate no simulator or adapter errors.

- [ ] **Step 5: Run cross-check evaluation**

  Generate outputs with provenance metadata.

- [ ] **Step 6: Add paper summary**

  Add generated table and cautious interpretation.

**Validation:**
- Smoke rollout succeeds.
- Observation/action shape tests pass.
- Source provenance includes hash, command, and commit.

---

## Final Execution Order

### Milestone 1: P0 Provenance Closure

- [x] Task 1: Canonical manifest spine
- [x] Task 2: Provenance schema and no-absolute-path gate
- [x] Task 3: Exporter defaults read manifest
- [x] Task 5: Evidence matrix layered source refactor
- [x] Task 4: Generated main table

### Milestone 2: Paper-Facing Reproducibility

- [x] Task 6: Unified paper assets builder
- [x] Task 7: README and paper text synchronization
- [x] Task 8: Paper PDF build wrapper
- [x] Task 9: Reviewer smoke tests in anonymous snapshot

### Milestone 3: Engineering Trust

- [x] Task 10: Lightweight import boundary
- [x] Task 11: No-training CI gate
- [x] Task 13: Claim boundary cleanup

### Milestone 3b: Optional Post-Closure Refactor

- [ ] Task 12: Targeted module split

### Milestone 4: Scientific Strengthening

- [ ] Task 14: Canonical v2 seed expansion
- [ ] Task 15: Sensitivity matrix
- [ ] Task 16: Pose / 6D proxy and MuJoCo cross-check

---

## Final Acceptance Checklist

- [x] `main_benchmark_manifest.json` declares exactly one canonical main benchmark.
- [x] schema2 appears only in appendix / diagnostic whitelist roles.
- [x] Figure 2 default source equals canonical manifest source.
- [x] benchmark table default source equals canonical manifest source.
- [x] evidence matrix benchmark rows equal canonical source values after documented rounding.
- [x] pure-RL evidence rows remain from confirm report and are clearly marked as a separate contract.
- [x] `paper/main.tex` no longer hardcodes main benchmark rows.
- [x] generated LaTeX table includes a do-not-edit provenance comment.
- [x] paper-facing artifacts contain no local absolute paths.
- [x] all paper-facing artifacts include repo-relative source paths and source hashes.
- [x] README primary reproduction command is `build_paper_assets.py`.
- [x] README primary PDF build command is `build_paper_pdf.py`.
- [x] anonymous snapshot contains `tests/reviewer/`.
- [x] `python -m pytest -q tests/reviewer` passes inside the snapshot.
- [x] `python -c "import vi_full"` is lightweight.
- [x] CI / local no-training gate catches source drift.
- [ ] optional v2 experiments are versioned, compared, and promoted only by explicit manifest decision.

---

## Recommended Final Verification Commands

```bash
python -m pytest -q tests/artifacts/test_canonical_manifest.py
python -m pytest -q tests/artifacts/test_artifact_provenance.py
python -m pytest -q tests/paper/test_exporter_defaults.py
python -m pytest -q tests/paper/test_paper_table_sync.py
python -m pytest -q tests/paper/test_three_dof_evidence_matrix.py tests/paper/test_sprint2_paper_sync.py
python -m pytest -q tests/core/test_import_boundaries.py
python -m pytest -q tests/reviewer
python scripts/export/build_paper_assets.py --check
python scripts/export/build_paper_assets.py
python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind
```

Milestone 3 note: local PDF/TeX deployment is not a required gate. `build_paper_pdf.py` remains available as a diagnostic wrapper, but Engineering Trust closure uses no-training Python checks and `build_paper_assets.py --check`.

---

## Critical Implementation Note

If only one slice can be implemented first, implement **Task 1 through Task 5 together**. Partial canonicalization is dangerous: it can make the repository look more formal while still leaving the paper table, Figure 2, evidence matrix, and README on different sources.
