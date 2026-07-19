# -*- coding: utf-8 -*-
from pathlib import Path
import csv

bio = Path(r"E:/RProject/生信分析技能_BioinformaticsSkills")
csv_path = bio / "07_分类验证_Validation" / "样例数据来源审计.csv"
rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))

lines = []
lines.append("## 样例数据来源总表（data_provenance）")
lines.append("")
lines.append(
    "> **诚实摘要（70 个 01_样例_sample）**：**REAL=1**，**TOY=57**，**BLOCKED=12**。"
)
lines.append(
    "> 绝大多数样例为可复现模拟（TOY），**不是** GEO 真下载；唯一 REAL 为网络药理学用户交付中间表。"
)
lines.append(
    "> 完整 CSV：`样例数据来源审计.csv`；严谨性：`技能严谨性审核.md`。"
)
lines.append("")
lines.append("| 技能 | 数据来源类型 | 证据路径 | 说明 |")
lines.append("|------|--------------|----------|------|")
for r in rows:
    skill = r["技能"].replace("|", "/")
    ev = r["证据路径"]
    marker = "生信分析技能_BioinformaticsSkills"
    if marker in ev.replace("\\", "/"):
        ev = ev.replace("\\", "/").split(marker + "/")[-1]
    else:
        ev = ev.replace("\\", "/")
        # make relative if absolute under bio
        try:
            ev = str(Path(r["证据路径"]).resolve().relative_to(bio)).replace("\\", "/")
        except Exception:
            pass
    lines.append(
        "| `{skill}` | **{prov}** | `{ev}` | {note} |".format(
            skill=skill, prov=r["数据来源类型"], ev=ev, note=r["说明"]
        )
    )
lines.append("")
md = "\n".join(lines)

header = """# 验证总报告 / Per-Skill Sample Validation

- **更新时间**：2026-07-18T21:30:00
- **布局版本**：catalog + 统一交付规范 + 图面 English + **data_provenance 强制标注**
- **样例 provenance**：**REAL 1 / TOY 57 / BLOCKED 12**（共 70）
- **本轮要点**：网络药理学按交付物重做；VizStandards 典型图种；严谨性审核见 `技能严谨性审核.md`

"""

rep = bio / "07_分类验证_Validation" / "验证总报告.md"
text = rep.read_text(encoding="utf-8")
marker = "## 关于 Cursor/Git"
if marker in text:
    _, post = text.split(marker, 1)
    # drop old leading H1 content
    new = header + md + "\n" + marker + post
else:
    new = header + md + "\n" + text
rep.write_text(new, encoding="utf-8")
print("updated", rep, "lines", len(new.splitlines()))
