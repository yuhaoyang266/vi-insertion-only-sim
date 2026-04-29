# Review Response Matrix 2026-04-25

This internal matrix binds each high-risk reviewer concern to required evidence, manuscript scope, and a decision gate. It is not an anonymous-submission artifact unless explicitly selected later.

| Reviewer concern | Claim affected | Severity | Required evidence | Planned experiment / text revision | Success criterion | Manuscript location | Response draft | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Teacher support and VI prior are confounded | VI value; support gate | Fatal | FI teacher x VI teacher crossed ablation | Add VI/FI teacher x VI/FI policy crossed experiment | Demonstration-support effect remains visible after teacher impedance prior is controlled; VI value is stated only if VI improves load/work or robustness under FI/matched support | Main + appendix | We added crossed teacher/action-space and motion-matched controls to separate demonstration support from impedance prior. The Sprint B main-protocol artifact keeps broad VI superiority gated: teacher support/motion remains a claim boundary, while variable-impedance command capacity is supported only under matched-support contrasts. | Main-protocol evidence landed: `artifacts/main_benchmark/three_dof_motion_matched_main_20260429.json` |
| Motion prior and impedance prior are confounded | VI value | Fatal | Motion-matched impedance controls | Add VI motion + FI K and FI motion + VI K comparisons | The manuscript can state whether the observed effect comes from motion support, stiffness schedule, or both | Main | We decouple motion command source from stiffness command source and report the residual impedance effect. The 2026-04-29 main-protocol run shows `fi_motion_vi_k` succeeds (1.000 five-profile mean) while `vi_motion_fi_k` and `fi_full` fail, so the revised claim should emphasize variable-impedance action capacity under matched teacher support rather than broad VI-teacher superiority. | Main-protocol evidence landed; Gate A supports bounded VI-capacity language |
| SCI is post-hoc and bin-dependent | SCI diagnostic | Major | Bin sensitivity + alternative support metrics | Add fine/default/coarse SCI, state-only/action-only SCI, nearest-demo distance, Jaccard/MMD if stable | SCI remains correlated with contact entry/success across bin settings and is not dominated by trivial distance metrics; otherwise SCI is downgraded | Main summary + appendix full grid | We audited SCI against a 3x3 state/action bin grid and continuous alternatives rather than relying on one discretization. The Sprint B artifact audit found aggregated support metrics but no raw demo/rollout trace fields in the target canonical artifacts, so SCI is formally retained as an exploratory benchmark-local diagnostic rather than predictive real-trace evidence. | Gate C resolved by formal downgrade |
| VI value unclear because tuned FI can succeed | VI physical role | Major | Success-matched mechanics analysis | Add success/failure split, success-only curves, success-matched force/work, Pareto, phase portraits | VI shows lower load/work under matched-success conditions, not just higher success or mixed failure composition | Main Figure 3 replacement + appendix | We no longer claim broad VI superiority; Figure 3 now uses equal-count successful traces and reports lower load/work only inside the released high-friction success-matched subset. | Resolved for Gate B evidence: `outputs/revision/three_dof_impedance_mechanics_20260429.json` |
| 3DoF analytical benchmark may be toy | External validity | Major/Fatal depending venue | Stress layer or downscoped claims | Add cross-sim/contact-model stress if targeting Q2+; otherwise put orientation/real-robot in limitations | Support-gate and lower-load trends survive at least contact-model/parameter stress, or the paper explicitly targets a controlled benchmark note | Main limitations + supplement if run | We treat the benchmark as controlled evidence and avoid sim-to-real claims. | Pending P2.1 |
| Internal process jargon weakens credibility | All claims | Major | Full prose cleanup | Remove Sprint/Branch/confirm JSON language from manuscript | Abstract, intro, experiments, and conclusion read as a coherent scientific argument, not an engineering log | Main | We rewrote the paper around support, motion, and impedance factors, replacing process labels with controlled benchmark, matched-demonstration, teacher-boundary, and pure-clearance stress terminology. | P0.5 prose rewrite complete |

## Decision Gates

- Gate A: If FI-teacher or motion-matched controls invalidate the VI claim, remove VI superiority language and make support/motion the main result.
- Gate B: If success-only or success-matched mechanics do not show lower work/load for VI, remove Figure 3 causal interpretation.
- Gate C: If SCI is bin-sensitive or lacks useful association with contact/success metrics, demote SCI to exploratory appendix diagnostic.
- Gate D: If no cross-sim/contact-stress/orientation layer is added, do not target the paper as a general robot-insertion method.

## Update Protocol

