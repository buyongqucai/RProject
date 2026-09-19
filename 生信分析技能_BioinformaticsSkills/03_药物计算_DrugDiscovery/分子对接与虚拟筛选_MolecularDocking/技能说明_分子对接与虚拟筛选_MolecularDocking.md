---
name: bioinfo-molecular-docking
description: >-
  分子对接与虚拟筛选 / MolecularDocking：验证靶点结合、虚筛排序；山水 M16。
  工具：AutoDock-GPU, AutoSite, Meeko, Vina(可选), Open Babel, PyMOL, bio3d, ggplot2。
  每个对接任务必须登记 center_source（共晶/AutoSite/P2Rank/Fpocket/文献/手填）。
  交付范式 FROZEN（2026-09-05；2026-09-06 增补 detail/result 定稿）；不做共晶重对接 RMSD 验收。
  触发：分子对接, Vina, AutoDock-GPU, 虚拟筛选, 对接盒子, 中心位点。
  流水线见文档_docs/分子对接流水线规范_DockingPipelineSOP.md；
  detail/result 定稿见 SOP §7.3/§7.4 与文档_docs/result拼图与detail导出定稿_CollageDetailExport.md；
  冻结见文档_docs/对接与交付约束_DockingFrozen.md。
  交付目录金标：桌面「痤疮_分子对接_序号文件夹」。
---

# 分子对接与虚拟筛选 / MolecularDocking

> **对接与交付 SSOT：** [`文档_docs/对接与交付约束_DockingFrozen.md`](文档_docs/对接与交付约束_DockingFrozen.md) — **`FROZEN`（2026-09-05；detail/result 2026-09-06）**。改引擎/定心/`center_source`/PyMOL 语义/detail·result 定稿/目录金标前须你说「解冻」。**定稿路径不含**共晶重对接 RMSD 自检。  
> **进化：** 你确认的截图/拼图规则只写入 SOP §7.3/§7.4（+ FROZEN 指针）；本入口不另起版本。

**流水线 SSOT：** [`分子对接流水线规范_DockingPipelineSOP.md`](文档_docs/分子对接流水线规范_DockingPipelineSOP.md)  
**盒子 / 中心登记 / 技术路线：** [`对接盒子定心与定边_DockingBoxProtocol.md`](文档_docs/对接盒子定心与定边_DockingBoxProtocol.md) · [`中心位点方法登记_CenterSourceRegistry.md`](文档_docs/中心位点方法登记_CenterSourceRegistry.md) · [`技术路线_AutoSite_AutoDockGPU.md`](文档_docs/技术路线_AutoSite_AutoDockGPU.md)  
**金标目录：** 桌面 `痤疮_分子对接_序号文件夹/`（`N/` + `图片/` 内 big/surface/detail/result；`.pse` 在任务根）

流水线摘要：下载 → 定盒并登记 `center_source` → AutoGrid → AutoDock-GPU → summary/热图 → PyMOL →（手调后）§7.3 导出 detail + §7.4 拼 result。
## 1. 数据来源

