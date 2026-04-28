# Findings & Decisions

## Requirements
- 鐢ㄦ埛甯屾湜鎻愬崌椤圭洰/璁烘枃涓婇檺锛屾牳蹇冧笉鏄ぇ閲嶆瀯锛岃€屾槸閫氳繃鏇村己鐨勫疄楠屽彊浜嬪拰璇佹嵁璁捐鎻愰珮鎶曠绔炰簤鍔涖€?- 鐢ㄦ埛宸茬粡缁欏嚭涓€涓?6-sprint 鑽夋锛岄噸鐐瑰寘鎷細
- 鍏堢ǔ澶嶇幇 Appendix B 涓?PPO-only 鐨勫叧閿礋缁撴灉锛屼綔涓鸿礋璇佹嵁鍦板熀銆?- 瀵?SAC/TD3 鍋氬緢钖勭殑 off-policy sanity锛屽啀鍦?Sprint 1 鍋氳法绠楁硶瀹舵棌 pilot銆?- 鍦?pilot 鍓嶉娉ㄥ唽 3 涓?narrative branches锛岄伩鍏嶇粨鏋滃嚭鏉ュ悗涓存椂缂栨晠浜嬨€?- 灏?teacher study 鍗囩骇涓轰簩缁?mini-ablation锛岃€屼笉鏄彧鍋?fixed vs variable teacher銆?- 寮哄埗鍔犲叆涓€涓€滅獊鐮磋竟鐣屸€濈殑 evidence block锛屼紭鍏?hardware demo锛屽惁鍒?cross-simulator transfer銆?- 浠ｇ爜渚у彧鍋氳交閲忔敹鍙ｏ紝涓嶅仛 env 鍥涘眰澶ф媶鎴栧ぇ瑙勬ā registry/packaging 宸ョ▼銆?
## Research Findings
- 褰撳墠宸ヤ綔鍖哄灞?`F:\edge download\learning` 涓嶆槸 git repo锛屽疄闄呴」鐩湪 `F:\edge download\learning\vi-insertion-only-sim`銆?- 椤圭洰椤跺眰鍖呭惈 `paper/`, `figures/`, `docs/`, `src/`, `scripts/`, `tests/`, `artifacts/`锛岃鏄庤鏂囥€佸疄楠岃剼鏈拰浠ｇ爜璧勪骇閮藉湪鍚屼竴浠撳簱鍐咃紝閫傚悎鍋?repo-aware planning銆?- 鐢ㄦ埛鐨勮鍒掑凡缁忓叿鏈夎緝寮?reviewer-facing 瀵煎悜锛屽挨鍏跺己璋冿細
- broader off-policy comparison
- teacher prior 涓?support coverage 鐨勮В鑰?- external-validity/boundary-breaking evidence
- `README.md` 褰撳墠鎶婅鏂囦富寮犳槑纭檺瀹氫负锛?- 鈥渄emonstration support is the cleanest gate into useful contact鈥?- variable impedance 鐨勪紭鍔夸富瑕佹槸 localized high-friction load/work advantage
- 杩欒鏄庣幇绋挎洿鍍忊€渢eacher-coupled benchmark-local finding鈥濓紝杩樻病鏈夎嚜鐒堕暱鎴愭洿楂樹笂闄愮殑 benchmark methodology/evidence protocol 璁烘枃銆?- `README` 鐨?evidence map 琛ㄦ槑浠撳簱宸茬粡鏈変互涓嬭祫浜э細
- main five-seed benchmark
- appendix teacher/termination package
- factorized support/reset/BC/PPO diagnostics
- PPO large-budget audit
- tuned fixed-impedance sweep
- pose-perturbation proxy
- `README` 宸茬粡鍖哄垎 `jam_rate` 涓?`documented_force_jam_rate`锛岃鏄?failure decomposition 鐨勮涔夋鏋跺凡缁忔湁涓€閮ㄥ垎鍩虹璁炬柦銆?- `paper/main.tex` 褰撳墠鎽樿銆佽础鐚拰璁ㄨ閮芥妸涓诲紶鍘嬪湪涓€涓緢绐勭殑鑼冨洿鍐咃細
- PPO-only 50k--200k audit 浠嶆槸 non-contact failure
- BC support 鏄?useful contact 鐨勫叧閿?gate
- variable impedance 鐨勪环鍊间富瑕佷綋鐜板湪 localized high-friction load/work
- claim 鏄庣‘澹版槑涓?benchmark-local銆乼eacher-coupled锛岃€屼笉鏄?general algorithm ranking
- 姝ｆ枃鍜?limitations 宸茬粡涓诲姩鎵胯锛?- broader off-policy baselines锛堝 SAC锛夋湭瑕嗙洊
- BC demonstrations 鐢?variable-impedance teacher 鐢熸垚锛宼eacher prior 灏氭湭瑙ｈ€?- 鐜浠嶆槸 sim-only銆?DoF銆乤nalytical contact model
- 褰撳墠浠撳簱宸茬粡鏈?appendix teacher block锛屽苟涓旀槸涓€涓幇鎴愮殑 2x2 璁捐锛?- `teacher_variable_variable__repaired_mainline`
- `teacher_variable_fixed__repaired_mainline`
- `teacher_pose_variable__repaired_mainline`
- `teacher_pose_fixed__repaired_mainline`
- 杩欎釜 2x2 鏇存帴杩?`motion rule 脳 impedance rule`锛屼笉鏄敤鎴风幇鍦ㄦ兂瑕佺殑 `teacher type 脳 demo quality/quantity`銆?- `src/vi_full/three_dof_policies.py` 涓?teacher spec registry 鏄庣‘鍐欐浜嗚繖 4 涓?preset锛?- `teacher_variable_variable`: `contact_aware_variable_motion 脳 contact_aware_variable_impedance`
- `teacher_variable_fixed`: `contact_aware_variable_motion 脳 fixed`
- `teacher_pose_variable`: `pose_feedback 脳 contact_aware_variable_impedance`
- `teacher_pose_fixed`: `pose_feedback 脳 fixed`
- `src/*.py` 涓病鏈?`SAC` 鎴?`TD3` 鐨?Python 浠ｇ爜鍖归厤锛岃鏄?off-policy family pilot 鐩墠娌℃湁鐜版垚瀹炵幇鍏ュ彛銆?- 鐢ㄦ埛鍒楀嚭鐨?3 涓簳绾挎祴璇曞悕鍦ㄥ綋鍓?`tests/*.py` 涓病鏈夊尮閰嶏紝琛ㄦ槑杩欎簺 contract tests 闇€瑕佹柊寤烘垨閲嶅懡鍚嶏紝鑰屼笉鏄畝鍗曠户鎵裤€?- 褰撳墠姝ｆ枃 section 楠ㄦ灦鏄細
- Main Benchmark
- Factorized Causal Study
- High-Friction Role of Variable Impedance
- Supplementary Budget Stress Test After BC Support Is Restored
- Pose-Perturbation Scope Stress Test
- 鍐嶅姞 Discussion/Conclusion 鍜?appendix audits
- 褰撳墠涓昏〃 `paper/main.tex:456-464` 鐨勫垪浠嶆槸锛?- `Baseline`
- `High fric.`
- `Noisy force`
- `Mean success`
- `Jam`
- `Final dist.`
- `Peak force`
- `Contact steps`
- 杩欎笌鐢ㄦ埛寤鸿鍗囩骇鎴?`performance / failure / mechanics` 涓夊眰涓昏〃鏄洿鎺ュ搴旂殑锛屽彲鍦ㄧ幇鏈夎〃瀵煎嚭閫昏緫涓婃墿灞曡€屼笉蹇呭畬鍏ㄦ帹鍊掋€?
## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| 浣跨敤 `planning-with-files` 鐨勬枃浠跺寲瑙勫垝鏂瑰紡 | 浠诲姟鏄庢樉灞炰簬澶嶆潅澶氶樁娈电爺绌惰鍒?|
| 鍏堟妸鐢ㄦ埛鑽夋杞垚 repo-aware 鎵ц璁″垝锛岃€屼笉鏄洿鎺モ€滀紭鍖栨帾杈炩€?| 闇€瑕佺敤浠撳簱鍜岃鏂囩幇鐘舵牎楠屽摢浜?sprint 鑳借惤鍦?|
| 鏆備笉鎶?`recoverable_contact_entry_rate` 瑙嗕负榛樿涓績鎸囨爣 | 鐢ㄦ埛宸叉槑纭洿鍋忓悜璁╁畠浣滀负 failure/reachability 浜嬩欢璁℃暟鍣?|
| 鎼滅储宸ュ叿浠?`rg` 鍒囨崲鍒?PowerShell `Select-String` | 褰撳墠鐜璋冪敤 `rg.exe` 杩斿洖 Access is denied锛屼笉鑳介噸澶嶅悓鏍峰け璐ュ姩浣?|
| 灏?Sprint 3 瑙嗕负鈥滄墿灞曠幇鏈?teacher block鈥濊€岄潪浠庨浂寮€濮?| 浠撳簱宸插叿澶?2x2 teacher registry銆乤ppendix table/figure 鍜岀浉鍏虫祴璇曟敮鎾?|
| 灏?Sprint 1 鏍囪涓洪珮宸ョ▼椋庨櫓闃舵 | 鐜版湁浠ｇ爜鍙毚闇?PPO 璁粌璺緞锛宱ff-policy pilot 涓嶆槸闆舵垚鏈閲?|
| 灏嗚鏂囨敼绋胯涓衡€滈噸鎺掑凡鏈?section 楠ㄦ灦 + 鎻掑叆鏂?evidence block鈥?| 褰撳墠涓绘枃鍜?appendix 宸叉湁娓呮櫚鎸傜偣锛屼笉闇€瑕佷粠绌虹櫧鐩綍閲嶅缓 |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| 鍒濆 cwd 涓嶆槸 git repo | 灏嗛」鐩牴鍒囨崲鍒?`vi-insertion-only-sim` 骞跺湪璇ョ洰褰曞垱寤?planning files |
| `rg.exe` 鏃犳硶鎵ц锛圓ccess is denied锛?| 鏀圭敤 PowerShell 鍘熺敓鍛戒护 `Get-ChildItem` + `Select-String` 缁х画浠ｇ爜/璁烘枃妫€绱?|
| PowerShell 璇诲彇 teacher spec 涓婁笅鏂囨椂鍛戒腑浜嗗涓嚱鏁板畾涔夊鑷磋鍙蜂负鏁扮粍 | 鏀惧純涓€娆℃€ц嚜鍔ㄥ彇涓婁笅鏂囷紝鏀圭敤鏇村畾鐐圭殑璇诲彇鏂瑰紡 |

