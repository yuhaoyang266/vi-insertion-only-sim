# Progress Log

### Phase 7.1 Sprint A: Bundle Manifest Path Hardening (2026-04-29)
- **Status:** local gate strengthened; remote CI sign-off still pending.
- Actions taken:
  - Strict review found one remaining bundle-facing path-lineage gap: `submission_bundle_manifest.json` recorded absolute local source/output paths even though the anonymous snapshot itself was clean.
  - Updated the submission bundle manifest to redact `source_root` and record snapshot/editor/archive paths relative to the bundle root.
  - Hardened local path scanning for JSON-escaped Windows paths and slash-style drive paths (`F:/...`) so copied reviewer artifacts and reviewer-smoke tests catch both path encodings.
  - Updated submission docs to state that the generated manifest uses portable bundle-relative paths.
- Verification:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/packaging/test_submission_bundle.py tests/reviewer` -> 13 passed.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/core/test_import_boundaries.py tests/reviewer` -> 5 passed.
  - `python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/gate_a1_manifest_check` -> exit 0; generated manifest uses `anonymous_snapshot`, `editor_materials`, and zip filenames rather than absolute paths.
  - From `tmp/submission_bundle/gate_a1_manifest_check/anonymous_snapshot`: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/reviewer` -> 4 passed.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/artifacts/test_canonical_manifest.py tests/artifacts/test_artifact_provenance.py tests/paper/test_exporter_defaults.py tests/paper/test_paper_table_sync.py tests/paper/test_three_dof_evidence_matrix.py tests/paper/test_sprint2_paper_sync.py tests/paper/test_paper_claim_boundaries.py` -> 62 passed, 9 warnings.
  - `python scripts/export/build_paper_assets.py --check` -> exit 0.
  - `git diff --check` -> exit 0.
- Next blocker:
  - Push the committed branch or open a PR, then mark Gate A1 only after GitHub Actions `reviewer-smoke` and `paper-assets-check` pass.

### Phase 7.1 Sprint A: Local Gate A1 Strict Review (2026-04-29)
- **Status:** local gate strengthened; remote CI sign-off still pending.
- Actions taken:
  - Found one reviewer-snapshot leakage risk during strict review: `outputs/pilot_report/three_dof_cross_family_pilot_report.json` embedded the local source path in `chunk_dir`.
  - Updated the cross-family pilot report exporter to keep default chunk paths repo-relative / slash-normalized, then regenerated `outputs/pilot_report/three_dof_cross_family_pilot_report.json` and the companion internal PDFs.
  - Hardened anonymous bundle assembly so copied snapshot files are scanned for the resolved source-root path as well as identity tokens.
  - Added reviewer-smoke coverage that scans reviewer-facing artifact inputs for local path tokens, so Gate A1 catches this class locally and in CI.
- Verification:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/three_dof/test_three_dof_cross_family_pilot_report.py tests/packaging/test_submission_bundle.py tests/reviewer` -> 15 passed, 1 warning.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/core/test_import_boundaries.py tests/reviewer` -> 5 passed.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/artifacts/test_canonical_manifest.py tests/artifacts/test_artifact_provenance.py tests/paper/test_exporter_defaults.py tests/paper/test_paper_table_sync.py tests/paper/test_three_dof_evidence_matrix.py tests/paper/test_sprint2_paper_sync.py tests/paper/test_paper_claim_boundaries.py` -> 62 passed, 9 warnings.
  - `python scripts/export/build_paper_assets.py --check` -> exit 0.
  - `python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/gate_a1_local_check --paper-pdf paper/main.pdf` -> exit 0 after a local PDF wrapper build; MiKTeX printed update-check notices and the existing overfull hbox warning.
  - From `tmp/submission_bundle/gate_a1_local_check/anonymous_snapshot`: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/reviewer` -> 4 passed.
  - `git diff --check` -> exit 0.
- Next blocker:
  - Push the committed branch or open a PR, then mark Gate A1 only after GitHub Actions `reviewer-smoke` and `paper-assets-check` pass.

### Phase 7.1 Sprint A: Post-Commit Gate A1 Checkpoint (2026-04-29)
- **Status:** local gate remains complete; remote CI sign-off still pending.
- Actions taken:
  - Committed the staged Sprint A readiness package as `46cfef70183f22246f2ecf1f52620d674f3f0715` (`feat: finalize sprint a submission readiness`).
  - Fixed one trailing-space issue in `docs/plans/2026-04-25-review-driven-revision-plan.md` before committing so `git diff --cached --check` passes.
  - Reviewed `docs/plans/2026-04-28-12-month-tier2-roadmap-task-list.md` after commit; the only remaining Sprint A item is Gate A1 remote sign-off. Sprint B must not start until the CI workflows pass on the committed branch.
