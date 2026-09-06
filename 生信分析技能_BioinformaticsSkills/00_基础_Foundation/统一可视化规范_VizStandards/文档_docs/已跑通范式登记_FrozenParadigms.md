# 已跑通范式登记 / Frozen Paradigms Registry

**目的：** 防止后续 Agent/请求在未明确解冻时改坏已验证的出图配方。  
**规则：** Status=`frozen` 的技能，**Agents MUST NOT** 修改其视觉 recipe（配色、布局、网络算法参数、样例交付图）除非用户明确说「解冻 / unfreeze」。  
**范式 SSOT：** [`高分期刊出图范式_JournalFigureParadigm.md`](高分期刊出图范式_JournalFigureParadigm.md)

状态枚举：`frozen` | `aligned` | `aligned-by-reference` | `pending`

---

## 登记表

| Skill id / path | Status | 冻结/对齐内容 | Evidence | 日期 |
|-----------------|--------|---------------|----------|------|
| `bioinfo-network-pharmacology` / `03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology` | **frozen** | 全视觉轨 + 轨 B 目录 + 疾病双口径 + Fig16–19 + KEGG Top20 + HTML 报告（相对路径整夹分享）；**§J–§L 已用户授权增补**（网络分析报告 / 空靶点药 / 生物结构动画）；**禁止**未解冻改 §A–§H recipe | `文档_docs/出图约束_NetworkFigureStandards.md`（**FROZEN 2026-07-26**；§J–L 2026-07-27）；`01_样例_sample/`；技能说明首部 FROZEN 注记 | 2026-07-27 |
| `bioinfo-molecular-dynamics` / `03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics` | **frozen** | 3HTB 样例：`01`–`26` 图册序 + 一图一夹 + `工作文件_MdWork` 阶段归档；Origin FEL/曲线/能量柱 recipe（Viridis、journal muted、禁止 `showLines(3)`/`pfb color()`）；PyMOL 快照 + LigPlot 正式化学结构；分组 HTML 报告（KPI + 分条解读 + 0.20 ns 警示）；**禁止**未解冻改图样/报告结构/解读口径 | `文档_docs/出图与交付约束_MdFigureStandards.md`（**FROZEN 2026-09-03**）；`01_样例_sample/`；`样例报告_SampleReport_v1.html` | 2026-09-03 |
| `bioinfo-molecular-docking` / `03_药物计算_DrugDiscovery/分子对接与虚拟筛选_MolecularDocking` | **frozen** | AutoDock-GPU 默认路线；定心决策树（共晶包盒 / AutoSite / 回退）；`center_source` 强制登记；PyMOL ST/PT/CJ/QJ + detail 手调断点；**detail 截图定稿**（最大化 / buffer=4 / 满度 0.72 / 视口中心 6000²）+ **result 拼图效力序**（SOP §7.3/§7.4）；序号交付目录；热图色标 **仅非正值（vmax=0）**；**禁止**共晶 RMSD 重对接验收；**禁止**未解冻改路线/图样语义/schema | `文档_docs/对接与交付约束_DockingFrozen.md`（**FROZEN 2026-09-05**；detail/result 定稿 **2026-09-06**）；SOP §7.3/§7.4；`plot_docking_affinity_heatmap.py`；`努力学习/docking_adgpu/` | 2026-09-06 |
| `bioinfo-viz-standards` / `00_基础_Foundation/统一可视化规范_VizStandards` | **aligned** | journal muted 色板；火山/热图/富集 bar·dot/UMAP/KM recipe；PlotQA 强制；多面板范式文档 | `出版级出图_PublicationPlot.R`；`出图后审核_PlotQA.*`；本目录两篇范式文档 | 2026-07-19 |
| `bioinfo-plotqa`（PlotQA，挂于 VizStandards） | **aligned** | 出图后遮挡/长标签审核钩子 | `文档_docs/出图后审核_PlotQA.md`；`脚本_scripts/出图后审核_PlotQA.R` | 2026-07-19 |
| `bioinfo-rnaseq` / `01_组学_Omics/转录组分析_RNA-seq` | **aligned** | 文档对齐 Fig1/2 图种 + PlotQA + 真实数据门禁 | 技能说明 §6 | 2026-07-19 |
| `bioinfo-geo-tcga` / `01_组学_Omics/公共库挖掘_GEO-TCGA` | **aligned** | 队列 PCA/箱线对齐范式；样例 GSE10072 REAL | `01_样例_sample/`；TEST_REPORT（若有） | 2026-07-19 |
| `bioinfo-microarray` / `01_组学_Omics/基因芯片表达分析_Microarray` | **aligned** | GSE10072 limma + 期刊火山；PlotQA | `01_样例_sample/`；`TEST_REPORT_JournalParadigm.md` | 2026-07-19 |
| `bioinfo-scrna-spatial` / `01_组学_Omics/单细胞与空间转录组分析_scRNA-Spatial` | **aligned** | 文档对齐 Fig3 UMAP/比例/feature | 技能说明 §6 | 2026-07-19 |
| `bioinfo-gsea-pathway` / `05_系统方法_SystemsMethods/基因集富集与通路_GSEA-Pathway` | **aligned** | 水平柱/点图 + GSEA 曲线期望；禁止默认棒棒糖 | 技能说明 §6 | 2026-07-19 |
| `bioinfo-survival` / `04_临床预测与统计_ClinicalStats/生存分析与预后模型_Survival` | **aligned** | KM + risk table；High/Low `bioinfo_survival` | 技能说明 §6 | 2026-07-19 |
| `differential-analysis-and-umap` / `06_已落地流水线_ProductionPipelines/差异分析与UMAP流水线_DEG-UMAP` | **aligned** | 标准图集映射 Fig1–3；强制真实性 + PlotQA | 技能说明 §6 | 2026-07-19 |
| `bioinfo-research-orchestrator` | **aligned** | 计划章引用期刊范式 + 冻结登记；选图走 VizStandards recipes | 技能说明 §6 | 2026-07-19 |
| `bioinfo-metabolomics` | **aligned-by-reference** | 技能说明「对齐高分期刊范式」短注；近邻：PCA/热图/柱·点 | 技能说明 | 2026-07-19 |
| `bioinfo-16s` | **aligned-by-reference** | 同上；近邻：箱线 + PCoA | 技能说明 | 2026-07-19 |
| `bioinfo-gwas` | **aligned-by-reference** | 同上；近邻：曼哈顿/QQ（期刊主题） | 技能说明 | 2026-07-19 |
| `bioinfo-epigenomics`（ChIP） | **aligned-by-reference** | 同上；近邻：富集柱/热图 | 技能说明 | 2026-07-19 |
| `bioinfo-proteomics` | **aligned-by-reference** | 同上；近邻：火山/热图/PCA | 技能说明 | 2026-07-19 |
| 其他 DrugDiscovery（结构/ADMET/CMap/GDSC 等，**不含** NetPharm、**不含** MD、**不含** Docking） | **aligned-by-reference** | 短注对齐 VizStandards；不强制重写代码 | 各技能说明 | 2026-07-19 |
| 其余未点名技能 | **pending** | 尚未逐条改文档；默认仍须走 VizStandards + PlotQA | — | 2026-07-19 |

