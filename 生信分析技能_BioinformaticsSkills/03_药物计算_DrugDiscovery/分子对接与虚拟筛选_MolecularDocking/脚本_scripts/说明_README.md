# 分子对接与虚拟筛选 — 脚本

**交付目录金标：** 桌面 `痤疮_分子对接_序号文件夹/`（见 SOP §2）。

| 文件 | 说明 |
|------|------|
| `运行骨架_runSkeleton.R` | R 侧骨架入口 |
| `pymol_dock_viz_standard.py` | 首次三视图（ST/PT/CJ/QJ；PNG 直写 `图片/`） |
| `export_detail_png_from_pse.py` | **手调后**导出 detail：每任务 `PyMOLWin.exe detail-N.pse -r pymol_detail_export_hook.py` → 最大化 → **Qt API 收起代码区** → 截图；禁止写回 `.pse` |
| `pymol_detail_export_hook.py` | PyMOL `-r` 钩子（`toggle_command_log` / `dockWidget.hide`）；由 export 脚本调用 |
| `collapse_pymol_console.py` | 仅收起代码区、不退出（手验用） |
| `run_nuli_ting_detail_combine.py` | 努力学习 Top10 + 痤疮：逐任务截图 detail 并拼 `result_*.png` |
| `collect_nuli_viz_top10.py` | 努力学习 Top10 汇总（默认 merge；`--force-wipe` 需用户明确） |
| `plot_docking_ring_heatmap.py` | **一对多**圆环结合能热图 + 外周 `result_N.png` 拼图（PNG+SVG，DPI≥600） |

result 拼图引擎（Pillow）：`E:\PythonProject\分子对接\2.分子对接结果图组合.py`  
（detail 按关键内容紧裁放大、排除蛋白丝带主色 → 填满右侧虚线框）

完整流水线：[`../文档_docs/分子对接流水线规范_DockingPipelineSOP.md`](../文档_docs/分子对接流水线规范_DockingPipelineSOP.md)

```bat
E:\pymol\python.exe 脚本_scripts\pymol_dock_viz_standard.py --jobs-root "<痤疮_分子对接_序号文件夹>" --all

REM 手调 detail.pse 之后（每组合只开一次 PyMOL；绝不覆盖 pse）
python 脚本_scripts\export_detail_png_from_pse.py --root "<项目根>"

REM 批量截图 detail + 拼 result
python 脚本_scripts\run_nuli_ting_detail_combine.py

REM 一对多圆环热图 + result 仪表盘
python 脚本_scripts\plot_docking_ring_heatmap.py --root "<项目根>"
```