**优先** `D:\数据库\分子对接数据库\`（已下载受体/配体与登记表）；缺项再 PDB/AlphaFold / PubChem 3D。细则见 SOP §1。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；亲和力与结构 ID 须可追溯。  
对接盒子与引擎：[`技术路线_AutoSite_AutoDockGPU.md`](文档_docs/技术路线_AutoSite_AutoDockGPU.md)（定心决策树与硬护栏见该文 / FROZEN）。

### 2.1 每个任务必须说明「中心位点用了什么方法」（强制）

对接交付**不是**只交结合能：对**每一个**蛋白×配体任务，须可追溯定心方法。受控词表与落盘位置见 [`中心位点方法登记_CenterSourceRegistry.md`](文档_docs/中心位点方法登记_CenterSourceRegistry.md)。

| 场景 | 应填 `center_source` |
|------|----------------------|
| 有共晶，Meeko 包盒 | `cocrystal_meeko`（或 `cocrystal`） |
| 无共晶，AutoSite 质控通过 | `autosite` |
| AutoSite 异常后 P2Rank / Fpocket / 文献 / 手填 | `p2rank` / `fpocket` / `annotated_site` / `manual` |
| 无法定心 | `FAIL`（该任务不交付假打分） |

**落盘：** 每任务 `task_info` + `summary_vina.csv` / `summary_adgpu.csv` 的 `center_source`（及 `center_detail`/`box_qc`/`fallback_used`/`engine`）+ 蛋白表受体级字段。缺 `center_source` 的新批次视为不合格。

## 3. 何时选用本技能

- 验证靶点结合、虚筛排序；山水 M16
- 山水用途层标签：药物-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

完整步骤见 SOP。摘要：

1. 下载受体/配体 → `big/` `small/`（可在项目外）  
2. 清洗加氢 → `*_clean/` `*_clean_h/`（PDBQT）  
3. **定心定盒**（决策树见技术路线）→ 写 `task_info`：`center_source` + 细节  
4. 序号任务 `config.txt` → **默认 AutoDock-GPU**（Vina 可选对照）→ 输出 + log  
5. **登记**：`分子对接_蛋白表.csv`（含受体级 `center_source`/`ref_ligand`）+ `分子对接_化合物表.csv`（不枚举组合）  
6. **结果**：`summary_adgpu.csv`（或 `summary_vina.csv`）**每行含 `center_source`** + 结合能矩阵 / 热图  
7. PyMOL 三视图：任务根 `big|surface|detail-N.pse`；`图片/` 内同名 PNG + **`result_N.png`**；**无 `_png_tmp`**  
8. **手调 detail 后**：按 SOP **§7.3** 截图导出 `detail-N.png`，再按 **§7.4** 拼 `result_N.png`（定稿路径见 SOP；入口不复述步骤）  
9. 多组合可汇总 `可视化组合_Top10/`；项目根 git 管理

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `bio3d` | 核心 R 包 | |
| 分析 | `ggplot2` | 结合能条图等 | |
| 上游/主分析 | `AutoDock-GPU` | 对接打分（默认） | `E:\AutoDock-GPU\`；与 Vina 分表 |
| 上游/可选 | `AutoDock Vina` | 对照打分 | 非 R |
| 定心 | `AutoSite` / Meeko / P2Rank / Fpocket | 中心与盒子 | 见 CenterSourceRegistry |
| 上游/主分析 | `Open Babel` | 格式/加氢/PDBQT | 非 R |
| 3D 可视化 | `PyMOL` | ST/PT/CJ/QJ | `E:\pymol\python.exe` + `脚本_scripts/pymol_dock_viz_standard.py` |
| detail 重导 | `PyMOLWin` + `-r` 钩子 | 每任务一次；细则 SOP §7.3 | `export_detail_png_from_pse.py` + `pymol_detail_export_hook.py` |
| result 拼图 | Pillow | big+detail；细则 SOP §7.4 | `E:\PythonProject\分子对接\2.分子对接结果图组合.py` |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

结合能条图、2D 相互作用图、亲和力热图、**PyMOL 复合物图**、**result 拼图**；DPI≥600；热图 SVG+PNG；图面 English。  
**热图色标（FROZEN）：** `vmax=0`、无正值图例、无总/轴/色标标题；脚本 `plot_docking_affinity_heatmap.py`。

**PyMOL 语义（本技能写明，优先于通用习惯）：**

| 对象 | 含义 | 显示 |
|------|------|------|
| ST | 完整受体（定心+盒子决定口袋；完整入画=相机，不删原子） | big/detail：**cartoon**；surface：**仅 surface**；`protein_color`（默认 cyan） |
| PT | 最佳姿态配体 | sticks；`ligand_spectrum`（默认 **rainbow**，ADR 0001） |
| QJ | `distance(PT, not PT, mode=2)` | 虚线；`hbond_color`（默认 yellow） |
| CJ | 仅与 PT 有 QJ 的残基 | sticks；`residue_color`（默认橙） |

big/surface：完整入画、无标签；Draw(fast) **5040×3653、dpi=600、ray=0**。  
detail：自动选角 + 手调标签后只存 `.pse`；定稿 PNG = **截图导出**（SOP §7.3）。PNG 仅在 `图片/`（含 `result_N.png`）；`.pse` 在任务根。

**detail / result（用户确认定稿；正文只在 SOP）：**

- 效力摘要：清晰完整优先 → 拼图效力序 左完整不重叠 → 右等比抵虚线 → 左黑框内尽量抵框。  
- **细则唯一正文：** SOP [`§7.3`](文档_docs/分子对接流水线规范_DockingPipelineSOP.md) / [`§7.4`](文档_docs/分子对接流水线规范_DockingPipelineSOP.md)；指针 [`result拼图与detail导出定稿_CollageDetailExport.md`](文档_docs/result拼图与detail导出定稿_CollageDetailExport.md)。  
- 配色变量：`protein_color` / `residue_color` / `hbond_color` / `ligand_spectrum`（同批异色 `--auto-colors` / `--palette-json`）。

未另写条款 → [VizStandards](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)（热图标签黑 `#000000`）+ [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)。网药 FROZEN 图册由网药技能维护。
## 7. 数据结果解读

打分近似；解读须点明该任务 `center_source`。亲和力应为负值；正值先查定心/盒子再重对接。定稿路径不含共晶 RMSD 重对接验收（FROZEN）。

## 8. 能否结合其它生信

网络药理、蛋白结构、MD、ADMET；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 外部软件操作 SOP

**主文档：** [`文档_docs/分子对接流水线规范_DockingPipelineSOP.md`](文档_docs/分子对接流水线规范_DockingPipelineSOP.md)。  

样例目录仍可能 `STATUS=BLOCKED`（无真实结构时用契约桩）；有真实 PDBQT 时按 SOP 跑通 **定心登记 + AD-GPU/Vina + 热图 + PyMOL + result**。

## 样例验证

样例：`01_样例_sample/`  
**目录/出图金标：** 桌面 `痤疮_分子对接_序号文件夹/`（尤其 `10/`）  
标准 PyMOL：`脚本_scripts/pymol_dock_viz_standard.py`  
手调后截图导出：`脚本_scripts/export_detail_png_from_pse.py`（主路径：`-r pymol_detail_export_hook.py`）  
detail/result 定稿指针：[`文档_docs/result拼图与detail导出定稿_CollageDetailExport.md`](文档_docs/result拼图与detail导出定稿_CollageDetailExport.md)（SSOT 仍为 SOP §7.3/§7.4）  
手验收起代码区：`脚本_scripts/collapse_pymol_console.py`  
批量导出+拼接：`脚本_scripts/run_nuli_ting_detail_combine.py`  
Top10 汇总（默认 merge）：`脚本_scripts/collect_nuli_viz_top10.py`  
result 拼图引擎：`E:\PythonProject\分子对接\2.分子对接结果图组合.py`
