# RProject — Agent 说明

动手前先读 `CONTEXT.md`（词汇/边界）与 `docs/项目规范_ProjectStandards.md`（含 **§0 反馈进化闭环**、医学规范与存放）。

未 @ 技能时：意图路由见 `.cursor/skills/intent-skill-router`（自动 Read 对应 `技能说明_*.md`）。

## Agent skills

### 工单化（强制默认）

日常开发/审计/修技能：**先工单再改文件**。流程见 `docs/agents/工单工作流_WorkOrder.md`。  
Tracker 目录约定见 `docs/agents/问题跟踪_issue-tracker.md`（`.scratch/<功能>/issues/NN-*.md`）。  
口令映射：`to-spec` / `to-tickets` / `triage` / `implement`（来自 `E:\编程技能` / `~/.agents/skills`）。  
只认领 **frontier**（Blocked by 已完成）且标签为 `待Agent处理` 的单。

### 技能范式（新建 / 审计）

逐文件勾选：`docs/agents/技能范式清单_SkillParadigm.md`。  
新建领域技能：项目技能 `.cursor/skills/bioinfo-new-skill`。  
批量审计工单：`.scratch/技能逐文件审计_SkillFileAudit/`。

### Issue tracker（问题跟踪）

Issues 以本地 markdown 跟踪，目录 `.scratch/<功能名>/`。详见 `docs/agents/问题跟踪_issue-tracker.md`。

### Triage labels（分诊标签）

中文标签：待分诊 / 待补充信息 / 待Agent处理 / 待人工处理 / 不予修复 / 已完成。详见 `docs/agents/分诊标签_triage-labels.md`。

### Domain docs（领域文档）

单上下文：`CONTEXT.md` + `docs/架构决策_ADR/`。详见 `docs/agents/领域文档_domain.md`。
