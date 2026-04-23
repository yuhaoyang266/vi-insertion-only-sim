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

## Open Blockers

### 1. PDF build toolchain is missing on this machine

Checked on 2026-04-23:

- `latexmk`: missing
- `pdflatex`: missing
- `xelatex`: missing

Implication:

- The final paper PDF cannot be regenerated locally from `paper/main.tex` in the current
  environment.

### 2. Anonymous submission snapshot is not assembled

Current explicit identity surfaces include:

- `paper/main.tex`
  - author name
  - affiliation
  - email
  - public repository URL in the date line
- `README.md`
  - public repository URL and author-facing package language
- `docs/github_upload.md`
  - direct GitHub target URL and public upload steps

Implication:

- The working tree is not an anonymized package snapshot.
- A venue-specific anonymous package still needs a deliberate filtered export rather than a raw
  zip of the repository root.

## Recommended Packaging Sequence

1. Install a TeX toolchain that provides `latexmk` and `pdflatex`.
2. Build the manuscript from `paper/` and verify the generated PDF opens cleanly.
3. Decide whether the target venue requires anonymous supplementary materials.
4. If anonymity is required, create a filtered package copy that excludes or rewrites:
   - author identity in `paper/main.tex`
   - public repository URL references
   - `docs/github_upload.md`
5. Bundle:
   - paper PDF
   - supplementary figures
   - the filtered repo snapshot
   - the cover letter draft in `docs/cover_letter_draft.md`

## Minimal Completion Criteria

- Paper PDF built successfully in the target environment.
- Supplementary figure assets included.
- Snapshot contents match the target venue's anonymity policy.
- Cover letter draft reviewed once against the target venue.
