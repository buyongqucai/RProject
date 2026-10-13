# -*- coding: utf-8 -*-
"""Build compound-target / HCTP network contracts for UC atlas (skill schema).

Shared chemical names across ≥2 herbs → compound_id = same1, same2, ...
Herb-unique compounds → {herb_code}{n} (BX1, HQ2, ...).
"""
from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd

PREP = Path(r"D:/网络药理学文件/准备文件")
DATA = Path(r"E:/RProject/努力学习项目/网络药理学/数据文件")
TAB = Path(r"E:/RProject/努力学习项目/网络药理学/代码文件/结果文件/数据文件")
LOG = Path(r"E:/RProject/debug-360a4e.log")
DATA.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

HERB_META = [
    ("半夏", "Ban Xia", "BX"),
    ("茯苓", "Fu Ling", "FL"),
    ("木香", "Mu Xiang", "MX"),
    ("黄连", "Huang Lian", "HL"),
    ("干姜", "Gan Jiang", "GJ"),
    ("淫羊藿", "Yin Yang Huo", "YYH"),
    ("黄芩", "Huang Qin", "HQ"),
    ("肉桂", "Rou Gui", "RG"),
    ("人参", "Ren Shen", "RS"),
    ("白术", "Bai Zhu", "BZ"),
    ("香附", "Xiang Fu", "XF"),
    ("棕榈炭", "Zong Lv Tan", "ZLT"),
]


