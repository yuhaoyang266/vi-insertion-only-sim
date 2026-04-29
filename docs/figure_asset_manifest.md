# Only-Sim Figure Asset Manifest

This note defines the canonical asset names and export locations for the figures referenced by the
only-sim manuscript. It does not create plots or change any paper-facing result. Its role is only
to lock the file stems, output directory, and source-artifact mapping before actual figure export.

## Scope

- Main-body figures: `Figure 1`, `Figure 2`, `Figure 3`
- Appendix figures: `Figure A1`, `Figure A2`, `Figure A3`, `Figure A4`
- Supporting MuJoCo demo clips remain supporting media and are not promoted to numbered paper
  figures in the current draft

## Canonical Output Location

Rendered figure assets are organized under:

- `figures/main/` for manuscript Figures 1--3
- `figures/appendix/` for appendix figures
- `supplement/figures/` for supplementary companion views

Recommended export pair for each figure:

- `<stem>.pdf` as the canonical manuscript asset
- `<stem>.png` as a staging / slide / markdown-friendly fallback

If a figure is assembled from multiple panels, the final combined export should still use a single
canonical stem rather than panel-specific filenames.

## Naming Convention

Use the following stable stem pattern:

- main body: `fig<number>_<short_slug>`
- appendix: `figA<number>_<short_slug>`

Slug rules:

- lowercase ASCII only
- words separated by underscores
- keep the semantic unit, not the data source filename
- prefer the paper meaning over the implementation detail

## Manifest

| Figure | Canonical Stem | Expected Export Files | Manuscript Role | Primary Source Artifacts | Status |
| --- | --- | --- | --- | --- | --- |
| Figure 1 | `fig1_task_policy_impedance_overview` | `figures/main/fig1_task_policy_impedance_overview.pdf` and `.png` | main-body task/interface schematic for the structured 3DoF policy | generated directly by `src/vi_full/paper_figures.py` | exported |
| Figure 2 | `fig2_main_benchmark_evaluation_class_summary` | `figures/main/fig2_main_benchmark_evaluation_class_summary.pdf` and `.png` | main-body summary of the final benchmark across evaluation classes | `artifacts/main_benchmark/main_benchmark_manifest.json` -> `canonical_main_benchmark` -> `artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage4_20260429.json` | exported |
| Figure 3 | `fig3_high_friction_impedance_mechanism` | `figures/main/fig3_high_friction_impedance_mechanism.pdf` and `.png` | main-body success-matched high-friction mechanics evidence for the fixed-versus-variable comparison | `outputs/revision/three_dof_impedance_mechanics_20260429.json` | exported |
| Figure 3 companion | `fig3_high_friction_impedance_mechanism_success_only` | `supplement/figures/fig3_high_friction_impedance_mechanism_success_only.pdf` and `.png` | supplementary successful-only companion view for the high-friction mechanics traces | `artifacts/mechanics/latest_three_dof_high_friction_direct_mechanics_trace.json` | exported |
| Figure 3 legacy | `fig3_legacy_all_trace_high_friction_impedance_mechanism` | `figures/appendix/fig3_legacy_all_trace_high_friction_impedance_mechanism.pdf` and `.png` | appendix legacy heterogeneous all-trace mechanics diagnostic | `artifacts/mechanics/latest_three_dof_high_friction_direct_mechanics_trace.json` | exported |
| Figure A1 | `figA1_evaluation_class_mapping` | `figures/appendix/figA1_evaluation_class_mapping.pdf` and `.png` | appendix mapping from nominal profiles to evaluation classes | generated directly by `src/vi_full/paper_figures.py` | exported |
| Figure A2 | `fig1_contact_transition_audit` | `figures/appendix/fig1_contact_transition_audit.pdf` and `.png` | appendix contact-transition audit retained under a legacy stem for compatibility | `artifacts/mechanics/latest_three_dof_contact_model_audit.json` | exported |
| Figure A3 | `figA3_teacher_ablation_summary` | `figures/appendix/figA3_teacher_ablation_summary.pdf` and `.png` | appendix teacher 2x2 motion-versus-impedance summary | `artifacts/main_benchmark/three_dof_benchmark_schema2_paper_teacher_20260418_034230.json`, `artifacts/main_benchmark/table_3dof_appendix_schema2_20260418.json` | exported |
| Figure A4 | `figA4_termination_diagnostics_summary` | `figures/appendix/figA4_termination_diagnostics_summary.pdf` and `.png` | appendix termination-diagnostics decomposition across learned suites | `artifacts/main_benchmark/three_dof_benchmark_schema2_paper_teacher_20260418_034230.json`, `artifacts/main_benchmark/table_3dof_appendix_schema2_20260418.json` | exported |

## Reviewer-Facing Main-Table Assets

These assets support the main-table claim boundary but are not a new cross-contract leaderboard.

