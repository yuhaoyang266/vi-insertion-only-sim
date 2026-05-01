# Sprint C Review-Integrated Monthly Plan

> Date created: 2026-05-01
> Scope: one-month Sprint C execution plan after review of the Codex Potter run.
> Applies to: `vi-insertion-only-sim` on the no-hardware path.
> Source task history: `.codexpotter/projects/2026/05/01/1/MAIN.md`
> Baseline commit reviewed: `f8b7c7e`
> Relation to prior plan: this file supersedes `docs/plans/2026-05-01-one-month-sprint-c-detailed-plan.md` for May execution order, but keeps the same Sprint C goal.

## 1. Executive State

The project has completed Sprint A and Sprint B, and the Potter run has already advanced Sprint C substantially:

- Review-repair residue was committed.
- Sprint C kickoff plan was committed.
- Cross-paper interface contract was authored and pinned.
- Paper-B readiness was recorded.
- Bridge translation helpers and tests were added.
- Cross-sim dry-run ranking runner and smoke artifacts were generated.
- Contact-parameter sensitivity smoke was added.
- Modern offline baseline smoke scaffold was added.
- Paper Section 5 skeleton and Tier-2 cover-letter template were added.
- Several review hardening passes were committed, ending at `f8b7c7e`.

The remaining May work is no longer "start Sprint C"; it is "make Sprint C reviewer-proof enough to justify the June full protocol or fallback decision."

## 2. Review Findings To Integrate

### Finding R1: Paper-B commit provenance is trusted but not verified

**Severity:** High
**Current behavior:** `scripts/experiments/run_cross_sim_via_paper_b.py` accepts `--paper-b-commit` and records it into output metadata, but does not verify that the provided value matches the actual checked-out Paper-B commit.
**Risk:** A stale or wrong Paper-B commit can produce an artifact that looks properly pinned.
**Required fix:** Compare `--paper-b-commit` against `_git_commit(paper_b_repo_path)` and fail on mismatch. If no `--paper-b-commit` is provided, record the actual checkout commit.

### Finding R2: Contract reproduction command is not runnable as written

**Severity:** Medium
**Current behavior:** `docs/cross_paper_interface_contract.md` shows a "Paper-A driving Paper-B" command without `--dry-run`, but the runner currently raises unless `--dry-run` is set.
**Risk:** Reviewer follows the documented command and hits an expected failure that looks like a broken reproduction path.
**Required fix:** Add a current dry-run reproduction command and label the full Paper-B physics command as future-only until policy artifact loading and Paper-B physics execution land.

### Finding R3: Paper-B commit roles are ambiguous

**Severity:** Medium
**Current behavior:** the contract records Paper-B verification commit `3eb8408`, while the smoke artifact records Paper-B mirror commit `bb680b6`.
**Risk:** Reviewers cannot tell whether the artifact pins the physics-readiness commit, the contract-mirror commit, or both.
**Required fix:** Separate metadata roles:

- `paper_b_verified_env_commit`
- `paper_b_contract_mirror_commit`
- `paper_b_artifact_commit` or `paper_b_checkout_commit`

Every contract, artifact, progress entry, and test should use these names consistently.

## 3. May Goal

By 2026-05-31, Sprint C should have:

- verified cross-paper provenance semantics;
- runnable dry-run reproduction commands;
- clear separation between contract smoke and future Paper-B physics execution;
- a real or fallback external-validity path selected for June;
- a sensitivity-sweep expansion plan grounded in current smoke results;
- a modern baseline implementation decision beyond schema smoke.

## 4. Priority Ladder

### P0: Reviewer-trust fixes

These must happen before any new experiment expansion:

- Verify `--paper-b-commit` against the actual Paper-B checkout.
- Rename or add metadata fields to distinguish Paper-B verification, mirror, and checkout commits.
- Update contract reproduction commands to include a runnable dry-run path.
- Regenerate cross-sim smoke artifacts after metadata schema changes.
- Add tests that fail for wrong Paper-B commit metadata.

### P1: Sprint C evidence expansion

These make the May output scientifically useful:

- Expand contact sensitivity beyond `contact_xy_scale` smoke.
- Add a mid-scale within-A sensitivity run covering all five parameters.
- Decide whether Paper-B physics execution is ready or should be deferred.
- Define the exact loader contract for Paper-A learned policy artifacts.
- Move modern baseline from schema smoke toward real canonical demo ingestion.

### P2: Writing and packaging

These support submission, but should not precede artifacts:

