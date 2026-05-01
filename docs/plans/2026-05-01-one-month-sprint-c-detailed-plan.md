# 2026-05 One-Month Sprint C Detailed Plan

> Date created: 2026-05-01
> Scope: May 2026 execution plan for Sprint C, External Validity via Paper-B Bridge.
> Primary repo: `vi-insertion-only-sim`
> Planned companion repo: `research-cartesian-impedance-vla-sim`
> Source roadmap: `docs/plans/2026-04-28-12-month-tier2-roadmap-plan.md` and `docs/plans/2026-04-28-12-month-tier2-roadmap-task-list.md`

## 1. Current Project State

### 1.1 Completed Work

- Sprint A is complete: Tier-3 submission readiness, reviewer surface, anonymous bundle, paper asset checks, and CI gates are recorded.
- Sprint B is complete: matched-protocol main-table evidence, motion-matched decoupling, success-matched mechanics, stage4 canonical benchmark, and Section 3 rewrite are recorded.
- Review repair is complete in the working tree: paper-table CSV fallback, CSV stale-output checks, and provenance hardening have been implemented and verified.
- Current paper position is still simulation-only 3DoF. Hardware phases are cancelled under the no-hardware decision.
- SCI remains a benchmark-local diagnostic and is not a general sim-to-real metric.

### 1.2 Current Working Tree Notes

As of 2026-05-01, the branch reports `main...origin/main` with uncommitted review-repair files:

- `docs/project/progress.md`
- `scripts/export/export_paper_only_sim_benchmark_table.py`
- `src/vi_full/paper_tables.py`
- `tests/artifacts/test_artifact_provenance.py`
- `tests/paper/test_exporter_defaults.py`
- `tests/paper/test_paper_figures.py`
- `tests/paper/test_paper_tables.py`
- `tests/paper/test_prose_statistics_sync.py`
- `docs/plans/2026-04-29-review-repair-plan.md`
- `docs/plans/2026-04-29-review-repair-task-list.md`

Before starting Sprint C implementation, close or commit these changes so Sprint C diffs stay reviewable.

### 1.3 May Goal

By 2026-05-31, Sprint C should have a working external-validity path:

- A cross-paper interface contract exists and is version-pinned.
- Paper-B readiness is verified or the fallback path is formally triggered.
- A minimal Paper-A to Paper-B bridge passes contract-level tests.
- Contact-parameter sensitivity runs inside Paper-A.
- One modern baseline path is selected and smoke-tested.
- A mid-Sprint C evidence review decides whether June should run the full Paper-B protocol or the within-A fallback cross-check.

## 2. Sprint C Operating Rules

- Do not change manuscript numbers before artifacts land.
- Do not promote SCI beyond the current benchmark-local diagnostic boundary.
- Do not block indefinitely on Paper-B. If Paper-B parity is not reliable by 2026-05-18, trigger the fallback path.
- Add failing tests before new modules when practical.
- Record every meaningful command, exit code, and artifact path in `docs/project/progress.md`.
- Keep Paper-A and Paper-B contract copies identical when both repos are available.
- Prefer small smoke runs before full 5-profile x 5-seed protocols.

## 3. Deliverables By End Of May

### P0 Deliverables

- `docs/cross_paper_interface_contract.md`
- Paper-B mirrored `docs/cross_paper_interface_contract.md`, if Paper-B repo is available
- `tests/cross_paper/test_cross_paper_contract_sha_pin.py`
- `tests/cross_paper/test_cross_paper_bridge_contract.py`
- `src/vi_full/cross_paper_bridge.py`
- `scripts/experiments/run_cross_sim_via_paper_b.py`
- A smoke artifact under `outputs/cross_sim/`
- Paper-B readiness or fallback decision recorded in `docs/project/progress.md`

### P1 Deliverables

