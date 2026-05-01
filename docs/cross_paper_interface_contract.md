# Cross-Paper Interface Contract

Status: active Sprint C draft, 2026-05-01.

This contract defines the only supported interface between Paper-A (`vi-insertion-only-sim`) and the planned Paper-B repository (`research-cartesian-impedance-vla-sim`). Paper-A owns the support-gated 3DoF benchmark. Paper-B owns the MuJoCo Cartesian impedance and safety-layer environment. Cross-paper artifacts must record the contract SHA, Paper-A commit, distinct Paper-B commit roles when available, and the exact runner command.

## 1. Scope

The contract pins:

- Paper-A action to Paper-B Schema-P action mapping.
- Paper-B state to Paper-A observation projection.
- Shared success, jam, contact, horizon, and ranking metrics.
- The five-profile evaluation suite.
- Demonstration dataset schema for offline or imitation baselines.
- Version-pinning and refusal behavior.

The contract does not promote SCI beyond Paper-A's benchmark-local diagnostic boundary. It also does not claim hardware validity; both papers use this interface for simulation-only evidence.

## 2. Action Schema

Paper-A policies output a 5D action:

```text
a_A = [dx, dy, dz, k_xy, k_z]
```

Where:

- `dx`, `dy`, `dz` are normalized Cartesian commands in `[-1, 1]`.
- `k_xy` and `k_z` are normalized stiffness commands in `[0, 1]`.
- Paper-A decodes `dx` and `dy` with `step_scale_xy_m = 0.0012`.
- Paper-A decodes `dz` with `step_scale_z_m = 0.0010`.
- Paper-A decodes `k_xy` to `[20.0, 110.0]` N/m.
- Paper-A decodes `k_z` to `[35.0, 140.0]` N/m.

Paper-B Schema-P must accept the same upstream 5D vector:

```text
a_B = [dx, dy, dz, k_xy, k_z]
```

Mapping from Paper-A to Paper-B is identity for these five fields. Paper-A has no yaw command, so Paper-B must set `dyaw = 0.0` before any internal safety-layer or contact-frame processing. If Paper-B internally overrides stiffness for safety-layer evaluation, the artifact must record both the upstream stiffness command and the post-layer stiffness.

Invalid actions:

- Wrong shape is an error.
- Non-finite values are an error.
- Finite out-of-range values are clipped to the Paper-A action bounds before dispatch, matching `ThreeDoFInsertionEnv.step`.

## 3. Observation Projection

Paper-A observations are 14D:

```text
o_A = [p_rel_x, p_rel_y, p_rel_z,
       v_x, v_y, v_z,
       f_x, f_y, f_z,
       prev_dx, prev_dy, prev_dz, prev_k_xy, prev_k_z]
```

Paper-B must project its simulator state into this shape:

- `p_rel`: end-effector position minus the active hole or target-frame origin, in meters.
- `v`: end-effector linear velocity in meters per second.
- `f`: world-frame contact force in newtons. If Paper-B reports a 6D wrench, use the force components and log the dropped torque norm.
- `prev_action`: previous clipped Schema-P action after Paper-A bounds handling.

If Paper-B does not expose linear velocity directly, the bridge may use finite differences from consecutive `p_rel` values. The artifact must record the timestep used for that approximation. If dropped torque has episode mean greater than `0.1 N*m`, mark the episode `out_of_paper_a_scope = true` and exclude it from primary ranking rows.

## 4. Shared Metrics

Shared metric definitions:

| Name | Definition |
| --- | --- |
| `success` | Lateral error <= `0.0008` m, axial error <= `0.0010` m, and speed <= `0.08` m/s. |
| `force_jam` | Force norm >= `8.0` N for `3` consecutive steps. |
| `blocked_contact` | Paper-A-style blocked contact failure for `3` consecutive steps. |
| `jam` | `force_jam OR blocked_contact`. |
| `horizon` | `64` control steps for paper-facing benchmark runs. |
| `contact_entry` | First step where force norm >= `0.05` N. |
| `final_distance` | Final Euclidean distance to the contact target, in meters. |
| `peak_force` | Episode maximum force norm, in newtons. |
| `contact_work` | Sum of positive contact work increments over the episode. |
| `contact_impulse` | Sum of force norm times timestep over the episode. |

Ranking artifacts must report at least:

- `success_rate`
- `jam_rate`
- `documented_force_jam_rate`
- `blocked_contact_termination_rate`
- `mean_final_distance`
- `mean_peak_contact_force`
- `p95_peak_contact_force`
- `mean_contact_steps`
- `mean_contact_work`

## 5. Five-Profile Suite

The default suite is exactly:

```text
nominal
tight_clearance
high_friction
offset_bias
noisy_force
```

Paper-A profile parameters are:

| Profile | Parameters |
| --- | --- |
| `nominal` | `clearance_range_m = [0.00070, 0.00110]`, `hole_xy_offset_range_m = 0.0010`, `wall_friction_range = [0.12, 0.32]`, `force_noise_std_range = [0.02, 0.12]`. |
| `tight_clearance` | `clearance_range_m = [0.00045, 0.00075]`, `hole_xy_offset_range_m = 0.0011`; other values inherit `nominal`. |
| `high_friction` | `wall_friction_range = [0.28, 0.46]`, `force_noise_std_range = [0.03, 0.10]`; other values inherit `nominal`. |
| `offset_bias` | `hole_xy_offset_range_m = 0.0018`, `clearance_range_m = [0.00065, 0.00100]`; other values inherit `nominal`. |
| `noisy_force` | `force_noise_std_range = [0.12, 0.25]`, `wall_friction_range = [0.15, 0.30]`; other values inherit `nominal`. |

