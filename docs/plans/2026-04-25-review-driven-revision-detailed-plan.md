# Review-Driven Revision Detailed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current review-driven revision strategy into an executable, testable, evidence-first implementation plan for rebuilding the manuscript around support, motion, and impedance causal factors.

**Architecture:** Split the revision into five evidence blocks: response matrix, teacher/motion/impedance causal ablations, SCI validation, high-friction mechanics, and manuscript/package rebuild. Reuse existing `vi_full` 3DoF teacher presets, training configuration, support metrics, classical controllers, benchmark traces, and paper export infrastructure. Add focused modules only where the current code cannot produce the reviewer-facing evidence.

**Tech Stack:** Python, NumPy, Matplotlib, pytest, existing `vi_full` 3DoF benchmark/training modules, LaTeX manuscript in `paper/main.tex`, markdown documentation under `docs/`.

---

## Non-Negotiable Revision Spine

Do not implement this as a pile of reviewer-response patches. The revised paper must read as one causal study:

```text
We study contact-rich insertion not as an algorithm leaderboard, but as a support-gated learnability problem. Demonstration support controls contact entry; SCI audits whether rollouts remain in demonstration-supported contact-relevant regions; and variable impedance contributes primarily through lower-load contact paths once support, motion prior, and impedance prior are separated.
```

Paper-level claims to preserve only if the planned evidence supports them:

1. **Learnability gate:** demonstration support enables recoverable contact in the reduced 3DoF benchmark.
2. **SCI diagnostic:** SCI is useful only if sensitivity and alternative-metric audits show stable diagnostic value.
3. **VI physical role:** VI is not globally superior; its defensible value is lower-load/lower-work behavior under high-friction, motion-matched, or success-matched conditions.

## Success Gates

- **Gate A:** If FI-teacher or motion-matched controls invalidate the VI claim, remove VI superiority language and make support/motion the main result.
- **Gate B:** If success-only or success-matched mechanics do not show lower work/load for VI, remove Figure 3 causal interpretation.
- **Gate C:** If SCI is bin-sensitive or lacks useful association with contact/success metrics, demote SCI to exploratory appendix diagnostic.
- **Gate D:** If no cross-sim/contact-stress/orientation layer is added, do not target the paper as a general robot-insertion method.

## File Map

### Planning and review files

- Create: `docs/reviews/review_response_matrix_2026-04-25.md`
  - Maps each reviewer concern to claim, severity, required evidence, success criterion, manuscript location, and response draft.

- Create: `docs/reviews/claim_to_evidence_table_2026-04-25.md`
  - Reviewer-facing claim-to-evidence table for final package.

- Modify: `docs/project/task_plan.md`
  - Add Phase 6 revision hardening with P0/P1/P2 tasks.

- Modify: `docs/project/progress.md`
  - Log exact experiments, commands, failures, and verification results.

### Causal ablation files

- Create: `src/vi_full/three_dof_teacher_coupling_ablation.py`
  - Defines crossed teacher/action-space conditions and aggregation schema.

- Create: `scripts/experiments/run_3dof_teacher_coupling_ablation.py`
  - CLI runner for teacher-crossed and motion-matched ablations.

- Create: `tests/sprints/test_three_dof_teacher_coupling_ablation.py`
  - Unit/contract tests for condition grid and aggregation.

- Create: `tests/runners/test_run_3dof_teacher_coupling_ablation.py`
  - CLI smoke tests.

- Reuse: `src/vi_full/three_dof_policies.py`
  - Existing presets: `teacher_variable_variable`, `teacher_variable_fixed`, `teacher_pose_variable`, `teacher_pose_fixed`.

- Reuse: `src/vi_full/three_dof_training.py`
  - Existing fields: `bc_demo_policy_name`, `bc_demo_teacher_spec`, `bc_rollout_episodes`, `bc_pretrain_steps`, `total_timesteps`.

### Mechanics files

- Create: `src/vi_full/three_dof_impedance_mechanics.py`
  - Summarizes success/failure, success-matched force/work, phase-portrait samples, stiffness schedules, and Pareto rows.

- Create: `scripts/experiments/export_3dof_impedance_mechanics.py`
  - Exports JSON/CSV/Markdown and figure-ready summaries from trace JSON.

- Create: `tests/three_dof/test_three_dof_impedance_mechanics.py`
  - Tests metrics, partitions, and Pareto schema.

- Reuse/modify only if necessary: `scripts/export/export_paper_only_sim_high_friction_trace_figure.py`
  - Existing high-friction trace exporter.

