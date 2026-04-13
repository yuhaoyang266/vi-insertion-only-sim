# vi-insertion-only-sim

GitHub-ready paper package for:

**Demonstration Support Gates Learnability in a 3DoF Variable-Impedance Insertion Benchmark**

Target repository URL, also embedded in `paper/main.tex`:

`https://github.com/yuhaoyang266/vi-insertion-only-sim`

## Repository Layout

```text
paper/
  main.tex
  references.bib

figures/
  main/
    Figure 1, Figure 2, Figure 3 assets
  appendix/
    Appendix Figure A1 and A2 assets

supplement/
  figures/
    Successful-only companion view for Figure 3

artifacts/
  main_benchmark/
    final benchmark JSON/table/statistics artifacts
  diagnostics/
    factorized mechanism sweep artifacts
  stress_tests/
    PPO large-budget, tuned fixed-stiffness, and pose-perturbation artifacts
  mechanics/
    high-friction mechanics trace and contact-transition audit artifacts

scripts/
  export/
    figure/table export scripts
  experiments/
    experiment runner scripts for the reported artifacts

src/
  vi_full/
    source modules required by the experiment and export scripts

tests/
  focused tests for paper figures, tables, and paper-facing runners

docs/
  figure_asset_manifest.md
  github_upload.md
```

## Build The Manuscript

Run LaTeX from the `paper/` directory:

```bash
cd paper
latexmk -pdf main.tex
```

The manuscript uses relative figure paths and expects the repository layout above.

## Reproduce Paper Assets

The already-exported paper assets are committed under `figures/` and `supplement/`. To regenerate
them from artifacts:

```bash
python scripts/export/export_paper_only_sim_figure1.py
python scripts/export/export_paper_only_sim_figure2.py
python scripts/export/export_paper_only_sim_high_friction_trace_figure.py
python scripts/export/export_paper_only_sim_figureA1.py
python scripts/export/export_paper_only_sim_figureA2.py
```

The export scripts are copied from the working project and may need path adjustment if run outside
this packaged layout.

## Scope Note

This repository package is intended for a benchmark-local, teacher-coupled manuscript. The paper is
not framed as a teacher-independent theorem or a general robotics algorithm ranking.
