# 出图图册 — 虚拟敲除（SSOT）

> 改主线报告图序只改本文件。叠加 VizStandards（DPI≥600、图面 English、SVG+PNG）+ DeliveryStandards 命名。

## 来源

- 方法学 PDF / 论文图种：Osorio et al., *Patterns* 2022（scTenifoldKnk）— **采纳结构，禁止把论文截图当成本课题结果**
- 技能旧样例：`01_样例_sample/.../01_柱状图_KOrescue_Bar.svg` 等 — **regulon 备选附录**，非 scTenifoldKnk 主线

## 主线图序（scTenifoldKnk）

| 序 | 图种 | 对齐论文 | 数据阶段 | 备注 |
|----|------|----------|----------|------|
| 01 | Method overview | Fig 1 | 示意 | 自绘流程；若用论文示意图必须标注引用 |
| 02 | 亚群定位 + 靶基因表达 | — | Phase1 | UMAP/点图/小提琴 |
| 03 | 靶基因各亚群检出率柱图 | — | Phase1 | 决定 `subtypes_to_ko` |
| 04 | Top DR / perturbed genes 条图 | Fig 3 叙事 | Phase2 | **取代**旧 KOrescue 柱图主线角色 |
| 05 | 焦点通路富集（GSEA/ORA） | Fig 3 | Phase2 | 本课题不预先指定突触条目，基因集见筛选 SSOT |
| 06 | KO-centered 子网络 | 包网络图思路 | Phase2 | 显著 DR ∩ WT 网络边 |
| 07 | 跨亚群共享 vs 特异 | Fig 7 | Phase2 | 仅当 ≥2 亚群敲除 |

## 明确不纳入主线默认

| 论文图 | 原因 |
|--------|------|
| Fig 2 模拟模块 | 方法学验证，非课题数据 |
| Fig 5 DR 相关诊断 | 可选附录 |
| Fig 6 系统全基因敲除景观 | 本期单基因敲除不默认 |

## 方法示意与部位示意（SSOT）

| 图 | 规矩 |
|----|------|
| 方法示意 | **数形结合**（矩阵/张量/分布/阈值线），不画纯流程框。结构对齐对应论文：scTenifoldKnk = Osorio *Patterns* 2022 的 A/B/C 栏（A 建网流水→B 出边置零→C 流形对齐 + dRegulation + FDR）；GenKI = Yang *NAR* 2023 Fig.1 七步（WT scGRN → VGAE 二维高斯 → 边从/到置零 → KL → bagging hit 规则）。每栏给数值（nNet=10、K=3、HVG=3000、hit>95% 等）与几何对象。**琪乐无穷 `01_方法示意_scTenifoldKnkWorkflow.jpg` 是金标，禁止重绘**；其它课题照其结构自绘或共用同一文件。 |
| 部位示意 | 写实解剖（器官/皮肤层次/细胞类型 + 取材部位），不是抽象色块；页脚横幅「假设示意，非定位实验结果」。 |

自绘图脚本范例：婷婷 `12_统一方法示意_GeometryABC.py`（GenKI）、`13_部位示意_AcneSkin_AhrSites.py`。

## 备选线（regulon）

若表单 `method` 含 regulon：附录使用旧样例式 **rescued DEG 计数柱图**；正文声明非 scTenifoldKnk。
