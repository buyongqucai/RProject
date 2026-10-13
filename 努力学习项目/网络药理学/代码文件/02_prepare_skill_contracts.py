# -*- coding: utf-8 -*-
"""Rebuild skill contracts in 数据文件/ from D:/网络药理学文件/准备文件.

Writes skill-schema CSVs (herb_zh/herb_en/gene, source/gene). Does not write Desktop.
Keeps 上游_* untouched. Overwrites regenerable contract tables.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

PREP = Path(r"D:/网络药理学文件/准备文件")
DRUG_XLSX = Path(r"D:/网络药理学文件/药物中文名称.xlsx")
ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")
DATA = ROOT / "数据文件"
CTD = DATA / "上游_疾病" / "疾病靶点_CTD_DiseaseGenes.csv"

DISEASE = "Ulcerative Colitis"
GC_REL = 40.0

HERB_META = [
    ("半夏", "Ban Xia", "BanXia"),
    ("茯苓", "Fu Ling", "FuLing"),
    ("木香", "Mu Xiang", "MuXiang"),
    ("黄连", "Huang Lian", "HuangLian"),
    ("干姜", "Gan Jiang", "GanJiang"),
    ("淫羊藿", "Yin Yang Huo", "YinYangHuo"),
    ("黄芩", "Huang Qin", "HuangQin"),
    ("肉桂", "Rou Gui", "RouGui"),
    ("人参", "Ren Shen", "RenShen"),
    ("白术", "Bai Zhu", "BaiZhu"),
    ("香附", "Xiang Fu", "XiangFu"),
    ("棕榈炭", "Zong Lv Tan", "ZongLvTan"),
]


def norm_gene(x) -> str | None:
    if pd.isna(x):
        return None
    s = str(x).strip()
    if not s or s.lower() in {"nan", "none", "null", "gene", "symbol", "value", "key"}:
        return None
    s = re.sub(r"\s+", "", s)
    out = set()
    for part in re.split(r"[;/,|]", s):
        p = part.strip()
        if p and re.match(r"^[A-Za-z0-9][A-Za-z0-9\-_@\.]*$", p):
            out.add(p)
    return next(iter(out)) if len(out) == 1 else None


def uniq_genes(series) -> set[str]:
    out: set[str] = set()
    for v in series:
        if pd.isna(v):
            continue
        s = str(v).strip()
        if not s or s.lower() in {"nan", "none", "gene", "symbol", "value", "key"}:
            continue
        for part in re.split(r"[;/,|]", s):
            p = part.strip()
            if p and re.match(r"^[A-Za-z0-9][A-Za-z0-9\-_@\.]*$", p):
                out.add(p)
    return out


def genes_from_baishu_like(xlsx: Path) -> set[str]:
    df = pd.read_excel(xlsx, header=None)
    if df.shape[1] < 5:
        return set()
    return uniq_genes(df.iloc[1:, 4])


def genes_from_xiangfu(xlsx: Path) -> set[str]:
    df = pd.read_excel(xlsx, header=None)
    return uniq_genes(df.iloc[1:, 1])


def genes_from_zonglvtan() -> set[str]:
    xlsx = PREP / "棕榈炭" / "棕榈炭靶点基因.xlsx"
    integ = pd.read_excel(xlsx, sheet_name="整合靶点")
    gcol = "Gene Names (primary)" if "Gene Names (primary)" in integ.columns else integ.columns[-1]
    genes = uniq_genes(integ[gcol])
    herb = PREP / "棕榈炭" / "HERB_棕榈炭_靶点明细.csv"
    if herb.exists():
        h = pd.read_csv(herb, encoding="utf-8-sig")
        genes |= uniq_genes(h["gene"])
    return genes


def load_disease() -> dict[str, set[str]]:
    if not PREP.exists():
        raise SystemExit(f"Missing prep dir: {PREP}")
    db: dict[str, set[str]] = {}
    gc = pd.read_csv(PREP / "GeneCards Results.csv", encoding="utf-8-sig")
    db["GeneCards_full"] = uniq_genes(gc["Symbol"])
    db["GeneCards"] = uniq_genes(gc.loc[gc["Relevance Score"] >= GC_REL, "Symbol"])

    ttd = pd.read_csv(PREP / "TTD靶点数据.csv", encoding="utf-8-sig", header=None)
    db["TTD"] = uniq_genes(ttd.iloc[:, 0])

    dbank = pd.read_csv(PREP / "Drugbank靶点数据.csv", encoding="utf-8-sig")
    col = "Gene" if "Gene" in dbank.columns else dbank.columns[-1]
    db["DrugBank"] = uniq_genes(dbank[col])

    omim = pd.read_csv(PREP / "OMIM靶点数据.csv", encoding="utf-8-sig", header=None)
    db["OMIM"] = uniq_genes(omim.iloc[:, 0])

    if CTD.exists():
        ctd = pd.read_csv(CTD, encoding="utf-8-sig")
        gcol = "gene" if "gene" in ctd.columns else ctd.columns[0]
        db["CTD"] = uniq_genes(ctd[gcol])
    else:
        db["CTD"] = set()
        print("WARN CTD missing:", CTD)

    db["DisGeNET"] = set()
    return db


def load_herb_genes() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for zh, _en, _code in HERB_META:
        if zh == "棕榈炭":
            out[zh] = genes_from_zonglvtan()
        elif zh == "香附":
            p = PREP / "香附靶点基因.xlsx"
            out[zh] = genes_from_xiangfu(p) if p.exists() else set()
        else:
            p = PREP / f"{zh}靶点基因.xlsx"
            out[zh] = genes_from_baishu_like(p) if p.exists() else set()
    return out


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    db = load_disease()
    herb_genes = load_herb_genes()

    # downstream disease union (filtered GeneCards + others)
    D: set[str] = set()
    for k in ["GeneCards", "TTD", "DrugBank", "OMIM", "CTD"]:
        D |= db.get(k, set())

    # disease_by_db (filtered GeneCards as GeneCards)
    rows = []
    for k in ["GeneCards", "TTD", "DrugBank", "OMIM", "CTD"]:
        for g in sorted(db.get(k, set())):
            rows.append({"source": k, "gene": g})
    pd.DataFrame(rows).to_csv(DATA / "疾病靶点按库_DiseaseGenesByDB.csv", index=False, encoding="utf-8-sig")

    # venn full: GeneCards_full labeled GeneCards + other DBs
    vrows = []
    for g in sorted(db.get("GeneCards_full", set())):
        vrows.append({"source": "GeneCards", "gene": g})
    for k in ["TTD", "DrugBank", "OMIM", "CTD"]:
        for g in sorted(db.get(k, set())):
            vrows.append({"source": k, "gene": g})
    pd.DataFrame(vrows).to_csv(
        DATA / "疾病靶点按库_VennFull_DiseaseGenesByDB.csv", index=False, encoding="utf-8-sig"
    )

    pd.DataFrame({"gene": sorted(D)}).to_csv(
        DATA / "疾病靶点合并_DiseaseGenesUnion.csv", index=False, encoding="utf-8-sig"
    )

    # per-herb targets / overlaps
    all_herb: set[str] = set()
    summary_rows = []
    all_ov_rows = []
    for zh, en, code in HERB_META:
        gs = herb_genes.get(zh, set())
        all_herb |= gs
        ov = sorted(gs & D)
        tdf = pd.DataFrame({"herb_zh": zh, "herb_en": en, "gene": sorted(gs)})
        odf = pd.DataFrame({"herb_zh": zh, "herb_en": en, "gene": ov})
        tdf.to_csv(DATA / f"药物_{code}_靶点基因_HerbTargets.csv", index=False, encoding="utf-8-sig")
        odf.to_csv(DATA / f"药物_{code}_疾病交集_HerbDiseaseOverlap.csv", index=False, encoding="utf-8-sig")
        summary_rows.append({"herb_zh": zh, "herb_en": en, "n_overlap_genes": len(ov), "n_targets": len(gs)})
        for g in ov:
            all_ov_rows.append({"herb_zh": zh, "herb_en": en, "gene": g})
        print(f"  {zh}/{en}: targets={len(gs)} overlap={len(ov)}")

    pd.DataFrame(summary_rows).to_csv(
        DATA / "单药疾病交集汇总_PerHerbOverlapSummary.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(all_ov_rows).to_csv(
        DATA / "全量单药疾病交集_AllHerbDiseaseOverlaps.csv", index=False, encoding="utf-8-sig"
    )

    pd.DataFrame({"gene": sorted(all_herb)}).to_csv(
        DATA / "药物去重基因_DrugGenesUnion.csv", index=False, encoding="utf-8-sig"
    )
    # also keep AllHerbTargets alias used by some scripts
    pd.DataFrame({"gene": sorted(all_herb)}).to_csv(
        DATA / "药物靶点_全药_AllHerbTargets.csv", index=False, encoding="utf-8-sig"
    )

    I_A = sorted(all_herb & D)
    pd.DataFrame({"gene": I_A, "disease": DISEASE}).to_csv(
        DATA / "药物疾病交集_DrugDiseaseOverlap.csv", index=False, encoding="utf-8-sig"
    )

    (DATA / "DATA_SOURCE.md").write_text(
        "\n".join(
            [
                "# 数据来源",
                "",
                f"- 疾病英文名: {DISEASE}",
                f"- 用户准备文件: `{PREP.as_posix()}`",
                f"- 药物名称表: `{DRUG_XLSX.as_posix()}`",
                f"- CTD: `{CTD.as_posix()}`",
                "- 本目录: 技能契约 RAW（由 02_prepare_skill_contracts.py 从 D 盘重建）",
                "- 禁止把出图结果写回本目录",
                "",
            ]
        ),
        encoding="utf-8",
    )
    import json

    (DATA / "PROVENANCE.json").write_text(
        json.dumps(
            {
                "data_provenance": "REAL",
                "disease_english_name": DISEASE,
                "source": str(PREP).replace("\\", "/"),
                "ctd": str(CTD).replace("\\", "/"),
                "n_disease_union": len(D),
                "n_drug_union": len(all_herb),
                "n_overlap": len(I_A),
                "plotting": "NetworkPharmacology skill + VizStandards delivery_save_plot",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("OK contracts rebuilt from D drive")
    print(f"  disease_union={len(D)} drug_union={len(all_herb)} overlap={len(I_A)}")
    print("DATA=", DATA)


if __name__ == "__main__":
    main()
