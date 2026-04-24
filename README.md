# vi-insertion-only-sim

Simulation-only research package for the manuscript:

**Support-Gated Variable-Impedance Learning in a 3DoF Insertion Benchmark**

This repository contains the LaTeX source, paper figures, frozen result artifacts, and focused
reproduction scripts for a controlled 3DoF analytical insertion benchmark. The central claim is
deliberately scoped: in this teacher-coupled benchmark, behavior-cloning demonstration support is
the cleanest gate into useful contact, while variable impedance has a localized high-friction
load/work advantage rather than implying a general algorithm ranking. The current paper-facing
constructive layer packages the main recipe as Support-Gated Variable-Impedance Learning (SG-VI):
explicit variable-impedance actions, BC warm-start, and factorized support controls. It also
introduces Support Coverage Index (SCI), a quantized rollout-to-demo support-overlap diagnostic
implemented in `src/vi_full/three_dof_support_metrics.py`. Both remain benchmark-local and
teacher-coupled rather than general sim-to-real claims. The canonical paper-facing benchmark source
is declared in `artifacts/main_benchmark/main_benchmark_manifest.json`; it assigns the schema-3
stage3 artifact to the main manuscript Table 1 and Figure 2, while schema-2 artifacts are retained
for appendix / diagnostic legacy use only.

Repository URL embedded in the manuscript:

`https://github.com/yuhaoyang266/vi-insertion-only-sim`

## Quick Links

| Item | Path |
| --- | --- |
| Manuscript source | [`paper/main.tex`](paper/main.tex) |
| Bibliography | [`paper/references.bib`](paper/references.bib) |
| Main figures | [`figures/main/`](figures/main/) |
| Appendix figures | [`figures/appendix/`](figures/appendix/) |
| Supplementary successful-only mechanics view | [`supplement/figures/`](supplement/figures/) |
| Final benchmark artifacts | [`artifacts/main_benchmark/`](artifacts/main_benchmark/) |
| Sprint 2 reviewer table | [`outputs/evidence_matrix/three_dof_sprint2_main_table.md`](outputs/evidence_matrix/three_dof_sprint2_main_table.md) |
| Sprint 3 kickoff matrix | [`outputs/sprint3_teacher_mini_ablation/sprint3_teacher_mini_ablation_kickoff_matrix.pdf`](outputs/sprint3_teacher_mini_ablation/sprint3_teacher_mini_ablation_kickoff_matrix.pdf) |
| Sprint 4 clearance sweep | [`outputs/sprint4_clearance_shift/sprint4_clearance_shift.md`](outputs/sprint4_clearance_shift/sprint4_clearance_shift.md) |
| Sprint 4 clearance summary | [`outputs/sprint4_clearance_shift/sprint4_clearance_shift_summary.pdf`](outputs/sprint4_clearance_shift/sprint4_clearance_shift_summary.pdf) |
| Pure-RL budget-curve summary | [`outputs/cross_family_confirm/three_dof_cross_family_confirm_learning_curve_summary.png`](outputs/cross_family_confirm/three_dof_cross_family_confirm_learning_curve_summary.png) |
| Diagnostic sweep artifacts | [`artifacts/diagnostics/`](artifacts/diagnostics/) |
| Stress-test artifacts | [`artifacts/stress_tests/`](artifacts/stress_tests/) |
| Mechanics trace artifacts | [`artifacts/mechanics/`](artifacts/mechanics/) |
| Figure/table export scripts | [`scripts/export/`](scripts/export/) |
| Submission bundle builder | [`scripts/export/build_submission_bundle.py`](scripts/export/build_submission_bundle.py) |
| Experiment runners | [`scripts/experiments/`](scripts/experiments/) |
| Paper-facing source modules | [`src/vi_full/`](src/vi_full/) |
| Support metric utilities | [`src/vi_full/three_dof_support_metrics.py`](src/vi_full/three_dof_support_metrics.py) |

## Evidence Map

