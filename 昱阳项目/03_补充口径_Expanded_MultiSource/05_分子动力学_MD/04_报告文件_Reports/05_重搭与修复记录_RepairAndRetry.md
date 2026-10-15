# MD 重搭与修复记录 / Repair & Retry Log

> 日期：2026-10-13；依据 [`03_MD失败原因统计_FailureTally.md`](03_MD失败原因统计_FailureTally.md) 的 A/B/C 处置方案执行。

## 1. 处置摘要

| 类别 | 体系 | 处置 | 结果 |
|------|------|------|------|
| A 姿态不稳 | 01_EGFR、03_GSK3B | **换姿态**重建初态：EGFR 用 Vina MODEL2、GSK3B 用 Vina MODEL3（`extract_vina_model(model=n)`） | 已重建工作目录 |
| B 侧链缺失 | 04_SRC、05_HIF1A | **pdbfixer 1.12 补全**：SRC LYS423 补 CG/CD/CE/NZ；HIF1A THR327 补 OG1/CG2、LYS328 补 CG/CD/CE/NZ（去氢输出，原文件存 `protein_pre_fix.pdb`） | 补全验证通过 |
| C grompp 警告 | 02_AKT1 | 两条警告定性**良性**（① Ewald 净电荷：genion 中和即消；② 排除原子 2.88 nm > cutoff：拓扑长程排除已知噪声），队列导出 `MAXWARN_IONS=5 MAXWARN_GMX=5` 放行并继续监控 | 已放行 |
| 全体加固 | 5 体系 | 受体统一 pdbfixer 修复（补缺原子、解析 altloc）：EGFR 2511→2498、AKT1 2673→2607、GSK3B 5595→5596、SRC 3599→3603、HIF1A 1783→1791 重原子 | 完成 |

## 2. 目录与登记

- 旧工作目录（含失败证据 `monitor/ABORT_REASON.txt`、`SKIPPED.txt`、GROMACS 日志）整体归档：`05_工作文件_MdWork/99_失败存档_FailedArchive/{体系}__20261013/`（3HTB 为成功体系，已移回原位）。
- 新初态已按 raw 命名登记至 `01_数据文件_Data/01_初始数据_RawInitial/{NN}_RCSB与AutoDock_MD输入_{基因}_{PDBID}/`，含 `DATA_SOURCE.md`（记录 pose 型号与 pdbfixer 修复）。
- 队列脚本 `E:\dock_yuyang\queue_yuyang_dock_md.sh`：QUEUE=01–05 全量、移除 EGFR 强制跳过块、`MAXWARN_IONS/GMX=5`、`GMX_MAXBACKUP=-1`。

## 3. 运行口径（不变）

- `LIGAND_RES=QUE NET_CHARGE=0 NS=100 CHUNK_NS=1 MONITOR=1`；看门狗阈值：背骨 RMSD > 1.0 nm / 配体 RMSD > 1.5 nm / COM > 2.0 nm 中止（[`过程看门狗_MdWatchdog.md`](../../../../../../生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/文档_docs/过程看门狗_MdWatchdog.md)）。
- 若 A 类换姿态后仍 1 ns 内解离 → 升级换口袋重对接（AutoSite 备选口袋 / `cap_and_redock.py`），再不行登记 `md重搭登记_PoseRetryRegistry.json` 机制重跑。

## 4. 重试轮次记录（同日第二轮）

首轮重排队（19:59）触发新版 `运行复合物MD_runComplexMd.sh` 门禁，暴露 2 个新问题并已处置：

| 问题 | 定位 | 处置 |
|------|------|------|
| 配体 mol2 几何门禁失败（重原子间距 min 0.078 Å） | `prep_yuyang_dock_md_inputs.py` 的 `extract_vina_model` 在 MODEL≥2 时于首个 ENDMDL 提前退出 → 空缓冲触发回退，把 Vina **9 个姿态叠进一个 mol2**（198 个重原子） | 修函数（ENDMDL 仅在目标模型结束时退出）；EGFR/GSK3B 重新 prep（单模型 27 原子 / 22 重原子）并复检几何门禁通过 |
| AKT1 蛋白主链缺口门禁（SOP §9.0.3）`EXCLUDE: long_gap chain A 448-463 len=16` | 3CQW 链 A 主域 144–447 与尾段 464–478 之间缺 16 残基 linker（尾段为游离片段） | 按「无大段缺环结构」原则**修剪游离尾段（resSeq ≥ 464）**，保留连续激酶域 144–447（303 残基；308 单残基缺口 < 阈值）；记录于 `PREP_NOTE.txt` |

