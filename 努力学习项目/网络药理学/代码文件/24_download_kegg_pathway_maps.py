# -*- coding: utf-8 -*-
"""Download KEGG official pathway map PNGs (Top20 by enrichment p-value).

Uses KEGG REST: https://rest.kegg.jp/get/{hsaXXXXX}/image
Rate-limit ~2 req/s (academic use). Writes under 交付文件/图片/KEGG官方通路图/
and mirrors to 代码文件/结果文件/图片文件/KEGG官方通路图/.
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
DATA = ROOT / "数据文件"
OUT_DELIV = ROOT / "交付文件" / "图片" / "KEGG官方通路图"
OUT_CACHE = ROOT / "代码文件" / "结果文件" / "图片文件" / "KEGG官方通路图"
KEGG_CSV = DATA / "富集KEGG_TopPathways.csv"
TOP_N = 20
TIMEOUT = 180
RETRIES = 4


def safe_name(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", str(s), flags=re.UNICODE)
    return s.strip("_")[:60] or "pathway"


def is_good_png(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 1000:
        return False
    head = path.read_bytes()[:8]
    return head == b"\x89PNG\r\n\x1a\n"


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
    if "Desktop" in str(OUT_DELIV) or "桌面" in str(OUT_DELIV):
        raise SystemExit("Refusing Desktop path")
    kegg = pd.read_csv(KEGG_CSV, encoding="utf-8-sig")
    if "pvalue" in kegg.columns:
        kegg = kegg.sort_values("pvalue")
    kegg = kegg.head(TOP_N)
    id_col = "ID" if "ID" in kegg.columns else "id"
    desc_col = "Description" if "Description" in kegg.columns else "term"
    OUT_DELIV.mkdir(parents=True, exist_ok=True)
    OUT_CACHE.mkdir(parents=True, exist_ok=True)

    rows = []
    for i, r in enumerate(kegg.itertuples(index=False), start=1):
        pid = str(getattr(r, id_col)).strip()
        desc = str(getattr(r, desc_col, "")).strip()
        if not pid.startswith("hsa"):
            print("SKIP bad id", pid)
            continue
        url = f"https://rest.kegg.jp/get/{pid}/image"
        fname = f"{i:02d}_{pid}_{safe_name(desc)}.png"
        cache_path = OUT_CACHE / fname
        deliv_path = OUT_DELIV / fname

        if is_good_png(cache_path):
            print("HAVE cache", fname)
        elif is_good_png(deliv_path):
            print("HAVE deliv -> cache", fname)
            shutil.copy2(deliv_path, cache_path)
        else:
            print("GET", url, "->", fname)
            data = fetch_png(url)
            cache_path.write_bytes(data)
            time.sleep(0.7)

        if not is_good_png(deliv_path) or deliv_path.stat().st_size != cache_path.stat().st_size:
            shutil.copy2(cache_path, deliv_path)
            print("COPY", fname, "-> delivery")

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
    meta.to_csv(OUT_DELIV / "00_Top20通路图清单.csv", index=False, encoding="utf-8-sig")
    meta.to_csv(OUT_CACHE / "00_Top20通路图清单.csv", index=False, encoding="utf-8-sig")
    (OUT_DELIV / "README.txt").write_text(
        "KEGG 官方通路图（REST /get/{id}/image）。\n"
        "来源：富集KEGG_TopPathways.csv 按 pvalue 排序 Top20。\n"
        "仅学术用途；请遵守 KEGG 使用条款 https://www.kegg.jp/kegg/legal.html\n",
        encoding="utf-8",
    )
    print("DONE", len(rows), "maps ->", OUT_DELIV)


if __name__ == "__main__":
    main()
