# Task Plan: Raise the project's paper ceiling with a tighter evidence-driven roadmap

## Goal
将 `vi-insertion-only-sim` 从"sim-only 3DoF 单任务 narrow-claim"论文推进到 **SCI Q2 非 OA** 级别(T-ASE / T-MECH / MSSP 档)。若 Phase 2.5 硬件决策选择 Flexiv Rizon 4s 或 Franka Research 3,目标上调至 **Q1**(T-RO / IJRR 档);若不买硬件,目标回退至 **Q3 上游** 并以硬加分路径(cross-simulator transfer 或 named method + diagnostic tool)补偿。

## Target Venue Tier
| Path | Ceiling | Requires |
|------|---------|----------|
| No-hardware | Q3 upper / Q2 marginal | cross-sim transfer 或 named method 二选一补偿 |
| Franka-class hardware | Q2 稳妥 | Phase 3.5 + Phase H 完整执行 |
| Rizon 4s + Flexiv primitive baseline | Q1 有机会 | Phase 3.5 + Phase H + primitive 对照实验 |

Final tier 将在 Phase 2.5 关闭时锁定。

## Current Phase
Phase 3 complete; next: Phase 4 writing / artifact integration

## Phase Dependency Graph
```
Phase 1 (done)
   │
   v
Phase 2 (narrative lock)
   │
   ├──> Phase 2.5 (hardware gate) ──> Phase 3.5 (scaffolding, if hw) ──> Phase H (real, if hw)
   │                                                                            │
   └──> Phase 3 (sim-only, parallel) ──────────────────────────────────────────>│
                                                                                 v
                                                                           Phase 4 (writing)
                                                                                 │
                                                                                 v
                                                                           Phase 5 (delivery)
```
- **Phase 3 不 block 于 Phase 2.5**:A 类 sim 工作(SAC/TD3 pilot、teacher ablation、protocol freeze、failure decomp)与硬件决策解耦,可并行启动。
- **Phase 3.5 / Phase H 是 conditional**:仅在 Phase 2.5 = buy-hardware 时触发。
- **Effort 单位**:person-week,单人全职估算;半职请乘 2。

## Phases

### Phase 1: Repository & Paper Discovery  (effort: 1 day | risk: low | status: complete)
- [x] Understand user intent
- [x] Identify top-level repository structure
- [x] Create planning files and capture initial findings
- [x] Read the current README/paper structure and map existing evidence blocks
- [x] Confirm whether off-policy code paths and requested contract tests already exist
- **Deliverable:** `findings.md` Research Findings section (完成)

### Phase 2: Plan Audit & Narrative Lock  (effort: 2 days | risk: medium | status: complete)
- [x] Translate the user's sprint sketch into a phase-gated plan
- [x] Identify must-have vs nice-to-have items for Q2-class submission
- [x] Pre-register 3 narrative branches (A / B / C) with candidate abstract drafts
- [x] Define branch-switch criteria based on Phase 3 Sprint 1 pilot outputs
- **Deliverable:** `narrative_branches.md` + Branch A selected 2026-04-20

### Phase 2.5: Hardware Decision Gate  (effort: 1 week | risk: high | status: complete)
- **Decision: No-hardware** (2026-04-22)
- Venue ceiling: **Q3 upper / Q2 marginal**
- Hard bonus path: **named method (SG-VI) + diagnostic tool (SCI)** already landed; cross-sim transfer 可选做 1.5-2 周额外加分
- Phase 3.5 / Phase H: **cancelled**
- **Deliverable:** 本 decision record

### Phase 3: Sim-only Experiment Execution  (effort: 4–6 weeks | risk: medium | status: complete)
_A-category work. 可与 Phase 2.5 并行启动。_

- [x] Sprint 0: PPO-only 200k 复现 + `protocol_freeze.md`
  → Deliverable: 复现 JSON + 3 个 regression tests(force_jam consecutive、blocked_contact separate reason、ppo-only disables auxiliary stages)passing
- [x] Sprint 1: SAC / TD3 训练入口 + cross-family pilot
  → Deliverable: `src/vi_full/three_dof_cross_family_baselines.py` + `scripts/experiments/run_3dof_cross_family_pilot.py` + `src/vi_full/three_dof_cross_family_pilot_report.py` + `scripts/experiments/export_3dof_cross_family_pilot_report.py`;27 runs(3 methods × 3 seeds × 3 budgets);2 张内部图(success vs budget、first_contact_step vs budget)
  → 2026-04-20 17:05 Asia/Shanghai full pilot completed / Branch A evidence: `outputs/pilot_report/three_dof_cross_family_pilot_report.json` 已汇总 9/9 method-budget chunks，missing=0；已完成 `ppo_no_bc@50k/100k/200k`、`sac_no_bc@50k/100k/200k`、`td3_no_bc@50k/100k/200k`；三族 pure-RL 仍为 `success_rate=0`、`mean_contact_steps=0`、`mean_first_contact_step=64`，支持 Branch A（pure RL across families cannot reach useful contact）
