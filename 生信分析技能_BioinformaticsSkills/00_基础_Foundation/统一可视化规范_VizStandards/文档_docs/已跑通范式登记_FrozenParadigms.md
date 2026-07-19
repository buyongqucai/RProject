# 已跑通范式登记 / Frozen Paradigms Registry

**目的：** 防止后续 Agent/请求在未明确解冻时改坏已验证的出图配方。  
**规则：** Status=`frozen` 的技能，**Agents MUST NOT** 修改其视觉 recipe（配色、布局、网络算法参数、样例交付图）除非用户明确说「解冻 / unfreeze」。  
**范式 SSOT：** [`高分期刊出图范式_JournalFigureParadigm.md`](高分期刊出图范式_JournalFigureParadigm.md)

状态枚举：`frozen` | `aligned` | `aligned-by-reference` | `pending`

---

## 登记表

| Skill id / path | Status | 冻结/对齐内容 | Evidence | 日期 |
|-----------------|--------|---------------|----------|------|
| `bioinfo-network-pharmacology` / `03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology` | **frozen** | 全视觉轨：HCTP / Ellipse 网络、String PPI concentric、柱状（成分-疾病重叠、每药重叠、GO/KEGG）、韦恩等；**禁止重绘或「对齐期刊范式」改布局色** | `01_样例_sample/代码文件/结果文件/图片文件/`；`文档_docs/出图约束_NetworkFigureStandards.md`；技能说明首行 FROZEN 注记 | 2026-07-19 |
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
| 其他 DrugDiscovery（对接/MD/结构/ADMET/CMap/GDSC 等，**不含** NetPharm） | **aligned-by-reference** | 短注对齐 VizStandards；不强制重写代码 | 各技能说明 | 2026-07-19 |
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
| 2026-07-19 | 样例结果路径迁至 `代码文件/结果文件/`；NetPharm 仍 frozen（仅路径/编号，未改视觉） |
| 2026-07-19 | 初版登记；NetPharm frozen；期刊范式对齐批次 |
