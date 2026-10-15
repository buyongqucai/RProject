# 配体飞散/骨架展开（RMSD/COM 越界）— 先判 PBC 假象

- 日期/体系：2026-10-13；ESR2/FOS/PPARG/CYP1A1（努力学习 Top3 等）
- 状态：已解决（监控已免疫门禁）

## 症状（怎么发现的）
监控 ABORT：`backbone RMSD max 3.9–5.2 nm > 1.0 (possible unfold)`、`ligand RMSD max 2.4–13.3 nm`、`COM distance max 2.6–6.6 nm > 2.0`。多体系 1ns 内同时"飞散/展开"。

## 判定（真异常还是假象）
1. `gmx mindist -s md.tpr -f md.xtc -od mindist.xvg`（Protein/LIG，最小镜像）：**全程 0.15–0.26nm ⇒ 从未分离，假象**。
2. 配体自 RMSD（fit LIG / rmsd LIG，先 `trjconv -pbc mol`）：≤0.12nm ⇒ 配体完好。
3. 逐链骨架自 RMSD（python Kabsch，链内 fit）：0.16–0.45nm ⇒ 蛋白没散。
4. 假象特征：合并 RMSD 序列"3.9→0.5→3.9"振荡（**散了又合回来=物理不可能**）；t=0 即 COM 5.6nm。
5. 真实飞散特征：mindist 单调增大 >1nm + 配体自 RMSD 大（拓扑坏）或小（整体脱离）。

## 补救（按序尝试）
1. 分析端：`gmx trjconv -pbc mol`（逐分子完整）；多链复合物整体成像用 `-pbc cluster`（聚类组须整分子，如 non-Water），参考帧取成像后首帧。
2. 门禁端（已自动化）：`过程监控_monitorMdRun.sh` 改 **mindist 解离门禁（≤1.0nm）+ 配体自 RMSD 完整性门禁（≤1.0nm）**；合并 BB RMSD 仅记录不熔断。
3. 已中止的体系：判定为假象后**可从 md.cpt 续跑**（不违 SOP「不续跑真飞散初态」）。

## 何时放弃
mindist >1nm 且配体自 RMSD 正常 ⇒ 真解离，A3 姿态不稳：按 SOP §9.0.2 走自动重搭（A1/A2 优先）一轮，仍失败弃。

## 复盘
根因：`gmx trjconv/rms` 的 PBC 语义——多分子跨周期镜像时合并 RMSD/COM 虚高。预防：门禁已换免疫指标；分析管线先整体成像再算 RMSD。
