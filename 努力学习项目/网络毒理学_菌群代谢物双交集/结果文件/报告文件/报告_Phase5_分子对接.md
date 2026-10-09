# 报告：Phase 5 分子对接（核心对）

> 日期：2026-10-07 ｜ 脚本：`代码文件/12_分子对接.py`
> 定位：结合候选提示，不作疗效/毒性结论（项目规范 §2）。阈值 −20.9 kJ/mol（≈ −4.99 kcal/mol，计划 §4 Phase 5）。
> 产物：`数据/对接/对接全表.csv`（9 对 × 3 独立种子 = 27 次）、`对接汇总.csv`、`图片/总图/04_对接亲和力热图_DockingAffinityHeatmap.png/svg`

## 1. 方法

- 配对：取自 `核心代谢物靶点配对.csv` 真实存在的高优先级对（Tier A 代谢物 × 其三源共有靶点），共 9 对。
- 受体：RCSB 按 UniProt 精确检索，优先带合适有机共晶配体的结构（分辨率 ≤3.0 Å）；
  口袋中心 = 共晶配体重原子质心（连通分量聚类取最大簇，避免多拷贝平均偏移）；受体刚性（obabel `-xr`）。
- 配体：面板 PubChem canonical SMILES（含丁酸负离子态），Open Babel gen3d + 加氢。
- 重复：3 个独立种子（1/7/42），exhaustiveness=8，22 Å 立方搜索盒。

## 2. 结果（mean ± SD，3 次独立重复）

| 代谢物 × 靶点 | PDB | 口袋 | mean kJ/mol | SD | 阈值 |
|---|---|---|---:|---:|---|
| Tryptophan × MMP9 | 1GKD | co-ligand STN | **−35.04** | 0.07 | PASS |
| Indole × CYP1A1 | 4I8V | co-ligand BHF | **−29.69** | 0.00 | PASS |
| Adenosine × ADA | 3IAR | co-ligand 3D1 | **−27.56** | 0.06 | PASS |
| Phenylalanine × PPARG | 1FM9 | co-ligand 9CR | **−26.34** | 0.04 | PASS |
| Arginine × NOS3 | 1K2S | co-ligand H4B | **−26.08** | 0.09 | PASS |
| Tryptophan × MPO | 1CXP | co-ligand NAG | **−22.37** | 0.63 | PASS |
| 4-Hydroxyphenylacetic acid × CA2 | 1A42 | co-ligand BZU | **−22.02** | 0.04 | PASS |
| Indole-3-acetic acid × ACHE | 13CO | co-ligand NAG | −19.79 | 0.07 | no |
| Butyrate × PPARG | 1FM9 | co-ligand 9CR | −16.46 | 0.06 | no |

**9 对全部完成（27/27 次运行），7 对达到 −20.9 kJ/mol 阈值；3 次重复间 SD ≤0.63 kJ/mol，复现性良好。**

## 3. 结论边界

- 支持：色氨酸- MMP9/MPO、吲哚- CYP1A1、腺苷- ADA、苯丙氨酸- PPARG、精氨酸- NOS3 等为**结合候选**，
  可作为「复方-代谢物共同靶点轴」的结构层提示；与干预代谢物预测表（Tier A）互为印证。
- **如实报告的阴性项**：顶号代谢物丁酸 × PPARG 仅 −16.46 kJ/mol（未达阈值）；IAA × ACHE 差临界（−19.79）。
  丁酸为短链脂肪酸负离子、PPARG LBD 口袋对 SCFA 亲和力本就偏弱——只写「本对接设置下未达阈值」，
  不外推为「丁酸不起作用」（其 Tier A 地位由 14 个共有靶点 + 43 条实证边支撑，对接非其主证据）。
- 人 iNOS（P35212）无 PDB 结构，精氨酸 × NOS2 对以 NOS3（同家族、配对表中同样存在）替代，已在方法中注明。

## 4. 与既有报告衔接

- 对接对的代谢物均来自 `报告_复方干预代谢物预测.md` Tier A；
- 图件补齐计划 §5 Fig7；Fig1/2/3 见 `图片/总图/`。
