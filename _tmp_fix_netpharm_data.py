# -*- coding: utf-8 -*-
"""Undo wrong raw copies in 01; restore 药物/疾病 from delivery zip."""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

ROOT = Path(r"E:/RProject") / "努力学习项目"
M01 = next(ROOT.glob("01_*"))
ZIP = Path(r"D:\微信\聊天记录\xwechat_files\wxid_ulwwl4x2eyjx22_7138\msg\file\2026-10\交付文件(1).zip")
RAW = M01 / "数据文件" / "原始数据"
RES = M01 / "数据文件" / "结果数据"

# 1) remove wrongly mixed libraries
wrong = [
    RAW / "gutMGene数据库_gutMGene_v2",
    RAW / "GTEx数据库_GTEx",
]
for p in wrong:
    if p.exists():
        shutil.rmtree(p)
        print("removed", p.name)

# 2) extract 药物 / 疾病 as netpharm raw
# zip paths use 交付文件/数据/药物 and 交付文件/数据/疾病
z = zipfile.ZipFile(ZIP)
names = z.namelist()

def dest_for(name: str) -> Path | None:
    n = name.replace("\\", "/")
    if n.endswith("/"):
        return None
    marker_drug = "/数据/药物/"
    marker_dis = "/数据/疾病/"
    if marker_drug in n:
        rel = n.split(marker_drug, 1)[1]
        return RAW / "药物数据_复方成分与靶点" / rel
    if marker_dis in n:
        rel = n.split(marker_dis, 1)[1]
        return RAW / "疾病数据_UC靶点多库" / rel
    return None

n_drug = n_dis = 0
for name in names:
    dst = dest_for(name)
    if dst is None:
        continue
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_size == z.getinfo(name).file_size:
        continue
    with z.open(name) as src, dst.open("wb") as out:
        shutil.copyfileobj(src, out)
    if "药物数据" in str(dst):
        n_drug += 1
    else:
        n_dis += 1
print("extracted drug", n_drug, "disease", n_dis)

# 3) fill missing netpharm RESULT tables from zip 数据/{PPI,富集分析,网络图,药物疾病交集 already in 药物}
# Only copy files that are not already under 结果数据 (by filename)
existing = {p.name for p in RES.rglob("*") if p.is_file()}
result_markers = ("/数据/PPI/", "/数据/富集分析/", "/数据/网络图/")
added = []
for name in names:
    n = name.replace("\\", "/")
    if n.endswith("/"):
        continue
    hit = None
    for m in result_markers:
        if m in n:
            hit = m
            break
    if not hit:
        continue
    fname = Path(n).name
    if fname in existing:
        continue
    rel = n.split(hit, 1)[1]
    folder = {"/数据/PPI/": "PPI", "/数据/富集分析/": "富集分析", "/数据/网络图/": "网络图"}[hit]
    dst = RES / folder / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    with z.open(name) as src, dst.open("wb") as out:
        shutil.copyfileobj(src, out)
    added.append(str(dst.relative_to(M01)))
print("result tables added", len(added))
for a in added:
    print(" ", a)

# 4) correct provenance readme — drug + disease only
(RAW / "README_原始数据来源.md").write_text(
    "# 01 网络药理学 · 原始数据\n\n"
    "本模块只放**药物**与**疾病**两套输入（研究计划：F 与 D）。\n"
    "菌群代谢物（gutMGene / GMMAD2 / SEA / STP）、毒性（CTD 毒性分层）、"
    "结肠表达（GTEx）不放在本模块。\n\n"
    "| 目录 | 内容 | 来源 |\n"
    "|------|------|------|\n"
    "| `药物数据_复方成分与靶点/` | 12 味药成分、成分靶点、F、药物–疾病交集 | 交付轨 B；成分库 TCMSP 等，见表内来源列 |\n"
    "| `疾病数据_UC靶点多库/` | UC 疾病靶点合并，\\|D\\|=1517 | GeneCards / OMIM / DisGeNET / CTD 等，见 `疾病靶点按库` |\n\n"
    "来源压缩包：`交付文件(1).zip`（2026-10 聊天文件）。\n"
    "PPI / 富集 / 网络图是本模块**结果**，在 `数据文件/结果数据/`。\n",
    encoding="utf-8",
)

# 5) remove mistaken upstream copies that are not that module's own database
for prefix, folder in [
    ("04_", "上游03结果_交集基因表"),
    ("05_", "上游03结果_代谢物面板"),
]:
    p = next(ROOT.glob(prefix + "*")) / "数据文件" / "原始数据" / folder
    if p.exists():
        shutil.rmtree(p)
        print("removed", prefix, folder)

print("01 raw tops:")
for c in sorted(RAW.iterdir()):
    n = sum(1 for x in c.rglob("*") if x.is_file()) if c.is_dir() else 1
    print(" ", c.name, n)
