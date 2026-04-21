# 3DoF Evidence Matrix

Confirm source: `outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json`
Benchmark source: `artifacts/main_benchmark/three_dof_benchmark_schema2_paper_teacher_20260418_034230.json`

## Mixed-Contract Boundary

- Allowed: Use only for contact-gate contrast across nominal-only pilot and five-profile benchmark evidence.
- Not allowed: Do not read this matrix as a mixed-contract leaderboard or direct across-row ranking.
- Row sources: Each row cites the direct confirm or benchmark JSON input passed to the exporter; do not infer row provenance from separate paper table exports.

## Matrix

| Method | Family | Source contract | Contact? | Success | Final dist (mm) | Contact steps | Role |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| PPO w/o BC | pure_rl | nominal-only pilot | no | 0.00 | 25.48 | 0.00 | contact_gate_negative |
| SAC w/o BC | pure_rl | nominal-only pilot | no | 0.00 | 16.67 | 0.00 | contact_gate_negative |
| TD3 w/o BC | pure_rl | nominal-only pilot | no | 0.00 | 25.56 | 0.00 | contact_gate_negative |
| BC-only (stable 32/32) | imitation_anchor | five-profile benchmark | yes | 1.00 | 0.90 | 29.97 | support_reopens_contact |
| BC -> PPO | demo_augmented_rl | five-profile benchmark | yes | 1.00 | 0.94 | 26.28 | support_reopens_contact |
| DAPG-lite | demo_augmented_rl | five-profile benchmark | yes | 0.60 | 1.17 | 27.55 | support_reopens_contact |
| Fixed-impedance RL (stable BC 32/32) | fixed_impedance | five-profile benchmark | yes | 0.80 | 1.10 | 36.22 | mechanics_anchor |

## Claim Boundary

- `ppo_no_bc` allowed: Pure RL stays outside the useful-contact gate under the nominal-only pilot contract.
- `ppo_no_bc` not allowed: Do not claim this method reaches useful contact or compare it as a mixed-contract leaderboard winner.
- `sac_no_bc` allowed: Best pure-RL distance proxy under the nominal-only pilot contract, but still zero-contact.
- `sac_no_bc` not allowed: Do not claim SAC w/o BC solves insertion, enters useful contact, or wins a mixed-contract leaderboard.
- `td3_no_bc` allowed: Pure RL stays outside the useful-contact gate under the nominal-only pilot contract.
- `td3_no_bc` not allowed: Do not claim this method reaches useful contact or compare it as a mixed-contract leaderboard winner.
- `bc_only_stable_r32_p32` allowed: Demonstration support alone reopens contact and near-ceiling success under the five-profile benchmark.
- `bc_only_stable_r32_p32` not allowed: Do not compare this row as a mixed-contract leaderboard winner against nominal-only pure-RL pilot rows.
- `repaired_mainline_bc_to_ppo` allowed: Demo-supported RL reopens contact and non-zero success under the five-profile benchmark.
- `repaired_mainline_bc_to_ppo` not allowed: Do not compare this row as a mixed-contract leaderboard winner against nominal-only pure-RL pilot rows.
- `dapg_lite_repaired_mainline` allowed: Demo-supported RL reopens contact and non-zero success under the five-profile benchmark.
- `dapg_lite_repaired_mainline` not allowed: Do not compare this row as a mixed-contract leaderboard winner against nominal-only pure-RL pilot rows.
- `fixed_impedance_rl_stable_r32_p32` allowed: Fixed impedance still enters contact and succeeds under support, so this row acts as a mechanics anchor.
- `fixed_impedance_rl_stable_r32_p32` not allowed: Do not read this row as proof that impedance type alone determines learnability or as a mixed-contract leaderboard winner.
