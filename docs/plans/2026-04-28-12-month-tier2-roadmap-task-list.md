## 12-Month Tier-2 Roadmap Task List (2026-04-28)

> Decomposes `docs/plans/2026-04-28-12-month-tier2-roadmap-plan.md` into execution-sized items. Each block ties tasks to one Sprint exit gate. **Do not start a later Sprint until the prior Sprint's exit gate is recorded as `[x]`.**

### Status Legend

- `[ ]` not started
- `[~]` in progress
- `[x]` complete
- `[!]` blocked / needs user decision
- `[-]` dropped (record reason in `docs/project/progress.md`)

---

## Sprint A — Tier-3 Submission Readiness (Weeks 1-4, exit 2026-05-26)

### A.1 Canonical artifact unification

- [x] Audit every reference to a benchmark JSON path under `paper/`, `README.md`, `scripts/export/`, `scripts/experiments/`, `outputs/evidence_matrix/`, `artifacts/main_benchmark/`. Record findings in `docs/project/progress.md`.
- [x] Change `scripts/export/export_paper_only_sim_figure2.py` default input to read from `artifacts/main_benchmark/main_benchmark_manifest.json -> canonical_main_benchmark.path`.
- [x] Change `scripts/export/export_paper_only_sim_benchmark_table.py` default input the same way.
- [x] Regenerate `outputs/evidence_matrix/three_dof_sprint2_main_table.{md,csv,json}` from canonical manifest; verify Fixed-impedance RL success == 0.947, DAPG-lite success == 1.000.
- [x] Verify `paper/main.tex` Section 3.1 and Table 1 numbers match `artifacts/main_benchmark/table_3dof_paper_benchmark_stage3_20260412.md`.
- [x] Add `tests/paper/test_paper_table_sync.py::test_main_table_matches_default_export_and_evidence_matrix` (numeric-equality regression).
- [x] Run `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/paper/test_paper_table_sync.py tests/paper/test_three_dof_evidence_matrix.py tests/artifacts/`.

### A.2 LaTeX build path hardening

