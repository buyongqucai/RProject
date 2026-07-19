# 图表质量与样式规范

统一 bulk / scRNA 图表的可读性与一致性。  
**全组强制**另见 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)：

- **DPI ≥ 600**
- 同名输出 **SVG + PNG**（可另存 PDF）
- 中文可读；标签不遮挡；统一配色

绘图实现：`书清项目/共享脚本/工具_scRNA可视化.R`、`工具_富集与质控图.R`、`工具_统一出图.R`（`FIG_DPI <- 600`）。

## 1. 中文字体（必须）

```r
sysfonts::font_add("SimHei", "C:/Windows/Fonts/simhei.ttf")
showtext::showtext_auto()
showtext::showtext_opts(dpi = 600)
theme_set(theme_bw() + theme(text = element_text(family = "SimHei")))
```

ggrepel 标签显式 `family = "SimHei"`。勿用 `font_add("sans", ...)`。

## 2. 火山图

- `ggrepel::geom_text_repel` 标注上/下调各 ~15 个基因，**避免遮挡**。
- 阈值虚线；图例含上/下调数量；`padj` 用 `pmax(padj, 1e-300)`。

## 3. 质控箱线图

- 长表分组用 `rep(group, each = nrow(expr))` 对齐；先按 `colnames(expr)` 对齐 `sample_info`。

## 4. 质控 PCA

- 用**全部样本**；n&lt;3 跳过；分组虚线框；标签 ggrepel。

## 5. GO/KEGG

- 完整通路名 + `str_wrap`；画布随条目数加大。

## 6. 单细胞 UMAP / 比例图

- 细胞名标注；比例用计数图，面积≠比例。

## 7. 交付自检

- 每张图有 SVG 与 PNG；DPI≥600；中文正常；标签无遮挡；样本数与表一致。
- 数据真实性另见 [数据真实性验证](../../00_基础_Foundation/数据真实性验证_DataAuthenticity/技能说明_数据真实性验证_DataAuthenticity.md)。