- SRC（B 类修复后）**已过 pdb2gmx 与接触门禁**（pose contact 0.202 nm），进入生产段；HIF1A 排在其后。
- 19:59 轮的即时失败均带 `SKIPPED.txt`，重 prep 时已清除；`queue_yuyang_dock_md.sh` 增加命令行体系过滤参数，第二轮仅跑 01/02/03（`yuyang_queue_retry2.log`）。
- QQ 告警脚本路径问题已修：`E:\alert_kit\notify_alert.sh` 的 `powershell.exe -File` 原传 `/mnt/e/...`（Windows 侧无法解析），改为 Windows 路径 `E:\alert_kit\send_alert.ps1`。

## 5. 第三轮：脚本缺陷修复与结构修剪（同日）

| 问题 | 定位 | 处置 |
|------|------|------|
| 生产段一启动即 rc=127（SRC 20:08 实测） | `运行复合物MD_runComplexMd.sh` 调用了未定义的 `prune_md_gro_backups`（连带 `is_gro_backup_fatal`、`pipeline_alert` 也无定义）——拉取版本的脚本缺陷 | 三函数补定义（备份清理 / 仅匹配 `GMX_MAXBACKUP controls this maximum` 的备份上限 Fatal / 告警不中断）；`bash -n` 通过；同时停掉旧进程防热改脚本错位 |
| EGFR 缺口门禁 `EXCLUDE: long_gap chain A 965-976 len=12` | 1M17 链 A 主域 672–964 与游离尾段 977–995 之间缺 12 残基 | 同 AKT1：修剪游离尾段（resSeq ≥ 977），保留连续激酶域 672–964（293 残基） |
| GSK3B 结构检查 | 链 A 35–386 / 链 B 35–384 均连续无缺口 | 无需修剪；仅姿态 bug（§4）已修 |

- 第三轮队列（20:23 起）：全 5 体系顺序执行（EGFR MODEL2 → AKT1 修剪版 → GSK3B MODEL3 → SRC → HIF1A），日志 `~/md_runs/logs/yuyang_queue_retry.log`。

## 6. 第四轮：2026-10-13 夜 ～ 10-14 晨

| 事件 | 定位 | 处置 |
|------|------|------|
| EGFR MODEL2 仍飞散（20:23–20:53，ABORT：ligand RMSD max 8.732 nm > 1.5 nm） | 口袋内 2 个 Vina 姿态（MODEL1/MODEL2）均 <1 ns 解离 | **A 类升级为换口袋重对接**（AutoSite 备选口袋 / `cap_and_redock.py`）——待执行，重对接前 EGFR 不入列 |
| AKT1 生产段推进至 ~6.9 ns 后 mdrun exit=1（23:45） | 机器休眠挂起 WSL：mdrun 被杀、drvfs 报 `Input/output error`（队列写 STATUS 失败即中断，GSK3B/SRC/HIF1A 未跑） | 队列 STATUS 写入加 `|| true` 防中断；`md.cpt` 检查点完好，支持断点续跑 |
| 10-14 晨重启队列秒退（rc=2，`set: pipefail: invalid option name`） | `运行复合物MD_runComplexMd.sh` 混入 CRLF 行尾（疑似休眠期 drvfs 异常） | `sed` 清 CRLF + `bash -n` 通过后重启 |
| 失败作业遗留 `SKIPPED.txt` 被队列跳过 | 失败即写 SKIPPED 的约定与重试语义冲突 | 重试前清 `SKIPPED.txt`/`ABORT_REASON.txt`（失败证据已归档 `99_失败存档_FailedArchive/`） |
| 第四轮队列 08:58 起 | AKT1 自 **6.9 ns** 断点续跑（`-cpi md.cpt`），GSK3B（MODEL3，几何门禁 1.22 Å 通过）→ SRC → HIF1A 顺序入列 | 运行中；日志 `~/md_runs/logs/queue_yuyang_4.log`；watchdog + QQ 告警在岗 |
