---
name: bioinfo-viz-standards
description: >-
  统一可视化规范：高分期刊级出图——DPI≥600、SVG+PNG、单栏85–90mm/双栏180mm、
  journal muted 配色、富集 bar/dot 优先、图面英文、防遮挡；
  多面板范式见高分期刊出图范式_JournalFigureParadigm.md；冻结见已跑通范式登记_FrozenParadigms.md；
  出图后强制 PlotQA（填充/标签遮挡与长标签版式）。任何出图步骤强制使用；
  与 DeliveryStandards 同时 requires。
  R：ggplot2/ggrepel/pheatmap + 出版级出图_PublicationPlot.R + 出图后审核_PlotQA.R。
---

# 统一可视化规范 / VizStandards

**期刊多面板范式（SSOT）：** [`文档_docs/高分期刊出图范式_JournalFigureParadigm.md`](文档_docs/高分期刊出图范式_JournalFigureParadigm.md)  
**冻结登记：** [`文档_docs/已跑通范式登记_FrozenParadigms.md`](文档_docs/已跑通范式登记_FrozenParadigms.md)（`网络药理学`、`分子动力学模拟` = **frozen**，勿改其交付范式）  
**PlotQA：** [`文档_docs/出图后审核_PlotQA.md`](文档_docs/出图后审核_PlotQA.md)

## 1. 数据来源

各分析模块产出的 ggplot 对象或热图矩阵；不直接读原始测序。公共数据矩阵须来自官方 GEO/TCGA/NGDC（或可溯源实验），**禁止编造**。

## 2. 数据规范（判断是否可用）

- 绘图对象非空；标签与结果表一致；分组来自官方元数据  
- 标签过多须 Top-N 截断并图注说明  

## 3. 何时选用本技能

- **任何**需要交付图的分析步骤（编排计划第 6 章）  
- 用户提到 DPI、SVG、PNG、图面语言、标签重叠、期刊出图  

不适用：纯表格导出且无图。

### 回退优先级（强制）

出图时按下列顺序取规范；**不得**在未写明时凭通用习惯另起样式：

1. 用户当场指定的样式 / 明确解冻的 FROZEN 样例  
2. **领域技能**正文或 `文档_docs/` 中已写明的出图条款（含网药 FROZEN）  
3. **本技能（VizStandards）** ← 领域技能**未写明**出图规范时，**一律先用本规范**  
4. DeliveryStandards（仅文件命名 / 目录 / 审计，不管视觉 recipe）

## 4. 数据处理方法

1. `setup_cjk_fonts()` / `theme_journal()`（禁止无主题灰糊）  
2. `save_plot_pub(plot, stem, width, height, dpi=600)` → **同名 PNG+SVG**  
3. 火山/富集用 ggrepel 与折行；富集优先 `plot_enrich_hbar_facet` 或气泡点图  
4. 交付文件名由 DeliveryStandards `delivery_stem()` 生成（中英对照）  
5. **图面文字 English only**：`ggtitle` / `labs(title=…)` / 轴 / 图例 / strip / annotation **禁止中文**；文件名双语 ≠ 图面英文（见 DeliveryStandards §6）  
6. **出图后审核（强制）**：每张图保存后跑 PlotQA（见 [`文档_docs/出图后审核_PlotQA.md`](文档_docs/出图后审核_PlotQA.md)）；`source` `出图后审核_PlotQA.R`。检查色块互挡、标签互挡、长标签版式失衡；自动化 + 目视 PNG。FAIL 不得宣称 PASS；密网 WARN 可交付但须注明。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 语法图 | `ggplot2` | 主绘图 | 必需 |
| 标签 | `ggrepel` | 防遮挡 | 火山/PCA |
| 热图 | `pheatmap` 或 `ComplexHeatmap` | 矩阵热图 | 任选其一 |
| 字体 | `sysfonts`, `showtext` | 中文 SimHei | 否则 sans |
| SVG | `svglite`（推荐） | 矢量输出 | 缺省回退 `svg()` |
| 本库 | `出版级出图_PublicationPlot.R` | `save_plot_pub` + 色板/recipe | 规范源 |
| 出图后审核 | `出图后审核_PlotQA.R` | `viz_qa_*` PASS/WARN/FAIL | **每图强制**；见 PlotQA 文档 |

## 6. 数据可视化（高分期刊级强制条款）

对齐 [`高分期刊出图范式_JournalFigureParadigm.md`](文档_docs/高分期刊出图范式_JournalFigureParadigm.md) 三套参考面板：  
**Fig1** 轨迹/模块（cladogram·PCA·密度箱线·趋势·GO 水平柱·通路箱线+jitter）；  
**Fig2** 双态临床（热图·火山·通路热图·配对箱线·GSEA·KM+risk table）；  
**Fig3** scRNA+签名（UMAP·点图·GSEA·AUC 直方图·feature·比例·KM）。  
多面板字母 `annotate_panel_letter`；组间色全篇一致。富集以 **水平柱或气泡点图** 为默认（`plot_enrich_hbar_facet` / `plot_enrich_dot_journal`），**棒棒糖不作默认**。统计量（p/NES/logFC/n）上图。

写入并执行于 `出版级出图_PublicationPlot.R`：