### SCI files

- Create: `src/vi_full/three_dof_support_metric_sensitivity.py`
  - Defines SCI bin grids, state-only/action-only variants, nearest-demo distance, Jaccard, and optional MMD.

- Create: `scripts/experiments/export_3dof_support_metric_sensitivity.py`
  - Exports sensitivity/predictive-audit reports.

- Create: `tests/three_dof/test_three_dof_support_metric_sensitivity.py`
  - Tests bin configs, ranking stability, and alternative metrics.

- Reuse: `src/vi_full/three_dof_support_metrics.py`
  - Existing `ThreeDoFSupportMetricConfig` and SCI computation.

### Manuscript/package files

- Modify: `paper/main.tex`
  - Rewrite title/abstract/intro/experiments/discussion/conclusion around revised spine.

- Modify: `paper/references.bib`
  - Add classical insertion, demo-RL/offline RL, diffusion/transformer imitation, support diagnostics references.

- Modify: `README.md`
  - Update evidence map and reproduction commands.

- Modify: `docs/figure_asset_manifest.md`
  - Add new revision artifacts and figure sources.

- Modify: `docs/submission/submission_package_checklist.md`
  - Record refreshed package state.

---

## P0 Task 1: Review Response Matrix With Success Criteria

**Files:**
- Create: `docs/reviews/review_response_matrix_2026-04-25.md`
- Modify: `docs/project/task_plan.md`
- Modify: `docs/project/progress.md`

- [ ] **Step 1: Write the matrix skeleton**

Create `docs/reviews/review_response_matrix_2026-04-25.md`:

```markdown
# Review Response Matrix 2026-04-25

| Reviewer concern | Claim affected | Severity | Required evidence | Planned experiment / text revision | Success criterion | Manuscript location | Response draft | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Teacher support and VI prior are confounded | VI value; support gate | Fatal | FI teacher x VI teacher crossed ablation | Add VI/FI teacher x VI/FI policy crossed experiment | Demonstration-support effect remains visible after teacher impedance prior is controlled; VI value is stated only if VI improves load/work or robustness under FI/matched support | Main + appendix | We added a crossed teacher/action-space ablation to separate demonstration support from impedance prior. | Pending |
| Motion prior and impedance prior are confounded | VI value | Fatal | Motion-matched impedance controls | Add VI motion + FI K and FI motion + VI K comparisons | The manuscript can state whether the observed effect comes from motion support, stiffness schedule, or both | Main | We decouple motion command source from stiffness command source and report the residual impedance effect. | Pending |
| SCI is post-hoc and bin-dependent | SCI diagnostic | Major | Bin sensitivity + alternative support metrics | Add fine/default/coarse SCI, state-only/action-only SCI, nearest-demo distance, Jaccard/MMD if stable | SCI remains correlated with contact entry/success across bin settings and is not dominated by trivial distance metrics; otherwise SCI is downgraded | Main summary + appendix full grid | We audited SCI against bin settings and continuous alternatives rather than relying on one discretization. | Pending |
| VI value unclear because tuned FI can succeed | VI physical role | Major | Success-matched mechanics analysis | Add success/failure split, success-only curves, success-matched force/work, Pareto, phase portraits | VI shows lower load/work under matched-success conditions, not just higher success or mixed failure composition | Main Figure 3 replacement + appendix | We no longer claim broad VI superiority; we report lower-load contact paths when supported by matched mechanics evidence. | Pending |
| 3DoF analytical benchmark may be toy | External validity | Major/Fatal depending venue | Stress layer or downscoped claims | Add cross-sim/contact-model stress if targeting Q2+; otherwise put orientation/real-robot in limitations | Support-gate and lower-load trends survive at least contact-model/parameter stress, or the paper explicitly targets a controlled benchmark note | Main limitations + supplement if run | We treat the benchmark as controlled evidence and avoid sim-to-real claims. | Pending |
| Internal process jargon weakens credibility | All claims | Major | Full prose cleanup | Remove Sprint/Branch/confirm JSON language from manuscript | Abstract, intro, experiments, and conclusion read as a coherent scientific argument, not an engineering log | Main | We rewrote the paper around support, motion, and impedance factors. | Pending |
```

- [ ] **Step 2: Update phase plan**

In `docs/project/task_plan.md`, add a Phase 6 section:

