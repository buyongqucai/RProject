# DATA_SOURCE — 复方 UC 菌群代谢物三源共有靶点研究

> 访问/构建日期：2026-10-07
> provenance：交付 F/D/I₁ = `REAL`；外部数据库原始下载 = `REAL`；SEA/STP = `PREDICT`。
> 大型原始下载与批量预测缓存不进 Git；本文件保留版本、入口、快照计数和哈希/清单指针。

## 1. 固定项目输入（不修改）

| 集合 | 文件 | 项目口径 | provenance |
|---|---|---:|---|
| F 复方全药靶点 | `E:\RProject\努力学习项目\交付文件\数据\药物\药物靶点_全药.csv` | 636 个基因 | REAL |
| D UC 疾病靶点 | `E:\RProject\努力学习项目\交付文件\数据\疾病\疾病靶点合并.csv` | **1517（冻结口径）** | REAL |
| I₁ 复方–UC 交集 | `E:\RProject\努力学习项目\交付文件\数据\药物\药物疾病交集.csv` | 291 个基因 | REAL |

说明：D 按用户冻结口径固定为 1517；本阶段另记录 HGNC 标准化规则，但不改写该固定数字。

## 2. gutMGene v2.0

- 站点：`http://bio-computing.hrbmu.edu.cn/gutmgene/`
- API/下载根：`http://bio-computing.hrbmu.edu.cn/gutMGene2.0_api`
- 论文：PMID 39475181；DOI `10.1093/nar/gkae1002`
- 下载文件（2026-10-07）：
  - `Gut Microbe-Microbial metabolite.csv`：2488 行；human 子集 830 行、251 个唯一代谢物。
  - `Gut Microbe-Host Gene.csv`：1323 行。
  - `Microbial metabolite-Host Gene.csv`：1049 行；human 子集 265 行、45 个唯一代谢物、154 个基因。
- 本课题的“全库敏感性”定义为上述可下载文献关联表中 `human/mouse=human` 的 251 个唯一代谢物快照；H₂S 按特殊暴露物另列，因此进入小分子分析的全库敏感性面板为 250 个。论文中的 278 个还包括数据库其它层级/重建条目，不强行混入本快照。

## 3. GMMAD2

- 站点：`http://gepa.org.cn/GMMAD2/`
- UC：`/GMMAD2/browse3/D003093/`，2243 个代谢物；`FDR<0.05` 为 1642 个。
- IBD：`/GMMAD2/browse3/D015212/`，2146 个代谢物；`FDR<0.05` 为 1628 个。
- GMMAD2 score 为疾病/菌群丰度变化推导的关联分数；置信信息使用页面 `P_value/FDR`。本项目不把 score 当作实验效应量。
- 原始 HTML 保存在 `准备文件/外部数据库/GMMAD2/`（不进 Git）。

## 4. PubChem

- PUG REST：`https://pubchem.ncbi.nlm.nih.gov/rest/pug`
- 用途：按 CID/名称补齐 canonical/isomeric SMILES、InChIKey、分子式与分子量。
- 本次主面板 112/112 有 SMILES；gutMGene human 全库 228/251 有 SMILES；并集 313/336 有 SMILES。缺失项进入异常清单，不编造结构。

## 5. 靶点预测

| 工具 | 版本/库 | 保留规则 | 状态 |
|---|---|---|---|
| SwissTargetPrediction | Homo sapiens；站点 2026-10-07 可达 | `Probability > 0` | 300/335 个输入有保留结果；其余进异常清单 |
| SEA | 新站 ChEMBL 36/ECFP4 公共代理多次 502；回退 SEA16 ChEMBL 27/rdkit_ecfp4 | SEA16 官方 `sea-results.xls` 中 Homo 结果，按 Query ID 追溯 | 32/32 批次完成，27,754 条逐化合物命中 |
| gutMGene 实证 | human `Microbial metabolite-Host Gene.csv` | 直接进入 H 证据级 | 已下载 |

`M = H ∪（SEA∩STP）`；单工具命中只进补充/异常审计，不进入核心 M。

## 6. 文件状态

- 已生成：`数据/代谢物/` 下的 GMMAD2 表、主面板、全库敏感性、纳入排除清单、特殊暴露物。
- 已生成：`准备文件/预测输入/`。
- 缓存目录：`准备文件/外部数据库/`、`准备文件/STP原始/`、`准备文件/SEA原始/`，默认不进 Git。
