# Review Response Matrix 2026-04-25

This internal matrix binds each high-risk reviewer concern to required evidence, manuscript scope, and a decision gate. It is not an anonymous-submission artifact unless explicitly selected later.

| Reviewer concern | Claim affected | Severity | Required evidence | Planned experiment / text revision | Success criterion | Manuscript location | Response draft | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Teacher support and VI prior are confounded | VI value; support gate | Fatal | FI teacher x VI teacher crossed ablation | Add VI/FI teacher x VI/FI policy crossed experiment | Demonstration-support effect remains visible after teacher impedance prior is controlled; VI value is stated only if VI improves load/work or robustness under FI/matched support | Main + appendix | We added a crossed teacher/action-space ablation to separate demonstration support from impedance prior. | Pending P0.2 |
| Motion prior and impedance prior are confounded | VI value | Fatal | Motion-matched impedance controls | Add VI motion + FI K and FI motion + VI K comparisons | The manuscript can state whether the observed effect comes from motion support, stiffness schedule, or both | Main | We decouple motion command source from stiffness command source and report the residual impedance effect. | Pending P0.3 |
| SCI is post-hoc and bin-dependent | SCI diagnostic | Major | Bin sensitivity + alternative support metrics | Add fine/default/coarse SCI, state-only/action-only SCI, nearest-demo distance, Jaccard/MMD if stable | SCI remains correlated with contact entry/success across bin settings and is not dominated by trivial distance metrics; otherwise SCI is downgraded | Main summary + appendix full grid | We audited SCI against bin settings and continuous alternatives rather than relying on one discretization. | Pending P0.4 |
| VI value unclear because tuned FI can succeed | VI physical role | Major | Success-matched mechanics analysis | Add success/failure split, success-only curves, success-matched force/work, Pareto, phase portraits | VI shows lower load/work under matched-success conditions, not just higher success or mixed failure composition | Main Figure 3 replacement + appendix | We no longer claim broad VI superiority; we report lower-load contact paths when supported by matched mechanics evidence. | Pending P1.1 |
| 3DoF analytical benchmark may be toy | External validity | Major/Fatal depending venue | Stress layer or downscoped claims | Add cross-sim/contact-model stress if targeting Q2+; otherwise put orientation/real-robot in limitations | Support-gate and lower-load trends survive at least contact-model/parameter stress, or the paper explicitly targets a controlled benchmark note | Main limitations + supplement if run | We treat the benchmark as controlled evidence and avoid sim-to-real claims. | Pending P2.1 |
| Internal process jargon weakens credibility | All claims | Major | Full prose cleanup | Remove Sprint/Branch/confirm JSON language from manuscript | Abstract, intro, experiments, and conclusion read as a coherent scientific argument, not an engineering log | Main | We rewrote the paper around support, motion, and impedance factors. | Pending P0.5 |

## Decision Gates

- Gate A: If FI-teacher or motion-matched controls invalidate the VI claim, remove VI superiority language and make support/motion the main result.
- Gate B: If success-only or success-matched mechanics do not show lower work/load for VI, remove Figure 3 causal interpretation.
- Gate C: If SCI is bin-sensitive or lacks useful association with contact/success metrics, demote SCI to exploratory appendix diagnostic.
- Gate D: If no cross-sim/contact-stress/orientation layer is added, do not target the paper as a general robot-insertion method.

## Update Protocol

- Update `Status` when each evidence block lands, and keep any response draft conservative until the corresponding gate is evaluated.
- Prefer claim downgrades over adding unsupported prose if a gate is ambiguous.
- Keep manuscript-facing language benchmark-local unless a later stress layer changes the evidence boundary.