- Verification:
  - `git diff --cached --check` -> exit 0.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/paper/test_build_paper_pdf.py tests/packaging/test_submission_bundle.py tests/reviewer tests/paper/test_paper_table_sync.py tests/paper/test_three_dof_evidence_matrix.py` -> 43 passed, 9 warnings.
  - `python scripts/export/build_paper_assets.py --check` -> exit 0.
  - `python scripts/export/build_paper_pdf.py` -> exit 0; `paper/main.pdf` had 23 pages / 658450 bytes. MiKTeX printed update-check notices and the existing overfull hbox warning, but the build succeeded.
- Next blocker:
  - Push the committed branch or open a PR, then mark Gate A1 only after GitHub Actions `reviewer-smoke` and `paper-assets-check` pass.

### Phase 7.1 Sprint A: Tier-3 Submission Readiness (2026-04-28)
- **Status:** local gate complete; remote CI sign-off still pending.
- Actions taken:
  - Audited Sprint A state against `docs/plans/2026-04-28-12-month-tier2-roadmap-task-list.md`; existing exporter defaults already resolved through `artifacts/main_benchmark/main_benchmark_manifest.json`, but `scripts/export/build_paper_pdf.py`, `REVIEWER_GUIDE.md`, and the Tier-3 cover-letter template were missing.
  - Added `scripts/export/build_paper_pdf.py` with PATH lookup plus Windows MiKTeX fallbacks at `C:\Users\Windows\AppData\Local\Programs\MiKTeX\miktex\bin\x64` and the current-user MiKTeX path; wrapper now runs `pdflatex -> bibtex -> pdflatex -> pdflatex -> pdflatex`.
  - Added anonymized `REVIEWER_GUIDE.md`; updated bundle copying so `REVIEWER_GUIDE.md` and `tests/reviewer/` land in `anonymous_snapshot/`.
  - Regenerated `outputs/evidence_matrix/three_dof_sprint2_main_table.{json,csv,md}` and companion evidence outputs from the canonical manifest; fixed-impedance success now renders as `0.947`, DAPG-lite as `1.000`.
  - Added numeric sync coverage in `tests/paper/test_paper_table_sync.py`, PDF-wrapper tests, and reviewer-guide packaging coverage.
  - Wrote `docs/submission/cover_letter_tier3_template.md`; venue decision: Robotica primary, Advanced Robotics fallback.
- Verification:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/paper/test_build_paper_pdf.py tests/packaging/test_submission_bundle.py tests/reviewer tests/paper/test_paper_table_sync.py tests/paper/test_three_dof_evidence_matrix.py` -> 43 passed, 9 warnings.
  - `powershell -NoProfile -Command "python scripts/export/build_paper_pdf.py; exit $LASTEXITCODE"` -> exit 0; `paper/main.pdf` had 23 pages / 658450 bytes; final log had no unresolved-reference or rerun warnings.
  - `python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind --paper-pdf tmp/submission_bundle/anonymous_manuscript.pdf` -> exit 0; manifest 1565 bytes, anonymous snapshot zip 9407377 bytes, editor materials zip 3888 bytes, PDF 629170 bytes.
  - From `tmp/submission_bundle/journal_double_blind/anonymous_snapshot`: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/reviewer` -> 3 passed.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/core/test_import_boundaries.py tests/reviewer` -> 4 passed.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/artifacts/test_canonical_manifest.py tests/artifacts/test_artifact_provenance.py tests/paper/test_exporter_defaults.py tests/paper/test_paper_table_sync.py tests/paper/test_three_dof_evidence_matrix.py tests/paper/test_sprint2_paper_sync.py tests/paper/test_paper_claim_boundaries.py tests/paper/test_build_paper_pdf.py tests/packaging/test_submission_bundle.py` -> 71 passed, 9 warnings.
  - `python scripts/export/build_paper_assets.py --check` -> exit 0.
- Files changed:
  - `README.md`, `REVIEWER_GUIDE.md`, `scripts/export/build_paper_pdf.py`, `src/vi_full/submission_bundle.py`, `src/vi_full/three_dof_evidence_matrix.py`
  - `outputs/evidence_matrix/three_dof_evidence_matrix.*`, `outputs/evidence_matrix/three_dof_contact_gate_matrix.{png,pdf}`, `outputs/evidence_matrix/three_dof_sprint2_main_table.*`
  - `tests/paper/test_build_paper_pdf.py`, `tests/paper/test_paper_table_sync.py`, `tests/paper/test_three_dof_evidence_matrix.py`, `tests/paper/test_sprint2_paper_sync.py`, `tests/packaging/test_submission_bundle.py`, `tests/reviewer/test_snapshot_smoke.py`
  - `docs/submission/cover_letter_tier3_template.md`, `docs/plans/2026-04-28-12-month-tier2-roadmap-task-list.md`

### Repository Layout Consolidation (2026-04-25)
- **Status:** complete
- Actions taken:
  - Moved long-running project state from the repository root into `docs/project/`: task plan, progress log, findings, narrative branch notes, and protocol freeze notes.
  - Moved agent execution plans to `docs/plans/`, submission-only material to `docs/submission/`, and the SCI review report to `docs/reviews/`.
  - Grouped the root-level test files into purpose-specific directories: `tests/artifacts/`, `tests/core/`, `tests/paper/`, `tests/packaging/`, `tests/runners/`, `tests/sprints/`, and `tests/three_dof/`; kept `tests/reviewer/` stable for anonymous snapshot packaging.
  - Added `docs/README.md` and `tests/README.md` as directory indexes.
  - Updated CI commands, README paths, test repo-root calculations, and submission-bundle editor/excluded path handling for the new layout.
  - Rebuilt the final `tmp/submission_bundle/journal_double_blind` package with the existing anonymous PDF, then removed extracted staging directories so only package artifacts remain.
  - Fixed the benchmark-table CLI smoke test so it writes its LaTeX probe to `tmp_path` instead of mutating tracked `paper/generated/main_benchmark_table.tex`.
- Verification:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q` -> 204 passed, 15 skipped, 11 warnings.
  - `python scripts/export/build_paper_assets.py --check` -> completed without diffs.
  - `python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/structure_smoke` followed by `python -m pytest -q tests/reviewer` inside the temporary anonymous snapshot -> 3 passed; temporary output removed.
  - `python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind --paper-pdf tmp/submission_bundle/anonymous_manuscript.pdf` followed by `python -m pytest -q tests/reviewer` inside the rebuilt anonymous snapshot -> 3 passed; extracted staging directories removed after verification.

### Milestone 3: Engineering Trust Closure And Workspace Cleanup (2026-04-25)
- **Status:** complete
- Actions taken:
  - Cleaned ignored workspace residue while preserving tracked sources, paper assets, final submission zip/materials, manifest, summary, and anonymous PDF.
  - Removed Python/pytest caches, obsolete numbered scratch notes, old runner scripts/logs, the schema2 temporary compile zip, the Sprint 4 smoke scratch directory, the superseded `tmp/submission_bundle/audit_rebuild/`, and redundant extracted directories under `tmp/submission_bundle/journal_double_blind/`.
  - Marked Task 10, Task 11, and Task 13 complete in both Milestone 3 planning documents; left Task 12 and Milestone 4 scientific strengthening open.
  - Updated `docs/project/task_plan.md` so the current phase records Milestone 3 as complete and keeps local PDF/TeX deployment outside the blocking gate.
- Verification:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/core/test_import_boundaries.py tests/paper/test_paper_claim_boundaries.py tests/artifacts/test_canonical_manifest.py tests/artifacts/test_artifact_provenance.py tests/paper/test_exporter_defaults.py tests/paper/test_paper_table_sync.py tests/paper/test_three_dof_evidence_matrix.py tests/paper/test_sprint2_paper_sync.py tests/reviewer` -> 60 passed, 9 warnings.
  - Temporary extraction of `tmp/submission_bundle/journal_double_blind/anonymous_snapshot.zip` followed by `python -m pytest -q tests/reviewer` inside the extracted snapshot -> 3 passed.
  - `python scripts/export/build_paper_assets.py --check` -> completed without diffs.
  - `PYTHONPATH=src python -c "import vi_full; print(vi_full.__version__)"` -> `0.1.0`.
- Files modified:
  - `F:\edge download\learning\vi-insertion-only-sim\docs\plans\2026-04-24-canonical-paper-artifact-hardening.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\plans\2026-04-25-milestone-3-engineering-trust.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

