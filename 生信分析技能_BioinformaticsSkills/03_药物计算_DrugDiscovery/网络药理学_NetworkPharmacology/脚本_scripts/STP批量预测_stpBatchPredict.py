# -*- coding: utf-8 -*-
"""STP批量预测_stpBatchPredict.py
SwissTargetPrediction 批量提交（locate → predict → result 解析）。

输入 CSV 列：name_en,name_zh,source[,cid,smiles]
  - 若缺 cid/smiles，脚本先查 PubChem PUG 补齐（按英文名）。
输出（按 CompoundTargetSOP §4）：
  - {outdir}/{name_en}_Swiss预测靶点_筛选前.csv   STP 原始返回
  - {outdir}/{name_en}_Swiss预测靶点_筛选后.csv   Probability > 0
  - {outdir}/异常清单_CompoundTargetExceptions.csv（仅在有异常时）
用法：
  python STP批量预测_stpBatchPredict.py 成分表.csv --outdir 输出目录 [--sleep 3]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

import requests
from urllib.parse import quote

STP = "https://www.swisstargetprediction.ch"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

RESULT_COLS = ["Target", "Common name", "Uniprot ID", "ChEMBL ID",
               "Target Class", "Probability", "Known actives (2D/3D)"]


def pubchem_lookup(s: requests.Session, name: str) -> tuple[str, str]:
    """name -> (cid, canonical_smiles)；失败返回 ("","")。"""
    try:
        r = s.get(f"{PUG}/compound/name/{quote(name)}/property/CanonicalSMILES/JSON",
                  timeout=30)
        rec = r.json()["PropertyTable"]["Properties"][0]
        return str(rec["CID"]), rec.get("CanonicalSMILES") or rec.get("ConnectivitySMILES", "")
    except Exception as e:  # noqa: BLE001
        print(f"  pubchem_lookup({name}) 异常: {e}", flush=True)
        return "", ""


def stp_predict(s: requests.Session, smiles: str) -> list[dict]:
    """提交单个 SMILES，返回 STP 结果行（dict 列表）。

    实测流程（2026-08-31）：predict.php 响应内嵌轮询日志，末尾
    location.replace(".../result.php?job=...&organism=...") 即结果地址；
    必须带 Referer，否则静默返回表单页。locate.php 只是点击埋点，无需调用。
    """
    home = STP + "/"
    s.get(home, headers=UA, timeout=30)
    r = s.post(
        STP + "/predict.php",
        data={"organism": "Homo_sapiens", "smiles": smiles, "ioi": "2", "Example": ""},
        headers={**UA, "Referer": home, "Origin": STP},
        timeout=180,
    )
    m = re.search(r'result\.php\?job=(\d+)&(?:amp;)?organism=([\w]+)', r.text)
    if not m:
        raise RuntimeError("predict.php 未返回 job id")
    url = f"{STP}/result.php?job={m.group(1)}&organism={m.group(2)}"
    for _ in range(20):
        html = s.get(url, headers={**UA, "Referer": home}, timeout=60).text
        rows = parse_result_table(html)
        if rows:
            return rows
        if "still running" in html or "queue" in html.lower():
            time.sleep(3)
            continue
        return rows
    raise RuntimeError("STP 结果轮询超时")


def parse_result_table(html: str) -> list[dict]:
    """解析 STP result 页的结果表（无 bs4 依赖，用正则）。"""
    rows: list[dict] = []
    # 结果行为 <tr ...><td>Target</td>...<td>prob</td>...</tr>
    tbody = re.search(r'<table[^>]*id="resultTable"[^>]*>(.*?)</table>', html, re.S)
    block = tbody.group(1) if tbody else html
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", block, re.S):
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(cells) < 6:
            continue
        # STP 列序：Target / Common name / Uniprot ID / ChEMBL ID / Target Class / Probability / Known actives
        row = dict(zip(RESULT_COLS, cells[:7])) if len(cells) >= 7 else dict(zip(RESULT_COLS[:6], cells[:6]))
        rows.append(row)
    return rows


def prob_of(row: dict) -> float:
    try:
        return float(row.get("Probability", "0").replace("*", "").strip() or 0)
    except ValueError:
        return 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("compounds", help="成分表 CSV（name_en,name_zh,source[,cid,smiles]）")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--sleep", type=float, default=3.0, help="化合物间隔秒数（礼貌延时）")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(args.compounds, encoding="utf-8-sig")))
    s = requests.Session()
    s.trust_env = False  # 绕过系统代理（实测代理对 STP 连接不稳定）
    exceptions = []

    for i, rec in enumerate(rows, 1):
        name_en, name_zh = rec["name_en"].strip(), rec.get("name_zh", "").strip()
        cid, smiles = rec.get("cid", "").strip(), rec.get("smiles", "").strip()
        if not (cid and smiles):
            cid2, smi2 = pubchem_lookup(s, name_en)
            cid, smiles = cid or cid2, smiles or smi2
            rec["cid"], rec["smiles"] = cid, smiles
        safe = re.sub(r"[^\w\-]+", "_", name_en)
        pre = outdir / f"{safe}_Swiss预测靶点_筛选前.csv"
        post = outdir / f"{safe}_Swiss预测靶点_筛选后.csv"
        if pre.exists() and post.exists():
            print(f"[{i}/{len(rows)}] {name_en} 已存在，跳过", flush=True)
            continue
        if not smiles:
            exceptions.append({"compound": name_en, "stage": "pubchem", "error": "无 CID/SMILES"})
            print(f"[{i}/{len(rows)}] {name_en} PubChem 未命中", flush=True)
            continue
        try:
            res = stp_predict(s, smiles)
        except Exception as e:  # noqa: BLE001
            exceptions.append({"compound": name_en, "stage": "stp", "error": str(e)[:200]})
            print(f"[{i}/{len(rows)}] {name_en} STP 失败: {e}", flush=True)
            time.sleep(args.sleep)
            continue
        with open(pre, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=RESULT_COLS)
            w.writeheader()
            w.writerows(res)
        kept = [r for r in res if prob_of(r) > 0]
        with open(post, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=RESULT_COLS)
            w.writeheader()
            w.writerows(kept)
        print(f"[{i}/{len(rows)}] {name_en}（{name_zh}）CID={cid} 靶点 {len(res)}→{len(kept)}", flush=True)
        time.sleep(args.sleep)

    # 回填成分表（补 cid/smiles）
    with open(args.compounds, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["name_en", "name_zh", "source", "cid", "smiles"])
        w.writeheader()
        w.writerows(rows)
    if exceptions:
        with open(outdir / "异常清单_CompoundTargetExceptions.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["compound", "stage", "error"])
            w.writeheader()
            w.writerows(exceptions)
    print(f"done: {len(rows)} 成分, {len(exceptions)} 异常", flush=True)


if __name__ == "__main__":
    sys.exit(main())