- Update Section 5 only with landed artifact language.
- Update Tier-2 cover letter with precise "checkpoint" versus "physics-result" framing.
- Keep reviewer guide aligned with runnable commands.

## 5. Detailed Work Plan

### Week 0: 2026-05-01 to 2026-05-03

Goal: fix review findings R1-R3 before adding new scope.

#### W0.1 Fix Paper-B commit verification

- [ ] Add a helper such as `_resolve_and_verify_paper_b_commit(args, paper_b_repo_path)`.
- [ ] If `--paper-b-commit` is provided, compare it with `_git_commit(paper_b_repo_path)`.
- [ ] Accept either full SHA prefix or exact short SHA only if it resolves unambiguously.
- [ ] Raise `RuntimeError` on mismatch with both expected and actual values in the message.
- [ ] If no `--paper-b-commit` is provided, record the actual checkout commit.

**Files:**

- `scripts/experiments/run_cross_sim_via_paper_b.py`
- `tests/runners/test_run_cross_sim_via_paper_b.py`

**Tests:**

- Add test: wrong `--paper-b-commit` fails.
- Add test: omitted `--paper-b-commit` records actual checkout commit when git is available.
- Keep existing dry-run artifact test green.

#### W0.2 Split Paper-B commit metadata roles

- [ ] Update metadata keys emitted by the runner:
  - `paper_b_checkout_commit`
  - `paper_b_verified_env_commit`
  - `paper_b_contract_mirror_commit`
- [ ] Keep `paper_b_commit` only if needed for backward compatibility, but mark it as alias or remove it from new artifacts.
- [ ] Update the cross-paper contract version-pinning block.
- [ ] Update progress log language to clarify each role.
- [ ] Regenerate `outputs/cross_sim/three_dof_cross_sim_ranking_paper_b_smoke_20260501.{json,csv,md}`.

**Files:**

- `docs/cross_paper_interface_contract.md`
- `scripts/experiments/run_cross_sim_via_paper_b.py`
- `outputs/cross_sim/three_dof_cross_sim_ranking_paper_b_smoke_20260501.json`
- `outputs/cross_sim/three_dof_cross_sim_ranking_paper_b_smoke_20260501.csv`
- `outputs/cross_sim/three_dof_cross_sim_ranking_paper_b_smoke_20260501.md`
- `docs/project/progress.md`

#### W0.3 Fix reproduction command wording

- [ ] In the contract, add "Current dry-run smoke command" with `--dry-run`.
- [ ] Move the full Paper-B physics command under "Future full-physics command".
- [ ] In paper Section 5, keep the distinction that the current artifact is a dry-run smoke.
- [ ] In the Tier-2 cover letter, avoid implying landed Paper-B physics ranking.

**Files:**

- `docs/cross_paper_interface_contract.md`
- `paper/main.tex`
- `docs/submission/cover_letter_tier2_template.md`
- `REVIEWER_GUIDE.md` if reviewer commands are added there.

#### W0.4 Verification

Run:

```powershell
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/cross_paper tests/runners/test_run_cross_sim_via_paper_b.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/core/test_import_boundaries.py tests/reviewer
python scripts/export/build_paper_assets.py --check
git diff --check
```

**Exit criteria for Week 0:**

- Review findings R1-R3 are closed.
- Cross-sim smoke artifact metadata is self-explanatory.
- A reviewer can run the documented current command without hitting the future-only physics guard.

### Week 1: 2026-05-04 to 2026-05-10

Goal: make the dry-run bridge ready to become a real bridge.

#### W1.1 Define policy artifact loader contract

- [ ] Identify where the five Paper-A learned suites are stored or reconstructed.
- [ ] Define loader interface:
  - input suite name
  - input artifact path
  - observation shape `(14,)`
  - action shape `(5,)`
  - normalization state
  - unavailable-artifact behavior
- [ ] Add tests for unavailable, invalid, and valid stub loader cases.

**Candidate files:**

- `src/vi_full/cross_paper_bridge.py`
- `tests/cross_paper/test_cross_paper_bridge_contract.py`
- optional new `src/vi_full/cross_paper_policy_loader.py`

#### W1.2 Make dry-run records closer to real records

- [ ] Add explicit record schema for cross-sim episodes.
- [ ] Include fields that full physics will later populate:
  - `out_of_paper_a_scope`
  - `mean_dropped_torque_norm_nm`
  - `paper_a_policy_artifact`
  - `paper_b_env_config`
  - `episode_status`
- [ ] Keep `not_available` rows metric-null.
- [ ] Add tests that partial failures cannot be ranked as completed.

