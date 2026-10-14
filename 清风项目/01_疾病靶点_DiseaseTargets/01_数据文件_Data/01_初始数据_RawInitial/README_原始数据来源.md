# 原始数据来源 README — 01_疾病靶点_DiseaseTargets

**状态：PENDING（2026-10-14 建骨架，数据未获取）**

## 本目录放什么

IPF（Idiopathic pulmonary fibrosis）疾病六库原始导出，每库一个子目录（SampleLayoutNaming §2.1）：

| 子目录 | 来源库 | 档位 |
|--------|--------|------|
| `01_GeneCards_疾病靶点_IpfTargets` | GeneCards | MANUAL（注册导出） |
| `02_TTD_疾病靶点_IpfTargets` | TTD | MANUAL |
| `03_DrugBank_疾病靶点_IpfTargets` | DrugBank | KEY（学术许可） |
| `04_OMIM_疾病靶点_IpfTargets` | OMIM | KEY |
| `05_CTD_疾病靶点_IpfTargets` | CTD | AUTO_BULK |
| `06_DisGeNET_疾病靶点_IpfTargets` | DisGeNET | KEY（学术注册） |

每子目录落库方原始导出 + `DATA_SOURCE.md`（库/版本/检索词/参数/获取时间/档位）。

## 获取策略与连通性

见 `../../../01_分析报告_AnalysisReport/01_课题说明_ProjectBrief/02_数据来源总览_DATA_SOURCE.md`（§1 实测矩阵、§3 前端接口复现约束）。