## Resources
- Project root: `F:\edge download\learning\vi-insertion-only-sim`
- Planning skill: `C:\Users\Windows\.codex\skills\planning-with-files\SKILL.md`
- User draft plan: current conversation content

## Milestone 3 Engineering Trust Planning (2026-04-25)

- Milestone 2 Paper-Facing Reproducibility is treated as complete for the next work slice.
- The user does not want local LaTeX/PDF deployment to be a blocking workflow requirement.
- Milestone 3 should therefore close on no-training Python checks, source/prose audits, import-boundary checks, reviewer smoke checks, and `build_paper_assets.py --check`; it should not require `pdflatex`, `bibtex`, `latexmk`, or `build_paper_pdf.py`.
- Current Task 10 baseline is mostly implemented: `src/vi_full/__init__.py` exposes only `__version__`, and `tests/core/test_import_boundaries.py` exists.
- Current Task 11 baseline is not implemented: `.github/` does not exist.
- Current Task 13 baseline is not implemented: `tests/paper/test_paper_claim_boundaries.py` does not exist.
- Recommended execution order: Task 10 closeout -> Task 13 claim test/prose cleanup -> Task 11 CI workflows.

## Paper Ceiling Diagnosis (per 2026-04-18 discussion)

### Current trajectory ceiling
- **Sim-only + 3DoF 鍗曚换鍔?+ 4 鏉?observational contribution**:鐜扮姸鎶曠涓婇檺澶х害鍦?Q3 涓婃父,Q2 闈?OA 杈圭紭;鍗曞嚟 Sprint 0-5 鎵ц鍒颁綅,涓嶈冻浠ヨ嚜鍔ㄦ帹涓?Q2銆?- 璁烘枃 abstract 鑷О "simulation-only" + narrative 鑷О "benchmark-local and teacher-coupled" 鏄?**defensive framing**,瀵?T-RO / T-ASE / T-MECH / MSSP 妗?reviewer 鏄槑鏄惧噺鍒嗕俊鍙枫€?
### Two hard gaps blocking Q2
1. **No real-hardware evidence**:鎺ヨЕ浠诲姟鐨?sim-only 璁烘枃鍦?Q2 闈?OA 妗ｇ殑绗竴鍒€ reject 鐞嗙敱;Sprint 0-5 瀹屽叏娌℃湁 real-robot / cross-simulator / physical transfer 浠讳綍涓€绉嶃€?2. **Zero constructive contribution**:`paper/main.tex:106-118` 鐨?4 鏉?contributions 鍏ㄩ儴浠?"we provide / we show" 璧峰ご,鏃?"we propose"銆俀2 闈?OA 閫氬父瑕佹眰鑷冲皯 1 鏉″彲琚紩鐢ㄣ€佸彲琚鐢ㄧ殑璐＄尞(named method / framework / diagnostic tool)銆?
### Three hard upgrade paths (蹇呴€変竴鏉?鏈€濂戒袱鏉?
| Path | ROI | 鏃堕棿鎴愭湰 | 璇存槑 |
|------|-----|----------|------|
| A. Real-hardware validation | 鏈€楂?| 5鈥? 鍛?+纭欢 4鈥?0 鍛ㄥ埌璐? | 瑙﹀彂 Phase 2.5 / 3.5 / H;narrative 瀹氫綅涓?"controlled-fidelity existence proof",涓嶅崠 sim-to-real zero-gap |
| B. Cross-simulator transfer | 涓?| 1.5鈥? 鍛?| MuJoCo 鈫?Isaac Gym / PyBullet;鍗曚汉鍙仛,鍥炲嚮 "sim artifact" 璐ㄧ枒 |
| C. Named method + diagnostic tool | 浣?涓?| 3鈥? 澶?| 涓嶅姞瀹為獙,鎶?BC鈫扨PO + variable impedance + factorized support analysis 鍖呰鎴愭鏋?e.g. Support-Gated VI Learning),鍐嶆娊涓€涓?metric(e.g. Support Coverage Index) |

