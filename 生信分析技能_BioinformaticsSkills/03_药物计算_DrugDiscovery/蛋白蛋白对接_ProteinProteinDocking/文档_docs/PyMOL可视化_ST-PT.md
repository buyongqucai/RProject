# PyMOL 可视化（ST / PT / CJ / QJ）— 蛋白–蛋白对接

> 对象名与分子对接对齐；语义改为双蛋白。  
> detail/result **定稿规则不双写**：分子对接 SOP §7.3/§7.4。  
> 标准脚本：[`脚本_scripts/pymol_pp_dock_viz_standard.py`](../脚本_scripts/pymol_pp_dock_viz_standard.py)

## 1. 对象语义

| 对象 | 含义 | 显示 |
|------|------|------|
| **ST** | 固定侧蛋白（通常更大；ZDOCK Protein 1） | big：**半透明 cartoon**；surface：**仅 surface（transparency=0.35）**；detail：**高透明 cartoon（0.85）**；默认 `cyan` |
| **PT** | 移动侧蛋白（通常较小；ZDOCK Protein 2） | big/detail：**半透明/高透明 cartoon**；界面 sticks；默认与 ST 异色 |
| **QJ** | ST↔PT 分子间接触/氢键 | `distance` 虚线；默认 yellow |
| **CJ** | 参与 QJ 的界面残基（**两侧**） | sticks；默认 orange；detail 标签 |

**标签（对齐分子对接 §7.1 + PP 补强）：** `label_color=black`；`label_font_id=5`；字号 **24**；`label_digits=1`；`label_shadow_mode=0`；`label_outline_color=black`；**`label_bg_transparency=1` + `label_bg_outline=0`（关掉默认半透明白底，否则像白边）**。

氢键/接触建议：

```python
cmd.distance("QJ", "(PT)", "(ST)", quiet=1, mode=2, label=1, reset=1)
```

CJ：由 QJ 配对残基并集生成（ST 与 PT 两侧），禁止为减负删除 ST/PT 主链原子（完整入画=相机 zoom/clip）。

## 2. 视图与文件

**存放：** 每个构象一个数字任务夹（桌面 `{ST}_{PT}_蛋白蛋白对接_序号文件夹/N/`），与分子对接金标同构；`.pse` 在任务根，PNG **只**在该夹 `图片/`。细则见流水线 SOP §0 / §0.1 与 [`对接与交付基线_PPDockBaseline.md`](对接与交付基线_PPDockBaseline.md)。

| 产物 | 内容 |
|------|------|
| `big-N.pse` / `图片/big-N.png` | ST+PT cartoon + CJ + QJ；无残基标签 |
| `surface-N.pse` / `图片/surface-N.png` | ST surface + PT cartoon/surface 策略见脚本；+ CJ/QJ；无标签 |
| `detail-N.pse` | 透明 cartoon + CJ 界面 + 标签；**手调后**再截图 |
| `图片/detail-*.png` | 用户截图 → `prepare_detail_square.py` 切方（禁止定稿用偷懒 `cmd.png` 代替手调） |
| `图片/result_*.png` | 同一 big + 对应 detail；`combine_pp_result.py` |

`--out-dir` 必须指向该任务夹（例：`…_蛋白蛋白对接_序号文件夹/1`）。

big/surface：Draw(fast) 默认 **5040×3653、dpi=600、ray=0**（对齐分子对接）。

## 3. detail / result 定稿（指针）

| 步骤 | 文档/脚本 |
|------|-----------|
| 手调标签后截图 | 分子对接 SOP **§7.3**；窗口最大化；用户截图优先 |
| 切正方形 | `脚本_scripts/prepare_detail_square.py`（白边 + 近白行/列 → 居中切方，禁垫白） |
| 拼图 | SOP **§7.4**；`combine_pp_result.py` → `E:\PythonProject\分子对接\2.分子对接结果图组合.py` |
| 指针摘要 | [`result拼图与detail导出定稿_CollageDetailExport.md`](../../分子对接与虚拟筛选_MolecularDocking/文档_docs/result拼图与detail导出定稿_CollageDetailExport.md) |

取景仍以 `zoom(PT or CJ, buffer=4)` 等钩子逻辑为准（有 CJ 则 `PT or CJ`）。

## 4. 配色变量

| 变量 | 默认 | 对象 |
|------|------|------|
| `st_color` / `protein_color` | cyan | ST |
| `pt_color` | salmon | PT cartoon |
| `residue_color` | orange | CJ |
| `hbond_color` | yellow | QJ |

同批异色可用 `--palette-json`（格式可参考分子对接 `collage_palette.example.json`）。

## 5. 禁止

- 用对接前并排检查图冒充对接构象  
- 未手调标签就交付 detail/result 定稿  
- 覆盖已有手调 `detail-N.pse`（须先备份）  
