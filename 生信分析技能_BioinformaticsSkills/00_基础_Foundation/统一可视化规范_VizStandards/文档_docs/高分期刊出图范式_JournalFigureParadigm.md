# 高分期刊出图范式 / Journal Figure Paradigm

**SSOT 状态：** 本文件为项目级多面板参考目录（2026-07-19）。  
**配色与 recipe 实现：** [`出版级出图_PublicationPlot.R`](../脚本_scripts/出版级出图_PublicationPlot.R)  
**出图后审核：** [`出图后审核_PlotQA.md`](出图后审核_PlotQA.md)（每图强制）  
**冻结登记：** [`已跑通范式登记_FrozenParadigms.md`](已跑通范式登记_FrozenParadigms.md)

> 参考图来源：用户上传的三张多面板期刊风格图（工作区 assets；面板经目视核对）。  
> **网络药理学_NetworkPharmacology**、**分子动力学模拟_MolecularDynamics** 交付配方已 **FROZEN**——本范式不覆盖其专用图册（网药网络/韦恩/柱状；MD Origin FEL/能量柱/分组 HTML 报告）；见冻结登记。

---

## 0. 全局强制条款

| 条款 | 要求 |
|------|------|
| 数据 | 官方 GEO / TCGA / NGDC（或可溯源实验）；**禁止编造矩阵与分组** |
| 分辨率 / 格式 | DPI ≥ 600；同名 SVG + PNG |
| 图面语言 | **English only**（文件名可中英双语） |
| 分组色 | `bioinfo_groups` 全篇一致（Control / TreatA / TreatB…） |
| 统计上图 | p / padj / NES / logFC / n 写在图面或紧邻注释 |
| 多面板字母 | 左上角 **a/b/c…** 或 **A/B/C…**，同图统一大小写 |
| 出图后 | `viz_qa_after_plot` / PlotQA；FAIL 不得宣称 PASS |

---

## 1. Fig1 — HSCR 轨迹 / 模块范式（面板 a–j）

生物学叙事：对照 → 轻症 → 重症沿 severity / PC 轴；模块趋势 → 代表基因 → 富集 → 通路评分组间比较。

| 字母 | 图种 | 生物学目的 | 映射技能 / 分析步 |
|------|------|------------|-------------------|
| a | 树状图 / cladogram（样本层次聚类） | 样本整体相似度 | RNA-seq / Microarray / GEO-TCGA QC；WGCNA 树状可选 |
| b | PCA 散点（分组色 + 可选轨迹箭头） | 主变异与疾病进程方向 | RNA-seq / GEO-TCGA / DEG-UMAP QC-PCA |
| c | 密度 + 样本水平箱线（沿 PC 轴） | 组与样本在主轴上的分布 | RNA-seq QC；单细胞可改用 ridge/violin |
| d | 模块相对表达 vs severity（平滑线+CI） | 共表达模块沿表型轴动态 | WGCNA；剂量反应与时间序列_DoseTime |
| e | 单基因绝对表达趋势（斜率/S + P） | 驱动基因/标志物动态 | RNA-seq 趋势；DoseTime |
| f | GO/通路 **水平柱**（按模块分色） | 模块功能注释 | GSEA-Pathway ORA；RNA-seq 富集 |
| g–j | 通路评分箱线 + jitter + 显著性括号 | 通路活性组间定量比较 | GSVA/ssGSEA（GSEA-Pathway）；单细胞 AUCell 可类比 |

**实现要点：** `theme_journal`；分组色贯穿 b/c/g–j；富集用 `plot_enrich_hbar_facet`（禁止默认棒棒糖）；箱线用 `plot_box_bracket_journal`；树状图 `plot_sample_dendrogram_journal`；趋势 `plot_severity_trend_journal`；PC 分布 `plot_pc_density_box_journal`。

---

## 2. Fig2 — QSC/PSP 双态 + 临床范式（面板 A–J）

生物学叙事：两组转录差异 → 通路活性 → 处理配对效应 → GSEA → 风险分层生存。

| 字母 | 图种 | 生物学目的 | 映射技能 / 分析步 |
|------|------|------------|-------------------|
| A | 表达热图（蓝–白–红，列分组色条） | Top DEG 模式 | RNA-seq / Microarray / DEG-UMAP |
| B | 火山图（up/down 标注关键基因） | 差异显著性与效应量 | RNA-seq / Microarray / DEG-UMAP |
| C | 通路活性热图（样本×通路） | GSVA/通路重编程 | GSEA-Pathway（GSVA）；DEG-UMAP 延展 |
| D | 配对箱线（处理前后连线 + p） | 干预/药物响应 | DoseTime；DrugResponse（图种对齐） |
| E–F | GSEA enrichment 曲线（NES + p） | 基因集富集方向 | GSEA-Pathway |
| G–J | KM 生存/复发 + **number-at-risk** | 签名高低风险预后 | Survival；GEO-TCGA 临床层 |

