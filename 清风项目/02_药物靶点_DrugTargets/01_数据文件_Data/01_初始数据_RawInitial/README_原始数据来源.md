# 原始数据来源 README — 02_药物靶点_DrugTargets

**状态：ACTIVE（2026-10-16 洁净：只保留已抓库子目录）**

## 规则

**无库不建夹。** 瀑布中未走到的库（ETCM / HERB / STP / TCMBank）**不预建空目录**；走到再创。

## 本目录实际内容

| 子目录 | 来源库 | 内容 |
|--------|--------|------|
| `01_TCMSP_成分靶点_CompoundTargets/` | TCMSP | 全量目录 JSON + 8 味药药材成分导出 + PubChem 辅助属性；下游按 OB≥30%、DL≥0.18 筛 |
| `02_BATMAN_成分靶点_CompoundTargets/` | BATMAN-TCM 2.0 | **仅水蛭**：按药 API 作业包/JSON（非全库 browse）；known 视图 + 混条审计后专属成分 |

## 清风 BATMAN 水蛭怎么来的（事实）

**不是** Download 页 `known_browse_by_*` 全库下载再筛。  
流程：`POST queryTarget`（拼音 `shui zhi` 作业）→ 轮询 `queryTargetResult` → 存作业包 zip/JSON → 发现 Related Herb 实为**水栀子**混条 → 人工成分归属截取，只留水蛭专属 known 边（结果表在 `02_结果数据_ResultTables/BATMAN_水蛭*`）。

教训：非 TCMSP 检索必须拉丁/英文名（见技能 CompoundTargetSOP §8）。

## 获取策略

见 `../../../01_分析报告_AnalysisReport/01_课题说明_ProjectBrief/02_数据来源总览_DATA_SOURCE.md`  
与技能 `E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/文档_docs/成分靶点获取与交付规范_CompoundTargetSOP.md` §9 / §9.1。