### Milestone 3: Engineering Trust Planning (2026-04-25)
- **Status:** complete
- Actions taken:
  - Opened a dedicated Milestone 3 execution plan for Task 10, Task 11, and Task 13 at `docs/plans/2026-04-25-milestone-3-engineering-trust.md`.
  - Recorded the user constraint that Milestone 2 paper-facing reproducibility is complete, but local LaTeX/PDF deployment should not be a blocking gate.
  - Checked current M3 baselines: `src/vi_full/__init__.py` is already lightweight, `tests/core/test_import_boundaries.py` exists, `.github/` does not exist yet, and `tests/paper/test_paper_claim_boundaries.py` does not exist yet.
  - Updated the canonical hardening plan so Task 13 defers PDF rebuild to an external/editor environment and Milestone 2 tasks are marked complete.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\docs\plans\2026-04-25-milestone-3-engineering-trust.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\plans\2026-04-24-canonical-paper-artifact-hardening.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\findings.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

### Phase 5: Submission Package Finalization (2026-04-23)
- **Status:** complete
- Actions taken:
  - Installed `MiKTeX.MiKTeX` via `winget`, generated a fresh anonymous snapshot with `scripts/export/build_submission_bundle.py`, and compiled the manuscript from the staged anonymous `paper/` directory rather than from the named source tree.
  - Switched the local build path from `latexmk` to direct `pdflatex -> bibtex -> pdflatex` passes after MiKTeX reported that `latexmk` could not run without a `perl` script engine.
  - Verified the generated PDF with `pdfinfo` plus extracted-text token scans to confirm that author name, email, affiliation, and public repository URL do not survive into the anonymous manuscript.
  - Rebuilt `tmp/submission_bundle/journal_double_blind/` with `--paper-pdf` so the final staged package now includes the anonymous manuscript alongside `anonymous_snapshot/`, `editor_materials/`, both zip archives, and a manifest with `paper_pdf.status = included`.
  - Synced `docs/project/task_plan.md` and `docs/submission/submission_package_checklist.md` so the repository-facing Phase 5 status matches the completed local package.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\submission\submission_package_checklist.md`

### Phase 5: Anonymous Submission Bundle Staging (2026-04-23)
- **Status:** complete
- Actions taken:
  - Added `src/vi_full/submission_bundle.py` plus the repo-root CLI `scripts/export/build_submission_bundle.py` so Phase 5 can now generate a reviewer-facing anonymous snapshot and a separate editor-only staging directory instead of relying on a manual checklist.
  - Followed TDD for the new packaging contract: wrote failing tests for anonymous redaction, optional PDF inclusion, and CLI defaults; then implemented the minimal builder and repo-root `--help` coverage.
  - Tightened the anonymous snapshot boundary after an actual dry run exposed leakage through test fixtures and literal redaction strings: the builder now excludes `tests/`, uses generic email/URL patterns in the redaction code, and runs an identity-token scan over the staged snapshot before declaring success.
  - Generated a real staged bundle at `tmp/submission_bundle/journal_double_blind/` with `anonymous_snapshot/`, `editor_materials/`, `submission_bundle_manifest.json`, `submission_bundle_summary.md`, `anonymous_snapshot.zip`, and `editor_materials.zip`.
  - Narrowed the remaining Phase 5 blocker to TeX availability only: the local machine still lacks `latexmk`, `pdflatex`, and `xelatex`, so the final anonymous paper PDF must be added later via `--paper-pdf`.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\submission_bundle.py`
  - `F:\edge download\learning\vi-insertion-only-sim\scripts\export\build_submission_bundle.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\packaging\test_submission_bundle.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\runners\test_run_submission_bundle.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\runners\test_run_3dof_experiment_entrypoints.py`
  - `F:\edge download\learning\vi-insertion-only-sim\README.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\submission\submission_package_checklist.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

### Phase 5: Submission Package Probe (2026-04-23)
- **Status:** complete
- Actions taken:
  - Probed the local TeX toolchain and confirmed that `latexmk`, `pdflatex`, and `xelatex` are all missing in the current environment, so a fresh paper PDF cannot be built locally right now.
  - Audited the current identity surfaces and confirmed the working tree is not an anonymized snapshot because `paper/main.tex`, `README.md`, and `docs/submission/github_upload.md` still expose the public author/repository identity.
  - Added `docs/submission/submission_package_checklist.md` to capture package contents, completion criteria, and the current blockers.
  - Added `docs/submission/cover_letter_draft.md` so the remaining open submission task already has a venue-facing draft rather than only a TODO line.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\docs\submission\submission_package_checklist.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\submission\cover_letter_draft.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`

### Phase 5: Delivery Audit for CLI Closure and Teacher Serialization (2026-04-23)
- **Status:** complete
- Actions taken:
  - Verified repo-root experiment/export entrypoints after the Sprint 3/4 bundle work, including stripped-`PYTHONPATH` smoke for the Sprint 3 kickoff exporter and repo-root `--help` coverage for the Sprint 4 exporter.
  - Re-ran the teacher serialization regression suite to confirm resolved teacher metadata still survives training-config, dataset-metadata, and training-summary serialization.
  - Promoted the first two Phase 5 checklist items in `docs/project/task_plan.md` to complete; only the submission package remains open.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\tests\runners\test_run_3dof_experiment_entrypoints.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\runners\test_run_sprint3_teacher_mini_ablation_kickoff.py`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`