```markdown
### Phase 6: Review-Driven Revision Hardening (status: planned)
- [ ] P0: Review response matrix with success criteria
- [ ] P0: Teacher-coupling crossed ablation
- [ ] P0: Motion-matched impedance ablation
- [ ] P0: SCI sensitivity and alternative metric audit
- [ ] P0: Claim-boundary rewrite and jargon removal
- [ ] P1: High-friction mechanics split, success-matched force/work, and phase portraits
- [ ] P1: Classical baselines and one or two feasible modern demo-RL baselines
- [ ] P1: Claim-to-evidence table and full reproducibility package
- [ ] P2: Orientation or cross-sim/contact-model stress layer if targeting a top-tier venue
```

- [ ] **Step 3: Log planning action**

Append to `docs/project/progress.md`:

```markdown
### Phase 6 Planning: Review-Driven Revision Hardening (2026-04-25)
- Status: planned
- Actions taken:
  - Created review response matrix with explicit success criteria.
  - Split revision priorities into P0/P1/P2.
  - Reframed manuscript around support, motion, and impedance causal factors.
```

- [ ] **Step 4: Verify docs-related tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/paper/test_docs_claim_source_sync.py tests/paper/test_paper_claim_boundaries.py
```

Expected: pass or fail only on known claim-boundary wording that Task 7 will address.

---

## P0 Task 2: Teacher-Coupling Crossed Ablation

**Files:**
- Create: `src/vi_full/three_dof_teacher_coupling_ablation.py`
- Create: `scripts/experiments/run_3dof_teacher_coupling_ablation.py`
- Create: `tests/sprints/test_three_dof_teacher_coupling_ablation.py`
- Create: `tests/runners/test_run_3dof_teacher_coupling_ablation.py`
- Reuse: `src/vi_full/three_dof_policies.py`
- Reuse: `src/vi_full/three_dof_training.py`

**Design:** Minimal 2x2 crossed table:

| Condition | Demo teacher | Student/action space | Purpose |
| --- | --- | --- | --- |
| `vi_teacher_vi_student` | `teacher_variable_variable` | VI | Current reference |
| `vi_teacher_fi_student` | `teacher_variable_variable` | FI | Tests whether VI teacher support alone explains success |
| `fi_teacher_fi_student` | `teacher_variable_fixed` | FI | Fixed-teacher baseline |
| `fi_teacher_vi_student` | `teacher_variable_fixed` | VI | Tests whether VI student gains under FI support |

- [ ] **Step 1: Write failing grid test**

Create `tests/sprints/test_three_dof_teacher_coupling_ablation.py`:

```python
def test_teacher_coupling_grid_contains_minimal_cross():
    from vi_full.three_dof_teacher_coupling_ablation import build_teacher_coupling_grid

    grid = build_teacher_coupling_grid(seeds=[0], total_timesteps=16)
    names = {row.condition_name for row in grid}
    assert names == {
        "vi_teacher_vi_student",
        "vi_teacher_fi_student",
        "fi_teacher_fi_student",
        "fi_teacher_vi_student",
    }
```

- [ ] **Step 2: Run failing test**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/sprints/test_three_dof_teacher_coupling_ablation.py::test_teacher_coupling_grid_contains_minimal_cross
```

Expected: FAIL with module import error.

- [ ] **Step 3: Implement minimal dataclass and grid**

Create `src/vi_full/three_dof_teacher_coupling_ablation.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class TeacherCouplingCondition:
    condition_name: str
    demo_teacher_preset: str
    student_action_space: str
    total_timesteps: int
    seed: int


def build_teacher_coupling_grid(*, seeds: list[int], total_timesteps: int) -> list[TeacherCouplingCondition]:
    specs = [
        ("vi_teacher_vi_student", "teacher_variable_variable", "variable_impedance"),
        ("vi_teacher_fi_student", "teacher_variable_variable", "fixed_impedance"),
        ("fi_teacher_fi_student", "teacher_variable_fixed", "fixed_impedance"),
        ("fi_teacher_vi_student", "teacher_variable_fixed", "variable_impedance"),
    ]
    return [
        TeacherCouplingCondition(name, teacher, student, total_timesteps, seed)
        for seed in seeds
        for name, teacher, student in specs
    ]
```

- [ ] **Step 4: Run grid test**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/sprints/test_three_dof_teacher_coupling_ablation.py
```

Expected: PASS.

- [ ] **Step 5: Add teacher metadata test**

```python
def test_teacher_coupling_grid_resolves_existing_teacher_presets():
    from vi_full.three_dof_policies import resolve_3dof_teacher_spec
    from vi_full.three_dof_teacher_coupling_ablation import build_teacher_coupling_grid

    for condition in build_teacher_coupling_grid(seeds=[0], total_timesteps=16):
        spec = resolve_3dof_teacher_spec(policy_name=condition.demo_teacher_preset)
        assert spec.preset_name == condition.demo_teacher_preset
