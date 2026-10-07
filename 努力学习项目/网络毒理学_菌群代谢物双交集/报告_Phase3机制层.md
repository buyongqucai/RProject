# Phase 3 机制层执行报告

> 日期：2026-10-07
> 输入：`数据/C_main_evidence_priority_H_plus_M.csv`（78 个核心靶点）
> 方法来源：网络药理学技能的 STRING API、同心 Degree PPI、出版级出图、PlotQA 与交付命名规范。

## 1. PPI 与核心模块

- STRING：Homo sapiens，combined score ≥ 0.9。
- 主面板 PPI：52 个节点、90 条边。
- 全库敏感性 PPI：104 个节点、318 条边。
- 去孤立点后绘图；Degree 同时映射颜色和节点大小。
- CytoHubba 式 MCC-like 排序采用透明的 `Degree × local triangles` 指标，最高为 IL1B、TNF、IL6、JUN。由于本机无 Cytoscape/cytoHubba GUI，报告中不冒充官方插件原始分值。
- MCODE-compatible 模块检测按 BaderLab/MCODEAlgorithm 参数实现：degree cutoff=2、k-core=2、node score cutoff=0.2、haircut=true、fluff=false。得到 2 个 ≥3 节点模块：
  1. 炎症/趋化模块：JUN、IL1B、TNF、IL6、CCL2、CXCL8、ICAM1、MMP9、TLR4、IL10。
  2. 凋亡/存活模块：CASP3、BAX、BCL2、MCL1。

## 2. GO 与 KEGG

富集背景使用 UC D 集映射到 Entrez 后的 1,499 个背景基因；查询集 78/78 映射成功。

- GO：180 条显著条目。
- KEGG：24 条显著条目。
- 主要 KEGG：Lipid and atherosclerosis、Pathogenic E. coli infection、Fluid shear stress and atherosclerosis、AGE-RAGE、IL-17 signaling 等。
- GO 主要涉及脂质反应、含氧化合物反应、核受体/类固醇受体活性、金属肽酶活性等。

注意：富集主题包含广泛炎症、感染和代谢通路，符合 UC/网药数据的常见宽泛性；不能把所有显著通路都写成复方特异机制。

## 3. 核心代谢物–靶点与五层网络

- 核心代谢物–靶点配对：322 条。
- G-M-C-T-P 五层网络：62 个节点、106 条边。
- 节点层：Gut microbe → Metabolite → Compound → Target → Pathway。
- 图中只展示各层 Top-ranked 节点；完整关系保留在 CSV。

优先配对包括 Arginine–NOS2/NOS3、Indole–CYP1A1/OCLN/TJP1、Oleic acid–PPARG/PPARA/PPARD、Tryptophan–MPO 等。它们是共同调控候选，不是效应方向或结合验证。

## 4. 图件与 PlotQA

均输出同名 PNG+SVG，图面 English，DPI=600。

| 图件 | PlotQA |
|---|---|
| PPI 核心网络 | PASS |
| PPI 全库敏感性网络 | PASS |
| GO 富集 | PASS |
| KEGG 富集 | PASS |
| G-M-C-T-P 五层网络 | PASS |
| PPI MCC-like 核心靶点条形图 | PASS |
| 机制层组合图 | PASS |

## 5. 结论边界

- PPI、富集和五层网络支持“共同调控候选轴”的机制解释。
- MCC-like 与 MCODE 模块仍受 PPI 数据库和高连接炎症基因影响。
- 本阶段未完成毒性分层、分子对接、GEO、MR、MD；这些不能由当前网络图替代。
- 对接、GEO、MR 的结论仍按冻结计划写成结合候选、外部一致性和遗传支持。