### Phase 4: Reviewer-Facing Sprint 3/4 Figure Pipeline Close-out (2026-04-23)
- **Status:** complete
- Actions taken:
  - Extended the Sprint 3 kickoff exporter from `json/md` into a full reviewer-facing bundle: `json/csv/md` plus a kickoff matrix figure under `outputs/sprint3_teacher_mini_ablation/`.
  - Extended the Sprint 4 clearance-shift exporter to emit a summary figure under `outputs/sprint4_clearance_shift/` while preserving the existing pure-clearance contract and tracked JSON / CSV / Markdown outputs.
  - Synced `README.md`, `docs/figure_asset_manifest.md`, and `docs/project/task_plan.md` so the new artifact paths are discoverable and Phase 4 now closes as complete with Phase 5 next.
  - Verified the focused Sprint 3/4 export/doc suite after writing the new bundles.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\sprint3_teacher_mini_ablation_kickoff.py`
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\sprint4_clearance_shift.py`
  - `F:\edge download\learning\vi-insertion-only-sim\scripts\experiments\export_sprint3_teacher_mini_ablation_kickoff.py`
  - `F:\edge download\learning\vi-insertion-only-sim\scripts\experiments\export_sprint4_clearance_shift.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\sprints\test_sprint3_teacher_mini_ablation_kickoff.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\runners\test_run_sprint3_teacher_mini_ablation_kickoff.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\sprints\test_sprint4_clearance_shift.py`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\sprint3_teacher_mini_ablation\sprint3_teacher_mini_ablation_kickoff.csv`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\sprint3_teacher_mini_ablation\sprint3_teacher_mini_ablation_kickoff_matrix.pdf`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\sprint3_teacher_mini_ablation\sprint3_teacher_mini_ablation_kickoff_matrix.png`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\sprint4_clearance_shift\sprint4_clearance_shift_summary.pdf`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\sprint4_clearance_shift\sprint4_clearance_shift_summary.png`
  - `F:\edge download\learning\vi-insertion-only-sim\README.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\figure_asset_manifest.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`

### Phase 4: Sprint 4 Findings Integrated Into Manuscript (2026-04-23)
- **Status:** complete
- Actions taken:
  - Restored the unmerged Sprint 4 manuscript patch so the main text now references the cross-family pure-RL negative-evidence layer, the frozen Sprint 3 teacher-boundary artifact, and the Sprint 4A clearance-shift sweep.
  - Updated the abstract, introduction, experiments, discussion, and limitations to keep the paper-facing claim boundary explicit: benchmark-local, no-hardware, and train-once / eval-many-profile because paper-ready checkpoints are not persisted.
  - Kept the clearance ladder framed as a sprint-specific robustness stress test rather than a replacement for the frozen five-profile benchmark.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\paper\main.tex`

### Phase 3: Sprint 4A Clearance Shift Sweep (2026-04-23)
- **Status:** complete
- Actions taken:
  - Restored the missing Sprint 4A sweep/export code and tracked artifacts from the repo-local branch history.
  - Added a dedicated pure-clearance ladder with `clearance_easy`, `nominal`, and `clearance_hard`, keeping offset, friction, force noise, and the nominal train profile fixed.
  - Exported reviewer-facing JSON / CSV / Markdown artifacts and kept the contract explicit: selected demo-supported suites only, not a mixed-contract leaderboard and not a replacement for the frozen benchmark.
  - Synced repo-facing docs so README / manifest / task-plan references now point to the Sprint 4A exporter and artifact bundle.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\sprint4_clearance_shift.py`
  - `F:\edge download\learning\vi-insertion-only-sim\scripts\experiments\export_sprint4_clearance_shift.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\sprints\test_sprint4_clearance_shift.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\runners\test_run_sprint4_clearance_shift.py`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\sprint4_clearance_shift\sprint4_clearance_shift.json`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\sprint4_clearance_shift\sprint4_clearance_shift.csv`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\sprint4_clearance_shift\sprint4_clearance_shift.md`
  - `F:\edge download\learning\vi-insertion-only-sim\README.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\figure_asset_manifest.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`

### Phase 3: Sprint 3 Teacher Mini-Ablation Kickoff (2026-04-23)
- **Status:** complete
- Actions taken:
  - Froze Sprint 3 as a 4-condition teacher support quality x demo rollout budget kickoff boundary before launching new training.
  - Added machine-readable and Markdown kickoff artifacts under `outputs/sprint3_teacher_mini_ablation/`.
  - Kept `bc_pretrain_steps=32`, `bc_batch_size=64`, `total_timesteps=128`, BC-to-PPO initialization, and five-profile evaluation fixed.
  - Required Sprint 2 claim-control metrics plus `support_coverage_index` and `support_cell_coverage`; excluded BC-step, policy-init, no-teacher, and full appendix motion脳impedance sweeps from the kickoff.
  - Added tests covering the 4-condition matrix, teacher registry metadata alignment, deterministic export, CLI export, and repo-doc references.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\sprint3_teacher_mini_ablation_kickoff.py`
  - `F:\edge download\learning\vi-insertion-only-sim\scripts\experiments\export_sprint3_teacher_mini_ablation_kickoff.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\sprints\test_sprint3_teacher_mini_ablation_kickoff.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\runners\test_run_sprint3_teacher_mini_ablation_kickoff.py`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\sprint3_teacher_mini_ablation\sprint3_teacher_mini_ablation_kickoff.json`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\sprint3_teacher_mini_ablation\sprint3_teacher_mini_ablation_kickoff.md`
  - `F:\edge download\learning\vi-insertion-only-sim\README.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\figure_asset_manifest.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

### Housekeeping: SCI Residue Decision (2026-04-23)
- **Status:** complete
- Actions taken:
  - Confirmed the substantive SCI guardrails work was already landed in `0638087`, `e807e29`, `7546b4d`, and `ed189e9`.
  - Kept the remaining repo-facing residue narrow: committed SCI rollout helper docstrings in `6e7364b` and the pytest startup guard against the unused `zarr` plugin in `05b264f`.
  - Removed local-only execution residue: empty root `conftest.py` and `docs/superpowers/` plan/spec files.
  - Verified `python -m pytest -q tests/three_dof/test_three_dof_support_metrics.py` and the two root experiment-wrapper regressions.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\pyproject.toml`
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_benchmark.py`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

### Phase 3: Sprint 2 Main Table / Figures Close-out
- **Status:** complete
- Actions taken:
  - Reviewed Sprint 2 table/figure scope across commits `a272ff8..3af22a4` plus `81c9345`.
  - Confirmed the reviewer-facing Sprint 2 outputs are already landed: three-layer main table, evidence matrix, contact-gate matrix, and pure-RL budget-curve summary.
  - Confirmed the paper-facing boundary remains narrow: the Sprint 2 table is claim control, not a mixed-contract leaderboard; `SAC w/o BC` is only a zero-contact distance proxy.
  - Confirmed old stage3 frozen-artifact names are absent from active user-facing README / manifest / paper / script entrypoints; remaining stage3 strings are legacy test references, not user-facing entrypoints.
  - Updated `docs/project/task_plan.md` from "Phase 3 Sprint 2B complete; next: Sprint 2 main table" to "Phase 3 Sprint 2 complete; next: Sprint 3 teacher mini-ablation".
  - Aligned the Sprint 2 deliverable line with the actual closed assets: three-layer claim-control table, contact-gate matrix, and pure-RL budget-curve figure under separate evidence contracts.
  - Explicitly excluded existing workspace residue from the Sprint 2 close-out judgment: `pyproject.toml`, `src/vi_full/three_dof_benchmark.py`, `conftest.py`, and `docs/superpowers/`.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

