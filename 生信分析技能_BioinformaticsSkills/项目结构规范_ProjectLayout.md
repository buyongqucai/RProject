# 生信分析技能 — 项目结构规范 / Bioinformatics Skills — Layout Spec

本文件为 Skill 组的目录、命名与**正文模板 SSOT**。  
实体根：`E:/RProject/生信分析技能_BioinformaticsSkills/`  
Cursor 入口：`.cursor/skills/生信分析技能_BioinformaticsSkills/SKILL.md`（仅此处保留协议名 `SKILL.md`）

---

## 1. 中英对照命名（强制）

| 规则 | 说明 |
|------|------|
| 格式 | `中文简述_EnglishName`（下划线分隔） |
| 目录 | 顾名思义；禁止空泛名 |
| 技能正文 | `技能说明_<文件夹名>.md`；内容树**禁止** `SKILL.md` |
| 组总说明 | `技能组总说明_BioinformaticsSkills.md` |

唯一允许的 `SKILL.md`：Cursor 发现入口薄指针。

目录对照（含编排）：

| 目录 | 说明 |
|------|------|
| `研究方案编排_ResearchOrchestrator` | 研究目的→计划（优先入口） |
| `统一可视化规范_VizStandards` | 出版级出图技术（DPI/SVG/中文） |
| `统一交付规范_DeliveryStandards` | 命名 + 审计 + HTML 报告 + 样例目录约定 |
| `数据真实性验证_DataAuthenticity` | 公共数据真实性 |
| `转录组分析_RNA-seq` 等 | 见 `索引_INDEX.md` |

---

## 2. 技能说明正文模板（强制 8 段）

每个 `技能说明_*.md` **必须**含以下章节（禁止只写空泛提纲、禁止无 R 包表）：

1. **数据来源**
2. **数据规范（判断是否可用）**
3. **何时选用本技能**（触发条件 / 不适用场景）
4. **数据处理方法**（有序步骤）
5. **R 包与软件栈**（表格：`步骤 | R包或CLI | 作用 | 备注`）
6. **数据可视化**（DPI≥600；SVG+PNG；中文；防遮挡）
7. **数据结果解读**
8. **能否结合其它生信**（可组合技能路径）

CLI 工具（如 Bowtie2/MACS2）可写在同一表，**不得假装全流程仅一个 R 包**。

研究目的类请求：先读 `研究方案编排_ResearchOrchestrator`，再读本模板下的具体技能。

---

## 3. 目录树（摘要）

```text
生信分析技能_BioinformaticsSkills/
├── 技能组总说明_BioinformaticsSkills.md
├── 索引_INDEX.md
├── 目录重构说明_LayoutMigration.md
├── 技能目录_skill-catalog.json   # layout_version + category
├── 工作流_workflows.json
├── 00_基础_Foundation/
├── 01_组学_Omics/                    # 仅真正组学
├── 02_遗传与变异_Genetics/
├── 03_药物计算_DrugDiscovery/
├── 04_临床预测与统计_ClinicalStats/
├── 05_系统方法_SystemsMethods/
├── 06_已落地流水线_ProductionPipelines/
└── 07_分类验证_Validation/
```

每个技能目录：

```text
<技能目录>/
  技能说明_*.md
  脚本_scripts/
  01_样例_sample/          # 两位数字前缀排序；多例用 02_、03_…
    数据文件/              # RAW only（原始/输入）
    代码文件/              # 脚本 + 嵌套结果
      01_run_sample.R
      结果文件/
        图片文件/
        数据文件/
        报告文件/
```

**注意：** 结果必须在 `代码文件/结果文件/`，**禁止**与 `代码文件`、`数据文件` 同级的根级 `结果文件/`（旧布局仅作 `delivery_sample_paths()` 回退兼容）。  
完整约定见 [`统一交付规范_DeliveryStandards/文档_docs/样例目录与命名_SampleLayoutNaming.md`](00_基础_Foundation/统一交付规范_DeliveryStandards/文档_docs/样例目录与命名_SampleLayoutNaming.md)。

## 4. 样例与交付命名（强制，见 DeliveryStandards）

`01_样例_sample/代码文件/结果文件/` 强制中英对照，推荐流水线序号：`{NN}_{中文语义}_{EnglishCamelOrPascal}.{ext}`。  
禁止 `plot.png`、`sample_*.csv`、`toy_*.csv`、纯英文无中文前缀名。

| 类型 | 模式 | 示例 |
|------|------|------|
| 图片 | `{NN}_{中文图类}_{主题}_{EnType}.{png\|svg}` | `01_火山图_TreatVsControl_Volcano.png` |
| 数据表 | `{NN}_{中文表义}_{对象}_{EnType}.csv` | `02_差异结果_TreatVsControl_Deg.csv` |
| 审计 | 固定名，可加序号 | `01_审计后检_AuditPost.csv` |
| 报告 | 固定模式 | `样例报告_SampleReport_v1.html` |

**Git「未跟踪」**：指尚未 `git add` 的新文件状态，不是扩展名；样例产物默认未入库正常，需入库时再 add（勿擅自 commit）。

出图 API 只用 `统一可视化规范_VizStandards/.../出版级出图_PublicationPlot.R` 的 `save_plot_pub`（经 DeliveryStandards `delivery_save_plot` 封装）。  
样例 `run_sample.R` 须按序 source：VizStandards → DeliveryStandards → 本技能 `脚本_scripts/`。

## 5. Agent 加载

1. 研究目的 → `研究方案编排_ResearchOrchestrator`（7 章计划）  
2. 按计划打开对应 `技能说明_*.md`（用其 R 包表）  
3. 公共数据 → 真实性；出图 → 可视化规范；交付命名/报告 → 交付规范  
