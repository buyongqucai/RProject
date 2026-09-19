# 工单化与技能范式

**标签:** 已完成（脚手架落地；审计执行见姊妹议题）
**类别:** enhancement
**日期:** 2026-09-06

## Problem

仓库已有 mattpocock 式 tracker 文档，但与 `to-tickets` 的 `issues/NN-*.md` 不完全对齐；70 个领域技能缺少统一「新建默认范式」与逐文件审计工单。

## Solution

- Tracker / 工单工作流 / 范式清单写入 `docs/agents/`
- AGENTS + alwaysApply rule + `.cursor/skills/bioinfo-new-skill`
- 逐文件审计另立 `.scratch/技能逐文件审计_SkillFileAudit/`

## Acceptance（本父议题）

- [x] `问题跟踪` 对齐 `issues/` 模板
- [x] `工单工作流` + `技能范式清单` SSOT
- [x] AGENTS / 分诊「已完成」/ cursor rule / bioinfo-new-skill
- [x] 本目录 `issues/` 记录落地单

## 姊妹议题

技能逐文件审计 → `.scratch/技能逐文件审计_SkillFileAudit/`