### Phase 4: SG-VI / SCI Contribution Landing
- **Status:** complete
- Actions taken:
  - Landed the named method `Support-Gated Variable-Impedance Learning (SG-VI)` into the paper title, abstract, introduction, setup, discussion, and conclusion.
  - Landed the diagnostic metric `Support Coverage Index (SCI)` as an explicit benchmark-local formula over a projected, quantized state-action signature.
  - Added `src/vi_full/three_dof_support_metrics.py` plus rollout-sample collectors and regression tests so SCI is code-level, not only wording.
  - Updated `README.md` to mirror the constructive framing and link the new support-metric module.
  - Verified the focused Python regression suite; manuscript compile was attempted but the environment does not provide `latexmk` or `pdflatex`.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\paper\main.tex`
  - `F:\edge download\learning\vi-insertion-only-sim\README.md`
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_support_metrics.py`
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_benchmark.py`
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\__init__.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\three_dof\test_three_dof_support_metrics.py`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\findings.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

### Phase 3: Sprint 2B Strict-Review Contract Hardening
- **Status:** complete
- Actions taken:
  - Tightened the evidence-matrix builder so the pure-RL distance-proxy claim now follows `best_distance_proxy_method` from the direct confirm JSON rather than a hardcoded SAC assumption.
  - Added fail-fast validation for reviewer-facing confirm summary fields and anchor `five_profile_mean` metrics, preventing incomplete inputs from silently exporting zero-valued evidence rows.
  - Added regression tests for dynamic distance-proxy attribution and missing-field rejection.
  - Re-exported the tracked JSON / CSV / Markdown evidence-matrix artifacts from the real confirm + schema2 benchmark inputs.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_evidence_matrix.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\paper\test_three_dof_evidence_matrix.py`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\evidence_matrix\three_dof_evidence_matrix.json`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\evidence_matrix\three_dof_evidence_matrix.csv`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\evidence_matrix\three_dof_evidence_matrix.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\findings.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

### Phase 3: Sprint 2B Anchor-Integrated Evidence Matrix
- **Status:** complete
- Actions taken:
  - Added `src/vi_full/three_dof_evidence_matrix.py` to merge Branch-A confirm evidence with canonical five-profile benchmark anchors.
  - Added `scripts/experiments/export_3dof_evidence_matrix.py` to export JSON, CSV, Markdown, and contact-gate PNG/PDF artifacts.
  - Wrote new contract tests for the matrix builder and CLI exporter.
  - Generated `outputs/evidence_matrix/three_dof_evidence_matrix.{json,csv,md}` and `outputs/evidence_matrix/three_dof_contact_gate_matrix.{png,pdf}` from the real confirm and benchmark artifacts.
  - Updated `docs/project/protocol_freeze.md`, `docs/project/task_plan.md`, `docs/project/findings.md`, and `paper/main.tex` so the mixed-contract boundary is explicit and SAC stays framed as a distance proxy rather than a success baseline.
  - Tightened row-level provenance after review: matrix rows now cite the direct confirm JSON or schema2 benchmark JSON inputs, rather than indirect upstream pilot/table exports.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_evidence_matrix.py`
  - `F:\edge download\learning\vi-insertion-only-sim\scripts\experiments\export_3dof_evidence_matrix.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\paper\test_three_dof_evidence_matrix.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\runners\test_run_3dof_evidence_matrix.py`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\evidence_matrix\three_dof_evidence_matrix.json`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\evidence_matrix\three_dof_evidence_matrix.csv`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\evidence_matrix\three_dof_evidence_matrix.md`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\evidence_matrix\three_dof_contact_gate_matrix.png`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\evidence_matrix\three_dof_contact_gate_matrix.pdf`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\protocol_freeze.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\findings.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

### Phase 3: Sprint 2A Branch-A Confirm Benchmark Pack
- **Status:** complete
- Actions taken:
  - Created `docs/project/narrative_branches.md` and locked Branch A on 2026-04-20 Asia/Shanghai.
  - Updated `docs/project/protocol_freeze.md` with the Cross-Family Confirm Interpretation Boundary.
  - Updated planning notes to record: Sprint 1 full pilot completed 9/9 chunks; selected narrative branch A; no pure-RL method reached contact; SAC is only a terminal-distance proxy advantage.
  - Recorded the next Sprint 2 direction: compare Branch-A pure-RL failure against demo-supported anchors, not oversell SAC.
  - Added confirm report module, CLI exporter, contract tests, and paper-facing artifacts.
  - Hardened the confirm report contract so `summary_rows` must cover the full method-budget grid, not only report complete metadata.
  - Verified the focused confirm test suite with `8 passed in 12.18s`.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\narrative_branches.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\protocol_freeze.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\findings.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

## Session: 2026-04-18

### Phase 1: Repository & Paper Discovery
- **Status:** complete
- **Started:** 2026-04-18 Asia/Shanghai
- Actions taken:
  - 璇诲彇 `using-superpowers` 涓?`planning-with-files` 鎶€鑳借鏄庯紝纭鏈浠诲姟搴旈噰鐢ㄦ枃浠跺寲瑙勫垝娴佺▼銆?  - 纭澶栧眰鐩綍涓嶆槸浠撳簱锛岄」鐩牴鐩綍浣嶄簬 `F:\edge download\learning\vi-insertion-only-sim`銆?  - 璇诲彇 planning templates锛屽苟鍦ㄩ」鐩牴鐩綍鍒涘缓 `docs/project/task_plan.md`銆乣findings.md`銆乣progress.md`銆?  - 闃呰 `README.md`锛屾彁鍙栧綋鍓?manuscript claim銆乪vidence map 涓?jam metric semantics銆?  - 灏濊瘯鐢?`rg` 鎵弿璁烘枃涓庤剼鏈叧閿瘝锛屽彂鐜板綋鍓嶇幆澧?`rg.exe` 涓嶅彲鐢紝鍐冲畾鍒囨崲鍒?`Select-String`銆?  - 鎵弿 `paper/main.tex`锛岀‘璁ゅ綋鍓?contributions/limitations 宸叉槑纭毚闇?off-policy銆乼eacher prior銆乻im-only 涓夌被鐭澘銆?  - 鎵弿 `src` 涓?`tests`锛岀‘璁ょ幇鏈?appendix teacher block 涓?2x2 缁撴瀯锛屼絾 `SAC/TD3` 浠ｇ爜涓庣敤鎴风偣鍚嶇殑 3 涓?contract tests 鏆備笉瀛樺湪銆?  - 鎻愬彇褰撳墠姝ｆ枃 section 楠ㄦ灦銆佷富琛ㄥ垪瀹氫箟涓?teacher spec registry 鐨勭簿纭畾涔夛紝涓哄悗缁鍒掓敹鏁涙彁渚?repo-level 渚濇嵁銆?- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md` (created)
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\findings.md` (created)
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md` (created)