- [x] Sprint 1-End: 按预注册 A/B/C 选定 narrative 分支
  → Deliverable: Branch A locked in `narrative_branches.md` 2026-04-20
- [x] Sprint 2A: Branch-A confirm benchmark pack
  → Deliverable: confirm report + CSV + contact gate table + distance vs budget figure;8 tests passing
- [x] Sprint 2B: Anchor-integrated evidence matrix + strict review
  → Deliverable: evidence matrix (pure-RL × demo-supported anchors) + JSON/CSV/MD/PNG/PDF artifacts;code review passed (4 Important fixes applied);52 tests passing
- [x] Sprint 2 main table: 三层主表 + learning curves
  → Deliverable: reviewer-facing 三层 claim-control 主表 + contact-gate matrix + pure-RL budget-curve figure;nominal-only pure-RL rows 与 five-profile benchmark anchors 保持 separate evidence contracts
- [x] Sprint 3: Teacher mini-ablation kickoff,冻结 teacher support quality × demo rollout budget 小边界
  → Kickoff artifact: `outputs/sprint3_teacher_mini_ablation/sprint3_teacher_mini_ablation_kickoff.{json,md}`
  → Frozen boundary: 4 条件 teacher support quality x demo rollout budget;固定 `bc_pretrain_steps=32`、`total_timesteps=128`、BC-to-PPO init、five-profile evaluation、Sprint 2 claim-control metrics + SCI/support-cell coverage
  → Excluded from kickoff: BC pretrain-step sweep、policy-init sweep、teacher/no-teacher pure-RL control、完整 motion-rule × impedance-rule appendix sweep
- [x] Sprint 4A: Clearance shift 鲁棒性扫描
  → Deliverable: `outputs/sprint4_clearance_shift/sprint4_clearance_shift.{json,csv,md}`; pure-clearance `easy/nominal/hard` ladder × selected demo-supported suites;当前仓库无持久化 checkpoint,因此采用 train-once / eval-many-profile 合同
  → 2026-04-23 result snapshot: `BC-only (stable 32/32)` 在 hard ladder 仍为 `success_rate=1.0`; `DAPG-lite` 降至 `success_rate=0.768`, `jam_rate=0.05`; `BC -> PPO` 与 `Fixed-impedance RL (stable BC 32/32)` 在 hard ladder 保持约 `0.8` success 且 `jam_rate=0`
- **Depends on:** Phase 2 narrative lock
- **Does NOT depend on:** Phase 2.5

### Phase 3.5: CANCELLED (no-hardware decision 2026-04-22)
### Phase H: CANCELLED (no-hardware decision 2026-04-22)

### Phase 4: Writing & Artifact Strategy  (effort: 2-3 weeks | risk: medium | status: in_progress)
- [x] Contribution reframing: findings-only -> `propose + show` (>=1 constructive)
  -> Deliverable: 4 contributions, at least 1 named method / diagnostic tool
  -> 2026-04-21: SG-VI / SCI landed in `paper/main.tex`, `README.md`, and `src/vi_full/three_dof_support_metrics.py`
- [x] Abstract/Intro rewrite: reflect Branch A + SG-VI + cross-family evidence
  -> Deliverable: updated abstract and intro text
  -> 2026-04-23: abstract and introduction now carry Branch A, SG-VI / SCI, cross-family negative evidence, and Sprint 4A framing
- [x] Main text restructure: 4.1 cross-family / 4.2 learning curves / 4.3 failure decomp / 4.4 high-friction mechanics / 4.5 teacher ablation / 4.6 clearance shift / 4.7 real-robot(if any)
  -> Deliverable: updated `paper/main.tex` scaffolding
  -> 2026-04-23: experiments/discussion now include cross-family, teacher-boundary, clearance-shift, and appendix protocol-map alignment
- [ ] Figure/table pipeline extension
  -> Deliverable: failure heatmap, teacher 2x2x2, real-sim parity(if any) exporters
- [x] Limitations convergence: keep the no-hardware / sim-only boundary explicit until hardware exists
  -> Deliverable: rewritten Discussion / Limitations
  -> 2026-04-23: Discussion now states benchmark-local, no-hardware, proxy-study, and no-checkpoint boundaries explicitly
