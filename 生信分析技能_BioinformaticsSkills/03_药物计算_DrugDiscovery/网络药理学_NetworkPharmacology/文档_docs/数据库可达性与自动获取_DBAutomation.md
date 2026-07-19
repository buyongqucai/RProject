# 数据库可达性与自动获取（实测）

> 探测日期：2026-07-19（本机 HTTP/API 探测）。  
> **自动（AUTO）** = 代码/AI 可程序化取数；**手工（MANUAL）** = 需用户浏览器导出后放入 `数据文件/`；**陪跑** = 非交付主库、可选。

## 总表

| 类别 | 数据库 | 官网 | 本机可达 | 自动取数 | 结论 / 你需配合 |
|------|--------|------|----------|----------|-----------------|
| 疾病 | GeneCards | https://www.genecards.org/ | 403 禁止 | **MANUAL** | 浏览器按英文病名导出 CSV |
| 疾病 | TTD | https://db.idrblab.net/ttd/ | 200 | **MANUAL** | 页可达；无稳定公开批量 API，请网页导出 |
| 疾病 | DrugBank | https://go.drugbank.com/ | 403 禁止 | **MANUAL** | 登录/导出；本环境爬虫不可用 |
| 疾病 | OMIM | https://www.omim.org/ | 403 禁止 | **MANUAL**（可选 API） | 网页导出；或自备 `OMIM_API_KEY` |
| 疾病 | CTD | https://ctdbase.org/ | 首页易 302；**bulk 200** | **AUTO（bulk）** | `CTD_curated_genes_diseases.tsv.gz` 可下；按英文病名/MeSH 过滤 |
| 疾病 | DisGeNET | https://disgenet.com/ | 200 | **MANUAL** | 站可开；免费批量 API 未打通，请网页/账号导出 |
| 药物 | TCMSP | https://tcmsp-e.com/ | 首页 200；旧入口偶发连不上 | **MANUAL** | 无公开 REST；单药 OB/DL/靶点请网页导出 |
| 药物 | BATMAN-TCM | http://bionet.ncpsb.org.cn/batman-tcm/#/search | 200 | **MANUAL** | 仅 known 靶点；网页导出，禁止预测 |
| 药物 | ETCM2 | http://www.tcmip.cn/ETCM2/front/#/ | 200 | **MANUAL** | 前端页可达；无公开 API 实测 |
| 药物 | HERB 2.0 | http://47.92.70.12/ | 200 | **MANUAL** | 取成分+SMILES 后交 Swiss；网页导出 |
| 药物 | TCMBank | https://tcmbank.cn/（HTTPS TLS 失败）；**http://tcmbank.cn/** 200 | **MANUAL** | 优先用 http 打开；成分导出后再预测 |
| 药物 | SwissTargetPrediction | https://swisstargetprediction.ch/ | 200 | **MANUAL** | 表单站；无公开 REST；SMILES 提交后导出；MW 过大 → 异常清单 |
| 通路 | KEGG | https://www.kegg.jp/ + REST | 200 | **AUTO（REST）** | `https://rest.kegg.jp/` 列表/通路可程序化；官网位图下载仍可手工 |
| PPI | STRING | https://string-db.org/ + API | 200 | **AUTO（API）** | `get_string_ids` / `network` 已测通；**R/代码出图，无需 Cytoscape 手绘** |
| 陪跑 | Open Targets | GraphQL API | 200 | **AUTO（陪跑）** | 非交付主疾病库；可陪跑校验 |

## 出图（相对旧计划的修正）

| 图种 | 旧说法 | 实测/现行 |
|------|--------|-----------|
| STRING PPI 渐变/同心 | Cytoscape / 网页手绘 `BLOCKED_EXTERNAL` | **代码/AI 可绘**（STRING API + R：`04_交付网络布局_*.R`） |
| 药–成分–靶–通路网络 | 必须 Cytoscape GUI | **代码/AI 可绘**（`np_plot_hctp_network`）；Cytoscape 仅可选精修 |
| 疾病/药病韦恩、GO/KEGG 柱气泡等 | R | 仍为 R（需已有结果表或 CTD/KEGG 等自动源） |

## 探测原始记录

- `_db_probe_raw.json` / `_db_probe_deep.json`（同目录，机读缓存）

## 用户手工配合清单（请按此准备文件）

放入 `01_样例_sample/数据文件/`（或项目 raw 目录），英文病名 + 单药名可溯源：

1. `疾病靶点_GeneCards.csv`
2. `疾病靶点_TTD.csv`
3. `疾病靶点_DrugBank.csv`
4. `疾病靶点_OMIM.csv`
5. `疾病靶点_DisGeNET.csv`（新增）
6. 每药：TCMSP / BATMAN(known) / ETCM / HERB·TCMBank 成分表（按瀑布有则提供）
7. 若走预测：SwissTargetPrediction 导出表（已剔 probability=0）；失败行进 `异常清单_CompoundTargetExceptions.csv`

CTD / KEGG / STRING **不必**手工（代码可拉），除非你想固定某一版缓存。
