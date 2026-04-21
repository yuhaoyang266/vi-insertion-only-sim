# Progress Log

### Phase 3: Sprint 2B Anchor-Integrated Evidence Matrix
- **Status:** complete
- Actions taken:
  - Added `src/vi_full/three_dof_evidence_matrix.py` to merge Branch-A confirm evidence with canonical five-profile benchmark anchors.
  - Added `scripts/experiments/export_3dof_evidence_matrix.py` to export JSON, CSV, Markdown, and contact-gate PNG/PDF artifacts.
  - Wrote new contract tests for the matrix builder and CLI exporter.
  - Generated `outputs/evidence_matrix/three_dof_evidence_matrix.{json,csv,md}` and `outputs/evidence_matrix/three_dof_contact_gate_matrix.{png,pdf}` from the real confirm and benchmark artifacts.
  - Updated `protocol_freeze.md`, `task_plan.md`, `findings.md`, and `paper/main.tex` so the mixed-contract boundary is explicit and SAC stays framed as a distance proxy rather than a success baseline.
  - Tightened row-level provenance after review: matrix rows now cite the direct confirm JSON or schema2 benchmark JSON inputs, rather than indirect upstream pilot/table exports.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_evidence_matrix.py`
  - `F:\edge download\learning\vi-insertion-only-sim\scripts\experiments\export_3dof_evidence_matrix.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_three_dof_evidence_matrix.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_run_3dof_evidence_matrix.py`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\evidence_matrix\three_dof_evidence_matrix.json`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\evidence_matrix\three_dof_evidence_matrix.csv`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\evidence_matrix\three_dof_evidence_matrix.md`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\evidence_matrix\three_dof_contact_gate_matrix.png`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\evidence_matrix\three_dof_contact_gate_matrix.pdf`
  - `F:\edge download\learning\vi-insertion-only-sim\protocol_freeze.md`
  - `F:\edge download\learning\vi-insertion-only-sim\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\findings.md`
  - `F:\edge download\learning\vi-insertion-only-sim\progress.md`

### Phase 3: Sprint 2A Branch-A Confirm Benchmark Pack
- **Status:** complete
- Actions taken:
  - Created `narrative_branches.md` and locked Branch A on 2026-04-20 Asia/Shanghai.
  - Updated `protocol_freeze.md` with the Cross-Family Confirm Interpretation Boundary.
  - Updated planning notes to record: Sprint 1 full pilot completed 9/9 chunks; selected narrative branch A; no pure-RL method reached contact; SAC is only a terminal-distance proxy advantage.
  - Recorded the next Sprint 2 direction: compare Branch-A pure-RL failure against demo-supported anchors, not oversell SAC.
  - Added confirm report module, CLI exporter, contract tests, and paper-facing artifacts.
  - Hardened the confirm report contract so `summary_rows` must cover the full method-budget grid, not only report complete metadata.
  - Verified the focused confirm test suite with `8 passed in 12.18s`.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\narrative_branches.md`
  - `F:\edge download\learning\vi-insertion-only-sim\protocol_freeze.md`
  - `F:\edge download\learning\vi-insertion-only-sim\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\findings.md`
  - `F:\edge download\learning\vi-insertion-only-sim\progress.md`

## Session: 2026-04-18

### Phase 1: Repository & Paper Discovery
- **Status:** complete
- **Started:** 2026-04-18 Asia/Shanghai
- Actions taken:
  - 读取 `using-superpowers` 与 `planning-with-files` 技能说明，确认本次任务应采用文件化规划流程。
  - 确认外层目录不是仓库，项目根目录位于 `F:\edge download\learning\vi-insertion-only-sim`。
  - 读取 planning templates，并在项目根目录创建 `task_plan.md`、`findings.md`、`progress.md`。
  - 阅读 `README.md`，提取当前 manuscript claim、evidence map 与 jam metric semantics。
  - 尝试用 `rg` 扫描论文与脚本关键词，发现当前环境 `rg.exe` 不可用，决定切换到 `Select-String`。
  - 扫描 `paper/main.tex`，确认当前 contributions/limitations 已明确暴露 off-policy、teacher prior、sim-only 三类短板。
  - 扫描 `src` 与 `tests`，确认现有 appendix teacher block 为 2x2 结构，但 `SAC/TD3` 代码与用户点名的 3 个 contract tests 暂不存在。
  - 提取当前正文 section 骨架、主表列定义与 teacher spec registry 的精确定义，为后续计划收敛提供 repo-level 依据。
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\task_plan.md` (created)
  - `F:\edge download\learning\vi-insertion-only-sim\findings.md` (created)
  - `F:\edge download\learning\vi-insertion-only-sim\progress.md` (created)

