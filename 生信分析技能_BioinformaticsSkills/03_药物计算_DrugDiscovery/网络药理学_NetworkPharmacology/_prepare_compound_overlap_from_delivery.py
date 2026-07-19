# -*- coding: utf-8 -*-
"""Rebuild compound–target + rename map from delivery package into sample 数据文件.

SSOT (delivery):
  数据/网络图/重复有效成分命名表.xlsx
  数据/网络图/药物疾病交集靶点.csv   (no header)
  数据/药物/{药}靶点基因.xlsx         (use columns Unnamed:2 + Gene)

Outputs (sample 数据文件/):
  药物成分靶点_CompoundTargets.csv
  成分重命名_CompoundRenameMap.csv
  草药成分边_HerbCompoundEdges.csv
  成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv  (preview; also rebuilt in R)
  成分未映射备注_UnmappedCompounds.csv
"""
from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

DELIVERY_ROOT = Path(r"D:\网络药理学文件\网络药理学交付文件20260710(1)\交付文件")
SKILL_ROOT = Path(__file__).resolve().parent
SAMPLE_DATA = SKILL_ROOT / "01_样例_sample" / "数据文件"

HERBS = [
    # (xlsx stem, herb_code, herb_en, herb_zh)
    ("丹参", "DS", "Danshen", "丹参"),
    ("黄连", "HL", "Huanglian", "黄连"),
    ("人参", "RS", "Renshen", "人参"),
    ("黄芪", "HQ", "Huangqi", "黄芪"),
    ("葛根", "GG", "Gegen", "葛根"),
    ("三七", "SQ", "Sanqi", "三七"),
]


def _read_overlap(path: Path) -> list[str]:
    # no header — first gene must not be eaten as column name
    df = pd.read_csv(path, header=None, dtype=str, encoding="utf-8")
    genes = (
        df.iloc[:, 0]
        .astype(str)
        .str.strip()
        .replace({"nan": ""})
        .tolist()
    )
    genes = [g for g in genes if g]
    return sorted(set(genes))


