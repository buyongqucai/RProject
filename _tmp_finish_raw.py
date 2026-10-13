# -*- coding: utf-8 -*-
from pathlib import Path
import shutil

root = Path(r"E:/RProject") / "努力学习项目"
ext = next(root.glob("03_*")) / "数据文件" / "原始数据" / "外部数据库_多源"
m01 = next(root.glob("01_*"))
m02 = next(root.glob("02_*"))

for name, label in [("gutMGene_v2", "gutMGene数据库_gutMGene_v2"), ("GTEx", "GTEx数据库_GTEx")]:
    src = ext / name
    dst = m01 / "数据文件" / "原始数据" / label
    if src.is_dir() and not dst.exists():
        shutil.copytree(src, dst)
        print("01 got", label, sum(1 for _ in dst.rglob("*") if _.is_file()))

(m02 / "数据文件" / "原始数据" / "README_原始数据来源.md").write_text(
    "# 02 网络毒理学 · 原始数据来源\n\n"
    "CTD 全量约 380MB，不在本模块重复存放。\n\n"
    f"- **CTD 权威副本：** `{ext.as_posix()}/CTD/`\n"
    "- 毒性分层所用输入表：见 `03_…/数据文件/结果数据/` 与本模块 `数据文件/结果数据/毒性分层/`。\n",
    encoding="utf-8",
)

(m01 / "数据文件" / "原始数据" / "README_原始数据来源.md").write_text(
    "# 01 网络药理学 · 原始数据来源\n\n"
    "| 目录 | 来源数据库 |\n|------|------------|\n"
    "| `gutMGene数据库_gutMGene_v2/` | gutMGene v2 |\n"
    "| `GTEx数据库_GTEx/` | GTEx |\n\n"
    "大库不重复拷贝：\n"
    f"- CTD / GMMAD2 / GEO / GWAS → `{ext.as_posix()}/`\n"
    "- SEA / STP 原始 → `03_…/数据文件/原始数据/SEA数据库_*` 与 `SwissTargetPrediction_STP原始/`\n"
    "- 本模块产物表 → `数据文件/结果数据/`\n",
    encoding="utf-8",
)

left = []
for p in root.rglob("数据文件"):
    if "交付文件" in p.parts:
        continue
    if p.parent.name == "结果文件":
        left.append(str(p.relative_to(root)))
print("leftover", left)
print("done")