### Phase 2: Plan Audit & Narrative Lock
- **Status:** in_progress
- Actions taken:
  - 基于仓库现状评估用户提出的 Sprint 0-6 草案，识别哪些部分是低摩擦扩展，哪些部分是新的工程入口。
  - 读取 PPO-only large-budget runner、训练 config 和环境终止语义，确认 Sprint 0 可围绕现有 runner + 新 regression tests 快速收口。
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\findings.md`
  - `F:\edge download\learning\vi-insertion-only-sim\progress.md`

## Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Repo root detection | `git status --short` in outer dir | Either repo status or clear error | Reported not a git repository; located repo in subdir | pass |

## Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| 2026-04-18 | `git status` failed in outer working dir | 1 | Inspected child directory and switched planning target to repo root |
| 2026-04-18 | `rg.exe` failed with `Access is denied` | 1 | Switched repository search strategy to PowerShell `Select-String` |
| 2026-04-18 | PowerShell line-range extraction for teacher spec failed because the pattern matched multiple definitions | 1 | Narrow future reads to single paths / single matches |

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | Phase 2 in_progress(narrative lock 未完成);Phase 2.5 Hardware Decision Gate 为下一个显性 blocker;Phase 3 sim-only 工作可与 2.5 并行启动 |
| Where am I going? | Phase 3(sim-only 5 个 Sprint)→ Phase 3.5/H(conditional on 硬件决策)→ Phase 4(论文 rewrite,contribution 重构为 propose+show)→ Phase 5(submission package) |
| What's the goal? | 推进到 SCI Q2 非 OA(T-ASE / T-MECH / MSSP 档);若 Phase 2.5 = Rizon 4s / Franka Research 3 则上调至 Q1(T-RO / IJRR);若 no-hardware 则回退 Q3 上游 + cross-sim 或 named method 补偿 |
| What have I learned? | 1) `src/` 无 SAC/TD3 代码,Sprint 1 必须新建 `training_baselines.py`,不是零成本扩展;2) 当前 teacher 2×2 registry 是 `motion × impedance`(`teacher_variable_variable` 等 4 个 preset),不是 `teacher_type × demo_quality/quantity`,Sprint 3 需要加正交轴;3) 用户点名的 3 个 contract tests(force_jam consecutive / blocked_contact separate / ppo-only disables auxiliary)当前 `tests/` 下不存在,需新建;4) Abstract 自称 `simulation-only` + 4 条 contribution 全为 `we show` = Q2 天花板的两个硬伤,必须有 `we propose` + 真机/跨仿真二选一补偿;5) 硬件决策只 block Phase H 和 Phase 3.5 方向校准,**不 block** Phase 3(sim-only 约 70% 改动与硬件解耦);6) Synria Alicia-M/D 不适合做 primary real-robot validation(joint-level MIT、无 FT sensor、串口 200 Hz、精度未公开);Flexiv Rizon 4s 全档位超配,Franka Research 3 / 二手 Panda 为 Q2 稳妥退路 |
| What have I done? | 完成 repo/paper audit;把用户 Sprint 0-5 草案 lift 成 phase-gated plan(Phase 1 / 2 / 2.5 / 3 / 3.5 / H / 4 / 5);`task_plan.md` 已加 dependency graph、effort/risk/status/deliverable 字段、Meta vs Research decision 拆分;尚未修改训练代码或产出 `narrative_branches.md` / `hardware_decision.md` |

---
*Update after completing each phase or encountering errors*

### Phase 3: Sprint 0 Hardening
- **Status:** complete
- Actions taken:
  - 根据 review 补强 `protocol_freeze.md`：加入环境版本锁、稳定锚点、condition x profile 的 200k 地板表，以及 `50k / 100k` 待确认说明。
  - 在 `test_run_3dof_ppo_large_budget_ablation.py` 中补充 PPO-only condition 名单断言和 condition-specific optimizer 断言。
  - 在 `test_three_dof_contract.py` 中补充 blocked-contact persistence 负例和 force-jam interruption reset 负例。
  - 将 `task_plan.md` 中的 Sprint 0 checkbox 标记为完成。
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\protocol_freeze.md`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_run_3dof_ppo_large_budget_ablation.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_three_dof_contract.py`
  - `F:\edge download\learning\vi-insertion-only-sim\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\findings.md`
  - `F:\edge download\learning\vi-insertion-only-sim\progress.md`

## Sprint 0 Hardening Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Sprint 0 hardening regression suite | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q .\\tests\\test_three_dof_contract.py .\\tests\\test_run_3dof_ppo_large_budget_ablation.py` | New edge-case and registry assertions stay green | `10 passed in 6.24s` | pass |
### Phase 3: Sprint 0 Execution
- **Status:** in_progress
- Actions taken:
  - 将现有 env contract tests 对齐为 paper-facing 名称：`test_force_jam_requires_consecutive_violations` 与 `test_blocked_contact_failure_is_separate_reason`。
  - 按 TDD 新增 `test_ppo_only_protocol_disables_all_auxiliary_stages`，先观察其因 registry 依赖隐式默认值而失败。
  - 在 `src/vi_full/three_dof_benchmark.py` 新增 `_PPO_ONLY_PROTOCOL_FREEZE_OVERRIDES`，让两个 PPO-only conditions 显式冻结 auxiliary-stage disable keys。
  - 创建 `protocol_freeze.md`，写入 canonical command、frozen profiles、conditions、disable contract 与预期 200k 负结果。
  - 运行 200k reproduction，产出 `outputs/three_dof_ppo_large_budget_ablation_200k_repro.json`。
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_benchmark.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_three_dof_contract.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_run_3dof_ppo_large_budget_ablation.py`
  - `F:\edge download\learning\vi-insertion-only-sim\protocol_freeze.md`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\three_dof_ppo_large_budget_ablation_200k_repro.json`