Paper-B may map these parameters to its own simulator fields, but it must record the mapped values and any non-equivalent contact-law differences in the run artifact.

## 6. Demonstration Dataset Schema

Demo datasets exchanged under this contract use one record per episode:

```python
{
    "observations": float32[T, 14],
    "actions": float32[T, 5],
    "rewards": float32[T],
    "episode_id": str,
    "profile": str,
    "seed": int,
    "success": bool,
    "termination_reason": str,
    "source_policy": str,
    "paper_a_commit": str,
    "contract_sha": str,
}
```

Arrays must be step-aligned: `observations[t]` is the observation consumed before dispatching `actions[t]`. Profile names must be one of the five names in Section 5. Extra provenance keys are allowed; missing required keys are errors.

## 7. Policy Suite Names

Cross-sim bridge smoke and ranking runs use these Paper-A suite names unless a run explicitly narrows scope:

- `ppo_no_bc`
- `bc_only_stable_r32_p32`
- `fixed_impedance_rl_stable_r32_p32`
- `repaired_mainline_bc_to_ppo`
- `dapg_lite_repaired_mainline`

The bridge may expose placeholders for unavailable policy artifacts, but ranking artifacts must distinguish `not_available`, `skipped`, `failed`, and `completed`.

## 8. Version Pinning

Every cross-paper artifact must include:

```yaml
contract_sha: <sha256 of docs/cross_paper_interface_contract.md>
paper_a_commit: <git commit of vi-insertion-only-sim>
paper_b_checkout_commit: <actual Paper-B checkout commit used for the artifact, or deferred>
paper_b_verified_env_commit: <Paper-B commit where readiness/environment checks passed, or deferred>
paper_b_contract_mirror_commit: <Paper-B commit that mirrors this contract and SHA pin, or deferred>
paper_a_policy_artifact: <path or not_available>
paper_b_env_config: <path or not_available>
mapping_dyaw: 0.0
torque_drop_guard_n_m: 0.1
```

Paper-A stores its SHA pin in `src/vi_full/cross_paper_bridge.py` as `CONTRACT_SHA`. Paper-B must store the same value in its bridge copy when that repository is available. Bridge code must refuse to run when the computed contract SHA does not match the pinned value.

Current synchronized readiness baseline:

- `paper_b_verified_env_commit`: `3eb8408`; this is the Paper-B checkout where contract, readiness, peg-in-hole, contact-wrench, and safety-layer checks were recorded.
- `paper_b_contract_mirror_commit`: the Paper-B checkout that mirrors this contract and SHA pin; record the exact commit in each artifact.
- `paper_b_checkout_commit`: the actual Paper-B checkout used by the artifact runner; `scripts/experiments/run_cross_sim_via_paper_b.py` verifies `--paper-b-commit` against this checkout before writing artifacts.
- Verification evidence: Paper-B contract, readiness, peg-in-hole, contact-wrench, and safety-layer checks are recorded in Paper-A `docs/project/progress.md` on 2026-05-01.

## 9. Reproduction Templates

Current dry-run smoke command:

```bash
python scripts/experiments/run_cross_sim_via_paper_b.py \
  --paper-b-repo-path <path-to-paper-b-checkout> \
  --paper-b-commit <actual-paper-b-checkout-commit> \
  --profiles nominal \
  --seeds 0 \
  --episodes-per-seed 5 \
  --suites repaired_mainline_bc_to_ppo bc_only_stable_r32_p32 \
  --dry-run \
  --output outputs/cross_sim/three_dof_cross_sim_ranking_paper_b_smoke_20260501.json
```

Future full-physics command, after Paper-A policy artifact loading and Paper-B physics execution are implemented:

```bash
python scripts/experiments/run_cross_sim_via_paper_b.py \
  --paper-b-repo-path <path-to-paper-b-checkout> \
  --paper-b-commit <actual-paper-b-checkout-commit> \
  --profiles nominal tight_clearance high_friction offset_bias noisy_force \
  --seeds 0 1 2 3 4 \
  --episodes-per-seed 100 \
  --output outputs/cross_sim/three_dof_cross_sim_ranking_paper_b_<date>.json
```

Paper-A fallback if Paper-B is blocked:

```bash
python scripts/experiments/run_3dof_contact_parameter_sensitivity.py \
  --profiles nominal tight_clearance high_friction offset_bias noisy_force \
  --seeds 0 1 2 \
  --output outputs/revision/contact_parameter_sensitivity_<date>.json
```

## 10. Boundary Text

Paper-A may state that cross-simulator stability is evaluated by running its learned 3DoF suites through a separately pinned Paper-B simulator path. Paper-A must not claim Paper-B's safety-layer contribution.

Paper-B may state that it consumes a frozen Paper-A upstream policy via this contract. Paper-B must not re-establish Paper-A's support-gate or learnability claims.

## 11. Change Control

Contract changes require:

1. Updating this markdown file.
2. Updating the Paper-A `CONTRACT_SHA` pin.
3. Mirroring the same markdown bytes and SHA pin to Paper-B when Paper-B is available.
4. Recording the decision in `docs/project/progress.md`.

If Paper-B is unavailable or not parity-ready, Paper-A records that status and continues through the documented fallback path instead of weakening this contract.
