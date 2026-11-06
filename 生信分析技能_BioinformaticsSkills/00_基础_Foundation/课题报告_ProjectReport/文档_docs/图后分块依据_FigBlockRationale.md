# 图后分块依据（调研摘要）

> 供 `报告要求_ReportRequirements.md` §3.3 决策留痕。非第二份规则；规则以报告要求为准。

## 高分刊口径（主源）

| 来源 | 要点 |
|------|------|
| Springer Nature *Results* 写作指引 | Results **陈述发现、不解释含义**；Discussion 才回答 “what do results mean”；显著处给 p 等统计量 |
| Nature Formatting / Nature Methods | **图注**：短标题 + 各 panel 描述 + 符号 / n / 误差条；**不要**塞方法细节，**不要**在图注里做数据诠释 |
| Nature Methods 社论 *So you're writing a paper* | Results：观察与**直接**解读；细节方法在 Methods；Discussion 才做复杂诠释与 caveat |
| Clin Chem / IRDAM 顺序结果 | 每一结果小节四要素：**问题 → 实验概览 → 结果 → 对问题的回答**（方法细节仍在 Methods） |
| 生物医学 Results 写作综述 (PMC6635678) | Results 主句写发现；方法只用过渡从句带过，不复述协议 |

## 本课题报告如何映射

课题双报告 =「论文式 ≈ Results(+轻解读)」+「方法论 ≈ Methods(+读图图注)」的**扩写版**（要比期刊图注更详，但仍遵守分区）：

| 期刊角色 | 论文式每图块 | 方法论每图块 |
|----------|--------------|--------------|
| 本单元问题 + 设计一句话 | `setup` | —（总章 `#route` 已有；图内不重复长路线） |
| 发现（数字、显著与否） | `findings` | — |
| 直接解读（支持什么） | `takeaway` | — |
| 边界 / 不能证明 | `boundary` | 与 `pitfall` 互补 |
| 图注级读图（轴、符号、n） | — | `legend` |
| 可复现流程 | **禁止**在论文式展开 | `protocol` |
| 参数阈值 | — | `params` |
| QC 与误读 | — | `pitfall` |

因此：**论文式 4 块；方法论 4 块。** 旧版论文式把 `provenance` 放进每图，违背 Nature「方法细节进 Methods」；已撤出论文式强制块。