```

- [ ] **Step 6: Add aggregation schema test**

Add a test that synthetic per-seed rows aggregate to fields:

```text
condition_name, mean_success_rate, mean_jam_rate, mean_first_contact_step,
mean_peak_contact_force, mean_contact_work, seed_count
```

- [ ] **Step 7: Implement aggregator**

Add `summarize_teacher_coupling_results(rows: list[dict[str, object]]) -> list[dict[str, object]]` with only the fields tested.

- [ ] **Step 8: Add CLI smoke test**

Create `tests/runners/test_run_3dof_teacher_coupling_ablation.py` with:

```python
def test_teacher_coupling_runner_help():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/experiments/run_3dof_teacher_coupling_ablation.py", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "teacher" in result.stdout.lower()
```

- [ ] **Step 9: Implement CLI skeleton**

Runner arguments:

```text
--seeds 0 1 2
--total-timesteps 128
--episodes 16
--output outputs/revision/teacher_coupling_ablation_20260425.json
--smoke-only
```

`--smoke-only` may write grid metadata without training for fast tests.

- [ ] **Step 10: Run focused tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/sprints/test_three_dof_teacher_coupling_ablation.py \
  tests/runners/test_run_3dof_teacher_coupling_ablation.py \
  tests/three_dof/test_three_dof_teacher_policies.py \
  tests/three_dof/test_three_dof_teacher_training.py
```

Expected: PASS.

- [ ] **Step 11: Run real ablation only after smoke tests pass**

```bash
python scripts/experiments/run_3dof_teacher_coupling_ablation.py \
  --seeds 0 1 2 \
  --total-timesteps 128 \
  --episodes 16 \
  --output outputs/revision/teacher_coupling_ablation_20260425.json
```

Expected: JSON includes all four conditions with metrics required by the response matrix.

- [ ] **Step 12: Apply Gate A**

Decision:

- If `fi_teacher_vi_student` improves load/work or robustness over `fi_teacher_fi_student`, keep narrow VI role.
- If VI only helps under VI teacher, remove teacher-independent VI language.
- If FI teacher reopens contact as well as VI teacher, make support quality the central result and lower the VI claim.

---

## P0 Task 3: Motion-Matched Impedance Ablation

**Files:**
- Modify: `src/vi_full/three_dof_teacher_coupling_ablation.py`
- Modify: `scripts/experiments/run_3dof_teacher_coupling_ablation.py`
- Modify: `tests/sprints/test_three_dof_teacher_coupling_ablation.py`

**Design:** Same motion command, different stiffness command:

| Condition | Motion command | Stiffness command | Purpose |
| --- | --- | --- | --- |
| `vi_full` | VI motion | variable K | Original VI teacher path |
| `fi_full` | FI/pose motion | fixed K | Fixed baseline |
| `vi_motion_fi_k` | VI motion | fixed K | Tests whether VI benefit is motion only |
| `fi_motion_vi_k` | FI/pose motion | variable K | Tests whether stiffness schedule independently helps |
| `tuned_fi_k` | best fixed motion | tuned fixed K | Excludes weak midpoint FI explanation |

- [ ] **Step 1: Add failing motion-grid test**

```python
def test_motion_matched_grid_contains_hybrid_controls():
    from vi_full.three_dof_teacher_coupling_ablation import build_motion_matched_grid

    names = {row.condition_name for row in build_motion_matched_grid(seeds=[0], total_timesteps=16)}
    assert {
        "vi_full",
        "fi_full",
        "vi_motion_fi_k",
        "fi_motion_vi_k",
        "tuned_fi_k",
    }.issubset(names)
```

