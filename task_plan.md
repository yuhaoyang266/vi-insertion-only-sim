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
Phase 3 Sprint 1

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

### Phase 2: Plan Audit & Narrative Lock  (effort: 2 days | risk: medium | status: in_progress)
- [x] Translate the user's sprint sketch into a phase-gated plan
- [x] Identify must-have vs nice-to-have items for Q2-class submission
- [ ] Pre-register 3 narrative branches (A / B / C) with candidate abstract drafts
- [ ] Define branch-switch criteria based on Phase 3 Sprint 1 pilot outputs
- **Deliverable:** `narrative_branches.md`,包含 3 段候选 abstract + pilot-to-branch 选择规则

### Phase 2.5: Hardware Decision Gate  (effort: 1 week | risk: high | status: pending)
- [ ] 确认设备预算档位(10w / 20w / 40w / 60w+ RMB)
- [ ] 对接 Flexiv / Franka 学术渠道,获取折扣与到货时间
- [ ] 在 {Rizon 4s, Franka Research 3, 二手 Panda, no-hardware} 中 pick one
- [ ] 锁定 target venue tier(Q2 / Q1 / Q3-upper fallback),写入 Goal
- **Blocks:** Phase H 全部,Phase 3.5 方向校准
- **Does NOT block:** Phase 3(sim-only A 类)
- **Deliverable:** `hardware_decision.md` {platform, budget, delivery-window, venue-tier commitment}

### Phase 3: Sim-only Experiment Execution  (effort: 4–6 weeks | risk: medium | status: in_progress)
_A-category work. 可与 Phase 2.5 并行启动。_

- [x] Sprint 0: PPO-only 200k 复现 + `protocol_freeze.md`
  → Deliverable: 复现 JSON + 3 个 regression tests(force_jam consecutive、blocked_contact separate reason、ppo-only disables auxiliary stages)passing
- [x] Sprint 1: SAC / TD3 训练入口 + cross-family pilot
  → Deliverable: `src/vi_full/three_dof_cross_family_baselines.py` + `scripts/experiments/run_3dof_cross_family_pilot.py` + `src/vi_full/three_dof_cross_family_pilot_report.py` + `scripts/experiments/export_3dof_cross_family_pilot_report.py`;27 runs(3 methods × 3 seeds × 3 budgets);2 张内部图(success vs budget、first_contact_step vs budget)
  → 2026-04-20 17:05 Asia/Shanghai full pilot completed / Branch A evidence: `outputs/pilot_report/three_dof_cross_family_pilot_report.json` 已汇总 9/9 method-budget chunks，missing=0；已完成 `ppo_no_bc@50k/100k/200k`、`sac_no_bc@50k/100k/200k`、`td3_no_bc@50k/100k/200k`；三族 pure-RL 仍为 `success_rate=0`、`mean_contact_steps=0`、`mean_first_contact_step=64`，支持 Branch A（pure RL across families cannot reach useful contact）
- [ ] Sprint 1-End: 按预注册 A/B/C 选定 narrative 分支
  → Deliverable: 1-page outline 钉死已选分支;同步修改 abstract/intro 占位
- [ ] Sprint 2: Cross-family main table + learning curves(confirm benchmark)
  → Deliverable: 三层主表(performance / failure / mechanics)+ failure heatmap + learning-curve figure;5 methods × 5 seeds × 1–2 budgets × 5 profiles
- [ ] Sprint 3: Teacher mini-ablation,扩展 orthogonal 维度
  → Deliverable: variable/fixed teacher × clean/noisy demo 的 2×2×2 表;directional evidence 锁定 teacher-coupling claim
- [ ] Sprint 4A: Clearance shift 鲁棒性扫描
  → Deliverable: easy/nominal/hard clearance × best 3–4 methods;复用 checkpoint,评估为主
- **Depends on:** Phase 2 narrative lock
- **Does NOT depend on:** Phase 2.5

### Phase 3.5: Sim-to-Real Scaffolding  (conditional: hardware path | effort: 2–3 weeks | risk: medium | status: pending)
_B-category preventive refactor. Phase 2.5 锁定平台方向后立即启动;可与 Phase 3 并行。_

- [ ] Domain randomization 层(friction / mass / damping / latency / sensor noise),范围按目标平台标称参数校准
  → Deliverable: `domain_randomization.yaml` + ablation 证明 DR 下 policy 仍能训练(nominal success 下降 < 10%)
- [ ] Action adapter 抽象:policy output → {sim / Rizon / Franka} pluggable backend
  → Deliverable: `action_adapter.py` + 单元测试;单位/维度/clip 对齐