| Evidence block | Where to look | Role |
| --- | --- | --- |
| Main five-seed benchmark | `paper/main.tex`, `figures/main/fig2_*`, `artifacts/main_benchmark/` | Final benchmark estimate |
| Sprint 2 three-layer reviewer table | `outputs/evidence_matrix/three_dof_sprint2_main_table.*`, `outputs/evidence_matrix/three_dof_evidence_matrix.*` | Mixed-contract claim control, not a leaderboard |
| Sprint 3 teacher mini-ablation kickoff | `outputs/sprint3_teacher_mini_ablation/sprint3_teacher_mini_ablation_kickoff.{json,csv,md}` and `outputs/sprint3_teacher_mini_ablation/sprint3_teacher_mini_ablation_kickoff_matrix.{pdf,png}` | Frozen teacher support quality x demo rollout budget boundary before new training |
| Sprint 4 pure-clearance shift sweep | `outputs/sprint4_clearance_shift/sprint4_clearance_shift.{json,csv,md}` and `outputs/sprint4_clearance_shift/sprint4_clearance_shift_summary.{pdf,png}` | Selected demo-supported suites under a pure easy/nominal/hard clearance ladder |
| Pure-RL nominal-only budget curves | `outputs/cross_family_confirm/three_dof_cross_family_confirm_learning_curve_summary.*`, `outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json` | Distance proxy, success, and contact gate versus train budget |
| Appendix teacher/termination package | `figures/appendix/figA3_*`, `figures/appendix/figA4_*`, `artifacts/main_benchmark/table_3dof_appendix_schema2_20260418.*` | Supplementary teacher-ablation and jam-diagnostics evidence |
| Factorized support/reset/BC/PPO diagnostics | `artifacts/diagnostics/` | Directional mechanism analysis |
| High-friction mechanics traces | `figures/main/fig3_*`, `supplement/figures/`, `artifacts/mechanics/` | Load/work interpretation |
| PPO large-budget audit | `artifacts/stress_tests/three_dof_ppo_large_budget_ablation_20260413_full_cpu.json` | PPO-only non-contact check |
| Tuned fixed-stiffness sweep | `artifacts/stress_tests/three_dof_tuned_fixed_impedance_sweep_20260412_full.json` | Fixed-impedance tuning check |
| Pose-perturbation proxy | `artifacts/stress_tests/three_dof_pose_perturbation_study_stage5_20260412.json` | Scope stress test |

## Build The Manuscript

From the repository root:

```bash
python scripts/export/build_paper_pdf.py
```

The TeX source uses relative paths to `../figures/main/`, `../figures/appendix/`, and
`../supplement/figures/`.

The wrapper checks for `pdflatex` and `bibtex`, prints actionable MiKTeX/PATH diagnostics when they
are missing, then runs the direct `pdflatex -> bibtex -> pdflatex -> pdflatex` chain. Manual fallback
is the same sequence from inside `paper/` if wrapper diagnostics are not needed:
`pdflatex -interaction=nonstopmode -halt-on-error main.tex`, `bibtex main`, then two more
`pdflatex` passes.

## Build The Submission Bundle

The repository now includes a dedicated anonymous submission-bundle builder. From the repository
root:

```bash
python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind
```

This writes an `anonymous_snapshot/` tree, an `editor_materials/` tree, a
`submission_bundle_manifest.json`, a `submission_bundle_summary.md`, and zip archives for both
directories. The anonymous snapshot deliberately rewrites `README.md` and `paper/main.tex`, includes
only the reviewer-facing `tests/reviewer/` smoke subset, and excludes reviewer-irrelevant staging
content such as `docs/github_upload.md`, the rest of `tests/`, and the editor-only submission notes
from the reviewer-facing copy.

Keep `--output-dir` as a dedicated staging path such as `tmp/submission_bundle/...`. The builder
now rejects destinations that point at the repository root or that live inside copied source trees
such as `outputs/`, `paper/`, `scripts/`, or `src/`, because those paths would either delete the
working tree or recurse into self-copying source data.

Once an anonymous manuscript PDF is available, add it with:

```bash
python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind --paper-pdf <anonymous_manuscript.pdf>
```

Keep `<anonymous_manuscript.pdf>` outside the staged bundle directory, for example
`tmp/submission_bundle/anonymous_manuscript.pdf`. The builder recreates `--output-dir` on each run
and now rejects in-place PDF paths before deleting the staging tree.

## Reproduce Exported Assets

The exported PDF/PNG figures and generated main table are already included. To check or regenerate
the canonical paper-facing assets from the manifest, run from the repository root:

```bash
python scripts/export/build_paper_assets.py --check
python scripts/export/build_paper_assets.py
```

Advanced users can still run individual exporters; main-paper table and Figure 2 commands should pass
`--manifest artifacts/main_benchmark/main_benchmark_manifest.json` so they resolve the stage3 source
through the canonical manifest.

Appendix-only teacher/termination assets are exported from a Phase C benchmark artifact:

```bash
python scripts/export/export_paper_only_sim_appendix_table.py --benchmark-input <phase_c_benchmark.json>
python scripts/export/export_paper_only_sim_figureA3.py --benchmark-input <phase_c_benchmark.json>
python scripts/export/export_paper_only_sim_figureA4.py --benchmark-input <phase_c_benchmark.json>
```

If a stable fixed-impedance override artifact is available, pass it with `--fixed-impedance-input`
to keep the appendix diagnostics aligned with the paper-facing stable baseline.

