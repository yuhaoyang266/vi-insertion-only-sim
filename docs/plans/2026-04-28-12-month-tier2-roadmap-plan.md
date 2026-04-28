## 12-Month Tier-2 Roadmap Plan (2026-04-28)

> **Scope:** 12-month evidence-hardening roadmap that takes the current `vi-insertion-only-sim` from "submission-ready Tier-3 (SCI Q3) controlled-benchmark paper" to a credible Tier-2 (RAL / IEEE T-Mech / RCIM) candidate. Conservative by default; every Sprint declares a downgrade path so we can publish at the highest tier the evidence actually supports.
>
> **For agentic workers:** Companion task list is `docs/plans/2026-04-28-12-month-tier2-roadmap-task-list.md`. Treat each Sprint as a separate `Phase 7.x` block in `docs/project/task_plan.md` and append result entries to `docs/project/progress.md` with verification commands.

**Tech stack:** Python, NumPy, Matplotlib, pytest, existing `vi_full` modules, LaTeX manuscript in `paper/main.tex`. Plan adds MuJoCo MJX or Drake hydroelastic for cross-sim, optionally LeRobot/diffusion-policy for one modern baseline. No hardware on this roadmap.

---

### 1. Current State Diagnosis (2026-04-28)

**Resolved already (per `docs/reviews/review_response_matrix_2026-04-25.md`):**

- P0.2 teacher-coupling crossed ablation (`outputs/revision/teacher_coupling_ablation_20260425.json`, 3 seeds / 16 episodes / 128 steps)
- P0.3 motion-matched impedance ablation (`outputs/revision/motion_matched_impedance_ablation_20260425.json`, same small protocol)
- P0.4 SCI sensitivity tooling and 3x3 bin grid (`outputs/revision/sci_sensitivity_20260425.{json,csv,md}`)
- P0.5 manuscript prose cleanup (Sprint/Branch/confirm-JSON jargon removed, SG-VI/SCI scoped to benchmark-local)
- Canonical artifact manifest (`artifacts/main_benchmark/main_benchmark_manifest.json`) with sha256 + git_commit + generating_command

**Outstanding P0 risk (must clear before any submission):**

1. Artifact provenance unification across `paper/main.tex`, `README.md`, default exporter scripts, and `outputs/evidence_matrix/*` (per `docs/reviews/project_review_sci_assessment_20260424.md` P0-1).
2. README LaTeX build commands fail on a fresh PATH; `scripts/export/build_paper_pdf.py` must be the documented default and must run on the reviewer environment.
3. Anonymous submission bundle currently excludes most of `tests/`. A reviewer-facing reproducibility surface (`tests/reviewer/` + a `REVIEWER_GUIDE.md`) must be guaranteed inside the snapshot.
4. P0.2 / P0.3 small-protocol (3 seeds / 16 episodes / 128 steps) results currently sit in `docs/reviews/`, not as a paper-table layer. They are too small to upgrade to a main-benchmark contract; either keep them appendix-only or run an upgraded matched-protocol run before referencing them in the abstract.

**Outstanding scientific gaps (the reason a 12-month plan exists):**

- Teacher / VI prior coupling is only contained, not eliminated. Need a 5-seed / 100-episode-per-seed motion-matched contract under the main 5-profile evaluation suite.
- No cross-simulator stability check: a single-environment analytical contact model is not portable evidence.
- No modern demo-augmented baseline at the Tier-2 expected level (Diffusion Policy / ACT / IQL / CQL). DAPG-lite is intentionally not a faithful reproduction.
- Mechanics analysis (Figure 3) is heterogeneous all-trace; success-matched force/work/Pareto/phase-portrait views are still missing.
- SCI raw-trace association on real demos/rollouts is unfinished (P0.4 explicitly downgraded SCI to bounded diagnostic).
- 6D / orientation / pose-coupled jamming is only a proxy. SE(3) extension is the cleanest path to lift the "toy 3DoF" critique.

### 2. Roadmap Spine

```text
We accept that the present paper is a Tier-3 controlled-benchmark publication.
The 12-month plan converts it into a Tier-2 candidate by hardening four axes in
order: (A) submission readiness, (B) matched-protocol main-table evidence,
(C) external validity via cross-sim and modern baselines, (D) scope expansion
to 6D / orientation / offline-RL and one stronger venue submission.
Each Sprint has an independent publication exit so we never block on optional
evidence we cannot land in time.
```

