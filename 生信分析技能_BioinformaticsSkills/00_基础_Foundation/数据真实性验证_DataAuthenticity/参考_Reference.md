# 数据真实性验证 — 参考细节

## 配套脚本 `校验/数据真实性核对.R`

- 维护一张 `GEO_TRUTH` 登记表（dataset → GEO 官方样本数 + 备注），作为比对真值。
  **新增数据集时必须先去 GEO 页面核对样本数再登记。**
- 逐数据集检查：下载清单、样本数 vs GEO、矩阵↔元数据一致、编造/污染列、NA 分组、
  DEG 单向性与 log2FC 中位数。
- 输出 `校验/数据真实性核对报告.csv`（dataset, level, item, detail）。

## GEO 官方样本数如何核对

网页：`https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE207363`
（看 "Samples (N)" 及每个 GSM 的标题）。命令行/程序可用：

```r
# 若装了 GEOquery：
# gse <- GEOquery::getGEO("GSE207363", GSEMatrix = FALSE); length(GEOquery::GSMList(gse))
```

或直接抓网页文本核对 GSM 列表与分组标注。**GSM 编号/命名出现缺口（Sample2、Sample3 但无
Sample1、Sample4）几乎总是漏样本的信号。**

## 常见"造假/幻觉/污染"模式（本项目真实踩坑）

| 模式 | 表现 | 检测 | 处置 |
|------|------|------|------|
| 漏样本 | 处理样本数 < GEO | 与 GEO_TRUTH 比对 | 补下载缺失 GSM，重跑 |
| 汇总列混入 | `average_fpkm_*` 当作样本 | 名称含 average/mean | 收紧正则 `^fpkm_WT_(LPS\|PBS)_[0-9]+$`，剔除重跑 |
| 分组映射 bug | group 全 NA | 检查 NA 分组 | 修 GSM→group 映射（勿把样本名当分组）|
| 归一化伪影 | DEG 几乎全上调、中位 log2FC≈15 | 单向性/中位数 | scRNA pseudobulk 加 edgeR TMM 归一化 |
| 低重复假显著 | n=1/组仍报大量 DEG | 看每组样本数 | 用细胞级 FindMarkers；报告注明 n |
| 图-数不符 | QC 图样本数 ≠ 数据 | 目视/计数 | QC 用全部样本；重绘 |
| 编造矩阵 | 说不清来源的"数据" | 无下载清单 | 拒用，回到官方源重新获取 |

## 分析各步的"可溯源"要求

- **下载**：保存 URL + 文件 + 大小/校验和（下载清单.json）。
- **分组**：记录 GSM ↔ group 的依据（GEO title/characteristics 原文）。
- **预处理**：QC 阈值、过滤前后细胞/样本数留痕。
- **DEG**：方法（limma-voom / edgeR-TMM / FindMarkers）、对比、每组 n。
- **富集/延展**：输入基因集来源（org.db / KEGG REST / MSigDB 版本）。
- **图**：每张图对应的样本/细胞数应与数据一致。

## 交付前自检清单

- [ ] 每个数据集样本数 == GEO 官方（已在 GEO_TRUTH 登记并通过）
- [ ] 无 average/汇总列、无 NA 分组
- [ ] 表达矩阵列 == sample_info == GEO 样本
- [ ] DEG 非全单向、中位 log2FC≈0（或已说明低重复）
- [ ] 所有图样本数与数据一致、可正常打开
- [ ] 有下载清单、set.seed、脚本可一键重跑
- [ ] 交付说明如实写清来源/处理/局限，不夸大
