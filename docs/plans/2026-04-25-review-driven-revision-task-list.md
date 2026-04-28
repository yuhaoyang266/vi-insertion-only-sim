# Review-Driven Revision Task List

This task list decomposes `docs/plans/2026-04-25-review-driven-revision-detailed-plan.md` into execution-sized items.

## Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` complete
- `[!]` blocked / needs user decision

---

## P0: Do Not Resubmit Without These

### P0.1 Review Response Matrix

- [x] Create `docs/reviews/review_response_matrix_2026-04-25.md`.
- [x] Add columns: Reviewer concern, Claim affected, Severity, Required evidence, Planned experiment/text revision, Success criterion, Manuscript location, Response draft, Status.
- [x] Add fatal row for teacher support / VI prior confounding.
- [x] Add fatal row for motion prior / impedance prior confounding.
- [x] Add major row for SCI post-hoc/bin sensitivity.
- [x] Add major row for tuned FI weakening VI success-superiority claim.
- [x] Add major/fatal row for 3DoF toy benchmark external validity.
- [x] Add major row for Sprint/internal jargon.
- [x] Update `docs/project/task_plan.md` with Phase 6 P0/P1/P2 task list.
- [x] Update `docs/project/progress.md` with Phase 6 planning log.
- [x] Run `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/paper/test_docs_claim_source_sync.py tests/paper/test_paper_claim_boundaries.py`.
- [x] Record command result in `docs/project/progress.md`.

### P0.2 Teacher-Coupling Crossed Ablation

- [x] Create failing test `tests/sprints/test_three_dof_teacher_coupling_ablation.py::test_teacher_coupling_grid_contains_minimal_cross`.
- [x] Run the failing test and confirm import failure.
- [x] Create `src/vi_full/three_dof_teacher_coupling_ablation.py`.
- [x] Add `TeacherCouplingCondition` dataclass.
- [x] Add `build_teacher_coupling_grid(seeds, total_timesteps)`.
- [x] Include exactly four minimal crossed conditions: `vi_teacher_vi_student`, `vi_teacher_fi_student`, `fi_teacher_fi_student`, `fi_teacher_vi_student`.
- [x] Run grid test and confirm pass.
- [x] Add teacher preset resolution test using `resolve_3dof_teacher_spec`.
- [x] Add synthetic aggregation schema test.
- [x] Implement `summarize_teacher_coupling_results`.
- [x] Create CLI smoke test `tests/runners/test_run_3dof_teacher_coupling_ablation.py::test_teacher_coupling_runner_help`.
- [x] Create `scripts/experiments/run_3dof_teacher_coupling_ablation.py`.
- [x] Add CLI args: `--seeds`, `--total-timesteps`, `--episodes`, `--output`, `--smoke-only`.
- [x] Add smoke-only output mode for fast tests.
- [x] Run focused tests: teacher ablation, runner, teacher policies, teacher training.
- [x] Run real ablation: `python scripts/experiments/run_3dof_teacher_coupling_ablation.py --seeds 0 1 2 --total-timesteps 128 --episodes 16 --output outputs/revision/teacher_coupling_ablation_20260425.json`.
- [x] Record result interpretation for Gate A.

### P0.3 Motion-Matched Impedance Ablation

- [x] Add failing test for `build_motion_matched_grid`.
- [x] Add conditions: `vi_full`, `fi_full`, `vi_motion_fi_k`, `fi_motion_vi_k`, `tuned_fi_k`.
- [x] Extend condition dataclass with `motion_rule`, `impedance_rule`, `fixed_stiffness_xy`, `fixed_stiffness_z`.
- [x] Add config-resolve test for existing presets or `dataclasses.replace` specs.
- [x] Implement motion-matched grid builder.
- [x] Add tuned fixed K values from existing tuned fixed sweep.
- [x] Extend runner with `--include-motion-matched`.
- [x] Extend runner with `--motion-matched-output`.
- [x] Run focused teacher-coupling tests.
- [x] Run real motion-matched export.
- [x] Record result interpretation for Gate A.

### P0.4 SCI Sensitivity and Alternative Metric Audit

- [x] Create failing test `tests/three_dof/test_three_dof_support_metric_sensitivity.py::test_sci_sensitivity_configs_cover_fine_default_coarse`.
- [x] Create `src/vi_full/three_dof_support_metric_sensitivity.py`.
- [x] Implement `build_sci_sensitivity_configs` with fine/default/coarse configs.
- [x] Add tests for `compute_nearest_demo_distance`.
- [x] Add tests for `compute_support_jaccard`.
- [x] Add tests for `compute_state_only_sci`.
- [x] Add tests for `compute_action_only_sci`.
- [x] Add synthetic SCI rank-stability test across all 3x3 bin configs.
- [x] Implement all four alternative metrics in pure NumPy.
- [x] Add predictive audit schema test.
- [x] Implement predictive audit aggregation fields: success rate, contact-entry rate, jam rate, peak force, contact work, final distance, contact steps.
- [x] Create CLI `scripts/experiments/export_3dof_support_metric_sensitivity.py`.
- [x] Add CLI args: `--input-artifacts`, `--output-stem`, `--smoke-only`.
- [x] Run SCI focused tests.
- [x] Generate real report: `outputs/revision/sci_sensitivity_20260425.{json,csv,md}`.
- [x] Apply Gate C and update response matrix.

### P0.5 Manuscript Claim-Boundary Rewrite

