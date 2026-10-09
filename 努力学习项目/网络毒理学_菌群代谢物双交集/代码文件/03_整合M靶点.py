# -*- coding: utf-8 -*-
"""整合 gutMGene H 证据与 SEA∩STP 预测靶点，输出 M 主面板/全库敏感性。"""
from __future__ import annotations

import io
import json
import re
import time
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "结果文件" / "数据文件" / "代谢物"
PREP = ROOT / "数据文件"
GUT = PREP / "外部数据库" / "gutMGene_v2" / "Microbial metabolite-Host Gene.csv"
STP_DIR = PREP / "STP原始"
SEA_DIR = PREP / "SEA16原始"


def safe_name(name: str) -> str:
    return re.sub(r"[^\w\-]+", "_", str(name))


def norm_gene(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9\-./]", "", str(value or "")).upper()


def uniprot_genes(accessions: list[str], cache: dict[str, list[str]], session: requests.Session) -> dict[str, list[str]]:
    missing = [a for a in accessions if a and a not in cache]
    for start in range(0, len(missing), 80):
        chunk = missing[start:start + 80]
        query = "(" + " OR ".join(f"accession:{a}" for a in chunk) + ")"
        url = "https://rest.uniprot.org/uniprotkb/search"
        params = {"query": query, "fields": "accession,gene_primary,organism_id", "format": "tsv", "size": 500}
        try:
            response = session.get(url, params=params, timeout=90)
            response.raise_for_status()
            frame = pd.read_csv(io.StringIO(response.text), sep="\t")
            for _, row in frame.iterrows():
                acc = str(row.get("Entry", ""))
                gene = str(row.get("Gene Names (primary)", "") or "")
                cache[acc] = [norm_gene(gene)] if gene and gene != "nan" else []
        except Exception:
            for acc in chunk:
                cache.setdefault(acc, [])
        time.sleep(0.15)
    for acc in accessions:
        cache.setdefault(acc, [])
    return cache


