---
name: bioinfo-network-toxicology
description: >-
  网络毒理学 / NetworkToxicology：化学或菌群代谢物–靶点–疾病/表型–通路网络。
  库档位见可抓取登记（PubChem/ChEMBL/Open Targets 可 API；CTD/gutMGene 手工或官方包）。
  触发：网络毒理, network toxicology, CTD, gutMGene, 化学基因互作, AOP, ToxCast。
---

# 网络毒理学 / NetworkToxicology

> **库与能否抓取（SSOT）：** [`数据库可抓取登记_FetchRegistry.md`](文档_docs/数据库可抓取登记_FetchRegistry.md)  
> **步骤摘要：** [`流水线摘要_Pipeline.md`](文档_docs/流水线摘要_Pipeline.md)

暴露物（化学物、毒素、菌群代谢物）对宿主靶点与表型的**候选网络**。结论写「提示/候选」，不写确定性毒性或治疗疗效。

## 1. 数据来源

策展边、预测靶点、疾病基因分表存放。优先组合：PubChem 身份 + CTD 本地包 +（可选）gutMGene / STP + Open Targets 或疾病库手工表。细则与 AUTO/KEY/MANUAL 档只维护在可抓取登记。

## 2. 数据规范

- 每条边带来源库、版本或下载日期、`evidence=curated|predicted`
- 无导出则该步 `BLOCKED_EXTERNAL`；禁止编造化学–基因对
- CTD 批量查询带人机验证：**不写绕过脚本**；用用户已接受许可的月度文件
- `DATA_SOURCE.md` 写 `data_provenance`

## 3. 何时选用

- 网络毒理学、化学/环境暴露–基因–疾病、肠–器官轴代谢物毒理/药理网络  
- 与网药共用 STP、疾病库、KEGG、STRING、对接时，**主技能仍是本技能**（暴露物不是中药成分瀑布）

不适用：中药复方成分瀑布 → `网络药理学_NetworkPharmacology`。仅 ADMET 打分、无网络 → `类药性与QSAR_ADMET-QSAR`。仅对接 → 分子对接技能。

## 4. 数据处理方法

身份解析 → 策展互作（CTD 等）→ 可选预测靶点 → 与疾病/毒性基因交集 → PPI/通路/AOP → 可选对接。逐步见流水线摘要。

## 5. R 包与软件栈

| 步骤 | 工具 | 备注 |
|------|------|------|
| 身份 | PubChem PUG-REST | AUTO_API；遇 503 重试 |
| 活性/疾病 | ChEMBL REST、Open Targets GraphQL | AUTO_API |
| CTD | 本地 `CTD_*.csv` | 用户下载后读入 |
| 富集/PPI/出图 | clusterProfiler、STRING、VizStandards | 与网药相同交付约束 |
| 对接 | 分子对接技能 | 不在本技能内改 FROZEN 对接 |

脚本目录现为说明占位；取数脚本在登记档位稳定后再加，不先写爬虫。

## 6. 数据可视化

出图叠加 VizStandards + DeliveryStandards。图面 English。网络图在领域样式定稿前沿用期刊通用网络（节点来源分色），**不**复用网药 HCTP 的 FROZEN 配色冒充毒理图。

## 7. 数据结果解读

策展关联、预测靶点、对接亲和力分开写。CTD 推断边与实验边分开。菌群库关联不是 16S/代谢组实测。

## 8. 能否结合其它生信

下游：蛋白结构 → 对接 → MD。疾病基因可复用网药手工库流程。MR 仅在有工具变量时另走孟德尔随机化技能。

## 样例验证

样例目录已建，**尚未跑通分析**（`data_provenance: BLOCKED`）。有 CTD 本地包或 gutMGene 导出表后再开 Pilot。
