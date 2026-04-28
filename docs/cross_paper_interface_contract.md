# Cross-Paper Interface Contract (Paper-A <-> Paper-B)

**Status:** Active draft (2026-04-28). Mirror copy lives in the Paper-B repository at the same relative path. **Both copies must stay byte-identical.** When this contract changes, update the SHA pin in `src/vi_full/cross_paper_bridge.py` (Paper-A) and `src/variable_impedance/safety_layer/cross_paper.py` (Paper-B) atomically.

## 0. Parties

| Tag | Repository | Working title | Primary venue target |
| --- | --- | --- | --- |
| **Paper-A** | `vi-insertion-only-sim` | *Support-Gated Learnability and Variable-Impedance Load Paths in a 3DoF Insertion Benchmark* | Robotica / Adv. Robotics (Tier-3); RAL / T-Mech (Tier-2 stretch) |
| **Paper-B** | `research-cartesian-impedance-vla-sim` | *A Contact-State-Aware Adaptive Impedance Safety Layer for Force-Bounded Contact-Rich Precision Assembly* | IEEE RA-L (primary, 2026-11-15); T-Mech / RAS / Mechatronics (fallback) |

## 1. Scope of This Contract

This document is the **only** interface point between Paper-A and Paper-B. It pins:

1. The action schema mapping that lets a Paper-A learned policy drive Paper-B's environment.
2. The observation projection that lets a Paper-A policy receive a Paper-A-shaped observation from Paper-B's MuJoCo state.
3. The success / jam / horizon / metric definitions used in both papers' cross-cited tables.
4. The 5-profile evaluation suite and its per-profile parameters.
5. The demo dataset format used by both papers' learned baselines.
6. The version-pinning protocol: every cross-paper artifact records the exact commit hash and contract SHA used.

**Out of scope of this contract:**

- Paper-A's SG-VI / SCI claims, contributions, or main-table contents. Paper-B does not re-derive these.
- Paper-B's safety-layer construction, force-envelope theorem, or directional-K mechanics. Paper-A does not re-derive these.
- Either paper's standalone abstract, introduction, related work, or conclusion.
- Hardware. Both papers are simulation-only on this contract.

## 2. Action Schema (Paper-A 5D <-> Paper-B Schema-P)

**Paper-A learned policies output:**

```text
a_A = [Δx, Δy, Δz, κ_xy, κ_z]  ∈ ℝ^5
       └── Cartesian motion ──┘ └ stiffness ┘
```

with `Δx, Δy, Δz ∈ [-1, 1]` and `κ_xy, κ_z ∈ [0, 1]` per Paper-A `src/vi_full/three_dof_env.py`.

**Paper-B Schema-P upstream interface accepts:**

```text
a_up^P = Δx ∈ ℝ^5    (translation + lateral/axial stiffness mode)
```

per Paper-B `docs/SECTION3_METHOD.md` § 3.1.

**Mapping (Paper-A -> Paper-B):**

```text
Δx_paper_b[0:3]  = Δx_paper_a[0:3]              (translation, identity)
Δx_paper_b[3]    = κ_xy_paper_a                  (lateral stiffness mode)
Δx_paper_b[4]    = κ_z_paper_a                   (axial stiffness mode)
dyaw             = 0  (FORCED)                   (Paper-A is translation-only)
```

The Paper-B contact-frame estimator and directional-K decomposition treat `dyaw=0` as a Schema-P contract; this is acceptable for Paper-B's cylindrical peg-in-hole and chamfered-hole tasks (square / slot variants are deferred in Paper-B per its scope statement).

**Stiffness decoding inside Paper-B:** Paper-B's MuJoCo environment converts `(κ_xy, κ_z)` into the same `K_xy ∈ [20, 110]` and `K_z ∈ [35, 140]` ranges used by Paper-A `src/vi_full/three_dof_config.py`. If Paper-B's safety layer overrides stiffness, that override happens **after** the upstream policy decode; this preserves the Paper-A interface while exercising Paper-B's directional-K logic.

## 3. Observation Projection (Paper-B MuJoCo state -> Paper-A 14D observation)

**Paper-A observation:**

