# Submission Package Checklist

## Scope

This note records the concrete contents and local verification state of the
anonymous submission package assembled from this repository.

## Package Contents

- Manuscript source:
  - `paper/main.tex`
  - `paper/references.bib`
- Main figures:
  - `figures/main/`
- Appendix figures:
  - `figures/appendix/`
- Supplementary figures:
  - `supplement/figures/`
- Frozen benchmark artifacts:
  - `artifacts/main_benchmark/`
  - `artifacts/diagnostics/`
  - `artifacts/mechanics/`
  - `artifacts/stress_tests/`
- Reviewer-facing Sprint artifacts:
  - `outputs/evidence_matrix/`
  - `outputs/cross_family_confirm/`
  - `outputs/sprint3_teacher_mini_ablation/`
  - `outputs/sprint4_clearance_shift/`
- Reproduction entrypoints:
  - `scripts/export/`
  - `scripts/experiments/`

## Current Verification Status

- `README.md` documents the repo-root commands for the manuscript-facing and reviewer-facing exports.
- Repo-root CLI smoke coverage passes for the public experiment/export entrypoints.
- Teacher metadata serialization coverage passes in `tests/test_three_dof_teacher_training.py`.
- Sprint 3 and Sprint 4 reviewer-facing bundles are present under `outputs/`.
- `scripts/export/build_submission_bundle.py` can now stage an anonymous snapshot plus editor-only
  materials under `tmp/submission_bundle/` while recording the package contents in
  `submission_bundle_manifest.json`.
- 2026-04-23: the local anonymous manuscript PDF was built successfully at
  `tmp/submission_bundle/journal_double_blind/anonymous_manuscript.pdf`.
- 2026-04-23: the final staged package exists under `tmp/submission_bundle/journal_double_blind/`
  with `anonymous_snapshot/`, `editor_materials/`, `submission_bundle_manifest.json`,
  `submission_bundle_summary.md`, `anonymous_snapshot.zip`, `editor_materials.zip`, and
  `anonymous_manuscript.pdf`.
- `submission_bundle_manifest.json` now records `paper_pdf.status = included` and
  `identity_token_scan_passed = true`.
- PDF metadata and extracted text were checked after the anonymous build; no author name, email,
  or public repository URL survived into the generated PDF.

## Local Build Notes

- 2026-04-23: `MiKTeX.MiKTeX` was installed via `winget`.
- The local MiKTeX install exposes `pdflatex`, `bibtex`, `xelatex`, and `initexmf` under the
  user profile.
- `latexmk` still cannot run in this environment because MiKTeX does not see a local `perl`
  script engine. This is not a packaging blocker because the direct `pdflatex` / `bibtex` chain
  succeeds.
- Successful local PDF sequence:
  1. `python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind`
  2. in `tmp/submission_bundle/journal_double_blind/anonymous_snapshot/paper/`, run
     `pdflatex -interaction=nonstopmode -halt-on-error main.tex`, `bibtex main`, then `pdflatex`
     until cross-references stabilize
  3. copy the resulting anonymous PDF outside the staged directory and rerun
     `python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind --paper-pdf tmp/submission_bundle/anonymous_manuscript.pdf`
     because the builder recreates `--output-dir` on each invocation and now rejects in-place PDF
     paths before deleting the staging tree

## Remaining Notes

- No repository-local blocker remains for the Phase 5 submission package.
- `docs/cover_letter_draft.md` is already staged into `editor_materials/`; any venue-specific
  wording update is editorial follow-up rather than a repository build blocker.

## Recommended Packaging Sequence

1. Refresh the anonymous snapshot with:
   - `python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind`
2. Build the anonymous manuscript PDF from `tmp/submission_bundle/journal_double_blind/anonymous_snapshot/paper/`.
3. Stage the final bundle with:
   - `python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind --paper-pdf <anonymous_manuscript.pdf>`
4. Review `tmp/submission_bundle/journal_double_blind/submission_bundle_manifest.json` against the
   target venue's anonymity policy.
5. Bundle:
   - paper PDF
   - supplementary figures inside `anonymous_snapshot/`
   - the anonymous repo snapshot or `anonymous_snapshot.zip`
   - editor-only material from `editor_materials/`, including `cover_letter_draft.md`

## Anonymous Snapshot Contract

The anonymous bundle builder currently applies the following filtering rules:

- `paper/main.tex`
  - rewrites the author block to `Anonymous Authors`
  - removes the repository URL from the title metadata
- `README.md`
  - removes the public repository URL section
  - relabels the snapshot as reviewer-facing anonymous material
- `docs/github_upload.md`
  - excluded from the anonymous snapshot
- `docs/cover_letter_draft.md`
  - copied only into `editor_materials/`
- `tests/` and internal planning notes
  - excluded from the anonymous snapshot to keep the reviewer-facing package narrow and avoid
    reintroducing author-facing staging text

## Minimal Completion Criteria

- [x] Paper PDF built successfully in the current environment.
- [x] Supplementary figure assets are included in the anonymous snapshot.
- [x] Snapshot contents match the current anonymity policy and manifest.
- [x] Cover letter draft is staged under `editor_materials/`; venue-specific wording can be tuned later if needed.
