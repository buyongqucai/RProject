# 备份清单 · 对接热图按筛选分支拆分 + 06 存放修正（2026-10-14 23:20）

改动前备份（13 文件，保持相对路径）。改动内容：

1. 合拼热图作废（移入本备份，不删）：`06_分子对接/结果文件/图片文件/04_对接亲和力热图_DockingAffinityHeatmap.{png,svg}`；报告侧副本 `00_全流程报告/结果文件/图片文件/dock.png`、`panel_06_对接.png`（项目 + 交付文件镜像各一份）。
2. `06_分子对接/结果文件/文档文件/`（3 个 md）并入 `结果文件/报告文件/`（文件名不变）。
3. 报告 `论文版_全流程.html` / `方法版_全流程.html`（项目 + 镜像）：图 15 合拼热图 → 图 15a（成分轨）/ 图 15b（代谢物轨）分图。
4. 新增分轨热图（正式引擎 `plot_docking_affinity_heatmap.py`）：
   - `矩阵_结合能热图_成分_DockingAffinityHeatmapCompounds.{png,svg}`（8 配体 × 8 受体）
   - `矩阵_结合能热图_代谢物_DockingAffinityHeatmapMetabolites.{png,svg}`（8 配体 × 6 受体）
   数值仅取真表 `成分对接汇总.csv` / `代谢物对接汇总.csv` 的三种子均值 mean_kcal。

分组依据（12 组任务 = C* 双轨终筛达阈 12 对）：
- 成分轨：筛选步骤① 成分 B–C* Degree Top L=8（selection_rule=`TopL by B-C* degree`）
- 代谢物轨：筛选步骤③ 代谢物 Tier A* Top M=8（selection_rule=`TopM by H-in-C*, n_C*, GMMAD2`）
- 靶点：步骤② C* 上 PPI Top T=8，各配体配其 C* 邻居中 PPI 最前（优先落入 Top 靶点）1 个基因。

未动：`交付文件/06_分子对接/`（轨 B 归档快照，报告引用其 `对接汇总.csv`/`对接全表.csv` 作归档批次）、MD 图册、`E:\Origin_Data\`。
