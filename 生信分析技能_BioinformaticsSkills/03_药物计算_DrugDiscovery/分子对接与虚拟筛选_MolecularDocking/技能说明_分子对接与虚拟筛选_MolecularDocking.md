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

> **对接与交付 SSOT：** [`文档_docs/对接与交付约束_DockingFrozen.md`](文档_docs/对接与交付约束_DockingFrozen.md) — 状态 **`FROZEN`（2026-09-05；2026-09-06 增补 detail/result）**。未经「解冻 / unfreeze」不得改引擎路线、定心决策树、`center_source` 登记、PyMOL 语义、detail 断点/截图定稿、result 拼图效力序、目录金标。**不做共晶重对接 RMSD 自检。**

**流水线 SSOT（强制）：** [`文档_docs/分子对接流水线规范_DockingPipelineSOP.md`](文档_docs/分子对接流水线规范_DockingPipelineSOP.md)  
**对接盒子 SSOT：** [`文档_docs/对接盒子定心与定边_DockingBoxProtocol.md`](文档_docs/对接盒子定心与定边_DockingBoxProtocol.md)  
**中心方法登记 SSOT（强制）：** [`文档_docs/中心位点方法登记_CenterSourceRegistry.md`](文档_docs/中心位点方法登记_CenterSourceRegistry.md) — **每个对接任务必须写明 `center_source`**  
**当前指定技术路线：** [`文档_docs/技术路线_AutoSite_AutoDockGPU.md`](文档_docs/技术路线_AutoSite_AutoDockGPU.md)（**有共晶则包盒定心；否则 AutoSite + AutoDock-GPU；异常回退 P2Rank/Fpocket**）  
**交付目录金标（强制对齐）：** 桌面 `痤疮_分子对接_序号文件夹/`（任务 `N/` + `图片/` 内 big/surface/detail/result；`.pse` 在任务根；无 `_png_tmp`；项目根 git）

（下载 → 定盒并**登记中心方法** → AutoGrid → **AutoDock-GPU** → 登记表/`summary_*`（含 `center_source`）与结合能矩阵 → PyMOL → 热图；Vina 仅作可选对照；**无**共晶 RMSD 重对接步骤）
## 1. 数据来源

