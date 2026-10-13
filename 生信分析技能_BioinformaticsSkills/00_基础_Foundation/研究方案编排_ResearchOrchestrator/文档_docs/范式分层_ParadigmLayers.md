# 范式分层 / Paradigm Layers

> **地位：** 仓库内「范式」一词的唯一分层正文。改层定义或选图规则只改本文件。  
> **不覆盖：** 各 L2 recipe 仍在原 FROZEN / 期刊文档；本文件不复述配色、布局、图序。  
> **登记状态：** [`已跑通范式登记_FrozenParadigms.md`](../../统一可视化规范_VizStandards/文档_docs/已跑通范式登记_FrozenParadigms.md)（L2）。  
> **写法勾选（另一含义）：** [`技能范式清单_SkillParadigm.md`](../../../../docs/agents/技能范式清单_SkillParadigm.md)（L0）。

## 0. 选图（Agent 按此顺序）

1. 先定 **L4 论文/工作流**（用户要的是哪类成稿）。
2. 再跑所需 **L3 步骤**（步骤可脱离某篇论文单独调用）。
3. 出图时 L3 **只指向一套 L2**，不另写第三套样式：
   - L4 = 网络药理学（或用户明确要网药图样）→ 网药 FROZEN：[`出图约束_NetworkFigureStandards.md`](../../../03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/文档_docs/出图约束_NetworkFigureStandards.md)
   - L4 = 组学/临床期刊图 → [`高分期刊出图范式_JournalFigureParadigm.md`](../../统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md)
4. `frozen` 的 L2 recipe：未听到「解冻 / unfreeze」不改脚本与样例图。

同一分析两套合法图样，按 L4 选择，不互相覆盖：

| 步骤 | 网药图样（FROZEN） | 期刊图样 |
|------|-------------------|----------|
| 韦恩 | 出图约束 §G；轨 A `01`/`02` | 本仓库无第二套韦恩 recipe；非网药任务若未指定，仍用 §G，不自创 |
| STRING PPI | 出图约束 §B（同心 / Degree）；无成分层时不要画 HCTP | 步骤技能默认不另造网络皮肤 |
| GO / KEGG ORA | 图 06–10：BP/CC/MF 气泡与柱、KEGG 棒棒糖 / 柱 / 圈图；官方通路图 §F | 水平柱或气泡点图；GSEA 曲线。棒棒糖仅 Fig3-C，组学论文不作默认 |
| GSEA 曲线 | 网药图册不替代 GSEA 曲线 | Fig2-E·F / Fig3-D |

HCTP、疾病双口径、轨 B 目录只属于网药 **L4**，不是步骤的必交付。

## 1. L0 写法

新建或审计技能目录时的勾选清单，不是科学方法，也不是出图 recipe。  
SSOT：`docs/agents/技能范式清单_SkillParadigm.md`。

## 2. L1 横切

几乎所有交付都叠加，不替代 L2：

| 项 | 入口 |
|----|------|
| 命名、STATUS、目录 | `统一交付规范_DeliveryStandards` |
| DPI≥600、SVG+PNG、图面 English、PlotQA | `统一可视化规范_VizStandards` |
| 公共数据可追溯 | `数据真实性验证_DataAuthenticity` |

## 3. L2 图种 recipe

状态以冻结登记表为准。摘要：

- **frozen：** 网药全图册；分子动力学图册 01–26；分子对接 PyMOL（ST/PT/CJ/QJ）+ 亲和力热图（`vmax=0`）。
- **aligned：** 期刊多面板（火山、热图、KM、UMAP、富集柱）、PlotQA，以及 RNA-seq、GEO-TCGA、芯片、单细胞、GSEA、生存、DEG-UMAP 流水线的文档对齐。
- **aligned-by-reference：** 代谢、16S、GWAS、表观、蛋白组，以及除网药 / MD / 对接以外的药物计算技能。
- **pending：** 未点名技能；仍走 L1，不私自发明图样。

## 4. L3 分析步骤

可单独调用。图样由第 0 节的 L4 决定，步骤技能不拥有第二份 recipe。

| 步骤 | 技能 | 网药图样落点 |
|------|------|----------------|
| 多集合韦恩 / UpSet | 网药脚本可复用；无独立技能目录 | 出图约束 §G；UpSet 为图 16 |
| STRING PPI | `蛋白质互作网络_PPI-Network` | §B。触发「仅 PPI、无成分层」时用本技能，不画 HCTP |
| GO/KEGG ORA、GSEA、GSVA | `基因集富集与通路_GSEA-Pathway` | 网药论文：图 06–10 与 §C/§F。组学论文：期刊水平柱 / 气泡 / GSEA 曲线 |
| 其余 | DEG、WGCNA、生存、ROC、对接、MD、ADMET、蛋白结构、虚拟敲除等 | 各技能已对齐的 L2；对接与 MD 用各自 frozen recipe |

没有中药成分层时，仍可只跑交集、PPI、GO/KEGG（药–病交集即此类）。

## 5. L4 论文 / 工作流

组合 L3，不重写步骤实现。编排入口是本技能 `技能说明_研究方案编排_ResearchOrchestrator.md`；模板在 `工作流_workflows.json`。编排器本身不是一篇论文。

| 工作流 | 组合 | 专用、不可套到别的论文上的部分 |
|--------|------|--------------------------------|
| `wf-drug-target-gene` | 网药 → 结构 → 对接 → MD ± ADMET | HCTP、疾病双口径、轨 B、网药 HTML 报告 |
| 网络毒理 | 暴露/菌群代谢物 → 靶点网络 → 同图种 | 数据来源与库档位；图样可引用网药 L2，口径不照搬中药瀑布 |
| `wf-prognosis-survival` | GEO → 生存 ± ROC | 期刊 KM / ROC |
| `wf-mechanism-scrna` | 单细胞 ± 通讯 ± 转录组 | 期刊 UMAP / 比例 |
| `wf-metabolomics-rna` | 代谢 ± 转录 ± GSEA | 期刊图样 |
| `wf-cerna-mir` | ceRNA ± 转录组 | 期刊图样 |
| `wf-metagenome` | 宏基因组 | 期刊图样 |
| `wf-scm-deg-umap` | 四数据集 DEG-UMAP | 期刊 Fig1–3 |

编排组学论文时使用期刊图样。网药棒棒糖、同心 PPI、微生信韦恩只在 L4 为网药或用户点名网药图样时使用。
