# Milestone 3 Engineering Trust Plan

## Context

Milestone 2 Paper-Facing Reproducibility is treated as complete for the next work slice. The user does not plan to maintain a local LaTeX/PDF build environment, so Milestone 3 must not make local PDF compilation or TeX installation a blocking acceptance gate.

Current repository state checked before writing this plan:

- `src/vi_full/__init__.py` is already lightweight: package docstring, `__version__`, and `__all__` only.
- `tests/test_import_boundaries.py` already exists and checks that `import vi_full` does not load `stable_baselines3` or `mujoco`, and does not emit the Gym deprecation warning.
- `.github/` does not exist yet.
- `tests/test_paper_claim_boundaries.py` does not exist yet.

## Scope

Milestone 3 includes:

- Task 10: Lightweight import boundary
- Task 11: No-training CI gate
- Task 13: Claim boundary cleanup

Milestone 3 excludes:

- Task 12 targeted module split, unless a Task 10 call-site fix proves it is necessary.
- Any new training run.
- Mandatory local PDF compilation.
- LaTeX/PDF toolchain installation.

## Execution Order

1. Close Task 10 first because CI should depend on the import boundary contract.
2. Implement Task 13 next because CI should run the claim-boundary test.
3. Add Task 11 last so the workflows can call the final no-training test set.

## Task 10: Lightweight Import Boundary

**Goal:** Make the top-level package import safe for reviewers, CI, and snapshot users.

**Current status:** partially implemented; needs audit, documentation, and final verification.

**Files expected to touch:**

- `src/vi_full/__init__.py` only if the existing boundary regresses during audit.
- `tests/test_import_boundaries.py` only if coverage needs a small assertion.
- `README.md` to document the import contract.

**Checklist:**

- [ ] Run the existing boundary test:
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_import_boundaries.py`
- [ ] Audit `from vi_full import ...` call sites. Only `__version__` should be allowed from top level; runtime APIs should use explicit submodules.
- [ ] Confirm `python -c "import vi_full; print(vi_full.__version__)"` works with `PYTHONPATH=src`.
- [ ] Add a short README note that `import vi_full` is intentionally lightweight and training/simulator APIs are imported from explicit submodules.
- [ ] Close with the import-boundary pytest and direct import command.

**Acceptance:**

- `import vi_full` does not import `mujoco`, `stable_baselines3`, legacy Panda env code, or training modules.
- No Gym deprecation warning is emitted by top-level import.
- README tells reviewers which import is safe and where explicit runtime APIs live.

## Task 13: Claim Boundary Cleanup

**Goal:** Keep manuscript and repo-facing prose aligned with the evidence roles.

**Files expected to touch:**

- `paper/main.tex`
- `tests/test_paper_claim_boundaries.py`
- Optionally `README.md` if broad claims appear there.

**Rules to enforce:**

- SG-VI is benchmark-local methodology, not a universal robotics method.
- SCI is a support-coverage diagnostic, not proof of generalization.
- DAPG-lite is a matched-protocol mechanism control, not a faithful prior reproduction.
- PPO w/o BC did not reach useful contact under tested contracts and budgets; do not imply all PPO failure.
- Near-ceiling success should not be framed as a global method ranking; emphasize evidence role, force/contact work, and Pareto tradeoffs.

**Checklist:**

- [ ] Add `tests/test_paper_claim_boundaries.py` with grep-style checks for unsafe phrases and narrow whitelists.
- [ ] Scan `paper/main.tex` for broad claims around SG-VI, SCI, DAPG-lite, PPO, generalization, and state-of-the-art wording.
- [ ] Patch only the specific overclaiming sentences that fail the test or violate the rules above.
- [ ] Run:
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_paper_claim_boundaries.py`
- [ ] Do not require local PDF compilation. If visual PDF inspection is needed later, use an external/editor build or an already generated anonymous PDF.

**Acceptance:**

- Claim-boundary test passes.
- The manuscript remains paper-facing but conservative: benchmark-local, teacher-coupled, no-hardware, and no universal generalization claim.
- No local TeX/PDF build is required for Task 13 closure.

## Task 11: No-Training CI Gate

**Goal:** Add a CI guard that catches provenance, artifact, import, reviewer-smoke, and claim-boundary drift without running training.

**Files expected to touch:**

- `.github/workflows/reviewer-smoke.yml`
- `.github/workflows/paper-assets-check.yml`
- `README.md`

**Workflow split:**

- `reviewer-smoke.yml`
  - top-level lightweight import check
  - `tests/test_import_boundaries.py`
  - `tests/reviewer`
  - no training runners
  - no TeX/PDF build

- `paper-assets-check.yml`
  - canonical manifest test
  - artifact provenance scan
  - exporter default/source sync tests
  - paper table sync tests
  - evidence selected-row sync tests
  - claim-boundary tests
  - `python scripts/export/build_paper_assets.py --check`
  - no training runners
  - no mandatory TeX/PDF build

**Checklist:**

- [ ] Add `.github/workflows/reviewer-smoke.yml`.
- [ ] Add `.github/workflows/paper-assets-check.yml`.
- [ ] Keep CI commands as local equivalents in README so failures are reproducible outside GitHub.
- [ ] Ensure neither workflow invokes `build_paper_pdf.py`, `pdflatex`, `bibtex`, `latexmk`, or full benchmark training.
- [ ] Validate locally with the same no-training commands that do not require TeX/PDF.

**Acceptance:**

- CI gate exists and is explicitly no-training.
- CI does not require a local or hosted TeX/PDF environment.
- README documents the CI purpose and local command equivalents.

## Local Verification Set

Run these before closing Milestone 3:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_import_boundaries.py tests/test_paper_claim_boundaries.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_canonical_manifest.py tests/test_artifact_provenance.py tests/test_exporter_defaults.py tests/test_paper_table_sync.py tests/test_three_dof_evidence_matrix.py tests/test_sprint2_paper_sync.py tests/reviewer
python scripts/export/build_paper_assets.py --check
PYTHONPATH=src python -c "import vi_full; print(vi_full.__version__)"
```

The verification set intentionally omits `build_paper_pdf.py`.
