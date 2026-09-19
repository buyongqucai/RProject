# 02 — summary_vina.csv 双 schema 统一

标签: 已完成（2026-08-30，commit 61538fd）

## 来源

Standards 轴（Primitive Obsession / 缺 schema）。

## 问题

同一 `summary_vina.csv`：`pymol_dock_viz_standard.py:561-566` 读 `best_affinity_kcal`/`对接序号`；`plot_docking_ring_heatmap.py:83-88` 读 `affinity_kcal_mol`/`task`/`ligand`。SOP §5 未定义该表列。跨项目必崩其一。

## 验收标准

- SOP §5 写明 `summary_vina.csv` 唯一 schema（列名、含义、示例行）；
- 两个脚本改为读同一 schema，或对旧列名做显式兼容映射并标注弃用；
- 用 `杨程茗分子对接` 与金标 `痤疮_分子对接_序号文件夹` 各跑一次验证。
