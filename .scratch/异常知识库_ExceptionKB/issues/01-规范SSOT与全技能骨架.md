# 01 规范 SSOT 与全技能骨架

- 标签：已完成
- Blocked by：无（frontier）

## 内容
1. `docs/agents/异常知识库规范_ExceptionKb.md`：目录约定、案例模板（症状/判定/补救/何时放弃/复盘）、写入纪律、工单联动。
2. 骨架批铺：`scaffold_exception_kb.py` → 70 个技能新建 `异常知识库_ExceptionKB/README.md` + `案例_Cases/`（幂等、不覆盖）。
3. `技能范式清单_SkillParadigm.md` 增 A7 行 + F 骨架行（只留指针，规则不双写）。
4. MD/对接 `技能说明_*.md` 各加一行指针。

## 验收
- [x] 每个含 `技能说明_*.md` 的技能都有 `异常知识库_ExceptionKB/README.md`
- [x] 规则只在 SSOT 一处；清单与技能说明仅指针
