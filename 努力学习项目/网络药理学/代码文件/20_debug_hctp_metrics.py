# -*- coding: utf-8 -*-
"""Debug HCTP: shared compounds, label/canvas metrics → debug-360a4e.log"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd

LOG = Path(r"E:/RProject/debug-360a4e.log")
SESSION = "360a4e"
DATA = Path(r"E:/RProject/努力学习项目/网络药理学/数据文件")
FIG = Path(r"E:/RProject/努力学习项目/网络药理学/代码文件/结果文件/图片文件")
DELIV = Path(r"E:/RProject/努力学习项目/网络药理学/交付文件/图片/网络图")


def log(hypothesis_id: str, location: str, message: str, data: dict, run_id: str = "pre-fix") -> None:
    payload = {
        "sessionId": SESSION,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def norm_name(s: str) -> str:
    s = str(s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def main() -> None:
    run_id = "post-fix" if "--post-fix" in sys.argv else "pre-fix"
    rm = pd.read_csv(DATA / "成分重命名_CompoundRenameMap.csv", encoding="utf-8-sig")
    typ = pd.read_csv(DATA / "网络节点类型_type.csv", encoding="utf-8-sig")

    herb_col = "herb_zh" if "herb_zh" in rm.columns else "herb"
    by_name = rm.groupby(rm["compound_name"].map(norm_name)).agg(
        n_herbs=(herb_col, "nunique"),
        ids=("compound_id", lambda x: sorted(set(map(str, x)))),
        herbs=(herb_col, lambda x: sorted(set(map(str, x)))),
    )
    shared = by_name[by_name["n_herbs"] > 1]
    same_ids = sorted({str(i) for i in rm["compound_id"].astype(str) if str(i).lower().startswith("same")})
    log(
        "A",
        "20_debug_hctp_metrics.py:shared",
        "shared chemicals vs same* IDs",
        {
            "n_rename_rows": int(len(rm)),
            "n_unique_chem_names": int(rm["compound_name"].map(norm_name).nunique()),
            "n_shared_chem_names": int(len(shared)),
            "shared_examples": [
                {"name": n, "n_herbs": int(r.n_herbs), "ids": r.ids, "herbs": r.herbs}
                for n, r in shared.head(12).iterrows()
            ],
            "n_same_star_ids": len(same_ids),
            "same_star_sample": same_ids[:20],
        },
        run_id=run_id,
    )

    name_to_ids: dict[str, set[str]] = defaultdict(set)
    for _, r in rm.iterrows():
        name_to_ids[norm_name(r["compound_name"])].add(str(r["compound_id"]))
    # After fix: shared chem should map to exactly one sameN id
    multi_id_chems = {n: ids for n, ids in name_to_ids.items() if len(ids) > 1}
    b_nodes = set(typ.loc[typ["type"] == "B", "term"].astype(str))
    same_in_b = sorted(x for x in b_nodes if x.startswith("same"))
    log(
        "B",
        "20_debug_hctp_metrics.py:topology",
        "chemically-same ID collapse check",
        {
            "n_B_nodes": len(b_nodes),
            "n_chem_with_multiple_ids": len(multi_id_chems),
            "n_same_in_B": len(same_in_b),
            "same_in_B": same_in_b,
            "multi_id_examples": [
                {"name": n, "ids": sorted(ids)} for n, ids in list(multi_id_chems.items())[:8]
            ],
        },
        run_id=run_id,
    )

    for stem, tag in [
        ("11_网络图_HerbCompoundTargetPathway_Network", "columns"),
        ("12_网络图_HerbCompoundTargetPathway_Ellipse_Network", "ellipse"),
    ]:
        svg = FIG / f"{stem}.svg"
        png = FIG / f"{stem}.png"
        if not svg.exists():
            log("C", f"missing:{tag}", "svg missing", {"path": str(svg)}, run_id=run_id)
            continue
        text = svg.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"viewBox='([^']+)'", text) or re.search(r'viewBox="([^"]+)"', text)
        vb = m.group(1) if m else ""
        w_m = re.search(r"width='([0-9.]+)pt'", text) or re.search(r'width="([0-9.]+)pt"', text)
        h_m = re.search(r"height='([0-9.]+)pt'", text) or re.search(r'height="([0-9.]+)pt"', text)
        genes = re.findall(r">([A-Z][A-Z0-9\-]{1,12})<", text)
        hsas = re.findall(r">(hsa[0-9]+)<", text)
        comps = re.findall(r">((?:same)?[A-Z]{1,4}\d+|same\d+)<", text, flags=re.I)
        same_labs = sorted({c for c in comps if str(c).lower().startswith("same")})
        log(
            "C",
            f"20_debug_hctp_metrics.py:svg:{tag}",
            "svg canvas and label inventory",
            {
                "mode": tag,
                "svg_bytes": svg.stat().st_size,
                "png_bytes": png.stat().st_size if png.exists() else 0,
                "viewBox": vb,
                "width_pt": float(w_m.group(1)) if w_m else None,
                "height_pt": float(h_m.group(1)) if h_m else None,
                "n_unique_gene_like": len(set(genes)),
                "n_hsa": len(set(hsas)),
                "n_unique_compound_like": len(set(comps)),
                "has_same_labels": bool(same_labs),
                "same_labels": same_labs,
                "compound_sample": sorted(set(comps))[:30],
            },
            run_id=run_id,
        )
        if w_m and h_m:
            area = float(w_m.group(1)) * float(h_m.group(1))
            n_lab = len(set(genes)) + len(set(hsas)) + len(set(comps))
            log(
                "D",
                f"20_debug_hctp_metrics.py:density:{tag}",
                "label density vs canvas",
                {
                    "mode": tag,
                    "canvas_pt2": area,
                    "approx_unique_labels": n_lab,
                    "labels_per_1000pt2": n_lab / (area / 1000.0),
                    "png_mb": (png.stat().st_size / 1e6) if png.exists() else 0,
                },
                run_id=run_id,
            )

    for name in [
        "药物有效成分疾病靶点通路网络图.svg",
        "药物有效成分疾病靶点通路网络图_椭圆布局.svg",
    ]:
        p = DELIV / name
        log(
            "E",
            "20_debug_hctp_metrics.py:delivery",
            "delivery svg present",
            {"name": name, "exists": p.exists(), "bytes": p.stat().st_size if p.exists() else 0},
            run_id=run_id,
        )

    print("OK wrote", LOG, "run_id=", run_id)


if __name__ == "__main__":
    main()