### Phase 2: Plan Audit & Narrative Lock
- **Status:** in_progress
- Actions taken:
  - 鍩轰簬浠撳簱鐜扮姸璇勪及鐢ㄦ埛鎻愬嚭鐨?Sprint 0-6 鑽夋锛岃瘑鍒摢浜涢儴鍒嗘槸浣庢懇鎿︽墿灞曪紝鍝簺閮ㄥ垎鏄柊鐨勫伐绋嬪叆鍙ｃ€?  - 璇诲彇 PPO-only large-budget runner銆佽缁?config 鍜岀幆澧冪粓姝㈣涔夛紝纭 Sprint 0 鍙洿缁曠幇鏈?runner + 鏂?regression tests 蹇€熸敹鍙ｃ€?- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\findings.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

## Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Repo root detection | `git status --short` in outer dir | Either repo status or clear error | Reported not a git repository; located repo in subdir | pass |

## Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| 2026-04-18 | `git status` failed in outer working dir | 1 | Inspected child directory and switched planning target to repo root |
| 2026-04-18 | `rg.exe` failed with `Access is denied` | 1 | Switched repository search strategy to PowerShell `Select-String` |
| 2026-04-18 | PowerShell line-range extraction for teacher spec failed because the pattern matched multiple definitions | 1 | Narrow future reads to single paths / single matches |

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | Phase 2 in_progress(narrative lock 鏈畬鎴?;Phase 2.5 Hardware Decision Gate 涓轰笅涓€涓樉鎬?blocker;Phase 3 sim-only 宸ヤ綔鍙笌 2.5 骞惰鍚姩 |
| Where am I going? | Phase 3(sim-only 5 涓?Sprint)鈫?Phase 3.5/H(conditional on 纭欢鍐崇瓥)鈫?Phase 4(璁烘枃 rewrite,contribution 閲嶆瀯涓?propose+show)鈫?Phase 5(submission package) |
| What's the goal? | 鎺ㄨ繘鍒?SCI Q2 闈?OA(T-ASE / T-MECH / MSSP 妗?;鑻?Phase 2.5 = Rizon 4s / Franka Research 3 鍒欎笂璋冭嚦 Q1(T-RO / IJRR);鑻?no-hardware 鍒欏洖閫€ Q3 涓婃父 + cross-sim 鎴?named method 琛ュ伩 |
| What have I learned? | 1) `src/` 鏃?SAC/TD3 浠ｇ爜,Sprint 1 蹇呴』鏂板缓 `training_baselines.py`,涓嶆槸闆舵垚鏈墿灞?2) 褰撳墠 teacher 2脳2 registry 鏄?`motion 脳 impedance`(`teacher_variable_variable` 绛?4 涓?preset),涓嶆槸 `teacher_type 脳 demo_quality/quantity`,Sprint 3 闇€瑕佸姞姝ｄ氦杞?3) 鐢ㄦ埛鐐瑰悕鐨?3 涓?contract tests(force_jam consecutive / blocked_contact separate / ppo-only disables auxiliary)褰撳墠 `tests/` 涓嬩笉瀛樺湪,闇€鏂板缓;4) Abstract 鑷О `simulation-only` + 4 鏉?contribution 鍏ㄤ负 `we show` = Q2 澶╄姳鏉跨殑涓や釜纭激,蹇呴』鏈?`we propose` + 鐪熸満/璺ㄤ豢鐪熶簩閫変竴琛ュ伩;5) 纭欢鍐崇瓥鍙?block Phase H 鍜?Phase 3.5 鏂瑰悜鏍″噯,**涓?block** Phase 3(sim-only 绾?70% 鏀瑰姩涓庣‖浠惰В鑰?;6) Synria Alicia-M/D 涓嶉€傚悎鍋?primary real-robot validation(joint-level MIT銆佹棤 FT sensor銆佷覆鍙?200 Hz銆佺簿搴︽湭鍏紑);Flexiv Rizon 4s 鍏ㄦ。浣嶈秴閰?Franka Research 3 / 浜屾墜 Panda 涓?Q2 绋冲Ε閫€璺?|
| What have I done? | 瀹屾垚 repo/paper audit;鎶婄敤鎴?Sprint 0-5 鑽夋 lift 鎴?phase-gated plan(Phase 1 / 2 / 2.5 / 3 / 3.5 / H / 4 / 5);`docs/project/task_plan.md` 宸插姞 dependency graph銆乪ffort/risk/status/deliverable 瀛楁銆丮eta vs Research decision 鎷嗗垎;灏氭湭淇敼璁粌浠ｇ爜鎴栦骇鍑?`docs/project/narrative_branches.md` / `hardware_decision.md` |

---
*Update after completing each phase or encountering errors*

### Phase 3: Sprint 0 Hardening
- **Status:** complete
- Actions taken:
  - 鏍规嵁 review 琛ュ己 `docs/project/protocol_freeze.md`锛氬姞鍏ョ幆澧冪増鏈攣銆佺ǔ瀹氶敋鐐广€乧ondition x profile 鐨?200k 鍦版澘琛紝浠ュ強 `50k / 100k` 寰呯‘璁よ鏄庛€?  - 鍦?`test_run_3dof_ppo_large_budget_ablation.py` 涓ˉ鍏?PPO-only condition 鍚嶅崟鏂█鍜?condition-specific optimizer 鏂█銆?  - 鍦?`test_three_dof_contract.py` 涓ˉ鍏?blocked-contact persistence 璐熶緥鍜?force-jam interruption reset 璐熶緥銆?  - 灏?`docs/project/task_plan.md` 涓殑 Sprint 0 checkbox 鏍囪涓哄畬鎴愩€?- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\protocol_freeze.md`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\runners\test_run_3dof_ppo_large_budget_ablation.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\three_dof\test_three_dof_contract.py`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\findings.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

