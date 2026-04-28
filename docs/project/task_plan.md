# Task Plan: Raise the project's paper ceiling with a tighter evidence-driven roadmap

## Goal
灏?`vi-insertion-only-sim` 浠?sim-only 3DoF 鍗曚换鍔?narrow-claim"璁烘枃鎺ㄨ繘鍒?**SCI Q2 闈?OA** 绾у埆(T-ASE / T-MECH / MSSP 妗?銆傝嫢 Phase 2.5 纭欢鍐崇瓥閫夋嫨 Flexiv Rizon 4s 鎴?Franka Research 3,鐩爣涓婅皟鑷?**Q1**(T-RO / IJRR 妗?;鑻ヤ笉涔扮‖浠?鐩爣鍥為€€鑷?**Q3 涓婃父** 骞朵互纭姞鍒嗚矾寰?cross-simulator transfer 鎴?named method + diagnostic tool)琛ュ伩銆?

## Target Venue Tier
| Path | Ceiling | Requires |
|------|---------|----------|
| No-hardware | Q3 upper / Q2 marginal | cross-sim transfer 鎴?named method 浜岄€変竴琛ュ伩 |
| Franka-class hardware | Q2 绋冲Ε | Phase 3.5 + Phase H 瀹屾暣鎵ц |
| Rizon 4s + Flexiv primitive baseline | Q1 鏈夋満浼?| Phase 3.5 + Phase H + primitive 瀵圭収瀹為獙 |

Final tier 灏嗗湪 Phase 2.5 鍏抽棴鏃堕攣瀹氥€?

## Current Phase
Phase 5 delivery complete; submission package assembled. Milestone 3 Engineering Trust is complete: lightweight import, no-training CI gates, and paper claim-boundary checks are closed, with local PDF/TeX deployment explicitly excluded from the blocking gate.

## Phase Dependency Graph
```
Phase 1 (done)
   鈹?
   v
Phase 2 (narrative lock)
   鈹?
   鈹溾攢鈹€> Phase 2.5 (hardware gate) 鈹€鈹€> Phase 3.5 (scaffolding, if hw) 鈹€鈹€> Phase H (real, if hw)
   鈹?                                                                           鈹?
   鈹斺攢鈹€> Phase 3 (sim-only, parallel) 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€>鈹?
                                                                                 v
                                                                           Phase 4 (writing)
                                                                                 鈹?
                                                                                 v
                                                                           Phase 5 (delivery)
```
- **Phase 3 涓?block 浜?Phase 2.5**:A 绫?sim 宸ヤ綔(SAC/TD3 pilot銆乼eacher ablation銆乸rotocol freeze銆乫ailure decomp)涓庣‖浠跺喅绛栬В鑰?鍙苟琛屽惎鍔ㄣ€?
- **Phase 3.5 / Phase H 鏄?conditional**:浠呭湪 Phase 2.5 = buy-hardware 鏃惰Е鍙戙€?
- **Effort 鍗曚綅**:person-week,鍗曚汉鍏ㄨ亴浼扮畻;鍗婅亴璇蜂箻 2銆?

## Phases

### Phase 1: Repository & Paper Discovery  (effort: 1 day | risk: low | status: complete)
- [x] Understand user intent
- [x] Identify top-level repository structure
- [x] Create planning files and capture initial findings
- [x] Read the current README/paper structure and map existing evidence blocks
- [x] Confirm whether off-policy code paths and requested contract tests already exist
- **Deliverable:** `docs/project/findings.md` Research Findings section (瀹屾垚)

### Phase 2: Plan Audit & Narrative Lock  (effort: 2 days | risk: medium | status: complete)
- [x] Translate the user's sprint sketch into a phase-gated plan
- [x] Identify must-have vs nice-to-have items for Q2-class submission
- [x] Pre-register 3 narrative branches (A / B / C) with candidate abstract drafts
- [x] Define branch-switch criteria based on Phase 3 Sprint 1 pilot outputs
- **Deliverable:** `docs/project/narrative_branches.md` + Branch A selected 2026-04-20

### Phase 2.5: Hardware Decision Gate  (effort: 1 week | risk: high | status: complete)
- **Decision: No-hardware** (2026-04-22)
- Venue ceiling: **Q3 upper / Q2 marginal**
- Hard bonus path: **named method (SG-VI) + diagnostic tool (SCI)** already landed; cross-sim transfer 鍙€夊仛 1.5-2 鍛ㄩ澶栧姞鍒?
- Phase 3.5 / Phase H: **cancelled**
- **Deliverable:** 鏈?decision record