- [ ] **Step 2: Run failing test**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/sprints/test_three_dof_teacher_coupling_ablation.py::test_motion_matched_grid_contains_hybrid_controls
```

Expected: FAIL because function does not exist.

- [ ] **Step 3: Implement motion-matched grid metadata**

Add dataclass fields:

```python
motion_rule: str
impedance_rule: str
fixed_stiffness_xy: float | None = None
fixed_stiffness_z: float | None = None
```

- [ ] **Step 4: Add config-resolve test**

Test that each hybrid condition can be expressed through existing `ThreeDoFTeacherSpec` or through a `replace()` copy of one existing spec.

- [ ] **Step 5: Implement config builder**

Use existing presets and `dataclasses.replace` to construct:

```text
vi_motion_fi_k: base teacher_variable_variable with impedance_rule="fixed"
fi_motion_vi_k: base teacher_variable_fixed with impedance_rule="contact_aware_variable_impedance"
tuned_fi_k: fixed rule with tuned stiffness values from tuned fixed sweep
```

- [ ] **Step 6: Extend CLI**

Add:

```text
--include-motion-matched
--motion-matched-output outputs/revision/motion_matched_impedance_ablation_20260425.json
```

- [ ] **Step 7: Run focused tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/sprints/test_three_dof_teacher_coupling_ablation.py tests/runners/test_run_3dof_teacher_coupling_ablation.py
```

Expected: PASS.

- [ ] **Step 8: Run real motion-matched export**

```bash
python scripts/experiments/run_3dof_teacher_coupling_ablation.py \
  --include-motion-matched \
  --seeds 0 1 2 \
  --total-timesteps 128 \
  --episodes 16 \
  --output outputs/revision/teacher_coupling_ablation_20260425.json \
  --motion-matched-output outputs/revision/motion_matched_impedance_ablation_20260425.json
```

Expected: JSON contains success, jam, first contact, peak force, contact work, motion rule, and impedance rule for each condition.

---

## P0 Task 4: SCI Sensitivity and Alternative Metric Audit

**Files:**
- Create: `src/vi_full/three_dof_support_metric_sensitivity.py`
- Create: `scripts/experiments/export_3dof_support_metric_sensitivity.py`
- Create: `tests/three_dof/test_three_dof_support_metric_sensitivity.py`
- Reuse: `src/vi_full/three_dof_support_metrics.py`

- [ ] **Step 1: Write failing bin-grid test**

```python
def test_sci_sensitivity_configs_cover_fine_default_coarse():
    from vi_full.three_dof_support_metric_sensitivity import build_sci_sensitivity_configs

    configs = build_sci_sensitivity_configs()
    triples = {
        (cfg.obs_xy_norm_bin_m, cfg.force_norm_bin_n, cfg.action_xy_norm_bin, cfg.action_k_xy_bin)
        for cfg in configs
    }
    assert (2.5e-4, 0.125, 0.05, 0.05) in triples
    assert (5e-4, 0.25, 0.1, 0.1) in triples
    assert (1e-3, 0.5, 0.2, 0.2) in triples
```

- [ ] **Step 2: Run failing test**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/three_dof/test_three_dof_support_metric_sensitivity.py::test_sci_sensitivity_configs_cover_fine_default_coarse
```

Expected: FAIL with module import error.

- [ ] **Step 3: Implement config grid**

Create configs using `ThreeDoFSupportMetricConfig`:

```python
from vi_full.three_dof_support_metrics import ThreeDoFSupportMetricConfig


def build_sci_sensitivity_configs() -> list[ThreeDoFSupportMetricConfig]:
    return [
        ThreeDoFSupportMetricConfig(2.5e-4, 5e-4, 0.125, 0.05, 0.05, 0.05, 0.05),
        ThreeDoFSupportMetricConfig(5e-4, 5e-4, 0.25, 0.1, 0.1, 0.1, 0.1),
        ThreeDoFSupportMetricConfig(1e-3, 1e-3, 0.5, 0.2, 0.2, 0.2, 0.2),
    ]
```

- [ ] **Step 4: Add alternative metric tests**

Test functions:

```text
compute_nearest_demo_distance
compute_support_jaccard
compute_state_only_sci
compute_action_only_sci
```

Synthetic criterion: identical rollout has higher overlap/lower distance than shifted rollout.

- [ ] **Step 5: Implement pure NumPy alternatives**

Avoid dependencies. Use pairwise distances only for small arrays in tests; for larger arrays, batch if needed.

- [ ] **Step 6: Add predictive audit schema test**

Aggregator output rows must include:

```text
metric_name, condition_name, value, success_rate, contact_entry_rate,
jam_rate, peak_force, contact_work, final_distance, contact_steps
```

- [ ] **Step 7: Implement exporter CLI**

Arguments:

```text
--input-artifacts outputs/evidence_matrix/three_dof_evidence_matrix.json
--output-stem outputs/revision/sci_sensitivity_20260425
--smoke-only
```

- [ ] **Step 8: Run focused tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/three_dof/test_three_dof_support_metrics.py \
  tests/three_dof/test_three_dof_support_metric_sensitivity.py
```

