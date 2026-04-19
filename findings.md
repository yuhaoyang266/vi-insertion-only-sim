# Findings & Decisions

## Requirements
- 用户希望提升项目/论文上限，核心不是大重构，而是通过更强的实验叙事和证据设计提高投稿竞争力。
- 用户已经给出一个 6-sprint 草案，重点包括：
- 先稳复现 Appendix B 中 PPO-only 的关键负结果，作为负证据地基。
- 对 SAC/TD3 做很薄的 off-policy sanity，再在 Sprint 1 做跨算法家族 pilot。
- 在 pilot 前预注册 3 个 narrative branches，避免结果出来后临时编故事。
- 将 teacher study 升级为二维 mini-ablation，而不是只做 fixed vs variable teacher。
- 强制加入一个“突破边界”的 evidence block，优先 hardware demo，否则 cross-simulator transfer。
- 代码侧只做轻量收口，不做 env 四层大拆或大规模 registry/packaging 工程。

## Research Findings
- 当前工作区外层 `F:\edge download\learning` 不是 git repo，实际项目在 `F:\edge download\learning\vi-insertion-only-sim`。
- 项目顶层包含 `paper/`, `figures/`, `docs/`, `src/`, `scripts/`, `tests/`, `artifacts/`，说明论文、实验脚本和代码资产都在同一仓库内，适合做 repo-aware planning。
- 用户的计划已经具有较强 reviewer-facing 导向，尤其强调：
- broader off-policy comparison
- teacher prior 与 support coverage 的解耦
- external-validity/boundary-breaking evidence
- `README.md` 当前把论文主张明确限定为：
- “demonstration support is the cleanest gate into useful contact”
- variable impedance 的优势主要是 localized high-friction load/work advantage
- 这说明现稿更像“teacher-coupled benchmark-local finding”，还没有自然长成更高上限的 benchmark methodology/evidence protocol 论文。
- `README` 的 evidence map 表明仓库已经有以下资产：
- main five-seed benchmark
- appendix teacher/termination package
- factorized support/reset/BC/PPO diagnostics
- PPO large-budget audit
- tuned fixed-impedance sweep
- pose-perturbation proxy
- `README` 已经区分 `jam_rate` 与 `documented_force_jam_rate`，说明 failure decomposition 的语义框架已经有一部分基础设施。
- `paper/main.tex` 当前摘要、贡献和讨论都把主张压在一个很窄的范围内：
- PPO-only 50k--200k audit 仍是 non-contact failure
- BC support 是 useful contact 的关键 gate
- variable impedance 的价值主要体现在 localized high-friction load/work
- claim 明确声明为 benchmark-local、teacher-coupled，而不是 general algorithm ranking
- 正文和 limitations 已经主动承认：
- broader off-policy baselines（如 SAC）未覆盖
- BC demonstrations 由 variable-impedance teacher 生成，teacher prior 尚未解耦
- 环境仍是 sim-only、3DoF、analytical contact model
- 当前仓库已经有 appendix teacher block，并且是一个现成的 2x2 设计：
- `teacher_variable_variable__repaired_mainline`
- `teacher_variable_fixed__repaired_mainline`
- `teacher_pose_variable__repaired_mainline`
- `teacher_pose_fixed__repaired_mainline`
- 这个 2x2 更接近 `motion rule × impedance rule`，不是用户现在想要的 `teacher type × demo quality/quantity`。
- `src/vi_full/three_dof_policies.py` 中 teacher spec registry 明确写死了这 4 个 preset：
- `teacher_variable_variable`: `contact_aware_variable_motion × contact_aware_variable_impedance`
- `teacher_variable_fixed`: `contact_aware_variable_motion × fixed`
- `teacher_pose_variable`: `pose_feedback × contact_aware_variable_impedance`
- `teacher_pose_fixed`: `pose_feedback × fixed`
- `src/*.py` 中没有 `SAC` 或 `TD3` 的 Python 代码匹配，说明 off-policy family pilot 目前没有现成实现入口。
- 用户列出的 3 个底线测试名在当前 `tests/*.py` 中没有匹配，表明这些 contract tests 需要新建或重命名，而不是简单继承。
- 当前正文 section 骨架是：
- Main Benchmark
- Factorized Causal Study
- High-Friction Role of Variable Impedance
- Supplementary Budget Stress Test After BC Support Is Restored
- Pose-Perturbation Scope Stress Test
- 再加 Discussion/Conclusion 和 appendix audits
- 当前主表 `paper/main.tex:456-464` 的列仍是：
- `Baseline`
- `High fric.`
- `Noisy force`
- `Mean success`
- `Jam`
- `Final dist.`
- `Peak force`
- `Contact steps`
- 这与用户建议升级成 `performance / failure / mechanics` 三层主表是直接对应的，可在现有表导出逻辑上扩展而不必完全推倒。

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| 使用 `planning-with-files` 的文件化规划方式 | 任务明显属于复杂多阶段研究规划 |
| 先把用户草案转成 repo-aware 执行计划，而不是直接“优化措辞” | 需要用仓库和论文现状校验哪些 sprint 能落地 |
| 暂不把 `recoverable_contact_entry_rate` 视为默认中心指标 | 用户已明确更偏向让它作为 failure/reachability 事件计数器 |
| 搜索工具从 `rg` 切换到 PowerShell `Select-String` | 当前环境调用 `rg.exe` 返回 Access is denied，不能重复同样失败动作 |
| 将 Sprint 3 视为“扩展现有 teacher block”而非从零开始 | 仓库已具备 2x2 teacher registry、appendix table/figure 和相关测试支撑 |
| 将 Sprint 1 标记为高工程风险阶段 | 现有代码只暴露 PPO 训练路径，off-policy pilot 不是零成本增量 |
| 将论文改稿视为“重排已有 section 骨架 + 插入新 evidence block” | 当前主文和 appendix 已有清晰挂点，不需要从空白目录重建 |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| 初始 cwd 不是 git repo | 将项目根切换到 `vi-insertion-only-sim` 并在该目录创建 planning files |
| `rg.exe` 无法执行（Access is denied） | 改用 PowerShell 原生命令 `Get-ChildItem` + `Select-String` 继续代码/论文检索 |
| PowerShell 读取 teacher spec 上下文时命中了多个函数定义导致行号为数组 | 放弃一次性自动取上下文，改用更定点的读取方式 |