#### W1.3 Paper-B readiness follow-up

- [ ] Re-run Paper-B readiness smoke after metadata-role clarification.
- [ ] Confirm whether `bb680b6` or `3eb8408` is the right current checkout for future physics work.
- [ ] Record exact Paper-B dirty-worktree status without touching unrelated files.

**Exit criteria for Week 1:**

- The bridge has a documented path from stub policy to artifact-backed policy.
- Cross-sim records have schema fields that full physics can reuse.
- Paper-B commit role ambiguity remains closed.

### Week 2: 2026-05-11 to 2026-05-17

Goal: expand sensitivity evidence and make fallback credible.

#### W2.1 Full contact-parameter sensitivity dry run

- [ ] Run all five parameters on at least:
  - profiles: `nominal high_friction tight_clearance`
  - seeds: `0 1 2`
  - episodes per seed: start with `5`, increase if runtime is acceptable
  - policies: `fixed_impedance variable_impedance`
- [ ] Export to:
  - `outputs/revision/contact_parameter_sensitivity_202605xx.json`
  - `outputs/revision/contact_parameter_sensitivity_202605xx.csv`
  - `outputs/revision/contact_parameter_sensitivity_202605xx.md`

#### W2.2 Improve sensitivity analysis

- [ ] Add metric deltas beyond success:
  - peak force delta
  - contact work delta
  - final distance delta
  - jam-rate delta
- [ ] Keep deltas stratified by parameter/profile/policy.
- [ ] Add a summary table that reports most sensitive parameter per metric.

#### W2.3 Fallback decision preparation

- [ ] If Paper-B physics execution is still blocked, create a fallback scope note:
  - no Paper-B physics ranking in May;
  - within-A sensitivity becomes the external-validity proxy for June;
  - Paper-B remains a pinned interface artifact, not evidence.

**Exit criteria for Week 2:**

- Sensitivity artifact covers all five parameters at more than smoke scale.
- The next action is either Paper-B real policy loading or within-A fallback expansion.

### Week 3: 2026-05-18 to 2026-05-24

Goal: make the 2026-05-18 Paper-B decision and execute the chosen path.

#### W3.1 Decision gate

Record one of:

- **Paper-B active:** policy loader and Paper-B physics path are ready for mid-scale run.
- **Paper-B deferred:** bridge remains contract-level; within-A fallback becomes June path.

#### W3.2 If Paper-B active

- [ ] Implement the first real policy artifact loader.
- [ ] Run one suite, one profile, one seed, five episodes through Paper-B physics.
- [ ] Compare dry-run metadata and real-run metadata.
- [ ] Add explicit "completed" episode record tests.

#### W3.3 If Paper-B deferred

- [ ] Draft `src/vi_full/three_dof_alt_contact_model.py` design note or scaffold.
- [ ] Define what differs from the base contact law.
- [ ] Add tests proving shared observation/action/metric contracts still hold.
- [ ] Keep this as a fallback contact-law cross-check, not a second simulator claim.

#### W3.4 Modern baseline next step

- [ ] Locate canonical demo dataset source or runner to generate it.
- [ ] Add real dataset ingestion path beside synthetic schema smoke.
- [ ] If no canonical dataset exists, add a task to materialize one from existing teacher rollouts.

**Exit criteria for Week 3:**

- May has a concrete external-validity direction.
- Modern baseline is no longer only a synthetic schema claim, or the blocker is documented.

### Week 4: 2026-05-25 to 2026-05-31

Goal: close May with a defensible checkpoint.

#### W4.1 Run chosen mid-scale evidence

If Paper-B active:

- [ ] Run cross-sim mid-scale:
  - suites: at least two learned suites
  - profiles: all five if runtime permits
  - seeds: at least `0 1 2`
  - episodes per seed: at least `20`, target `100`

If Paper-B deferred:

- [ ] Run within-A fallback mid-scale:
  - all five parameters
  - all five profiles
  - seeds `0 1 2`
  - both handcrafted policies
  - optional learned-row proxy if policy artifacts are available

#### W4.2 Update writing only after artifacts land

- [ ] Update Section 5 wording to reflect May decision.
- [ ] Keep current artifact labels precise:
  - dry-run smoke
  - sensitivity smoke or mid-scale sensitivity
  - scaffold-only baseline or dataset-ingestion baseline
- [ ] Update cover-letter template with the same scope.

#### W4.3 Final verification

Run:

