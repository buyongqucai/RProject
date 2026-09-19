# 清单：网络药理学_NetworkPharmacology

**路径:** `03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology`  
**范式:** `docs/agents/技能范式清单_SkillParadigm.md`  
**状态:** 已审  
**总评:** 合规  
**结构:** lines=66 docs=4 scripts=10 flags=none

## 技能说明

| 文件 | A1-A3 | B1-B4 | 判定 | 笔记 |
|------|-------|-------|------|------|
| `技能说明_网络药理学_NetworkPharmacology.md` | PASS | PASS | 合规 | lines=66 |

## 文档_docs

| 文件 | SSOT单点 | 指针有效 | 判定 | 笔记 |
|------|----------|----------|------|------|
| `出图约束_NetworkFigureStandards.md` | 抽查 | 是 | 保留 |  |
| `成分靶点获取与交付规范_CompoundTargetSOP.md` | 抽查 | 是 | 保留 |  |
| `手工导出与Cytoscape可选_ManualOps.md` | 抽查 | 是 | 保留 |  |
| `数据库分类与流水线_DataSourcesPipeline.md` | 抽查 | 是 | 保留 |  |

## 脚本_scripts

| 文件 | 入口/可读 | Viz/Delivery | 判定 | 笔记 |
|------|-----------|--------------|------|------|
| `01_契约接口_DataContracts.R` | 有 | 按技能 | 保留 |  |
| `02_可视化_NetworkPharmPlots.R` | 有 | 按技能 | 保留 |  |
| `03_STRING与网络图_StringNetwork.R` | 有 | 按技能 | 保留 |  |
| `04_交付网络布局_DeliveryNetworkLayouts.R` | 有 | 按技能 | 保留 |  |
| `05_高级附图_AdvancedPanels.R` | 有 | 按技能 | 保留 |  |
| `STP批量预测_stpBatchPredict.py` | 有 | 按技能 | 保留 |  |
| `TCMSP批量抓取_tcmspBatchScrape.py` | 有 | 按技能 | 保留 |  |
| `TCMSP靶点UniProt映射_mapTcmspUniprot.py` | 有 | 按技能 | 保留 |  |
| `说明_README.md` | 有 | 按技能 | 保留 |  |
| `运行骨架_runSkeleton.R` | 有 | 按技能 | 保留 |  |

## 样例

| 路径 | C1-C5 | 判定 | 笔记 |
|------|-------|------|------|
| `01_样例_sample/` | PASS | 有 | DATA_SOURCE=是 |

## 总结

- 总评：`合规`
- flags：none
- 已做修改：见工单 Notes / 本轮脚本小修
- 子工单：无
