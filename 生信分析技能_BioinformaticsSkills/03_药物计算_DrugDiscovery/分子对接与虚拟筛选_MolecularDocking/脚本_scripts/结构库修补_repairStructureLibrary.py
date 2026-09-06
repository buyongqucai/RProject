# -*- coding: utf-8 -*-
"""结构库修补：处理 prepareStructureLibrary 遗留失败项。

1) 9cmk 等瞬时下载失败重试。
2) 盐型 CID（*_hydrochloride/mesylate/...）→ PUG 名称解析母体 CID → 母体 3D SDF，
   仍按登记表文件名落盘，日志记录 salt→parent 映射。
3) 平面分子（如苯甲酸 z-span=0）：x/y 跨度正常即放行，备注 planar。
4) 含 Si 等 Vina 不支持原子的配体：跳过 pdbqt，记 SKIP_unsupported。
"""
from __future__ import annotations

import csv
import re
import time
from pathlib import Path

import requests

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "prep", Path(__file__).with_name("结构库准备_prepareStructureLibrary.py"))
prep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prep)

DB = Path(r"D:\数据库\分子对接数据库")
ROOT = DB / "test"
LOG = ROOT / "_structure_lib_repair.csv"

SALT_SUFFIXES = ["hydrochloride", "mesylate", "ditosylate", "tosylate", "malate",
                 "maleate", "calcium", "sodium", "potassium", "bisulfate",
                 "diphosphate", "besylate", "dihydrogen_salt", "succinate",
                 "citrate", "tartrate", "sulfate", "phosphate", "acetate"]


def parent_name(name: str) -> str | None:
    parts = name.split("_")
    for i, p in enumerate(parts):
        if p in SALT_SUFFIXES and i > 0:
            return " ".join(parts[:i])
    return None


def main():
    s = requests.Session()
    s.headers.update(prep.UA)
    write_header = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8-sig") as fh:
        log = csv.writer(fh)
        if write_header:
            log.writerow(["key", "action", "status", "note", "ts"])

        comps = prep.read_csv_any(DB / "分子对接_化合物表.csv") \
            if hasattr(prep, "read_csv_any") else None
        # 重新读表（prep 的 read_csv_any 在 main 内，局部不可见 → 这里自读）
        raw = (DB / "分子对接_化合物表.csv").read_bytes()
        for enc in ("utf-8-sig", "gbk"):
            try:
                comps = list(csv.DictReader(raw.decode(enc).splitlines()))
                break
            except UnicodeDecodeError:
                continue

        for row in comps:
            cid = (row.get("活性成分3D结构名称") or "").strip()
            cname = (row.get("活性成分名称") or "").strip()
            name = prep.safe_name(cname or f"cid_{cid}")
            stem = cid  # 2026-08-31 起：化合物文件一律以 PubChem CID 命名
            sdf = ROOT / "small" / f"{stem}.sdf"
            clean = ROOT / "small_clean" / f"{stem}_clean.sdf"
            pdbqt = ROOT / "small_clean_h" / f"{stem}_clean_h.pdbqt"
            if pdbqt.exists() and pdbqt.stat().st_size > 100:
                continue

            # --- 下载缺失：盐型 → 母体 CID ---
            if not sdf.exists():
                pname = parent_name(name)
                got = False
                if pname:
                    try:
                        r = s.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/"
                                  f"compound/name/{requests.utils.quote(pname)}/cids/JSON",
                                  timeout=60)
                        pcid = r.json()["IdentifierList"]["CID"][0]
                        got = prep.fetch(
                            s, f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/"
                               f"cid/{pcid}/SDF?record_type=3d", sdf)
                        log.writerow([cid, "salt_to_parent", "OK" if got else "FAIL",
                                      f"{name} -> {pname} CID {pcid}",
                                      time.strftime("%F %T")])
                    except Exception as e:
                        log.writerow([cid, "salt_to_parent", "FAIL",
                                      f"{name}: {e}"[:150], time.strftime("%F %T")])
                if not got and not sdf.exists():
                    continue
                time.sleep(0.3)

            # --- 平面分子放行 ---
            if not clean.exists():
                z = prep.sdf_zspan(sdf)
                if z < 0.3:
                    txt = sdf.read_text(encoding="utf-8", errors="ignore").splitlines()
                    xs, ys = [], []
                    try:
                        na = int(txt[3][0:3])
                        for ln in txt[4:4 + na]:
                            xs.append(float(ln[0:10]))
                            ys.append(float(ln[10:20]))
                    except Exception:
                        pass
                    if xs and (max(xs) - min(xs)) > 1.0 and (max(ys) - min(ys)) > 1.0:
                        log.writerow([cid, "planar_accept", "OK",
                                      f"{name} z-span {z:.2f}", time.strftime("%F %T")])
                    else:
                        log.writerow([cid, "planar_accept", "FAIL", name,
                                      time.strftime("%F %T")])
                        continue
                clean.write_bytes(sdf.read_bytes())

            # --- pdbqt（Si 等不支持原子跳过）---
            if "siloxane" in cname.lower() or "_si" in name:
                log.writerow([cid, "pdbqt", "SKIP_unsupported", name,
                              time.strftime("%F %T")])
                continue
            mol2 = ROOT / "small_clean_h" / f"{stem}.mol2"
            ok1, m1 = prep.obabel([str(clean), "-O", str(mol2), "-h"])
            ok2, m2 = False, "no mol2"
            if ok1 and mol2.exists():
                ok2, m2 = prep.obabel([str(mol2), "-O", str(pdbqt), "-h",
                                       "--partialcharge", "gasteiger"])
                mol2.unlink(missing_ok=True)
            if not ok2:  # 回退：SDF 直接转
                ok3, m3 = prep.obabel([str(clean), "-O", str(pdbqt), "-h",
                                       "--partialcharge", "gasteiger"])
                ok2, m2 = ok3, (m2 + "|direct:" + m3)[-250:]
            log.writerow([cid, "pdbqt", "OK" if ok2 else "FAIL",
                          (m1 + "|" + m2)[-250:], time.strftime("%F %T")])
            time.sleep(0.3)

        # --- 9cmk 重试 ---
        dest = ROOT / "big" / "9cmk.pdb"
        if not dest.exists():
            ok = prep.fetch(s, "https://files.rcsb.org/download/9CMK.pdb", dest)
            log.writerow(["9cmk", "download_retry", "OK" if ok else "FAIL", "",
                          time.strftime("%F %T")])
            if ok:
                clean = ROOT / "big_clean" / "9cmk_clean.pdb"
                prep.clean_protein(dest, clean)
                pdbqt = ROOT / "big_clean_h" / "9cmk_clean_h.pdbqt"
                ok2, m2 = prep.obabel([str(clean), "-O", str(pdbqt), "-h"])
                log.writerow(["9cmk", "pdbqt", "OK" if ok2 else "FAIL", m2,
                              time.strftime("%F %T")])
    print("repair done", flush=True)


if __name__ == "__main__":
    main()
