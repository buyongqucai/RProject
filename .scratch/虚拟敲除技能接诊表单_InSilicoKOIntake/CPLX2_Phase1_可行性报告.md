# CPLX2 Phase1 可行性报告（2026-09-29）

> 表单 A+B 已确认。本报告**只评估公共数据**，不跑 scTenifoldKnk，不编造亚群检出率数字（未下载矩阵前不得填假 %).

## 1. 理想条件对照

| 需求（确认表） | Phase1 结论 |
|----------------|-------------|
| 小鼠 | 有 |
| 组织 = **TG** | 有多个 sc/sn；**无**「TG + 严格 TN 模型 + sc」同集 |
| **TN/IoN-CCI/CION vs 正常** + **单细胞** | **TG 上未找到**；Sp5C 上有 CION vs Sham（GSE322600） |
| 感觉神经元亚群 | TG atlas / 正常 TG sc 具备 |
| 可跑 scTenifoldKnk（需 sc/sn counts） | bulk **不可**直接作引擎输入 |

**总判：** 理想集「小鼠 × TG × TN vs 正常 × sc/sn」在公开检索中 **不适用 / 缺失**。须选 fallback（下节）。

## 2. 候选登记表

| 登录号 | 物种 | 组织 | 设计 | 技术 | 对 VKO | 评级 |
|--------|------|------|------|------|--------|------|
| **GSE316925** | 小鼠 | **TG** | IoN-CCI 多时点 vs sham（±Trpm3 KO） | **bulk** RNA-seq | 贴 TN 模型，**不能**跑 scTenifoldKnk；可作背景/日后 bulk 验证 | 背景 only |
| **GSE322600** | 小鼠 | **Sp5C**（非 TG） | CION vs Sham；PBN-projecting 单神经元 | Smart-seq3 | 有疾病对比；组织=中枢；细胞宇宙窄（投射亚群） | Fallback **F2** |
| **GSE186421** | 小鼠 | TG | 对照 vs **口面炎症痛**（CFA） | scRNA；设计约 2 库 | 有「两组」但 **≠ TN**；细胞/重复有限 | Fallback **F1b**（弱） |
| **GSE197289** | 小鼠（+人） | TG | 健康/图谱；偏头痛遗传与头痛模型解读用 atlas | **snRNA**；小鼠约 6 万核、多生物学重复 | 亚群成熟（tg.painseq.com）；**无 TN vs 正常 sc 对比**；适合亚群定位 + 基底态 VKO | Fallback **F1**（推荐保底主分析） |
| **GSE213105** | 小鼠 | TG | 正常 TG | scRNA；~2.3 万细胞；6 神经元亚群 | 同 F1；全细胞类型清楚 | Fallback **F1** 备选/对照 |
| GSE240432 | 小鼠 | TG | 非神经元 | scRNA | **排除**主分析 | 排除 |

文献旁证：`Cplx2` 在小鼠感觉神经元（含 TG 富集组分）转录组中作为突触相关基因出现（如 Scientific Reports 性差研究），支持「神经元可测」方向；**各亚群检出率仍须下载后实测**。

## 3. 推荐路径（请你勾一项作为 C.fallback_choice / dataset 策略）

| 选项 | 做法 | 优点 | 代价 |
|------|------|------|------|
| **F1**（建议默认） | 主分析：**GSE197289 小鼠 TG snRNA**（可加 GSE213105 敏感性）；按感觉亚群测 `Cplx2` → 表达够则亚群 VKO | 贴截图「小鼠 TG + 亚群」；细胞多 | **无 TN vs 正常**；解释为基底态预测 |
| **F1+F1b** | F1 + 在 GSE186421 炎症库上尝试（若神经元细胞数够） | 看状态依赖 | 炎症≠TN；样本少、网络易不稳 |
| **F2** | 主分析改 **GSE322600 Sp5C CION vs Sham** | 真有模型对比 | **不是 TG**；与外周 IF/CGRP 叙事要改写 |
| **F3** | F1 做 TG 亚群 VKO **且** F2 做 Sp5C 补充（两套报告章节） | 外周+中枢 | 工作量约翻倍 |

**GSE316925 bulk** 建议：不进 scTenifoldKnk；若你要「TN TG 转录有无 Cplx2 变动」可另开 bulk 检查（本期 VKO_only 可不做）。

## 4. C 类字段（待你二次确认）

请回复例如：`Phase1选 F1；主集 GSE197289` 或 `F3` 等。

| 字段 | 待填 |
|------|------|
| `dataset_id` | 例如 `GSE197289`（小鼠侧）± `GSE213105` / `GSE322600` |
| `dataset_fit` | 理想集 = **否**；所选 fallback = … |
| `fallback_choice` | F1 / F1+F1b / F2 / F3 |
| `subtypes_to_ko` | **下载并分群后**根据 `Cplx2` 检出率与细胞数再定（含 Calca+ / Nefh+） |
| `n_cells_per_subtype` / `gene_detection_rate` | 实测后填；本报告不编造 |

## 5. 下一步闸门

1. 你勾选 F1/F2/F3（及主 GSE）  
2. 再下载对应矩阵 → 出 Phase1 图 02–03（表达/检出率）  
3. 你确认 `subtypes_to_ko`  
4. 才 Phase2 scTenifoldKnk  

**本期仍未正式敲除。**
