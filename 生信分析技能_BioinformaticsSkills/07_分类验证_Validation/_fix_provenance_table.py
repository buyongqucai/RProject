# -*- coding: utf-8 -*-
from pathlib import Path
import csv

bio = Path(r"E:/RProject/生信分析技能_BioinformaticsSkills")
rows = []
n_real = n_toy = n_blocked = 0
for ds in sorted(bio.rglob("DATA_SOURCE.md")):
    if "01_样例_sample" not in str(ds):
        continue
    # .../skill/01_样例_sample/数据文件/DATA_SOURCE.md
    sample_root = ds.parents[1]  # 01_样例_sample
    skill = ds.parents[2]
    rel = skill.relative_to(bio).as_posix()
    text = ds.read_text(encoding="utf-8", errors="replace")
    st = sample_root / "结果文件" / "报告文件" / "STATUS.txt"
    status = ""
    if st.exists():
        status = st.read_text(encoding="utf-8", errors="replace").strip().splitlines()[0]
    if "网络药理学" in rel or "NetworkPharmacology" in rel:
        prov = "REAL"
    elif status == "BLOCKED" or "blocked_" in text.lower():
        prov = "BLOCKED"
    elif "data_provenance: REAL" in text:
        prov = "REAL"
    else:
        prov = "TOY"
    if prov == "REAL":
        n_real += 1
        note = "用户交付中间表 / REAL"
    elif prov == "BLOCKED":
        n_blocked += 1
        note = "契约桩 BLOCKED"
    else:
        n_toy += 1
        note = "脚本模拟 toy；不可外推"
    evidence = (sample_root / "数据文件").relative_to(bio).as_posix()
    rows.append([rel, prov, evidence, note, status or "MISSING"])

outp = bio / "07_分类验证_Validation" / "样例数据来源审计.csv"
with open(outp, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["技能", "数据来源类型", "证据路径", "说明", "STATUS"])
    w.writerows(rows)
print("REAL", n_real, "TOY", n_toy, "BLOCKED", n_blocked, "TOTAL", len(rows))

# rebuild markdown table in 验证总报告
lines = [
    "## 样例数据来源总表（data_provenance）",
    "",
    f"> **诚实摘要（{len(rows)} 个 01_样例_sample）**：**REAL={n_real}**，**TOY={n_toy}**，**BLOCKED={n_blocked}**。",
    "> 绝大多数样例为可复现模拟（TOY），**不是** GEO 真下载；唯一 REAL 为网络药理学用户交付中间表。",
    "> 完整 CSV：`样例数据来源审计.csv`；严谨性：`技能严谨性审核.md`。",
    "",
    "| 技能 | 数据来源类型 | 证据路径 | 说明 |",
    "|------|--------------|----------|------|",
]
for skill, prov, ev, note, _st in rows:
    lines.append(f"| `{skill}` | **{prov}** | `{ev}` | {note} |")
lines.append("")
md = "\n".join(lines)

header = f"""# 验证总报告 / Per-Skill Sample Validation

- **更新时间**：2026-07-18T21:30:00
- **布局版本**：catalog + 统一交付规范 + 图面 English + **data_provenance 强制标注**
- **样例 provenance**：**REAL {n_real} / TOY {n_toy} / BLOCKED {n_blocked}**（共 {len(rows)}）
- **本轮要点**：网络药理学按交付物重做；VizStandards 典型图种；严谨性审核见 `技能严谨性审核.md`

"""

rep = bio / "07_分类验证_Validation" / "验证总报告.md"
text = rep.read_text(encoding="utf-8")
marker = "## 关于 Cursor/Git"
if marker in text:
    _, post = text.split(marker, 1)
    new = header + md + "\n" + marker + post
else:
    new = header + md + "\n" + text
rep.write_text(new, encoding="utf-8")
print("fixed report")