Implication: do not delay submission of the Tier-3 paper while running Tier-2 work. Sprint A submits; Sprints B-D extend and resubmit at higher tier.

### 3. Sprint Plan and Decision Gates

#### Sprint A — Tier-3 submission readiness (Weeks 1-4, ends 2026-05-26)

**Goal:** Submit current manuscript to a Tier-3 venue (Robotica / Advanced Robotics / JIRS / Intelligent Service Robotics) within four weeks. Do not add experimental scope. Only fix submission-blocking artifact provenance, build commands, and reviewer-facing packaging.

**Exit gate (Gate A1):** `python scripts/export/build_paper_pdf.py` succeeds on a fresh PATH, `python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind --paper-pdf <pdf>` produces a snapshot whose paper-facing tables, README evidence map, and evidence-matrix all reference the same canonical artifact (`main_benchmark_manifest.json` -> stage3), and a numeric-equality regression test enforces this. If this gate fails by 2026-05-26, defer everything else and finish Sprint A.

**Downgrade path:** if numeric drift cannot be eliminated, target `Sensors` / `Machines` / `Actuators` Q4 instead — same paper, lower confidence venue.

#### Sprint B — Matched-protocol main-table evidence (Weeks 5-12, ends 2026-07-21)

**Goal:** Upgrade the 4 most fragile evidence layers from small diagnostic protocol (3 seeds / 16 episodes / 128 steps) to main-benchmark contract (5 seeds / 100 episodes per seed/profile / 128 PPO steps under 5 profiles), and replace Figure 3 with success-matched mechanics.

**Exit gate (Gate B1):** Motion-matched, teacher-coupling, success-matched mechanics, and a 10-seed expansion of the canonical main benchmark all live under the same protocol map (Tab. A1 in `paper/main.tex`) and have bootstrap-CI + paired-test entries. Manuscript Section 3 is restructured around three main evidence blocks: (i) main 5-profile benchmark, (ii) motion-matched teacher decoupling, (iii) success-matched mechanics. SCI is either backed by a real-trace association audit or formally demoted to "exploratory appendix diagnostic" (Gate C in review matrix).

**Downgrade path:** if cross-sim work in Sprint C cannot land, this Sprint B output is sufficient to resubmit at *Robotica* / *Advanced Robotics* with substantially stronger main-table evidence and a tighter VI claim.

#### Sprint C — External validity via Paper-B MuJoCo cross-sim and modern baselines (Weeks 13-24, ends 2026-10-13)

**Two-paper coordination note (2026-04-28 update):** Original Sprint C planned a ground-up MJX or Drake hydroelastic cross-sim. That spike is replaced by **bridging to the sister project `research-cartesian-impedance-vla-sim` (Paper-B) MuJoCo 7-DoF Panda environment**, after agreement to publish Paper-A and Paper-B as a cross-cited two-paper bundle (Paper-A: support-gated learnability; Paper-B: contact-state-aware adaptive impedance safety layer). The interface contract that both papers commit to is `docs/cross_paper_interface_contract.md` (mirror copy lives in the Paper-B repo). The contract pins the Schema-P 5D action mapping (`(Δx, Δy, Δz, κ_xy, κ_z)`), the 14D observation projection, the success / jam definitions, the 5-profile evaluation suite, and the canonical demo dataset format so that ranking comparisons between Paper-A's analytical 3DoF benchmark and Paper-B's MuJoCo physics environment are measured under one protocol.

**Goal:** Land three external-validity blocks. (i) Cross-sim ranking-stability table by running Paper-A's five learned suites (`PPO w/o BC`, `BC-only`, `Fixed-impedance RL`, `BC->PPO`, `DAPG-lite`) inside Paper-B's MuJoCo `peg_in_hole.py` environment under the contract above; (ii) contact-parameter sensitivity sweep over `(alpha_xy, alpha_z, mu_wall, jam_threshold, transition_band)` on Paper-A's analytical environment, kept to ground the MuJoCo cross-check rather than to replace it; (iii) one modern demo-augmented baseline (recommendation: IQL/CQL on the existing canonical demo dataset; falls back fastest because no environment interaction is needed).

**Exit gate (Gate C1):** Cross-sim ranking on the 5 learned suites under the same 5-profile evaluation contract has top-3 stability margin <= 1 rank change OR the manuscript explicitly flags the instability. Sensitivity sweep covers >= 3 levels per parameter. One modern baseline runs end-to-end under the 5-profile contract and is added to the main table even if it underperforms. Paper-B repo has run a parity smoke pass through the same contract and recorded its commit hash in `docs/cross_paper_interface_contract.md` so Paper-A's cross-sim numbers are traceable to a fixed Paper-B revision.

