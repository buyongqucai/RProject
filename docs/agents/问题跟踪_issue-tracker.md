# 问题跟踪（Issue Tracker）— 本地 markdown

本仓库的 issue **不**放在 GitHub Issues，而是以本地 markdown 文件跟踪。`to-tickets`、`triage`、`to-spec` 等技能读写本文件描述的目录，**不要**调用 `gh issue`。

## 位置与结构

```text
.scratch/                      # 约定目录名（保持英文，工具链约定）
  <功能名>/                    # 每个功能/议题一个目录，可用中文命名，如「对接热图优化」
    README.md                  # 议题描述：背景、目标、验收标准
    01-子任务.md               # 可选：拆分子任务，前缀数字排序
    02-子任务.md
```

## 工作流约定

1. **新建议题**：在 `.scratch/` 下建 `<功能名>/README.md`，写清背景、目标、验收标准。
2. **分诊**：`triage` 技能按 `docs/agents/分诊标签_triage-labels.md` 的中文标签在 README 头部标注状态（如 `标签: 待分诊`）。
3. **实施**：标签为 `待Agent处理` 的议题可由 agent 直接认领实现。
4. **归档**：议题完成后在 README 标记 `已完成` 并记录完成日期；定期可移入 `.scratch/_归档/`。

## 外部 PR

本仓库不接受外部 PR 作为请求入口（个人项目）。如未来需要，将 PR 纳入分诊队列时再修改本文件。
