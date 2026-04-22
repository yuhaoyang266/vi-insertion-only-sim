# Sprint 2 Main Table

Confirm source: `outputs/cross_family_confirm/three_dof_cross_family_confirm_report.json`
Evidence-matrix source: `outputs/evidence_matrix/three_dof_evidence_matrix.json`
Benchmark source: `artifacts/main_benchmark/three_dof_benchmark_schema2_paper_teacher_20260418_034230.json`

## Boundary

- Allowed: Use only for contact-gate contrast across nominal-only pilot and five-profile benchmark evidence.
- Not allowed: Do not read this matrix as a mixed-contract leaderboard or direct across-row ranking.
- Main-table reading: three evidence layers, not a leaderboard.

## Pure-RL nominal-only negative rows

Pure-RL rows from the nominal-only Branch-A confirm contract; these rows stay outside useful contact.

| Method | Source contract | Train budget | Contact? | Success | Final dist (mm) | Contact steps | Role | Claim boundary |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| PPO w/o BC | nominal-only pilot | 200000 | no | 0.00 | 25.48 | 0.00 | contact_gate_negative | Pure RL stays outside the useful-contact gate under the nominal-only pilot contract. |
| SAC w/o BC | nominal-only pilot | 200000 | no | 0.00 | 16.67 | 0.00 | contact_gate_negative | Best pure-RL distance proxy under the nominal-only pilot contract, but still zero-contact. |
| TD3 w/o BC | nominal-only pilot | 200000 | no | 0.00 | 25.56 | 0.00 | contact_gate_negative | Pure RL stays outside the useful-contact gate under the nominal-only pilot contract. |

## Demo-supported contact-reopening rows

Five-profile benchmark rows showing that demonstration support reopens contact and non-zero success.

| Method | Source contract | Train budget | Contact? | Success | Final dist (mm) | Contact steps | Role | Claim boundary |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| BC-only (stable 32/32) | five-profile benchmark | BC 32/32 | yes | 1.00 | 0.90 | 29.97 | support_reopens_contact | Demonstration support alone reopens contact and near-ceiling success under the five-profile benchmark. |
| BC -> PPO | five-profile benchmark | BC 32/32 + PPO 128 | yes | 1.00 | 0.94 | 26.28 | support_reopens_contact | Demo-supported RL reopens contact and non-zero success under the five-profile benchmark. |
| DAPG-lite | five-profile benchmark | BC 32/32 + DAPG-lite 128 | yes | 0.60 | 1.17 | 27.55 | support_reopens_contact | Demo-supported RL reopens contact and non-zero success under the five-profile benchmark. |

## Mechanics / fixed-impedance anchor rows

Five-profile fixed-impedance row retained as a mechanics anchor, not as a leaderboard entry.

| Method | Source contract | Train budget | Contact? | Success | Final dist (mm) | Contact steps | Role | Claim boundary |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |
| Fixed-impedance RL (stable BC 32/32) | five-profile benchmark | BC 32/32 + PPO 128 | yes | 0.80 | 1.10 | 36.22 | mechanics_anchor | Fixed impedance still enters contact and succeeds under support, so this row acts as a mechanics anchor. |
