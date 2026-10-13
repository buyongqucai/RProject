# -*- coding: utf-8 -*-
"""Download ALL KEGG pathway maps from 交付 KEGG.csv (rank 01..N).

Source: 交付文件/数据/富集分析/KEGG.csv
REST: https://rest.kegg.jp/get/{hsaXXXXX}/image
"""
from __future__ import annotations

import re
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")
KEGG_CSV = ROOT / "交付文件" / "数据" / "富集分析" / "KEGG.csv"
OUT_DELIV = ROOT / "交付文件" / "图片" / "KEGG官方通路图"
OUT_CACHE = ROOT / "代码文件" / "结果文件" / "图片文件" / "KEGG官方通路图"
OUT_DB = Path(r"D:/数据库/KEGG数据库/KEGG通路图")
TIMEOUT = 180
RETRIES = 4
SLEEP = 0.65


def safe_name(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", str(s), flags=re.UNICODE)
    return s.strip("_")[:80] or "pathway"


def is_good_png(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 1000:
        return False
    return path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def fetch_png(url: str) -> bytes:
    last_err: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "RProject-NetPharm/1.0 (academic)"}
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
            if data.startswith(b"\x89PNG") and len(data) > 1000:
                return data
            raise RuntimeError(f"unexpected payload bytes={len(data)}")
        except (TimeoutError, urllib.error.URLError, RuntimeError, OSError) as e:
            last_err = e
            wait = 2.0 * attempt
            print(f"RETRY {attempt}/{RETRIES} after {e!r}; sleep {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"failed {url}: {last_err}")


def main() -> None:
    kegg = pd.read_csv(KEGG_CSV, encoding="utf-8-sig")
    if "pvalue" in kegg.columns:
        kegg = kegg.sort_values("pvalue", kind="mergesort").reset_index(drop=True)
    id_col = "ID" if "ID" in kegg.columns else "id"
    desc_col = "Description" if "Description" in kegg.columns else "term"

    for d in (OUT_DELIV, OUT_CACHE, OUT_DB):
        d.mkdir(parents=True, exist_ok=True)

    rows = []
    n_get = 0
    for i, r in enumerate(kegg.itertuples(index=False), start=1):
        pid = str(getattr(r, id_col)).strip()
        desc = str(getattr(r, desc_col, "")).strip()
        if not pid.startswith("hsa"):
            print("SKIP", pid)
            continue
        url = f"https://rest.kegg.jp/get/{pid}/image"
        fname = f"{i:03d}_{pid}_{safe_name(desc)}.png" if len(kegg) > 99 else f"{i:02d}_{pid}_{safe_name(desc)}.png"
        # keep 3-digit for full set clarity
        fname = f"{i:03d}_{pid}_{safe_name(desc)}.png"
        cache_path = OUT_CACHE / fname
        deliv_path = OUT_DELIV / fname

        # also accept old Top20 2-digit filenames for ranks 1-20
        old2 = OUT_DELIV / f"{i:02d}_{pid}_{safe_name(desc)}.png"
        old2_alt = None
        for p in OUT_DELIV.glob(f"{i:02d}_{pid}_*.png"):
            old2_alt = p
            break

        if is_good_png(cache_path):
            print("HAVE", fname)
        elif old2_alt and is_good_png(old2_alt):
            print("MIGRATE", old2_alt.name, "->", fname)
            shutil.copy2(old2_alt, cache_path)
        elif is_good_png(deliv_path):
            shutil.copy2(deliv_path, cache_path)
            print("HAVE deliv", fname)
        else:
            print("GET", f"{i}/{len(kegg)}", pid)
            data = fetch_png(url)
            cache_path.write_bytes(data)
            n_get += 1
            time.sleep(SLEEP)

        shutil.copy2(cache_path, deliv_path)
        shutil.copy2(cache_path, OUT_DB / fname)

        rows.append(
            {
                "rank": i,
                "pathway_id": pid,
                "description": desc,
                "file": fname,
                "url": url,
            }
        )

    meta = pd.DataFrame(rows)
    for dest in (OUT_DELIV, OUT_CACHE, OUT_DB.parent / "映射表" if False else OUT_DELIV):
        pass
    meta.to_csv(OUT_DELIV / "00_全部通路图清单.csv", index=False, encoding="utf-8-sig")
    meta.to_csv(OUT_CACHE / "00_全部通路图清单.csv", index=False, encoding="utf-8-sig")
    # keep Top20 slice for compatibility
    meta.head(20).to_csv(OUT_DELIV / "00_Top20通路图清单.csv", index=False, encoding="utf-8-sig")

    # remove obsolete 2-digit Top20 files that were migrated
    for p in OUT_DELIV.glob("0[0-9]_hsa*.png"):
        # if a 3-digit equivalent exists, drop 2-digit
        m = re.match(r"^(\d{2})_(hsa\d+)_", p.name)
        if not m:
            continue
        rank = int(m.group(1))
        pid = m.group(2)
        newer = list(OUT_DELIV.glob(f"{rank:03d}_{pid}_*.png"))
        if newer:
            p.unlink()
            print("RM old", p.name)

    (OUT_DELIV / "README.txt").write_text(
        f"KEGG 官方通路图（REST /get/{{id}}/image）。\n"
        f"来源：交付文件/数据/富集分析/KEGG.csv，共 {len(meta)} 条，按 pvalue 排序，编号 001 起。\n"
        f"清单：00_全部通路图清单.csv\n"
        f"仅学术用途；请遵守 KEGG 使用条款 https://www.kegg.jp/kegg/legal.html\n",
        encoding="utf-8",
    )
    print("DONE maps=", len(meta), "downloaded_new=", n_get, "->", OUT_DELIV)


if __name__ == "__main__":
    main()
