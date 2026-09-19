---
name: bioinfo-delivery-standards
description: >-
  统一交付规范：样例/结果的中英对照命名、数据审计、HTML 报告骨架、目录约定。
  与统一可视化规范互补——后者管出图技术（DPI/SVG/期刊版式），本技能管交付物命名与审计。
  任何样例 requires VizStandards + DeliveryStandards。
  触发：样例报告、文件命名、交付规范、审计表、sample report、未跟踪。
---

# 统一交付规范 / DeliveryStandards

## 1. 数据来源

本技能不产生生物学原始数据；约束各技能 `01_样例_sample/` 与项目交付物的**命名、审计、报告**。  
样例数据须在 `数据文件/DATA_SOURCE.md`、`代码文件/结果文件/报告文件/STATUS.txt`、`审计后检_AuditPost.csv` **显式标注**：

```
data_provenance: REAL | TOY | BLOCKED
```

| 取值 | 含义 |
|------|------|
| **REAL** | GEO/公共库真实下载、用户交付中间表、或可核对 accession/缓存 |
| **TOY** | 脚本内 `rnorm`/`runif`/硬编码矩阵等编造；**不可外推**为真实结论 |
| **BLOCKED** | 客观缺 CLI/商业库的契约桩；不得假装 PASS 分析 |

**禁止**把 TOY/BLOCKED 包装成真实分析结论。兼容旧字段 `toy=TRUE/FALSE`，但新样例以 `data_provenance` 为准。

### 关于 Cursor/Git「未跟踪 Untracked」

此处「未跟踪」指 **Git 对尚未 `git add` / 未 commit 的新文件** 的状态标记，**不是**文件扩展名或后缀名。

- 样例跑出的 `代码文件/结果文件/` 产物默认未入库属**正常**（避免把大图/中间表强行进版本库）。
- 若需纳入版本库：由用户自行 `git add` 相关路径；**不要擅自 `git commit`**，除非用户明确要求。

## 2. 数据规范（判断是否可用）

- 目录树符合 [项目结构规范_ProjectLayout.md](../../项目结构规范_ProjectLayout.md) 与 [`文档_docs/样例目录与命名_SampleLayoutNaming.md`](文档_docs/样例目录与命名_SampleLayoutNaming.md)
- **交付文件名强制中英对照**（见 §6）；禁止纯英文无中文前缀；推荐流水线 `01_`/`02_` 前缀
- 跑前/跑后写出审计表到 `代码文件/结果文件/数据文件/`
- HTML 报告用**相对路径**引用本样例图片，且含 PASS/BLOCKED
- `数据文件/` = raw only；结果不得放在样例根级 `结果文件/`（须在 `代码文件/结果文件/`）

## 3. 何时选用本技能

- 编写或重跑**任何**技能样例（与 [`统一可视化规范_VizStandards`](../统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md) **同时 requires**）
- 编排计划第 6 章「交付物」命名
- 用户质疑图雷同、命名随意、报告无图、Git「未跟踪」含义

不适用：纯算法草稿且不落地文件。

## 4. 数据处理方法

每个样例 `run_sample.R` **顶部强制**按序：

```r
# 1) source 统一可视化规范 出版级出图
# 2) source 统一交付规范 出图命名/审计/报告
# 3) source 本技能 脚本_scripts
```

具体：

1. `source` VizStandards `出版级出图_PublicationPlot.R`
2. `source` 本目录 `规范_出图与命名_PlotNaming.R` / `规范_数据审计_DataAudit.R` / `规范_报告生成_ReportBuild.R`
3. `source` **本技能** `脚本_scripts/*.R`（骨架/工具），禁止全局假 DEG 模板冒充
4. 文件名用 `delivery_stem()` / `delivery_table_name()` / `delivery_audit_name()` / `delivery_report_name()`（可选 `order=` 流水线序号）
5. 路径用 `delivery_sample_paths(sample_root)`（结果默认 `代码文件/结果文件/`，兼容旧根级回退）
6. `write_delivery_report()` → 合规 HTML（版式见 [`文档_docs/样例报告范式_SampleReportParadigm.md`](文档_docs/样例报告范式_SampleReportParadigm.md)；金标为分子动力学样例报告）

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 出图技术 | `ggplot2` + VizStandards `出版级出图_PublicationPlot.R` | DPI≥600 SVG+PNG；期刊版式 | **必须先 source** |
| 命名 | `规范_出图与命名_PlotNaming.R` | 中英对照 stem | 本技能 |
| 审计 | `规范_数据审计_DataAudit.R` | 样本数/行列/分组来源 | 本技能 |
| 报告 | `规范_报告生成_ReportBuild.R` | HTML 骨架 | 本技能 |

编排与任何样例：**requires** `bioinfo-viz-standards` + `bioinfo-delivery-standards`。

## 6. 数据可视化与文件命名（强制）

出图技术 → [`统一可视化规范_VizStandards`](../统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。  
**命名 / 图面英文 / 图册门禁 / STATUS** → [`文档_docs/交付命名与图册门禁_DeliveryNamingGate.md`](文档_docs/交付命名与图册门禁_DeliveryNamingGate.md)（SSOT）。  
目录树 → [`文档_docs/样例目录与命名_SampleLayoutNaming.md`](文档_docs/样例目录与命名_SampleLayoutNaming.md)。

摘要：交付文件名中英对照；图面 English only；BLOCKED 技能出契约桩 + 主题相关示意（图注 `schematic · BLOCKED`）。

## 7. 数据结果解读

- 审计写出且图/表命名合规 → 可进入解读
- toy 结论写「不可外推」；REAL 可核对 accession / 路径
- 报告须写明是否 `source` 了 VizStandards + DeliveryStandards + 本技能脚本
- `data_provenance` 与 STATUS 分列，勿混
- HTML 版式 → [`文档_docs/样例报告范式_SampleReportParadigm.md`](文档_docs/样例报告范式_SampleReportParadigm.md)

## 8. 能否结合其它生信

- 与 VizStandards：**互补且同时强制**
- 与 ResearchOrchestrator：计划交付物须遵守本规范
- 与 DataAuthenticity：公共数据审计字段对齐
- catalog：`requires: [bioinfo-viz-standards, bioinfo-delivery-standards]`

## 样例验证

`01_样例_sample/`（迁移见 [`文档_docs/样例结构迁移清单_SampleLayoutMigration.md`](文档_docs/样例结构迁移清单_SampleLayoutMigration.md)）

```bash
Rscript 01_样例_sample/代码文件/01_run_sample.R
```