- Update `Status` when each evidence block lands, and keep any response draft conservative until the corresponding gate is evaluated.
- Prefer claim downgrades over adding unsupported prose if a gate is ambiguous.
- Keep manuscript-facing language benchmark-local unless a later stress layer changes the evidence boundary.

## Gate A Interim Readout (P0.2)

- Artifact: `outputs/revision/teacher_coupling_ablation_20260425.json`.
- Minimal crossed result: `vi_teacher_vi_student` success 1.00; `vi_teacher_fi_student` success 0.67; both FI-teacher conditions success 0.00 under the small 3-seed / 128-step / 16-episode run.
- Interpretation: teacher support/motion quality is not separable enough to support broad VI-superiority language yet; keep VI claims conditional until P0.3 motion-matched impedance controls land.


## Gate A Readout (P0.3)

- Artifact: `outputs/revision/motion_matched_impedance_ablation_20260425.json`.
- Minimal motion-matched result: `vi_full` success 1.00, `fi_full` success 0.00, `vi_motion_fi_k` success 0.00, `fi_motion_vi_k` success 1.00, `tuned_fi_k` success 0.00 under the small 3-seed / 128-step / 16-episode run.
- Sprint B main-protocol artifact: `artifacts/main_benchmark/three_dof_motion_matched_main_20260429.json`; table: `artifacts/main_benchmark/table_3dof_motion_matched_20260429.md`.
- Main-protocol result: `vi_full` success 0.800, `fi_full` success 0.000, `vi_motion_fi_k` success 0.000, `fi_motion_vi_k` success 1.000 under the 5-seed / 100-episode / five-profile / 128-step run.
- Interpretation: the decisive contrast is not just VI teacher motion. The `fi_motion_vi_k` condition recovers success while fixed-K variants fail, supporting a bounded claim that variable impedance/action capacity can reopen useful insertion under this controlled benchmark. Keep load/work claims gated on P1 mechanics.

## Gate B Readout (Sprint B)

- Artifact: `outputs/revision/three_dof_impedance_mechanics_20260429.json`; CSV: `outputs/revision/three_dof_impedance_mechanics_20260429.csv`; main figure: `figures/main/fig3_high_friction_impedance_mechanism.{pdf,png}`.
- Legacy all-trace assets: `figures/appendix/fig3_legacy_all_trace_high_friction_impedance_mechanism.{pdf,png}`.
- Success-matched protocol: equal 75 successful high-friction traces per method from `artifacts/mechanics/latest_three_dof_high_friction_direct_mechanics_trace.json`.
- Readout: learned variable has lower mean peak force than learned fixed (1.188 N vs 1.437 N) and slightly lower final contact work (0.003220 vs 0.003405); hand-crafted variable also stays below the default fixed anchor on both load and work.
- Interpretation: Figure 3 can now be used as a success-matched mechanics explanation inside the released high-friction trace protocol. Keep the claim benchmark-local and avoid treating tuned fixed impedance as physically impossible.


## Gate C Readout (P0.4)

- Artifact: `outputs/revision/sci_sensitivity_20260425.{json,csv,md}`.
- Audit coverage: 3x3 fine/default/coarse state/action SCI configs, synthetic SCI rank-stability rows, nearest-demo distance, Jaccard, state-only SCI, action-only SCI, and predictive rows with success/contact/jam/force/work/distance/steps fields.
- Sprint B artifact capability audit: `artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json`, `outputs/revision/teacher_coupling_ablation_20260425.json`, and `outputs/revision/motion_matched_impedance_ablation_20260425.json` expose `support_metrics` summaries but no persisted `demo_observations`, `demo_actions`, `rollout_observations`, `rollout_actions`, or trace-run fields needed for a real-trace SCI association audit.
- Interpretation: tooling, schema, and synthetic rank-stability checks are in place, but the target artifacts do not contain the raw state-action traces needed for real-trace association. SCI is formally downgraded to an exploratory benchmark-local diagnostic and should not be described as predictive validity evidence.


## P0.5 Manuscript Boundary Readout

- Updated `paper/main.tex`, `README.md`, and `docs/figure_asset_manifest.md` to remove paper-facing Sprint/Branch/confirm-JSON phrasing and reduce teacher-coupled/propose language.
- Retitled the manuscript around support-gated learnability and variable-impedance load paths, added explicit non-claims for 6D wrench dynamics, orientation-induced jamming, sensor drift, and vision, and added restrained Diffusion Policy / ACT / IQL scope-setting references.
- Contribution wording now uses study/audit/decouple/show framing and keeps SG-VI/SCI benchmark-local.
- Prose tests passed after rewrite.