### Hardware-to-code coupling classification
- **A 绫?~70%,纭欢鏃犲叧)**:PPO-only 澶嶇幇銆丼AC/TD3 pilot銆? 涓?contract tests銆乼eacher 2脳2 鎵╁睍銆乫ailure decomp 鍗囨牸銆乧learance shift銆乴earning curve 鈥斺€?鐜板湪灏辫兘鍚姩,涓?block 浜?Phase 2.5銆?- **B 绫?~20%,纭欢鏂瑰悜瀹氫簡灏卞惎鍔?**:Domain randomization銆乤ction adapter 鎶借薄銆乷bs source 鎶借薄銆乵etric source 缁熶竴銆乧ontrol-rate mismatch銆乻afety envelope 鈥斺€?Phase 3.5 鐨勫叏閮ㄥ唴瀹?涓嶇瓑纭欢鍒拌揣,鏂瑰悜瀹氫簡灏卞姩銆?- **C 绫?~10%,绛夌‖浠跺埌璐?**:RDK/ROS 2 bridge銆乨eployment runtime銆乼rial runner銆乺eal-sim gap 閲忓寲銆丗lexiv primitive 瀵圭収 鈥斺€?Phase H 鐨勫叏閮ㄥ唴瀹广€?
### Narrative branches (Phase 2 pre-register)
| Branch | Trigger (Sprint 1 pilot result) | Narrative pivot |
|--------|---------------------------------|-----------------|
| A | Pure RL across families 閮借繘涓嶄簡 useful contact | 淇濇寔 "demonstration support is the gate";Q2 闇€闈犵‖浠惰瘉鎹垨 named method 琛?|
| B | 鏌?off-policy family 鑳借繘鎺ヨЕ,浣嗕綆棰勭畻鏄庢樉宸簬 demo-supported | 涓绘帹 "sample-efficiency differentiation under teacher-coupled support" |
| C | Off-policy family 宸查€艰繎 demo-supported | 涓绘枃蹇呴』杞啓涓?benchmark methodology,涓嶈兘鍐嶅崠 support superiority |

