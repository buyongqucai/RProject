---
name: bioinfo-molecular-dynamics
description: >-
  分子动力学模拟 / MolecularDynamics：对接后稳定性/结合自由能；山水 M17；勿假装纯 R 跑 MD。工具：bio3d, ggplot2, GROMACS, Amber。
  触发：分子动力学, GROMACS, MD, RMSD。交付范式 FROZEN（2026-09-03）。
---

# 分子动力学模拟 / MolecularDynamics

> **出图与交付 SSOT：** [`文档_docs/出图与交付约束_MdFigureStandards.md`](文档_docs/出图与交付约束_MdFigureStandards.md) — **`FROZEN`（2026-09-03）**。改图册序/Origin recipe/报告结构前须你说「解冻」。  
> **进化：** 计算步骤回写 [`复合物MD流水线_GromacsSop.md`](文档_docs/复合物MD流水线_GromacsSop.md)；出图规则回写 FROZEN；本入口不复述长 SOP。  
> 登记：[`已跑通范式登记_FrozenParadigms.md`](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/已跑通范式登记_FrozenParadigms.md)。

## 1. 数据来源

对接复合物或已知复合物

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 对接后稳定性/结合自由能；山水 M17；勿假装纯 R 跑 MD
- 山水用途层标签：药物-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

溶剂化→最小化→平衡→生产→RMSD/RMSF/氢键/MM-PBSA

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `bio3d` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `GROMACS` | CLI 工具 | 非 R |
| 上游/主分析 | `Amber` | CLI 工具 | 非 R |
| 出图 | Origin（`origin出图_plotMdOrigin.py` COM/LabTalk） | DPI≥600 PNG+SVG | 分析曲线/FEL/能量柱必须 Origin；R 只备 CSV |

## 6. 数据可视化

RMSD/RMSF 曲线；**DPI≥600；SVG+PNG；图面 English；防遮挡**。

**对齐高分期刊范式：** 遵循 [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)；近邻折线/箱线。**本技能出图与交付已 FROZEN**（见 [`出图与交付约束_MdFigureStandards.md`](文档_docs/出图与交付约束_MdFigureStandards.md)）。网药视觉 **FROZEN**，勿改。

## 7. 数据结果解读

力场、时长和有无熵项决定能说什么。样例 HTML 必须把 **0.20 ns / 21 帧** 写在页首：可陈述本窗口内 RMSD/Rg/COM/MM-GBSA 数字，**禁止**写成发表级 ΔG、长期稳定结合或 FEL 能垒。

报告金标：`01_样例_sample/代码文件/结果文件/报告文件/样例报告_SampleReport_v1.html`  
生成器：同目录 `代码文件/03_写样例报告_writeSampleReport.R`（只写 HTML，不重跑 GROMACS/Origin）  
版式范式：[统一交付规范 样例报告范式](../../00_基础_Foundation/统一交付规范_DeliveryStandards/文档_docs/样例报告范式_SampleReportParadigm.md)

## 8. 能否结合其它生信

分子对接、蛋白结构；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 蛋白-配体复合物 MD 流水线

**执行 SOP（强制）：** [`文档_docs/复合物MD流水线_GromacsSop.md`](文档_docs/复合物MD流水线_GromacsSop.md)（原技能说明 §9–§10：一键调用、拓扑、平衡、分析、环境与踩坑）。  
**出图/交付 FROZEN：** [`文档_docs/出图与交付约束_MdFigureStandards.md`](文档_docs/出图与交付约束_MdFigureStandards.md)。

摘要：`运行复合物MD_runComplexMd.sh` + mdp 模板；分析图走 Origin（见 FROZEN）；样例整理 `整理样例目录_layoutMdSample.py`。

```bash
wsl -d Ubuntu-24.04 -- bash -c "cd <工作目录> && \
  LIGAND_RES=JZ4 NET_CHARGE=0 NS=1 \
  bash 运行复合物MD_runComplexMd.sh . protein.pdb jz4_h.mol2"
```

## 样例验证

样例：`01_样例_sample/`（**范式 FROZEN 2026-09-03**；`STATUS=REAL`，`data_provenance=REAL`，2026-08-30 E2E）。入口 `代码文件/01_run_sample.R` → 检查 `工作文件_MdWork/3HTB/08_轨迹分析_Analysis/` xvg 后调 `02_分析出图_plotMdAnalysis.R`；仅更新 HTML：`03_写样例报告_writeSampleReport.R`。MD 计算侧见上述 SOP。工作目录布局见 `工作文件_MdWork/3HTB/00_目录说明_Layout.md`。