- `src/vi_full/cross_sim_ranking.py`
- `src/vi_full/three_dof_contact_parameter_sensitivity.py`
- `scripts/experiments/run_3dof_contact_parameter_sensitivity.py`
- Contact sensitivity artifact under `outputs/revision/`
- Modern baseline decision record and smoke scaffold

### P2 Deliverables

- Section 5 skeleton in `paper/main.tex`, without unlanded numbers
- `docs/submission/cover_letter_tier2_template.md`
- A May checkpoint review note in `docs/project/progress.md`

## 4. Calendar Plan

### Week 0: 2026-05-01 to 2026-05-03

Goal: close review-repair residue and prepare a clean Sprint C baseline.

#### Tasks

- [ ] R0.1 Review current dirty files and confirm they all belong to review repair.
- [ ] R0.2 Run focused repair checks:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/paper/test_paper_tables.py`
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/paper/test_exporter_defaults.py tests/paper/test_paper_table_sync.py`
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/artifacts/test_artifact_provenance.py tests/paper/test_prose_statistics_sync.py tests/paper/test_paper_figures.py`
- [ ] R0.3 Run full confidence checks:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`
  - `python scripts/export/build_paper_assets.py --check`
- [ ] R0.4 Commit review-repair changes as two commits if the user wants commits:
  - `fix: repair paper table csv export checks`
  - `test: harden stage4 artifact provenance checks`
- [ ] R0.5 Add Sprint C kickoff note to `docs/project/progress.md`.

#### Exit Criteria

- Working tree is clean or intentionally dirty only with this May plan file.
- Current local checks are green or failures are logged with a non-repeated next action.

### Week 1: 2026-05-04 to 2026-05-10

Goal: write the cross-paper contract and pin the interface before code depends on it.

#### Tasks

- [ ] C0.1 Author `docs/cross_paper_interface_contract.md`.
- [ ] C0.2 Define Schema-P action mapping:
  - Paper-A action shape
  - Paper-B action shape
  - stiffness mapping
  - yaw policy for Paper-A to Paper-B transfer
  - invalid-action handling
- [ ] C0.3 Define Paper-B to Paper-A observation projection:
  - relative position
  - velocity or finite-difference approximation
  - force or wrench projection
  - contact state
  - profile metadata
  - normalization assumptions
- [ ] C0.4 Define shared metrics:
  - success
  - force jam
  - blocked contact
  - horizon
  - contact entry
  - final distance
  - peak force
  - contact work
- [ ] C0.5 Define 5-profile evaluation suite:
  - nominal
  - tight clearance
  - high friction
  - offset bias
  - noisy force
- [ ] C0.6 Define demo dataset schema:
  - observation array shape
  - action array shape
  - episode boundaries
  - profile labels
  - provenance metadata
- [ ] C0.7 Add contract SHA pin protocol.
- [ ] C0.8 Mirror contract to Paper-B repo if available.
- [ ] C0.9 Add `tests/cross_paper/test_cross_paper_contract_sha_pin.py`.

#### Exit Criteria

- Contract is readable without implementation context.
- Paper-A has a test that fails if the bridge SHA pin drifts from the contract.
- Paper-B owner or local Paper-B checkout accepts the dyaw/stiffness mapping decision, or a blocking decision is logged.

### Week 2: 2026-05-11 to 2026-05-17

Goal: verify Paper-B readiness and build the smallest bridge that can be tested.

#### Tasks

- [ ] C1.1 Locate Paper-B repo and record its path in `docs/project/progress.md`.
- [ ] C1.2 Verify Paper-B branch and commit:
  - `git status --short --branch`
  - `git rev-parse --short HEAD`
- [ ] C1.3 Read Paper-B `peg_in_hole.py` and its relevant tests.
- [ ] C1.4 Run Paper-B physical-correctness or W2 audit checks.
- [ ] C1.5 Run a Paper-B scripted-policy parity smoke against the contract.
- [ ] C1.6 Record Paper-B verifying commit hash in `docs/cross_paper_interface_contract.md`.
- [ ] C2.1 Add failing bridge contract test:
  - `tests/cross_paper/test_cross_paper_bridge_contract.py`