**Downgrade path:** if Paper-B's MuJoCo environment does not reach the parity smoke gate by week 18, fall back to an alternative analytical contact-law variant (`src/vi_full/three_dof_alt_contact_model.py`) and treat it as a within-A "second contact model" cross-check. Paper-A still ships at Tier-2 with this within-repo cross-check, while Paper-B's own cross-sim section is deferred to its own publication. Do not block on Paper-B beyond week 18.

#### Sprint D — 6D / orientation / offline-RL and Tier-2 submission (Weeks 25-52, ends 2027-04-26)

**Goal:** Extend the benchmark from 3DoF translational to SE(3)-local-linearized 6D with roll/pitch/yaw coupling and a quasi-static moment model. Add IQL and CQL as offline-RL baselines on the existing demo dataset. Resubmit to a target Tier-2 venue: RAL (preferred — short-format, sim-friendly), IEEE T-Mech, or RCIM.

**Exit gate (Gate D1):** SE(3) extension reproduces the support-gate finding within bootstrap CI of the 3DoF main benchmark, OR the paper repositions as "support-gate scaling boundary across 3DoF and 6D" (still publishable). Offline-RL baselines run on the canonical demo dataset and report success/contact/jam metrics. Manuscript section 4 adds a 6D evidence block and a Tier-2 cover letter.

**Downgrade path:** if 6D extension does not reproduce, do not force the result. Submit Sprint A+B+C as Tier-2 candidate with 6D as appendix-only proxy and explicit limitations. Target RCIM, which accepts simulation-grounded benchmarking.

### 4. File Architecture by Sprint

#### Sprint A files (modify only, no new modules)

- `paper/main.tex` — verify table source paths, update repository URL block if blinded.
- `README.md` — replace direct `pdflatex`/`bibtex` invocations with `python scripts/export/build_paper_pdf.py`; document MiKTeX PATH note; ensure `Reproduce Exported Assets` and `Build The Submission Bundle` sections all flow through the canonical manifest.
- `scripts/export/build_paper_pdf.py` — confirm PATH probing covers Windows MiKTeX install path, return non-zero exit code with diagnostic on failure.
- `scripts/export/build_submission_bundle.py` — guarantee `REVIEWER_GUIDE.md` and `tests/reviewer/` are copied into `anonymous_snapshot/` regardless of opt-out.
- `scripts/export/export_paper_only_sim_figure2.py` and `scripts/export/export_paper_only_sim_benchmark_table.py` — change defaults (and any hardcoded path) to read through `artifacts/main_benchmark/main_benchmark_manifest.json` -> `canonical_main_benchmark`.
- `outputs/evidence_matrix/*` — regenerate from canonical manifest; remove schema2 numbers from paper-facing copy.
- `tests/paper/test_paper_table_sync.py` — extend to assert paper main table == default exporter output == evidence-matrix selected rows == `table_3dof_paper_benchmark_stage3_*.md` numeric equality.
- `tests/packaging/test_submission_bundle.py` — assert `REVIEWER_GUIDE.md` and `tests/reviewer/` exist inside snapshot tree.

New files (Sprint A):

- `REVIEWER_GUIDE.md` (top-level, also embedded in snapshot) — quick-start for reviewers: `python scripts/export/build_paper_pdf.py`, `pytest tests/reviewer/`, layout map, claim-boundary summary.
- `docs/submission/cover_letter_tier3_template.md` — Tier-3 venue cover letter, positioned as "controlled simulation benchmark for support-gated learnability".

#### Sprint B files

