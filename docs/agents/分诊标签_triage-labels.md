# 分诊标签（Triage Labels）

`triage` 技能使用以下**中文标签**，直接套用，**不要**创建英文重复标签。

| 角色（role） | 默认英文 | 本仓库中文标签 | 含义 |
|--------------|----------|----------------|------|
| needs-triage | `needs-triage` | `待分诊` | 新议题，尚未评估 |
| needs-info | `needs-info` | `待补充信息` | 信息不足，需提出者补充 |
| ready-for-agent | `ready-for-agent` | `待Agent处理` | 已明确，可交给 agent 实现 |
| ready-for-human | `ready-for-human` | `待人工处理` | 需要人工判断或操作 |
| wontfix | `wontfix` | `不予修复` | 确认不处理，附原因 |
| done | `done` | `已完成` | 验收勾完；可归档 |

## 使用方式

- 本地 markdown 跟踪下，标签写在议题 / 工单头部，如：`标签: 待分诊`。
- 状态流转：`待分诊` →（信息不足 → `待补充信息`）→ `待Agent处理` / `待人工处理` / `不予修复`；做完 → `已完成`。