def main() -> None:
    panel = pd.read_csv(DATA / "代谢物面板_主分析与全库敏感性.csv")
    panel["safe_name"] = panel["metabolite"].map(safe_name)
    if panel["safe_name"].duplicated().any():
        dup = panel.loc[panel["safe_name"].duplicated(keep=False), ["metabolite", "safe_name"]]
        raise RuntimeError(f"文件名安全映射冲突:\n{dup}")
    name_map = panel.set_index("safe_name")["metabolite"].to_dict()
    info_map = panel.set_index("metabolite").to_dict("index")

    # H evidence
    gut = pd.read_csv(GUT)
    gut = gut[gut["human/mouse"].astype(str).str.casefold().eq("human")].copy()
    h_rows = []
    for _, row in gut.iterrows():
        gene = norm_gene(row.get("Gene", ""))
        metabolite = str(row.get("Metabolite", "")).strip()
        if not gene or not metabolite:
            continue
        h_rows.append({
            "metabolite": metabolite, "gene": gene, "evidence_level": "H",
            "source": "gutMGene_v2_human_metabolite_gene",
            "source_identifier": str(row.get("Gene ID", "")),
            "pmid": str(row.get("PMID", "")), "alteration": str(row.get("Alteration", "")),
            "method": str(row.get("Experimental method", "")), "sample": str(row.get("Sample", "")),
        })
    h_df = pd.DataFrame(h_rows).drop_duplicates(["metabolite", "gene"])

    # STP predictions
    session = requests.Session()
    session.headers.update({"User-Agent": "RProject-M-integration/1.0"})
    up_cache: dict[str, list[str]] = {}
    stp_rows = []
    stp_files = list(STP_DIR.glob("*_Swiss预测靶点_筛选后.csv"))
    for path in stp_files:
        safe = path.name.replace("_Swiss预测靶点_筛选后.csv", "")
        metabolite = name_map.get(safe)
        if not metabolite:
            continue
        frame = pd.read_csv(path)
        for _, row in frame.iterrows():
            try:
                probability = float(str(row.get("Probability", "0")).replace("*", ""))
            except ValueError:
                probability = 0.0
            if probability <= 0:
                continue
            common = norm_gene(row.get("Common name", ""))
            accessions = [x.strip() for x in str(row.get("Uniprot ID", "")).replace("&", ";").split(";") if x.strip()]
            genes = [common] if common else []
            if not genes:
                uniprot_genes(accessions, up_cache, session)
                for acc in accessions:
                    genes.extend(up_cache.get(acc, []))
            if not genes:
                genes = [""]
            for gene in genes:
                if not gene:
                    continue
                stp_rows.append({
                    "metabolite": metabolite, "gene": gene, "stp_probability": probability,
                    "stp_uniprot_ids": "&".join(accessions), "stp_target": str(row.get("Target", "")),
                    "stp_target_class": str(row.get("Target Class", "")),
                })
    stp_df = pd.DataFrame(stp_rows).drop_duplicates(["metabolite", "gene"])

    # SEA hits from batch top10 tables mapped through manifest compound_mapping
    sea_files = list(SEA_DIR.glob("batch_*/compound_target_hits.tsv"))
    sea_rows = []
    for path in sea_files:
        try:
            hits = pd.read_csv(path, sep="\t") if path.stat().st_size > 0 else pd.DataFrame()
        except pd.errors.EmptyDataError:
            hits = pd.DataFrame()
        if hits.empty:
            continue
        mapping = pd.read_csv(path.parent / "compound_mapping.csv")
        cmap = mapping.set_index("compound_id")["name_en"].to_dict()
        for _, row in hits.iterrows():
            metabolite = cmap.get(str(row.get("compound_id", "")), "")
            if not metabolite:
                continue
            species = str(row.get("target_species", ""))
            acc = str(row.get("uniprot_accession", "") or "")
            up_id = str(row.get("uniprot_id", "") or "")
            if species != "Homo" and not acc.upper().endswith("_HUMAN") and not up_id.upper().endswith("_HUMAN"):
                continue
            gene = norm_gene(row.get("target_gene", ""))
            if not gene and acc:
                genes = uniprot_genes([acc], up_cache, session).get(acc, [])
                gene = norm_gene(genes[0]) if genes else ""
                continue
            sea_rows.append({
                "metabolite": metabolite, "gene": gene,
                "target_chembl_id": str(row.get("target_chembl_id", "")),
                "target_name": str(row.get("target_name", "")), "uniprot_accession": acc,
                "sea_z_score": row.get("sea_z_score", ""), "sea_p_value": row.get("sea_p_value", ""),
                "sea_minus_log10_p": row.get("sea_minus_log10_p", ""),
                "query_known_hit_tanimoto": row.get("query_known_hit_tanimoto", ""),
            })
    sea_df = pd.DataFrame(sea_rows).drop_duplicates(["metabolite", "gene"])

    m_rows = []
    if not sea_df.empty and not stp_df.empty:
        predicted = sea_df.merge(stp_df, on=["metabolite", "gene"], how="inner")
        for _, row in predicted.iterrows():
            m_rows.append({
                "metabolite": row["metabolite"], "gene": row["gene"], "evidence_level": "M",
                "source": "SEA16_ChEMBL27_intersect_STP", "source_identifier": row.get("target_chembl_id", ""),
                "sea_z_score": row.get("sea_z_score", ""), "sea_p_value": row.get("sea_p_value", ""),
                "stp_probability": row.get("stp_probability", ""),
                "target_name": row.get("target_name", ""), "uniprot_accession": row.get("uniprot_accession", ""),
            })
    predicted_df = pd.DataFrame(m_rows)
    threshold_df = pd.DataFrame()
    if not sea_df.empty and not stp_df.empty:
        threshold_df = sea_df.merge(stp_df, on=["metabolite", "gene"], how="inner").copy()
        tc = pd.to_numeric(threshold_df.get("query_known_hit_tanimoto"), errors="coerce").fillna(0)
        prob = pd.to_numeric(threshold_df.get("stp_probability"), errors="coerce").fillna(0)
        threshold_df["pass_relaxed"] = True
        threshold_df["pass_medium"] = (tc >= 0.35) & (prob >= 0.05)
        threshold_df["pass_strict"] = (tc >= 0.40) & (prob >= 0.10)
        threshold_df["threshold_level"] = np.select([threshold_df["pass_strict"], threshold_df["pass_medium"]], ["strict", "medium"], default="relaxed")
        threshold_df.to_csv(DATA / "M_阈值敏感性.csv", index=False, encoding="utf-8-sig")
    all_targets = pd.concat([h_df, predicted_df], ignore_index=True, sort=False)
    all_targets = all_targets.drop_duplicates(["metabolite", "gene", "evidence_level"])

    main_names = set(panel.loc[panel["included_main"].astype(bool), "metabolite"])
    full_names = set(panel.loc[panel["in_full_sensitivity"].astype(bool), "metabolite"])
    main_targets = all_targets[all_targets["metabolite"].isin(main_names)].copy()
    full_targets = all_targets[all_targets["metabolite"].isin(full_names)].copy()
    all_targets.to_csv(DATA / "M_全部靶点.csv", index=False, encoding="utf-8-sig")
    main_targets.to_csv(DATA / "M_主面板靶点.csv", index=False, encoding="utf-8-sig")
    full_targets.to_csv(DATA / "M_全库敏感性靶点.csv", index=False, encoding="utf-8-sig")

    exceptions = []
    for _, row in panel.iterrows():
        metabolite = row["metabolite"]
        if not row.get("canonical_smiles"):
            exceptions.append({"metabolite": metabolite, "stage": "structure", "issue": "missing SMILES"})
        if metabolite not in set(stp_df.get("metabolite", pd.Series(dtype=str))):
            exceptions.append({"metabolite": metabolite, "stage": "STP", "issue": "no retained STP target"})
        if metabolite not in set(sea_df.get("metabolite", pd.Series(dtype=str))):
            exceptions.append({"metabolite": metabolite, "stage": "SEA", "issue": "no retained Homo SEA hit"})
    pd.DataFrame(exceptions).to_csv(DATA / "M_靶点异常清单.csv", index=False, encoding="utf-8-sig")

    summary = {
        "gutmgene_H_edges": int(len(h_df)), "STP_edges": int(len(stp_df)),
        "SEA_human_edges": int(len(sea_df)), "SEA_intersect_STP_edges": int(len(predicted_df)),
        "all_M_rows": int(len(all_targets)), "main_M_rows": int(len(main_targets)),
        "full_M_rows": int(len(full_targets)),
        "main_M_genes": int(main_targets["gene"].nunique()) if not main_targets.empty else 0,
        "full_M_genes": int(full_targets["gene"].nunique()) if not full_targets.empty else 0,
        "sea_batch_files": len(sea_files), "stp_filtered_files": len(stp_files),
        "threshold_relaxed_edges": int(threshold_df.get("pass_relaxed", pd.Series(dtype=bool)).sum()),
        "threshold_medium_edges": int(threshold_df.get("pass_medium", pd.Series(dtype=bool)).sum()),
        "threshold_strict_edges": int(threshold_df.get("pass_strict", pd.Series(dtype=bool)).sum()),
    }
    (DATA / "M_构建摘要.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
