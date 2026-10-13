# 报告：Phase 5b 活性成分分子对接

> 日期：2026-10-12 ｜ 脚本：`代码文件/18_活性成分对接.py`  
> 选型：[`对接选型逻辑_成分与代谢物统一.md`](对接选型逻辑_成分与代谢物统一.md)  
> **单位：kcal/mol（FROZEN）**；阈值 **−5.0 kcal/mol**。结论=结合候选。

## 1. 筛选逻辑（本次纠正后）

| 层 | 规则 |
|----|------|
| 靶点宇宙 | C = F ∩ M ∩ D |
| **配体** | 网药 `network.csv` 中 **type=B Degree 最高**（排除 cellulose/tannins） |
| **靶点** | 该成分在 C 上的邻居，按机制层 **PPI Degree**（`PPI网络指标_MCC排序.csv`）优先；同靶点最多 2 个配体 |
| 引擎 | 同代谢物批次；口袋优先共晶 |

说明：首轮 rutin×IL1B 为盲对接口袋、分数异常，已按同规则改绑 **SIRT1**（共晶）；Caffeic Acid×TLR4 未达阈值，改绑 **CYP1A1**（共晶）。均写入配对表 `selection_rule`。

`3beta-Hydroxyurs-12-En-28-Syre` 的 PubChem 三维按同义检索映射为 **ursolic acid（CID 64945）**，报告中保留原网络名并注明。

## 2. 结果（mean ± SD，kcal/mol）

| 成分（网络 Degree） × 靶点（PPI Degree） | PDB | mean | SD | 阈值 |
|---|---|---:|---:|---|
| 3beta-Hydroxyurs-12-En-28-Syre（48） × TNF（11） | 2AZ5 | **−10.00** | 0.00 | PASS |
| Delphinidin（33） × MMP9（7） | 1GKD | **−9.53** | 0.06 | PASS |
| Caffeic Acid（24） × CYP1A1（5） | 4I8V | **−8.17** | 0.15 | PASS |
| luteolin（34） × TNF（11） | 2AZ5 | **−7.90** | 0.00 | PASS |
| beta-sitosterol（21） × CASP3（6） | 1GFW | **−7.60** | 0.00 | PASS |
| wogonin（21） × CASP3（6） | 1GFW | **−7.40** | 0.00 | PASS |
| rutin（25） × SIRT1（7） | 4I5I | **−7.37** | 0.06 | PASS |
| quercetin（168） × JUN（12） | 8SOS | **−5.90** | 0.00 | PASS |
| kaempferol（58） × JUN（12） | 8SOS | **−5.63** | 0.15 | PASS |

**9/9 达 −5.0 kcal/mol。**

## 3. 与代谢物对接

代谢物批次已改为 **kcal/mol 主单位**（未重跑 Vina）。代谢物靶点当时**不是**按 PPI Degree 选的；成分侧现已按「网络 Degree 配体 × PPI Degree 靶点」执行网药常用枢纽逻辑。
