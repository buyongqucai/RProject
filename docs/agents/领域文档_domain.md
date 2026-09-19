# 领域文档（Domain Docs）— 单上下文

本仓库为**单上下文（single-context）**布局。仓内可有课题沙箱目录，但不另建 `CONTEXT-MAP.md`（见 ADR 0003）。

## 布局

```text
CONTEXT.md                 # 词汇 + 边界（SSOT）
docs/
  架构决策_ADR/            # NNNN-标题.md
  项目规范_ProjectStandards.md   # 含 §0 反馈进化闭环
```

## Agent 消费规则

1. **动手前先读** `CONTEXT.md`。  
2. **架构/边界决策**先查 `docs/架构决策_ADR/`；新决策按序号新建。  
3. **你确认的术语/边界当场写回** `CONTEXT.md` 或 ADR，不停留在对话。  
4. **反馈进化：** 满意规则写入技能 `文档_docs/` 的 SOP/FROZEN（单点）；技能说明只改指针。流程见 `项目规范` §0。  
5. `CONTEXT.md` 无实现细节（不是 spec）。