- New module: `src/vi_full/three_dof_motion_matched_main_protocol.py` — wrap existing `three_dof_teacher_coupling_ablation.py` in a 5-seed / 100-episode / 5-profile protocol that matches `three_dof_benchmark.py` rather than the small diagnostic protocol.
- New runner: `scripts/experiments/run_3dof_motion_matched_main_protocol.py`.
- New module: `src/vi_full/three_dof_impedance_mechanics.py` — success/failure split, success-matched force/work curves, Pareto rows, force-position phase portrait helpers.
- New runner: `scripts/experiments/export_3dof_impedance_mechanics.py`.
- Replace: `figures/main/fig3_high_friction_impedance_mechanism.{pdf,png}` with success-matched composite (preserve old as `figures/appendix/fig3_legacy_all_trace_*`).
- New module: `src/vi_full/three_dof_real_trace_sci_audit.py` — raw demo+rollout SCI association on the canonical artifact's stored traces.
- New runner: `scripts/experiments/export_3dof_real_trace_sci_audit.py`.
- 10-seed expansion: rerun canonical main benchmark with `--seeds 0..9` and freeze as `artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage4_<date>.json`. Update `main_benchmark_manifest.json` with both stage3 and stage4; flag stage3 as superseded.
- Tests: `tests/sprints/test_three_dof_motion_matched_main_protocol.py`, `tests/three_dof/test_three_dof_impedance_mechanics.py`, `tests/runners/test_run_3dof_real_trace_sci_audit.py`.
- Manuscript: rewrite Section 3.1 / 3.2 / 3.4 around three main evidence blocks; demote SG-VI to "Section 2.4 controlled benchmark protocol" header; add motion-matched main-table row; replace Figure 3.

#### Sprint C files

- New file: `docs/cross_paper_interface_contract.md` — canonical contract bridging Paper-A (`vi-insertion-only-sim`) and Paper-B (`research-cartesian-impedance-vla-sim`). Pins Schema-P 5D action mapping, 14D observation projection, success / jam / horizon definitions, 5-profile evaluation suite, and demo dataset format. Mirror copy must exist in the Paper-B repo at the same relative path; both copies updated atomically and cross-referenced by SHA in the manifest.
- New module: `src/vi_full/cross_paper_bridge.py` — adapter that wraps Paper-A learned policies (`PPO w/o BC`, `BC-only`, `Fixed-impedance RL`, `BC->PPO`, `DAPG-lite`) for evaluation inside Paper-B's MuJoCo `peg_in_hole.py` environment. Translates 14D analytical observation <-> 7-DoF MuJoCo state via the contract above. Refuses to run if the contract SHA stored in the cross-paper bridge does not match the SHA recorded in `docs/cross_paper_interface_contract.md`.
- New module: `src/vi_full/cross_sim_ranking.py` — same-protocol ranking aggregator: 5 profiles x 5 seeds x 100 episodes; outputs `outputs/cross_sim/three_dof_cross_sim_ranking_paper_b_<date>.{json,csv,md}` with top-3 stability margin and per-profile success / jam / peak-force rows.
- New runner: `scripts/experiments/run_cross_sim_via_paper_b.py` — drives the bridge against a checked-out Paper-B working copy. CLI args: `--paper-b-repo-path`, `--paper-b-commit` (must match contract pin), `--profiles`, `--seeds`, `--episodes-per-seed`, `--output`.
- New module: `src/vi_full/three_dof_contact_parameter_sensitivity.py` — `(alpha_xy, alpha_z, mu_wall, jam_threshold, transition_band)` sweep on Paper-A's analytical environment, three levels each. Retained as a within-A sensitivity layer; not a cross-sim substitute.
- New runner: `scripts/experiments/run_3dof_contact_parameter_sensitivity.py`.
- New module: `src/vi_full/three_dof_alt_contact_model.py` — fallback alternative analytical contact law used only if the Paper-B bridge cannot land by week 18 (downgrade path). Provides a within-A "second contact model" cross-check so Sprint C can still ship at Tier-2.
- New module: `src/vi_full/modern_baseline_<chosen>.py` — choose ONE of `iql_cql_offline` (preferred), `diffusion_policy`, `act`. Implementation must reuse existing demo dataset and respect the 5D action / 14D observation contract.
- New runner: `scripts/experiments/run_modern_baseline_<chosen>.py`.
- New tests: `tests/cross_paper/test_cross_paper_bridge_contract.py` (asserts Schema-P + observation + metric parity), `tests/cross_paper/test_cross_paper_contract_sha_pin.py` (asserts the contract SHA in `cross_paper_bridge.py` matches the markdown contract head SHA).
- New manuscript section: Section 5 "Cross-simulator stability via the Paper-B physics environment"; Tables 5/6 added; Limitations updated to drop "no cross-sim" but retain "no hardware" and "translational only". Section explicitly cross-cites Paper-B and clarifies non-overlapping scope (Paper-A: learnability gate; Paper-B: force-bounded safety layer).

#### Sprint D files