## Sprint 0 Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Sprint 0 regression suite (RED) | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q .\\tests\\test_three_dof_contract.py .\\tests\\test_run_3dof_ppo_large_budget_ablation.py` | New protocol-freeze test fails for expected reason | Failed because PPO-only registry omitted explicit auxiliary-stage freeze overrides | pass |
| Sprint 0 regression suite (GREEN) | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q .\\tests\\test_three_dof_contract.py .\\tests\\test_run_3dof_ppo_large_budget_ablation.py` | All targeted regression tests pass | `8 passed in 6.42s` | pass |
| PPO-only 200k reproduction | `python .\\scripts\\experiments\\run_3dof_ppo_large_budget_ablation.py --budgets 200000 --output .\\outputs\\three_dof_ppo_large_budget_ablation_200k_repro.json` | Both PPO-only conditions remain in non-contact regime | Both conditions: success=0, contact_steps=0, first_contact=64, peak_force=0 | pass |

## Sprint 0 Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
| 2026-04-18 | `pytest` plugin autoload crashed via `zarr` and `numpy.dtypes` mismatch | 1 | Re-ran targeted tests with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` |
| 2026-04-18 | First JSON summary script for reproduction artifact hit a PowerShell empty-pipe parser error | 1 | Rewrote the extraction with an explicit row accumulator |
### Phase 3: Sprint 1 Scaffolding
- **Status:** in_progress
- Actions taken:
  - Added `src/vi_full/three_dof_cross_family_baselines.py` as a minimal algorithm-agnostic 3DoF training layer for `PPO`, `SAC`, and `TD3`
  - Added `build_3dof_cross_family_pilot_registry()` with default pure-RL methods `ppo_no_bc / sac_no_bc / td3_no_bc`
  - Added `scripts/experiments/run_3dof_cross_family_pilot.py` to materialize the method x budget pilot grid into a JSON artifact
  - Reused `VecNormalizePredictor + evaluate_3dof_predictor` so Sprint 1 can stay off the PPO/BC mainline code path
  - Fixed the new baseline trainer to force `device='cpu'` and avoid the SB3 MLP-on-GPU warning during pilot runs
  - Ran a real smoke command and wrote `F:\edge download\learning\vi-insertion-only-sim\outputs\three_dof_cross_family_pilot_smoke.json`
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_cross_family_baselines.py`
  - `F:\edge download\learning\vi-insertion-only-sim\scripts\experiments\run_3dof_cross_family_pilot.py`
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\__init__.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_three_dof_cross_family_baselines.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_run_3dof_cross_family_pilot.py`