### Phase 3: Sim-only Experiment Execution  (effort: 4鈥? weeks | risk: medium | status: complete)
_A-category work. 鍙笌 Phase 2.5 骞惰鍚姩銆俖

- [x] Sprint 0: PPO-only 200k 澶嶇幇 + `docs/project/protocol_freeze.md`
  鈫?Deliverable: 澶嶇幇 JSON + 3 涓?regression tests(force_jam consecutive銆乥locked_contact separate reason銆乸po-only disables auxiliary stages)passing
- [x] Sprint 1: SAC / TD3 璁粌鍏ュ彛 + cross-family pilot
  鈫?Deliverable: `src/vi_full/three_dof_cross_family_baselines.py` + `scripts/experiments/run_3dof_cross_family_pilot.py` + `src/vi_full/three_dof_cross_family_pilot_report.py` + `scripts/experiments/export_3dof_cross_family_pilot_report.py`;27 runs(3 methods 脳 3 seeds 脳 3 budgets);2 寮犲唴閮ㄥ浘(success vs budget銆乫irst_contact_step vs budget)
  鈫?2026-04-20 17:05 Asia/Shanghai full pilot completed / Branch A evidence: `outputs/pilot_report/three_dof_cross_family_pilot_report.json` 宸叉眹鎬?9/9 method-budget chunks锛宮issing=0锛涘凡瀹屾垚 `ppo_no_bc@50k/100k/200k`銆乣sac_no_bc@50k/100k/200k`銆乣td3_no_bc@50k/100k/200k`锛涗笁鏃?pure-RL 浠嶄负 `success_rate=0`銆乣mean_contact_steps=0`銆乣mean_first_contact_step=64`锛屾敮鎸?Branch A锛坧ure RL across families cannot reach useful contact锛?
- [x] Sprint 1-End: 鎸夐娉ㄥ唽 A/B/C 閫夊畾 narrative 鍒嗘敮
  鈫?Deliverable: Branch A locked in `docs/project/narrative_branches.md` 2026-04-20
- [x] Sprint 2A: Branch-A confirm benchmark pack
  鈫?Deliverable: confirm report + CSV + contact gate table + distance vs budget figure;8 tests passing
- [x] Sprint 2B: Anchor-integrated evidence matrix + strict review
  鈫?Deliverable: evidence matrix (pure-RL 脳 demo-supported anchors) + JSON/CSV/MD/PNG/PDF artifacts;code review passed (4 Important fixes applied);52 tests passing
- [x] Sprint 2 main table: 涓夊眰涓昏〃 + learning curves
  鈫?Deliverable: reviewer-facing 涓夊眰 claim-control 涓昏〃 + contact-gate matrix + pure-RL budget-curve figure;nominal-only pure-RL rows 涓?five-profile benchmark anchors 淇濇寔 separate evidence contracts