## Resources
- Project root: `F:\edge download\learning\vi-insertion-only-sim`
- Planning skill: `C:\Users\Windows\.codex\skills\planning-with-files\SKILL.md`
- User draft plan: current conversation content

## Paper Ceiling Diagnosis (per 2026-04-18 discussion)

### Current trajectory ceiling
- **Sim-only + 3DoF 单任务 + 4 条 observational contribution**:现状投稿上限大约在 Q3 上游,Q2 非 OA 边缘;单凭 Sprint 0-5 执行到位,不足以自动推上 Q2。
- 论文 abstract 自称 "simulation-only" + narrative 自称 "benchmark-local and teacher-coupled" 是 **defensive framing**,对 T-RO / T-ASE / T-MECH / MSSP 档 reviewer 是明显减分信号。

### Two hard gaps blocking Q2
1. **No real-hardware evidence**:接触任务的 sim-only 论文在 Q2 非 OA 档的第一刀 reject 理由;Sprint 0-5 完全没有 real-robot / cross-simulator / physical transfer 任何一种。
2. **Zero constructive contribution**:`paper/main.tex:106-118` 的 4 条 contributions 全部以 "we provide / we show" 起头,无 "we propose"。Q2 非 OA 通常要求至少 1 条可被引用、可被复用的贡献(named method / framework / diagnostic tool)。

### Three hard upgrade paths (必选一条,最好两条)
| Path | ROI | 时间成本 | 说明 |
|------|-----|----------|------|
| A. Real-hardware validation | 最高 | 5–8 周(+硬件 4–10 周到货) | 触发 Phase 2.5 / 3.5 / H;narrative 定位为 "controlled-fidelity existence proof",不卖 sim-to-real zero-gap |
| B. Cross-simulator transfer | 中 | 1.5–2 周 | MuJoCo ↔ Isaac Gym / PyBullet;单人可做,回击 "sim artifact" 质疑 |
| C. Named method + diagnostic tool | 低-中 | 3–5 天 | 不加实验,把 BC→PPO + variable impedance + factorized support analysis 包装成框架(e.g. Support-Gated VI Learning),再抽一个 metric(e.g. Support Coverage Index) |

### Hardware-to-code coupling classification
- **A 类(~70%,硬件无关)**:PPO-only 复现、SAC/TD3 pilot、3 个 contract tests、teacher 2×2 扩展、failure decomp 升格、clearance shift、learning curve —— 现在就能启动,不 block 于 Phase 2.5。
- **B 类(~20%,硬件方向定了就启动)**:Domain randomization、action adapter 抽象、obs source 抽象、metric source 统一、control-rate mismatch、safety envelope —— Phase 3.5 的全部内容;不等硬件到货,方向定了就动。
- **C 类(~10%,等硬件到货)**:RDK/ROS 2 bridge、deployment runtime、trial runner、real-sim gap 量化、Flexiv primitive 对照 —— Phase H 的全部内容。

### Narrative branches (Phase 2 pre-register)
| Branch | Trigger (Sprint 1 pilot result) | Narrative pivot |
|--------|---------------------------------|-----------------|
| A | Pure RL across families 都进不了 useful contact | 保持 "demonstration support is the gate";Q2 需靠硬件证据或 named method 补 |
| B | 某 off-policy family 能进接触,但低预算明显差于 demo-supported | 主推 "sample-efficiency differentiation under teacher-coupled support" |
| C | Off-policy family 已逼近 demo-supported | 主文必须转写为 benchmark methodology,不能再卖 support superiority |

