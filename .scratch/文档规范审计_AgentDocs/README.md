# 文档规范审计（writing-for-agents + domain-modeling）

- **状态：** 待Agent处理 → **本轮已落地修改**（2026-09-06）；待你抽查后可标「不予修复」外的关闭
- **完整缘由：** 见对话回复「为何这样改才能随反馈进化」

## 已落地

| ID | 动作 |
|----|------|
| A2 对接 | 技能说明去掉 §7.3/§7.4 长复述 → 指针 SOP |
| A2 MD | §9–§10 → `文档_docs/复合物MD流水线_GromacsSop.md` |
| A2 网药 | Cytoscape/手工导出 → `文档_docs/手工导出与Cytoscape可选_ManualOps.md` |
| A3 | 入口改为正向「定稿路径 / 解冻前」表述 |
| A4 | ProjectStandards §6 地图 + `.gitignore` 沙箱大图/scratch 图 |
| B2 | CONTEXT 补术语 + 反馈闭环 |
| B3 | ADR 0003 仓内沙箱 vs 桌面金标 |
| 进化 | ProjectStandards §0；FROZEN/AGENTS/domain 回写进化句 |

## 抽查清单（你）

- [ ] 对接：改满度只改 SOP §7.3，技能说明无第二份步骤
- [ ] MD：技能说明约 75 行，SOP 独立文件可搜到踩坑
- [ ] 努力学习 KEGG PNG 不会被 `git add -A` 误加（gitignore）
- [ ] 「解冻对接」口令语义仍清楚
