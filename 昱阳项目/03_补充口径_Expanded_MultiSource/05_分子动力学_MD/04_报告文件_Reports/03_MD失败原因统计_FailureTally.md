# MD 本地失败原因统计 / Failure Tally

> 统计日期：2026-10-13；范围：`05_工作文件_MdWork/` 全部 6 个体系（5 个槲皮素对接体系 + 3HTB 烟测体系）。
> 证据来源：各工作目录 `monitor/ABORT_REASON.txt`、`SKIPPED.txt`、GROMACS 日志（`pdb2gmx.log`、`grompp_ions.log`）。

## 1. 总览

| 体系 | 结果 | 失败阶段 | 直接原因（日志原文摘要） |
|------|------|----------|--------------------------|
| 01_EGFR_1M17_Quercetin | ✗ 中止 | 1.0 ns 生产监控 | `ligand RMSD max 11.397 nm > 1.5 nm (ligand fly/dissociate)` — 配体飞出结合口袋 |
| 02_AKT1_3CQW_Quercetin | ✗ 跳过 | 体系构建 grompp(ions) | `Fatal error: Too many warnings (2). use the -maxwarn option` — 拓扑/参数警告超限 |
| 03_GSK3B_1H8F_Quercetin | ✗ 中止 | 1.0 ns 生产监控 | `backbone RMSD max 4.859 nm > 1.0 nm (possible unfold)`；`ligand RMSD max 10.467 nm > 1.5 nm`；`COM distance max 4.859 nm > 2.0 nm` — 蛋白解折叠 + 配体解离 |
| 04_SRC_2SRC_Quercetin | ✗ 跳过 | pdb2gmx 拓扑生成 | `Residue 340 named LYS ... atom CG ... is not found in the input file` — 残基侧链原子缺失 |
| 05_HIF1A_4H6J_Quercetin | ✗ 跳过 | pdb2gmx 拓扑生成 | `Residue 90 named THR ... atom CG2 ... is not found in the input file` — 残基侧链原子缺失 |
| 3HTB_JZ4_100ns | ✓ 完成 | — | 100 ns 跑完；中途曾因 `GMX_MAXBACKUP` 在 6.0 ns 停摆，设 `-1` 后自 `md.cpt` 续跑（见 `01_STATUS.txt`） |

## 2. 按根因归类

> 处置执行记录见 [`05_重搭与修复记录_RepairAndRetry.md`](05_重搭与修复记录_RepairAndRetry.md)（2026-10-13 已执行 A/B/C 修复并重排队）。

### A. 对接姿态不稳（1、3 号）→ 重搭初态后重跑
配体在 1 ns 内飞出/解离，为初始姿态或结合位点摆放问题，不是 MD 参数问题。
- 证据：`05_工作文件_MdWork/01_EGFR_1M17_Quercetin/monitor/ABORT_REASON.txt`、`05_工作文件_MdWork/03_GSK3B_1H8F_Quercetin/monitor/ABORT_REASON.txt`（配 RMSD/COM 监控图 `monitor/*.png`）。
- 处置：换姿态/换口袋重对接 → 重建初态 → 重新排队。可复用技能 `脚本_scripts/自动重搭初态_rebuildPoseRetry.py` + `md重搭登记_PoseRetryRegistry.json` 的登记机制（现登记表仅含努力学习 top3，本项目 5 体系可按同格式补登）。

### B. 蛋白结构不完整（4、5 号）→ 补全残基后重跑
pdb2gmx 因侧链原子缺失失败：SRC `LYS340` 缺 `CG`；HIF1A `THR90` 缺 `CG2`。晶体结构缺原子/非标准建模所致。
- 证据：`05_工作文件_MdWork/04_SRC_2SRC_Quercetin/pdb2gmx.log`、`05_工作文件_MdWork/05_HIF1A_4H6J_Quercetin/pdb2gmx.log`。
- 处置：受体预处理补全缺失侧链（pdbfixer / ChimeraX `repair` / 让 pdb2gmx 选替代构象），再重跑；或换同靶点备选 PDB。

### C. 体系构建警告超限（2 号）→ 检查配体参数后重跑
`grompp(ions)` 报 2 个警告超限（`Too many warnings`）。
- 证据：`05_工作文件_MdWork/02_AKT1_3CQW_Quercetin/grompp_ions.log`（`mdout.mdp` 同目录）。
- 处置：查警告内容（多为配体电荷/原子类型或近距约束）；确认无害可加 `-maxwarn`，否则修 acpype 参数或初始构象接触。

## 3. 队列与口径

- 队列原始清单：`02_MD队列_Queue.txt`（01–05 号 + 3HTB 先行）；3HTB 已产出 24 图（`03_图片文件_Figures/3HTB_JZ4_100ns/`、`03_图片文件_Figures/3HTB_JZ4_100ns/`）。
- 5 个失败体系均**未产出**分析图；补救重跑前不进入出图环节。
- 看门狗口径（背骨 RMSD > 1.0 nm / 配体 RMSD > 1.5 nm / COM > 2.0 nm 即中止）见技能 `文档_docs/过程看门狗_MdWatchdog.md`。
