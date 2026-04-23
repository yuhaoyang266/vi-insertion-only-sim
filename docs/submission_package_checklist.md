# Submission Package Checklist

## Scope

This note tracks what still needs to happen before the repository can be treated as a
submission-facing package.

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

## Open Blockers

### 1. PDF build toolchain is missing on this machine

Checked on 2026-04-23:

- `latexmk`: missing
- `pdflatex`: missing
- `xelatex`: missing

Implication:

- The final paper PDF cannot be regenerated locally from `paper/main.tex` in the current
  environment.

## Recommended Packaging Sequence

1. Install a TeX toolchain that provides `latexmk` and `pdflatex`.
2. Build the anonymous manuscript PDF from `paper/` and verify the generated PDF opens cleanly.
3. Stage the bundle with:
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

- Paper PDF built successfully in the target environment.
- Supplementary figure assets included.
- Snapshot contents match the target venue's anonymity policy.
- Cover letter draft reviewed once against the target venue.