def _dbg(hid: str, loc: str, msg: str, data: dict, run_id: str = "post-fix") -> None:
    # #region agent log
    payload = {
        "sessionId": "360a4e",
        "runId": run_id,
        "hypothesisId": hid,
        "location": loc,
        "message": msg,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    # #endregion


def norm_gene(x) -> str | None:
    if pd.isna(x):
        return None
    s = str(x).strip()
    if not s or s.lower() in {"nan", "none", "gene", "value", "key"}:
        return None
    for part in re.split(r"[;/,|]", s):
        p = part.strip()
        if p and re.match(r"^[A-Za-z0-9][A-Za-z0-9\-_@\.]*$", p):
            return p
    return None


def norm_cpd_name(s: str) -> str:
    s = str(s).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def norm_cpd_key(s: str) -> str:
    return norm_cpd_name(s).lower()


def extract_baishu_like(xlsx: Path) -> list[tuple[str, str]]:
    df = pd.read_excel(xlsx, header=None)
    if df.shape[1] < 5:
        return []
    out = []
    for _, r in df.iloc[1:].iterrows():
        cpd = r.iloc[2]
        gene = norm_gene(r.iloc[4])
        if pd.isna(cpd) or not gene:
            continue
        name = norm_cpd_name(cpd)
        if not name or name.lower().startswith("unnamed"):
            continue
        out.append((name, gene))
    return out


def extract_xiangfu(xlsx: Path) -> list[tuple[str, str]]:
    df = pd.read_excel(xlsx, header=None)
    out = []
    for _, r in df.iloc[1:].iterrows():
        cpd = r.iloc[0]
        gene = norm_gene(r.iloc[1])
        if pd.isna(cpd) or not gene:
            continue
        name = norm_cpd_name(cpd)
        if name.lower() in {"key", "value"}:
            continue
        out.append((name, gene))
    return out


def extract_zlt() -> list[tuple[str, str]]:
    xlsx = PREP / "棕榈炭" / "棕榈炭靶点基因.xlsx"
    df = pd.read_excel(xlsx, sheet_name="整合靶点")
    out = []
    for _, r in df.iterrows():
        cpd = r.get("成分")
        gene = norm_gene(r.get("Gene Names (primary)"))
        if pd.isna(cpd) or not gene:
            continue
        out.append((norm_cpd_name(cpd), gene))
    return out


ov = set(
    pd.read_csv(DATA / "药物疾病交集_DrugDiseaseOverlap.csv", encoding="utf-8-sig")["gene"]
    .astype(str)
    .str.strip()
)

# Pass 1: collect per-herb compound lists + edges
herb_compounds: dict[str, list[str]] = {}  # code -> ordered unique display names
herb_meta = {code: (zh, en) for zh, en, code in HERB_META}
pairs_by_herb: dict[str, list[tuple[str, str]]] = {}

for zh, en, code in HERB_META:
    if zh == "棕榈炭":
        pairs = extract_zlt()
    elif zh == "香附":
        p = PREP / "香附靶点基因.xlsx"
        pairs = extract_xiangfu(p) if p.exists() else []
    else:
        p = PREP / f"{zh}靶点基因.xlsx"
        pairs = extract_baishu_like(p) if p.exists() else []
    pairs_by_herb[code] = pairs
    compounds: list[str] = []
    seen: set[str] = set()
    for cpd, _ in pairs:
        k = norm_cpd_key(cpd)
        if k not in seen:
            seen.add(k)
            compounds.append(cpd)
    herb_compounds[code] = compounds

# Pass 2: which chemical keys appear in ≥2 herbs → sameN
key_to_herbs: dict[str, list[str]] = defaultdict(list)
key_to_display: dict[str, str] = {}
for code, compounds in herb_compounds.items():
    for cpd in compounds:
        k = norm_cpd_key(cpd)
        if code not in key_to_herbs[k]:
            key_to_herbs[k].append(code)
        key_to_display.setdefault(k, cpd)

shared_keys = sorted([k for k, hs in key_to_herbs.items() if len(hs) >= 2])
same_map = {k: f"same{i+1}" for i, k in enumerate(shared_keys)}

_dbg(
    "A",
    "05_build_compound_hctp_contracts.py:same_map",
    "assigned sameN for multi-herb chemicals",
    {
        "n_shared_keys": len(shared_keys),
        "same_map_sample": [
            {"key": k, "id": same_map[k], "display": key_to_display[k], "herbs": key_to_herbs[k]}
            for k in shared_keys[:12]
        ],
    },
)

# Pass 3: per-herb unique IDs + rows
rows = []
rename_rows = []
hc_rows = []
for zh, en, code in HERB_META:
    compounds = herb_compounds.get(code, [])
    uniq = [c for c in compounds if norm_cpd_key(c) not in same_map]
    cpd2id: dict[str, str] = {}
    for i, cpd in enumerate(uniq):
        cpd2id[norm_cpd_key(cpd)] = f"{code}{i+1}"
    for cpd in compounds:
        k = norm_cpd_key(cpd)
        cid = same_map[k] if k in same_map else cpd2id[k]
        share_count = len(key_to_herbs[k])
        rename_rows.append(
            {
                "compound_name": key_to_display[k],
                "compound_id": cid,
                "herb_code": code,
                "herb": en,
                "herb_zh": zh,
                "share_count": share_count,
            }
        )
        hc_rows.append({"herb_code": code, "compound_id": cid, "herb": en, "herb_zh": zh})
    for cpd, gene in pairs_by_herb.get(code, []):
        k = norm_cpd_key(cpd)
        cid = same_map[k] if k in same_map else cpd2id[k]
        rows.append(
            {
                "herb": en,
                "herb_zh": zh,
                "herb_code": code,
                "compound_id": cid,
                "compound_name": key_to_display[k],
                "target_gene": gene,
            }
        )

ct = pd.DataFrame(rows).drop_duplicates()
ct.to_csv(DATA / "药物成分靶点_CompoundTargets.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(rename_rows).to_csv(DATA / "成分重命名_CompoundRenameMap.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(hc_rows).drop_duplicates().to_csv(
    DATA / "草药成分边_HerbCompoundEdges.csv", index=False, encoding="utf-8-sig"
)

ct_ov = ct[ct["target_gene"].isin(ov)].copy()
n_same = ct["compound_id"].astype(str).str.startswith("same").sum()
print(
    "compound edges",
    len(ct),
    "overlap edges",
    len(ct_ov),
    "compounds",
    ct["compound_id"].nunique(),
    "sameN_ids",
    ct["compound_id"].astype(str).str.match(r"^same\d+$").sum(),
)

net_ab = (
    ct_ov[["herb_code", "compound_id"]]
    .drop_duplicates()
    .rename(columns={"herb_code": "from", "compound_id": "to"})
)
net_bc = (
    ct_ov[["compound_id", "target_gene"]]
    .drop_duplicates()
    .rename(columns={"compound_id": "from", "target_gene": "to"})
)

kegg_path = DATA / "富集KEGG_TopPathways.csv"
net_cd_rows = []
pathway_nodes = []
if kegg_path.exists():
    kegg = pd.read_csv(kegg_path, encoding="utf-8-sig")
    if "pvalue" in kegg.columns:
        kegg = kegg.sort_values("pvalue").head(20)
    for _, r in kegg.iterrows():
        pid = str(r.get("ID", "")).strip()
        if not pid.startswith("hsa"):
            continue
        genes = str(r.get("geneID", "")).replace(";", "/").split("/")
        for g in genes:
            g = g.strip()
            if g in ov:
                net_cd_rows.append({"from": g, "to": pid})
        pathway_nodes.append(pid)

net_cd = pd.DataFrame(net_cd_rows).drop_duplicates() if net_cd_rows else pd.DataFrame(columns=["from", "to"])

net = pd.concat(
    [
        net_ab.rename(columns={"from": "ID", "to": "SYMBOL"}),
        net_bc.rename(columns={"from": "ID", "to": "SYMBOL"}),
        net_cd.rename(columns={"from": "ID", "to": "SYMBOL"}),
    ],
    ignore_index=True,
).drop_duplicates()
net.to_csv(DATA / "网络边_network.csv", index=False, encoding="utf-8-sig")
net.to_csv(TAB / "17_网络边_network.csv", index=False, encoding="utf-8-sig")

type_rows = []
for zh, en, code in HERB_META:
    # Keep all formula herbs in type table (even if 0 targets / no AB edges)
    type_rows.append({"term": code, "type": "A"})
for cid in sorted(set(net_ab["to"]) | set(net_bc["from"])):
    type_rows.append({"term": cid, "type": "B"})
for g in sorted(set(net_bc["to"]) | set(net_cd["from"] if len(net_cd) else [])):
    type_rows.append({"term": g, "type": "C"})
for p in sorted(set(pathway_nodes)):
    type_rows.append({"term": p, "type": "D"})
type_df = pd.DataFrame(type_rows).drop_duplicates(subset=["term"], keep="first")
type_df.to_csv(DATA / "网络节点类型_type.csv", index=False, encoding="utf-8-sig")
type_df.to_csv(TAB / "18_网络节点类型_type.csv", index=False, encoding="utf-8-sig")

same_in_net = sorted({t for t in type_df.loc[type_df["type"] == "B", "term"].astype(str) if t.startswith("same")})
_dbg(
    "A",
    "05_build_compound_hctp_contracts.py:network",
    "network B nodes include sameN",
    {
        "n_B": int((type_df["type"] == "B").sum()),
        "n_same_in_B": len(same_in_net),
        "same_ids": same_in_net,
        "n_AB_edges_to_same": int(net_ab["to"].astype(str).str.startswith("same").sum()),
    },
)

print("network edges", len(net), "nodes", len(type_df), "CD", len(net_cd), "sameB", same_in_net)
print("done")