**优先** `D:\数据库\分子对接数据库\`（已下载受体/配体与登记表）；缺项再 PDB/AlphaFold / PubChem 3D。细则见 SOP §1。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；**禁止编造**亲和力或结构 ID。  
对接盒子与引擎：默认按 [`技术路线_AutoSite_AutoDockGPU.md`](文档_docs/技术路线_AutoSite_AutoDockGPU.md)（AutoSite → AutoDock-GPU；异常回退 P2Rank/Fpocket）。禁止整链 COM、禁止全 HETATM 平均、禁止固定边长 22。

### 2.1 每个任务必须说明「中心位点用了什么方法」（强制）

对接交付**不是**只交结合能：对**每一个**蛋白×配体任务，须可追溯定心方法。受控词表与落盘位置见 [`中心位点方法登记_CenterSourceRegistry.md`](文档_docs/中心位点方法登记_CenterSourceRegistry.md)。

| 场景 | 应填 `center_source` |
|------|----------------------|
| 有共晶，Meeko 包盒 | `cocrystal_meeko`（或 `cocrystal`） |
| 无共晶，AutoSite 质控通过 | `autosite` |
| AutoSite 异常后 P2Rank / Fpocket / 文献 / 手填 | `p2rank` / `fpocket` / `annotated_site` / `manual` |
| 无法定心 | `FAIL`（不得冒充打分） |

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
8. **手调 detail 后**：按 SOP **§7.3** 截图重导 `detail-N.png`（最大化 + 紧取景 + 自适应满度）；**禁止** `cmd.png` / 写回 `.pse`；再按 **§7.4** 拼 `result_N.png`  
9. 多组合项目可另汇总 `可视化组合_Top10/`；项目根须 **git** 管理

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
| detail 重导 | `PyMOLWin` + `-r` 钩子 | 每任务开一次；最大化 → 紧取景 → 视口中心正方形 6000²（SOP §7.3） | `export_detail_png_from_pse.py` + `pymol_detail_export_hook.py` |
| result 拼图 | Pillow | big+detail；右图仅白边 trim 等比抵虚线（SOP §7.4） | `E:\PythonProject\分子对接\2.分子对接结果图组合.py` |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

结合能条图、2D 相互作用图、亲和力热图、**PyMOL 对接复合物图**、**result 拼图**；**DPI≥600；SVG+PNG（热图）；图面 English；防遮挡**。  
**结合能热图色标（FROZEN）：** `vmax=0`，图例**不得**出现正值；**无**总标题/轴标题/色标标题/底部脚注；脚本 `plot_docking_affinity_heatmap.py`。

**PyMOL（本技能写明，优先于通用习惯）：**

| 对象 | 含义 | 显示 |
|------|------|------|
| ST | 完整受体（口袋由定心工具+盒子决定；禁止减负删原子） | big/detail：**cartoon**；surface：**仅 surface（无 cartoon）**；色=`protein_color`（默认 cyan） |
| PT | 最佳姿态配体 | sticks；色=`ligand_spectrum`（默认 **rainbow**；用户明确提出才更换；3D 结构图为本技能写明条款，不受 VizStandards 禁彩虹约束） |
| QJ | `distance(PT, not PT, mode=2)` 氢键 | 虚线；色=`hbond_color`（默认 yellow） |
| CJ | **仅与 PT 有 QJ 的残基** | sticks；色由 **`residue_color`**（默认橙色）；无氢键不显示 |

**完整入画：** 相机 zoom/clip，保证当前显示对象完整进画面且不被近远裁切面切黑；**≠** 裁掉蛋白。  
**detail：** 导出前自动旋转选角，减轻配体/氢键/残基及标签在 2D 截图中的遮挡；再手调标签。  
big/surface：**完整入画**，**无标签**；导出对齐 GUI **Draw (fast)**：**5040×3653、dpi=600、ray=0**。  
detail：自动选角 + 标签后只存 `.pse`；**定稿 PNG 用截图导出**（不用 `cmd.png`，避免标签变小）。  
PNG **只**在 `图片/`（含 `result_N.png`）；**.pse 在任务根**；**禁止** `_png_tmp`。  

**detail / result 定稿（2026-09-06 用户确认；细则 SOP §7.3 / §7.4，勿在本处另起版本）：**

- **第一原则：清晰完整** — 中心残基/配体/氢键/标签须全部在 `detail-N.png` 内；拼图找不回被截掉的内容。宁可略空，不要裁切。  
- **detail 导出：** 每任务只开一次 `PyMOLWin.exe detail-N.pse -r pymol_detail_export_hook.py` → **最大化**（`IsZoomed=True`）→ 隐藏侧栏 + 收起底部代码区 → **始终** `zoom(PT|CJ, buffer=4)`（禁止保留过宽手调缩放）→ 自适应拉近目标满度 **0.72**（标签余量 1.15）→ 顶栏剥离 → **视口几何中心**正方形 → 6000²。禁止 `cmd.png` / cover 裁切 / 内容检测再裁 / 写回 `.pse`。可调：`PYMOL_DETAIL_BUFFER` / `PYMOL_DETAIL_FILL_TARGET` / `PYMOL_DETAIL_LABEL_PAD`。  
- **result 拼图效力序：** ① 左右不重叠，左图完整铺开丝带等（实线黑框**不是**裁切框）→ ② 右图完整 + 锁纵横比 + 仅白边 trim 后等比抵虚线 → ③ 左关键簇尽量抵黑框（不得破坏①）。  
- **配色变量：** `protein_color` / `residue_color` / `hbond_color` / `ligand_spectrum`；同批异色 `--auto-colors` 或 `--palette-json`。  

**出图规范回退：** 本技能未另写的条款，**先用** [统一可视化规范_VizStandards](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。热图：**行/列名与格内数值标签一律黑色 `#000000`**。

**对齐高分期刊范式：** 遵循 [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)。**本技能对接与交付已 FROZEN**（见 [`对接与交付约束_DockingFrozen.md`](文档_docs/对接与交付约束_DockingFrozen.md)）。**网络药理学视觉轨已 FROZEN，本技能不得改网药样例图。**

## 7. 数据结果解读

打分近似；勿单凭对接定药效。亲和力应为负值；正值须查该任务的 `center_source`/`size_*` 并重对接。解读结合能时**必须点明定心方法**（例：「EGFR×槲皮素，center_source=cocrystal_meeko，affinity=…」）。  
**不做**共晶配体 RMSD 重对接验收（见 FROZEN 约束）。

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