**实现要点：** 热图 `scale_fill_diverging_rb` / `plot_pathway_activity_heatmap_journal`；火山 `plot_volcano_journal`；配对 `plot_paired_box_journal`；GSEA `plot_gsea_classic_journal`；生存 High/Low = `bioinfo_survival`；KM **必须** `plot_km_risk_table_journal`（含 risk table）。

---

## 3. Fig3 — scRNA + META 签名范式（面板 A–H）

生物学叙事：细胞图谱 → 代谢/通路富集 → AUC 阈值 → feature 映射 → 比例 → 临床生存。

| 字母 | 图种 | 生物学目的 | 映射技能 / 分析步 |
|------|------|------------|-------------------|
| A | UMAP 细胞类型注释 | 细胞组成与身份 | scRNA-Spatial；DEG-UMAP |
| B | UMAP 条件/亚簇/样本来源 | 原发–转移或批次/条件分布 | scRNA-Spatial；scRNA-Advanced |
| C | 富集 **棒棒糖**（Count × padj 渐变；Fig3-C）或气泡点图 | META/通路显著性 | GSEA-Pathway；scRNA 下游富集 |
| D | GSEA 曲线（签名基因集） | 签名在排序列表中的富集 | GSEA-Pathway |
| E | AUC 直方图 + 阈值竖线 | 定义 Activate 细胞子集 | AUCell（DEG-UMAP 延展 / scRNA-Advanced） |
| F | Feature plot（连续蓝阶） | 签名评分空间定位 | scRNA-Spatial（`bioinfo_feature_blue`） |
| G | 堆叠比例图（风险组×细胞状态） | 临床组细胞组成差异 | scRNA-Spatial 比例图 |
| H | KM + number-at-risk | META risk 预后验证 | Survival |

**实现要点：** 离散 UMAP `plot_umap_discrete_journal(..., label_on_plot=TRUE)`（簇上白底标注）；连续 feature `plot_umap_feature_journal`（灰→深蓝）；比例 `plot_stacked_proportion_journal`；Fig3-C 用 `plot_enrich_lollipop_journal`；GSEA 用 `plot_gsea_classic_journal`（绿 ES + 红蓝 rank bar + 嵌字统计）。

---

## 4. 技能 → 最低图种期望（对齐本范式）

| 技能类 | 最低应出图种（从本范式选取） |
|--------|------------------------------|
| 统一可视化规范_VizStandards | SSOT 色板 + recipe + PlotQA |
| 转录组 / Microarray / DEG-UMAP bulk | PCA、火山、Top 热图、富集水平柱/点图 |
| GEO-TCGA | 队列 PCA/箱线；下游接 Survival KM |
| GSEA-Pathway | 水平柱或气泡点 + GSEA 曲线（有序基因时） |
| scRNA-Spatial / DEG-UMAP sc | UMAP 注释 + 条件 UMAP + 比例；可选 feature/AUC |
| Survival | KM + risk table（High/Low 色） |
| WGCNA / DoseTime | 模块/基因趋势线（Fig1 d/e） |
| 网络药理学 | **不采用本表重绘**；维持冻结交付（见登记） |

---

## 5. 获取 / 处理 / 出图检查清单

1. **获取：** 记录 accession、平台、n、分组字段（SOFT / series matrix / GDC）。  
2. **真实性格查：** `数据真实性验证_DataAuthenticity`；n 对齐官网。  
3. **处理：** 官方分组 → 归一化/DEG/富集/评分；`set.seed` 仅用于可复现抽样，不伪造表达。  
4. **出图：** `source` PublicationPlot → recipe → `save_plot_pub` / `delivery_save_plot`。  
5. **PlotQA：** 每图后审核；多面板拼图时各子图字母一致。  
6. **解读：** 图注写清对比、阈值、n；禁止用无关 volcano 顶替主题图。

---

## 6. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-07-19 | 初版：三参考图面板目录 + 技能映射；NetPharm 明确排除视觉覆盖 |
| 2026-07-19 | 全面补充 journal helpers（GSEA 经典曲线、feature UMAP、堆叠比例、KM+risk table、括号箱线、配对箱线、严重度趋势、样本树、通路活性热图、PC 密度箱线）；样例重生成；NetPharm 仍 frozen |