## Sprint 0 Hardening Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Sprint 0 hardening regression suite | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q .\\tests\\test_three_dof_contract.py .\\tests\\test_run_3dof_ppo_large_budget_ablation.py` | New edge-case and registry assertions stay green | `10 passed in 6.24s` | pass |
### Phase 3: Sprint 0 Execution
- **Status:** in_progress
- Actions taken:
  - 灏嗙幇鏈?env contract tests 瀵归綈涓?paper-facing 鍚嶇О锛歚test_force_jam_requires_consecutive_violations` 涓?`test_blocked_contact_failure_is_separate_reason`銆?  - 鎸?TDD 鏂板 `test_ppo_only_protocol_disables_all_auxiliary_stages`锛屽厛瑙傚療鍏跺洜 registry 渚濊禆闅愬紡榛樿鍊艰€屽け璐ャ€?  - 鍦?`src/vi_full/three_dof_benchmark.py` 鏂板 `_PPO_ONLY_PROTOCOL_FREEZE_OVERRIDES`锛岃涓や釜 PPO-only conditions 鏄惧紡鍐荤粨 auxiliary-stage disable keys銆?  - 鍒涘缓 `docs/project/protocol_freeze.md`锛屽啓鍏?canonical command銆乫rozen profiles銆乧onditions銆乨isable contract 涓庨鏈?200k 璐熺粨鏋溿€?  - 杩愯 200k reproduction锛屼骇鍑?`outputs/three_dof_ppo_large_budget_ablation_200k_repro.json`銆?- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_benchmark.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\three_dof\test_three_dof_contract.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\runners\test_run_3dof_ppo_large_budget_ablation.py`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\protocol_freeze.md`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\three_dof_ppo_large_budget_ablation_200k_repro.json`

## Sprint 0 Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Sprint 0 regression suite (RED) | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q .\\tests\\test_three_dof_contract.py .\\tests\\test_run_3dof_ppo_large_budget_ablation.py` | New protocol-freeze test fails for expected reason | Failed because PPO-only registry omitted explicit auxiliary-stage freeze overrides | pass |
| Sprint 0 regression suite (GREEN) | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q .\\tests\\test_three_dof_contract.py .\\tests\\test_run_3dof_ppo_large_budget_ablation.py` | All targeted regression tests pass | `8 passed in 6.42s` | pass |
| PPO-only 200k reproduction | `python .\\scripts\\experiments\\run_3dof_ppo_large_budget_ablation.py --budgets 200000 --output .\\outputs\\three_dof_ppo_large_budget_ablation_200k_repro.json` | Both PPO-only conditions remain in non-contact regime | Both conditions: success=0, contact_steps=0, first_contact=64, peak_force=0 | pass |

## Sprint 0 Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| 2026-04-18 | `pytest` plugin autoload crashed via `zarr` and `numpy.dtypes` mismatch | 1 | Re-ran targeted tests with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` |
| 2026-04-18 | First JSON summary script for reproduction artifact hit a PowerShell empty-pipe parser error | 1 | Rewrote the extraction with an explicit row accumulator |
### Phase 3: Sprint 1 Scaffolding
- **Status:** in_progress
- Actions taken:
  - Added `src/vi_full/three_dof_cross_family_baselines.py` as a minimal algorithm-agnostic 3DoF training layer for `PPO`, `SAC`, and `TD3`
  - Added `build_3dof_cross_family_pilot_registry()` with default pure-RL methods `ppo_no_bc / sac_no_bc / td3_no_bc`
  - Added `scripts/experiments/run_3dof_cross_family_pilot.py` to materialize the method x budget pilot grid into a JSON artifact
  - Reused `VecNormalizePredictor + evaluate_3dof_predictor` so Sprint 1 can stay off the PPO/BC mainline code path
  - Fixed the new baseline trainer to force `device='cpu'` and avoid the SB3 MLP-on-GPU warning during pilot runs
  - Ran a real smoke command and wrote `F:\edge download\learning\vi-insertion-only-sim\outputs\three_dof_cross_family_pilot_smoke.json`
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_cross_family_baselines.py`
  - `F:\edge download\learning\vi-insertion-only-sim\scripts\experiments\run_3dof_cross_family_pilot.py`
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\__init__.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_three_dof_cross_family_baselines.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_run_3dof_cross_family_pilot.py`

## Sprint 1 Scaffolding Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Cross-family runner + baseline contract suite | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q .\\tests\\test_three_dof_cross_family_baselines.py .\\tests\\test_run_3dof_cross_family_pilot.py` | New module and runner contracts pass | `4 passed in 6.36s` | pass |
| Sprint 0 + Sprint 1 targeted regression suite | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q .\\tests\\test_three_dof_contract.py .\\tests\\test_run_3dof_ppo_large_budget_ablation.py .\\tests\\test_three_dof_cross_family_baselines.py .\\tests\\test_run_3dof_cross_family_pilot.py` | New pilot scaffolding does not regress Sprint 0 contracts | `14 passed in 9.91s` | pass |
| Cross-family pilot smoke | `python .\\scripts\\experiments\\run_3dof_cross_family_pilot.py --seeds 0 --episodes 1 --budgets 8 --profiles nominal --output .\\outputs\\three_dof_cross_family_pilot_smoke.json` | All three methods write a pilot artifact | `ppo_no_bc/sac_no_bc/td3_no_bc` all completed and wrote JSON | pass |

### Phase 3: Sprint 1 Reporting & Full Pilot Execution
- **Status:** complete
- Actions taken:
  - Added `src/vi_full/three_dof_cross_family_pilot_report.py` to merge per-method per-budget chunk artifacts, detect missing grid cells, and flatten pilot-facing metrics.
  - Added `scripts/experiments/export_3dof_cross_family_pilot_report.py` to export a merged JSON report plus two internal figures (`success_vs_budget`, `first_contact_step_vs_budget`).
  - Wrote and passed new tests for report merge/export contracts and CLI execution.
  - Exported the final Sprint 1 report to `outputs/pilot_report/three_dof_cross_family_pilot_report.json`.
  - Completed and merged the full 9/9 method-budget pilot grid:
    `ppo_no_bc@50k/100k/200k`, `sac_no_bc@50k/100k/200k`, and `td3_no_bc@50k/100k/200k`.
  - Refreshed both internal figure pairs from the final merged report.
  - Recorded Branch A evidence: all pure-RL rows have `success_rate=0`, `mean_contact_steps=0`, and `mean_first_contact_step=64`; SAC only improves the terminal-distance proxy.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_cross_family_pilot_report.py`
  - `F:\edge download\learning\vi-insertion-only-sim\scripts\experiments\export_3dof_cross_family_pilot_report.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_three_dof_cross_family_pilot_report.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_run_3dof_cross_family_pilot_report.py`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_chunks\three_dof_cross_family_pilot__sac_no_bc__200000.json`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_chunks\three_dof_cross_family_pilot__td3_no_bc__200000.json`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_report\three_dof_cross_family_pilot_report.json`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_report\three_dof_cross_family_pilot_success_vs_budget.pdf`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_report\three_dof_cross_family_pilot_success_vs_budget.png`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_report\three_dof_cross_family_pilot_first_contact_step_vs_budget.pdf`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_report\three_dof_cross_family_pilot_first_contact_step_vs_budget.png`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\findings.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

## Sprint 1 Reporting & Full Pilot Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Cross-family report + CLI contract suite | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q .\\tests\\test_three_dof_cross_family_baselines.py .\\tests\\test_run_3dof_cross_family_pilot.py .\\tests\\test_three_dof_cross_family_pilot_report.py .\\tests\\test_run_3dof_cross_family_pilot_report.py` | Runner, report merge/export, and CLI stay green together | `9 passed, 1 fontTools warning in 12.98s` | pass |
| Full pilot report export | `python .\\scripts\\experiments\\export_3dof_cross_family_pilot_report.py --chunk-dir .\\outputs\\pilot_chunks --output-dir .\\outputs\\pilot_report` | Merge all 9 chunks and refresh two internal figures | Wrote JSON + 4 figure files; merged report records `completed_chunk_count=9`, `missing_chunk_count=0`; stderr only showed the existing `gym` deprecation warning and a `fontTools` deprecation warning during matplotlib export | pass |
| Merged report invariant check | PowerShell JSON assertion over `outputs\\pilot_report\\three_dof_cross_family_pilot_report.json` | `completed=9`, `missing=0`, `summary_rows=9`, all rows preserve Branch A contact invariants | `report_json_ok completed=9 missing=0 branch_a_rows=9` | pass |
| Internal figure artifact check | PowerShell file-size assertion over the 2 PDF + 2 PNG report figures | All refreshed figure files exist and are non-empty | Success figure: `18256`/`55150` bytes; first-contact figure: `18651`/`58337` bytes | pass |
| Real pilot chunk: TD3 50k | background queue invoking `python .\\scripts\\experiments\\run_3dof_cross_family_pilot.py --methods td3_no_bc --budgets 50000 --output .\\outputs\\pilot_chunks\\three_dof_cross_family_pilot__td3_no_bc__50000.json` | Materialize the missing `td3_no_bc@50k` chunk | Wrote JSON; `success_mean_over_profiles=0.0`; `mean_final_distance鈮?0.78 mm`; `mean_first_contact_step=64` | pass |