- New module: `src/vi_full/six_dof_local_linearized_env.py` — quasi-static moment model around 3DoF kernel, roll/pitch/yaw with small-angle approximation; reuses analytical contact law where possible.
- New module: `src/vi_full/three_dof_offline_rl_baselines.py` — IQL and CQL on canonical demo dataset; numpy + minimal torch.
- New runners under `scripts/experiments/run_six_dof_*.py` and `scripts/experiments/run_3dof_offline_rl_*.py`.
- Manuscript: add Section 6 "Scope expansion to 6D and offline-RL", new Figure 4 6D evidence block. Update title to "Support-Gated Learnability of Variable-Impedance Insertion across 3DoF and 6D Benchmarks" (or revert if 6D does not reproduce).
- Tier-2 cover letter: `docs/submission/cover_letter_tier2_template.md`.

### 5. Verification Strategy (per Sprint)

Each Sprint must run the existing two-CI workflow plus its own focused tests before merging:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/core/test_import_boundaries.py \
  tests/reviewer
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/artifacts/test_canonical_manifest.py \
  tests/artifacts/test_artifact_provenance.py \
  tests/paper/test_exporter_defaults.py \
  tests/paper/test_paper_table_sync.py \
  tests/paper/test_three_dof_evidence_matrix.py \
  tests/paper/test_sprint2_paper_sync.py \
  tests/paper/test_paper_claim_boundaries.py
python scripts/export/build_paper_assets.py --check
```

Sprint-specific verification commands are listed in the companion task list.

### 6. Risk Register

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Sprint A artifact-unification surfaces deeper schema2/stage3 entanglement than expected | Medium | High (blocks submission) | Time-box Sprint A to 4 weeks; if not closeable, downgrade target venue and freeze stage3 numbers as "official" with a full audit trail. |
| 10-seed expansion changes the near-ceiling near-equality between BC-only / BC->PPO / DAPG-lite | Medium | Medium | This is a legitimate finding; revise abstract numbers and paired-test entries. Do not cherry-pick. |
| MJX / Drake setup blocks for >2 weeks | High on Windows | High | Pick whichever bootstraps faster on the current Windows machine; if both block, replace cross-sim with a re-implemented analytical contact model in a separate file (`three_dof_alt_contact_model.py`) and report ranking-stability across two contact-law variants. Keep the Tier-2 ambition. |
| Modern baseline (Diffusion Policy / ACT / IQL) gets stuck on infrastructure | Medium | Medium | Prefer IQL/CQL on the existing demo dataset — pure offline, no environment interaction needed. Falls back to a runnable result fastest. |
| 6D extension does not reproduce the support-gate finding | Medium | Medium | Reframe the paper as a scaling-boundary study; this is publishable at Tier-2 if the 3DoF main result is solid. |
| Statistical power stays weak even at 10 seeds | Low-Medium | Medium | Switch primary main-table metric from success rate to bootstrap-CI of contact-work / peak-force / Pareto coordinates, where seed variance is more informative. |
| Reviewer pushes for hardware | High at Tier-2 | Low (we have a defense) | Cover letter explicitly scopes the paper as cross-sim controlled benchmark; cite hardware path as separate future work; do not commit to hardware on this roadmap. |

### 7. Out of Scope (Explicit Non-Goals)

- Hardware experiments. Treat any reviewer push toward this as a "future work" item, never as a revision commitment.
- A new RL algorithm. SG-VI stays a benchmark protocol; do not promote it to a method paper.
- A general SCI metric claim. Keep SCI scoped to this benchmark unless Sprint B real-trace audit produces strong cross-method association.
- A full classical-controller survey. The current minimal anchor roster is sufficient under the controlled-benchmark frame.
- Visual / vision-based perception. Out of scope on every Sprint.

### 8. Submission Calendar (target dates)

- 2026-05-26 — Sprint A submission to Tier-3 venue (Robotica preferred for Q3-Q2 borderline).
- 2026-07-21 — Sprint B revision (if Tier-3 reviews land in time) or supplementary revision.
- 2026-10-13 — Sprint C resubmission to Tier-2 (RAL or IEEE T-Mech).
- 2027-04-26 — Sprint D resubmission to Tier-2 if D extends scope materially; otherwise final Tier-3 acceptance.

### 9. Update Protocol

- Each Sprint owner appends to `docs/project/progress.md` with command and exit code.
- Gate decisions are recorded in `docs/reviews/review_response_matrix_2026-04-25.md` (or a new `2026-XX-XX` matrix when the review cycle changes).
- Manuscript edits never precede artifact landing; preserve the established "evidence-first, prose-second" discipline.
- `MEMORY.md` is not modified by this plan; project state stays inside `docs/project/`.