**写法**:三份 abstract 草稿提前写在 `narrative_branches.md`,Sprint 1 结束当天选分支,不事后编故事。

### Timeline inflation
- 原用户草案 5–8 周:过于乐观(60–75 training runs + iteration tax)。
- **No-hardware path**:现实 10–14 周。
- **Franka-class hardware path**:现实 15–22 周(加 Phase 3.5 + Phase H)。
- **Rizon 4s + Flexiv primitive baseline(Q1 路径)**:现实 18–26 周。
- Effort 估算按单人全职;半职乘 2。

### Contribution rewrite target
- 当前 4 条 contributions 要求改为至少 1 条 constructive + 3 条 observational 的结构。
- Named method 候选:**Support-Gated Variable-Impedance Learning** (SG-VI / SGVIL);组件 = BC→PPO + variable impedance action space + factorized support analysis。
- Diagnostic metric 候选:**Support Coverage Index** = demo state-action 对 policy rollout state-action 的覆盖率;作为 reusable 指标写入 Phase 4。

## Visual/Browser Findings
- 本轮尚未查看图片、PDF 或网页内容。
- 2026-04-18 通过 WebFetch / fetch MCP 读取 `github.com/Synria-Robotics` 组织页及 Alicia-M-SDK / RoboCore / Alicia-D-SDK README,用于硬件候选评估(见 Paper Ceiling Diagnosis 中 Hardware candidate assessment)。

---
*Update this file after every 2 view/browser/search operations*
*This prevents visual information from being lost*

## Sprint 1 Pre-Pilot Contract Tightening
- Off-policy defaults were tightened before the formal 27-run grid:
  - `learning_starts` changed from `0` to `1024`
  - `buffer_size` changed from `100000` to `200000`
- The chosen warmup rule is `max(1000, max_episode_steps * n_envs * 16)`, which evaluates to `1024` under the current `64`-step, single-env Sprint 1 pilot contract
- This is a reviewer-facing fairness fix, not an opportunistic boost:
  - it avoids undercutting SAC/TD3 with a `learning_starts=0` setup that is known to be brittle at low budgets
  - it avoids replay FIFO churn before the `200k` pilot budget completes
- `run_3dof_cross_family_pilot.py` now exposes `--train-profile` so the current `nominal`-train assumption is explicit rather than hardcoded
- `action_noise_std` is now treated as TD3-only; non-TD3 baselines fail fast instead of silently swallowing the field
- `three_dof_cross_family_baselines.py` no longer imports the private `_default_3dof_train_reset_config`; the reset factory is promoted to the public `build_3dof_default_train_reset_config()`

## Sprint 1 Pilot Execution Snapshot (2026-04-19 17:50 Asia/Shanghai)
- `outputs/pilot_report/three_dof_cross_family_pilot_report.json` now acts as the live progress ledger for Sprint 1.
- Report/export layer is in place:
  - `src/vi_full/three_dof_cross_family_pilot_report.py`
  - `scripts/experiments/export_3dof_cross_family_pilot_report.py`
  - exported figures:
    - `outputs/pilot_report/three_dof_cross_family_pilot_success_vs_budget.{pdf,png}`
    - `outputs/pilot_report/three_dof_cross_family_pilot_first_contact_step_vs_budget.{pdf,png}`
- Completed pilot chunks: 6 / 9
  - `ppo_no_bc@50k/100k/200k`
  - `sac_no_bc@50k/100k`
  - `td3_no_bc@50k`
- In-flight pilot chunks at the time of this snapshot:
  - `sac_no_bc@200k`
  - `td3_no_bc@100k`
  - `td3_no_bc@200k`
- Current partial trend:
  - all completed pure-RL chunks still show `success_rate=0`, `mean_first_contact_step=64`, and `mean_contact_steps=0`
  - the observable separation so far is **distance-to-contact**, not successful insertion
  - `sac_no_bc` is the strongest partial family on this proxy:
    - `23.27 mm @50k`
    - `17.58 mm @100k`
  - `ppo_no_bc` improves with budget but remains worse on the same proxy:
    - `31.02 mm @50k`
    - `29.47 mm @100k`
    - `25.48 mm @200k`
  - `td3_no_bc@50k` currently looks PPO-like rather than SAC-like:
    - `30.78 mm`, still no contact
- Narrative implication if the remaining 3 chunks stay zero-contact:
  - Sprint 1 will still support Branch A ("pure RL across families cannot reach useful contact")
  - the weaker but still useful nuance is that off-policy training may shrink the terminal distance without crossing the contact gate
