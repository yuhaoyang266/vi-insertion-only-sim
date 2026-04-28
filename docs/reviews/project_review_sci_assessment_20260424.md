# vi-insertion-only-sim 项目 Review 与 SCI 二/三区投稿评估

日期：2026-04-24  
审阅范围：`README.md`、`paper/main.tex`、`src/vi_full/`、`scripts/`、`tests/`、`artifacts/`、`outputs/`、`docs/`。  
说明：这里的“SCI 二/三区”指期刊分区投稿质量；项目内部的 `SCI` 指 `Support Coverage Index`，两者不要混淆。

## 结论先行

**当前不建议直接投 SCI 二/三区。** 项目已经具备较好的工程化基础、较完整的论文草稿、可运行测试与匿名打包入口；但存在一个会被审稿人/编辑直接抓住的硬伤：**论文主表、README/默认导出脚本、证据矩阵正在引用不同版本的 benchmark artifact，导致 Fixed-impedance RL 和 DAPG-lite 等关键数值互相矛盾。**

修复 P0/P1 问题后：

- **SCI 三区：有机会**，前提是定位为 simulation benchmark / reproducibility / methods note，而不是泛化机器人插入算法论文。
- **SCI 二区：偏吃力但不是完全不可能**，需要补齐结果 provenance、统一 artifact、增加敏感性/外部有效性证据；若目标是机器人/控制主流二区期刊，仅凭 simulation-only 3DoF analytical benchmark 风险较高。
- **SCI 一区或强 robotics venue：当前证据不足**，主要缺硬件、跨仿真、6D/真实接触、多 baseline 和系统敏感性验证。

## 已验证结果

| 检查项 | 命令/方式 | 结果 | 含义 |
| --- | --- | --- | --- |
| Python 语法编译 | `python -m compileall -q src scripts tests` | 通过 | 源码、脚本、测试无语法级阻断 |
| 完整测试 | `python -m pytest -q` | `160 passed, 15 skipped, 9 warnings in 115.27s` | 回归测试基础较好；但跳过项和 heavy experiment 仍不是完整复现实验 |
| 测试收集 | `python -m pytest --collect-only -q` | `175 tests collected` | 覆盖面比一般论文仓库好 |
| LaTeX 直接 README 命令 | `pdflatex ...; bibtex ...` | 失败：`pdflatex` / `bibtex` 不在 PATH | README 当前命令对新环境不稳 |
| LaTeX 绝对路径构建 | `C:\Users\Windows\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe ...` | 通过，输出 `main.pdf` 23 页 / 654055 bytes | 本机能构建；需修复 PATH/README 可复现性 |
| 投稿包 builder | `python scripts/export/build_submission_bundle.py --output-dir tmp/review_submission_bundle` | 通过，生成 snapshot/editor zips 和 manifest | 打包入口可用 |
| 默认 benchmark table export | `python scripts/export/export_paper_only_sim_benchmark_table.py --output-dir tmp/review_default_table` | 通过但生成 schema2 数值 | 暴露与论文主表的关键不一致 |

项目相关失败证据：

