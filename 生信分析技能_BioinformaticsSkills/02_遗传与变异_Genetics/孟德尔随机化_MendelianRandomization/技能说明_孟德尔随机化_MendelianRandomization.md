---
name: bioinfo-mr
description: >-
  孟德尔随机化 / MendelianRandomization：用遗传工具变量检验暴露对结局的因果假设。
  默认路径为汇总数据两样本、乘法随机效应 IVW，敏感性用不同假设的稳健方法。
  触发：孟德尔随机化, Mendelian randomization, TwoSampleMR, IVW, 工具变量, STROBE-MR, 药物靶点 MR。
---

# 孟德尔随机化 / MendelianRandomization

**流水线 SSOT：** [`文档_docs/实现流水线_MrPipeline.md`](文档_docs/实现流水线_MrPipeline.md)（现行默认，尚未冻结）  
**版本与文献 SSOT：** [`文档_docs/信源与工具选型_SourcesAndStack.md`](文档_docs/信源与工具选型_SourcesAndStack.md)（检索日 2026-10-30）

出图叠加 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md) 与 [统一交付规范](../../00_基础_Foundation/统一交付规范_DeliveryStandards/技能说明_统一交付规范_DeliveryStandards.md)。

## 1. 数据来源

暴露与结局的 GWAS 汇总统计，或（路径 E）同一个体的基因型与表型。每份数据写明编号、基因组版本、祖先、样本量、效应量尺度、URL 和下载日期。OpenGWAS 程序化访问使用 `OPENGWAS_JWT`，令牌不入库。

## 2. 数据规范（判断是否可用）

协调后至少保留 1 个 SNP，且 LD 参考人群与样本祖先一致，才进入估计。平均 F≤10、样本重叠、或工具变量全在同一基因区时，改走流水线中的对应路径。估计、区间和 p 值只来自本次运行输出。

## 3. 何时选用本技能

- 要用遗传变异作为工具变量，检验「干预该暴露是否影响该结局」
- 输入是暴露与结局的汇总统计，或明确的单样本个体数据

不适用：只做 GWAS 位点发现（用全基因组关联分析技能）；只评估性状间共享遗传率；网络药理学里的靶点交集。

## 4. 数据处理方法

先在运行记录里选定路径，再估计：

| 路径 | 何时 | 主分析 |
|------|------|--------|
| A 默认 | 两样本、单一暴露、独立工具变量 | 乘法随机效应 IVW（≤3 个 SNP 时固定效应） |
| B 多变量 | 多个暴露共用工具变量 | MVMR，先报告条件 F |
| C 药物靶点 | 同一基因区 | cis 工具变量 + coloc |
| D 分子性状 | 暴露是 xQTL | SMR + HEIDI |
| E 单样本 | 个体水平数据 | 两阶段最小二乘 |

路径 A 的敏感性至少包括加权中位数、加权众数或 contamination mixture、以及 MR-Egger 截距。步骤与停下条件只维护在流水线文件。

## 5. R 包与软件栈

默认：`TwoSampleMR`（取数、协调、`mr_ivw_mre`、作图）+ `ieugwasr` + `MendelianRandomization::mr_ivw`（主分析）。`mr()` 默认的 `mr_ivw` 含欠离散校正，只作对照列。

重叠、弱工具变量、MVMR、MR-PRESSO、coloc、SMR 是分支工具。版本号只维护在选型文件。执行前核对 Burgess 指南是否已有 version 3 之后的更新。

骨架脚本 `脚本_scripts/运行骨架_runSkeleton.R` 只检查默认包是否可加载，不跑因果估计。

## 6. 数据可视化

路径 A 交付散点、森林、漏斗、留一法四张图。图面英文、DPI≥600、SVG+PNG，出图后 PlotQA。文件名中英对照。

## 7. 数据结果解读

在写明的工具变量假设下检验因果假设。效应对应遗传差异所代理的长期暴露差异。主分析与敏感性不同号时，结论写明方法名。报告附 STROBE-MR 清单（<https://www.strobe-mr.org/>）。

## 8. 能否结合其它生信

GWAS 技能提供汇总统计的质控与位点背景；药物靶点路径在本技能内做 coloc，不把共定位另写成一套阈值。出图与目录分别走 VizStandards、DeliveryStandards。

## 样例

`01_样例_sample/` 的 provenance 为 **TOY**，只验证目录结构，不作为真实 MR 结论。