Expected: PASS.

- [ ] **Step 9: Generate real SCI audit**

```bash
python scripts/experiments/export_3dof_support_metric_sensitivity.py \
  --input-artifacts outputs/evidence_matrix/three_dof_evidence_matrix.json \
  --output-stem outputs/revision/sci_sensitivity_20260425
```

Expected: JSON/CSV/Markdown contain bin sensitivity, alternative metrics, and predictive audit fields.

- [ ] **Step 10: Apply Gate C**

Decision:

- Stable ranking + useful association: keep SCI in main text.
- Stable ranking + weak association: move SCI mostly to appendix.
- Unstable ranking: remove SCI as contribution.

---

## P0 Task 5: Manuscript Claim-Boundary Rewrite

**Files:**
- Modify: `paper/main.tex`
- Modify: `paper/references.bib`
- Modify: `README.md`
- Modify: `docs/figure_asset_manifest.md`
- Tests: `tests/paper/test_paper_claim_boundaries.py`, `tests/paper/test_prose_statistics_sync.py`, `tests/paper/test_paper_figures.py`

- [ ] **Step 1: Rewrite title decision**

Choose one safer title unless new evidence justifies a stronger one:

```text
A Diagnostic Study of Demonstration Support and Variable Impedance in 3DoF Contact-Rich Insertion
```

or:

```text
Support-Gated Learnability and Variable-Impedance Load Paths in a 3DoF Contact Insertion Benchmark
```

- [ ] **Step 2: Remove process/internal terms**

Search `paper/main.tex` for:

```text
Sprint
Branch
confirm JSON
benchmark-local recipe
teacher-coupled
algorithm ranking
```

Replace with scientific terms:

```text
clearance sensitivity sweep
controlled benchmark protocol
matched teacher-generated demonstration setting
support-gated learnability
```

- [ ] **Step 3: Rewrite abstract around three claims**

Abstract must include:

```text
1. demonstration support gates contact entry
2. SCI is a task-specific diagnostic, validated by sensitivity/audit results
3. VI is evaluated as lower-load contact path, not universal success superiority
```

- [ ] **Step 4: Rewrite contributions**

Use safer language:

```text
We study ...
We audit ...
We decouple ...
We show, under matched-success mechanics evidence, ...
```

Avoid:

```text
We propose SG-VI as a general method
VI outperforms FI
SCI is a universal metric
```

- [ ] **Step 5: Add explicit non-claims**

Add limitations:

```text
The benchmark omits full 6D wrench dynamics, orientation-induced jamming, hardware calibration error, sensor drift, and vision-based perception. The results therefore should not be read as sim-to-real evidence or industrial insertion generality.
```

- [ ] **Step 6: Add modern/classical references**

Update `paper/references.bib` with restrained categories:

```text
classical insertion and impedance/admittance control
demo-augmented RL and offline RL
Diffusion Policy / ACT / transformer imitation
support coverage / dataset coverage diagnostics
```

Do not cite a method as direct baseline unless actually comparable or tested.

- [ ] **Step 7: Run prose tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/paper/test_paper_claim_boundaries.py \
  tests/paper/test_prose_statistics_sync.py \
  tests/paper/test_paper_figures.py
```

Expected: PASS after tests are updated to the new claim boundary.

---

## P1 Task 6: High-Friction Mechanics Split, Phase Portraits, and Pareto

**Files:**
- Create: `src/vi_full/three_dof_impedance_mechanics.py`
- Create: `scripts/experiments/export_3dof_impedance_mechanics.py`
- Create: `tests/three_dof/test_three_dof_impedance_mechanics.py`
- Reuse/modify only if needed: `scripts/export/export_paper_only_sim_high_friction_trace_figure.py`

- [ ] **Step 1: Write partition test**

```python
def test_mechanics_summary_splits_success_failure_and_all():
    from vi_full.three_dof_impedance_mechanics import summarize_mechanics_by_outcome

    runs = [
        {"suite": "vi", "is_success": True, "is_jammed": False, "trace": [{"cumulative_contact_work": 0.1, "peak_contact_force": 1.0, "contact_force_norm": 0.5, "decoded_k_xy": 0.2, "decoded_k_z": 0.3, "distance_to_target": 0.001}]},
        {"suite": "vi", "is_success": False, "is_jammed": True, "trace": [{"cumulative_contact_work": 0.4, "peak_contact_force": 2.0, "contact_force_norm": 1.5, "decoded_k_xy": 0.7, "decoded_k_z": 0.8, "distance_to_target": 0.004}]},
    ]
    summary = summarize_mechanics_by_outcome(runs)
    assert summary["vi"]["success"]["count"] == 1
    assert summary["vi"]["failure"]["count"] == 1
    assert summary["vi"]["all"]["count"] == 2
