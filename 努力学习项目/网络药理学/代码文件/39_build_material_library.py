# -*- coding: utf-8 -*-
"""Build material library folders + catalog CSV/xlsx from existing bio_base PNGs."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")
ASSETS = Path(r"C:/Users/10540/.cursor/projects/e-RProject/assets")
DELIV_BASES = ROOT / "交付文件" / "图片" / "动画_生物结构" / "_bases"
LIB_DELIV = ROOT / "交付文件" / "图片" / "动画_生物结构" / "_素材库"
LIB_DB = Path(r"D:/数据库/KEGG数据库/KEGG动画素材库")

sys.path.insert(0, str(ROOT / "代码文件"))
from kegg_base_library import ARCHETYPES, LIBRARY_README  # noqa: E402


def main() -> None:
    for lib in (LIB_DELIV, LIB_DB):
        lib.mkdir(parents=True, exist_ok=True)
        (lib / "按原型").mkdir(exist_ok=True)
        (lib / "全部底图").mkdir(exist_ok=True)

    search = [ASSETS, DELIV_BASES]
    rows = []
    seen = set()

    for arch, names in ARCHETYPES.items():
        arch_dir_d = LIB_DELIV / "按原型" / arch
        arch_dir_b = LIB_DB / "按原型" / arch
        arch_dir_d.mkdir(parents=True, exist_ok=True)
        arch_dir_b.mkdir(parents=True, exist_ok=True)
        for name in names:
            src = None
            for d in search:
                p = d / name
                if p.exists():
                    src = p
                    break
            if src is None:
                continue
            # copy to 全部底图 once
            if name not in seen:
                shutil.copy2(src, LIB_DELIV / "全部底图" / name)
                shutil.copy2(src, LIB_DB / "全部底图" / name)
                seen.add(name)
            # copy/link into archetype folder
            shutil.copy2(src, arch_dir_d / name)
            shutil.copy2(src, arch_dir_b / name)
            rows.append({"原型": arch, "底图文件": name, "字节": src.stat().st_size, "来源": str(src)})

    # also vacuum any other bio_base_* into 全部底图
    for d in search:
        for p in d.glob("bio_base_*.png"):
            if p.name in seen:
                continue
            shutil.copy2(p, LIB_DELIV / "全部底图" / p.name)
            shutil.copy2(p, LIB_DB / "全部底图" / p.name)
            seen.add(p.name)
            rows.append({"原型": "未分类入库", "底图文件": p.name, "字节": p.stat().st_size, "来源": str(p)})

    cat = pd.DataFrame(rows)
    cat.to_csv(LIB_DELIV / "素材库目录.csv", index=False, encoding="utf-8-sig")
    cat.to_csv(LIB_DB / "素材库目录.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(LIB_DB / "素材库目录.xlsx", engine="openpyxl") as w:
        cat.to_excel(w, sheet_name="底图清单", index=False)
        pd.DataFrame(
            [{"原型": k, "候选数": len(v), "首选": v[0] if v else ""} for k, v in ARCHETYPES.items()]
        ).to_excel(w, sheet_name="原型说明", index=False)

    (LIB_DELIV / "README.txt").write_text(LIBRARY_README, encoding="utf-8")
    (LIB_DB / "README.txt").write_text(LIBRARY_README, encoding="utf-8")
    print("OK bases=", len(seen), "rows=", len(cat))
    print("DELIV", LIB_DELIV)
    print("DB", LIB_DB)


if __name__ == "__main__":
    main()
