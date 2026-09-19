# 数据库分类与流水线（网药）— SSOT

> 从技能说明披露；改库表/瀑布/AUTO-MANUAL 只改本文件。  
> 成分靶点交付精简 → [`成分靶点获取与交付规范_CompoundTargetSOP.md`](成分靶点获取与交付规范_CompoundTargetSOP.md)  
> 手工导出 / Cytoscape 可选 → [`手工导出与Cytoscape可选_ManualOps.md`](手工导出与Cytoscape可选_ManualOps.md)

## 1. 三类库不得混写

疾病基因库 ≠ 药物/成分–靶点库 ≠ 通路/PPI 库。

### 1.1 疾病（六库，英文病名）

| # | 数据库 | 产出 |
|---|--------|------|
| 1 | GeneCards | `疾病靶点_GeneCards.csv` |
| 2 | TTD | `疾病靶点_TTD.csv` |
| 3 | DrugBank | `疾病靶点_DrugBank.csv` |
| 4 | OMIM | `疾病靶点_OMIM.csv` |
| 5 | CTD | `疾病靶点_CTD.csv` |
| 6 | DisGeNET | `疾病靶点_DisGeNET.csv` |

疾病多库韦恩用**完整 GeneCards**；下游用 Relevance≥40 过滤后再与其他库并集。见出图约束 **§0a**。

### 1.2 药物 / 成分–靶点

| 库 | 用途 |
|----|------|
| TCMSP | 优先：OB≥30%, DL≥0.18 + 成分–靶点 |
| BATMAN-TCM | **仅 known/curated**；禁止预测靶点 |
| ETCM / ETCM2 | 补充 |
| HERB 2.0 | 成分 + SMILES → SwissTargetPrediction |
| SwissTargetPrediction | 剔除 Probability=0 |
| TCMBank | 可取成分再预测 |

### 1.3 通路 / PPI

KEGG（通路）；STRING（PPI）。

### 1.4 AUTO vs MANUAL（2026-07-19）

| 能力 | 库 |
|------|-----|
| AUTO | CTD bulk；KEGG REST；STRING API；HERB chedi；STP 表单（可达时） |
| MANUAL | GeneCards、TTD、DrugBank、OMIM、DisGeNET；TCMSP、BATMAN、ETCM2、TCMBank；AUTO 失败回退 |

## 2. 流水线步骤（摘要）

1. 单药列表 → 2. 每药瀑布成分–靶点 → 3. 六库疾病导出 → 4. 疾病韦恩/并集 → 5. 全药∩疾病 → 6. 每药∩疾病 → 7. network.csv + type.csv（A/B/C/D）→ 8. STRING API + 代码 PPI → 9. GO/KEGG → 10. 代码 HCTP 网络 → 11. 审计/PlotQA/异常清单  

瀑布细则与异常清单列 → CompoundTargetSOP。  
`network.csv`：A–B、B–C、C–D；`type.csv`：A药 B成分 C靶点 D通路。
