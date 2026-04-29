# 3DoF Evidence Matrix

Confirm source: `outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json`
Manifest source: `artifacts/main_benchmark/main_benchmark_manifest.json`
Benchmark source: `artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage4_20260429.json`

## Mixed-Contract Boundary

- Allowed: Use only for contact-gate contrast across nominal-only pilot and five-profile benchmark evidence.
- Not allowed: Do not read this matrix as a mixed-contract leaderboard or direct across-row ranking.
- Row sources: Each row cites the direct confirm or benchmark JSON input passed to the exporter; do not infer row provenance from separate paper table exports.

## Matrix

| Method | Family | Source contract | Train budget | Source report | Contact? | Success | Final dist (mm) | Contact steps | Role |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| PPO w/o BC | pure_rl | nominal-only pilot | 200000 | outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json | no | 0.000 | 25.482 | 0.000 | contact_gate_negative |
| SAC w/o BC | pure_rl | nominal-only pilot | 200000 | outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json | no | 0.000 | 16.674 | 0.000 | contact_gate_negative |
| TD3 w/o BC | pure_rl | nominal-only pilot | 200000 | outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json | no | 0.000 | 25.556 | 0.000 | contact_gate_negative |
| BC-only (stable 32/32) | imitation_anchor | five-profile benchmark | BC 32/32 | artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage4_20260429.json | yes | 1.000 | 0.899 | 28.940 | support_reopens_contact |
| BC -> PPO | demo_augmented_rl | five-profile benchmark | BC 32/32 + PPO 128 | artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage4_20260429.json | yes | 0.838 | 0.980 | 24.886 | support_reopens_contact |
| DAPG-lite | demo_augmented_rl | five-profile benchmark | BC 32/32 + DAPG-lite 128 | artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage4_20260429.json | yes | 0.853 | 1.020 | 24.712 | support_reopens_contact |
| Fixed-impedance RL (stable BC 32/32) | fixed_impedance | five-profile benchmark | BC 32/32 + PPO 128 | artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage4_20260429.json | yes | 0.884 | 0.994 | 30.198 | mechanics_anchor |

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
