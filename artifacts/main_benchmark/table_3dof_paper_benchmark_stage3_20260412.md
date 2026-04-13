# 3DoF Paper Benchmark Table

Main benchmark source: `F:\edge download\learning\full_projects\vi_insertion_full_only_sim\outputs\three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json`
Statistics source: `F:\edge download\learning\full_projects\vi_insertion_full_only_sim\outputs\paper_only_sim_tables\three_dof_statistics_report_stage3_20260412.json`

Entries report mean +- std with 95% CI where a statistics report is attached.

## Main Table

| Suite | Success | Jam | Final Dist (mm) | Mean Peak Force (N) | P95 Force (N) | Contact Steps |
| --- | --- | --- | --- | --- | --- | --- |
| PPO w/o BC | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 18.381 +- 0.336 (95% CI [18.047, 18.645]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) |
| BC-only (stable 32/32) | 1.000 +- 0.001 (95% CI [0.999, 1.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.901 +- 0.008 (95% CI [0.892, 0.907]) | 0.932 +- 0.033 (95% CI [0.903, 0.959]) | 1.234 +- 0.047 (95% CI [1.192, 1.270]) | 29.972 +- 1.137 (95% CI [29.010, 30.934]) |
| Fixed-impedance RL (stable BC 32/32) | 0.947 +- 0.067 (95% CI [0.879, 0.994]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.916 +- 0.030 (95% CI [0.895, 0.945]) | 1.071 +- 0.109 (95% CI [1.002, 1.181]) | 1.417 +- 0.143 (95% CI [1.329, 1.561]) | 36.492 +- 1.243 (95% CI [35.436, 37.508]) |
| BC -> PPO | 1.000 +- 0.000 (95% CI [1.000, 1.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.902 +- 0.007 (95% CI [0.896, 0.908]) | 0.902 +- 0.064 (95% CI [0.858, 0.963]) | 1.192 +- 0.093 (95% CI [1.125, 1.279]) | 29.759 +- 1.473 (95% CI [28.554, 31.133]) |
| DAPG-lite | 1.000 +- 0.000 (95% CI [1.000, 1.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.895 +- 0.003 (95% CI [0.893, 0.897]) | 1.009 +- 0.101 (95% CI [0.919, 1.092]) | 1.339 +- 0.138 (95% CI [1.216, 1.452]) | 29.556 +- 0.990 (95% CI [28.782, 30.471]) |
| DAPG-lite old reset (coverage collapse) | 0.107 +- 0.189 (95% CI [0.000, 0.301]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 2.035 +- 1.084 (95% CI [1.265, 3.139]) | 0.656 +- 0.047 (95% CI [0.609, 0.690]) | 0.888 +- 0.066 (95% CI [0.823, 0.935]) | 19.844 +- 5.981 (95% CI [14.372, 24.311]) |
| DAPG-lite old reset (repaired) | 1.000 +- 0.000 (95% CI [1.000, 1.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.894 +- 0.010 (95% CI [0.885, 0.902]) | 0.995 +- 0.097 (95% CI [0.912, 1.077]) | 1.317 +- 0.128 (95% CI [1.202, 1.424]) | 29.791 +- 0.901 (95% CI [28.952, 30.620]) |
| DAPG-lite new reset (coverage collapse) | 0.183 +- 0.223 (95% CI [0.001, 0.370]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 2.039 +- 1.264 (95% CI [1.146, 3.324]) | 0.636 +- 0.062 (95% CI [0.576, 0.686]) | 0.857 +- 0.087 (95% CI [0.775, 0.927]) | 19.408 +- 6.955 (95% CI [12.697, 24.830]) |
| DAPG-lite new reset (repaired) | 1.000 +- 0.000 (95% CI [1.000, 1.000]) | 0.000 +- 0.000 (95% CI [0.000, 0.000]) | 0.895 +- 0.003 (95% CI [0.893, 0.897]) | 1.009 +- 0.101 (95% CI [0.919, 1.092]) | 1.339 +- 0.138 (95% CI [1.216, 1.453]) | 29.556 +- 0.990 (95% CI [28.782, 30.439]) |

## Handcrafted / Classical Anchors

| Suite | Success | Jam | Final Dist (mm) | Mean Peak Force (N) | P95 Force (N) | Contact Steps |
| --- | --- | --- | --- | --- | --- | --- |
| Pose-only | 1.000 | 0.000 | 0.969 | 1.112 | 1.464 | 11.000 |
| Handcrafted fixed impedance | 1.000 | 0.000 | 0.969 | 2.959 | 3.917 | 11.000 |
| Handcrafted variable impedance | 0.990 | 0.000 | 0.947 | 0.885 | 1.143 | 30.594 |

## Comparison Notes

- Fixed-impedance RL (stable BC 32/32): vs BC -> PPO on success_rate: materially different.
- BC -> PPO: vs BC-only (stable 32/32) on success_rate: negligible under ceiling saturation.
- DAPG-lite: vs BC-only (stable 32/32) on success_rate: negligible under ceiling saturation.

## Annotation

Five nominal eval profiles collapse to three effective pressure classes in this 3DoF environment design.

- `baseline`: nominal, tight_clearance, offset_bias. No extra active pressure under current 3DoF semantics. offset_bias is absorbed by the relative observation coordinate frame; tight_clearance only activates under lateral overflow.
- `high_friction`: high_friction. Force-impedance coupling. higher wall friction changes the contact force response.
- `noisy_force`: noisy_force. Force-sensor uncertainty. force noise perturbs the observed contact signal.
