# PPO-Only Large-Budget Audit Protocol Freeze

## Scope

This document freezes the paper-facing PPO-only large-budget audit used for the 3DoF insertion benchmark.
It is intentionally narrow: it only covers the Appendix B style PPO-only stress test and its regression
contracts, not the full training system.

## Canonical Runner

From the repository root:

```powershell
python scripts/experiments/run_3dof_ppo_large_budget_ablation.py --budgets 200000 --output outputs/three_dof_ppo_large_budget_ablation_200k_repro.json
```

Runner entrypoint:

- File: [run_3dof_ppo_large_budget_ablation.py](F:\edge download\learning\vi-insertion-only-sim\scripts\experiments\run_3dof_ppo_large_budget_ablation.py)
- Entrypoint: `main()`
- Registry source: `build_3dof_ppo_large_budget_ablation_registry()` in [three_dof_benchmark.py](F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_benchmark.py)

## Environment Lock

Canonical environment file:

- [environment.yml](F:\edge download\learning\vi-insertion-only-sim\environment.yml)

Sprint 0 freeze pins:

- `python=3.11`
- `torch==2.7.1`
- `mujoco==3.4.0`
- `gymnasium==1.2.3`
- `stable-baselines3==2.7.1`
- `pytest`
- `gymnasium-robotics`

Any future artifact claim should cite this environment file or an equally explicit lockfile.

## Frozen Evaluation Contract

- Train seeds: `0 1 2 3 4`
- Eval episodes per seed/profile: `100`
- Budgets in scope: `50000`, `100000`, `200000`
- Sprint 0 reproduction target: `200000`
- Profiles:
- `nominal`
- `tight_clearance`
- `high_friction`
- `offset_bias`
- `noisy_force`
- Max episode steps: `64`
- Train profile: `nominal`
- Conditions:
- `ppo_only_paper_matched`
- `ppo_only_reviewer_fair`

## Frozen PPO-Only Conditions

Shared PPO-only auxiliary-stage freeze contract:

- Constant name: `_PPO_ONLY_PROTOCOL_FREEZE_OVERRIDES`
- Defined in: `build_3dof_ppo_large_budget_ablation_registry()` source file [three_dof_benchmark.py](F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_benchmark.py)

Both PPO-only conditions must explicitly disable all auxiliary training stages instead of relying on inherited defaults.

Frozen disabled stage controls:

- `bc_rollout_episodes = 0`
- `bc_pretrain_steps = 0`
- `approach_bc_rollout_episodes = 0`
- `approach_bc_pretrain_steps = 0`
- `contact_bc_rollout_episodes = 0`
- `contact_bc_pretrain_steps = 0`
- `contact_bc_after_finetune = False`
- `contact_finetune_timesteps = 0`
- `contact_finetune_anchor_rollout_episodes = 0`
- `contact_finetune_anchor_bc_steps = 0`
- `contact_finetune_anchor_interval_timesteps = 0`
- `phase_bias_distill_rollout_episodes = 0`
- `phase_bias_distill_pretrain_steps = 0`
- `intent_lift_bc_rollout_episodes = 0`
- `intent_lift_bc_pretrain_steps = 0`
- `intent_lift_bc_after_stabilization = False`
- `stabilization_bc_rollout_episodes = 0`
- `stabilization_bc_pretrain_steps = 0`
- `dapg_enabled = False`

Condition-specific optimizer settings:

