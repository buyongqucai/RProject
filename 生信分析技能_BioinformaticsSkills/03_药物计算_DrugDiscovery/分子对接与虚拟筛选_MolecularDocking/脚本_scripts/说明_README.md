# 分子对接与虚拟筛选 — 脚本

**交付目录金标：** 桌面 `痤疮_分子对接_序号文件夹/`（见 SOP §2）。  
**FROZEN（2026-09-05）：** [`../文档_docs/对接与交付约束_DockingFrozen.md`](../文档_docs/对接与交付约束_DockingFrozen.md) — 未解冻不得改路线/PyMOL 语义；**不做**共晶 RMSD 重对接。

| 文件 | 说明 |
|------|------|
| `重算蛋白表中心_recenterProteinTable.py` | 按**单一共晶配体**重原子质心重写库表 `x/y/z`；无有机共晶则清空并标记 FAIL |
| `批量对接_runBatchAdgpu.py` | **默认主路径**：共晶/AutoSite → AutoGrid → AutoDock-GPU；写 `summary_adgpu.csv` |
| `批量对接_runBatchDocking.py` | **[DEPRECATED]** 旧 Vina 批处理；仅可选对照，勿作正式交付默认 |
| `pymol_dock_viz_standard.py` | 首次三视图（完整 ST；detail 自动选角减遮挡；PNG 直写 `图片/`） |
| `export_detail_png_from_pse.py` | **手调后**导出 detail：启动 PyMOLWin + 钩子；细则 **SOP §7.3**（最大化 / buffer=4 / 满度 0.72 / 视口中心 6000²）；禁止写回 `.pse` |
| `pymol_detail_export_hook.py` | `-r` 钩子：最大化、收面板/代码区、紧取景、自适应满度、截图；由 export 脚本调用 |
| `collapse_pymol_console.py` | 仅收起代码区、不退出（手验用） |
| `run_nuli_ting_detail_combine.py` | 努力学习 Top10 + 痤疮：逐任务截图 detail 并拼 `result_*.png` |
| `collect_nuli_viz_top10.py` | 努力学习 Top10 汇总（默认 merge；`--force-wipe` 需用户明确） |
| `plot_docking_affinity_heatmap.py` | **矩形**结合能热图（PNG+SVG，DPI≥600；标签黑色；色标仅 ≤0，无正值图例） |
| `plot_docking_ring_heatmap.py` | **一对多**圆环结合能热图 + 外周 `result_N.png` 拼图（PNG+SVG，DPI≥600） |
| `dock_export_common.py` | 公共 helper：`log`（GBK 安全）、`ensure_img_subdir`、`collapse_console_qt`（Qt 收起代码区，hook/手验共用） |
| `dock_summary_schema.py` | `summary_*.csv` schema（含强制 `center_source` 等扩展列；legacy 中文列归一化） |

result 拼图引擎（Pillow）：`E:\PythonProject\分子对接\2.分子对接结果图组合.py`  
（**SOP §7.4** 定稿：左右不重叠且左完整 → 右仅白边 trim 等比抵虚线 → 左黑框内尽量抵框）  
指针文档：[`../文档_docs/result拼图与detail导出定稿_CollageDetailExport.md`](../文档_docs/result拼图与detail导出定稿_CollageDetailExport.md)  
配色变量：`--protein-color` / `--residue-color` / `--hbond-color` / `--ligand-spectrum`（与 `pymol_dock_viz_standard.py` 同名）；同批异色 `--auto-colors` 或 `--palette-json=`（例：`collage_palette.example.json`）

完整流水线：[`../文档_docs/分子对接流水线规范_DockingPipelineSOP.md`](../文档_docs/分子对接流水线规范_DockingPipelineSOP.md)  
中心方法登记：[`../文档_docs/中心位点方法登记_CenterSourceRegistry.md`](../文档_docs/中心位点方法登记_CenterSourceRegistry.md)

```bat
E:\pymol\python.exe 脚本_scripts\pymol_dock_viz_standard.py --jobs-root "<痤疮_分子对接_序号文件夹>" --all

REM 手调 detail.pse 之后（每组合只开一次 PyMOL；绝不覆盖 pse）
python 脚本_scripts\export_detail_png_from_pse.py --root "<项目根>"

REM 批量截图 detail + 拼 result
python 脚本_scripts\run_nuli_ting_detail_combine.py

REM 一对多圆环热图 + result 仪表盘
python 脚本_scripts\plot_docking_ring_heatmap.py --root "<项目根>"
```