- [x] Decide title: conservative diagnostic title or support-gated learnability title.
- [x] Search `paper/main.tex` for `Sprint` and remove paper-facing internal process terms.
- [x] Search for `Branch` and remove paper-facing internal process terms.
- [x] Search for `confirm JSON` and remove paper-facing internal process terms.
- [x] Search for `benchmark-local recipe` and replace with controlled protocol wording.
- [x] Reduce repeated `teacher-coupled` wording to precise matched-demonstration language.
- [x] Rewrite abstract around learnability gate, SCI diagnostic, and VI lower-load role.
- [x] Rewrite contributions using `We study`, `We audit`, `We decouple`, `We show under matched-success mechanics`.
- [x] Remove or downgrade `We propose SG-VI` language.
- [x] Remove or downgrade universal SCI language.
- [x] Add explicit non-claims about 6D wrench, orientation-induced jamming, hardware calibration, sensor drift, and vision.
- [x] Update `paper/references.bib` with restrained classical/demo-RL/offline-RL/diffusion/transformer references.
- [x] Run prose/figure tests.
- [x] Update response matrix statuses for writing changes.

---

## P1: Strongly Recommended for Credible Journal Revision

### P1.1 High-Friction Mechanics Split, Phase Portraits, and Pareto

- [ ] Create failing partition test in `tests/three_dof/test_three_dof_impedance_mechanics.py`.
- [ ] Create `src/vi_full/three_dof_impedance_mechanics.py`.
- [ ] Implement `summarize_mechanics_by_outcome`.
- [ ] Include partitions: success, failure, all.
- [ ] Include metrics: count, mean contact work, mean peak force, p95 force, contact steps, jam rate, mean Kxy, mean Kz.
- [ ] Add phase-portrait sample test.
- [ ] Implement `extract_phase_portrait_samples`.
- [ ] Add Pareto schema test.
- [ ] Implement `build_force_work_pareto`.
- [ ] Explicitly analyze the `fi_motion_vi_k` tradeoff: success recovers under variable impedance action capacity, but peak force/contact work exceed `vi_full` in the P0.3 artifact.
- [ ] Create CLI `scripts/experiments/export_3dof_impedance_mechanics.py`.
- [ ] Export JSON/CSV/Markdown mechanics summary.
- [ ] Export final Figure 3 replacement candidates as PNG/PDF.
- [ ] Run focused mechanics and existing Figure 3 tests.
- [ ] Generate real mechanics artifacts from `artifacts/mechanics/latest_three_dof_high_friction_direct_mechanics_trace.json`.
- [ ] Apply Gate B and update response matrix.

### P1.2 Classical and Modern Baseline Coverage

- [ ] Audit evidence artifacts for `ThreeDoFHybridPositionForceController`.
- [ ] Audit evidence artifacts for `ThreeDoFCompliantSearchController`.
- [ ] Audit evidence artifacts for `ThreeDoFTunedImpedanceController`.
- [ ] Audit evidence artifacts for BC-only, BC→PPO, DAPG-lite, PPO/SAC/TD3 without BC.
- [ ] If classical anchors are missing, add tests in `tests/paper/test_three_dof_evidence_matrix.py`.
- [ ] Add missing classical rows using existing controllers only.
- [ ] Decide modern low-D baseline scope: TD3+BC/SAC+demo/residual RL.
- [ ] If modern baseline selected, create a separate mini-plan before implementation.
- [ ] Update `paper/main.tex` baseline discussion.
- [ ] Update `paper/references.bib`.
- [ ] Run baseline/paper focused tests.

### P1.3 Claim-to-Evidence Table and Reproducibility Package

- [ ] Create `docs/reviews/claim_to_evidence_table_2026-04-25.md`.
- [ ] Add claim: Demo support reopens useful contact.
- [ ] Add claim: SCI diagnoses support gate.
- [ ] Add claim: VI lowers contact load.
- [ ] Add limitation column for each claim.
- [ ] Ensure final package includes config files, seeds, generators/scripts, raw logs/artifacts, figure regeneration scripts.
- [ ] Update `docs/submission/submission_package_checklist.md`.
- [ ] Update `docs/project/progress.md`.

---

## P2: Top-Tier / Scope Stress Decisions

### P2.1 Scope Stress Decision

- [ ] Choose target tier A/B/C.
- [ ] If A: document downscoped controlled-benchmark target in manuscript limitations.
- [ ] If B: define same-interface stress conditions: friction, clearance, force noise, hidden calibration/pose-frame bias, combined stress.
- [ ] If B: create separate tests and runner for stress layer.
- [ ] If C: stop and write separate cross-sim/orientation/hardware plan.
- [ ] Update Gate D in response matrix.

---

## Final Verification

- [ ] Run focused revision test suite.
- [ ] Run full no-training gate: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q`.
- [ ] Run paper asset check: `python scripts/export/build_paper_assets.py --check`.
- [ ] Build paper PDF: `python scripts/export/build_paper_pdf.py`.
- [ ] Rebuild anonymous bundle without PDF.
- [ ] Build anonymous PDF from staged snapshot.
- [ ] Rebuild anonymous bundle with PDF.
- [ ] Extract anonymous snapshot and run `python -m pytest -q tests/reviewer`.
- [ ] Record exact verification results in `docs/project/progress.md`.
- [ ] Record final package state in `docs/submission/submission_package_checklist.md`.

---

## Current Execution Recommendation

Start with P0.1, then P0.2 and P0.3. Do not rewrite the manuscript before the teacher/motion gates produce interpretable evidence, except for obvious removal of internal Sprint terminology.