| 条款 | 要求 |
|------|------|
| 分辨率 | **DPI ≥ 600** |
| 格式 | **同时**输出同名 **SVG + PNG** |
| 版式 | 单栏约 **85–90 mm**；双栏约 **180 mm**；`theme_journal()` 白底、浅灰主网格、无次网格、细浅边框 |
| 字体 | 图面 **Arial/sans**；English only |
| 分组色 | Control `#6B8F71` / TreatA `#C17B7B` / TreatB `#8B7BA8`（`bioinfo_groups`；Accent1 `#D4A574` / Accent2 `#5B8FA8`） |
| 发散色 | 蓝–白–红（热图/通路活性 `bioinfo_diverging_rb`：`#2166AC`…`#B2182B`） |
| **热图标签** | **一律黑色 `#000000`**：行名、列名、格内数值（annot）、坐标轴标题、图例标题/刻度文字；禁止随底色自动反白/灰字（除非领域技能 FROZEN 另有规定） |
| 火山 | up `#C0392B` / down `#1A7A6D` / ns `#BDBDBD` |
| 富集 | **默认水平柱 / 气泡点图**；facet 色 `bioinfo_enrich_facet`（BP `#6B8F71` / CC `#8B7BA8` / MF `#D4A574` / KEGG `#5B8FA8`）；**禁止以 lollipop 为默认** |
| UMAP | 分类 `bioinfo_umap_discrete`；连续表达 `bioinfo_feature_blue` |
| 生存 | High `#C0392B` / Low `#2166AC` |
| 禁止 | 彩虹、默认灰糊、假 Cytoscape、单图种糊弄、富集默认棒棒糖 |
| 出图后审核 | **强制** PlotQA：填充遮挡 / 标签遮挡 / 长标签版式；见 §4.6 与 `文档_docs/出图后审核_PlotQA.md` |

### 子图样式对照（参考面板映射）

| 参考子图类型 | 本库对应实现要点 |
|--------------|------------------|
| 多面板字母 | `annotate_panel_letter` |
| PCA 散点 + 分组色 | `plot_pca_journal` / `bioinfo_groups` + `theme_journal` |
| 火山 up/down | `scale_color_volcano` / `plot_volcano_journal` |
| 热图蓝白红 | `scale_fill_diverging_rb`；标签黑色见上表「热图标签」与 `plot_pathway_activity_heatmap_journal` |
| 富集水平柱（按类着色） | `plot_enrich_hbar_facet` + `bioinfo_enrich_facet` |
| 富集气泡/点图（Count × −log10p） | `plot_enrich_dot_journal`（**优先于棒棒糖**） |
| 箱线+抖动 | `plot_box_jitter_journal` |
| 箱线+抖动+显著性括号 | `plot_box_bracket_journal` |
| 配对箱线（灰线连接） | `plot_paired_box_journal` |
| UMAP 注释 | `plot_umap_discrete_journal` / `bioinfo_umap_discrete` |
| Feature UMAP（连续蓝阶） | `plot_umap_feature_journal` / `bioinfo_feature_blue` |
| 堆叠细胞比例 | `plot_stacked_proportion_journal` |
| GSEA 经典曲线（ES+barcode+metric） | `plot_gsea_classic_journal` |
| KM + risk table + log-rank p | `plot_km_risk_table_journal`（默认 ggplot；`options(bioinfo.km.use_survminer=TRUE)` 用 survminer） |
| 严重度/时间趋势（smooth+CI） | `plot_severity_trend_journal` |
| 样本树状图 / cladogram | `plot_sample_dendrogram_journal` |
| 通路活性热图（GSVA 风格） | `plot_pathway_activity_heatmap_journal` |
| PC 密度+箱线组合 | `plot_pc_density_box_journal` |

网药交付原图副本（对照用）：`网络药理学_.../01_样例_sample/参考_交付原图/`（历史对照；**新图勿再默认棒棒糖**）。

### 技能典型图种组合（最低期望）

| 技能类 | 至少包含 |
|--------|----------|
| RNA-seq / Microarray / Proteomics | 火山 + PCA/箱线 或 Top 热图 |
| 单细胞 | UMAP + 比例/小提琴（择一） |
| 富集/GSEA | **水平柱或气泡点图** +（可选）NES 条形；**勿默认棒棒糖** |
| 网络药理 | 多库/交集 + 网络 + PPI 或富集气泡/水平柱 |
| 16S | Alpha 箱线 + Beta PCoA（或等价） |
| WGCNA | 模块-性状热图（或树状+相关性） |
| 生存 | KM 曲线（± ROC） |
| BLOCKED 契约 | **主题相关**示意/降级图，禁止无关 volcano |

文件命名强制见 [`统一交付规范_DeliveryStandards`](../统一交付规范_DeliveryStandards/技能说明_统一交付规范_DeliveryStandards.md)：`{中文语义}_{EnglishPascal}.{ext}`。  
**注意**：`delivery_stem()` 只用于文件名，勿拼进 `ggtitle()` / `labs(title=)`；**文件名中英 ≠ 图面英文**。

## 7. 数据结果解读

图是证据展示，图注写清对比、阈值、n；图面出现中文=不合格。  
未完成出图后审核（或仍有未说明的 FAIL）= 交付不合格。

## 8. 能否结合其它生信

被全部组学技能与编排技能强制依赖。

与 [`统一交付规范_DeliveryStandards`](../统一交付规范_DeliveryStandards/技能说明_统一交付规范_DeliveryStandards.md) 互补且**同时 requires**：本技能管出图技术；交付规范管文件命名、审计与报告。样例 `run_sample.R` 须先 source 本技能再 source DeliveryStandards。

## 样例验证

样例：`01_样例_sample/`