```

- [ ] **Step 2: Run failing test**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/three_dof/test_three_dof_impedance_mechanics.py::test_mechanics_summary_splits_success_failure_and_all
```

Expected: FAIL with module import error.

- [ ] **Step 3: Implement summary function**

Include fields:

```text
count, mean_contact_work, mean_peak_force, p95_peak_force,
mean_contact_steps, jam_rate, mean_k_xy, mean_k_z
```

- [ ] **Step 4: Add phase-portrait test**

Test `extract_phase_portrait_samples(trace)` returns rows:

```text
lateral_displacement_norm, lateral_force_norm, insertion_depth, axial_force, k_xy, k_z
```

- [ ] **Step 5: Add Pareto test**

Test `build_force_work_pareto(summary)` returns:

```text
suite, partition, success_rate, mean_contact_work, mean_peak_force, jam_rate
```

- [ ] **Step 6: Implement exporter CLI**

Arguments:

```text
--trace-json artifacts/mechanics/latest_three_dof_high_friction_direct_mechanics_trace.json
--output-stem outputs/revision/high_friction_mechanics_split_20260425
```

Outputs:

```text
outputs/revision/high_friction_mechanics_split_20260425.json
outputs/revision/high_friction_mechanics_split_20260425.csv
outputs/revision/high_friction_mechanics_split_20260425.md
figures/main/fig3_high_friction_impedance_mechanism_success_failure.png
figures/main/fig3_high_friction_impedance_mechanism_success_failure.pdf
```

- [ ] **Step 7: Run focused tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/three_dof/test_three_dof_impedance_mechanics.py \
  tests/paper/test_export_paper_only_sim_high_friction_trace_figure.py
```

Expected: PASS.

- [ ] **Step 8: Generate mechanics artifacts**

```bash
python scripts/experiments/export_3dof_impedance_mechanics.py \
  --trace-json artifacts/mechanics/latest_three_dof_high_friction_direct_mechanics_trace.json \
  --output-stem outputs/revision/high_friction_mechanics_split_20260425
```

Expected: outputs and figure files created.

- [ ] **Step 9: Apply Gate B**

Decision:

- If success-matched VI has lower work/load than FI, keep lower-load VI claim.
- If only all-trace aggregate favors VI, remove causal VI mechanics claim.
- If FI shows deadlock/limit-cycle-like phase portraits while VI escapes, report as qualitative trace evidence only.

---

## P1 Task 7: Classical and Modern Baseline Coverage

**Files:**
- Modify if needed: `src/vi_full/three_dof_evidence_matrix.py`
- Modify if needed: `scripts/experiments/export_3dof_evidence_matrix.py`
- Modify: `paper/main.tex`
- Modify: `paper/references.bib`
- Modify: `README.md`
- Tests: `tests/paper/test_three_dof_evidence_matrix.py`, `tests/three_dof/test_three_dof_benchmark_diagnostics.py`

- [ ] **Step 1: Audit current baseline coverage**

Check whether these appear in active evidence artifacts:

```text
ThreeDoFHybridPositionForceController
ThreeDoFCompliantSearchController
ThreeDoFTunedImpedanceController
BC-only
BC→PPO
DAPG-lite
PPO/SAC/TD3 without BC
```

- [ ] **Step 2: Add missing classical anchor tests only if absent**

If evidence matrix omits existing classical controllers, add tests asserting their rows exist.

- [ ] **Step 3: Add missing rows using existing controllers**

Do not invent new controllers unless the audit proves the existing ones do not answer the review.

- [ ] **Step 4: Decide modern low-D baseline scope**

Choose at most two:

```text
Recommended first: TD3+BC or SAC+demo
Recommended second: residual RL over classical impedance
Defer: full vision Diffusion Policy, RVT-2, 3D Diffusion Policy, DrEureka
```

- [ ] **Step 5: If modern baseline is selected, create separate mini-plan**

Do not bury a new algorithm implementation in this task. Write a separate plan before implementation.

- [ ] **Step 6: Update literature discussion**

Add restrained discussion of modern methods as scope-setting, not direct same-interface baselines unless tested.

- [ ] **Step 7: Run focused tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/paper/test_three_dof_evidence_matrix.py \
  tests/three_dof/test_three_dof_benchmark_diagnostics.py \
  tests/paper/test_paper_claim_boundaries.py
```