| Asset | Expected Export Files | Source Artifacts | Role |
| --- | --- | --- | --- |
| Three-layer main table | `outputs/evidence_matrix/three_dof_sprint2_main_table.json`, `.csv`, and `.md` | `outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json`, `outputs/evidence_matrix/three_dof_evidence_matrix.json`, `artifacts/main_benchmark/main_benchmark_manifest.json` -> `canonical_main_benchmark` -> `artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage4_20260429.json` | pure-RL nominal-only negatives, demo-supported contact reopening, and mechanics / fixed-impedance anchor |
| Pure-RL budget-curve summary | `outputs/cross_family_confirm/three_dof_cross_family_confirm_learning_curve_summary.pdf` and `.png` | `outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json` | distance proxy, success, and contact steps versus training budget within the nominal-only pure-RL contract |

## Reviewer-Facing Teacher-Boundary Assets

These assets freeze the next experiment boundary before training. They are not result tables and should
not be cited as outcome evidence.

| Asset | Expected Export Files | Source Artifacts | Role |
| --- | --- | --- | --- |
| Teacher mini-ablation boundary | `outputs/sprint3_teacher_mini_ablation/sprint3_teacher_mini_ablation_kickoff.json`, `.csv`, `.md`, and `sprint3_teacher_mini_ablation_kickoff_matrix.pdf` / `.png` | generated directly by `src/vi_full/sprint3_teacher_mini_ablation_kickoff.py` | 4-condition teacher support quality x demo rollout budget boundary with fixed metrics, controls, closure criteria, and a reviewer-facing kickoff matrix |

## Reviewer-Facing Clearance-Stress Assets

These assets add a sprint-specific pure-clearance stress ladder. They are paper-facing robustness
artifacts, not new manuscript figure exports and not a replacement for the frozen five-profile
benchmark contract.

| Asset | Expected Export Files | Source Artifacts | Role |
| --- | --- | --- | --- |
| Pure-clearance shift sweep | `outputs/sprint4_clearance_shift/sprint4_clearance_shift.json`, `.csv`, `.md`, and `sprint4_clearance_shift_summary.pdf` / `.png` | generated directly by `src/vi_full/sprint4_clearance_shift.py` via `scripts/experiments/export_sprint4_clearance_shift.py` | selected demo-supported suites under a pure `clearance_easy` / `nominal` / `clearance_hard` ladder with fixed train profile, explicit claim boundary, and a reviewer-facing summary figure |

## Panel Intent

These panel intents are locked only to keep export work aligned with the current manuscript.

### Figure 1

- schematic overview
- show the observation stack, the structured 5D action, and the meaning of fixed vs variable stiffness
- keep the figure implementation-local and deterministic rather than tying it to a frozen benchmark JSON

### Figure 2

- main benchmark summary
- show success across the three evaluation classes plus the 5-profile mean column
- keep the same five main learned suites that appear in the paper-facing final benchmark table
- use the attached statistics report only for brief comparison notes, not for a second result panel

### Figure 3

- four-suite success-matched direct-mechanics figure
- panels: successful-contact force, cumulative contact work, force-position phase portrait, force-work Pareto
- include `learned_fixed`, `learned_variable`, `handcrafted_fixed`, and `handcrafted_variable`
- use equal-count successful traces as the primary manuscript view
- keep the previous `all_traces` export as an appendix legacy diagnostic, not the main explanation

### Figure A1

- mapping diagram
- show how `nominal`, `tight_clearance`, and `offset_bias` collapse into the `baseline` class
- keep `high_friction` and `noisy_force` as separate evaluation classes

### Figure A2

- appendix-only contact-model audit
- keep the legacy stem `fig1_contact_transition_audit` for compatibility with existing exports
- show the original vs repaired contact law and the safe-window widening from about `0.85 mm` to about `1.25 mm`

### Figure A3

- appendix-only teacher ablation view
- keep the 2x2 structure explicit: motion rule by impedance rule
- main panel shows five-profile mean success; auxiliary readout shows force and final-distance cost

### Figure A4

- appendix-only termination diagnostics view
- split jammed outcomes into `force_only`, `blocked_only`, and `force_and_blocked`
- keep `documented_force_jam_rate` separate from the stacked jam attribution bars

## Supporting Media Boundary

The existing MuJoCo demo clips remain supporting media and are not included in this manuscript-only
GitHub package. In the full working repository they live under:

- `outputs/mujoco_demo_clips_pose_lock_socket_retrained_three_panel/`

Current files already present there:

- `nominal_learned_success_seed10000.gif`
- `stress_xy_learned_success_seed10001.gif`
- `stress_xy_learned_jam_seed10003.gif`
- `manifest.json`

These clips are not renamed into `Figure S1` assets in the current paper package. If a later venue
requires a visual supplement, they can be referenced as demo media rather than promoted to the main
figure numbering scheme.

## Export Checklist

Before any actual figure export is considered complete, check:

1. The exported filename matches the canonical stem exactly.
2. The figure caption in the manuscript uses the same figure number and semantic label.
3. The plotted source artifact paths match the manifest above.
4. The asset is written to `figures/` or `supplement/figures/`, not to `docs/`.
5. Appendix figures do not introduce any new claim beyond the current strict-criterion and
   supporting-closure readings.

