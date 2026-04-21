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
teacher-coupled rather than general sim-to-real claims. The main 3DoF uncertainty benchmark JSON
artifacts now also record per-seed, per-profile, and per-suite SCI summaries under the same
benchmark-local quantization contract.

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
| Diagnostic sweep artifacts | [`artifacts/diagnostics/`](artifacts/diagnostics/) |
| Stress-test artifacts | [`artifacts/stress_tests/`](artifacts/stress_tests/) |
| Mechanics trace artifacts | [`artifacts/mechanics/`](artifacts/mechanics/) |
| Figure/table export scripts | [`scripts/export/`](scripts/export/) |
| Experiment runners | [`scripts/experiments/`](scripts/experiments/) |
| Paper-facing source modules | [`src/vi_full/`](src/vi_full/) |
| Support metric utilities | [`src/vi_full/three_dof_support_metrics.py`](src/vi_full/three_dof_support_metrics.py) |

## Evidence Map

| Evidence block | Where to look | Role |
| --- | --- | --- |
| Main five-seed benchmark | `paper/main.tex`, `figures/main/fig2_*`, `artifacts/main_benchmark/` | Final benchmark estimate |
| Appendix teacher/termination package | `figures/appendix/figA3_*`, `figures/appendix/figA4_*`, `artifacts/main_benchmark/table_3dof_appendix_schema2_20260418.*` | Supplementary teacher-ablation and jam-diagnostics evidence |
| Factorized support/reset/BC/PPO diagnostics | `artifacts/diagnostics/` | Directional mechanism analysis |
| High-friction mechanics traces | `figures/main/fig3_*`, `supplement/figures/`, `artifacts/mechanics/` | Load/work interpretation |
| PPO large-budget audit | `artifacts/stress_tests/three_dof_ppo_large_budget_ablation_20260413_full_cpu.json` | PPO-only non-contact check |
| Tuned fixed-stiffness sweep | `artifacts/stress_tests/three_dof_tuned_fixed_impedance_sweep_20260412_full.json` | Fixed-impedance tuning check |
| Pose-perturbation proxy | `artifacts/stress_tests/three_dof_pose_perturbation_study_stage5_20260412.json` | Scope stress test |

## Build The Manuscript

From the repository root:

```bash
cd paper
latexmk -pdf main.tex
```

The TeX source uses relative paths to `../figures/main/`, `../figures/appendix/`, and
`../supplement/figures/`.

## Reproduce Exported Assets

The exported PDF/PNG figures are already included. To regenerate them from the frozen artifacts,
run the export scripts from the repository root:

```bash
python scripts/export/export_paper_only_sim_figure1.py
python scripts/export/export_paper_only_sim_figure2.py
python scripts/export/export_paper_only_sim_high_friction_trace_figure.py
python scripts/export/export_paper_only_sim_figureA1.py
python scripts/export/export_paper_only_sim_figureA2.py
```

The scripts are preserved with the source modules used to produce the paper assets. If running them
outside the original working tree, verify paths before regenerating figures.

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
python scripts/export/export_paper_only_sim_benchmark_table.py --benchmark-input <phase_c_benchmark.json> --fixed-impedance-input <fixed_impedance_override.json> --statistics-report-input <statistics_report.json>
```

When the input benchmark JSON includes `support_metrics`, the supplementary statistics report also
exports Support Coverage Index (SCI) and support-cell-coverage summaries alongside the main table
confidence intervals.

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