- [x] Read current `scripts/export/build_paper_pdf.py`. Confirm it probes for MiKTeX install path on Windows (`C:\Users\Windows\AppData\Local\Programs\MiKTeX\miktex\bin\x64\`) and prints actionable diagnostics on failure.
- [x] Update `README.md` "Build The Manuscript" section so the documented default command is `python scripts/export/build_paper_pdf.py` and not raw `pdflatex`.
- [x] Add a fresh-shell smoke check: open a new terminal, run the documented command, capture exit code, paste in `docs/project/progress.md`.
- [x] If wrapper fails on a fresh shell, fix wrapper (PATH probe order, error message), do not rewrite README to match.

### A.3 Anonymous-snapshot reviewer surface

- [x] Add top-level `REVIEWER_GUIDE.md` (anonymized) covering: build command, smoke-test command, claim-boundary summary, layout map.
- [x] Update `scripts/export/build_submission_bundle.py` to always include `REVIEWER_GUIDE.md` and `tests/reviewer/` inside `anonymous_snapshot/`, regardless of opt-out flags.
- [x] Add `tests/packaging/test_submission_bundle.py::test_snapshot_includes_reviewer_guide_and_reviewer_tests`.
- [x] Build a sample bundle: `python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind`. Record manifest + zip sizes in progress log.

### A.4 Path lineage cleanup

- [x] Remove all `F:\edge download\learning\...` and `full_projects\vi_insertion_full_only_sim\...` strings from any tracked artifact under `artifacts/main_benchmark/*.md`.
- [x] Replace with repo-relative path + sha256 + git_commit + generating_command.
- [x] Add `tests/artifacts/test_artifact_provenance.py::test_no_local_absolute_paths_in_paper_artifacts`.

### A.5 Cover letter and submission

- [x] Write `docs/submission/cover_letter_tier3_template.md`. Position as "controlled simulation benchmark for support-gated learnability and variable-impedance load paths in 3DoF insertion".
- [x] Decide target venue (recommendation: Robotica primary; Advanced Robotics fallback). Record decision in `docs/project/progress.md`.
- [x] Final manuscript build: `python scripts/export/build_paper_pdf.py` -> verify page count and references resolved.
- [x] Final bundle: `python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind --paper-pdf <pdf>`.
- [x] **Sprint A Gate A1 sign-off:** GitHub Actions `reviewer-smoke` and `paper-assets-check` passed on `8f46792`. Bundle build produced a self-consistent snapshot; Sprint B remains unchanged until this Gate A1 record is committed.

---

## Sprint B — Matched-Protocol Main-Table Evidence (Weeks 5-12, exit 2026-07-21)

### B.1 Motion-matched main protocol

- [ ] Add failing test `tests/sprints/test_three_dof_motion_matched_main_protocol.py::test_motion_matched_main_grid_uses_main_benchmark_contract`.
- [ ] Create `src/vi_full/three_dof_motion_matched_main_protocol.py` reusing `three_dof_teacher_coupling_ablation.py` condition definitions but binding to `DEFAULT_3DOF_BENCHMARK_CONTRACT` (5 seeds / 100 episodes / 5 profiles / paper-matched PPO budget).
- [ ] Create runner `scripts/experiments/run_3dof_motion_matched_main_protocol.py` with `--seeds`, `--episodes-per-seed`, `--profiles`, `--output`.
- [ ] Run real protocol: `python scripts/experiments/run_3dof_motion_matched_main_protocol.py --seeds 0..4 --episodes-per-seed 100 --output artifacts/main_benchmark/three_dof_motion_matched_main_<date>.json`.
- [ ] Add bootstrap-CI + paired sign-permutation aggregation; export to `artifacts/main_benchmark/table_3dof_motion_matched_<date>.md`.
- [ ] Update `paper/main.tex` Section 3 to add a "motion-matched teacher decoupling" main-table block; cite `vi_full + vi_K` vs `vi_motion + fi_K` vs `fi_motion + vi_K` vs `fi_full` results.
- [ ] Update `docs/reviews/review_response_matrix_2026-04-25.md` Gate A row from "P0.3 evidence recorded" to "main-protocol evidence landed" with the new artifact path.

### B.2 Success-matched mechanics replacement for Figure 3

- [ ] Add failing test `tests/three_dof/test_three_dof_impedance_mechanics.py::test_success_failure_split_partitions_traces`.
- [ ] Create `src/vi_full/three_dof_impedance_mechanics.py` with: `partition_traces_by_outcome`, `compute_success_matched_force_curve`, `compute_success_matched_work_curve`, `compute_force_position_phase_portrait`, `compute_force_work_pareto_rows`.
- [ ] Add tests for each function (synthetic traces; assert deterministic numpy outputs).
- [ ] Create runner `scripts/experiments/export_3dof_impedance_mechanics.py`.
- [ ] Generate new Figure 3 composite: success-only force/work curves + Pareto + phase-portrait subplot. Save as `figures/main/fig3_high_friction_impedance_mechanism.{pdf,png}`.
- [ ] Move legacy heterogeneous figure to `figures/appendix/fig3_legacy_all_trace_*` for traceability.
- [ ] Update `paper/main.tex` Figure 3 caption and Section 3.4 prose to reflect success-matched contrast.
- [ ] Update `docs/reviews/review_response_matrix_2026-04-25.md` "VI value unclear" row from `Pending P1.1` to `Resolved` with new artifact path.

### B.3 Real-trace SCI association audit

- [ ] Add failing test `tests/three_dof/test_three_dof_real_trace_sci_audit.py::test_real_trace_audit_emits_predictive_rows`.
- [ ] Create `src/vi_full/three_dof_real_trace_sci_audit.py`. Pull demo and rollout traces from canonical artifacts (or add a trace-export step to canonical benchmark runner if traces are not currently persisted).
- [ ] Decision point `[!]`: if canonical artifact does not store raw traces, decide between (a) re-running the canonical benchmark with `--persist-traces`, or (b) keeping SCI demoted to exploratory appendix-only diagnostic. Record decision in `docs/project/progress.md`.
- [ ] If (a): rerun canonical benchmark with traces; refresh manifest; refresh statistics report.
- [ ] If (b): rewrite `paper/main.tex` Section 2.4 to demote SCI to "exploratory benchmark-local diagnostic, currently without strong real-trace association".
- [ ] Run audit; export `outputs/revision/sci_real_trace_<date>.{json,csv,md}`.
- [ ] Update `docs/reviews/review_response_matrix_2026-04-25.md` Gate C row.

### B.4 10-seed canonical benchmark expansion

- [ ] Run canonical benchmark with seeds 0..9: produce `artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage4_<date>.json`.
- [ ] Refresh `artifacts/main_benchmark/three_dof_statistics_report_stage4_<date>.json` with 10-seed bootstrap CI and paired sign-permutation tests.
- [ ] Update `artifacts/main_benchmark/main_benchmark_manifest.json` to add a `canonical_main_benchmark_stage4` entry; flag stage3 as `superseded_by_stage4` while keeping it readable.
- [ ] Update `paper/main.tex` main table to use stage4 numbers; verify near-ceiling success differences against the previous 5-seed numbers.
- [ ] Decision point `[!]`: if stage4 invalidates the near-ceiling equality story, **rewrite Section 3.1 conservatively** before continuing.

### B.5 Manuscript Section 3 restructure

- [ ] Rewrite `paper/main.tex` so Section 3 has three explicit main evidence blocks: (i) main 5-profile benchmark (stage4), (ii) motion-matched teacher decoupling (B.1), (iii) success-matched mechanics (B.2).
- [ ] Demote SG-VI from a contribution to a Section 2.4 "controlled benchmark protocol" header.
- [ ] Run prose tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/paper/test_paper_claim_boundaries.py tests/paper/test_prose_statistics_sync.py`.

### B.6 Sprint B revision submission

- [ ] If Tier-3 reviews have arrived: bundle into a revision; otherwise prepare a supplementary update for the active submission.
- [ ] **Sprint B Gate B1 sign-off:** all four B.1-B.4 evidence blocks live, manuscript Section 3 restructured, all CI passes.

---

## Sprint C — External Validity via Paper-B Bridge (Weeks 13-24, exit 2026-10-13)

> **Two-paper coordination (2026-04-28 update):** original cross-sim (MJX / Drake spike) is **replaced** by bridging Paper-A's learned suites into Paper-B (`research-cartesian-impedance-vla-sim`)'s MuJoCo `peg_in_hole.py` environment. Cross-paper interface contract lives in `docs/cross_paper_interface_contract.md` (mirrored in Paper-B repo). Schema-P 5D action mapping, 14D observation projection, success / jam definitions, and demo-dataset format are pinned by SHA in both copies.

### C.0 Cross-paper interface contract

- [ ] Author `docs/cross_paper_interface_contract.md` in Paper-A repo. Sections required: (i) action schema mapping (`(Δx, Δy, Δz, κ_xy, κ_z)` <-> Paper-B Schema-P 5D), (ii) observation projection (Paper-B 6D pose + 6D wrench + state -> Paper-A 14D analytical observation), (iii) success / jam / horizon definitions, (iv) 5-profile evaluation suite, (v) demo dataset schema, (vi) version pinning protocol.
- [ ] Mirror identical contract to Paper-B repo at `docs/cross_paper_interface_contract.md`. Both copies head-pinned by SHA; update atomically.
- [ ] Add `tests/cross_paper/test_cross_paper_contract_sha_pin.py` to Paper-A; assert the SHA constant in `cross_paper_bridge.py` matches the markdown contract head SHA.
- [ ] Decision point `[!]`: confirm with Paper-B owner that the contract's action-mapping rule (force `dyaw=0` when feeding A's policy into B) is acceptable for B's RA-L scope.

### C.1 Paper-B repo readiness gate

- [ ] Verify Paper-B `peg_in_hole.py` environment passes its own physical-correctness audit (W2 in Paper-B `task_plan.md`). Record the verifying commit hash in `docs/cross_paper_interface_contract.md`.
- [ ] Run Paper-B parity smoke: drive its environment with a Schema-P scripted policy at zero-impedance variance; expect deterministic episode within tolerance per the contract.
- [ ] Time-box this gate to week 18 (mid-Sprint C). Record in `docs/project/progress.md`.
- [ ] **Fallback path `[!]`:** if Paper-B parity gate not met by week 18, switch to within-A alternative contact model: implement `src/vi_full/three_dof_alt_contact_model.py`, treat it as a within-repo "second contact model" cross-check, and explicitly declare in Section 5 that the Paper-B bridge is deferred to a follow-up.

### C.2 Cross-paper bridge module

- [ ] Add failing test `tests/cross_paper/test_cross_paper_bridge_contract.py::test_bridge_translates_action_and_observation_per_contract`.
- [ ] Create `src/vi_full/cross_paper_bridge.py`. Wrap each of Paper-A's 5 learned suites (`PPO w/o BC`, `BC-only`, `Fixed-impedance RL`, `BC->PPO`, `DAPG-lite`) so they run inside Paper-B's MuJoCo env via the contract.
- [ ] Implement contract-SHA refusal: bridge raises if the SHA constant disagrees with `docs/cross_paper_interface_contract.md` head.
- [ ] Create runner `scripts/experiments/run_cross_sim_via_paper_b.py` with `--paper-b-repo-path`, `--paper-b-commit`, `--profiles`, `--seeds`, `--episodes-per-seed`, `--output`.
- [ ] Run main cross-sim protocol: 5 profiles x 5 seeds x 100 episodes x 5 learned suites against Paper-B's MuJoCo env. Pin the Paper-B commit on the CLI; verify it equals the contract-pinned commit.
- [ ] Create `src/vi_full/cross_sim_ranking.py`; export ranking-stability table to `outputs/cross_sim/three_dof_cross_sim_ranking_paper_b_<date>.{json,csv,md}`. Top-3 stability margin must be reported, not only ranks.

### C.3 Contact-parameter sensitivity sweep (within-A grounding)

- [ ] Add failing test `tests/three_dof/test_three_dof_contact_parameter_sensitivity.py::test_sensitivity_grid_covers_three_levels_per_parameter`.
- [ ] Create `src/vi_full/three_dof_contact_parameter_sensitivity.py`. Sweep `(alpha_xy, alpha_z, mu_wall, jam_threshold, transition_band)` at fine/default/coarse levels.
- [ ] Create runner `scripts/experiments/run_3dof_contact_parameter_sensitivity.py`.
- [ ] Run sweep on canonical 5 learned suites. Export to `outputs/revision/contact_parameter_sensitivity_<date>.{json,csv,md}`.
- [ ] Identify the parameter most likely to overturn support-gate finding; document in `docs/project/progress.md`.

### C.4 Modern baseline (choose ONE)

- [ ] Decision point `[!]`: choose baseline. Recommendation order: IQL/CQL offline (fastest to land, uses existing demos) > Diffusion Policy via LeRobot > ACT.
- [ ] Add failing test for chosen baseline scaffold.
- [ ] Create `src/vi_full/modern_baseline_<chosen>.py`. Reuse 14D obs / 5D action / canonical demo dataset.
- [ ] Create runner `scripts/experiments/run_modern_baseline_<chosen>.py`.
- [ ] Run on 5 seeds / 100 episodes / 5 profiles. Export to `artifacts/main_benchmark/three_dof_modern_baseline_<chosen>_<date>.json`.
- [ ] Add modern-baseline row to main table even if it underperforms.
- [ ] Update `paper/references.bib` with the corresponding citation.

### C.5 Manuscript Section 5 + Tier-2 cover letter

- [ ] Add Section 5 "Cross-simulator stability via the Paper-B physics environment" to `paper/main.tex`. Cite Paper-B explicitly; clarify non-overlapping scope (Paper-A: learnability gate; Paper-B: force-bounded safety layer); state that the cross-sim numbers are reproduced under `docs/cross_paper_interface_contract.md` against the pinned Paper-B commit.
- [ ] Add new tables for cross-sim ranking (under Paper-B), contact-parameter sensitivity (within-A), and modern-baseline row.
- [ ] Update Limitations section: drop "no cross-sim validation" line; keep "no hardware" and "translational only"; add "no force-bounded safety guarantee — see Paper-B".
- [ ] Update title only if evidence justifies; do not change otherwise.
- [ ] Write `docs/submission/cover_letter_tier2_template.md`. Reference Paper-B as a coordinated companion submission, not a derivative work.
- [ ] **Sprint C Gate C1 sign-off:** Paper-B parity gate met (or fallback path explicitly invoked), cross-sim ranking landed, sensitivity sweep landed, one modern baseline landed, manuscript Section 5 added.

---

## Sprint D — 6D / Offline-RL / Tier-2 Submission (Weeks 25-52, exit 2027-04-26)

### D.1 SE(3)-local-linearized 6D environment

- [ ] Add failing test `tests/six_dof/test_six_dof_local_linearized_env.py::test_six_dof_environment_reduces_to_three_dof_when_orientation_disabled`.
- [ ] Create `src/vi_full/six_dof_local_linearized_env.py`. Quasi-static moment model around 3DoF kernel, small-angle roll/pitch/yaw approximation. Reuse analytical contact law where possible.
- [ ] Add reset / step / reward parity tests against 3DoF when orientation flag is disabled.
- [ ] Create runner `scripts/experiments/run_six_dof_main_protocol.py`.
- [ ] Run main protocol on 6D: 5 seeds / 100 episodes / 5 profiles / 5 main learned suites.
- [ ] Decision point `[!]`: if support-gate finding does not reproduce within 3DoF bootstrap CI, **reframe the paper as scaling-boundary study**. Do not force.

### D.2 Offline-RL baselines (IQL + CQL)

- [ ] Add failing tests for both `iql` and `cql` on canonical demo dataset.
- [ ] Create `src/vi_full/three_dof_offline_rl_baselines.py`. Implement both with minimal torch + numpy.
- [ ] Run on 5 seeds / 100 episodes / 5 profiles. Export to `artifacts/main_benchmark/three_dof_offline_rl_<date>.json`.
- [ ] Add IQL/CQL rows to main table.

### D.3 Manuscript Section 6 + Tier-2 submission

- [ ] Add Section 6 "Scope expansion to 6D and offline-RL".
- [ ] Add Figure 4 6D evidence block.
- [ ] Update title only if 6D reproduces.
- [ ] Re-run all CI workflows + manuscript build.
- [ ] **Decision point `[!]`:** target venue. Recommendation: RAL (short-format, sim-friendly) primary; IEEE T-Mech secondary; RCIM tertiary.
- [ ] Build final bundle and submit.
- [ ] **Sprint D Gate D1 sign-off:** Tier-2 submission acknowledged by venue editor or editor desk-rejection feedback received and digested.

---

## Cross-Sprint Standing Rules

- Never modify `paper/main.tex` numbers ahead of the artifact landing for that block.
- Always add a failing test before adding a new module. The repo's test-first convention is load-bearing for reviewer trust.
- Update `docs/project/progress.md` with every command + exit code. Reviewer audits that file.
- Update `docs/reviews/review_response_matrix_2026-04-25.md` Status column whenever a Gate readout changes.
- Keep `MEMORY.md` untouched by these tasks; project state lives in `docs/project/`.
- If a sprint slips past its exit date, do **not** start the next sprint. Submit the current state at the matching downgrade tier.