def _read_rename(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    # expected: Rename, Mol Rename, Unnamed: 3 (herb code), Count
    cols = list(df.columns)
    rename_col = "Rename" if "Rename" in cols else cols[0]
    mol_col = "Mol Rename" if "Mol Rename" in cols else cols[1]
    herb_col = None
    for c in cols:
        if str(c).startswith("Unnamed") or c in ("Herb", "herb_code", "Code"):
            herb_col = c
            break
    if herb_col is None and len(cols) >= 3:
        herb_col = cols[2]
    out = pd.DataFrame(
        {
            "compound_name": df[rename_col].astype(str).str.strip(),
            "compound_id": df[mol_col].astype(str).str.strip(),
            "herb_code": df[herb_col].astype(str).str.strip(),
        }
    )
    if "Count" in cols:
        out["share_count"] = pd.to_numeric(df["Count"], errors="coerce")
    else:
        out["share_count"] = 1
    out = out[out["compound_name"].ne("") & out["compound_name"].ne("nan")]
    return out.reset_index(drop=True)


def _read_herb_edges(path: Path, herb_code: str, herb_en: str, herb_zh: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    # Prefer explicit names; fall back to positional C/E (0-based 2 and 4)
    if "Gene" in df.columns:
        gene_col = "Gene"
    elif "Unnamed: 4" in df.columns:
        gene_col = "Unnamed: 4"
    else:
        gene_col = df.columns[4] if len(df.columns) > 4 else df.columns[-1]

    if "Unnamed: 2" in df.columns:
        compound_col = "Unnamed: 2"
    else:
        compound_col = df.columns[2] if len(df.columns) > 2 else df.columns[0]

    out = pd.DataFrame(
        {
            "herb_zh": herb_zh,
            "herb_en": herb_en,
            "herb_code": herb_code,
            "compound_name": df[compound_col].astype(str).str.strip(),
            "target_gene": df[gene_col].astype(str).str.strip(),
        }
    )
    out = out[
        out["compound_name"].ne("")
        & out["compound_name"].ne("nan")
        & out["target_gene"].ne("")
        & out["target_gene"].ne("nan")
    ]
    return out.reset_index(drop=True)


def main() -> None:
    net_dir = DELIVERY_ROOT / "数据" / "网络图"
    drug_dir = DELIVERY_ROOT / "数据" / "药物"
    rename_path = net_dir / "重复有效成分命名表.xlsx"
    overlap_path = net_dir / "药物疾病交集靶点.csv"

    if not rename_path.exists():
        raise SystemExit(f"Missing rename map: {rename_path}")
    if not overlap_path.exists():
        raise SystemExit(f"Missing overlap: {overlap_path}")

    rename = _read_rename(rename_path)
    overlap = set(_read_overlap(overlap_path))
    print(f"rename rows={len(rename)} unique_ids={rename['compound_id'].nunique()}")
    print(f"overlap genes={len(overlap)}")

    edge_parts: list[pd.DataFrame] = []
    for stem, code, en, zh in HERBS:
        xp = drug_dir / f"{stem}靶点基因.xlsx"
        if not xp.exists():
            raise SystemExit(f"Missing herb sheet: {xp}")
        part = _read_herb_edges(xp, code, en, zh)
        print(f"  {zh}: rows={len(part)} compounds={part['compound_name'].nunique()}")
        edge_parts.append(part)

    edges = pd.concat(edge_parts, ignore_index=True)

    # map compound_name + herb_code → Mol Rename
    key_rename = rename.assign(_k=rename["compound_name"] + "||" + rename["herb_code"])
    edges = edges.assign(_k=edges["compound_name"] + "||" + edges["herb_code"])
    edges = edges.merge(
        key_rename[["_k", "compound_id"]].drop_duplicates("_k"),
        on="_k",
        how="left",
    )
    # fallback: name-only (shared same* may still resolve)
    miss = edges["compound_id"].isna()
    name_only = rename.drop_duplicates("compound_name").set_index("compound_name")["compound_id"]
    edges.loc[miss, "compound_id"] = edges.loc[miss, "compound_name"].map(name_only)

    unmapped = edges[edges["compound_id"].isna()][
        ["herb_zh", "herb_en", "herb_code", "compound_name"]
    ].drop_duplicates()
    # keep unmapped with synthetic id for QC (not for Cytoscape)
    for i, idx in enumerate(edges.index[edges["compound_id"].isna()], start=1):
        edges.at[idx, "compound_id"] = f"UNMAPPED_{i}"

    edges = edges.drop(columns=["_k"])
    edges["in_disease_overlap"] = edges["target_gene"].isin(overlap)

    # sample CT: all compound–gene with mapped IDs preferred; keep mapped only for main CT
    ct_all = edges[
        ~edges["compound_id"].astype(str).str.startswith("UNMAPPED")
    ][["herb_en", "compound_id", "target_gene"]].copy()
    ct_all = ct_all.rename(columns={"herb_en": "herb"}).drop_duplicates()

    overlap_edges = edges[edges["in_disease_overlap"]].copy()
    overlap_out = overlap_edges[
        [
            "herb_zh",
            "herb_en",
            "herb_code",
            "compound_name",
            "compound_id",
            "target_gene",
            "in_disease_overlap",
        ]
    ].drop_duplicates()

    herb_comp = rename[["herb_code", "compound_id"]].copy()
    code_to_en = {c: e for _, c, e, _ in HERBS}
    herb_comp["herb"] = herb_comp["herb_code"].map(code_to_en)
    herb_comp = herb_comp[["herb_code", "compound_id", "herb"]].drop_duplicates()

    SAMPLE_DATA.mkdir(parents=True, exist_ok=True)

    def write_csv(df: pd.DataFrame, name: str) -> None:
        p = SAMPLE_DATA / name
        df.to_csv(p, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)
        print(f"wrote {p.name} rows={len(df)}")

    write_csv(ct_all, "药物成分靶点_CompoundTargets.csv")
    write_csv(
        rename.rename(columns={})[
            ["compound_name", "compound_id", "herb_code"]
            + (["share_count"] if "share_count" in rename.columns else [])
        ],
        "成分重命名_CompoundRenameMap.csv",
    )
    write_csv(herb_comp, "草药成分边_HerbCompoundEdges.csv")
    write_csv(overlap_out, "成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv")
    write_csv(unmapped, "成分未映射备注_UnmappedCompounds.csv")

    # refresh overlap gene list file (with header) if delivery had no header
    ov_df = pd.DataFrame({"gene": sorted(overlap)})
    write_csv(ov_df, "药物疾病交集_DrugDiseaseOverlap.csv")

    print(
        f"DONE ct={len(ct_all)} overlap_edges={len(overlap_out)} "
        f"unmapped_compounds={len(unmapped)} "
        f"unique_mol={ct_all['compound_id'].nunique()}"
    )


if __name__ == "__main__":
    main()