Expected: PASS.

---

## P2 Task 8: Scope Stress Decision

**Files:**
- Create only if selected: `src/vi_full/three_dof_cross_sim_stress.py` or `src/vi_full/three_dof_orientation_stress.py`
- Create only if selected: `scripts/experiments/run_3dof_cross_sim_stress.py` or `scripts/experiments/run_3dof_orientation_stress.py`
- Create only if selected: tests under `tests/sprints/` and `tests/runners/`
- Modify: `paper/main.tex`

- [ ] **Step 1: Decide target tier**

Choose:

```text
A. Controlled benchmark submission: no new stress layer; downscope claims.
B. Stronger Q2/RA-L attempt: add contact-model/contact-parameter stress in current interface.
C. Top-tier attempt: create separate cross-sim/orientation/hardware plan.
```

- [ ] **Step 2: If B, define same-interface stress conditions**

Minimum:

```text
friction stress
clearance stress
force-noise stress
hidden calibration/pose-frame bias
combined stress
```

- [ ] **Step 3: If C, stop and write a separate plan**

Full robosuite/MuJoCo/6DoF/hardware work changes task definition and must not be treated as a subtask here.

---

## P1 Task 9: Claim-to-Evidence Table, Verification, and Bundle Refresh

**Files:**
- Create: `docs/reviews/claim_to_evidence_table_2026-04-25.md`
- Modify: `docs/submission/submission_package_checklist.md`
- Modify: `docs/project/progress.md`
- Regenerate final package under: `tmp/submission_bundle/journal_double_blind/`

- [ ] **Step 1: Create claim-to-evidence table**

```markdown
# Claim-to-Evidence Table 2026-04-25

| Claim | Main evidence | Supplementary evidence | Limitation |
| --- | --- | --- | --- |
| Demo support reopens useful contact | Teacher crossed ablation | PPO/SAC/TD3 negative audit | Benchmark-local |
| SCI diagnoses support gate | SCI sensitivity + alternative metrics | Seed-wise correlation | Not a universal metric |
| VI lowers contact load | Success-matched high-friction traces | Motion-matched ablation | No hardware yet |
```

- [ ] **Step 2: Run focused revision tests**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q \
  tests/sprints/test_three_dof_teacher_coupling_ablation.py \
  tests/runners/test_run_3dof_teacher_coupling_ablation.py \
  tests/three_dof/test_three_dof_impedance_mechanics.py \
  tests/three_dof/test_three_dof_support_metric_sensitivity.py \
  tests/paper/test_paper_claim_boundaries.py \
  tests/paper/test_docs_claim_source_sync.py \
  tests/paper/test_paper_figures.py
```

Expected: all pass.

- [ ] **Step 3: Run full no-training gate**

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

Expected: all tests pass with expected skips only.

- [ ] **Step 4: Check paper assets**

```bash
python scripts/export/build_paper_assets.py --check
```

Expected: no unexpected diffs.

- [ ] **Step 5: Build paper PDF**

```bash
python scripts/export/build_paper_pdf.py
```

Expected: PDF builds through direct `pdflatex -> bibtex -> pdflatex -> pdflatex` chain.

- [ ] **Step 6: Refresh anonymous bundle**

```bash
python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind
```

Build anonymous PDF from:

```text
tmp/submission_bundle/journal_double_blind/anonymous_snapshot/paper/
```

Then stage final bundle:

```bash
python scripts/export/build_submission_bundle.py \
  --output-dir tmp/submission_bundle/journal_double_blind \
  --paper-pdf tmp/submission_bundle/anonymous_manuscript.pdf
```

- [ ] **Step 7: Verify reviewer snapshot**

Extract `anonymous_snapshot.zip` to a temporary directory and run:

```bash
python -m pytest -q tests/reviewer
```

Expected: reviewer smoke tests pass.

- [ ] **Step 8: Update checklist and progress**

Record exact commands, outputs, package contents, and any remaining limitations in:

```text
docs/submission/submission_package_checklist.md
docs/project/progress.md
```

---

## Execution Policy

- Start with P0 only. Do not run P1/P2 experiments before P0 gates are interpretable.
- Use TDD for new Python modules.
- Keep all new result artifacts under `outputs/revision/` unless they are final paper figures.
- Do not modify anonymous submission package until manuscript and artifacts are finalized.
- Do not commit unless the user explicitly asks.
