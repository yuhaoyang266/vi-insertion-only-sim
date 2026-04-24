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

## Milestone 3 Engineering Trust Planning (2026-04-25)

- Milestone 2 Paper-Facing Reproducibility is treated as complete for the next work slice.
- The user does not want local LaTeX/PDF deployment to be a blocking workflow requirement.
- Milestone 3 should therefore close on no-training Python checks, source/prose audits, import-boundary checks, reviewer smoke checks, and `build_paper_assets.py --check`; it should not require `pdflatex`, `bibtex`, `latexmk`, or `build_paper_pdf.py`.
- Current Task 10 baseline is mostly implemented: `src/vi_full/__init__.py` exposes only `__version__`, and `tests/test_import_boundaries.py` exists.
- Current Task 11 baseline is not implemented: `.github/` does not exist.
- Current Task 13 baseline is not implemented: `tests/test_paper_claim_boundaries.py` does not exist.
- Recommended execution order: Task 10 closeout -> Task 13 claim test/prose cleanup -> Task 11 CI workflows.

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
- 当前 constructive layer 已落地到 manuscript / README / code:
  - named method:**Support-Gated Variable-Impedance Learning** (SG-VI / SGVIL)
  - diagnostic metric:**Support Coverage Index** (SCI)
- `paper/main.tex` 现已包含:
  - title-level SG-VI 命名
  - 2 条 `we propose` 型 contributions(SG-VI + SCI)
  - benchmark-local SCI 数学定义(projected state-action signature + quantized support set)
- `src/vi_full/three_dof_support_metrics.py` 已实现 SCI 的 projected signature、量化和 rollout→demo coverage 计算；`README.md` 已同步 constructive framing。
- 仍需保持的边界:
  - SG-VI / SCI 目前仍是 benchmark-local、teacher-coupled 定义
  - 还没有 cross-sim / hardware 级别的外部有效性证明

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

## Sprint 1 Full Pilot Execution Snapshot (2026-04-20 17:05 Asia/Shanghai)
- `outputs/pilot_report/three_dof_cross_family_pilot_report.json` now acts as the live progress ledger for Sprint 1.
- Report/export layer is in place:
  - `src/vi_full/three_dof_cross_family_pilot_report.py`
  - `scripts/experiments/export_3dof_cross_family_pilot_report.py`
  - exported figures:
    - `outputs/pilot_report/three_dof_cross_family_pilot_success_vs_budget.{pdf,png}`
    - `outputs/pilot_report/three_dof_cross_family_pilot_first_contact_step_vs_budget.{pdf,png}`
- Completed pilot chunks: 9 / 9
  - `ppo_no_bc@50k/100k/200k`
  - `sac_no_bc@50k/100k/200k`
  - `td3_no_bc@50k/100k/200k`
- Missing pilot chunks: 0 / 9
- Full pilot trend:
  - all pure-RL chunks show `success_rate=0`, `mean_first_contact_step=64`, `mean_contact_steps=0`, `mean_peak_contact_force_n=0`, and `jam_rate=0`
  - the observable separation is **distance-to-contact**, not successful insertion or contact mechanics
  - `sac_no_bc` is the strongest family on this proxy:
    - `23.27 mm @50k`
    - `17.58 mm @100k`
    - `16.67 mm @200k`
  - `ppo_no_bc` improves with budget but remains worse on the same proxy:
    - `31.02 mm @50k`
    - `29.47 mm @100k`
    - `25.48 mm @200k`
  - `td3_no_bc` also improves with budget but remains PPO-like rather than SAC-like:
    - `30.78 mm @50k`
    - `28.62 mm @100k`
    - `25.56 mm @200k`
- Narrative implication:
  - Sprint 1 supports Branch A ("pure RL across families cannot reach useful contact")
  - the weaker but still useful nuance is that off-policy training can shrink terminal distance without crossing the contact gate

## Sprint 2A Confirm Benchmark Boundary

- `narrative_branches.md` now locks the selected branch as Branch A with the 2026-04-20 Asia/Shanghai selection date.
- Sprint 1 full pilot completed: 9/9 chunks.
- No pure-RL method reached contact under the frozen 3DoF nominal-train, nominal-eval, 50k/100k/200k contract.
- SAC shows strongest terminal-distance proxy but still zero-contact:
  - `23.27 mm @50k`
  - `17.58 mm @100k`
  - `16.67 mm @200k`
- Paper-facing boundary:
  - Allowed: pure RL remains outside useful contact; SAC reduces terminal distance.
  - Not allowed: SAC solves insertion; off-policy reaches useful contact; this proves pure RL can never solve insertion.

Next Sprint 2 direction: confirm benchmark should compare Branch-A pure-RL failure against
demo-supported anchors, not oversell SAC.

## Sprint 2B Evidence Matrix Findings (2026-04-21)

- The cleanest way to connect Branch A and the main benchmark is a mixed-contract evidence matrix, not a merged ranking table.
- Confirm rows should stay method-level, not budget-level:
  - use the best pure-RL budget as `train_budget`
  - preserve `entered_contact = false`, `success_rate = 0`, and best distance proxy values
- Anchor rows should come from the canonical five-profile benchmark artifact and keep their own contract:
  - `bc_only_stable_r32_p32`: contact reopened, near-ceiling success
  - `repaired_mainline_bc_to_ppo`: contact reopened, success reopened
  - `dapg_lite_repaired_mainline`: contact reopened, non-zero success
  - `fixed_impedance_rl_stable_r32_p32`: contact reopened; useful as a mechanics anchor, not a gate-failure row
- The matrix-level claim boundary is now explicit:
  - allowed: contact-gate contrast across contracts
  - not allowed: mixed-contract leaderboard reading
- SAC should be written as the strongest distance proxy among pure-RL rows, never as insertion success.
- The repo currently has two parallel paper-facing benchmark artifact lines:
  - stage3 main-table/statistics artifacts for the manuscript's learned-method table
  - schema2 teacher/termination benchmark artifact for appendix-style benchmark anchors
- The Sprint 2B matrix uses the schema2 benchmark artifact for anchor rows, so row-level `source_report`
  should cite the direct confirm/benchmark JSON inputs rather than upstream pilot reports or separate paper-table exports.
- Strict review follow-up:
  - the reviewer-facing distance-proxy claim must follow `best_distance_proxy_method` from the confirm JSON, not a hardcoded SAC assumption in the exporter
  - missing confirm/benchmark metrics must fail fast instead of silently degrading into `0.0`, or the matrix can fabricate false negative evidence from incomplete inputs
