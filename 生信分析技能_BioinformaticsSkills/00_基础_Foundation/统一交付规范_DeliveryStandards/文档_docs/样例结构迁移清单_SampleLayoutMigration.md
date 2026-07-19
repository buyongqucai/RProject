# 样例结构迁移清单 / Sample Layout Migration Checklist

**规范 SSOT：** [`样例目录与命名_SampleLayoutNaming.md`](样例目录与命名_SampleLayoutNaming.md)  
**日期：** 2026-07-19  

状态含义：

| 状态 | 含义 |
|------|------|
| **done_full** | 结果已嵌套 `代码文件/结果文件/` + 脚本/`NN_` 编号 + 主要图/表编号 |
| **done_layout+script** | 嵌套布局 + `01_run_sample.R` + `delivery_sample_paths()`；图/表编号待补 |
| **done_layout** | 嵌套布局 + README stub + 路径助手；脚本多为 `run_sample.R`；文件编号 pending |
| **pending_numbering** | 仅缺流水线文件编号（布局已完成） |

全库 `01_样例_sample`：**70/70** 已将 `结果文件/` 迁入 `代码文件/结果文件/`（无遗留根级 `结果文件/`）。

---

## done_full（参考实现）

| 技能 | 备注 |
|------|------|
| `03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology` | 脚本 `01`/`02`/`03`；图 `01`–`15`；结果表编号；视觉 **仍 frozen** |

重跑：

```bash
Rscript 01_样例_sample/代码文件/01_run_sample.R
# 可选
Rscript 01_样例_sample/代码文件/02_run_network_preview.R
Rscript 01_样例_sample/代码文件/03_regen_hctp_layouts.R
```

---

## done_layout+script（高流量）

| 技能 | 脚本 |
|------|------|
| `00_基础_Foundation/统一交付规范_DeliveryStandards` | `01_run_sample.R` |
| `00_基础_Foundation/统一可视化规范_VizStandards` | `01_run_sample.R` |
| `01_组学_Omics/转录组分析_RNA-seq` | `01_run_sample.R` |
| `01_组学_Omics/公共库挖掘_GEO-TCGA` | `01_run_sample.R` |
| `01_组学_Omics/基因芯片表达分析_Microarray` | `01_run_sample.R` |
| `05_系统方法_SystemsMethods/基因集富集与通路_GSEA-Pathway` | `01_run_sample.R` |
| `04_临床预测与统计_ClinicalStats/生存分析与预后模型_Survival` | `01_run_sample.R` |
| `06_已落地流水线_ProductionPipelines/差异分析和UMAP流水线_DEG-UMAP` | `01_run_sample.R` |

上述技能图/表 `NN_` 前缀：**pending_numbering**（重跑样例时用 `delivery_save_plot(..., order=)` 补齐）。

---

## done_layout（其余全部样例）

其余 ~61 个 `01_样例_sample`：

- 已迁移：`结果文件/` → `代码文件/结果文件/`
- 已写：`README_样例目录.md`
- 已改：`run_sample.R` 使用 `delivery_sample_paths()`（在 source PlotNaming 之后）
- **pending：** 脚本改名 `01_run_sample.R`；结果图/表流水线编号

含：Foundation 其它、组学大部分、Genetics 全部、DrugDiscovery（除 NetPharm）、ClinicalStats（除 Survival）、SystemsMethods（除 GSEA）等。

---

## 助手与工具

| 文件 | 作用 |
|------|------|
| `脚本_scripts/规范_出图与命名_PlotNaming.R` | `delivery_sample_paths` / `delivery_order_prefix` / `order=` |
| `_migrate_sample_layout.py` | 批量嵌套迁移（已执行） |
| `_fix_paths_order.py` | 修正 paths 须在 source 之后 |

---

## 兼容

`delivery_sample_paths()`：优先 `代码文件/结果文件/`；若仅有旧根级 `结果文件/` 则回退（`layout="legacy"`）。新工作禁止再建根级结果目录。
