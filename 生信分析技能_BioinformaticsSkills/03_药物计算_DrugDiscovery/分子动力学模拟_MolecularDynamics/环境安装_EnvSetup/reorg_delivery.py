# -*- coding: utf-8 -*-
"""Reorganize 努力学习项目 delivery: project-based 交付文件_修正版 → 交付文件."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

proj = next(p for p in Path(r"E:/RProject").iterdir() if p.is_dir() and "努力" in p.name)
fixed = proj / "交付文件_修正版"
old = proj / "交付文件"
tox_work = next(proj.glob("网络毒理学*"))
tox_results = tox_work / "结果文件"
pharma = proj / "网络药理学"

print("PROJ", proj)
assert fixed.is_dir() and old.is_dir() and tox_results.is_dir()

# --- inspect html paths ---
html = fixed / "图注与解读说明.html"
if html.exists():
    text = html.read_text(encoding="utf-8", errors="replace")
    refs = sorted(set(re.findall(r'(?:src|href)=["\']([^"\']+)', text)))
    print("html_refs", len(refs))
    for r in refs[:25]:
        print(" ", r)

pharma_name = "网络药理学"
tox_name = tox_work.name  # 网络毒理学_菌群代谢物双交集

pharma_dst = fixed / pharma_name
tox_dst = fixed / tox_name

# 1) Nest existing 修正版 content under 网络药理学/
if not pharma_dst.exists():
    pharma_dst.mkdir(parents=True)
    for name in ("图片文件", "数据文件", "报告文件"):
        src = fixed / name
        if src.exists():
            print("move", src.name, "->", pharma_name)
            shutil.move(str(src), str(pharma_dst / name))
    for name in (
        "README_归档说明.md",
        "README_轨B说明.txt",
        "图注与解读说明.html",
    ):
        src = fixed / name
        if src.exists():
            print("move", name, "->", pharma_name)
            shutil.move(str(src), str(pharma_dst / name))
else:
    print("skip nest pharma: already exists")

# 2) Put 网络毒理学 结果文件 into 修正版 (copy tree; keep work tree intact)
if tox_dst.exists():
    print("remove existing tox_dst for clean copy")
    shutil.rmtree(tox_dst)
print("copy tox results ->", tox_name)
shutil.copytree(tox_results, tox_dst)

# 3) Ensure MD from old 交付文件 is present (move into tox if missing/newer)
for kind, folder in (
    ("图片文件", "分子动力学图_MD"),
    ("数据文件", "分子动力学_MD"),
):
    src_md = old / kind / folder
    dst_md = tox_dst / kind / folder
    if src_md.exists():
        if dst_md.exists():
            # prefer source that has more files
            n_src = sum(1 for _ in src_md.rglob("*") if _.is_file())
            n_dst = sum(1 for _ in dst_md.rglob("*") if _.is_file())
            print(f"MD {folder}: old_delivery={n_src} tox={n_dst}")
            if n_src > n_dst:
                shutil.rmtree(dst_md)
                shutil.copytree(src_md, dst_md)
                print("  refreshed from old 交付文件")
        else:
            dst_md.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src_md, dst_md)
            print("copied MD", folder, "from old 交付文件")
        # remove MD from old delivery after ensuring present
        shutil.rmtree(src_md)
        print("removed MD from old 交付文件:", kind, folder)
    else:
        print("no MD in old 交付文件:", kind, folder)

# also drop MD from old delivery if still under flat paths after move above
# (already removed)

# 4) Write top-level README for the new package
readme = fixed / "README_轨B说明.txt"
readme.write_text(
    "轨 B 客户归档（按课题分子目录）。\n"
    "目录：\n"
    f"  {pharma_name}/     — 网络药理学交付（图片文件/数据文件/报告文件）\n"
    f"  {tox_name}/ — 网络毒理学交付（图片文件/数据文件/报告文件，含分子动力学）\n"
    "\n"
    "【发给别人】请打包整个「交付文件」文件夹。\n"
    f"  网药入口：{pharma_name}/图注与解读说明.html\n"
    f"  网毒图/表：{tox_name}/图片文件/ 、{tox_name}/数据文件/\n"
    "\n"
    "规范：努力学习项目/存放规范_ProjectLayout.md\n",
    encoding="utf-8",
)

# 5) Replace old 交付文件 with 修正版
bak = proj / "交付文件_旧版待删"
if bak.exists():
    shutil.rmtree(bak)
print("rename old 交付文件 -> 交付文件_旧版待删")
old.rename(bak)
print("rename 交付文件_修正版 -> 交付文件")
fixed.rename(proj / "交付文件")

new_del = proj / "交付文件"

# 6) Update 存放规范
layout = proj / "存放规范_ProjectLayout.md"
if layout.exists():
    text = layout.read_text(encoding="utf-8")
    new_section = (
        "## 3. 交付包（轨 B）\n\n"
        "```text\n"
        "交付文件/\n"
        "  网络药理学/\n"
        "    数据文件/\n"
        "    图片文件/\n"
        "    报告文件/\n"
        "    图注与解读说明.html\n"
        "  网络毒理学_菌群代谢物双交集/\n"
        "    数据文件/          # 含 分子动力学_MD/\n"
        "    图片文件/          # 含 分子动力学图_MD/\n"
        "    报告文件/\n"
        "  README_轨B说明.txt\n"
        "```\n\n"
        "只维护一份活动交付：`交付文件/`（按课题分子目录）。"
        "工作树产物仍在各课题 `结果文件/`；轨 B 为客户包副本。\n"
    )
    text2 = re.sub(
        r"## 3\. 交付包（轨 B）\n.*?(?=\n## 4\. |\Z)",
        new_section + "\n",
        text,
        count=1,
        flags=re.S,
    )
    # drop obsolete 修正版 row in table
    text2 = text2.replace(
        "| `交付文件_修正版/` | 历史快照（勿再写） | 同上三夹名 |\n",
        "",
    )
    text2 = text2.replace(
        "| `交付文件/` | 对外交付包（轨 B） | `数据文件/` `图片文件/` `报告文件/` |\n",
        "| `交付文件/` | 对外交付包（轨 B） | 按课题：`网络药理学/`、`网络毒理学_…/` |\n",
    )
    layout.write_text(text2, encoding="utf-8")
    print("updated 存放规范_ProjectLayout.md")

# update tox layout pointer
tox_layout = tox_work / "存放规范_ProjectLayout.md"
if tox_layout.exists():
    t = tox_layout.read_text(encoding="utf-8")
    t = t.replace(
        "轨 B 客户包 `努力学习项目/交付文件/`：\n\n```text\n交付文件/\n  数据文件/\n  图片文件/\n  报告文件/\n```",
        "轨 B 客户包 `努力学习项目/交付文件/`（按课题分子目录）：\n\n"
        "```text\n"
        "交付文件/\n"
        "  网络药理学/\n"
        "  网络毒理学_菌群代谢物双交集/   # 本课题轨 B 副本（含 MD）\n"
        "```",
    )
    tox_layout.write_text(t, encoding="utf-8")
    print("updated tox ProjectLayout")

# update 网络药理学 README
pharma_readme = pharma / "README_目录角色.md"
if pharma_readme.exists():
    pharma_readme.write_text(
        "# 目录角色（2026-10-10）\n\n"
        "当前仓库主要是 KEGG 官方通路图拉取脚本与清单；完整网药图/表在轨 B。\n\n"
        "- 网毒 UC 主工作树：`../网络毒理学_菌群代谢物双交集/`\n"
        "- 活动交付：`../交付文件/网络药理学/`\n"
        "- 网毒交付：`../交付文件/网络毒理学_菌群代谢物双交集/`\n"
        "- 存放规范：`../存放规范_ProjectLayout.md`\n",
        encoding="utf-8",
    )
    print("updated 网络药理学 README")

# 7) Remove backup old delivery after success check
summary = {
    "delivery": str(new_del),
    "children": sorted([p.name for p in new_del.iterdir()]),
    "pharma_dirs": sorted([p.name for p in (new_del / pharma_name).iterdir()])
    if (new_del / pharma_name).exists()
    else [],
    "tox_dirs": sorted([p.name for p in (new_del / tox_name).iterdir()])
    if (new_del / tox_name).exists()
    else [],
    "md_pic": (new_del / tox_name / "图片文件" / "分子动力学图_MD").exists(),
    "md_data": (new_del / tox_name / "数据文件" / "分子动力学_MD").exists(),
    "old_bak": str(bak),
    "old_bak_exists": bak.exists(),
}
Path(r"E:/md_kit/_reorg_delivery_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False, indent=2))

# delete old bak if MD already in new delivery
if summary["md_pic"] and summary["md_data"] and bak.exists():
    shutil.rmtree(bak)
    print("deleted 交付文件_旧版待删")
print("DONE")
