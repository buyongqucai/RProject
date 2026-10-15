# -*- coding: utf-8 -*-
from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0, r"E:\RProject\努力学习项目\网络药理学\代码文件")
from kegg_zh_names import ZH

man = Path(r"E:\RProject\努力学习项目\网络药理学\交付文件\图片\KEGG官方通路图\00_全部通路图清单.csv")
anim = Path(r"D:\数据库\KEGG数据库\KEGG动画图")
bases = Path(r"E:\RProject\努力学习项目\网络药理学\交付文件\图片\动画_生物结构\_bases")
df = pd.read_csv(man, encoding="utf-8-sig")
have_rank = set()
if anim.exists():
    for p in anim.glob("*_动画.gif"):
        try:
            have_rank.add(int(p.name.split("_")[0]))
        except ValueError:
            pass
base_rank = set()
if bases.exists():
    for p in bases.glob("bio_base_*.png"):
        parts = p.stem.split("_")
        if len(parts) >= 3:
            try:
                base_rank.add(int(parts[2]))
            except ValueError:
                pass
missing = [int(r) for r in df["rank"] if int(r) not in have_rank]
print("manifest", len(df), "gifs", len(have_rank), "bases", len(base_rank))
print("missing", len(missing))
print("missing_ranks", ",".join(f"{x:03d}" for x in missing[:40]))
sub = df[df["rank"].isin(missing[:20])]
for _, r in sub.iterrows():
    pid = str(r["pathway_id"]).strip()
    zh = ZH.get(pid, "?")
    print(f"{int(r['rank']):03d}\t{pid}\t{zh}\t{r['description']}")