```powershell
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/cross_paper tests/runners/test_run_cross_sim_via_paper_b.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/three_dof/test_three_dof_contact_parameter_sensitivity.py tests/runners/test_run_3dof_contact_parameter_sensitivity.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/three_dof/test_modern_baseline_smoke.py tests/runners/test_run_modern_baseline_iql_smoke.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/core/test_import_boundaries.py tests/reviewer
python scripts/export/build_paper_assets.py --check
git diff --check
```

If runtime is acceptable, also run:

```powershell
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

#### W4.4 May checkpoint entry

Add a `docs/project/progress.md` entry with:

- Paper-B path status.
- Cross-sim artifact path.
- Sensitivity artifact path.
- Modern baseline status.
- June recommendation.
- Verification commands and exit codes.

**Exit criteria for Week 4:**

- The repo has a self-contained May checkpoint.
- June work can start from either a Paper-B physics path or a documented fallback path.

## 6. Acceptance Criteria

### Must Pass

- Wrong `--paper-b-commit` fails before artifact writing.
- Current dry-run reproduction command in the contract runs.
- Cross-sim artifact metadata distinguishes Paper-B commit roles.
- No local absolute paths appear in reviewer-facing artifacts.
- Section 5 does not claim Paper-B physics ranking until real physics artifacts exist.
- Modern baseline artifact stays labeled `scaffold_only` until real training/evaluation exists.

### Should Pass

- Contact-parameter sensitivity covers all five planned parameters.
- Sensitivity summary reports per-metric most-sensitive parameters, not only success-rate delta.
- Paper-B readiness state is verified after commit-role cleanup.
- The Tier-2 cover letter uses "checkpoint" language for smoke artifacts.

### Nice To Have

- First real Paper-B physics episode record.
- Canonical demo dataset ingestion for IQL/CQL smoke.
- Alternative contact-model scaffold if Paper-B is deferred.

## 7. Review Checklist

Use this checklist before calling Sprint C May work complete:

- [ ] Does every cross-paper artifact record contract SHA?
- [ ] Does every cross-paper artifact record actual Paper-A commit?
- [ ] Does every cross-paper artifact distinguish Paper-B verification/mirror/checkout commits?
- [ ] Can the documented current command run without hitting a future-only code path?
- [ ] Are dry-run rows clearly `not_available` and metric-null?
- [ ] Are completed rows only possible after real episode metrics exist?
- [ ] Are sensitivity deltas computed within matching parameter/profile/policy strata?
- [ ] Are paper claims limited to landed artifacts?
- [ ] Are generated artifacts free of local absolute paths?
- [ ] Are tests and asset checks recorded in `docs/project/progress.md`?

## 8. Suggested Commit Plan

Keep commits reviewable:

1. `fix: verify paper b commit provenance`
2. `docs: clarify cross-sim dry-run reproduction`
3. `test: split paper b commit metadata roles`
4. `feat: expand contact sensitivity summaries`
5. `feat: add policy loader contract for cross sim`
6. `docs: record sprint c may checkpoint`

## 9. June Decision Outputs

At the end of May, choose exactly one June path:

### Path A: Paper-B Active

Use when:

- commit provenance is verified;
- Paper-B physics command works;
- at least one real Paper-B episode record completes;
- policy artifact loading has a clear implementation path.

June focus:

- full 5-suite x 5-profile x 5-seed cross-sim ranking;
- Paper-B physics section update;
- modern baseline real dataset ingestion.

### Path B: Paper-B Deferred

Use when:

- Paper-B physics path is still blocked;
- policy artifact loading is unavailable;
- only dry-run smoke exists.

June focus:

- within-A alternative contact model;
- full contact-parameter sensitivity;
- offline baseline real dataset ingestion;
- paper language keeps Paper-B as interface-only.

## 10. Final May Status Template

```markdown
### Sprint C May Checkpoint (2026-05-31)
- Status: Paper-B active / Paper-B deferred.
- Review findings:
  - R1 Paper-B commit verification: closed / open.
  - R2 runnable dry-run command: closed / open.
  - R3 Paper-B commit-role metadata: closed / open.
- Cross-paper contract: `docs/cross_paper_interface_contract.md`, SHA `<sha>`.
- Paper-B verified env commit: `<sha or deferred>`.
- Paper-B contract mirror commit: `<sha or deferred>`.
- Paper-B checkout commit used in artifacts: `<sha or not_applicable>`.
- Cross-sim artifact: `<path>`.
- Sensitivity artifact: `<path>`.
- Modern baseline artifact: `<path>`.
- June path: Paper-B active / Paper-B deferred fallback.
- Verification:
  - `<command>` -> exit `<code>`.
```
