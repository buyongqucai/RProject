# RProject — Agent 说明

动手前先读 `CONTEXT.md`（领域词汇）与 `docs/项目规范_ProjectStandards.md`（医学/生物学/学术规范与存放约定）。

## Agent skills

### Issue tracker（问题跟踪）

Issues 以本地 markdown 文件跟踪，存放于 `.scratch/<功能名>/`（功能名可用中文）。详见 `docs/agents/问题跟踪_issue-tracker.md`。

### Triage labels（分诊标签）

使用中文标签：待分诊 / 待补充信息 / 待Agent处理 / 待人工处理 / 不予修复。详见 `docs/agents/分诊标签_triage-labels.md`。

### Domain docs（领域文档）

单上下文布局：根目录 `CONTEXT.md` + `docs/架构决策_ADR/`。详见 `docs/agents/领域文档_domain.md`。