- [x] Sprint 3: Teacher mini-ablation kickoff,鍐荤粨 teacher support quality 脳 demo rollout budget 灏忚竟鐣?
  鈫?Kickoff artifact: `outputs/sprint3_teacher_mini_ablation/sprint3_teacher_mini_ablation_kickoff.{json,md}`
  鈫?Frozen boundary: 4 鏉′欢 teacher support quality x demo rollout budget;鍥哄畾 `bc_pretrain_steps=32`銆乣total_timesteps=128`銆丅C-to-PPO init銆乫ive-profile evaluation銆丼print 2 claim-control metrics + SCI/support-cell coverage
  鈫?Excluded from kickoff: BC pretrain-step sweep銆乸olicy-init sweep銆乼eacher/no-teacher pure-RL control銆佸畬鏁?motion-rule 脳 impedance-rule appendix sweep
- [x] Sprint 4A: Clearance shift 椴佹鎬ф壂鎻?
  鈫?Deliverable: `outputs/sprint4_clearance_shift/sprint4_clearance_shift.{json,csv,md}`; pure-clearance `easy/nominal/hard` ladder 脳 selected demo-supported suites;褰撳墠浠撳簱鏃犳寔涔呭寲 checkpoint,鍥犳閲囩敤 train-once / eval-many-profile 鍚堝悓
  鈫?2026-04-23 result snapshot: `BC-only (stable 32/32)` 鍦?hard ladder 浠嶄负 `success_rate=1.0`; `DAPG-lite` 闄嶈嚦 `success_rate=0.768`, `jam_rate=0.05`; `BC -> PPO` 涓?`Fixed-impedance RL (stable BC 32/32)` 鍦?hard ladder 淇濇寔绾?`0.8` success 涓?`jam_rate=0`
- **Depends on:** Phase 2 narrative lock
- **Does NOT depend on:** Phase 2.5

### Phase 3.5: CANCELLED (no-hardware decision 2026-04-22)
### Phase H: CANCELLED (no-hardware decision 2026-04-22)

### Phase 4: Writing & Artifact Strategy  (effort: 2-3 weeks | risk: medium | status: complete)
- [x] Contribution reframing: findings-only -> `propose + show` (>=1 constructive)
  -> Deliverable: 4 contributions, at least 1 named method / diagnostic tool
  -> 2026-04-21: SG-VI / SCI landed in `paper/main.tex`, `README.md`, and `src/vi_full/three_dof_support_metrics.py`
- [x] Abstract/Intro rewrite: reflect Branch A + SG-VI + cross-family evidence
  -> Deliverable: updated abstract and intro text
  -> 2026-04-23: abstract and introduction now carry Branch A, SG-VI / SCI, cross-family negative evidence, and Sprint 4A framing
- [x] Main text restructure: 4.1 cross-family / 4.2 learning curves / 4.3 failure decomp / 4.4 high-friction mechanics / 4.5 teacher ablation / 4.6 clearance shift / 4.7 real-robot(if any)
  -> Deliverable: updated `paper/main.tex` scaffolding
  -> 2026-04-23: experiments/discussion now include cross-family, teacher-boundary, clearance-shift, and appendix protocol-map alignment
- [x] Figure/table pipeline extension
  -> Deliverable: Sprint 3 kickoff matrix exporter + Sprint 4 clearance summary exporter; real-sim parity N/A on the no-hardware path
  -> 2026-04-23: reviewer-facing Sprint 3 bundle now exports `json/csv/md + kickoff_matrix.pdf/png`; Sprint 4 bundle now exports `json/csv/md + summary.pdf/png`
- [x] Limitations convergence: keep the no-hardware / sim-only boundary explicit until hardware exists
  -> Deliverable: rewritten Discussion / Limitations
  -> 2026-04-23: Discussion now states benchmark-local, no-hardware, proxy-study, and no-checkpoint boundaries explicitly
- **Depends on:** Phase 3 complete(+ Phase H if hardware path)

### Phase 5: Delivery  (effort: 1 week | risk: low | status: complete)
- [x] README / runner CLI 鏀跺彛
  -> 2026-04-23: README quick links / reproduce commands now surface the Sprint 3 kickoff matrix and Sprint 4 clearance summary bundles; repo-root smoke coverage includes the public experiment/export entrypoints plus Sprint 3 actual CLI export
- [x] Contract smoke tests + teacher serialization tests
  -> 2026-04-23: `tests/runners/test_run_3dof_experiment_entrypoints.py`, `tests/runners/test_run_sprint3_teacher_mini_ablation_kickoff.py`, `tests/runners/test_run_sprint4_clearance_shift.py`, and `tests/three_dof/test_three_dof_teacher_training.py` verified the delivery-facing smoke + teacher serialization path (`22 passed`)
- [x] Submission package(paper PDF + supplementary + repo snapshot + anonymization)
  -> 2026-04-23: built `tmp/submission_bundle/journal_double_blind/anonymous_manuscript.pdf` from the staged anonymous snapshot under `tmp/submission_bundle/journal_double_blind/anonymous_snapshot/paper/`, then re-ran `python scripts/export/build_submission_bundle.py --output-dir tmp/submission_bundle/journal_double_blind --paper-pdf tmp/submission_bundle/anonymous_manuscript.pdf`
  -> build note (2026-04-23): local MiKTeX provides `pdflatex` / `bibtex`, but `latexmk` remains unusable without a Perl script engine; the successful local manuscript path is direct `pdflatex -> bibtex -> pdflatex` passes inside the anonymized snapshot
  -> final staged bundle now contains `anonymous_snapshot/`, `editor_materials/`, `submission_bundle_manifest.json`, `submission_bundle_summary.md`, `anonymous_snapshot.zip`, `editor_materials.zip`, and `anonymous_manuscript.pdf` with `paper_pdf.status = included`
  -> staging docs: `docs/submission/submission_package_checklist.md`, `docs/submission/cover_letter_draft.md`
- **Depends on:** Phase 4 complete
- **Deliverable:** submission-ready package + cover letter draft

### Phase 6: Review-Driven Revision Hardening (status: P0 complete; P1/P2 planned)
- [x] P0: Review response matrix with success criteria
- [x] P0: Teacher-coupling crossed ablation
- [x] P0: Motion-matched impedance ablation
- [x] P0: SCI sensitivity and alternative metric audit
- [x] P0: Claim-boundary rewrite and jargon removal
- [ ] P1: High-friction mechanics split, success-matched force/work, and phase portraits
- [ ] P1: Classical baselines and one or two feasible modern demo-RL baselines
- [ ] P1: Claim-to-evidence table and full reproducibility package
- [ ] P2: Orientation or cross-sim/contact-model stress layer if targeting a top-tier venue

### Phase 7.1: Sprint A Tier-3 Submission Readiness (status: local gate complete; remote CI pending)
- [x] Canonical artifact unification: default exporters and evidence-matrix outputs resolve through `artifacts/main_benchmark/main_benchmark_manifest.json`.
- [x] LaTeX build hardening: `scripts/export/build_paper_pdf.py` builds the manuscript through a direct MiKTeX-aware `pdflatex` / `bibtex` chain.
- [x] Reviewer surface: top-level `REVIEWER_GUIDE.md` and `tests/reviewer/` are copied into anonymous snapshots.
- [x] Provenance cleanup: local absolute path leakage is covered by paper-facing artifact provenance tests.
- [x] Tier-3 submission material: Robotica primary / Advanced Robotics fallback recorded; `docs/submission/cover_letter_tier3_template.md` added.
- [ ] Gate A1 remote sign-off: mark only after `reviewer-smoke` and `paper-assets-check` pass in CI on the committed branch.

## Key Questions 鈥?Resolved (2026-04-22)
1. **Phase 2.5 鈫?No-hardware**銆俈enue ceiling: Q3 upper / Q2 marginal銆侾hase 3.5/H cancelled銆?
2. ~~鐪熸満瀛︽湳鎶樻墸~~ N/A銆?
3. **Sprint 3 kickoff boundary 鈫?4 鏉′欢 teacher support quality x demo rollout budget**锛涘厛鍐荤粨灏忕煩闃碉紝涓嶅惎鍔ㄥぇ sweep銆?
4. **Hard bonus path 鈫?SG-VI + SCI already landed**; cross-sim transfer 涓哄彲閫夐澶栧姞鍒嗛」銆?
5. **Compute 鈫?GPU 鍙敤**,璁粌鍙姞閫熴€?

## Decisions Made

### Meta / Tooling Decisions
| Decision | Rationale |
|----------|-----------|
| 浣跨敤 `planning-with-files` 鏂囦欢鍖栬鍒?| 澶嶆潅澶氶樁娈电爺绌朵换鍔?|
| 鎼滅储宸ュ叿浠?`rg` 鍒囨崲鍒?PowerShell `Select-String` | `rg.exe` Access is denied |
| Planning files 鏀惧湪 `vi-insertion-only-sim/` 椤圭洰鏍?| 澶栧眰鐩綍闈?git repo |
| 褰撳墠闃舵鍙啓 planning files,涓嶆敼璁粌浠ｇ爜 | 鏈疆鏄鍒?涓嶆槸瀹炴柦 |

### Research / Scope Decisions
| Decision | Rationale |
|----------|-----------|
| 鐩爣浠?鏇存湁璇存湇鍔涚殑 benchmark paper"鍗囩骇涓?鍐?Q2 闈?OA,纭欢鍏佽鍒欏啿 Q1" | 2026-04-18 瀵硅瘽閿愯瘎;narrow-claim 瀹氫綅瀵?Q2 澶╄姳鏉夸笉瓒?|
| 鏂板 Phase 2.5 Hardware Decision Gate 涓虹嫭绔嬮樁娈?| 纭欢鍐崇瓥鏄綋鍓嶇湡姝?blocking 鐨勫叧閿喅绛?涓嶅簲鍩嬪湪 narrative lock 閲?|
| Phase 3(sim-only A 绫?涓?Phase 2.5 骞惰,涓嶇浉浜?block | ~70% sim 绔伐浣滀笌纭欢鍐崇瓥瑙ｈ€?涓嶅簲鍥?绛夊喅瀹?鍋滄墜 |
| 鏂板 Phase 3.5 Sim-to-Real Scaffolding 涓?conditional phase | 涔扮‖浠跺悗鎵嶈Е鍙?鎻愬墠鏍囪閬垮厤纭欢鍒拌揣鍚庢墠浠撲績琛?DR / adapter |
| 鏂板 Phase H Hardware Integration 涓?conditional phase | 灏嗙湡鏈?experiment 浠?sim 娴佺▼鐙珛,閬垮厤鑰﹀悎 |
| Sprint 1 鏍囪楂樺伐绋嬮闄?SAC/TD3 浠ｇ爜涓嶅瓨鍦? | findings.md 宸茬‘璁?`src/` 鏃?off-policy 鍏ュ彛 |
| Sprint 3 teacher ablation 鍏堝喕缁?4 鏉′欢灏忚竟鐣?| 2026-04-23 kickoff 灏嗙洰鏍囨敹鏁涗负 teacher support quality x demo rollout budget锛岄伩鍏嶇洿鎺ユ墿鎴愬ぇ sweep |
| `recoverable_contact_entry_rate` 闄嶇骇涓?event counter | 鐢ㄦ埛鏄庣‘鍋忓ソ;涓嶅仛 learning-curve 涓昏 |
| 璁烘枃鏀圭瑙嗕负"閲嶆帓楠ㄦ灦 + 鎻掑叆 evidence block" | 鐜版湁姝ｆ枃/appendix 鎸傜偣娓呮櫚 |
| Contribution 閲嶆瀯瑕佹眰鑷冲皯 1 鏉?`we propose` | 褰撳墠 4 鏉″叏鏄?`we show`,Q2 閫氬父闇€瑕?constructive contribution |
| Phase 2.5 = no-hardware (2026-04-22) | 鐢ㄦ埛鍐崇瓥;venue ceiling 闄嶈嚦 Q3 upper / Q2 marginal;Phase 3.5/H cancelled |
| Sprint 3 kickoff 灏忕煩闃?(2026-04-23) | support-rich/support-poor teacher 脳 few/many demo rollouts锛涘浐瀹?BC steps銆丳PO budget銆乸olicy init 涓庝簲 profile |
| Compute: GPU 鍙敤 (2026-04-22) | Sprint 2 main table 璁粌鍙敤 GPU 鍔犻€?|

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| `git status` 鍦?`F:\edge download\learning` 澶辫触:not a git repository | 1 | 纭瀹為檯浠撳簱鏍圭洰褰曚负 `F:\edge download\learning\vi-insertion-only-sim` |
| `rg.exe` 鍦ㄥ綋鍓嶇幆澧冩墽琛屽け璐?Access is denied | 1 | 鏀惧純閲嶅浣跨敤 `rg`,鏀逛负 PowerShell `Select-String` |
| PowerShell 鑷姩鍙?teacher spec 涓婁笅鏂囨椂鍖归厤鍒板涓畾涔?瀵艰嚧琛屽彿杩愮畻鎶ラ敊 | 1 | 鏀逛负鏇寸獎鐨勫崟鐐规绱?涓嶉噸澶嶅悓鏍风殑涓婁笅鏂囪剼鏈?|

## Notes
- 鏈浠诲姟浠ヨ鍒掑拰璇佹嵁缁勭粐涓轰富,涓嶉粯璁ゅ睍寮€浠ｇ爜閲嶆瀯銆?
- 鍚庣画姣忓畬鎴愪竴涓?Phase,閮借鍥炲啓 `docs/project/findings.md` 鍜?`docs/project/progress.md`銆?
- 鑻ュ彂鐜扮敤鎴疯鎯充笌浠撳簱鐜扮姸鍐茬獊,闇€瑕佹槑纭爣鍑虹害鏉熻€屼笉鏄粯璁ゅ彲琛屻€?
- **Phase 3 涓嶇瓑 Phase 2.5**:纭欢鍐崇瓥涓?block A 绫?sim 宸ヤ綔銆?
- **Phase 3.5 鏄?conditional**:浠呭湪 Phase 2.5 = buy-hardware 鍚庤Е鍙?鎻愬墠璁捐閬垮厤纭欢鍒拌揣鍚庤ˉ DR 澶辫触銆?
- **Q1 鍗囩骇璺緞**:浠呭湪 Phase 2.5 = Rizon 4s 涓?Phase H 瀹屾垚 Flexiv primitive 瀵圭収鏃舵墠鍚姩 Q1 鎶曠璺嚎銆?
- Effort 浼扮畻:person-week,鍗曚汉鍏ㄨ亴;鍗婅亴涔?2銆?
## Sprint 0 Execution Note
- `docs/project/protocol_freeze.md` created and frozen as PPO-only audit contract
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
