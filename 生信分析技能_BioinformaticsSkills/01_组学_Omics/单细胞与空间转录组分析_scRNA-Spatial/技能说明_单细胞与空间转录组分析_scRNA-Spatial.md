---
name: bioinfo-scrna-spatial
description: >-
  单细胞与空间转录组：GEO 自动读入、自适应QC、DoubletFinder、Harmony、分辨率扫描、
  SingleR 注释、pseudobulk/探索性 DEG、GO/KEGG、UMAP/比例图。
  R包：Seurat、GEOquery、DoubletFinder、harmony、clustree、SingleR、edgeR、clusterProfiler。
---

# 单细胞与空间转录组分析 / scRNA-Spatial

> 流程参考：[只需一个GEO编号，一键跑完单细胞全流程](https://mp.weixin.qq.com/s/Z8x1a1Q8A5uQq3qAzBpDpg)
> （GEO 下载 → 原始计数校验 → 自适应质控 → 按样本 DoubletFinder → 整合 → 注释 → 差异/富集）

## 1. 数据来源

- GEO 补充文件（`GEOquery::getGEOSuppFiles`）：10X mtx/h5、CSV/TSV 计数矩阵、Seurat RDS/RData
- 用户本地 10x / h5ad（需转 counts）/ Visium·Xenium 空间对象
- 书清：`工具_单细胞对象.R`、`工具_scRNA细胞注释.R`、`工具_富集与质控图.R`

**硬门槛：** 必须是**单细胞原始计数**（非负、高整数比）。拒绝 microarray、TPM/CPM/log 已标准化矩阵、伪 bulk 汇总表。

## 2. 数据规范（判断是否可用）

| 校验 | 要求 |
|------|------|
| 细胞数 | ≥80（过低疑似 bulk/芯片） |
| 基因数 | ≥200 |
| 计数值 | 非负；非零值整数占比 ≥0.90 |
| 双细胞 | **按原始样本分别**跑 DoubletFinder，禁止在合并对象上一次算完 |
| 注释 | marker / SingleR 可溯源；图例禁纯数字簇号当最终类型 |
| 差异 | 每组生物学样本 ≥2 → edgeR **pseudobulk**；否则细胞级 Wilcoxon 且标明「探索性」 |

**禁止：** 把同一患者/同一样本内细胞当独立重复做组间检验（伪重复 → 假阳性）。

## 3. 何时选用本技能

- 细胞类型定位、亚群 DEG、免疫微环境、空间定位
- 仅有 GSE 号、需可复核自动流水线（决策日志 + 结构化输出）
- 编排：机制假说 + 细胞分辨率

不适用：只需组织平均表达且无细胞需求（用 bulk 转录组）；确认为芯片/array 的 GEO。

## 4. 数据处理方法（推荐全流程）

```text
GEO_ID
  → 下载补充文件 + 递归解压
  → 格式判别（10X mtx/h5 / RDS / CSV·TSV）
  → 「原始计数」科学校验 + 物种推断（人/鼠）
  → 样本↔GSM 匹配 + 分组语义推断（无证据则跳过组间比较）
  → 每样本：自适应 QC（MAD）→ DoubletFinder
  → 合并 → Normalize → HVG → PCA
  → Harmony（仅当多样本且分组设计安全：单组或每组≥2 样本）
  → 分辨率网格 + Clustree/ARI 选最优 → 聚类 → UMAP/t-SNE
  → FindAllMarkers → SingleR 聚类级注释
  → 细胞类型比例图
  → 按细胞类型分层 DEG（pseudobulk 或探索性）→ 火山图
  → GO/KEGG（显著上/下调分别）→ 保存 Seurat.rds
```

### 建议输出目录（GEO 自动模式）

```text
GSEXXXXX_auto_scRNA/
├── 00_download/
├── 01_extracted/
├── 02_figures/          # 01_QC … 20_KEGG 顺序编号
├── 03_tables/
├── 04_objects/          # Seurat.rds / Seurat.Rdata
└── 05_reports/          # automatic_decisions.csv、DEG_method_note.txt、…
```

交付到本仓库样例时，仍映射到 DeliveryStandards：`代码文件/结果文件/{图片,数据,报告}文件/`。

### 关键可调参数（默认）

> 2026-08-30 议题 08 落地：`脚本_scripts/运行单细胞空转骨架_runScrnaSkeleton.R` 已实现 `scrna_qc_filter` / `scrna_resolution_grid` / `scrna_find_markers` 并接入 `run_scrna_pipeline` 签名；PBMC3k 真实数据 E2E 见 `01_样例_sample/代码文件/run_pbmc3k_pipeline.R`。

| 参数 | 默认 | 含义 |
|------|------|------|
| `QC_MIN_FEATURE_FLOOR` | 200 | 基因数硬下限 |
| `PB_MIN_SAMPLES` | 2 | 启用伪 bulk 的每组最小样本数 |
| `DE_LOGFC` / `DE_FDR` | 1 / 0.05 | 差异阈值 |
| `RES_GRID` | 0.1–1.2 step 0.1 | 分辨率扫描 |

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| GEO | `GEOquery`, `Biobase` | 元数据与补充文件 | 需可访问 NCBI |
| 主框架 | `Seurat`, `SeuratObject`, `Matrix` | 对象与聚类 | |
| 双细胞 | `DoubletFinder` | 按样本去双细胞 | GitHub |
| 整合 | `harmony` | 批次校正 | 设计不安全时跳过 |
| 分辨率 | `clustree` | 树图 + 评分选 res | |
| 注释 | `SingleR`, `celldex` | 参考注释 | 人 HPCA / 鼠 MouseRNAseq |
| 差异(样本) | `edgeR` | pseudobulk | **有重复时首选** |
| 差异(细胞) | Seurat `FindMarkers` | 探索性 | 必须写进报告 |
| 富集 | `clusterProfiler`, `enrichplot`, `org.Hs.eg.db`/`org.Mm.eg.db` | GO/KEGG | |
| 出图 | `ggplot2`, `patchwork`, `ggrepel` + VizStandards | UMAP/比例/火山/气泡 | DPI≥600 |
| 空间 | `Seurat` / `Giotto` / `BayesSpace` | Visium 等 | 按平台 |
| 书清 | `工具_单细胞对象.R` 等 | 生产封装 | 可选叠加 |

## 6. 数据可视化

对齐 [高分期刊出图范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) **Fig3**，并兼容 GEO 流水线编号图：

| 面板/序号 | 图种 | recipe / 说明 |
|-----------|------|----------------|
| QC | 质控前后小提琴 | `VlnPlot` nFeature/nCount/MT |
| 03 | Doublet UMAP | 按样本 |
| A / 07–09 | UMAP 簇/样本/分组 | `plot_umap_discrete_journal` / `bioinfo_umap_discrete` |
| 11–12 | Marker 点图/热图 | DotPlot / DoHeatmap |
| 13 | 注释 UMAP | SingleR celltype |
| G / 14–15 | 堆叠比例、分组箱线 | 与 UMAP 色一致 |
| 16–17 | Feature / Vln marker | 连续色 `bioinfo_feature_blue` |
| 18 | 火山图 | `plot_volcano_journal` |
| C / 19–20 | GO/KEGG 气泡 | `plot_enrich_dot_journal` |

**强制：** 细胞数/元数据可溯源；DPI≥600；SVG+PNG；每图 [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)；`05_reports/automatic_decisions.csv` 记录自动决策。

## 7. 数据结果解读

- 报告亚群变化与 marker；cluster 编号 ≠ 生物学名称
- 批次与生物学混淆须声明（Harmony 跳过原因写入决策表）
- 无可靠分组 → **跳过**组间 DEG/富集，勿编造对照
- 探索性细胞级 DEG 不得写成「确证组间差异」

## 8. 能否结合其它生信

bulk 转录组验证；细胞通讯；拟时序（进阶技能）；空间+病理；DEG→GSEA。

## 样例验证

样例：`01_样例_sample/`  
骨架：`脚本_scripts/运行单细胞空转骨架_runScrnaSkeleton.R`