| Condition | `n_envs` | `n_steps` | `batch_size` | `n_epochs` | `learning_rate` | `gamma` | `gae_lambda` | `ent_coef` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ppo_only_paper_matched` | 1 | 64 | 64 | 1 | `1e-4` | `0.95` | `0.95` | `0.0` |
| `ppo_only_reviewer_fair` | 4 | 256 | 256 | 4 | `3e-4` | `0.99` | `0.95` | `0.01` |

## Expected 200k Reproduction Signal

Reference artifacts:

- Frozen archive: `artifacts/stress_tests/three_dof_ppo_large_budget_ablation_20260413_full_cpu.json`
- Sprint 0 rerun: `outputs/three_dof_ppo_large_budget_ablation_200k_repro.json`

At `200000` PPO steps, both condition families should stay in the same non-contact regime.

| Condition | Profile | Success | Contact steps | First contact step | Peak force |
| --- | --- | ---: | ---: | ---: | ---: |
| `ppo_only_paper_matched` | `nominal` | 0.0 | 0.0 | 64.0 | 0.0 |
| `ppo_only_paper_matched` | `tight_clearance` | 0.0 | 0.0 | 64.0 | 0.0 |
| `ppo_only_paper_matched` | `high_friction` | 0.0 | 0.0 | 64.0 | 0.0 |
| `ppo_only_paper_matched` | `offset_bias` | 0.0 | 0.0 | 64.0 | 0.0 |
| `ppo_only_paper_matched` | `noisy_force` | 0.0 | 0.0 | 64.0 | 0.0 |
| `ppo_only_reviewer_fair` | `nominal` | 0.0 | 0.0 | 64.0 | 0.0 |
| `ppo_only_reviewer_fair` | `tight_clearance` | 0.0 | 0.0 | 64.0 | 0.0 |
| `ppo_only_reviewer_fair` | `high_friction` | 0.0 | 0.0 | 64.0 | 0.0 |
| `ppo_only_reviewer_fair` | `offset_bias` | 0.0 | 0.0 | 64.0 | 0.0 |
| `ppo_only_reviewer_fair` | `noisy_force` | 0.0 | 0.0 | 64.0 | 0.0 |

This table is the negative-result floor Sprint 0 is meant to preserve.

## Lower-Budget Status

- `50000` and `100000` are part of the frozen audit scope.
- Sprint 0 only reran the `200000` checkpoint because that is the paper-critical negative-result floor.
- `50000` and `100000` floors should be re-confirmed during Sprint 1 cross-family pilot work and then copied into this document if they remain stable.

## Regression Tests

Minimum Sprint 0 guardrails:

- File: [test_three_dof_contract.py](F:\edge download\learning\vi-insertion-only-sim\tests\three_dof\test_three_dof_contract.py)
  Tests:
  `test_blocked_contact_failure_is_separate_reason`,
  `test_blocked_contact_failure_requires_persistence`,
  `test_force_jam_requires_consecutive_violations`,
  `test_force_jam_counter_resets_after_below_threshold_step`
- File: [test_run_3dof_ppo_large_budget_ablation.py](F:\edge download\learning\vi-insertion-only-sim\tests\runners\test_run_3dof_ppo_large_budget_ablation.py)
  Test:
  `test_ppo_only_protocol_disables_all_auxiliary_stages`

## Interpretation Boundary

- This audit does not prove that every PPO variant fails in principle.
- It does freeze the paper-facing claim that, under the matched 3DoF benchmark contract and the reviewer-fair PPO contract, PPO-only remains in a non-contact regime up to `200000` steps.
- Any future change to the runner, registry, training defaults, or expected signal should update both this document and the regression tests in the same commit.

## SCI Quantization Contract

Projected signature fields:

- `||obs_xy||`
- `obs_z`
- `||force||`
- `||action_xy||`
- `action_dz`
- `action_k_xy`
- `action_k_z`

Default widths frozen in `ThreeDoFSupportMetricConfig` (`src/vi_full/three_dof_support_metrics.py`):

- `obs_xy_norm_bin_m = 5e-4`
- `obs_z_bin_m = 5e-4`
- `force_norm_bin_n = 0.25`
- `action_xy_norm_bin = 0.1`
- `action_dz_bin = 0.1`
- `action_k_xy_bin = 0.1`
- `action_k_z_bin = 0.1`

Reviewer-facing rationale:

- The `5e-4` position bins are frozen to resolve sub-millimeter contact-entry structure relative to the benchmark success tolerances `success_lateral_tolerance_m = 0.0008` and `success_axial_tolerance_m = 0.0010` in `src/vi_full/three_dof_config.py`.
- The `0.25` force bin is intentionally coarse relative to the benchmark jam threshold `jam_force_threshold_n = 8.0` in `src/vi_full/three_dof_config.py` and the mirrored paper-facing contract in `src/vi_full/three_dof_contract.py`, while still separating low-force approach from contact.
- The `0.1` action bins are coarse normalized partitions for the explicit motion/stiffness interface `(\Delta x, \Delta y, \Delta z, K_{xy}, K_z)` so SCI does not collapse into near-exact sample matching.

These widths are frozen benchmark-local quantization choices, not a completed sensitivity-optimized SCI calibration.

## Cross-Family Pilot Contract

This section freezes the default Sprint 1 pure-RL pilot contract used to compare PPO, SAC, and TD3 before the
full confirm benchmark.

Canonical runner:

```powershell
python scripts/experiments/run_3dof_cross_family_pilot.py --output outputs/three_dof_cross_family_pilot.json
```

Runner entrypoint:

- File: [run_3dof_cross_family_pilot.py](F:\edge download\learning\vi-insertion-only-sim\scripts\experiments\run_3dof_cross_family_pilot.py)
- Entrypoint: `main()`
- Registry source: `build_3dof_cross_family_pilot_registry()` in [three_dof_cross_family_baselines.py](F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_cross_family_baselines.py)

Frozen default pilot settings:

- Methods:
- `ppo_no_bc`
- `sac_no_bc`
- `td3_no_bc`
- Budgets: `50000`, `100000`, `200000`
- Train seeds: `0 1 2`
- Eval episodes per seed/profile: `50`
- Train profile: `nominal`
- Eval profiles:
- `nominal`
- Max episode steps: `64`

Method-specific default optimizer and replay settings:

| Method | Key settings |
| --- | --- |
| `ppo_no_bc` | `n_envs=4`, `n_steps=256`, `batch_size=256`, `n_epochs=4`, `learning_rate=3e-4`, `gamma=0.99`, `gae_lambda=0.95`, `ent_coef=0.01` |
| `sac_no_bc` | `n_envs=1`, `batch_size=256`, `learning_rate=3e-4`, `gamma=0.99`, `buffer_size=200000`, `learning_starts=1024`, `train_freq=1`, `gradient_steps=1`, `tau=0.005`, `ent_coef=auto` |
| `td3_no_bc` | `n_envs=1`, `batch_size=256`, `learning_rate=3e-4`, `gamma=0.99`, `buffer_size=200000`, `learning_starts=1024`, `train_freq=1`, `gradient_steps=1`, `tau=0.005`, `policy_delay=2`, `target_policy_noise=0.2`, `target_noise_clip=0.5`, `action_noise_std=0.1` |

Rationale for the off-policy freeze:

- `learning_starts=1024` is the current contract value because `max(1000, max_episode_steps * n_envs * 16)` evaluates to `1024` under the default `64`-step, `1`-env pilot setting.
- This warmup avoids claiming poor off-policy sample efficiency under a `learning_starts=0` contract that would force critics to bootstrap from the actor's untrained distribution immediately.
- `buffer_size=200000` matches the largest pilot budget so the replay buffer does not start FIFO-dropping early experience before the maximum planned Sprint 1 run finishes.
- `action_noise_std` is only part of the `td3_no_bc` contract; non-TD3 baselines should not silently accept it.

Scope note:

- The runner now exposes `--train-profile`, but the frozen Sprint 1 default remains `nominal` train and `nominal` eval unless a later protocol update says otherwise.

## Cross-Family Confirm Interpretation Boundary

Sprint 1 full pilot completed: 9/9 chunks.

Selected narrative branch: A.

No pure-RL method reached contact under the frozen 3DoF contract. SAC shows the strongest
terminal-distance proxy but still remains zero-contact.

- This pilot does not prove pure RL can never solve insertion.
- It shows that under the frozen 3DoF nominal-train, nominal-eval, 50k/100k/200k contract, PPO/SAC/TD3 do not enter useful contact.
- Distance-to-contact may be used as a secondary diagnostic proxy, not as a success metric.

Next Sprint 2 direction: the confirm benchmark should compare Branch-A pure-RL failure against
demo-supported anchors, not oversell SAC.

## Sprint 2B Evidence Matrix Boundary

Canonical exporter:

```powershell
python .\scripts\experiments\export_3dof_evidence_matrix.py `
  --confirm-report .\outputs\cross_family_confirm\three_dof_cross_family_confirm_report.json `
  --benchmark-report .\artifacts\main_benchmark\three_dof_benchmark_schema2_paper_teacher_20260418_034230.json `
  --output-dir .\outputs\evidence_matrix
```

