# 任务 05 detail 手调断点（luteolin × PCNA，1U7B）— 提示文件

> 状态：**已完成（2026-10-15）**：任务 05 由旧批次「无任务文件、引用 vina_legacy −4.60±0.53」升级为**新跑 AutoDock-GPU 补齐**（用户确认）；协议与任务 01/09 完全同源（p2rank rank2 PIP 沟，center_source=p2rank，同盒同地图）。三种子 1/7/42 均值 **−5.31 ± 0.00 kcal/mol**（seed_affinities=s1:-5.310;s7:-5.310;s42:-5.310）。三视图与 `图片/detail-05.png`（截图导出，钩子定稿）、`图片/result_05.png`（11520×6480、dpi=600）均已产出。
> 旧值 −4.60 ± 0.53（vina_legacy、legacy_blind_geometric_center）保留在 `多对多3x4_对接全表/汇总.csv` 作历史引用（engine=vina_legacy 行）；矩阵与报告主值用新 AD-GPU −5.31。

## 本任务产物（命名同兄弟任务）

- `1U7B_clean_h.pdbqt`、`5280445_clean_h.pdbqt`、`output.pdbqt`、`config.txt`、`log.txt`、`task_info.txt`
- `big-05.pse`、`surface-05.pse`、`detail-05.pse`（任务根）
- `图片/big-05.png`、`图片/surface-05.png`（Draw(fast) 5040×3653、dpi=600、ray=0）
- `图片/detail-05.png`（视口中心正方形 → 6000×6000、dpi=600）、`图片/result_05.png`（拼图）
- 氢键/残基：QJ pairs=5、CJ atoms=32（自动日志）；run_dir=`E:\RProject\_dock_m2m\runs\05_luteolin_PCNA`

## 禁止（同 SOP §7.3）

- 重建本任务（会覆盖 .pse）、`cmd.save` 写回 .pse、`cmd.png` 定稿带标签 detail、cover/内容检测裁切。