- **Depends on:** Phase 3 complete(+ Phase H if hardware path)

### Phase 5: Delivery  (effort: 1 week | risk: low | status: pending)
- [ ] README / runner CLI 收口
- [ ] Contract smoke tests + teacher serialization tests
- [ ] Submission package(paper PDF + supplementary + repo snapshot + anonymization)
- **Depends on:** Phase 4 complete
- **Deliverable:** submission-ready package + cover letter draft

## Key Questions — Resolved (2026-04-22)
1. **Phase 2.5 → No-hardware**。Venue ceiling: Q3 upper / Q2 marginal。Phase 3.5/H cancelled。
2. ~~真机学术折扣~~ N/A。
3. **Sprint 3 kickoff boundary → 4 条件 teacher support quality x demo rollout budget**；先冻结小矩阵，不启动大 sweep。
4. **Hard bonus path → SG-VI + SCI already landed**; cross-sim transfer 为可选额外加分项。
5. **Compute → GPU 可用**,训练可加速。

## Decisions Made

### Meta / Tooling Decisions
| Decision | Rationale |
|----------|-----------|
| 使用 `planning-with-files` 文件化规划 | 复杂多阶段研究任务 |
| 搜索工具从 `rg` 切换到 PowerShell `Select-String` | `rg.exe` Access is denied |
| Planning files 放在 `vi-insertion-only-sim/` 项目根 | 外层目录非 git repo |
| 当前阶段只写 planning files,不改训练代码 | 本轮是规划,不是实施 |

### Research / Scope Decisions
| Decision | Rationale |
|----------|-----------|
| 目标从"更有说服力的 benchmark paper"升级为"冲 Q2 非 OA,硬件允许则冲 Q1" | 2026-04-18 对话锐评;narrow-claim 定位对 Q2 天花板不足 |
| 新增 Phase 2.5 Hardware Decision Gate 为独立阶段 | 硬件决策是当前真正 blocking 的关键决策,不应埋在 narrative lock 里 |
| Phase 3(sim-only A 类)与 Phase 2.5 并行,不相互 block | ~70% sim 端工作与硬件决策解耦,不应因"等决定"停手 |
| 新增 Phase 3.5 Sim-to-Real Scaffolding 为 conditional phase | 买硬件后才触发;提前标记避免硬件到货后才仓促补 DR / adapter |
| 新增 Phase H Hardware Integration 为 conditional phase | 将真机 experiment 从 sim 流程独立,避免耦合 |
| Sprint 1 标记高工程风险(SAC/TD3 代码不存在) | findings.md 已确认 `src/` 无 off-policy 入口 |
| Sprint 3 teacher ablation 先冻结 4 条件小边界 | 2026-04-23 kickoff 将目标收敛为 teacher support quality x demo rollout budget，避免直接扩成大 sweep |
| `recoverable_contact_entry_rate` 降级为 event counter | 用户明确偏好;不做 learning-curve 主角 |
| 论文改稿视为"重排骨架 + 插入 evidence block" | 现有正文/appendix 挂点清晰 |
| Contribution 重构要求至少 1 条 `we propose` | 当前 4 条全是 `we show`,Q2 通常需要 constructive contribution |
| Phase 2.5 = no-hardware (2026-04-22) | 用户决策;venue ceiling 降至 Q3 upper / Q2 marginal;Phase 3.5/H cancelled |
| Sprint 3 kickoff 小矩阵 (2026-04-23) | support-rich/support-poor teacher × few/many demo rollouts；固定 BC steps、PPO budget、policy init 与五 profile |
| Compute: GPU 可用 (2026-04-22) | Sprint 2 main table 训练可用 GPU 加速 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| `git status` 在 `F:\edge download\learning` 失败:not a git repository | 1 | 确认实际仓库根目录为 `F:\edge download\learning\vi-insertion-only-sim` |
| `rg.exe` 在当前环境执行失败:Access is denied | 1 | 放弃重复使用 `rg`,改为 PowerShell `Select-String` |
| PowerShell 自动取 teacher spec 上下文时匹配到多个定义,导致行号运算报错 | 1 | 改为更窄的单点检索,不重复同样的上下文脚本 |