### Phase 6 Planning: Review-Driven Revision Hardening (2026-04-25)
- **Status:** P0 complete; P1/P2 remain planned.
- Actions taken:
  - Created review response matrix with explicit success criteria.
  - Split revision priorities into P0/P1/P2.
  - Reframed manuscript around support, motion, and impedance causal factors.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\docs\reviews\review_response_matrix_2026-04-25.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\docs\project\progress.md`

### Phase 6 P0 Closure: Review-Driven Revision Hardening (2026-04-26)
- **Status:** P0.1-P0.5 closed with bounded claims.
- Actions taken:
  - Marked P0.1-P0.5 complete in `docs/plans/2026-04-25-review-driven-revision-task-list.md`.
  - Updated `docs/project/task_plan.md` Phase 6 status to "P0 complete; P1/P2 planned".
  - Expanded SCI sensitivity from 3 configs to a 3x3 state/action bin grid and regenerated `outputs/revision/sci_sensitivity_20260425.{json,csv,md}`.
  - Retitled the manuscript around support-gated learnability and variable-impedance load paths.
  - Removed paper-facing `Sprint` artifact names from `paper/main.tex`.
  - Added explicit non-claims for full 6D wrench dynamics, orientation-induced jamming, sensor drift, and vision-based perception.
  - Added restrained Diffusion Policy, ACT, and IQL scope-setting references.
  - Added synthetic SCI rank-stability reporting across all 3x3 bin configs.
  - Added a P1.1 task to analyze the `fi_motion_vi_k` force/work tradeoff from P0.3.
- Gate readouts:
  - Gate A remains bounded: P0.2/P0.3 support VI/action-capacity language only under matched benchmark controls, not broad VI superiority.
  - Gate C remains bounded: SCI tooling/schema and synthetic rank-stability checks are complete, but real raw-trace association remains pending because the P0 ablation artifacts expose aggregated weak/zero SCI values rather than demo/rollout sample traces.
- Verification:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/three_dof/test_three_dof_support_metric_sensitivity.py::test_sci_rank_stability_prefers_supported_rollout_for_all_bin_configs` -> first run failed with `KeyError: 'sci_rank_stability'`; after implementation, `1 passed in 0.12s`.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/three_dof/test_three_dof_support_metric_sensitivity.py::test_sci_sensitivity_configs_cover_fine_default_coarse tests/paper/test_paper_claim_boundaries.py::test_manuscript_hides_internal_process_artifact_names tests/paper/test_paper_claim_boundaries.py::test_limitations_name_out_of_scope_robotics_axes tests/paper/test_paper_claim_boundaries.py::test_references_cover_modern_scope_setting_baselines` -> first run failed for the expected missing P0 closure constraints; after fixes, `4 passed in 0.15s`.
  - `python scripts/experiments/export_3dof_support_metric_sensitivity.py --input-artifacts outputs/evidence_matrix/three_dof_evidence_matrix.json outputs/revision/teacher_coupling_ablation_20260425.json outputs/revision/motion_matched_impedance_ablation_20260425.json --output-stem outputs/revision/sci_sensitivity_20260425` -> regenerated report with 9 bin rows, 9 synthetic rank-stability rows, and 112 predictive audit rows.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/three_dof/test_three_dof_support_metric_sensitivity.py tests/runners/test_export_3dof_support_metric_sensitivity.py tests/paper/test_docs_claim_source_sync.py tests/paper/test_paper_claim_boundaries.py` -> 21 passed in 0.40s.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/paper/test_docs_claim_source_sync.py tests/paper/test_paper_claim_boundaries.py` -> 16 passed in 0.05s.
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/paper/test_docs_claim_source_sync.py tests/paper/test_paper_claim_boundaries.py tests/sprints/test_three_dof_teacher_coupling_ablation.py tests/sprints/test_three_dof_motion_matched_ablation.py tests/runners/test_run_3dof_teacher_coupling_ablation.py tests/three_dof/test_three_dof_support_metric_sensitivity.py tests/runners/test_export_3dof_support_metric_sensitivity.py tests/paper/test_prose_statistics_sync.py tests/paper/test_paper_figures.py tests/three_dof/test_three_dof_teacher_policies.py tests/three_dof/test_three_dof_teacher_training.py tests/three_dof/test_three_dof_support_metrics.py` -> 54 passed, 12 skipped, 1 warning.
  - `python scripts/export/build_paper_assets.py --check` -> exit 0; temporary asset paths printed under `%TEMP%`.
