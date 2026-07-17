# 04 WGCNA 共表达模块与 hub 基因（人 GSE79962）
# 数据来源：GSE79962 表达矩阵 + 分组；意义：无监督找“共调控基因模块”，
# 关联疾病表型(SCM vs Control)，定位模块内 hub 基因（潜在核心调控/标志）
source("00_公共函数.R", encoding = "UTF-8")
suppressPackageStartupMessages({ library(WGCNA); library(pheatmap) })
options(stringsAsFactors = FALSE)

ds <- "GSE79962"
expr <- load_bulk_expr(ds); meta <- load_bulk_meta(ds)
expr <- as.matrix(expr)

# 取变异最大的 5000 基因，样本 × 基因
vars <- apply(expr, 1, var)
sel <- names(sort(vars, decreasing = TRUE))[1:min(5000, length(vars))]
datExpr <- t(expr[sel, , drop = FALSE])
gsg <- goodSamplesGenes(datExpr, verbose = 0)
datExpr <- datExpr[gsg$goodSamples, gsg$goodGenes]

# 软阈值
powers <- 1:20
sft <- pickSoftThreshold(datExpr, powerVector = powers, verbose = 0)
power <- sft$powerEstimate
if (is.na(power)) power <- 6
message("WGCNA 选用 soft power = ", power)

net <- blockwiseModules(datExpr, power = power, TOMType = "unsigned",
                        minModuleSize = 30, mergeCutHeight = 0.25,
                        numericLabels = TRUE, verbose = 0, maxBlockSize = 6000)
moduleColors <- labels2colors(net$colors)
MEs <- moduleEigengenes(datExpr, moduleColors)$eigengenes
MEs <- orderMEs(MEs)

# 表型：SCM=1, Control=0
case <- DATASETS$case[DATASETS$id == ds]
trait <- as.integer(factor(meta$group, levels = c(DATASETS$control[DATASETS$id == ds], case))) - 1
trait <- data.frame(SCM = trait); rownames(trait) <- rownames(datExpr)

moduleTraitCor <- cor(MEs, trait$SCM, use = "p")
moduleTraitP <- corPvalueStudent(moduleTraitCor, nrow(datExpr))
mt <- data.frame(module = rownames(moduleTraitCor),
                 cor_SCM = moduleTraitCor[, 1], p = moduleTraitP[, 1])
mt <- mt[order(-abs(mt$cor_SCM)), ]
save_tab(mt, "04_WGCNA_模块-表型相关.csv")

# 模块-表型相关热图
pdf(file.path(EXT$图形, "04_WGCNA_模块表型相关.pdf"), width = 5, height = max(4, nrow(mt) * 0.4))
labeledHeatmap(Matrix = moduleTraitCor,
               xLabels = "SCM", yLabels = rownames(moduleTraitCor),
               ySymbols = rownames(moduleTraitCor), colorLabels = FALSE,
               colors = blueWhiteRed(50),
               textMatrix = paste0(signif(moduleTraitCor, 2), "\n(p=", signif(moduleTraitP, 1), ")"),
               setStdMargins = FALSE, cex.text = 0.7, main = "模块-SCM 相关")
dev.off()

# 最相关模块的 hub 基因（kME 最高）
top_mod_color <- sub("^ME", "", mt$module[1])
kME <- signedKME(datExpr, MEs)
mod_genes <- colnames(datExpr)[moduleColors == top_mod_color]
kme_col <- paste0("kME", top_mod_color)
if (kme_col %in% colnames(kME)) {
  hub <- data.frame(gene = mod_genes, kME = kME[mod_genes, kme_col])
  hub <- hub[order(-hub$kME), ]
  save_tab(hub, paste0("04_WGCNA_hub基因_", top_mod_color, ".csv"))
  message("最相关模块: ", top_mod_color, " (", nrow(hub), " 基因); top hub: ",
          paste(head(hub$gene, 10), collapse = ", "))
}

saveRDS(list(moduleColors = moduleColors, MEs = MEs, mt = mt, genes = colnames(datExpr)),
        file.path(EXT$中间, "04_wgcna.rds"))
message("完成: 04_WGCNA模块.R")