```text
o_A = [p_xy_rel ∈ ℝ^2,  p_z_rel ∈ ℝ,  v_rel ∈ ℝ^3,  f ∈ ℝ^3,  a_{t-1} ∈ ℝ^5]   total 14
```

per Paper-A § 2.2 / `three_dof_env.py::_get_observation`.

**Paper-B exposes** in `peg_in_hole.py`: 7-DoF Panda joint state, `RobotState` (ee_pos, ee_quat, ee_twist, J), and a 6D wrench sample from `ContactWrenchSample` summed in the world frame.

**Projection (Paper-B -> Paper-A):**

```text
hole_frame_origin   = peg-in-hole task target site (Paper-B `peg_in_hole.py` exposes this)
p_rel               = ee_pos - hole_frame_origin                  (3D)
v_rel               = ee_linear_twist                              (3D, world frame)
f_xyz               = wrench_sample.wrench[0:3]                    (3D linear force, world frame)
a_{t-1}             = previous Schema-P action (5D), stored on the bridge
```

Yaw, roll, pitch components and torque components of the Paper-B wrench are **dropped** by this projection. The bridge MUST log dropped torque magnitude per step; if mean dropped-torque exceeds `0.1 N·m` over an episode, mark the episode as "out-of-Paper-A-scope" and exclude from cross-sim ranking. This guard prevents Paper-A policies from being scored on episodes whose dynamics fall outside Paper-A's 3DoF assumption.

## 4. Success, Jam, Horizon, Metrics

