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
6. `write_delivery_report()` → 合规 HTML

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 出图技术 | `ggplot2` + VizStandards `出版级出图_PublicationPlot.R` | DPI≥600 SVG+PNG；期刊版式 | **必须先 source** |
| 命名 | `规范_出图与命名_PlotNaming.R` | 中英对照 stem | 本技能 |
| 审计 | `规范_数据审计_DataAudit.R` | 样本数/行列/分组来源 | 本技能 |
| 报告 | `规范_报告生成_ReportBuild.R` | HTML 骨架 | 本技能 |

编排与任何样例：**requires** `bioinfo-viz-standards` + `bioinfo-delivery-standards`。

## 6. 数据可视化与文件命名（强制）

出图技术以 [`统一可视化规范_VizStandards`](../统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md) 为准（DPI≥600、SVG+PNG、色盲友好、单栏/双栏版式）。本技能强制**文件名语义化**。

**出图后审核钩子：** `delivery_save_plot()` 在保存后自动调用 VizStandards [`出图后审核_PlotQA`](../统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md) 启发式检查（色块/标签/长标签）；默认 WARN 不中断保存。网络等有坐标的图须在布局脚本中另调 `viz_qa_network_nodes()`。关闭钩子：`options(bioinfo.plotqa.after_save = FALSE)`；FAIL 时中断：`options(bioinfo.plotqa.hard_fail = TRUE)`。

### 文件名双语 ≠ 图面英文（必须严格区分）

| 层级 | 规则 | 示例 |
|------|------|------|
| **交付文件名** | **强制**中英对照 `{中文语义}_{EnglishPascal}.{ext}` | `热图_ContactMatrixStub_Heatmap.png` |
| **图内主标题 / 副标题 / 轴标题 / 图例 / strip / annotation**（`ggtitle` / `labs(title=…)` / `main=`） | **English only**；**禁止中文**出现在图内 | `Contact matrix (schematic · BLOCKED)` |

**禁止**把文件名对照逻辑搬进图面，写成中英并排标题，例如：

- ~~`接触矩阵示意 Contact Matrix Stub`~~
- ~~`火山图 Treat vs Control Volcano`~~
- ~~`接触矩阵（示意·BLOCKED）`~~（图面用中文）

图面状态词用英文（如 `schematic · BLOCKED`）；轴上惯用符号（`logFC`、`-log10(p)`）可保留。HTML 报告正文仍可用中文说明；**仅图面文字强制英文**。

### 结果文件命名（强制）

```
[{NN}_]{中文语义}_{EnglishCamelOrPascal}.{ext}
```

可选两位流水线序号前缀（`01_`、`02_`…）表示产出顺序；`delivery_stem(..., order = n)` / `delivery_save_plot(..., order = n)`。

可含对比/对象段，例如：

| 类型 | 模式 | 示例 |
|------|------|------|
| 图片 | `{NN}_{中文图类}_{对比或主题}_{EnType}.{png\|svg}` | `01_火山图_TreatVsControl_Volcano.png` + 同名 `.svg` |
| 数据表 | `{NN}_{中文表义}_{对象}_{EnType}.csv` | `02_差异结果_TreatVsControl_Deg.csv` |
| 审计表 | `审计前检_AuditPre.csv` / `审计后检_AuditPost.csv`（可加 `01_`） | （固定中英对照） |
| 契约桩 | `契约阻塞桩_ContractBlockedStub.csv` | BLOCKED 技能 |
| 报告 | `样例报告_SampleReport_v1.html` | |

样例目录角色与编号细则见 [`文档_docs/样例目录与命名_SampleLayoutNaming.md`](文档_docs/样例目录与命名_SampleLayoutNaming.md)。

**禁止**：纯英文无中文前缀的 `sample_*.csv`、`toy_*.csv`、`plot.png`、`fig1.png`、`RNA-seq_volcano_*.png`（仅技能英文开头）、无语义 `out.csv`。

技能英文缩写可作**目录名 / 内部 id / catalog id**，但**交付文件名**必须中英对照。

客观 BLOCKED 技能：产出与主题相关的契约表 + 审计表 + **主题相关示意/降级图**（图面英文标明 `schematic · BLOCKED`）；禁止无关 `toy_deg_results` 或滥贴火山图。

### 图册责任表门禁（对齐网络药理学标杆）

每个技能说明 **必须** 含「交付图册 × 实现状态」表，逐项标注：

| 状态 | 含义 |
|------|------|
| **R可复现** | 样例脚本必须真正产出（SVG+PNG） |
| **外部软件必做** | 本环境不做 GUI/商业工具出图；skill 写软件名、版本、逐步操作；样例 `STATUS` 标 `BLOCKED_EXTERNAL` 或总状态 `PARTIAL` |
| **不做** | 明确声明范围外 |

**禁止**：

- 用无关简图 / igraph 等「顶替」必须由 Cytoscape、AutoDock、MACS2 等完成的交付图
- 把 `PARTIAL` / `BLOCKED_EXTERNAL` 写成全流程 `PASS`
- 缺图却不在 skill 写清用什么软件、如何操作

标杆示例：[`网络药理学_NetworkPharmacology`](../../03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/技能说明_网络药理学_NetworkPharmacology.md)。

### STATUS 取值

| STATUS | 何时使用 |
|--------|----------|
| `PASS` | 该技能声明的 R 可复现图册与契约全部完成，且无未说明的外部缺图 |
| `PARTIAL` | R 子集完成 + 外部图已诚实断点（如网药） |
| `BLOCKED` / `BLOCKED_EXTERNAL` | 关键 CLI/GUI 不可用；仅契约桩 + SOP |

## 7. 数据结果解读

- 审计写出且图/表命名合规 → 可进入解读
- toy 数据结论必须写「不可外推」；REAL 须可核对 accession / 病名查询词 / 交付路径
- 报告须写明是否 `source` 了 VizStandards + DeliveryStandards + 本技能脚本
- `data_provenance` 可取 `REAL|TOY|BLOCKED`；图完成度另用 STATUS（勿混为一谈）

## 8. 能否结合其它生信

- 与 [`统一可视化规范_VizStandards`](../统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)：**互补且同时强制**（技术 vs 交付）
- 与 [`研究方案编排_ResearchOrchestrator`](../研究方案编排_ResearchOrchestrator/技能说明_研究方案编排_ResearchOrchestrator.md)：计划交付物必须遵守本规范；编排 **requires** 本技能 + VizStandards
- 与 [`数据真实性验证_DataAuthenticity`](../数据真实性验证_DataAuthenticity/技能说明_数据真实性验证_DataAuthenticity.md)：公共数据审计字段对齐
- **全部样例强制依赖**本技能与可视化规范（catalog：`requires: [bioinfo-viz-standards, bioinfo-delivery-standards]`）

## 样例验证

样例：`01_样例_sample/`（目录与命名见 [`文档_docs/样例目录与命名_SampleLayoutNaming.md`](文档_docs/样例目录与命名_SampleLayoutNaming.md)；迁移进度见 [`文档_docs/样例结构迁移清单_SampleLayoutMigration.md`](文档_docs/样例结构迁移清单_SampleLayoutMigration.md)）

```bash
Rscript 01_样例_sample/代码文件/01_run_sample.R
```
