# 工单工作流（Work Order）

> 工程技能来源：`E:\编程技能\mattpocock-skills`（已装到 `~/.agents/skills/` 的同名技能）。  
> 本仓库 tracker = 本地 `.scratch/`（见 [`问题跟踪_issue-tracker.md`](问题跟踪_issue-tracker.md)）。

## 何时用哪张技能

| 你说的话 | 调用 | 产物 |
|----------|------|------|
| 把讨论写成规格 | `to-spec` | 规格正文 + 标签 `待Agent处理` |
| 拆成可执行工单 | `to-tickets` | `.scratch/<功能>/issues/NN-*.md` |
| 这批议题怎么排 | `triage` | 中文标签 + agent brief |
| 做下一张 / 认领 frontier | `implement` | 改代码/文档至验收勾完 |
| 写/改技能说明、AGENTS | `writing-for-agents` | 短入口 + SSOT 指针 |
| 术语/边界不清 | `domain-modeling` / `grilling` | 回写 `CONTEXT.md` / ADR |
| 新建生信技能目录 | 项目技能 `bioinfo-new-skill` + 范式清单 | 合规骨架 |

## 默认节奏（个人仓）

1. **进线**：新想法 → `.scratch/<功能>/README.md`（父议题，`标签: 待分诊`）。
2. **分诊**：信息够 → `待Agent处理`；不够 → `待补充信息`；需你拍板 → `待人工处理`。
3. **拆单**：大议题 → `to-tickets`；每单一个 context 能做完。
4. **执行**：只碰 frontier；做完标 `已完成`。
5. **进化**：你确认的规则写入技能 `文档_docs/` SSOT（`项目规范` §0），不写第二份。

## Agent 短声明

开工时一句话：`工单：.scratch/<功能>/issues/NN-…；范式：SkillParadigm`。
