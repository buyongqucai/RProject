# 延展生信分析 — 参考细节

配套 技能说明_差异分析与UMAP流水线_DEG-UMAP.md 的「延展生信分析」章节。所有脚本先 `source("00_公共函数.R")`
（提供路径 `EXT`、`load_deg/load_bulk_expr/load_seurat`、`mouse_to_human`、
`deg_rank_vector`、`save_fig/save_tab`，以及中文字体）。

## 0. 依赖与中文字体

CRAN：`msigdbr babelgene WGCNA circlize ggpubr showtext sysfonts pdftools`
Bioc：`fgsea GSVA AUCell decoupleR progeny dorothea GSEABase ComplexHeatmap GO.db impute preprocessCore`

```r
if (!requireNamespace("BiocManager", quietly = TRUE)) install.packages("BiocManager")
BiocManager::install(c("GSVA","AUCell","decoupleR","progeny","dorothea","fgsea"), update = FALSE, ask = FALSE)
```

中文字体（放在公共函数顶部，PDF 才显示中文）：

```r
library(showtext)
sysfonts::font_add("SimHei", "C:/Windows/Fonts/simhei.ttf")   # 勿 font_add("sans",...) 会报错
showtext::showtext_auto(); showtext::showtext_opts(dpi = 300)
ggplot2::theme_set(ggplot2::theme_bw() + ggplot2::theme(text = ggplot2::element_text(family = "SimHei")))
```

排错：出现 `mbcsToSbcs conversion failure` 即字体未生效；`showtext_auto()` 后
ggplot 与 pheatmap 中文均正常。用 `pdftools::pdf_convert()` 把 PDF 转 PNG 做视觉 QC。

## 1. 跨物种保守基因

```r
library(babelgene)
ortho <- babelgene::orthologs(genes = unique(mouse_syms), species = "mouse", human = FALSE)
map <- setNames(ortho$human_symbol, ortho$symbol)   # 鼠 symbol -> 人 symbol
```

以人显著 DEG 为参照，统计每基因在小鼠模型中"显著且方向一致"的数据集数；**方向一致性用
向量化计算，勿对混合类型 data.frame 用 `apply`（会强制转 character 使 `sign()` 失败）**。
输出保守核心表 + log2FC 热图（`breaks` 对称到 ±max）。

## 2. GSEA（用 clusterProfiler，避开 msigdbr）

```r
library(clusterProfiler)
ranks <- deg_rank_vector(deg)                        # 命名向量，降序
ego <- gseGO(ranks, OrgDb = orgdb, ont = "BP", keyType = "SYMBOL",
             minGSSize = 10, maxGSSize = 500, pvalueCutoff = 0.25, eps = 0)
map <- bitr(names(ranks), "SYMBOL", "ENTREZID", OrgDb = orgdb)   # KEGG 需 entrez
re <- ranks[map$SYMBOL]; names(re) <- map$ENTREZID; re <- sort(re, decreasing = TRUE)
ekegg <- gseKEGG(re, organism = "hsa", pvalueCutoff = 0.25, eps = 0)  # mmu for mouse
```

出图：取 |NES| 前 12 上/下调，条形图正红(激活)负蓝(抑制)。

## 3. 代谢重编程

KEGG 代谢基因集（缓存）：`download_KEGG(kegg_org)` → 取编号 <02000 的通路 → entrez 转 symbol。

bulk GSVA：
```r
param <- GSVA::gsvaParam(as.matrix(expr), sets, kcdf = "Gaussian")  # 新版 API
gsva_res <- GSVA::gsva(param)                                        # 旧版: gsva(expr, sets, method="gsva")
fit <- eBayes(contrasts.fit(lmFit(gsva_res, design), makeContrasts(case-ctrl, levels=design)))
```

scRNA AUCell（大数据先抽样，用 data 层）：
```r
expr <- GetAssayData(obj, layer = "data")            # 先 JoinLayers
rk <- AUCell::AUCell_buildRankings(expr, plotStats = FALSE)
auc <- AUCell::getAUC(AUCell::AUCell_calcAUC(sets, rk))   # sets x cells
```
按 celltype×group 汇总；重点看心肌 OXPHOS 疾病 vs 对照（应显著下降）。

