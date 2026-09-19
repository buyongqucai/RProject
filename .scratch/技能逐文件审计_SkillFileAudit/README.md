# 技能逐文件审计（70）

**标签:** 已完成
**类别:** enhancement
**完成日期:** 2026-09-06
**粒度:** 一技能一工单

## Goal

对每个领域技能按 [`技能范式清单_SkillParadigm.md`](../../docs/agents/技能范式清单_SkillParadigm.md) **逐文件**勾选；小修当场改。

## 结果摘要

| 项 | 值 |
|----|-----|
| 工单 | 70 / 70 已完成 |
| 清单 | `清单_checklist/*.md` 均已填总评 |
| 本轮小修 | 网药入口瘦身；MultiOmics 去 BOM；DEG-UMAP 附录 → `文档_docs/生产流水线SOP_*` |
| 预检脚本 | `scripts/audit_all_skills.py`（可复跑） |

## 方法（以后复审）

1. `python .scratch/技能逐文件审计_SkillFileAudit/scripts/gen_checklists.py`
2. `python .scratch/技能逐文件审计_SkillFileAudit/scripts/audit_all_skills.py`
3. 对报告中「小修/大修」人工披露或补 DATA_SOURCE，再复跑关单

## Out of scope（本轮未做）

- 未重跑全部样例计算
- 未解冻 FROZEN 视觉
