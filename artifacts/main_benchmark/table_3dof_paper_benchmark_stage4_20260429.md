# 3DoF Paper Benchmark Table

Main benchmark source: `artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage4_20260429.json`
Statistics source: `artifacts/main_benchmark/three_dof_statistics_report_stage4_20260429.json`

Entries report mean +- std with 95% CI where a statistics report is attached.

## Main Table

| Suite | Success | Jam | Final Dist (mm) | Mean Peak Force (N) | P95 Force (N) | Contact Steps |
| --- | --- | --- | --- | --- | --- | --- |
| PPO w/o BC | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 18.366 +- 0.321 (95% CI [18.167, 18.560]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) |
| BC-only (stable 32/32) | 1.000 +- 0.001 (95% CI [0.999, 1.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.899 +- 0.009 (95% CI [0.893, 0.904]) | 0.979 +- 0.095 (95% CI [0.925, 1.042]) | 1.303 +- 0.123 (95% CI [1.225, 1.383]) | 28.940 +- 1.615 (95% CI [27.937, 29.994]) |
| Fixed-impedance RL (stable BC 32/32) | 0.884 +- 0.296 (95% CI [0.684, 1.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.994 +- 0.142 (95% CI [0.931, 1.094]) | 1.002 +- 0.165 (95% CI [0.905, 1.109]) | 1.314 +- 0.217 (95% CI [1.190, 1.454]) | 30.198 +- 8.968 (95% CI [24.715, 35.890]) |
| BC -> PPO | 0.838 +- 0.335 (95% CI [0.615, 1.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.980 +- 0.113 (95% CI [0.917, 1.055]) | 0.794 +- 0.136 (95% CI [0.716, 0.880]) | 1.040 +- 0.180 (95% CI [0.939, 1.158]) | 24.886 +- 6.446 (95% CI [21.587, 29.482]) |
| DAPG-lite | 0.853 +- 0.317 (95% CI [0.653, 1.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 1.020 +- 0.157 (95% CI [0.938, 1.130]) | 0.922 +- 0.152 (95% CI [0.835, 1.020]) | 1.214 +- 0.205 (95% CI [1.097, 1.348]) | 24.712 +- 8.032 (95% CI [20.545, 30.738]) |
| DAPG-lite old reset (coverage collapse) | 0.100 +- 0.300 (95% CI [0.000, 0.300]) | 0.073 +- 0.180 (95% CI [0.000, 0.198]) | 2.350 +- 1.655 (95% CI [1.444, 3.540]) | 37.607 +- 63.951 (95% CI [2.120, 82.930]) | 47.124 +- 74.724 (95% CI [8.267, 94.055]) | 19.478 +- 5.589 (95% CI [15.669, 22.688]) |
| DAPG-lite old reset (repaired) | 0.700 +- 0.458 (95% CI [0.400, 1.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 1.110 +- 0.302 (95% CI [0.949, 1.304]) | 0.925 +- 0.170 (95% CI [0.824, 1.032]) | 1.216 +- 0.227 (95% CI [1.090, 1.369]) | 24.889 +- 8.106 (95% CI [20.520, 30.482]) |
| DAPG-lite new reset (coverage collapse) | 0.200 +- 0.400 (95% CI [0.000, 0.500]) | 0.125 +- 0.262 (95% CI [0.000, 0.291]) | 2.155 +- 1.432 (95% CI [1.339, 3.126]) | 13.360 +- 25.333 (95% CI [1.043, 29.723]) | 23.668 +- 44.573 (95% CI [1.654, 53.743]) | 19.091 +- 6.414 (95% CI [14.827, 22.669]) |
| DAPG-lite new reset (repaired) | 0.853 +- 0.317 (95% CI [0.606, 1.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 1.020 +- 0.157 (95% CI [0.939, 1.124]) | 0.922 +- 0.152 (95% CI [0.837, 1.017]) | 1.214 +- 0.205 (95% CI [1.098, 1.349]) | 24.712 +- 8.032 (95% CI [20.524, 30.764]) |

## Handcrafted / Classical Anchors

| Suite | Success | Jam | Final Dist (mm) | Mean Peak Force (N) | P95 Force (N) | Contact Steps |
| --- | --- | --- | --- | --- | --- | --- |
| Pose-only | 1.000 | 0.000 | 0.969 | 1.107 | 1.465 | 10.999 |
| Handcrafted fixed impedance | 1.000 | 0.000 | 0.969 | 2.942 | 3.913 | 11.000 |
| Handcrafted variable impedance | 0.991 | 0.000 | 0.946 | 0.881 | 1.141 | 30.588 |
| Hybrid position-force | 1.000 | 0.000 | 0.885 | 3.313 | 4.407 | 16.485 |
| Compliant search | 1.000 | 0.000 | 0.867 | 2.880 | 3.831 | 15.252 |
| Hand-tuned impedance | 1.000 | 0.000 | 0.939 | 3.581 | 4.813 | 37.191 |

## Comparison Notes

- Fixed-impedance RL (stable BC 32/32): vs BC -> PPO on success_rate: materially different.
- BC -> PPO: vs BC-only (stable 32/32) on success_rate: materially different.
- DAPG-lite: vs BC-only (stable 32/32) on success_rate: materially different.

## Annotation

Five nominal eval profiles collapse to three effective pressure classes in this 3DoF environment design.

- `baseline`: nominal, tight_clearance, offset_bias. No extra active pressure under current 3DoF semantics. offset_bias is absorbed by the relative observation coordinate frame; tight_clearance only activates under lateral overflow.
- `high_friction`: high_friction. Force-impedance coupling. higher wall friction changes the contact force response.
- `noisy_force`: noisy_force. Force-sensor uncertainty. force noise perturbs the observed contact signal.