- [ ] C2.2 Implement `src/vi_full/cross_paper_bridge.py` with pure translation helpers first.
- [ ] C2.3 Implement contract-SHA refusal.
- [ ] C2.4 Add minimal policy wrapper stubs for five learned suites:
  - `ppo_no_bc`
  - `bc_only_stable_r32_p32`
  - `fixed_impedance_rl_stable_r32_p32`
  - `repaired_mainline_bc_to_ppo`
  - `dapg_lite_repaired_mainline`

#### Exit Criteria

- Paper-B readiness is green or the exact blocker is logged.
- Bridge unit tests pass without running the full simulator.
- 2026-05-18 fallback decision is prepared if Paper-B readiness is not green.

### Week 3: 2026-05-18 to 2026-05-24

Goal: choose Paper-B bridge or fallback, then generate first smoke artifacts.

#### Tasks

- [ ] C1.7 Make the 2026-05-18 decision:
  - continue Paper-B if parity smoke is reliable
  - trigger fallback if parity smoke is blocked
- [ ] C2.5 Create `scripts/experiments/run_cross_sim_via_paper_b.py`.
- [ ] C2.6 Run bridge smoke:
  - 1 profile
  - 1 seed
  - 5 to 10 episodes
  - 1 to 2 learned suites
- [ ] C2.7 Create `src/vi_full/cross_sim_ranking.py`.
- [ ] C2.8 Export smoke ranking artifact under `outputs/cross_sim/`.
- [ ] C3.1 Add failing sensitivity-grid test.
- [ ] C3.2 Implement `src/vi_full/three_dof_contact_parameter_sensitivity.py`.
- [ ] C3.3 Implement `scripts/experiments/run_3dof_contact_parameter_sensitivity.py`.
- [ ] C3.4 Run sensitivity dry run on one profile and one seed.
- [ ] C4.1 Choose modern baseline:
  - preferred: IQL/CQL offline
  - fallback: Diffusion Policy via LeRobot
  - fallback: ACT
- [ ] C4.2 Add baseline decision record to `docs/project/progress.md`.

#### Fallback Tasks If Paper-B Is Blocked

- [ ] F1 Add `src/vi_full/three_dof_alt_contact_model.py`.
- [ ] F2 Add tests proving the alternative model differs only in contact-law assumptions.
- [ ] F3 Run a within-A second-contact-model smoke check.
- [ ] F4 Update the Sprint C plan status to say Paper-B bridge is deferred.

#### Exit Criteria

- Either Paper-B bridge smoke artifact exists, or fallback smoke artifact exists.
- Contact sensitivity dry run exists.
- Modern baseline choice is locked.

### Week 4: 2026-05-25 to 2026-05-31

Goal: run a useful mid-scale protocol and decide June direction.

#### Tasks

- [ ] C2.9 Run mid-scale cross-sim protocol if Paper-B path is active:
  - 5 learned suites
  - 5 profiles
  - 3 seeds
  - 100 episodes per seed/profile
- [ ] C2.10 Export mid-scale ranking artifact:
  - `outputs/cross_sim/three_dof_cross_sim_ranking_paper_b_202605xx.json`
  - `outputs/cross_sim/three_dof_cross_sim_ranking_paper_b_202605xx.csv`
  - `outputs/cross_sim/three_dof_cross_sim_ranking_paper_b_202605xx.md`
- [ ] C3.5 Run full contact-parameter sensitivity:
  - 5 parameters
  - 3 levels each
  - canonical learned suites
  - 5 profiles where feasible
