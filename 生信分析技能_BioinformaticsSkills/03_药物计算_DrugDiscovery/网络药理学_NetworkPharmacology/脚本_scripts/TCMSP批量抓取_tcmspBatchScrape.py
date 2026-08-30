# -*- coding: utf-8 -*-
"""TCMSP 批量抓取：参数表格 + 有效成分靶点表格（对齐既有模板格式）。

链路（无需登录，2026-08-31 验证）：
  tcmsp.php 取 token
  → tcmspsearch.php?qs=herb_all_name&q={拼音}&token=        搜草药得拉丁名
  → tcmspsearch.php?qr={拉丁名}&qsr=herb_en_name&token=     成分 JSON（kendoGrid 内嵌）
  → molecule.php?qn={molecule_ID}                           每成分靶点 + ADME（tpsa）

模板约定（与 TCMSP羌活/秦艽 参考表逐项核对）：
  参数表格：13 列 [Mol ID, Molecule Name, MW, AlogP, Hdon, Hacc, OB, Caco-2, BBB,
                   DL, FASA-(实为 tpsa), HL, Save(空)]；筛选 OB>=30 且 DL>=0.18；数值 2 位小数。
  靶点表格：无表头，2 列 [成分名, 靶点名]；按参数表格行序逐成分展开。

用法：
  python TCMSP批量抓取_tcmspBatchScrape.py --pilot 羌活 --out <临时目录>   # 试点
  python TCMSP批量抓取_tcmspBatchScrape.py --all --out "D:\\数据库\\药物数据库\\准备文件"
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import time
from pathlib import Path

import requests
from openpyxl import Workbook

BASE = "https://www.tcmsp-e.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

PARAM_HEADER = ["Mol ID", "Molecule Name", "MW", "AlogP", "Hdon", "Hacc",
                "OB", "Caco-2", "BBB", "DL", "FASA-", "HL", "Save"]
OB_MIN, DL_MIN = 30.0, 0.18


def new_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    return s


def get_token(s: requests.Session) -> str:
    r = s.get(f"{BASE}/tcmsp.php", timeout=60)
    r.raise_for_status()
    m = re.search(r'name="token" value="([a-f0-9]+)"', r.text)
    if not m:
        raise RuntimeError("token not found on tcmsp.php")
    return m.group(1)


def extract_grids(html: str) -> list[list[dict]]:
    """返回页面中全部 kendoGrid data JSON 块（按出现顺序）。"""
    grids = []
    for m in re.finditer(r"(?:var\s+\w+\s*=|data:\s*)\s*(\[\{.*?\}\])", html, re.S):
        try:
            grids.append(json.loads(m.group(1)))
        except json.JSONDecodeError:
            continue
    return grids


def pick_grid(grids: list[list[dict]], key: str) -> list[dict]:
    for g in grids:
        if g and key in g[0]:
            return g
    return []


def list_all_herbs(s: requests.Session) -> list[dict]:
    r = s.get(f"{BASE}/browse.php?qc=herbs", timeout=60)
    r.raise_for_status()
    return pick_grid(extract_grids(r.text), "herb_cn_name")


def search_latin(s: requests.Session, token: str, pinyin: str) -> str | None:
    r = s.get(f"{BASE}/tcmspsearch.php",
              params={"qs": "herb_all_name", "q": pinyin, "token": token},
              timeout=60)
    r.raise_for_status()
    rows = pick_grid(extract_grids(r.text), "herb_en_name")
    if not rows:
        return None
    for row in rows:
        if row.get("herb_pinyin", "").lower() == pinyin.lower():
            return row["herb_en_name"]
    return rows[0]["herb_en_name"]


def herb_ingredients(s: requests.Session, token: str, latin: str) -> list[dict]:
    r = s.get(f"{BASE}/tcmspsearch.php",
              params={"qr": latin, "qsr": "herb_en_name", "token": token},
              timeout=120)
    r.raise_for_status()
    return pick_grid(extract_grids(r.text), "molecule_ID")


def molecule_adme_targets(s: requests.Session, molecule_id: str) -> tuple[dict, list[str]]:
    r = s.get(f"{BASE}/molecule.php", params={"qn": molecule_id}, timeout=60)
    r.raise_for_status()
    grids = extract_grids(r.text)
    adme = pick_grid(grids, "pubchem_cid")
    targets = [row["target_name"] for row in pick_grid(grids, "target_name")
               if row.get("target_name")]
    return (adme[0] if adme else {}), targets


def polite(lo=0.6, hi=1.4):
    time.sleep(random.uniform(lo, hi))


def fnum(v, nd=2):
    """数值两位小数；空串/None → None。"""
    if v is None or v == "":
        return None
    try:
        return round(float(v), nd)
    except ValueError:
        return None


def scrape_herb(s: requests.Session, token: str, cn: str, pinyin: str,
                out_dir: Path, log: dict) -> dict:
    latin = search_latin(s, token, pinyin)
    if not latin:
        log.update(status="NOT_FOUND", note="search empty")
        return log
    polite()
    ingredients = herb_ingredients(s, token, latin)
    log["n_ingredients"] = len(ingredients)
    if not ingredients:
        log.update(status="NO_INGREDIENTS", note=latin)
        return log

    filtered = [g for g in ingredients
                if (fnum(g.get("ob"), 99) or 0) >= OB_MIN
                and (fnum(g.get("dl"), 99) or 0) >= DL_MIN]
    log["n_filtered"] = len(filtered)

    param_rows, edge_rows = [], []
    for g in filtered:
        polite()
        adme, targets = molecule_adme_targets(s, g["molecule_ID"])
        src = {**g, **adme}  # molecule 页补 tpsa
        param_rows.append([
            g.get("MOL_ID"), g.get("molecule_name"), fnum(src.get("mw")),
            fnum(src.get("alogp")), int(float(src.get("hdon") or 0)),
            int(float(src.get("hacc") or 0)), fnum(src.get("ob")),
            fnum(src.get("caco2")), fnum(src.get("bbb")), fnum(src.get("dl")),
            fnum(src.get("tpsa")), fnum(src.get("halflife")), None,
        ])
        for t in targets:
            edge_rows.append([g.get("molecule_name"), t])
    log["n_pairs"] = len(edge_rows)

    wb = Workbook()
    ws = wb.active
    ws.append(PARAM_HEADER)
    for row in param_rows:
        ws.append(row)
    wb.save(out_dir / f"TCMSP{cn}参数表格.xlsx")

    wb2 = Workbook()  # 靶点表格：无表头
    ws2 = wb2.active
    for row in edge_rows:
        ws2.append(row)
    wb2.save(out_dir / f"TCMSP{cn}有效成分靶点表格.xlsx")

    log.update(status="OK", note=latin)
    return log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", nargs="*", default=None,
                    help="试点药味（中文名+拼音，如 羌活 Qianghuo）；缺省只跑这些")
    ap.add_argument("--all", action="store_true", help="browse 全清单补缺")
    ap.add_argument("--out", required=True)
    ap.add_argument("--log", default=None, help="进度 CSV（默认 <out>/_tcmsp_scrape_log.csv）")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = Path(args.log) if args.log else out_dir / "_tcmsp_scrape_log.csv"

    s = new_session()
    token = get_token(s)
    print(f"[token] {token}", flush=True)

    if args.all:
        herbs = list_all_herbs(s)
        print(f"[browse] {len(herbs)} herbs", flush=True)
        todo = []
        for h in herbs:
            cn = h["herb_cn_name"]
            if (out_dir / f"TCMSP{cn}参数表格.xlsx").exists() and \
               (out_dir / f"TCMSP{cn}有效成分靶点表格.xlsx").exists():
                continue
            todo.append((cn, h["herb_pinyin"]))
    else:
        pairs = args.pilot or []
        todo = [(pairs[i], pairs[i + 1]) for i in range(0, len(pairs) - 1, 2)]

    print(f"[todo] {len(todo)} herbs", flush=True)
    write_header = not log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        if write_header:
            w.writerow(["herb_cn", "pinyin", "status", "n_ingredients",
                        "n_filtered", "n_pairs", "note", "ts"])
        for i, (cn, pinyin) in enumerate(todo, 1):
            log = {"n_ingredients": 0, "n_filtered": 0, "n_pairs": 0,
                   "status": "ERROR", "note": ""}
            try:
                log = scrape_herb(s, token, cn, pinyin, out_dir, log)
            except Exception as e:  # 单味失败不中断批次
                log["note"] = f"{type(e).__name__}: {e}"[:200]
            w.writerow([cn, pinyin, log["status"], log["n_ingredients"],
                        log["n_filtered"], log["n_pairs"], log["note"],
                        time.strftime("%F %T")])
            fh.flush()
            print(f"[{i}/{len(todo)}] {cn} {log['status']} "
                  f"ing={log['n_ingredients']} filt={log['n_filtered']} "
                  f"pairs={log['n_pairs']}", flush=True)
            polite(1.0, 2.0)


if __name__ == "__main__":
    sys.exit(main())
