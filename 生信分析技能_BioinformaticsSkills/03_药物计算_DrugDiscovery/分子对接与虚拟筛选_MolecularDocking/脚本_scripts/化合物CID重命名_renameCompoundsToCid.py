# -*- coding: utf-8 -*-
"""化合物CID重命名_renameCompoundsToCid.py
把对接库小分子文件从「语义英文名」改为「PubChem CID」命名：
  small/{slug}.sdf            -> small/{cid}.sdf
  small_clean/{slug}_clean.sdf -> small_clean/{cid}_clean.sdf
  small_clean_h/{slug}_clean_h.pdbqt -> small_clean_h/{cid}_clean_h.pdbqt
同一 CID 多名称（盐/母体撞车）时保留先见文件，重复文件删除并记入对照表。
输出：D:\\数据库\\分子对接数据库\\化合物_CID命名对照.csv
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

BASE = Path(r"D:\数据库\分子对接数据库\test")
TABLE = Path(r"D:\数据库\分子对接数据库\分子对接_化合物表.csv")
OUT_MAP = Path(r"D:\数据库\分子对接数据库\化合物_CID命名对照.csv")


def safe_name(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", name.strip().lower()).strip("_")
    return re.sub(r"_+", "_", s)


def read_any(p: Path) -> list[list[str]]:
    for enc in ("utf-8-sig", "gbk"):
        try:
            with open(p, encoding=enc) as f:
                return list(csv.reader(f))
        except UnicodeDecodeError:
            continue
    raise RuntimeError(str(p))


def main() -> None:
    rows = read_any(TABLE)
    header = rows[0]
    i_name, i_cid = header.index("活性成分名称"), header.index("活性成分3D结构名称")
    pairs = [(r[i_name].strip(), r[i_cid].strip()) for r in rows[1:] if len(r) > i_cid]

    mapping, seen_cid, n_ren, n_dup, n_miss = [], {}, 0, 0, 0
    for name, cid in pairs:
        slug = safe_name(name)
        action = "rename"
        for sub, old_pat, new_pat in [
            ("small", f"{slug}.sdf", f"{cid}.sdf"),
            ("small_clean", f"{slug}_clean.sdf", f"{cid}_clean.sdf"),
            ("small_clean_h", f"{slug}_clean_h.pdbqt", f"{cid}_clean_h.pdbqt"),
        ]:
            old = BASE / sub / old_pat
            new = BASE / sub / new_pat
            if not old.exists():
                if new.exists():
                    continue  # 已重命名过（幂等）
                continue
            if new.exists():
                # CID 撞车：同名分子已存在 → 删除重复
                old.unlink()
                action = "dup_removed"
                n_dup += 1
                continue
            old.rename(new)
            n_ren += 1
        if not (BASE / "small" / f"{slug}.sdf").exists() and not (BASE / "small" / f"{cid}.sdf").exists():
            action = "missing_small"
            n_miss += 1
        mapping.append({"活性成分名称": name, "slug": slug, "CID": cid, "action": action})

    with open(OUT_MAP, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["活性成分名称", "slug", "CID", "action"])
        w.writeheader()
        w.writerows(mapping)
    print(f"renamed={n_ren} dup_removed={n_dup} missing={n_miss} total={len(pairs)}")
    print("map ->", OUT_MAP)


if __name__ == "__main__":
    sys.exit(main())