Supplementary benchmark statistics and the main paper table can also be regenerated from the same
benchmark artifact:

```bash
python scripts/experiments/run_3dof_statistics_report.py --input <phase_c_benchmark.json> --fixed-impedance-input <fixed_impedance_override.json>
python scripts/export/export_paper_only_sim_benchmark_table.py --manifest artifacts/main_benchmark/main_benchmark_manifest.json
```

The Sprint 2 reviewer-facing table and pure-RL budget-curve summary use the frozen confirm report,
evidence matrix, and canonical main-benchmark manifest:

```bash
python scripts/experiments/export_3dof_cross_family_confirm_report.py --pilot-report outputs/pilot_report/three_dof_cross_family_pilot_report.json --output-dir outputs/cross_family_confirm
python scripts/experiments/export_3dof_evidence_matrix.py --confirm-report outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json --manifest artifacts/main_benchmark/main_benchmark_manifest.json --output-dir outputs/evidence_matrix
```

Read `outputs/evidence_matrix/three_dof_sprint2_main_table.md` as a three-layer claim-control
table: pure-RL nominal-only negatives, demo-supported contact-reopening rows, and a mechanics /
fixed-impedance anchor. `SAC w/o BC` is only a zero-contact distance proxy in that table; it is not
a solve-insertion or useful-contact claim.

The Sprint 3 teacher mini-ablation kickoff is a boundary artifact, not a training result. It freezes
the 4-condition teacher support quality x demo rollout budget matrix and now exports both a machine-
readable bundle and a reviewer-facing matrix figure while keeping BC steps, PPO steps, policy
initialization, metrics, and paper-facing claim limits fixed before running new jobs:

```bash
python scripts/experiments/export_sprint3_teacher_mini_ablation_kickoff.py --output-dir outputs/sprint3_teacher_mini_ablation
```

Sprint 4A adds a pure-clearance stress sweep for the selected demo-supported suites. The generated
artifact bundle is sprint-specific: it uses a `clearance_easy` / `nominal` / `clearance_hard`
ladder, exports a reviewer-facing summary figure, and must not be read as a replacement for the
frozen five-profile manuscript benchmark:

```bash
python scripts/experiments/export_sprint4_clearance_shift.py --output-dir outputs/sprint4_clearance_shift
```

When the input benchmark JSON includes `support_metrics`, the supplementary statistics report also
exports Support Coverage Index (SCI) and support-cell-coverage summaries alongside the main table
confidence intervals.

The bundled canonical main benchmark JSON is
`artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json`;
the paired canonical statistics report is
`artifacts/main_benchmark/three_dof_statistics_report_stage3_20260412.json`;
schema-2 benchmark artifacts remain appendix / diagnostic legacy inputs only.

## Reproduce Experiments

The frozen artifacts used by the manuscript are included under `artifacts/`. The corresponding
runners are kept under `scripts/experiments/`:

```bash
python scripts/experiments/run_3dof_uncertainty_benchmark.py
python scripts/experiments/run_3dof_factor_sweeps.py
python scripts/experiments/run_3dof_ppo_large_budget_ablation.py
python scripts/experiments/run_3dof_tuned_fixed_impedance_sweep.py
python scripts/experiments/run_3dof_pose_perturbation_study.py
python scripts/experiments/run_3dof_statistics_report.py --input <phase_c_benchmark.json>
python scripts/experiments/export_sprint4_clearance_shift.py --output-dir outputs/sprint4_clearance_shift
```

These runs can be computationally slower than figure export. For manuscript inspection, the frozen
JSON/Markdown artifacts are the canonical paper record.

## Scope

This is a simulation-only, translational 3DoF analytical benchmark. It uses relative observations,
synthetic force signals, diagonal stiffness decoding, and behavior-cloning demonstrations generated
by a variable-impedance teacher. The repository should therefore be read as a benchmark-local,
teacher-coupled learnability study rather than a hardware validation, a 6DoF insertion benchmark, or
a teacher-independent causal theorem.

Phase C+ benchmark artifacts also report two force-jam diagnostics with intentionally different
semantics: `jam_rate` tracks the active jam termination rule (`three consecutive force-threshold
violations OR persistent blocked contact`), while `documented_force_jam_rate` isolates just the
paper-facing force-jam slice (`three consecutive force-threshold violations`, excluding pure
blocked-contact failures). Both are retained so the combined jam rate and the force-specific jam
mechanism stay auditable side by side.

## Repository Hygiene

The repository intentionally separates manuscript files, figures, supplementary views, result
artifacts, scripts, source modules, and tests. Generated LaTeX products and Python caches are
ignored; frozen paper artifacts are tracked.