**鍐欐硶**:涓変唤 abstract 鑽夌鎻愬墠鍐欏湪 `docs/project/narrative_branches.md`,Sprint 1 缁撴潫褰撳ぉ閫夊垎鏀?涓嶄簨鍚庣紪鏁呬簨銆?
### Timeline inflation
- 鍘熺敤鎴疯崏妗?5鈥? 鍛?杩囦簬涔愯(60鈥?5 training runs + iteration tax)銆?- **No-hardware path**:鐜板疄 10鈥?4 鍛ㄣ€?- **Franka-class hardware path**:鐜板疄 15鈥?2 鍛?鍔?Phase 3.5 + Phase H)銆?- **Rizon 4s + Flexiv primitive baseline(Q1 璺緞)**:鐜板疄 18鈥?6 鍛ㄣ€?- Effort 浼扮畻鎸夊崟浜哄叏鑱?鍗婅亴涔?2銆?
### Contribution rewrite target
- 褰撳墠 constructive layer 宸茶惤鍦板埌 manuscript / README / code:
  - named method:**Support-Gated Variable-Impedance Learning** (SG-VI / SGVIL)
  - diagnostic metric:**Support Coverage Index** (SCI)
- `paper/main.tex` 鐜板凡鍖呭惈:
  - title-level SG-VI 鍛藉悕
  - 2 鏉?`we propose` 鍨?contributions(SG-VI + SCI)
  - benchmark-local SCI 鏁板瀹氫箟(projected state-action signature + quantized support set)
