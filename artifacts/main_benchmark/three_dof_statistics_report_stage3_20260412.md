# 3DoF Statistics Report

Benchmark source: `artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json`

## Sample Plan

- recommended training seeds: 5 to 10
- recommended episodes per seed/profile: >= 100
- observed training seeds: 5
- observed episodes per seed: 100

## Selected Comparisons

- BC -> PPO vs BC-only (stable 32/32) on success_rate: delta = 0.000, 95% CI [0.000, 0.001], p = 1.000, negligible under ceiling saturation.
- DAPG-lite vs BC-only (stable 32/32) on success_rate: delta = 0.000, 95% CI [0.000, 0.001], p = 1.000, negligible under ceiling saturation.
- Fixed-impedance RL (stable BC 32/32) vs BC -> PPO on success_rate: delta = -0.053, 95% CI [-0.121, -0.006], p = 0.062, materially different.