```text
Command: pdflatex -interaction=nonstopmode -halt-on-error main.tex; bibtex main; pdflatex -interaction=nonstopmode -halt-on-error main.tex; pdflatex -interaction=nonstopmode -halt-on-error main.tex
Exit code: 1
Error excerpt:
pdflatex : The term 'pdflatex' is not recognized as the name of a cmdlet, function, script file, or operable program.
bibtex : The term 'bibtex' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

## 项目强项

1. **主张边界明显收敛**  
   论文多次声明是 `simulation-only`、`3DoF`、`teacher-coupled`、`benchmark-local`，不是泛化机器人算法排名。这个姿态比“PPO/SAC/TD3 谁强”更安全。

2. **证据层次比普通小论文清楚**  
   主表、pure-RL pilot、factorized controls、high-friction mechanics、pose perturbation、tuned fixed sweep、protocol map 分层呈现，避免把不同 contract 硬混成 leaderboard。

3. **工程测试基础较扎实**  
   175 个可收集测试、160 个通过测试，覆盖导出脚本、evidence matrix、support metrics、teacher metadata、submission bundle 等纸面关键路径。

4. **负结果叙事有价值**  
   `PPO/SAC/TD3 w/o BC` 在 nominal-only pilot 50k/100k/200k 都不进入 useful contact；若限定为该 benchmark 的 support gate 发现，这是一个可写的 controlled negative result。

5. **论文主动暴露限制**  
   `paper/main.tex` 已明确承认没有硬件、没有跨仿真、不是 6D orientation benchmark、SCI 指标未做系统敏感性优化。这能降低过度主张风险。

## P0：投稿前必须修复的问题

### P0-1 论文主表与默认 artifact/证据矩阵不一致

这是最大硬伤。

- `paper/main.tex` 主表使用 stage3 数值：Fixed-impedance RL mean success `0.947`，DAPG-lite `1.000`。
- `artifacts/main_benchmark/table_3dof_paper_benchmark_stage3_20260412.md` 也记录 stage3：Fixed `0.947`，DAPG-lite `1.000`。
- 但 `outputs/evidence_matrix/three_dof_sprint2_main_table.md` 使用 schema2：Fixed `0.80`，DAPG-lite `0.60`。
- `scripts/export/export_paper_only_sim_figure2.py` 和 `scripts/export/export_paper_only_sim_benchmark_table.py` 默认输入都是 `three_dof_benchmark_schema2_paper_teacher_20260418_034230.json`。
- `README.md` 的无参数 Figure 2 复现命令会走这个 schema2 默认输入。

量化差异：

| Suite | Metric | schema2 | stage3 | 差异 |
| --- | --- | ---: | ---: | ---: |
| Fixed-impedance RL | success | 0.800 | 0.9468 | -0.1468 |
| Fixed-impedance RL | peak force | 0.8977 | 1.0706 | -0.1729 |
| BC -> PPO | peak force | 0.6801 | 0.9022 | -0.2221 |
| DAPG-lite | success | 0.600 | 1.000 | -0.4000 |
| DAPG-lite | contact steps | 27.546 | 29.5564 | -2.0104 |

**影响：** 这不是小的格式问题，而是论文 claim provenance 冲突。SCI 二/三区审稿中，这会被判定为结果版本管理不可靠，甚至可能质疑主结论是否 cherry-pick。


关键定位：

- `paper/main.tex:535`、`paper/main.tex:537`、`paper/main.tex:539`：论文主表 stage3 数值。
- `artifacts/main_benchmark/table_3dof_paper_benchmark_stage3_20260412.md:14`、`artifacts/main_benchmark/table_3dof_paper_benchmark_stage3_20260412.md:16`：stage3 表中 Fixed/DAPG 主表数值。
- `outputs/evidence_matrix/three_dof_sprint2_main_table.md:31`、`outputs/evidence_matrix/three_dof_sprint2_main_table.md:39`：evidence matrix 中 schema2 的 DAPG/Fixed 数值。
- `scripts/export/export_paper_only_sim_figure2.py:30`、`scripts/export/export_paper_only_sim_benchmark_table.py:30`：默认导出输入仍指向 schema2 artifact。
- `README.md:123`、`README.md:156`：README 的无参数 Figure 2 复现命令与 evidence-matrix 命令指向 schema2 路径。
**建议：** 冻结一个唯一 canonical main benchmark artifact。然后同步：

- `paper/main.tex` 主表和 Figure 2；
- `README.md` reproduce 命令；
- `scripts/export/*figure2*` 与 `*benchmark_table*` 默认值；
- `outputs/evidence_matrix/*` 与 manifest；
- `artifacts/main_benchmark/*table*.md/json` 的 source path；
- 测试中加入 “paper table == default export == evidence matrix selected rows” 的数值一致性回归。

### P0-2 可复现路径仍含本机绝对路径和外部源路径

多个 tracked artifacts 写入 `F:\edge download\learning\...` 或旧 `full_projects\vi_insertion_full_only_sim\outputs\...` 路径。示例：

- `artifacts/main_benchmark/table_3dof_paper_benchmark_stage3_20260412.md` 的 source 指向旧工作树绝对路径。
- `artifacts/main_benchmark/table_3dof_appendix_schema2_20260418.md` 指向当前机器的 `F:\...\outputs\...`。
- README 里也承认 schema2 frozen artifact predates newer export path。

**影响：** 外部审稿人无法区分 “repo 内可复现输入” 和 “作者本机历史路径”。这会削弱 reproducibility。

**建议：** 所有 paper-facing artifact metadata 改为 repo-relative path + artifact hash + generating command + git commit。绝对路径只允许出现在本地 log，不应出现在提交给审稿人的 artifact。

### P0-3 README 构建命令与本机环境不一致

README 写 `pdflatex` / `bibtex` 直接可用，但当前 shell PATH 找不到它们。绝对路径下 MiKTeX 可以构建，但 README 对新机器不够稳。

**影响：** 审稿人按 README 操作失败，会直接降低可信度。

**建议：** README 增加 Windows MiKTeX PATH 说明、`where pdflatex` 检查、或提供 `scripts/export/build_paper_pdf.py` 封装绝对路径/环境诊断。更好是提供 CI 或 portable TeX build recipe。

## P1：强烈建议修复的问题

### P1-1 外部有效性不足，Q2 风险高

论文已经诚实承认：环境是 analytical 3DoF、relative-frame、synthetic force、diagonal stiffness、无真实 F/T、无 6D pose、多点接触或硬件校准。这些限制在 `paper/main.tex` 的 discussion 里写得比较完整。

**判断：** 对 SCI 三区 simulation benchmark paper 尚可；对 SCI 二区 robotics/control 论文偏弱。除非目标期刊接受 “controlled simulation benchmark + reproducible artifact” 类型，否则需要至少增加：

- 一个真实或更高保真仿真平台交叉验证；
- 6D/姿态扰动更系统的实验；
- contact parameter / stiffness / reward / reset / teacher quality 的敏感性分析；
- 更强 classical / offline RL / demo-augmented RL baselines。

### P1-2 统计效力偏低，近天花板结果不利于强结论

主表多项接近 `1.000` success，只有 5 seeds。论文也写了 Fixed vs BC->PPO 的 sign-permutation p-value `0.0625`，并承认不是 conventional `p<0.05`。

**建议：** 增加 10-seed 或更多 seed expansion；对 near-ceiling 方法改报告 effect size、success-force Pareto、contact work、energy/distance joint metrics，而不要强调成功率排序。

### P1-3 顶层包导入过重，复现体验差

`src/vi_full/__init__.py` 顶层导入 legacy MuJoCo/Panda 模块、SB3 training、3DoF training 等。未安装 editable package 时直接 import 失败；设置 `PYTHONPATH=src` 后可 import，但会输出 Gym deprecation warning。

**建议：** 顶层 `__init__` 只导出轻量核心，训练/legacy/MuJoCo 模块改为显式子模块导入。至少保证 `import vi_full.three_dof_env` 和 CLI helper 不触发不相关 Gym/MuJoCo/SB3 警告。

### P1-4 代码组织存在维护风险

行数热点：

- `src/vi_full/three_dof_training.py`：2239 行；
- `src/vi_full/paper_figures.py`：1778 行；
- `src/vi_full/three_dof_benchmark.py`：1648 行；
- `src/vi_full/paper_tables.py`：1392 行。

**影响：** 这不一定影响论文结论，但会影响长期可维护性和审稿人对工程可信度的观感。

**建议：** 不要大重构论文前夕；先加 contract tests。投前只做最小拆分：artifact provenance、default path、table/figure/evidence sync。大模块拆分可以放到投稿后。

### P1-5 匿名 snapshot 排除了 tests

`docs/submission/submission_package_checklist.md` 说明 anonymous snapshot 排除 `tests/`。如果期刊希望审稿人复现，去掉 tests 会降低 reviewer-facing package 的透明度。

**建议：** 匿名包至少保留 smoke tests 或 `tests/reviewer/` 子集；若必须排除完整 tests，也要在 snapshot README 中说明如何从公开 repo 获取 tests。

## P2：改进后更像成熟论文包的问题

- `pyproject.toml` package 名称仍是 `vi-insertion-full`，但 repo 是 `vi-insertion-only-sim`，会让 scope 感觉不统一。
- Figure A2 文件名仍用 `fig1_contact_transition_audit` legacy stem，虽然有兼容理由，但 paper-facing 命名不够干净。
- 论文中 SG-VI / SCI 两个新概念目前更像 benchmark-local packaging 和 diagnostic；需要避免写成普适方法贡献。
- `PPO w/o BC` 的 no-contact 结论是有价值负结果，但它只覆盖有限 PPO contracts；不要写成所有 PPO 都失败。
- `DAPG-lite` 明确不是某个 prior implementation 的 faithful reproduction，这个边界要保留，否则审稿人会追问公平性。

## 证据链支撑度评估

| Claim | 当前支撑度 | 评价 |
| --- | --- | --- |
| Pure RL 在本 benchmark 下打不开 useful contact gate | 中-强 | PPO/SAC/TD3 pilot + PPO large-budget audit 支撑；但不是 exhaustive hyperparameter theorem |
| BC demonstration support 是 cleanest gate | 中 | factorized diagnostics 支撑；但 teacher 是 variable-impedance，demo support 与 VI prior 未完全解耦 |
| Variable impedance 在 high-friction 下有低载荷/低功优势 | 中 | mechanics trace 和 hand-crafted anchors 支撑；但 fixed tuned sweep 已显示 fixed 也可高成功，因此只能说 localized load/work benefit |
| SG-VI 是可推广方法 | 弱 | 当前更像 benchmark-local recipe，不应泛化 |
| SCI 是通用指标 | 弱 | 当前 bin widths 是 benchmark-local，需要 sensitivity analysis |
| 可投 SCI 三区 | 中 | 修复 P0 后有机会，尤其是 simulation benchmark / reproducibility 方向 |
| 可投 SCI 二区 | 中-低 | 需要更强外部有效性、统一 provenance、更多敏感性/统计证据 |

## 建议投稿定位

更稳的题目/定位：

> A controlled simulation benchmark showing that demonstration support gates learnable contact in 3DoF variable-impedance insertion.

不建议的定位：

> A general variable-impedance RL algorithm that outperforms PPO/SAC/TD3 for robotic insertion.

推荐目标：

- **三区/偏工程仿真的机器人或智能系统期刊**：优先，修复 P0 后可以尝试。
- **二区 simulation / automation / intelligent robotics 边缘期刊**：可尝试，但需要把 reproducibility 和 benchmark-local honesty 打磨到很强。
- **强机器人二区或一区**：当前不建议，除非新增真实/高保真验证和更完整 baseline。

## 最小投前整改清单

1. 选定唯一 canonical main benchmark artifact，并删除/降级冲突的 schema2/stage3 默认路径。
2. 重新导出 Figure 2、main table、evidence matrix、README evidence map，确保所有数值一致。
3. 添加回归测试：论文主表数值、默认导出数值、evidence matrix 数值必须一致。
4. 清理所有 paper-facing artifact 中的本机绝对路径，改为 repo-relative + hash + command + commit。
5. 修复 README LaTeX build 指令，加入 PATH 检查或封装脚本。
6. 在 anonymous snapshot 中保留最小 reviewer tests 或明确给出复现测试入口。
7. 增加一页 supplementary：artifact lineage / command manifest / seed count / skipped-heavy-experiment boundary。

## 最终判断

**当前质量：工程基础好，但 submission readiness 不足。** 主要不是代码跑不通，而是 **paper-facing artifact lineage 不统一**。如果现在投，最可能被拒的理由不是算法完全没价值，而是审稿人会认为“结果版本、图表、证据矩阵不一致，难以信任”。

**修完 P0 后，SCI 三区可以认真尝试；SCI 二区需要额外实验与更强外部有效性，否则成功概率偏低。**