## Notes
- 本次任务以规划和证据组织为主,不默认展开代码重构。
- 后续每完成一个 Phase,都要回写 `findings.md` 和 `progress.md`。
- 若发现用户设想与仓库现状冲突,需要明确标出约束而不是默认可行。
- **Phase 3 不等 Phase 2.5**:硬件决策不 block A 类 sim 工作。
- **Phase 3.5 是 conditional**:仅在 Phase 2.5 = buy-hardware 后触发;提前设计避免硬件到货后补 DR 失败。
- **Q1 升级路径**:仅在 Phase 2.5 = Rizon 4s 且 Phase H 完成 Flexiv primitive 对照时才启动 Q1 投稿路线。
- Effort 估算:person-week,单人全职;半职乘 2。
## Sprint 0 Execution Note
- `protocol_freeze.md` created and frozen as PPO-only audit contract
- 3 regression tests landed (protocol-freeze test red-then-green)
- `outputs/three_dof_ppo_large_budget_ablation_200k_repro.json` generated
- 200k reproduction result: both PPO-only conditions are `success=0, contact_steps=0, first_contact=64, peak_force=0`
## Sprint 1 Scaffolding Note (2026-04-18)
- [x] Add `src/vi_full/three_dof_cross_family_baselines.py` as the minimal pure-RL training entry for `ppo_no_bc`, `sac_no_bc`, and `td3_no_bc`
- [x] Add `scripts/experiments/run_3dof_cross_family_pilot.py` with default `50k/100k/200k` budgets and nominal-only pilot profiles
- [x] Add contract tests for the new registry, TD3 action-noise path, and runner JSON grid
- [x] Run a real smoke artifact at `outputs/three_dof_cross_family_pilot_smoke.json`
- [x] Sprint 1 milestone completed: execute the full method-budget pilot grid and generate the two internal pilot figures

## Sprint 2A: Branch-A Confirm Benchmark Pack

- [x] Sprint 1 full pilot completed: 9/9 chunks.
- [x] Selected narrative branch: A.
- [x] No pure-RL method reached contact under the frozen 3DoF contract.
- [x] SAC shows strongest terminal-distance proxy but still zero-contact.
- [x] Export paper-facing confirm JSON/CSV/table/figure artifacts under `outputs/cross_family_confirm/`.
- [x] Add contract tests for the confirm report module and CLI exporter.

Next Sprint 2 direction: confirm benchmark should compare Branch-A pure-RL failure against
demo-supported anchors, not oversell SAC.

## Sprint 2B Execution Note (2026-04-21)
- Added a dedicated reviewer-facing evidence-matrix layer instead of overloading the confirm report.
- New implementation/export entrypoints:
  - `src/vi_full/three_dof_evidence_matrix.py`
  - `scripts/experiments/export_3dof_evidence_matrix.py`
- Frozen matrix roster:
  - pure RL: `ppo_no_bc`, `sac_no_bc`, `td3_no_bc`
  - anchors: `bc_only_stable_r32_p32`, `repaired_mainline_bc_to_ppo`, `dapg_lite_repaired_mainline`, `fixed_impedance_rl_stable_r32_p32`
- Mixed-contract rule is now explicit in the artifacts:
  - pure-RL rows stay tagged as `nominal-only pilot`
  - anchor rows stay tagged as `five-profile benchmark`
  - the matrix allows contact-gate contrast, not leaderboard ranking
- 2026-04-22 hardening close-out:
  - confirm aggregation now fail-fast on missing/null `jam_rate` and `mean_peak_contact_force_n` instead of silently folding them into `0.0`
  - contract regressions cover module + CLI failure paths for confirm/evidence exporters
  - reviewer-facing confirm/evidence artifacts were re-exported after the contract tightened

## Sprint 2 Main Table / Figures Close-out (2026-04-23)
- Sprint 2 reviewer-facing main table and budget-curve figure are complete.
- Closed artifacts:
  - `outputs/evidence_matrix/three_dof_sprint2_main_table.{json,csv,md}`
  - `outputs/evidence_matrix/three_dof_evidence_matrix.{json,csv,md}`
  - `outputs/evidence_matrix/three_dof_contact_gate_matrix.{png,pdf}`
  - `outputs/cross_family_confirm/three_dof_cross_family_confirm_learning_curve_summary.{png,pdf}`
- Claim boundary:
  - the Sprint 2 table is a three-layer reviewer-facing claim-control table, not a mixed-contract leaderboard
  - `SAC w/o BC` is retained only as a zero-contact distance proxy under the nominal-only confirm contract
  - row-level provenance stays tied to the direct confirm JSON or schema2 benchmark JSON inputs
- Determinism:
  - confirm export uses the frozen pilot source timestamp
  - evidence-matrix and Sprint 2 table exports have deterministic rerun coverage
- Final close-out review covered commits `a272ff8..3af22a4` plus `81c9345`.
- Workspace boundary: existing dirty paths `pyproject.toml`, `src/vi_full/three_dof_benchmark.py`, `conftest.py`, and `docs/superpowers/` are SCI guardrails / workspace residue and were not used in the Sprint 2 table/figures closure decision.