Paper-facing artifacts:

- `outputs/evidence_matrix/three_dof_evidence_matrix.json`
- `outputs/evidence_matrix/three_dof_evidence_matrix.csv`
- `outputs/evidence_matrix/three_dof_evidence_matrix.md`
- `outputs/evidence_matrix/three_dof_contact_gate_matrix.png`
- `outputs/evidence_matrix/three_dof_contact_gate_matrix.pdf`

Frozen row roster:

- `ppo_no_bc`
- `sac_no_bc`
- `td3_no_bc`
- `bc_only_stable_r32_p32`
- `repaired_mainline_bc_to_ppo`
- `dapg_lite_repaired_mainline`
- `fixed_impedance_rl_stable_r32_p32`

Frozen interpretation boundary:

- `source_contract` must stay explicit:
  - pure-RL rows use `nominal-only pilot`
  - anchor rows use `five-profile benchmark`
- row-level `source_report` must point to the matrix's direct JSON inputs:
  - pure-RL rows cite the exported confirm report JSON directly
  - anchor rows cite `artifacts/main_benchmark/three_dof_benchmark_schema2_paper_teacher_20260418_034230.json` directly
  - do not infer row provenance from separate stage3 paper-table exports
- Allowed:
  - contact-gate contrast across contracts
  - stating that pure RL stays outside useful contact under the nominal-only pilot
  - stating that demo-supported anchors reopen contact and non-zero success under the five-profile benchmark
  - stating that SAC is the best distance proxy among pure-RL rows without contact entry
- Not allowed:
  - mixed-contract leaderboard ranking
  - claiming SAC solves insertion
  - claiming off-policy pure RL entered useful contact
  - claiming fixed-impedance success makes impedance irrelevant
