# 3DoF Appendix Benchmark Tables

Benchmark source: `artifacts/main_benchmark/three_dof_benchmark_schema2_paper_teacher_20260418_034230.json`

## Teacher Ablation

| Suite | teacher_motion_rule | teacher_impedance_rule | success_rate | jam_rate | mean_final_distance_mm | mean_peak_contact_force_n | mean_contact_steps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Teacher: variable motion + variable impedance (`teacher_variable_variable__repaired_mainline`) | contact_aware_variable_motion | contact_aware_variable_impedance | 1.000 | 0.000 | 0.941 | 0.680 | 26.282 |
| Teacher: variable motion + fixed impedance (`teacher_variable_fixed__repaired_mainline`) | contact_aware_variable_motion | fixed | 0.000 | 0.000 | 7.519 | 0.314 | 1.995 |
| Teacher: pose motion + variable impedance (`teacher_pose_variable__repaired_mainline`) | pose_feedback | contact_aware_variable_impedance | 1.000 | 0.000 | 0.832 | 1.893 | 8.000 |
| Teacher: pose motion + fixed impedance (`teacher_pose_fixed__repaired_mainline`) | pose_feedback | fixed | 0.200 | 0.000 | 3.554 | 1.022 | 19.013 |

### Teacher Per-Profile Readout

#### Teacher: variable motion + variable impedance (`teacher_variable_variable__repaired_mainline`)

| Profile | success_rate | jam_rate | mean_final_distance_mm | mean_peak_contact_force_n | mean_contact_steps |
| --- | --- | --- | --- | --- | --- |
| nominal | 1.000 | 0.000 | 0.938 | 0.580 | 26.262 |
| tight_clearance | 1.000 | 0.000 | 0.937 | 0.562 | 26.244 |
| high_friction | 1.000 | 0.000 | 0.954 | 0.904 | 26.524 |
| offset_bias | 1.000 | 0.000 | 0.937 | 0.570 | 26.154 |
| noisy_force | 1.000 | 0.000 | 0.938 | 0.785 | 26.226 |

#### Teacher: variable motion + fixed impedance (`teacher_variable_fixed__repaired_mainline`)

| Profile | success_rate | jam_rate | mean_final_distance_mm | mean_peak_contact_force_n | mean_contact_steps |
| --- | --- | --- | --- | --- | --- |
| nominal | 0.000 | 0.000 | 7.518 | 0.292 | 1.998 |
| tight_clearance | 0.000 | 0.000 | 7.521 | 0.301 | 1.994 |
| high_friction | 0.000 | 0.000 | 7.519 | 0.314 | 2.000 |
| offset_bias | 0.000 | 0.000 | 7.518 | 0.299 | 1.986 |
| noisy_force | 0.000 | 0.000 | 7.518 | 0.364 | 1.996 |

#### Teacher: pose motion + variable impedance (`teacher_pose_variable__repaired_mainline`)

| Profile | success_rate | jam_rate | mean_final_distance_mm | mean_peak_contact_force_n | mean_contact_steps |
| --- | --- | --- | --- | --- | --- |
| nominal | 1.000 | 0.000 | 0.830 | 1.667 | 8.000 |
| tight_clearance | 1.000 | 0.000 | 0.830 | 1.609 | 8.000 |
| high_friction | 1.000 | 0.000 | 0.841 | 2.856 | 8.000 |
| offset_bias | 1.000 | 0.000 | 0.830 | 1.631 | 8.000 |
| noisy_force | 1.000 | 0.000 | 0.830 | 1.703 | 8.000 |

#### Teacher: pose motion + fixed impedance (`teacher_pose_fixed__repaired_mainline`)

| Profile | success_rate | jam_rate | mean_final_distance_mm | mean_peak_contact_force_n | mean_contact_steps |
| --- | --- | --- | --- | --- | --- |
| nominal | 0.200 | 0.000 | 3.553 | 0.874 | 18.954 |
| tight_clearance | 0.200 | 0.000 | 3.555 | 1.066 | 18.940 |
| high_friction | 0.200 | 0.000 | 3.556 | 1.230 | 19.140 |
| offset_bias | 0.200 | 0.000 | 3.553 | 0.929 | 18.898 |
| noisy_force | 0.200 | 0.000 | 3.553 | 1.011 | 19.134 |

## Termination Diagnostics

| Suite | jam_rate | force_threshold_termination_rate | blocked_contact_termination_rate | force_threshold_only_termination_rate | blocked_contact_only_termination_rate | force_and_blocked_termination_rate | documented_force_jam_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BC-only (stable 32/32) | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| BC -> PPO | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| DAPG-lite | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| Fixed-impedance RL (stable BC 32/32) | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
