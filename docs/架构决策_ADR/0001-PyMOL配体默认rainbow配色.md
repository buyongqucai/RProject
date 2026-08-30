# 0001 — PyMOL 配体默认 rainbow 配色

- 日期：2026-08-30
- 状态：已接受（用户明确决策）

## 背景

code-review Standards 轴发现 `pymol_dock_viz_standard.py` 默认 `--ligand-spectrum rainbow`，与 VizStandards「禁止彩虹」存在张力。

## 决策

分子对接 3D 结构图中，**配体（PT）默认使用 rainbow（spectrum）配色**，仅当用户明确提出才更换。

## 理由

- 3D 配体的 rainbow 沿主链/原子序渐变，用于呈现空间走向，是结构生物学惯例（如 PyMOL/ChimeraX 默认），与 2D 统计图表中滥用彩虹色误导数值感知不同。
- 该条款已写入 `分子对接与虚拟筛选_MolecularDocking/技能说明` PyMOL 表，属「领域技能已写明条款」，按路由规则优先于 VizStandards 默认。

## 影响

- VizStandards 禁彩虹条款继续适用于所有 2D 统计图/热图。
- code-review 基线中对此的标记应被本 ADR 抑制。
