# Sprint 3 Teacher Mini-Ablation Kickoff

Boundary: teacher support quality x demo rollout budget.

Target question: Does support-rich teacher demonstration reopen the contact gate, and does that directional claim survive a reduced demo rollout budget?

## Condition Matrix

| Condition | Teacher preset | Support quality | Demo budget | BC rollouts | BC steps | PPO steps |
| --- | --- | --- | --- | --- | --- | --- |
| support_rich_many_demo | teacher_variable_variable | support_rich | many_demo | 32 | 32 | 128 |
| support_rich_few_demo | teacher_variable_variable | support_rich | few_demo | 8 | 32 | 128 |
| support_poor_many_demo | teacher_pose_fixed | support_poor | many_demo | 32 | 32 | 128 |
| support_poor_few_demo | teacher_pose_fixed | support_poor | few_demo | 8 | 32 | 128 |

## Fixed Metrics

`success_rate`, `mean_final_distance_mm`, `mean_contact_steps`, `jam_rate`, `mean_peak_contact_force_n`, `support_coverage_index`, `support_cell_coverage`

## Frozen Controls

- BC pretrain steps: `32`
- BC batch size: `64`
- PPO fine-tune steps: `128`
- Policy init: `bc_to_ppo_from_scratch`
- Profiles: `nominal`, `tight_clearance`, `high_friction`, `offset_bias`, `noisy_force`

## Closure Criteria

- artifact reproducible
- table/plot claim boundary explicit
- contract tests required
- paper-facing text must not overclaim

## Claim Boundary

Allowed:
- directional teacher-coupling evidence under the fixed 3DoF benchmark contract
- contact-gate contrast between support-rich and support-poor teacher demonstrations
- demo-budget sensitivity within the frozen BC-to-PPO initialization path

Not allowed:
- teacher-independent causal claim
- general robotics or sim-to-real claim
- cross-contract leaderboard
- claim that training completion alone closes Sprint 3

This is not a leaderboard; it is a small teacher-coupled contact-gate check.
