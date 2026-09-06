# PROSPERO 方案提纲 — 胰腺癌新辅助 vs 直接手术

> **状态：** 草稿提纲（Pilot 配套）；正式注册前须用户确认 PICO 终稿。  
> **课题：** Neoadjuvant therapy versus upfront surgery for resectable and borderline resectable pancreatic cancer.

## 1. Review title（英文草案）

Neoadjuvant therapy versus upfront surgery for resectable and borderline resectable pancreatic ductal adenocarcinoma: a systematic review and meta-analysis of randomised controlled trials

## 2. PICO（待用户锁定处用【待确认】标出）

| 要素 | 草案 | 待确认 |
|------|------|--------|
| Population | Adults with **resectable and/or borderline resectable** PDAC | BRPC 定义：【NCCN / IAP / 原文作者定义】 |
| Intervention | Neoadjuvant chemotherapy ± chemoradiotherapy pathway | Broad vs Narrow：【待确认】 |
| Comparator | Upfront / immediate surgery (± adjuvant chemotherapy) | 须提取对照组辅助比例 |
| Primary outcome | 【DFS 或 PFS 二选一】 | Pilot 暂用 **OS** 验证工具链 |
| Secondary | OS（若非 Primary）、R0、pCR、手术并发症、90 天死亡率、DFS/PFS（另一终点） | 清单【待确认】 |

## 3. 纳排标准

**纳入**
- RCT（主分析）
- 直接比较 neoadjuvant pathway vs upfront surgery
- 报告 OS 和/或 DFS/PFS/RFS 的 HR 及 95%CI，或可换算的生存数据
- 全文可获取（英文【±中文：待确认】）

**排除**
- 单臂、非随机比较（主分析排除；敏感性分析是否纳入【待确认】）
- 转移性或不可切除且无意向手术路径
- 仅会议摘要且无可用 HR
- 重复发表：保留信息最全的报告

## 4. 检索（框架）

| 库 | 用途 |
|----|------|
| PubMed/MEDLINE | 必做 |
| Embase | 【有机构权限则做】 |
| Cochrane CENTRAL | 必做 |
| Web of Science | 建议 |
| ClinicalTrials.gov | 灰色文献 / 在研 |

**概念块：** pancreatic cancer / PDAC + neoadjuvant / preoperative + resectable / borderline + surgery / upfront + randomised  

检索日期、完整检索式写入补充材料 S1。

## 5. 筛选与提取

- 双人独立筛题录/全文；分歧第三方仲裁（【第二人：待确认】）
- 提取表字段对齐 Pilot `03_提取表_Extraction_pilot.csv`，并增加：RoB 2 域、辅助化疗完成率、R0、pCR

## 6. 偏倚与证据质量

- RCT：**RoB 2**（结局导向：OS / DFS）
- 观察性敏感性（若启用）：**ROBINS-I**
- 结局证据：**GRADE** → Summary of Findings 表

## 7. 综合方法

- 效应量：logHR + SE；模型：**REML 随机效应**（`metafor`）
- 异质性：I²、τ²、Q；讨论临床异质性（BRPC vs resectable、含放疗与否、方案）
- 预设亚组：仅 BRPC；含 CRT vs 纯化疗；地区（东亚 vs 欧美）
- 敏感性：留一法；排除高 RoB；排除可行性/II 期短随访研究
- 发表偏倚：纳入 Meta 研究数 **≥10** 时做漏斗图 / Egger；否则正文说明不做

## 8. 软件

R（`metafor`）、VizStandards 出图、DeliveryStandards 审计；可选 RevMan 对照。

## 9. 利益冲突与资金

【注册时填写】

## 10. 与 Pilot 的关系

Pilot（`02_医学SRMA样例_MedicalSrmaPilot`）仅验证工具链；正式注册后按本提纲重跑全库检索，**不得**把 Pilot 三研究合并结果直接写入投稿结论。
