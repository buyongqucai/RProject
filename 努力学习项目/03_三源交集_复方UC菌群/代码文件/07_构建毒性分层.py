# -*- coding: utf-8 -*-
"""构建非主线毒性分层：有害暴露物、CTD策展靶点、不良结局与效应方向。"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "结果文件" / "数据文件"
TOX = DATA / "毒性分层"
CTD = ROOT / "数据文件" / "外部数据库" / "CTD"

EXPOSURES = [
    {"label":"TMAO","identity":"trimethylamine N-oxide","ctd_id":"MESH:C005855","class":"small_molecule","group":"harmful_candidate","outcomes":"intestinal inflammation;mucosal injury/cancer risk","direction_context":"abundance/context dependent"},
    {"label":"p-Cresol sulfate","identity":"4-cresol sulfate","ctd_id":"MESH:C408690","class":"small_molecule","group":"harmful_candidate","outcomes":"intestinal barrier injury;intestinal inflammation","direction_context":"dose/tissue dependent"},
    {"label":"Indoxyl sulfate","identity":"3-indoxyl sulfate","ctd_id":"MESH:D007200","class":"small_molecule","group":"harmful_candidate","outcomes":"intestinal barrier injury;intestinal inflammation","direction_context":"dose/tissue dependent"},
    {"label":"Deoxycholic acid","identity":"Deoxycholic Acid","ctd_id":"MESH:D003840","class":"small_molecule","group":"harmful_candidate_secondary_bile_acid","outcomes":"mucosal injury;intestinal inflammation;mucosal injury/cancer risk","direction_context":"receptor-, dose- and stage-dependent"},
    {"label":"Lithocholic acid","identity":"Lithocholic Acid","ctd_id":"MESH:D008095","class":"small_molecule","group":"harmful_candidate_secondary_bile_acid","outcomes":"mucosal injury;intestinal inflammation;mucosal injury/cancer risk","direction_context":"receptor-, dose- and stage-dependent"},
    {"label":"Lipopolysaccharide (LPS)","identity":"Lipopolysaccharides","ctd_id":"MESH:D008070","class":"PAMP_not_small_molecule","group":"special_harmful_exposure","outcomes":"intestinal barrier injury;intestinal inflammation","direction_context":"dose/source dependent"},
    {"label":"Hydrogen sulfide (H2S)","identity":"Hydrogen Sulfide","ctd_id":"MESH:D006862","class":"gaseous_signal","group":"special_harmful_exposure","outcomes":"intestinal barrier injury;intestinal inflammation","direction_context":"dose-dependent biphasic"},
]
BENEFICIAL = [
    ("Acetate","SCFA","beneficial_candidate","context dependent"),
    ("Propionate","SCFA","beneficial_candidate","context dependent"),
    ("Butyrate","SCFA","beneficial_candidate","context dependent"),
    ("Indole","tryptophan/indole","beneficial_candidate","receptor/dose dependent"),
    ("Indole-3-acetic acid","tryptophan/indole","beneficial_candidate","receptor/dose dependent"),
    ("3-Indolepropionic acid","tryptophan/indole","beneficial_candidate","receptor/dose dependent"),
]


def main() -> None:
    TOX.mkdir(parents=True, exist_ok=True)
    i1 = set(pd.read_csv(DATA / "I2_main_evidence_priority_H_plus_M.csv")["gene"].astype(str).str.upper()) if False else set(pd.read_csv(DATA / "C_main_evidence_priority_H_plus_M.csv")["gene"].astype(str).str.upper())
    # C is the core shared target set; I1 is loaded separately below.
    i1 = set(pd.read_csv(ROOT.parent / "交付文件" / "数据文件" / "药物" / "药物疾病交集.csv")["gene"].astype(str).str.upper())
    c_main = set(pd.read_csv(DATA / "C_main_evidence_priority_H_plus_M.csv")["gene"].astype(str).str.upper())

    panel = pd.read_csv(DATA / "代谢物" / "代谢物面板_主分析与全库敏感性.csv")
    panel_lookup = {str(r.metabolite).casefold(): r for r in panel.itertuples()}

    id_set = {x["ctd_id"].replace("MESH:", "") for x in EXPOSURES}
    gene_rows = []
    columns = ["chemical_name","chemical_id","cas_rn","gene_symbol","gene_id","gene_form","organism","organism_id","interaction","interaction_actions","pubmed_ids"]
    for chunk in pd.read_csv(CTD / "CTD_chem_gene_ixns.csv.gz", header=None, names=columns, skiprows=29,
                             compression="gzip", dtype=str, low_memory=False, chunksize=250000):
        sub = chunk[chunk["chemical_id"].isin(id_set) & (chunk["organism_id"] == "9606")]
        if len(sub):
            gene_rows.append(sub)
    gene_df = pd.concat(gene_rows, ignore_index=True) if gene_rows else pd.DataFrame(columns=columns)
    gene_df["gene"] = gene_df["gene_symbol"].astype(str).str.upper()
    gene_df.to_csv(TOX / "CTD_有害暴露物基因互作.csv", index=False, encoding="utf-8-sig")

    summary_rows = []
    pair_rows = []
    for exp in EXPOSURES:
        sub = gene_df[gene_df["chemical_id"].eq(exp["ctd_id"].replace("MESH:", ""))]
        genes = sorted(set(sub["gene"].dropna()) - {"", "NAN"})
        actions = " | ".join(sorted(set(sub["interaction_actions"].dropna().astype(str))))
        pmids = set()
        for value in sub["pubmed_ids"].dropna().astype(str):
            pmids.update(x.strip() for x in value.split("|") if x.strip())
        direction_increases = int(sub["interaction_actions"].fillna("").str.contains("increases", case=False).sum())
        direction_decreases = int(sub["interaction_actions"].fillna("").str.contains("decreases", case=False).sum())
        direction_affects = int(sub["interaction_actions"].fillna("").str.contains("affects", case=False).sum())
        panel_row = panel_lookup.get(exp["label"].casefold())
        abundance_direction = getattr(panel_row, "gmmad2_best_alteration", "") if panel_row else ""
        summary_rows.append({
            **exp,
            "pubchem_cid": getattr(panel_row, "pubchem_cid", "") if panel_row else "",
            "canonical_smiles": getattr(panel_row, "canonical_smiles", "") if panel_row else "",
            "gmmad2_abundance_direction": abundance_direction,
            "ctd_human_gene_count": len(genes),
            "ctd_gene_overlap_I1": len(set(genes) & i1),
            "ctd_gene_overlap_C": len(set(genes) & c_main),
            "ctd_action_increases_rows": direction_increases,
            "ctd_action_decreases_rows": direction_decreases,
            "ctd_action_affects_rows": direction_affects,
            "ctd_pmids": len(pmids),
            "effect_direction_status": "mixed curated actions; abundance direction is not toxic-effect direction",
            "evidence_level": "CTD curated interactions",
        })
        for gene in genes:
            pair_rows.append({
                "exposure": exp["label"], "ctd_id": exp["ctd_id"], "gene": gene,
                "in_I1": gene in i1, "in_C": gene in c_main,
                "adverse_outcomes": exp["outcomes"], "direction_context": exp["direction_context"],
                "interaction_actions": " | ".join(sorted(set(sub.loc[sub["gene"].eq(gene), "interaction_actions"].dropna().astype(str)))),
                "pmids": " | ".join(sorted({p for v in sub.loc[sub["gene"].eq(gene), "pubmed_ids"].dropna().astype(str) for p in v.split("|") if p.strip()})),
                "evidence": "curated",
            })
    exposure_df = pd.DataFrame(summary_rows)
    pair_df = pd.DataFrame(pair_rows)
    exposure_df.to_csv(TOX / "有害暴露物清单.csv", index=False, encoding="utf-8-sig")
    pair_df.to_csv(TOX / "毒性线索_暴露物靶点不良结局.csv", index=False, encoding="utf-8-sig")

    beneficial_rows = []
    for name, group, status, context in BENEFICIAL:
        row = panel_lookup.get(name.casefold())
        beneficial_rows.append({
            "metabolite": name, "group": group, "status": status, "direction_context": context,
            "pubchem_cid": getattr(row, "pubchem_cid", "") if row else "",
            "canonical_smiles": getattr(row, "canonical_smiles", "") if row else "",
            "gmmad2_abundance_direction": getattr(row, "gmmad2_best_alteration", "") if row else "",
            "note": "beneficial/harmful labels are downstream annotations, not entry filters",
        })
    pd.DataFrame(beneficial_rows).to_csv(TOX / "代谢物有益有害分层.csv", index=False, encoding="utf-8-sig")

    summary = {
        "selected_exposures": len(EXPOSURES),
        "small_molecule_exposures": sum(x["class"] == "small_molecule" for x in EXPOSURES),
        "special_exposures": sum(x["class"] != "small_molecule" for x in EXPOSURES),
        "ctd_human_interactions": int(len(gene_df)),
        "ctd_unique_genes": int(gene_df["gene"].nunique()) if len(gene_df) else 0,
        "exposures_with_ctd_genes": int((exposure_df["ctd_human_gene_count"] > 0).sum()),
        "overlap_C_exposure_rows": int(pair_df["in_C"].sum()) if len(pair_df) else 0,
        "adverse_outcomes": ["intestinal barrier injury", "intestinal inflammation", "mucosal injury/cancer risk"],
        "interpretation": "toxicity线索/共同调控假设；not antagonism or mitigation",
        "ctd_source": "CTD official bulk files, accessed 2026-10-07",
    }
    (TOX / "毒性分层构建摘要.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
