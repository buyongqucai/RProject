# -*- coding: utf-8 -*-
"""铺 异常知识库_ExceptionKB 骨架到所有技能（幂等：已存在不覆盖）。"""
from pathlib import Path

ROOT = Path(r"E:\RProject\生信分析技能_BioinformaticsSkills")
SSOT = r"E:\RProject\docs\agents\异常知识库规范_ExceptionKb.md"
FOLDER = "异常知识库_ExceptionKB"

STUB = """# 异常知识库_ExceptionKB — {skill}

> 写法与案例模板：`{ssot}`（SSOT）。
> 本技能案例见 `案例_Cases/`；首个异常关闭后按模板录入。

## 案例索引

| 序号 | 症状 | 判定要点（一锤定音） | 补救路径 | 案例 |
|------|------|----------------------|----------|------|
| — | （待录入） | | | |
"""

created, skipped = [], []
for cat in sorted(ROOT.iterdir()):
    if not cat.is_dir() or cat.name.startswith((".", "0")) and "_" not in cat.name:
        pass
    if not cat.is_dir():
        continue
    for skill in sorted(cat.iterdir()):
        if not skill.is_dir():
            continue
        desc = list(skill.glob("技能说明_*.md"))
        if not desc:
            continue
        kb = skill / FOLDER
        readme = kb / "README.md"
        if readme.is_file():
            skipped.append(skill.name)
            continue
        (kb / "案例_Cases").mkdir(parents=True, exist_ok=True)
        readme.write_text(STUB.format(skill=skill.name, ssot=SSOT), encoding="utf-8")
        created.append(f"{cat.name}/{skill.name}")

print(f"created={len(created)} skipped(existing)={len(skipped)}")
for x in created:
    print(" +", x)
