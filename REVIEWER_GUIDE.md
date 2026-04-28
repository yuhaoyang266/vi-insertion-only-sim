# Reviewer Guide

This anonymous snapshot contains the manuscript source, frozen paper artifacts, focused export scripts,
and a small reviewer smoke-test suite. It is designed for inspection and no-training verification.

## Quick Start

From the repository root:

```bash
python scripts/export/build_paper_pdf.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/reviewer
python scripts/export/build_paper_assets.py --check
```

The PDF wrapper runs `pdflatex -> bibtex -> pdflatex -> pdflatex -> pdflatex` and reports MiKTeX/PATH
diagnostics if TeX tools are not discoverable.

## Claim Boundary

- The benchmark is simulation-only and translational 3DoF.
- Table 1 and Figure 2 use the canonical schema-3 benchmark declared in
  `artifacts/main_benchmark/main_benchmark_manifest.json`.
- The evidence matrix is a claim-control table, not a mixed-contract leaderboard.
- Schema-2 artifacts are retained only for appendix diagnostics.
- SCI is a benchmark-local support diagnostic, not a general sim-to-real metric.

## Layout Map

- `paper/`: LaTeX manuscript and generated table include.
- `figures/`: checked-in main and appendix figures.
- `artifacts/main_benchmark/`: canonical benchmark, statistics report, and table artifacts.
- `outputs/evidence_matrix/`: reviewer-facing claim-control table and evidence matrix.
- `scripts/export/`: paper asset, PDF, and submission bundle utilities.
- `src/vi_full/`: implementation modules used by the exporters and tests.
- `tests/reviewer/`: minimal no-training smoke tests copied into the anonymous snapshot.