- [ ] C3.6 Identify parameter most likely to overturn the support-gate finding.
- [ ] C4.3 Implement modern baseline smoke scaffold.
- [ ] C4.4 Run baseline smoke and write artifact under `outputs/revision/` or `artifacts/main_benchmark/` depending on maturity.
- [ ] C5.1 Add Section 5 skeleton to `paper/main.tex` only after at least smoke artifacts exist.
- [ ] C5.2 Draft `docs/submission/cover_letter_tier2_template.md`.
- [ ] C5.3 Run Sprint C checkpoint checks:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/core/test_import_boundaries.py tests/reviewer`
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/cross_paper tests/three_dof/test_three_dof_contact_parameter_sensitivity.py`
  - `python scripts/export/build_paper_assets.py --check`
- [ ] C5.4 Write May checkpoint review in `docs/project/progress.md`.

#### Exit Criteria

- Sprint C has enough evidence to choose June execution mode.
- If Paper-B path is healthy, June should run full 5-seed cross-sim and integrate the modern baseline.
- If Paper-B path is blocked, June should finish the within-A alternative contact model and keep Paper-B as a deferred follow-up.

## 5. Task Breakdown By Workstream

### Workstream A: Repo Hygiene And Baseline

| ID | Priority | Task | Output | Validation |
| --- | --- | --- | --- | --- |
| A1 | P0 | Close review-repair worktree | clean or intentionally dirty git status | `git status --short` |
| A2 | P0 | Run full baseline tests | progress log entry | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q` |
| A3 | P0 | Run asset sync check | progress log entry | `python scripts/export/build_paper_assets.py --check` |

### Workstream B: Cross-Paper Contract

| ID | Priority | Task | Output | Validation |
| --- | --- | --- | --- | --- |
| B1 | P0 | Write Paper-A contract | `docs/cross_paper_interface_contract.md` | contract review |
| B2 | P0 | Mirror contract to Paper-B | Paper-B same path | SHA equality |
| B3 | P0 | Add SHA pin test | `tests/cross_paper/test_cross_paper_contract_sha_pin.py` | pytest |
| B4 | P0 | Record Paper-B commit | contract metadata | `git rev-parse --short HEAD` |

### Workstream C: Paper-B Readiness

| ID | Priority | Task | Output | Validation |
| --- | --- | --- | --- | --- |
| C1 | P0 | Verify Paper-B status | progress log | `git status --short --branch` |
| C2 | P0 | Run Paper-B parity smoke | smoke log | Paper-B command exit 0 |
| C3 | P0 | Make 2026-05-18 decision | progress decision | continue or fallback |

### Workstream D: Bridge And Ranking

| ID | Priority | Task | Output | Validation |
| --- | --- | --- | --- | --- |
| D1 | P0 | Implement translation helpers | `src/vi_full/cross_paper_bridge.py` | unit tests |
| D2 | P0 | Implement bridge runner | `scripts/experiments/run_cross_sim_via_paper_b.py` | `--help` and smoke |
| D3 | P1 | Implement ranking aggregator | `src/vi_full/cross_sim_ranking.py` | synthetic test |
| D4 | P1 | Export smoke ranking | `outputs/cross_sim/*.json` | artifact schema check |

### Workstream E: Sensitivity Sweep

| ID | Priority | Task | Output | Validation |
| --- | --- | --- | --- | --- |
| E1 | P1 | Add sensitivity grid tests | test file | pytest red then green |
| E2 | P1 | Implement sweep module | `src/vi_full/three_dof_contact_parameter_sensitivity.py` | pytest |
| E3 | P1 | Implement runner | `scripts/experiments/run_3dof_contact_parameter_sensitivity.py` | `--help` and smoke |
| E4 | P1 | Run full sweep | `outputs/revision/contact_parameter_sensitivity_202605xx.*` | artifact schema check |

### Workstream F: Modern Baseline

| ID | Priority | Task | Output | Validation |
| --- | --- | --- | --- | --- |
| F1 | P1 | Choose IQL/CQL or fallback | progress decision | user/project sign-off |
| F2 | P1 | Add baseline scaffold test | test file | pytest red then green |
| F3 | P1 | Implement smoke runner | `scripts/experiments/run_modern_baseline_<chosen>.py` | `--help` and smoke |
| F4 | P2 | Run baseline smoke | output artifact | schema check |

### Workstream G: Writing And Submission Prep

| ID | Priority | Task | Output | Validation |
| --- | --- | --- | --- | --- |
| G1 | P2 | Add Section 5 skeleton | `paper/main.tex` | prose tests |
| G2 | P2 | Draft Tier-2 cover letter | `docs/submission/cover_letter_tier2_template.md` | manual review |
| G3 | P2 | Write May checkpoint | `docs/project/progress.md` | self-contained status |

## 6. Risk Register For May

| Risk | Likelihood | Impact | Response |
| --- | --- | --- | --- |
| Paper-B environment is not parity-ready by 2026-05-18 | Medium | High | Trigger within-A alternative contact model fallback. |
| Contract mapping is ambiguous for yaw or stiffness | Medium | High | Record explicit decision and keep bridge refusal strict. |
| Cross-sim smoke reveals ranking instability | Medium | Medium | Report instability directly; do not force stability claim. |
| Modern baseline costs too much time | Medium | Medium | Choose IQL/CQL offline first and keep May scope to smoke. |
| Full tests become slow after new modules | Medium | Medium | Keep smoke tests small and mark expensive protocols outside unit tests. |
| Existing uncommitted repair changes blur Sprint C review | High | Medium | Close review-repair worktree before new implementation. |

## 7. Verification Commands

Use these commands as the recurring May baseline:

```powershell
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/core/test_import_boundaries.py tests/reviewer
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/artifacts/test_canonical_manifest.py tests/artifacts/test_artifact_provenance.py tests/paper/test_exporter_defaults.py tests/paper/test_paper_table_sync.py tests/paper/test_three_dof_evidence_matrix.py tests/paper/test_sprint2_paper_sync.py tests/paper/test_paper_claim_boundaries.py
python scripts/export/build_paper_assets.py --check
```

Use these commands after the first Sprint C code lands:

```powershell
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/cross_paper
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/three_dof/test_three_dof_contact_parameter_sensitivity.py
python scripts/experiments/run_cross_sim_via_paper_b.py --help
python scripts/experiments/run_3dof_contact_parameter_sensitivity.py --help
```

## 8. May Gate Decisions

### Gate C0: Contract Gate

Target date: 2026-05-10

Pass condition:

- Contract exists in Paper-A.
- Contract is mirrored or Paper-B unavailability is logged.
- SHA pin test exists.
- Action, observation, metric, and profile definitions are explicit.

### Gate C1a: Paper-B Readiness Gate

Target date: 2026-05-18

Pass condition:

- Paper-B commit is pinned.
- Paper-B parity smoke passes.
- Bridge unit tests pass.

Fail action:

- Trigger within-A alternative contact model fallback.
- Keep Paper-B bridge deferred rather than blocking Sprint C.

### Gate C1b: May Midpoint Evidence Gate

Target date: 2026-05-31

Pass condition:

- Cross-sim or fallback smoke artifact exists.
- Contact sensitivity dry or full artifact exists.
- Modern baseline path is chosen and smoke-scaffolded.
- June execution path is explicit.

## 9. Expected End-Of-Month Status Message

Use this shape for the 2026-05-31 progress entry:

```markdown
### Sprint C May Checkpoint (2026-05-31)
- Status: Paper-B bridge active / Paper-B deferred with fallback active.
- Contract: `docs/cross_paper_interface_contract.md`, SHA pinned to `<sha>`.
- Paper-B commit: `<commit>` or deferred reason.
- Bridge artifact: `<path>` or fallback artifact `<path>`.
- Sensitivity artifact: `<path>`.
- Modern baseline: `<chosen>`, smoke status `<status>`.
- June decision: full Paper-B protocol / within-A fallback cross-check.
- Verification:
  - `<command>` -> exit `<code>`.
```
