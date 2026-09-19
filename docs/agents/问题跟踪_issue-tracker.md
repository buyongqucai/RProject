# 问题跟踪（Issue Tracker）— 本地 markdown 工单

本仓库 **不**用 GitHub Issues 作日常工单。`to-tickets` / `triage` / `to-spec` / `implement` 读写本文件描述的目录，**不要**默认调用 `gh issue`。

外部 PR 不作请求入口（个人项目）。

## 目录结构（与 to-tickets 对齐）

```text
.scratch/
  <功能名>/                          # 中文或中英均可，如「技能逐文件审计」
    README.md                        # 父议题：背景、目标、验收、看板摘要
    BOARD.md                         # 可选：当前 frontier 一览
    issues/
      01-<slug>.md                   # 单张工单（依赖序编号）
      02-<slug>.md
    清单_checklist/                  # 可选：逐文件审计表等
    _归档/                           # 完成后可移入 .scratch/_归档/<功能名>/
```

旧议题若只有 `README.md` + `01-子任务.md`（无 `issues/`），仍有效；**新工单一律进 `issues/`**。

## 单张工单模板

```markdown
# <NN>: <标题>

**类别:** enhancement | bug
**标签:** 待Agent处理
**Blocked by:** None（可立即开始） | 01-xxx, 02-yyy

**What to build:** 从用户视角可验证的端到端结果（非分层实现清单）。

- [ ] 验收标准 1
- [ ] 验收标准 2

## Notes
（可选：分诊纪要、阻塞原因）
```

## 工作流（工单化）

| 口令 / 技能 | 作用 |
|-------------|------|
| `/to-spec` 或「写成规格」 | 对话 → 规格，写入 `.scratch/<功能>/README.md` 或 `issues/00-spec.md` |
| `/to-tickets` 或「拆成工单」 | 规格/对话 → `issues/NN-*.md`，声明 Blocked by |
| `/triage` 或「分诊」 | 标签状态机；`待Agent处理` 须有可执行验收标准 |
| `/implement` 或「做下一张」 | 认领 **frontier**（Blocked by 皆已完成）的一张 `待Agent处理` |
| 「看板」 | 读 `BOARD.md` 或扫 `issues/` 头部标签 |

状态标签（中文）：见 [`分诊标签_triage-labels.md`](分诊标签_triage-labels.md)。

## Frontier 规则

- 只做 **Blocked by 已全部完成** 且标签为 `待Agent处理` 的工单。
- 完成后：勾验收、标签改为 `已完成`、写完成日期；更新 `BOARD.md`。
- 宽重构用 expand–contract，勿硬塞进一张垂直切片。

## 与技能范式

新建/审计领域技能时，工单验收必须引用 [`技能范式清单_SkillParadigm.md`](技能范式清单_SkillParadigm.md) 的勾选项（逐文件）。
