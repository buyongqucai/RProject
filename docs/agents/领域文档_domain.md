# 领域文档（Domain Docs）— 单上下文

本仓库为**单上下文（single-context）**布局，无 monorepo 多包结构。

## 布局

```text
CONTEXT.md                 # 仓库根：领域词汇、核心概念、边界（SSOT，唯一）
docs/
  架构决策_ADR/            # Architecture Decision Records
    NNNN-标题.md           # 如 0001-热图标签统一黑色.md
```

## Agent 消费规则

1. **动手前先读** `CONTEXT.md`：理解领域词汇与模块边界，避免自造术语。
2. **涉及架构/规范决策时**：先查 `docs/架构决策_ADR/` 是否已有相关 ADR；新决策按序号新建 ADR，正文用中文，保留英文专业术语对照。
3. **决策落地即更新**：讨论中确定的领域术语/约定，当场写回 `CONTEXT.md` 或对应 ADR，不停留在对话里。
4. `CONTEXT.md` 不存在时，可在首次领域建模（domain-modeling）会话中创建。
