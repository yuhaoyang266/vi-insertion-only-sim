# 3DoF Statistics Report

Benchmark source: `artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage4_20260429.json`

## Sample Plan

- recommended training seeds: 5 to 10
- recommended episodes per seed/profile: >= 100
- observed training seeds: 10
- observed episodes per seed: 100

## Selected Comparisons

- BC -> PPO vs BC-only (stable 32/32) on success_rate: delta = -0.162, 95% CI [-0.400, 0.000], p = 0.500, materially different.
- DAPG-lite vs BC-only (stable 32/32) on success_rate: delta = -0.147, 95% CI [-0.347, 0.000], p = 0.500, materially different.
- Fixed-impedance RL (stable BC 32/32) vs BC -> PPO on success_rate: delta = 0.046, 95% CI [-0.034, 0.179], p = 1.000, materially different.

## Support Diagnostics

| Suite | Support Coverage Index | Support Cell Coverage |
| --- | --- | --- |
| PPO w/o BC | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) |
| BC-only (stable 32/32) | 0.241 +- 0.083 (95% CI [0.193, 0.292]) | 0.155 +- 0.030 (95% CI [0.136, 0.172]) |
| Fixed-impedance RL (stable BC 32/32) | 0.031 +- 0.085 (95% CI [0.000, 0.091]) | 0.023 +- 0.064 (95% CI [0.000, 0.065]) |
| BC -> PPO | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) |
| DAPG-lite | 0.008 +- 0.013 (95% CI [0.000, 0.017]) | 0.003 +- 0.005 (95% CI [0.000, 0.007]) |
| DAPG-lite old reset (coverage collapse) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) |
| DAPG-lite old reset (repaired) | 0.008 +- 0.012 (95% CI [0.000, 0.015]) | 0.004 +- 0.005 (95% CI [0.001, 0.007]) |
| DAPG-lite new reset (coverage collapse) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) |
| DAPG-lite new reset (repaired) | 0.008 +- 0.013 (95% CI [0.000, 0.016]) | 0.003 +- 0.005 (95% CI [0.000, 0.007]) |
