# -*- coding: utf-8 -*-
"""构建 UC/IBD 证据优先代谢物面板与 gutMGene 人类全库敏感性面板。"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
import time
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
GMMAD2_DIR = ROOT / "数据文件" / "外部数据库" / "GMMAD2"
GUT_DIR = ROOT / "数据文件" / "外部数据库" / "gutMGene_v2"
OUT_DIR = ROOT / "结果文件" / "数据文件" / "代谢物"
INPUT_DIR = ROOT / "数据文件" / "预测输入"

CELL_RE = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.I | re.S)
ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.I | re.S)
TABLE_RE = re.compile(r"<table[^>]*>(.*?)</table>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")

ANCHORS = {
    "Acetate", "Propionate", "Butyrate", "Indole", "Indole-3-acetic acid",
    "3-Indolepropionic acid", "Indoxyl sulfate", "Trimethylamine oxide",
    "Deoxycholic Acid", "Lithocholic acid", "Cholic Acid",
    "Chenodeoxycholic acid", "Isodeoxycholic acid",
}
SPECIAL_NAMES = {"Hydrogen Sulfide", "H2S", "Lipopolysaccharide", "LPS"}
SPECIAL_EXPOSURES = [
    {
        "exposure": "Lipopolysaccharide (LPS)",
        "identity": "PAMP/lipoglycan, not a small-molecule metabolite",
        "prediction_route": "curated mechanism only; exclude from SEA/STP",
        "adverse_outcomes": "intestinal barrier injury; intestinal inflammation",
    },
    {
        "exposure": "Hydrogen sulfide (H2S)",
        "identity": "gaseous signal molecule",
        "prediction_route": "curated mechanism only; exclude from SEA/STP",
        "adverse_outcomes": "intestinal barrier injury; intestinal inflammation",
    },
]


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub("", value))).strip()


def parse_gmmad2(path: Path) -> pd.DataFrame:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    table_match = TABLE_RE.search(raw)
    if not table_match:
        raise RuntimeError(f"未找到 GMMAD2 表格: {path}")
    rows = []
    for row_match in ROW_RE.finditer(table_match.group(1)):
        cells = [clean_text(x) for x in CELL_RE.findall(row_match.group(1))]
        if len(cells) == 9 and cells[0] != "Disease":
            rows.append(cells)
    columns = [
        "disease", "disease_id", "metabolite", "pubchem_cid", "score",
        "alteration", "p_value", "fdr", "details",
    ]
    df = pd.DataFrame(rows, columns=columns)
    for col in ["pubchem_cid", "score", "p_value", "fdr"]:
        df[col] = pd.to_numeric(df[col].replace("not available", None), errors="coerce")
    return df


def normalized(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.casefold()


def pubchem_properties(session: requests.Session, names: pd.DataFrame) -> pd.DataFrame:
    records = names.to_dict("records")
    by_cid: dict[str, dict] = {}
    cid_values = sorted({str(int(float(r["pubchem_cid"]))) for r in records if pd.notna(r["pubchem_cid"]) and str(r["pubchem_cid"]).strip()})
    for start in range(0, len(cid_values), 40):
        chunk = cid_values[start:start + 40]
        url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/" + ",".join(chunk) + "/property/CanonicalSMILES,IsomericSMILES,InChIKey,MolecularFormula,MolecularWeight/JSON"
        response = session.get(url, timeout=60)
        if response.ok:
            for item in response.json().get("PropertyTable", {}).get("Properties", []):
                by_cid[str(item.get("CID"))] = item
        time.sleep(0.2)

    out = []
    for record in records:
        name = record["metabolite"]
        cid = record.get("pubchem_cid")
        cid_key = str(int(float(cid))) if pd.notna(cid) and str(cid).strip() else ""
        prop = by_cid.get(cid_key, {})
        if not prop and name:
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(name)}/property/CanonicalSMILES,IsomericSMILES,InChIKey,MolecularFormula,MolecularWeight/JSON"
            try:
                response = session.get(url, timeout=45)
                if response.ok:
                    item = response.json()["PropertyTable"]["Properties"][0]
                    prop = item
                    cid_key = str(item.get("CID", cid_key))
            except Exception:
                prop = {}
            time.sleep(0.15)
        out.append({
            "metabolite": name,
            "pubchem_cid": cid_key,
            "canonical_smiles": prop.get("CanonicalSMILES") or prop.get("SMILES") or prop.get("ConnectivitySMILES") or "",
            "isomeric_smiles": prop.get("IsomericSMILES") or prop.get("SMILES") or "",
            "inchikey": prop.get("InChIKey", ""),
            "molecular_formula": prop.get("MolecularFormula", ""),
            "molecular_weight": prop.get("MolecularWeight", ""),
            "cid_source": "GMMAD2/gutMGene" if record.get("pubchem_cid") else ("PubChem-name" if prop else "missing"),
        })
    return pd.DataFrame(out).drop_duplicates(subset=["metabolite"], keep="first")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="不查询 PubChem，仅用已有 CID")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    INPUT_DIR.mkdir(parents=True, exist_ok=True)

    uc = parse_gmmad2(GMMAD2_DIR / "browse3_D003093.html")
    ibd = parse_gmmad2(GMMAD2_DIR / "browse3_D015212.html")
    uc.to_csv(OUT_DIR / "GMMAD2_UC_D003093.csv", index=False, encoding="utf-8-sig")
    ibd.to_csv(OUT_DIR / "GMMAD2_IBD_D015212.csv", index=False, encoding="utf-8-sig")

    gut_micro = pd.read_csv(GUT_DIR / "Gut Microbe-Microbial metabolite.csv")
    gut_gene = pd.read_csv(GUT_DIR / "Microbial metabolite-Host Gene.csv")
    gut_micro_h = gut_micro[gut_micro["human/mouse"].astype(str).str.casefold().eq("human")].copy()
    gut_gene_h = gut_gene[gut_gene["human/mouse"].astype(str).str.casefold().eq("human")].copy()

    full_names = (
        gut_micro_h[["Metabolite", "Metabolite PubChem CID"]]
        .rename(columns={"Metabolite": "metabolite", "Metabolite PubChem CID": "pubchem_cid"})
        .drop_duplicates("metabolite")
    )
    gene_names = (
        gut_gene_h[["Metabolite", "Metabolite PubChem CID"]]
        .rename(columns={"Metabolite": "metabolite", "Metabolite PubChem CID": "pubchem_cid"})
        .drop_duplicates("metabolite")
    )
    uc_gene_evidence = set(normalized(gene_names["metabolite"]))
    anchor_names = {x.casefold(): x for x in ANCHORS}

    uc_sig = uc[uc["fdr"].lt(0.05)].copy()
    ibd_sig = ibd[ibd["fdr"].lt(0.05)].copy()
    uc_quantile = float(uc_sig["score"].abs().quantile(0.90)) if not uc_sig.empty else math.inf
    uc_high = uc_sig[uc_sig["score"].abs().gt(uc_quantile)].copy()
    ibd_quantile = float(ibd_sig["score"].abs().quantile(0.90)) if not ibd_sig.empty else math.inf
    ibd_high = ibd_sig[ibd_sig["score"].abs().ge(ibd_quantile)].copy()

    main_names = set(normalized(uc_high["metabolite"]))
    main_names |= {
        name for name in normalized(pd.concat([uc_sig, ibd_sig])["metabolite"])
        if name in uc_gene_evidence
    }
    main_names |= {
        name for name in normalized(pd.concat([uc_sig, ibd_sig])["metabolite"])
        if name in anchor_names
    }

    all_disease = pd.concat([uc, ibd], ignore_index=True)
    all_disease["name_key"] = normalized(all_disease["metabolite"])
    disease_best = (
        all_disease.sort_values(["name_key", "fdr", "score"], na_position="last")
        .groupby("name_key", as_index=False)
        .first()
    )

    full_names["name_key"] = normalized(full_names["metabolite"])
    gene_names["name_key"] = normalized(gene_names["metabolite"])
    disease_lookup = disease_best.set_index("name_key").to_dict("index")
    gene_lookup = set(gene_names["name_key"])
    full_lookup = set(full_names["name_key"])

    decisions = []
    candidate_names = sorted(set(disease_best["name_key"]) | full_lookup)
    reverse_name = {}
    for frame in [uc, ibd, full_names, gene_names]:
        for value in frame["metabolite"].dropna().astype(str):
            reverse_name.setdefault(value.strip().casefold(), value.strip())

    for key in candidate_names:
        display = reverse_name.get(key, key)
        d = disease_lookup.get(key, {})
        in_full = key in full_lookup
        in_gene = key in gene_lookup
        uc_fdr = d.get("fdr")
        score = d.get("score")
        included = key in main_names
        reasons = []
        if pd.notna(score) and pd.notna(uc_fdr) and uc_fdr < 0.05 and abs(float(score)) > uc_quantile:
            reasons.append("GMMAD2 high-score: UC FDR<0.05 and |Score| strictly above the 90th percentile")
        if in_gene and (key in set(normalized(uc_sig["metabolite"])) or key in set(normalized(ibd_sig["metabolite"]))):
            reasons.append("gutMGene human metabolite-gene evidence + GMMAD2 UC/IBD FDR<0.05")
        if key in anchor_names and (key in set(normalized(uc_sig["metabolite"])) or key in set(normalized(ibd_sig["metabolite"]))):
            reasons.append("predeclared UC mechanism anchor + GMMAD2 UC/IBD FDR<0.05")
        if not reasons:
            if in_full:
                reasons.append("excluded from main; retained in gutMGene human full-library sensitivity")
            else:
                reasons.append("excluded from main; no qualifying evidence-priority rule")
        decisions.append({
            "metabolite": display,
            "name_key": key,
            "included_main": included,
            "in_gutmgene_human_full": in_full,
            "in_gutmgene_human_gene_evidence": in_gene,
            "is_predeclared_anchor": key in anchor_names,
            "gmmad2_best_score": score,
            "gmmad2_best_alteration": d.get("alteration"),
            "gmmad2_best_fdr": uc_fdr,
            "decision_reason": "; ".join(reasons),
        })
    decisions_df = pd.DataFrame(decisions).sort_values(["included_main", "metabolite"], ascending=[False, True])
    decisions_df.to_csv(OUT_DIR / "代谢物纳入排除清单.csv", index=False, encoding="utf-8-sig")

    panel_names = pd.concat([
        full_names.assign(panel_role="gutMGene human full-library"),
        all_disease[all_disease["name_key"].isin(main_names)][["metabolite", "pubchem_cid"]].assign(panel_role="evidence-priority main"),
    ], ignore_index=True)
    panel_names["name_key"] = normalized(panel_names["metabolite"])
    panel_names = (
        panel_names.sort_values(["name_key", "panel_role"], ascending=[True, False])
        .groupby("name_key", as_index=False)
        .first()
    )

    def cid_str(value):
        if pd.isna(value) or str(value).strip() in {"", "nan", "None"}:
            return ""
        try:
            return str(int(float(value)))
        except ValueError:
            return str(value).strip()

    panel_names["pubchem_cid"] = panel_names["pubchem_cid"].map(cid_str)

    if args.offline:
        props = panel_names.rename(columns={"metabolite": "metabolite"}).copy()
        props["canonical_smiles"] = ""
        props["isomeric_smiles"] = ""
        props["inchikey"] = ""
        props["molecular_formula"] = ""
        props["molecular_weight"] = ""
        props["cid_source"] = "existing-only"
    else:
        session = requests.Session()
        session.headers.update({"User-Agent": "RProject-metabolite-panel/1.0"})
        props = pubchem_properties(session, panel_names)

    props["pubchem_cid"] = props["pubchem_cid"].map(cid_str)
    merged = panel_names.merge(props, on=["metabolite", "pubchem_cid"], how="left", suffixes=("", "_pubchem"))
    if "canonical_smiles_pubchem" in merged:
        merged["canonical_smiles"] = merged["canonical_smiles"].fillna(merged["canonical_smiles_pubchem"])
    merged["included_main"] = merged["name_key"].isin(main_names)
    merged["in_full_sensitivity"] = merged["name_key"].isin(full_lookup)
    merged["in_gutmgene_gene_evidence"] = merged["name_key"].isin(gene_lookup)
    merged["is_predeclared_anchor"] = merged["name_key"].isin(anchor_names)
    merged = merged.merge(
        decisions_df[["name_key", "gmmad2_best_score", "gmmad2_best_alteration", "gmmad2_best_fdr", "decision_reason"]],
        on="name_key", how="left"
    )
    merged["evidence_tier"] = [
        "H" if gene else ("M" if main else "S")
        for gene, main in zip(merged["in_gutmgene_gene_evidence"], merged["included_main"])
    ]
    merged["special_exposure_excluded"] = merged["metabolite"].astype(str).str.casefold().isin({x.casefold() for x in SPECIAL_NAMES})
    merged.loc[merged["special_exposure_excluded"], ["included_main", "in_full_sensitivity"]] = False
    merged = merged.sort_values(["included_main", "in_full_sensitivity", "metabolite"], ascending=[False, False, True])
    merged.to_csv(OUT_DIR / "代谢物面板_主分析与全库敏感性.csv", index=False, encoding="utf-8-sig")

    main_panel = merged[merged["included_main"]].copy()
    full_panel = merged[merged["in_full_sensitivity"]].copy()
    main_panel.to_csv(OUT_DIR / "代谢物主面板.csv", index=False, encoding="utf-8-sig")
    full_panel.to_csv(OUT_DIR / "代谢物全库敏感性.csv", index=False, encoding="utf-8-sig")

    def prediction_input(frame: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
            "name_en": frame["metabolite"].astype(str),
            "name_zh": frame["metabolite"].astype(str),
            "source": frame.get("decision_reason", "gutMGene human full-library"),
            "cid": frame.get("pubchem_cid", "").fillna("").astype(str),
            "smiles": frame.get("canonical_smiles", "").fillna("").astype(str),
        }).drop_duplicates("name_en")

    prediction_input(main_panel).to_csv(INPUT_DIR / "代谢物预测输入_主面板.csv", index=False, encoding="utf-8-sig")
    prediction_input(merged[merged["in_full_sensitivity"] | merged["included_main"]]).to_csv(
        INPUT_DIR / "代谢物预测输入_全库与主面板并集.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(SPECIAL_EXPOSURES).to_csv(OUT_DIR / "特殊暴露物_不进入小分子预测.csv", index=False, encoding="utf-8-sig")

    summary = {
        "access_date": "2026-10-07",
        "gmmad2_uc_rows": int(len(uc)),
        "gmmad2_ibd_rows": int(len(ibd)),
        "gmmad2_uc_fdr_lt_0_05": int(uc["fdr"].lt(0.05).sum()),
        "gmmad2_ibd_fdr_lt_0_05": int(ibd["fdr"].lt(0.05).sum()),
        "gmmad2_uc_score_strictly_above_90th_percentile_threshold": uc_quantile,
        "gmmad2_uc_score_strictly_above_90th_percentile": int(len(uc_high)),
        "gmmad2_ibd_top_decile_threshold": ibd_quantile,
        "gutmgene_human_microbe_metabolites": int(gut_micro_h["Metabolite"].nunique()),
        "gutmgene_human_metabolite_gene_metabolites": int(gut_gene_h["Metabolite"].nunique()),
        "gutmgene_human_metabolite_gene_genes": int(gut_gene_h["Gene"].nunique()),
        "evidence_priority_main_metabolites": int(merged["included_main"].sum()),
        "full_library_sensitivity_metabolites": int(merged["in_full_sensitivity"].sum()),
        "prediction_input_union_metabolites": int(merged["in_full_sensitivity"].sum() + (~merged["in_full_sensitivity"] & merged["included_main"]).sum()),
        "special_exposures_excluded_from_smiles_prediction": len(SPECIAL_EXPOSURES),
    }
    (OUT_DIR / "代谢物面板构建摘要.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