---

## Agent 操作协议

1. 改任何出图前先查本表。  
2. `frozen` → **只改文档中的冻结声明/登记，不改脚本与样例图**（除非用户解冻）。**例外（允许）：** 样例目录迁移、文件路径/`NN_` 命名前缀、脚本路径指针更新——**不得**改视觉 recipe。  
3. `aligned` → 可增强 recipe，但须保持与期刊范式文档一致并跑 PlotQA。  
4. `aligned-by-reference` / `pending` → 优先继承 VizStandards，勿大改技能私有绘图，除非用户点名。

---

## 修订记录

| 日期 | 变更 |
|------|------|
| 2026-09-03 | MD 用户确认冻结：图册 01–26、Origin/PyMOL/LigPlot recipe、分组 HTML 报告与解读口径 → `出图与交付约束_MdFigureStandards.md` |
| 2026-07-27 | NetPharm：用户要求写入规范 — 出图约束增补 §J–§L（网络分析 HTML/大表、空靶点药味、生物结构动画）；成分靶点 SOP §7；**未解冻**既有视觉 recipe |
| 2026-07-26 | NetPharm 用户确认冻结：出图约束扩写 §0a/§E–§H（双口径、高级附图、KEGG Top20、HTML 报告、轨 B 树）并标 **FROZEN** |
| 2026-07-19 | 样例结果路径迁至 `代码文件/结果文件/`；NetPharm 仍 frozen（仅路径/编号，未改视觉） |
| 2026-07-19 | 初版登记；NetPharm frozen；期刊范式对齐批次 |
