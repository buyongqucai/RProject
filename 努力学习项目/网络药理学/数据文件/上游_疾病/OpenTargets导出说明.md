# Open Targets 导出说明（Ulcerative Colitis）

## 我导出的是什么？

通过 Open Targets **GraphQL API**（`api.platform.opentargets.org`）拉取的是：

**疾病–靶点关联总表**（Overall Association Score），不是网页上那张「证据气泡矩阵图」的截图。

对应疾病：`ulcerative colitis`（`MONDO_0005101`）

| 文件 | 内容 |
|------|------|
| `疾病靶点_OpenTargets.csv` | 完整表：gene / name / ensembl_id / score / disease_id / disease / source |
| `疾病靶点_OpenTargets_DiseaseGenes.csv` | 仅基因符号（下游交集用） |

字段含义：
- `gene`：Approved Symbol
- `name`：Approved Name
- `ensembl_id`：Ensembl gene id
- `score`：Open Targets **综合关联分数**（0–1，聚合 Clinical / GWAS / literature 等多源证据）
- 共 **7107** 个靶点（按 gene 去重）

**没有导出的内容：**
- 网页里按证据列（Clinical Precedence、GWAS、ClinVar、Europe PMC…）展开的气泡矩阵
- 各证据源的分列分数明细
- 该交互图本身的 PNG/SVG 矢量图

## 网页上的气泡图能不能导出？

| 方式 | 能否得到「图」 | 说明 |
|------|----------------|------|
| 页面 **Export** 按钮 | 通常是 **数据表**（TSV/CSV/JSON），不是气泡图图片 | 适合补全证据分列 |
| 浏览器截图 / 打印 PDF | 可以保存当前可见页的图 | 分页很多（上万行），无法一次导出全图 |
| GraphQL 再拉 `evidences` / datasource scores | 可得到做图用的分列数据 | 可用 R/Python 自绘类似热图/气泡图 |

结论：**综合分数表已自动拿到**；**气泡矩阵图本身不是 API 默认产物**，若需要分列证据或整图，可再导出/补拉。

## 注意

你截图 URL 里是 `MONDO_0008903`（肺癌示例页）；本项目病名是 **Ulcerative Colitis**（`MONDO_0005101`），请在 Open Targets 用溃疡性结肠炎页面核对/导出。

Open Targets 在网药技能中为 **陪跑库**（非交付主库）；交付主库仍是 GeneCards / TTD / DrugBank / OMIM / CTD / DisGeNET。