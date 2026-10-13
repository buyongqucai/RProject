# -*- coding: utf-8 -*-
"""Update scripts after 数据文件/原始数据 rename."""
from pathlib import Path

ROOT = Path(r"E:/RProject") / "努力学习项目"

REPLACEMENTS = [
    ('数据文件/外部数据库', '数据文件/原始数据/外部数据库_多源'),
    ('数据文件\\外部数据库', '数据文件\\原始数据\\外部数据库_多源'),
    ('"数据文件", "外部数据库"', '"数据文件", "原始数据", "外部数据库_多源"'),
    ("'数据文件', '外部数据库'", "'数据文件', '原始数据', '外部数据库_多源'"),
    ('数据文件/SEA原始', '数据文件/原始数据/SEA数据库_SEA原始'),
    ('数据文件/SEA16原始', '数据文件/原始数据/SEA数据库_SEA16原始'),
    ('数据文件/STP原始', '数据文件/原始数据/SwissTargetPrediction_STP原始'),
    ('数据文件\\SEA原始', '数据文件\\原始数据\\SEA数据库_SEA原始'),
    ('数据文件\\SEA16原始', '数据文件\\原始数据\\SEA数据库_SEA16原始'),
    ('数据文件\\STP原始', '数据文件\\原始数据\\SwissTargetPrediction_STP原始'),
    ('"数据文件", "SEA原始"', '"数据文件", "原始数据", "SEA数据库_SEA原始"'),
    ('"数据文件", "SEA16原始"', '"数据文件", "原始数据", "SEA数据库_SEA16原始"'),
    ('"数据文件", "STP原始"', '"数据文件", "原始数据", "SwissTargetPrediction_STP原始"'),
    ("'数据文件', 'SEA原始'", "'数据文件', '原始数据', 'SEA数据库_SEA原始'"),
    ("'数据文件', 'SEA16原始'", "'数据文件', '原始数据', 'SEA数据库_SEA16原始'"),
    ("'数据文件', 'STP原始'", "'数据文件', '原始数据', 'SwissTargetPrediction_STP原始'"),
    # MD
    ('数据文件/MD输入_Top3', '数据文件/原始数据/RCSB与对接姿态_MD输入_Top3'),
    ('数据文件\\MD输入_Top3', '数据文件\\原始数据\\RCSB与对接姿态_MD输入_Top3'),
    # docking workspace
    ('数据文件/对接工作区', '数据文件/原始数据/RCSB与PubChem_对接结构工作区'),
    ('数据文件\\对接工作区', '数据文件\\原始数据\\RCSB与PubChem_对接结构工作区'),
]

changed = []
for p in ROOT.rglob("*"):
    if "交付文件" in p.parts:
        continue
    if p.suffix.lower() not in {".py", ".r", ".md", ".txt", ".html"}:
        continue
    if not p.is_file():
        continue
    text = p.read_text(encoding="utf-8")
    new = text
    for a, b in REPLACEMENTS:
        new = new.replace(a, b)
    if new != text:
        p.write_text(new, encoding="utf-8")
        changed.append(str(p.relative_to(ROOT)))

print("changed", len(changed))
for c in changed:
    print(c)