- `src/vi_full/three_dof_support_metrics.py` 宸插疄鐜?SCI 鐨?projected signature銆侀噺鍖栧拰 rollout鈫抎emo coverage 璁＄畻锛沗README.md` 宸插悓姝?constructive framing銆?- 浠嶉渶淇濇寔鐨勮竟鐣?
  - SG-VI / SCI 鐩墠浠嶆槸 benchmark-local銆乼eacher-coupled 瀹氫箟
  - 杩樻病鏈?cross-sim / hardware 绾у埆鐨勫閮ㄦ湁鏁堟€ц瘉鏄?
## Visual/Browser Findings
- 鏈疆灏氭湭鏌ョ湅鍥剧墖銆丳DF 鎴栫綉椤靛唴瀹广€?- 2026-04-18 閫氳繃 WebFetch / fetch MCP 璇诲彇 `github.com/Synria-Robotics` 缁勭粐椤靛強 Alicia-M-SDK / RoboCore / Alicia-D-SDK README,鐢ㄤ簬纭欢鍊欓€夎瘎浼?瑙?Paper Ceiling Diagnosis 涓?Hardware candidate assessment)銆?
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

- `docs/project/narrative_branches.md` now locks the selected branch as Branch A with the 2026-04-20 Asia/Shanghai selection date.
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
