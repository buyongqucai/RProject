# 任务 14 detail 手调断点（quercetin × DNMT1，3EPZ）— 提示文件

> 状态：**首轮自动出图已完成，停在 detail 手调断点**（SOP §7.2/§7.3；未手调，未出定稿 detail）。

## 已自动生成（本轮）

- `图片/big-14.png`、`图片/surface-14.png`（Draw(fast) 5040×3653、dpi=600、ray=0）
- `big-14.pse`、`surface-14.pse`、`detail-14.pse`（任务根）
- 氢键/残基：QJ pairs=5、CJ atoms=33（自动日志）
- detail 首轮**只写 `.pse`、不出 PNG**（FROZEN：带标签 detail 禁止 `cmd.png` 定稿）

## 手调 + 定稿步骤（SOP §7.3 唯一路径，每任务只开一次 PyMOLWin）

1. `E:\pymol\PyMOLWin.exe "detail-14.pse" -r pymol_detail_export_hook.py`（钩子在技能 `脚本_scripts/pymol_detail_export_hook.py`）
2. **最大化窗口**（日志须 IsZoomed=True）→ 手调残基/氢键标签位置（字号 24、一位小数、不外推；只动标签，不删原子）
3. 钩子截图导出 `图片/detail-14.png`（视口中心正方形 → 6000×6000、dpi=600）；`detail-14_debug_window.png` 仅调试，验收完删除
4. 禁止：重建本任务（会覆盖 .pse）、`cmd.save` 写回 .pse、`cmd.png` 定稿、cover/内容检测裁切

## result 拼图（SOP §7.4，detail 定稿后）

- `E:\PythonProject\分子对接\2.分子对接结果图组合.py`（模板 `背景图.png` 同目录）→ `图片/result_14.png`（11520×6480、dpi=600）
- 效力序：左右不重叠 + 左图完整铺开 → 右图锁纵横比抵虚线 → 左图口袋尽量抵黑框

**未完成手调前，detail-14.png / result_14.png 不得当定稿交付。**