- [ ] Obs source 抽象:ground-truth / noisy-estimate / vision-stub
  → Deliverable: `obs_source.py` + noise injection 配置;支持带噪 hole pose 的 sim 等价训练
- [ ] Metric source 统一:peak_force / contact_work source-agnostic
  → Deliverable: sim 端 regression tests 重构后全通过;real 端(FT sensor / 关节 FSR)接口就绪
- [ ] Control-rate mismatch rollout 选项
  → Deliverable: retimed rollout,匹配目标平台有效 policy rate
- [ ] Safety envelope:force / position / velocity hard clips
  → Deliverable: safety-aware 训练产物 + envelope 参数表
- **Depends on:** Phase 2.5 = hardware path
- **Parallel with:** Phase 3

### Phase H: Hardware Integration & Real Experiments  (conditional: hardware path | effort: 5–8 weeks | risk: high | status: pending)
- [ ] RDK / ROS 2 driver bridge(按选定平台)
- [ ] Policy deployment runtime(checkpoint load、realtime inference、safety monitor)
- [ ] Trial runner(peg/hole reset workflow、episode control、video sync)
- [ ] Real-robot 评估矩阵:2–3 clearance × 2–3 methods × 20+ trials/condition
- [ ] Sim-to-real gap quantitative analysis(success / force / timing delta)
- [ ] (Rizon only) Flexiv 官方 primitive baseline 对照实验
- **Depends on:** Phase 3.5 完成 + 硬件实物到货
- **Deliverable:** real-robot 章节 + 表 + 图 + supplementary video

### Phase 4: Writing & Artifact Strategy  (effort: 2–3 weeks | risk: medium | status: pending)
- [ ] Contribution 重构:findings-only → `propose + show`(≥1 constructive)
  → Deliverable: 4 条 contribution,至少 1 条提出 named method / diagnostic tool
- [ ] 主文结构重排:4.1 cross-family / 4.2 learning curves / 4.3 failure decomp / 4.4 high-friction mechanics / 4.5 teacher ablation / 4.6 clearance shift / 4.7 real-robot(若有)
  → Deliverable: 更新后的 `paper/main.tex` scaffolding
- [ ] Figure/table pipeline 扩展
  → Deliverable: failure heatmap、teacher 2×2×2、real-sim parity(若有)的 exporter
- [ ] Limitations 收敛(硬件完成后去掉 sim-only 的自我贬低)
  → Deliverable: 改写后的 Discussion / Limitations
- **Depends on:** Phase 3 complete(+ Phase H if hardware path)

### Phase 5: Delivery  (effort: 1 week | risk: low | status: pending)
- [ ] README / runner CLI 收口
- [ ] Contract smoke tests + teacher serialization tests
- [ ] Submission package(paper PDF + supplementary + repo snapshot + anonymization)
- **Depends on:** Phase 4 complete
- **Deliverable:** submission-ready package + cover letter draft

## Key Questions
1. Phase 2.5 硬件倾向:Rizon 4s / Franka Research 3 / 二手 Panda / no-hardware?(决定 venue tier 与 Phase 3.5/H 是否触发)
2. 若选真机,是否有学术折扣或合作渠道?预算上限与到货窗口?
3. Sprint 3 teacher ablation 的 orthogonal 维度选 demo quality(clean/noisy)还是 demo quantity(少量/大量)?
4. 若 Phase 2.5 = no-hardware,硬加分路径选 cross-simulator transfer 还是 named method + diagnostic tool?

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
| Sprint 3 teacher ablation 扩展 orthogonal 维度(非仅 fixed/variable) | 当前 2×2 是 motion×impedance,不是真正的 teacher quality/quantity |
| `recoverable_contact_entry_rate` 降级为 event counter | 用户明确偏好;不做 learning-curve 主角 |
| 论文改稿视为"重排骨架 + 插入 evidence block" | 现有正文/appendix 挂点清晰 |
| Contribution 重构要求至少 1 条 `we propose` | 当前 4 条全是 `we show`,Q2 通常需要 constructive contribution |

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
- `protocol_freeze.md` 宸插垱寤?骞跺喕缁?PPO-only audit contract
- 3 涓?regression tests 宸茶惤鍦?鍏朵腑 protocol-freeze test 鍏堢孩鍚庣豢
- `outputs/three_dof_ppo_large_budget_ablation_200k_repro.json` 宸茬敓鎴?
- 200k reproduction 缁撴灉锛?2 涓?PPO-only conditions 鍧囦负 `success=0`, `contact_steps=0`, `first_contact=64`, `peak_force=0`
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