## 4. WGCNA

```r
library(WGCNA)
datExpr <- t(expr[高变前5000基因, ])                 # 样本 × 基因
sft <- pickSoftThreshold(datExpr); power <- sft$powerEstimate %||% 6
net <- blockwiseModules(datExpr, power = power, TOMType = "unsigned",
                        minModuleSize = 30, mergeCutHeight = 0.25, numericLabels = TRUE, maxBlockSize = 6000)
MEs <- moduleEigengenes(datExpr, labels2colors(net$colors))$eigengenes
cor(MEs, trait) ; corPvalueStudent(...)              # 模块-表型相关
kME <- signedKME(datExpr, MEs)                        # hub = kME 最高
```

## 5. TF / 通路活性（decoupleR）

```r
library(decoupleR); library(dorothea); library(progeny)
data("dorothea_hs"); net <- subset(dorothea_hs, confidence %in% c("A","B","C"))
net <- data.frame(source = net$tf, target = net$target, mor = net$mor)
mat <- matrix(deg$t, ncol = 1, dimnames = list(deg$gene, "contrast"))
acts <- run_ulm(mat, net, .source="source", .target="target", .mor="mor", minsize=5)
acts <- acts[acts$statistic == "ulm", ]              # TF 活性得分
# PROGENy：getModel("Human"/"Mouse", top=500) -> 融为 source=pathway,target=gene,weight
pacts <- run_mlm(mat, pnet, .source="source", .target="target", .mor="weight", minsize=5)
```
小鼠用 `dorothea_mm` / `getModel("Mouse")`。

## 6. 虚拟敲除（regulon-based in silico KO）

对高活性 master TF：取其 DoRothEA regulon（target, mor），TF 激活时靶基因预期方向
= `sign(mor) * sign(TF活性)`；与实际 DEG 方向一致且显著者 = "可逆转(rescued)基因"。
按 rescued 数排序 master TF（干预靶点优先级），对首选 TF 的 rescued 基因做 GO 富集。
（进阶：CellOracle / scTenifoldKnk 做真正的 GRN 扰动模拟。）

## 7. 细胞通讯（curated 配体-受体）

```r
data_mat <- GetAssayData(obj, layer = "data")        # 先 JoinLayers
# 各 (group, celltype) 平均归一化表达（非 log）：rowMeans(expm1(data[, cells]))
# 通讯强度[sender, receiver] = sum_over_LR( ligand_mean[sender] * receptor_mean[receiver] )
# 疾病 - 对照 得差异；出 sender×receiver 热图 + Top 增强 L-R 相互作用条形图
```
curated L-R 覆盖 TNF/IL1/IL6/趋化因子(CCL/CXCL)/CSF/TGFβ/SPP1/ICAM 等心脏免疫串扰核心。
（进阶：CellChat / CellPhoneDB / LIANA 用完整数据库。）

## 报告结构（务必逐部分写）

数据来源 → 数据处理 → 数据的生物学意义 → 结果的生物学意义 → 与其它部分的关联 → 解读；
最后给"综合整合模型"（把各部分串成一条机制链）+ 局限与展望 + 文件索引。
范例：`延展分析/报告/脓毒症心肌病_延展生信分析报告.md`。

## 常见坑

| 症状 | 处理 |
|------|------|
| `msigdbdf is not available for this version of R` | 弃用 msigdbr，改 clusterProfiler gseGO/gseKEGG |
| PDF 中文空白/`mbcsToSbcs` | showtext + SimHei（见 §0） |
| `font_add("sans",...)` 报错 | 只注册具名字体（如 "SimHei"），勿覆盖 sans |
| AUCell/GSVA 内存大 | scRNA 先抽样细胞（如 15000），用 data 层 |
| decoupleR 结果多种 statistic | 过滤 `statistic == "ulm"/"mlm"` |
| CellChat 安装失败(Windows) | 用 curated L-R 均值乘积法替代 |
