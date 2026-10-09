# 网络药理学工具链

> 库表与瀑布步骤的唯一正文：[`数据库分类与流水线_DataSourcesPipeline.md`](数据库分类与流水线_DataSourcesPipeline.md)。  
> 本文件只登记**本机用来跑这条流水线的程序**，不复述库清单。

| 步骤 | 工具 | 本机位置 / 调用 | 备注 |
|------|------|-----------------|------|
| 表与图 | R（ggplot2、circlize） | 技能 `脚本_scripts/` | 韦恩、GO/KEGG、网络预览 |
| PPI | STRING API + 本技能布局脚本 | `03_STRING与网络图_StringNetwork.R`、`04_交付网络布局_DeliveryNetworkLayouts.R` | 官方 3D 图可另存；假边禁止冒充 STRING |
| 网络精修 | Cytoscape | 可选，手工 | 见 [`手工导出与Cytoscape可选_ManualOps.md`](手工导出与Cytoscape可选_ManualOps.md) |
| GO 原始 | Metascape | 外部网站 | 样例可用预计算表 |
| 通路 | KEGG REST | AUTO | 官网位图可选、非默认 |
| 疾病/成分库 | GeneCards、TTD、DrugBank、OMIM、CTD、DisGeNET、TCMSP 等 | 多数 MANUAL 导出 | 档位见流水线 SSOT |
| 预测靶点 | SwissTargetPrediction | 网页或已导出表 | Probability=0 剔除 |
| 下游结构 | 蛋白结构 → 分子对接 → 分子动力学 | 各自技能 | 不在本技能内改对接/MD 的 FROZEN |

课题原始表（SEA、STP、疾病库导出）放在该课题目录，不放进本技能。
