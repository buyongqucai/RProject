---
name: bioinfo-new-skill
description: >-
  Scaffold or audit a BioinformaticsSkills domain skill against the SkillParadigm
  checklist. Use when creating a new 技能, 新建技能, skill scaffold, or when the
  user asks to follow the default skill paradigm / 技能范式.
---

# bioinfo-new-skill（新建/审计领域技能）

## 必读

1. [`docs/agents/技能范式清单_SkillParadigm.md`](../../../docs/agents/技能范式清单_SkillParadigm.md)
2. [`docs/agents/工单工作流_WorkOrder.md`](../../../docs/agents/工单工作流_WorkOrder.md)
3. 金标入口示例：`生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一交付规范_DeliveryStandards/技能说明_*.md`

## 新建步骤

1. **工单**：在 `.scratch/` 建功能目录或认领已有 `待Agent处理` 单；验收勾选范式 A–D。
2. **骨架**：按范式 §F 建目录；技能说明含 YAML + 八节（不适用则写明）。
3. **披露**：细则进 `文档_docs/`；入口只留指针。
4. **样例**：有跑通需求则 `DATA_SOURCE.md` + provenance；出图叠加 Viz + Delivery。
5. **挂钩**：更新 `intent-skill-router` catalog（`refresh_catalog.py`）；新术语写 `CONTEXT.md`。
6. **完成判据**：范式 A–D 全勾；若声明可跑，则 `STATUS.txt` 存在且非假 REAL。

## 逐文件审计步骤

1. 打开或生成 `.scratch/技能逐文件审计_SkillFileAudit/清单_checklist/<技能文件夹>.md`。
2. 按范式 §E 对 **技能说明 / 文档_docs / 脚本 / 样例** 逐文件判定。
3. `小修` 当场改并回写清单；`大修` 开子工单（`issues/`）。
4. 批次工单全部清单填完 → 标 `已完成`，更新 `BOARD.md`。

## 禁止

- 未开/未认领工单就批量改 70 个技能
- 在技能说明里粘贴 SOP 长文（双源）
- 把 TOY/BLOCKED 写成真实分析结论