## Sprint 1 Scaffolding Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Cross-family runner + baseline contract suite | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q .\\tests\\test_three_dof_cross_family_baselines.py .\\tests\\test_run_3dof_cross_family_pilot.py` | New module and runner contracts pass | `4 passed in 6.36s` | pass |
| Sprint 0 + Sprint 1 targeted regression suite | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q .\\tests\\test_three_dof_contract.py .\\tests\\test_run_3dof_ppo_large_budget_ablation.py .\\tests\\test_three_dof_cross_family_baselines.py .\\tests\\test_run_3dof_cross_family_pilot.py` | New pilot scaffolding does not regress Sprint 0 contracts | `14 passed in 9.91s` | pass |
| Cross-family pilot smoke | `python .\\scripts\\experiments\\run_3dof_cross_family_pilot.py --seeds 0 --episodes 1 --budgets 8 --profiles nominal --output .\\outputs\\three_dof_cross_family_pilot_smoke.json` | All three methods write a pilot artifact | `ppo_no_bc/sac_no_bc/td3_no_bc` all completed and wrote JSON | pass |

### Phase 3: Sprint 1 Reporting & Full Pilot Execution
- **Status:** complete
- Actions taken:
  - Added `src/vi_full/three_dof_cross_family_pilot_report.py` to merge per-method per-budget chunk artifacts, detect missing grid cells, and flatten pilot-facing metrics.
  - Added `scripts/experiments/export_3dof_cross_family_pilot_report.py` to export a merged JSON report plus two internal figures (`success_vs_budget`, `first_contact_step_vs_budget`).
  - Wrote and passed new tests for report merge/export contracts and CLI execution.
  - Exported the final Sprint 1 report to `outputs/pilot_report/three_dof_cross_family_pilot_report.json`.
  - Completed and merged the full 9/9 method-budget pilot grid:
    `ppo_no_bc@50k/100k/200k`, `sac_no_bc@50k/100k/200k`, and `td3_no_bc@50k/100k/200k`.
  - Refreshed both internal figure pairs from the final merged report.
  - Recorded Branch A evidence: all pure-RL rows have `success_rate=0`, `mean_contact_steps=0`, and `mean_first_contact_step=64`; SAC only improves the terminal-distance proxy.
- Files created/modified:
  - `F:\edge download\learning\vi-insertion-only-sim\src\vi_full\three_dof_cross_family_pilot_report.py`
  - `F:\edge download\learning\vi-insertion-only-sim\scripts\experiments\export_3dof_cross_family_pilot_report.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_three_dof_cross_family_pilot_report.py`
  - `F:\edge download\learning\vi-insertion-only-sim\tests\test_run_3dof_cross_family_pilot_report.py`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_chunks\three_dof_cross_family_pilot__sac_no_bc__200000.json`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_chunks\three_dof_cross_family_pilot__td3_no_bc__200000.json`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_report\three_dof_cross_family_pilot_report.json`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_report\three_dof_cross_family_pilot_success_vs_budget.pdf`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_report\three_dof_cross_family_pilot_success_vs_budget.png`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_report\three_dof_cross_family_pilot_first_contact_step_vs_budget.pdf`
  - `F:\edge download\learning\vi-insertion-only-sim\outputs\pilot_report\three_dof_cross_family_pilot_first_contact_step_vs_budget.png`
  - `F:\edge download\learning\vi-insertion-only-sim\task_plan.md`
  - `F:\edge download\learning\vi-insertion-only-sim\findings.md`
  - `F:\edge download\learning\vi-insertion-only-sim\progress.md`

## Sprint 1 Reporting & Full Pilot Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Cross-family report + CLI contract suite | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q .\\tests\\test_three_dof_cross_family_baselines.py .\\tests\\test_run_3dof_cross_family_pilot.py .\\tests\\test_three_dof_cross_family_pilot_report.py .\\tests\\test_run_3dof_cross_family_pilot_report.py` | Runner, report merge/export, and CLI stay green together | `9 passed, 1 fontTools warning in 12.98s` | pass |
| Full pilot report export | `python .\\scripts\\experiments\\export_3dof_cross_family_pilot_report.py --chunk-dir .\\outputs\\pilot_chunks --output-dir .\\outputs\\pilot_report` | Merge all 9 chunks and refresh two internal figures | Wrote JSON + 4 figure files; merged report records `completed_chunk_count=9`, `missing_chunk_count=0`; stderr only showed the existing `gym` deprecation warning and a `fontTools` deprecation warning during matplotlib export | pass |
| Merged report invariant check | PowerShell JSON assertion over `outputs\\pilot_report\\three_dof_cross_family_pilot_report.json` | `completed=9`, `missing=0`, `summary_rows=9`, all rows preserve Branch A contact invariants | `report_json_ok completed=9 missing=0 branch_a_rows=9` | pass |
| Internal figure artifact check | PowerShell file-size assertion over the 2 PDF + 2 PNG report figures | All refreshed figure files exist and are non-empty | Success figure: `18256`/`55150` bytes; first-contact figure: `18651`/`58337` bytes | pass |
| Real pilot chunk: TD3 50k | background queue invoking `python .\\scripts\\experiments\\run_3dof_cross_family_pilot.py --methods td3_no_bc --budgets 50000 --output .\\outputs\\pilot_chunks\\three_dof_cross_family_pilot__td3_no_bc__50000.json` | Materialize the missing `td3_no_bc@50k` chunk | Wrote JSON; `success_mean_over_profiles=0.0`; `mean_final_distance≈30.78 mm`; `mean_first_contact_step=64` | pass |