| Quantity | Definition | Source of truth |
| --- | --- | --- |
| Success | `‖p_rel_xy‖ ≤ 0.8 mm AND |p_rel_z| ≤ 1.0 mm AND ‖v_rel‖ ≤ 0.08 m/s` | Paper-A § 2.2 |
| Jam | `‖f‖ ≥ 8.0 N` for 3 consecutive steps | Paper-A § 2.2 |
| Episode horizon | 64 control steps | Paper-A § 2.2 |
| Control rate | 50 ms / step (Paper-B's upstream-layer rate) | Paper-B § 4.1.1 |
| Success rate | mean over episodes | both |
| Mean peak contact force | episode-max `‖f‖` averaged over episodes | both |
| Impulse | `∫ ‖f‖ dt` over episode | Paper-B; appendix-only in Paper-A |
| Mean contact steps | count of steps with `‖f‖ ≥ 0.05 N` | Paper-A § benchmark |

The cross-sim ranking table reports **success** and **mean peak contact force** as primary, **mean contact steps** and **jam rate** as secondary. Paper-B's safety-layer envelope-bound metric `ρ_m` is not part of this contract; Paper-B reports it independently.

## 5. Five-Profile Evaluation Suite

Both papers run the cross-sim ranking on the same 5 profiles (Paper-A § 2.5 nominal profiles):

| Profile | Variation axis | Range / value |
| --- | --- | --- |
| `nominal` | none (reference) | clearance 0.70-1.10 mm, μ_wall 0.25, force_noise σ=0.0 N |
| `tight_clearance` | clearance | 0.45-0.75 mm |
| `high_friction` | wall friction | μ_wall 0.55 |
| `offset_bias` | hole offset | hidden hole offset up to 1.5 mm (relative-frame attenuated) |
| `noisy_force` | force-sensor noise | σ = 0.4 N additive on `f` |

**Paper-B-side note:** Paper-B's MuJoCo environment must implement these 5 profiles using the same parameter values; per-profile overrides go into `configs/cross_paper_eval.yaml` (new file in Paper-B). The Paper-B physical contact model may produce different absolute force magnitudes than Paper-A's analytical model — this is expected and is exactly what the cross-sim ranking-stability table measures.

## 6. Demo Dataset Format

Paper-A's BC demonstrations (`bc_rollout_episodes = 32`, `bc_pretrain_steps = 32`) are the canonical demo source. Format:

```python
demo_record = {
    "observations": np.ndarray,      # (T, 14) float32, per § 3
    "actions": np.ndarray,           # (T, 5)  float32, per § 2
    "rewards": np.ndarray,           # (T,)    float32, optional
    "success": bool,
    "profile": str,                  # one of the 5 profiles
    "teacher_spec": dict,            # serialized ThreeDoFTeacherSpec
    "seed": int,
}
```

Paper-B's HybridIL-lite (Schema-PW) does NOT consume Paper-A demos directly because Paper-A demos lack wrench traces. Paper-B's IQL/CQL or any Schema-P offline-RL **does** consume Paper-A demos directly.

## 7. Version Pinning Protocol

Each cross-paper artifact records:

```yaml
contract_sha:        <SHA-256 of this markdown file at the time of the run>
paper_a_commit:      <git commit hash of vi-insertion-only-sim>
paper_b_commit:      <git commit hash of research-cartesian-impedance-vla-sim>
paper_a_policy_artifact: artifacts/main_benchmark/three_dof_benchmark_paper9suite_full5profile_bc32x32_stage3_20260412.json
paper_b_env_config:  configs/cross_paper_eval.yaml@<commit>
mapping_dyaw:        0  (forced; see § 2)
torque_drop_guard_n_m: 0.1  (see § 3)
```

`src/vi_full/cross_paper_bridge.py` (Paper-A) and `src/variable_impedance/safety_layer/cross_paper.py` (Paper-B) each contain a `CONTRACT_SHA` constant. At bridge load time, both refuse to run if the constant disagrees with the SHA computed from this markdown file. This guarantees Paper-A's cross-sim numbers and Paper-B's RQ7 numbers are reproduced against the same pinned contract.

## 8. Reproduction Command Templates

### From Paper-A repo (drives Paper-B as cross-sim)

```bash
python scripts/experiments/run_cross_sim_via_paper_b.py \
    --paper-b-repo-path <path-to-paper-b-checkout> \
    --paper-b-commit <pinned-commit> \
    --profiles nominal tight_clearance high_friction offset_bias noisy_force \
    --seeds 0 1 2 3 4 \
    --episodes-per-seed 100 \
    --output outputs/cross_sim/three_dof_cross_sim_ranking_paper_b_<date>.json
```

### From Paper-B repo (consumes Paper-A learned policy as U6 upstream)

```bash
python -m variable_impedance.experiments.safety_layer_eval \
    --upstream sg_vi_paper_a \
    --paper-a-policy-artifact <path-to-paper-a-stage3-json> \
    --tasks peg_in_hole chamfered \
    --layer-on-off both \
    --seeds 0..49 \
    --output reports/cross_paper_u6_<date>/
```

## 9. Boundary Statements For Each Manuscript

To avoid double-claiming, each paper must include a Related-Work paragraph that cross-cites the other and states:

**In Paper-A (Section 5 cross-sim block):**

> "Cross-simulator stability is established by running the five learned suites of this paper against the MuJoCo physics environment of the companion work [Paper-B]. The mapping is fixed by `docs/cross_paper_interface_contract.md` and is restricted to translational Schema-P policies. The companion work is independent and is not assessed here for its own contributions, which concern a force-bounded safety layer that is orthogonal to our learnability claim."

**In Paper-B (Section 4.6 RQ7 block):**

> "We additionally evaluate compositionality with a cross-cited Schema-P upstream from [Paper-A], the SG-VI BC->PPO policy. The policy is consumed as a frozen learned upstream via `docs/cross_paper_interface_contract.md`; we do not re-establish [Paper-A]'s support-gate or learnability claims, which are orthogonal to the safety-layer mechanism studied here."

These two boundary paragraphs are the only place where the papers explicitly reference each other in their main manuscripts.

## 10. Update and Conflict Resolution

- Either repo can propose a contract change. The change is committed atomically to both repos with the same SHA and the same date stamp at the top of this file.
- Conflicts (Paper-B physics rejects a Paper-A profile parameter, Paper-A scope shifts to non-translational, etc.) are resolved by Paper-A and Paper-B owner agreement and recorded in `docs/project/progress.md` (Paper-A) and an equivalent log in Paper-B.
- If either paper is desk-rejected and pivots venue, the contract continues to apply unless explicitly retired in writing in this section.

---

**Last updated:** 2026-04-28. Contract SHA: `<computed-on-write>`.
