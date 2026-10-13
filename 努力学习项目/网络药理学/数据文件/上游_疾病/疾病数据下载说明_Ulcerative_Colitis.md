# 疾病数据下载状态 — Ulcerative Colitis

- 英文病名: `Ulcerative Colitis`（来自 `疾病英文名称.csv`）
- CTD MeSH 名: `Colitis, Ulcerative`（MESH:D003093）
- 输出目录: `D:\网络药理学文件\准备文件`

## 已自动完成（AUTO）

| 库 | 基因数 | 文件 |
|----|--------|------|
| **CTD**（curated DirectEvidence） | 70 | `疾病靶点_CTD.csv` / `疾病靶点_CTD_DiseaseGenes.csv` |
| **Open Targets**（陪跑，非交付主库） | 7107 | `疾病靶点_OpenTargets.csv` / `疾病靶点_OpenTargets_DiseaseGenes.csv` |
| AUTO 并集（CTD∪OpenTargets） | 7109 | `疾病靶点合并_AUTO_DiseaseGenesUnion.csv` |
| AUTO 分库 | 7177 行 | `疾病靶点按库_AUTO_DiseaseGenesByDB.csv` |

另存：`CTD_Ulcerative_Colitis_all_associations.csv`（含化学推断关联，约 3.2 万基因，**下游分析勿直接当 curated 用**）。

状态 JSON：`疾病数据下载状态.json`

## 需浏览器手工导出（MANUAL）

按网络药理学技能说明，以下库无稳定公开批量 API，请用英文病名 **Ulcerative Colitis** 导出后放入本目录：

1. **GeneCards** https://www.genecards.org/ → 检索 → 导出 Results CSV → `GeneCards Results.csv` 或 `疾病靶点_GeneCards.csv`（韦恩用全量；下游交集 Relevance≥40）
2. **TTD** https://db.idrblab.net/ttd/ → 疾病检索导出 → `TTD疾病靶点数据.csv` / `疾病靶点_TTD.csv`
3. **DrugBank** https://go.drugbank.com/ → 疾病相关靶点 → `Drugbank疾病靶点数据.csv`
4. **OMIM** https://www.omim.org/ → Gene Map Search 导出 → `OMIM疾病靶点数据.csv`
5. **DisGeNET** https://disgenet.com/ → 疾病基因关联导出 → `疾病靶点_DisGeNET.csv`

## 说明

- 交付主疾病库：GeneCards / TTD / DrugBank / OMIM / CTD / DisGeNET
- 本机已完成：**CTD**；陪跑：**Open Targets**
- GeneCards / TTD / DrugBank / OMIM / DisGeNET 需你本地浏览器导出后放入上述目录，即可继续多库韦恩与药–病交集
