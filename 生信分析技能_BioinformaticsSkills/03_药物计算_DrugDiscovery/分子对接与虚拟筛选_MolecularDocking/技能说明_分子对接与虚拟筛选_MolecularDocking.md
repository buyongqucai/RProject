---
name: bioinfo-molecular-docking
description: >-
  分子对接与虚拟筛选 / MolecularDocking：验证靶点结合、虚筛排序；山水 M16。工具：bio3d, ggplot2, AutoDock Vina, Open Babel, PyMOL。
  触发：分子对接, Vina, 虚拟筛选。流水线见文档_docs/分子对接流水线规范_DockingPipelineSOP.md。
  交付目录金标：桌面「痤疮_分子对接_序号文件夹」。
---

# 分子对接与虚拟筛选 / MolecularDocking

**流水线 SSOT（强制）：** [`文档_docs/分子对接流水线规范_DockingPipelineSOP.md`](文档_docs/分子对接流水线规范_DockingPipelineSOP.md)  
**交付目录金标（强制对齐）：** 桌面 `痤疮_分子对接_序号文件夹/`（任务 `N/` + `图片/` 内 big/surface/detail/result；`.pse` 在任务根；无 `_png_tmp`；项目根 git）

（下载 → 命名/目录 → 清洗加氢 → Vina → 登记表与结合能矩阵 → PyMOL ST/PT/CJ/QJ → result 拼图 → 热图）

## 1. 数据来源

PDB/AlphaFold 结构；配体 PubChem 3D / SMILES。细则见 SOP §1。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；**禁止编造**亲和力或结构 ID。  
对接盒子须用活性位点/共晶配体中心，禁止误用整链 COM（易致正结合能）。

## 3. 何时选用本技能

- 验证靶点结合、虚筛排序；山水 M16
- 山水用途层标签：药物-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

完整步骤见 SOP。摘要：

1. 下载受体/配体 → `big/` `small/`（可在项目外）  
2. 清洗加氢 → `*_clean/` `*_clean_h/`（PDBQT）  
3. 序号任务 `config.txt` → Vina → `output.pdbqt` + `log.txt`  
4. **登记**：`分子对接_蛋白表.csv` + `分子对接_化合物表.csv`（不枚举组合）  
5. **结果**：`summary_vina.csv` + 结合能矩阵 xlsx / 热图  
6. PyMOL 三视图：任务根 `big|surface|detail-N.pse`；`图片/` 内同名 PNG + **`result_N.png`**；**无 `_png_tmp`**  
7. **手调 detail 后**：只用 `export_detail_png_from_pse.py` 截图重导 PNG（每任务开一次 `PyMOLWin.exe detail-N.pse -r pymol_detail_export_hook.py` → **最大化后 PyMOL Qt API 收起代码区** → 截图）；**禁止** `cmd.png` 离屏重渲 / 写回 `.pse`；再拼 `result_N.png`  
8. 多组合项目可另汇总 `可视化组合_Top10/`（结构同金标：`.pse` 在子目录根，PNG 在 `图片/`）  
9. 项目根须 **git** 管理

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `bio3d` | 核心 R 包 | |
| 分析 | `ggplot2` | 结合能条图等 | |
| 上游/主分析 | `AutoDock Vina` | 对接打分 | 非 R |
| 上游/主分析 | `Open Babel` | 格式/加氢/PDBQT | 非 R |
| 3D 可视化 | `PyMOL` | ST/PT/CJ/QJ | `E:\pymol\python.exe` + `脚本_scripts/pymol_dock_viz_standard.py` |
| detail 重导 | `PyMOLWin` + Qt API 钩子 | 每组合开一次；`-r pymol_detail_export_hook.py` 最大化后 `toggle_command_log(False)` + 隐藏 bottom dock | `export_detail_png_from_pse.py` |
| result 拼图 | Pillow | big+detail 局部放大图 | `E:\PythonProject\分子对接\2.分子对接结果图组合.py` |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

结合能条图、2D 相互作用图、亲和力热图、**PyMOL 口袋图**、**result 拼图**；**DPI≥600；SVG+PNG（热图）；图面 English；防遮挡**。

**PyMOL（本技能写明，优先于通用习惯）：**

| 对象 | 含义 | 显示 |
|------|------|------|
| ST | 受体 | big/detail：**cartoon**；surface：**仅 surface（无 cartoon）** |
| PT | 最佳姿态配体 | sticks；**默认 rainbow 配色**（用户明确提出才更换；3D 结构图为本技能写明条款，不受 VizStandards 禁彩虹约束） |
| QJ | `distance(PT, not PT, mode=2)` 氢键 | 黄色虚线 |
| CJ | **仅与 PT 有 QJ 的残基** | **橙色** sticks；无氢键不显示 |

big/surface：完整入画（防 clip），**无标签**；detail：**1:1**，残基 + 氢键长度标签（一位小数；`label_font_id=5`；字号 **24**；不外推，用户手调）。  
PNG **只**在 `图片/`（含 `result_N.png`）；**.pse 在任务根**；**禁止** `_png_tmp`。  

手调后重导（SOP §7.3）：每任务 **只开一次** `PyMOLWin.exe detail-N.pse -r pymol_detail_export_hook.py` → 最大化 → **PyMOL Qt API 收起底部代码区**（`toggle_command_log(False)`、`toggle_lineedit()`、`dockWidget.hide()`）→ 截图；禁止 `cmd.png`（标签相对变小）。勿在 PyMOL 命令行 `run hook,main`（`__file__` 会错位）。  
result（SOP §7.4）：detail 按关键内容（残基/配体/氢键/标签）紧裁，**排除蛋白丝带主色**，尽量放大填满右侧虚线框。

**出图规范回退：** 本技能未另写的条款，**先用** [统一可视化规范_VizStandards](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。热图：**行/列名与格内数值标签一律黑色 `#000000`**。

**对齐高分期刊范式：** 遵循 [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)。**网络药理学视觉轨已 FROZEN，本技能不得改网药样例图。**

## 7. 数据结果解读

打分近似；勿单凭对接定药效。亲和力应为负值；正值须查盒子并重对接。

## 8. 能否结合其它生信

网络药理、蛋白结构、MD、ADMET；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 外部软件操作 SOP

**主文档：** [`文档_docs/分子对接流水线规范_DockingPipelineSOP.md`](文档_docs/分子对接流水线规范_DockingPipelineSOP.md)。  

样例目录仍可能 `STATUS=BLOCKED`（无真实结构时用契约桩）；有真实 PDBQT 时按 SOP 跑通 Vina + 热图 + PyMOL + result。

## 样例验证

样例：`01_样例_sample/`  
**目录/出图金标：** 桌面 `痤疮_分子对接_序号文件夹/`（尤其 `10/`）  
标准 PyMOL：`脚本_scripts/pymol_dock_viz_standard.py`  
手调后截图导出：`脚本_scripts/export_detail_png_from_pse.py`（主路径：`-r pymol_detail_export_hook.py`）  
手验收起代码区：`脚本_scripts/collapse_pymol_console.py`  
批量导出+拼接：`脚本_scripts/run_nuli_ting_detail_combine.py`  
Top10 汇总（默认 merge）：`脚本_scripts/collect_nuli_viz_top10.py`  
result 拼图引擎：`E:\PythonProject\分子对接\2.分子对接结果图组合.py`
