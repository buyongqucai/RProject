# -*- coding: utf-8 -*-
"""19_按标准筛选并对接.py

执行技能「复方菌群代谢物整合对接」敲定标准：
  C → 网毒硬过滤 → C* → Top 靶点 / Top 成分 / Top 代谢物 → 分别对接。
归档旧对接全表后重跑。单位 kcal/mol，阈值 −5.0。

标准 SSOT：
  生信分析技能_BioinformaticsSkills/.../研究思路与标准_Paradigm/筛选标准_SelectionCriteria.md
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]  # 06_分子对接
PROJ = ROOT.parent
SEL = ROOT / "数据文件" / "结果数据" / "筛选执行_SelectionRun"
OUT_DOCK = ROOT / "数据文件" / "结果数据" / "对接"
WORK = ROOT / "数据文件" / "对接工作区"
ASCII = Path(r"E:\RProject\_dock_cmp")
ARCH = OUT_DOCK / f"_归档_旧对接_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

OB = Path(r"E:\OpenBabel-3.1.1\obabel.exe")
VINA = Path(r"E:\vina\vina.exe")
SEEDS = [1, 7, 42]
EXHAUST = 8
BOX = 22.0
THRESH_KCAL = -5.0
TOP_T, TOP_L, TOP_M = 8, 8, 8

HARMFUL_MET = {
    "TMAO",
    "p-Cresol sulfate",
    "p-cresyl sulfate",
    "Indoxyl sulfate",
    "Deoxycholic acid",
    "Lithocholic acid",
    "LPS",
    "H2S",
    "H₂S",
    "Hydrogen sulfide",
    "Lipopolysaccharide",
}
SKIP_COMPOUND_ID = {"ZLT1", "ZLT2"}
HARD_EXPOSURES = {
    "TMAO",
    "p-Cresol sulfate",
    "Indoxyl sulfate",
    "Deoxycholic acid",
    "Lithocholic acid",
}

SOLVENT_BLACK = {
    "SO4", "PO4", "GOL", "EDO", "PEG", "DMS", "ACT", "ACE", "MLI", "TRS",
    "MPD", "PG4", "1PE", "P6G", "BTB", "FMT", "AZI", "NO3", "NH4", "IOD",
    "BR", "CL", "NA", "K", "MG", "CA", "MN", "CD", "NI", "CO", "CU",
}
COFACTOR_KEEP = {
    "HEM", "HEB", "HEC", "HEA", "BHC", "VER", "HEX", "OR", "FAD", "FMN",
    "NAD", "NDP", "ZN", "SF4", "FES", "PLP", "B12", "CBL",
}

KNOWN_CID = {
    "quercetin": 5280343,
    "kaempferol": 5280863,
    "luteolin": 5280445,
    "rutin": 5280805,
    "baicalein": 5281605,
    "wogonin": 5281703,
    "beta-sitosterol": 222284,
    "stigmasterol": 5280794,
    "caffeic acid": 689043,
    "delphinidin": 128853,
    "cyanidin": 128861,
    "3beta-hydroxyurs-12-en-28-syre": 64945,
    "berberine": 2353,
    "epiberberine": 160876,
    "coptisine": 72322,
    "palmatine": 19009,
    "isorhamnetin": 5281654,
    "acacetin": 5280442,
    "oroxylin a": 5320315,
}


def norm(s: str) -> str:
    return re.sub(r"[\s_\-]+", "", str(s)).lower()


def is_harmful_met(name: str) -> bool:
    n = str(name)
    nl = n.lower()
    for h in HARMFUL_MET:
        if norm(h) == norm(n) or h.lower() in nl:
            return True
    return False


def http_json(url: str, payload: dict | None = None, retries: int = 3) -> dict:
    import time

    last = None
    for i in range(retries):
        try:
            if payload is None:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            else:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                )
            d = json.load(urllib.request.urlopen(req, timeout=30))
            time.sleep(0.12)
            return d
        except Exception as e:
            last = e
            time.sleep(1.2 * (i + 1))
    raise RuntimeError(f"http失败 {url}: {last}")


def uniprot_for_gene(gene: str) -> str | None:
    url = (
        "https://rest.uniprot.org/uniprotkb/search?"
        f"query=gene_exact:{gene}+AND+organism_id:9606+AND+reviewed:true&fields=accession&format=json&size=1"
    )
    try:
        d = http_json(url)
        results = d.get("results") or []
        if results:
            return results[0]["primaryAccession"]
    except Exception:
        return None
    return None


def pubchem_cid_smi(name: str) -> tuple[int | None, str | None]:
    key = name.lower()
    cid = KNOWN_CID.get(key)
    if cid is None:
        # try quote
        from urllib.parse import quote

        try:
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(name)}/cids/JSON"
            d = json.load(
                urllib.request.urlopen(
                    urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30
                )
            )
            cid = int(d["IdentifierList"]["CID"][0])
        except Exception:
            return None, None
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/ConnectivitySMILES,MolecularWeight/JSON"
    d = json.load(
        urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
    )
    p = d["PropertyTable"]["Properties"][0]
    return cid, p.get("ConnectivitySMILES")


def select() -> dict:
    SEL.mkdir(parents=True, exist_ok=True)
    uc = PROJ / "03_三源交集_复方UC菌群"
    npdir = PROJ / "01_网络药理学" / "数据文件" / "结果数据"
    tox = PROJ / "02_网络毒理学_毒性分层" / "数据文件" / "结果数据" / "毒性分层"
    mech = PROJ / "04_机制层_PPI富集" / "数据文件" / "结果数据" / "机制层"

    C = set(
        pd.read_csv(uc / "数据文件/结果数据/C_main_evidence_priority_H_plus_M.csv", encoding="utf-8-sig")[
            "gene"
        ].astype(str)
    )
    toxdf = pd.read_csv(tox / "毒性线索_暴露物靶点不良结局.csv", encoding="utf-8-sig")
    ToxHard = set(
        toxdf.loc[toxdf["exposure"].isin(HARD_EXPOSURES) & (toxdf["in_C"] == True), "gene"].astype(str)
    )
    Cstar = C - ToxHard
    pd.DataFrame({"gene": sorted(Cstar)}).to_csv(SEL / "Cstar_工作靶点.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame({"gene": sorted(ToxHard), "reason": "harmful_small_molecule_CTD_in_C"}).to_csv(
        SEL / "ToxHard_剔除靶点.csv", index=False, encoding="utf-8-sig"
    )

    # --- Top targets from MCC restricted to C*, fallback induced degree ---
    mcc = pd.read_csv(mech / "PPI网络指标_MCC排序.csv", encoding="utf-8-sig")
    mcc_c = mcc[mcc["gene"].astype(str).isin(Cstar)].copy()
    mcc_c = mcc_c.sort_values(
        ["degree", "mcc_like_degree_x_triangles", "betweenness"], ascending=False
    )
    # induced degrees
    edges = pd.read_csv(mech / "Main_STRING_edges.csv", encoding="utf-8-sig")
    deg_ind = Counter()
    for _, r in edges.iterrows():
        a, b = str(r["preferredName_A"]).upper(), str(r["preferredName_B"]).upper()
        if a in Cstar and b in Cstar:
            deg_ind[a] += 1
            deg_ind[b] += 1
    mcc_c["degree_induced_Cstar"] = mcc_c["gene"].map(lambda g: deg_ind.get(g, 0))
    # sort: induced degree first if any connectivity, else full degree
    if sum(deg_ind.values()) >= 4:
        mcc_c = mcc_c.sort_values(
            ["degree_induced_Cstar", "degree", "mcc_like_degree_x_triangles"], ascending=False
        )
    rows = []
    for _, r in mcc_c.iterrows():
        if len(rows) >= TOP_T:
            break
        u = uniprot_for_gene(r["gene"])
        if not u:
            continue
        rr = r.to_dict()
        rr["uniprot"] = u
        rows.append(rr)
    top_targets = pd.DataFrame(rows)
    top_targets.to_csv(SEL / "Top靶点_PPI_Cstar.csv", index=False, encoding="utf-8-sig")
    top_t_set = set(top_targets["gene"].astype(str))
    ppi_rank = {g: i + 1 for i, g in enumerate(top_targets["gene"].astype(str))}
    # also full C* rank for fallback pairing
    full_rank = {g: i + 1 for i, g in enumerate(mcc_c["gene"].astype(str))}
    up_map = dict(zip(top_targets["gene"].astype(str), top_targets["uniprot"]))

    # --- Top compounds by B–C* degree ---
    net = pd.read_csv(npdir / "网络图/network.csv", encoding="utf-8-sig")
    typ = pd.read_csv(npdir / "网络图/type.csv", encoding="utf-8-sig")
    type_map = dict(zip(typ["term"], typ["type"]))
    ren = pd.read_csv(npdir / "药物/成分重命名.csv", encoding="utf-8-sig")
    id2name = dict(zip(ren["compound_id"], ren["compound_name"]))
    ing = pd.read_csv(npdir / "药物/成分靶点.csv", encoding="utf-8-sig")
    ing_c = ing[ing["target_gene"].astype(str).isin(Cstar)].copy()
    bc_deg = ing_c.groupby("compound_id")["target_gene"].nunique().to_dict()
    # optional A-B
    ab = Counter()
    for _, r in net.iterrows():
        if type_map.get(r["ID"]) == "A" and type_map.get(r["SYMBOL"]) == "B":
            ab[r["SYMBOL"]] += 1
    comp_rows = []
    for cid, d in sorted(bc_deg.items(), key=lambda x: -x[1]):
        if cid in SKIP_COMPOUND_ID:
            continue
        if type_map.get(cid) != "B":
            continue
        name = id2name.get(cid, cid)
        comp_rows.append(
            {
                "compound_id": cid,
                "compound": name,
                "degree_BC_Cstar": d,
                "degree_AB": ab.get(cid, 0),
            }
        )
    comp_df = pd.DataFrame(comp_rows).sort_values(
        ["degree_BC_Cstar", "degree_AB"], ascending=False
    )
    # attach smiles
    kept = []
    for _, r in comp_df.iterrows():
        if len(kept) >= TOP_L:
            break
        cid_pc, smi = pubchem_cid_smi(r["compound"])
        if not smi:
            continue
        rr = r.to_dict()
        rr["pubchem_cid"] = cid_pc
        rr["canonical_smiles"] = smi
        kept.append(rr)
    top_comp = pd.DataFrame(kept)
    top_comp.to_csv(SEL / "Top成分_Degree_Cstar.csv", index=False, encoding="utf-8-sig")

    # compound pairs
    c_pairs = []
    for _, r in top_comp.iterrows():
        genes = set(ing_c.loc[ing_c["compound_id"] == r["compound_id"], "target_gene"].astype(str))
        cand = sorted(genes & top_t_set, key=lambda g: ppi_rank.get(g, 999))
        if not cand:
            cand = sorted(genes & Cstar, key=lambda g: full_rank.get(g, 9999))
        if not cand:
            continue
        g = cand[0]
        u = up_map.get(g) or uniprot_for_gene(g)
        if not u:
            continue
        c_pairs.append(
            {
                "ligand_type": "compound",
                "compound": r["compound"],
                "compound_id": r["compound_id"],
                "network_degree_Cstar": r["degree_BC_Cstar"],
                "gene": g,
                "uniprot": u,
                "ppi_rank_in_top": ppi_rank.get(g, ""),
                "pubchem_cid": r["pubchem_cid"],
                "canonical_smiles": r["canonical_smiles"],
                "selection_rule": "TopL by B-C* degree; target=best PPI among C* neighbors",
            }
        )
    c_pair_df = pd.DataFrame(c_pairs)
    c_pair_df.to_csv(SEL / "配对_成分_Cstar.csv", index=False, encoding="utf-8-sig")
    c_pair_df.to_csv(OUT_DOCK / "核心成分靶点配对.csv", index=False, encoding="utf-8-sig")

    # --- Top metabolites ---
    M = pd.read_csv(uc / "数据文件/结果数据/代谢物/M_主面板靶点.csv", encoding="utf-8-sig")
    panel = pd.read_csv(uc / "数据文件/结果数据/代谢物/代谢物主面板.csv", encoding="utf-8-sig")
    pairs_old = pd.read_csv(mech / "核心代谢物靶点配对.csv", encoding="utf-8-sig")
    pri = pairs_old.groupby("metabolite")["pair_priority_score"].max().to_dict()

    met_stats = []
    for met, gdf in M.groupby("metabolite"):
        if is_harmful_met(met):
            continue
        genes = set(gdf["gene"].dropna().astype(str))
        inter = genes & Cstar
        if not inter:
            continue
        nH = int((gdf["evidence_level"].astype(str) == "H").sum())
        h_in = int(((gdf["evidence_level"].astype(str) == "H") & gdf["gene"].isin(Cstar)).sum())
        p = panel[panel["metabolite"] == met]
        gscore = float(p["gmmad2_best_score"].abs().iloc[0]) if len(p) and pd.notna(p["gmmad2_best_score"].iloc[0]) else 0.0
        smi = p["canonical_smiles"].iloc[0] if len(p) else None
        cid = p["pubchem_cid"].iloc[0] if len(p) else None
        met_stats.append(
            {
                "metabolite": met,
                "n_Cstar": len(inter),
                "n_H_in_Cstar": h_in,
                "n_H": nH,
                "gmmad2_abs": gscore,
                "pair_priority_max": pri.get(met, 0),
                "pubchem_cid": cid,
                "canonical_smiles": smi,
                "genes_Cstar": "|".join(sorted(inter)),
            }
        )
    met_df = pd.DataFrame(met_stats).sort_values(
        ["n_H_in_Cstar", "n_Cstar", "gmmad2_abs", "pair_priority_max"], ascending=False
    )
    # need smiles
    m_kept = []
    for _, r in met_df.iterrows():
        if len(m_kept) >= TOP_M:
            break
        smi = r["canonical_smiles"]
        cid = r["pubchem_cid"]
        if not isinstance(smi, str) or not smi:
            cid2, smi2 = pubchem_cid_smi(r["metabolite"])
            cid, smi = cid2, smi2
        if not smi:
            continue
        rr = r.to_dict()
        rr["pubchem_cid"] = cid
        rr["canonical_smiles"] = smi
        m_kept.append(rr)
    top_met = pd.DataFrame(m_kept)
    top_met.to_csv(SEL / "Top代谢物_TierAstar_Cstar.csv", index=False, encoding="utf-8-sig")

    m_pairs = []
    for _, r in top_met.iterrows():
        genes = set(str(r["genes_Cstar"]).split("|"))
        cand = sorted(genes & top_t_set, key=lambda g: ppi_rank.get(g, 999))
        if not cand:
            cand = sorted(genes, key=lambda g: full_rank.get(g, 9999))
        g = cand[0]
        u = up_map.get(g) or uniprot_for_gene(g)
        if not u:
            continue
        m_pairs.append(
            {
                "ligand_type": "metabolite",
                "metabolite": r["metabolite"],
                "n_Cstar": r["n_Cstar"],
                "n_H_in_Cstar": r["n_H_in_Cstar"],
                "gene": g,
                "uniprot": u,
                "ppi_rank_in_top": ppi_rank.get(g, ""),
                "pubchem_cid": r["pubchem_cid"],
                "canonical_smiles": r["canonical_smiles"],
                "selection_rule": "TopM by H-in-C*, n_C*, GMMAD2; target=best PPI among C* neighbors",
            }
        )
    m_pair_df = pd.DataFrame(m_pairs)
    m_pair_df.to_csv(SEL / "配对_代谢物_Cstar.csv", index=False, encoding="utf-8-sig")
    m_pair_df.to_csv(OUT_DOCK / "核心代谢物对接配对.csv", index=False, encoding="utf-8-sig")

    summary = {
        "|C|": len(C),
        "|ToxHard|": len(ToxHard),
        "|C*|": len(Cstar),
        "top_targets": top_targets["gene"].tolist(),
        "n_compound_pairs": len(c_pair_df),
        "n_metabolite_pairs": len(m_pair_df),
        "THRESH_KCAL": THRESH_KCAL,
    }
    (SEL / "筛选摘要.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return {"c_pairs": c_pair_df, "m_pairs": m_pair_df, "summary": summary}


# ----- docking helpers (reuse Windows ASCII path) -----
STRUCT_CACHE = WORK / "structure_cache.json"


def load_cache() -> dict:
    return json.loads(STRUCT_CACHE.read_text(encoding="utf-8")) if STRUCT_CACHE.exists() else {}


def save_cache(c: dict) -> None:
    STRUCT_CACHE.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")


def search_entries(uniprot: str) -> list[str]:
    q = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                "operator": "exact_match",
                "value": uniprot,
            },
        },
        "request_options": {"paginate": {"start": 0, "rows": 25}},
        "return_type": "entry",
    }
    d = http_json("https://search.rcsb.org/rcsbsearch/v2/query", q)
    return [h["identifier"] for h in d.get("result_set", [])]


def pick_entry(entry_ids: list[str]) -> tuple[str, str | None, str]:
    best = (None, None, None)
    for eid in entry_ids[:10]:
        try:
            e = http_json(f"https://data.rcsb.org/rest/v1/core/entry/{eid}")
        except Exception:
            continue
        res = (e.get("rcsb_entry_info", {}).get("resolution_combined") or [99.0])[0]
        if res and res > 3.0:
            continue
        lig_ids = e.get("rcsb_entry_container_identifiers", {}).get("non_polymer_entity_ids", []) or []
        found = None
        for lid in lig_ids[:5]:
            try:
                ne = http_json(f"https://data.rcsb.org/rest/v1/core/nonpolymer_entity/{eid}/{lid}")
                cid = (ne.get("rcsb_nonpolymer_entity_container_identifiers") or {}).get("nonpolymer_comp_id")
                if not cid:
                    continue
                cc = http_json(f"https://data.rcsb.org/rest/v1/core/chemcomp/{cid}")
            except Exception:
                continue
            comp = cc.get("chem_comp") or {}
            mw = float(comp.get("formula_weight") or 0)
            formula = comp.get("formula") or ""
            if cid in SOLVENT_BLACK or cid in COFACTOR_KEEP:
                continue
            if "C" not in formula or not (90 <= mw <= 550):
                continue
            found = cid
            break
        score = (0 if found else 1, res or 99)
        if best[0] is None or score < best[0]:
            best = (score, eid, found)
        if found:
            break
    if best[1] is None:
        raise RuntimeError("无可用结构")
    return best[1], best[2], ("co-ligand:" + best[2]) if best[2] else "blind(geometric center)"


def download_pdb(entry_id: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(
            f"https://files.rcsb.org/download/{entry_id}.pdb", headers={"User-Agent": "Mozilla/5.0"}
        )
        data = urllib.request.urlopen(req, timeout=60).read()
        if len(data) > 1000 and b"ATOM" in data[:200000]:
            dest.write_bytes(data)
            return True
    except Exception:
        return False
    return False


# PDB 中 DNA/RNA 常记在 ATOM（DA/DC/DG/DT…），不是 HETATM；蛋白对接默认剔除
NUCLEIC_RES = {
    "DA", "DC", "DG", "DT", "DI",
    "A", "C", "G", "T", "U", "I",
    "RA", "RC", "RG", "RU",
    "ADE", "CYT", "GUA", "THY", "URA",
}


def prepare_receptor(pdb: Path, lig_comp: str | None):
    lines = pdb.read_text(errors="ignore").splitlines()
    kept, het_lig = [], []
    for ln in lines:
        rec = ln[:6].strip()
        if rec == "ATOM":
            res = ln[17:20].strip()
            if res in NUCLEIC_RES:
                continue  # 蛋白-only：去掉核酸链
            kept.append(ln)
        elif rec == "HETATM":
            res = ln[17:20].strip()
            if res == "HOH" or res in SOLVENT_BLACK:
                continue
            if res in NUCLEIC_RES:
                continue
            if lig_comp and res == lig_comp:
                het_lig.append(ln)
                continue
            if res in COFACTOR_KEEP:
                kept.append(ln)
    if het_lig:
        pts = [(float(l[30:38]), float(l[38:46]), float(l[46:54])) for l in het_lig]
        clusters: list[list[tuple]] = []
        for p in pts:
            for c in clusters:
                if any((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2 <= 16 for q in c):
                    c.append(p)
                    break
            else:
                clusters.append([p])
        big = max(clusters, key=len)
        center = (
            sum(p[0] for p in big) / len(big),
            sum(p[1] for p in big) / len(big),
            sum(p[2] for p in big) / len(big),
        )
        note = f"co-ligand:{lig_comp}(largest cluster {len(big)}/{len(pts)})"
    else:
        xs = [float(l[30:38]) for l in kept if l.startswith("ATOM")]
        ys = [float(l[38:46]) for l in kept if l.startswith("ATOM")]
        zs = [float(l[46:54]) for l in kept if l.startswith("ATOM")]
        center = (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))
        note = "blind(geometric center)"
    rec_pdb = pdb.with_suffix(".rec.pdb")
    rec_pdb.write_text("\n".join(kept) + "\n")
    return rec_pdb, center, note


def run(cmd: list[str], timeout: int = 900) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return (p.stdout or "") + (p.stderr or "")


def fetch_pubchem_3d_sdf(cid: int, dest: Path) -> None:
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{int(cid)}/SDF?record_type=3d"
    try:
        data = urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60
        ).read()
        dest.write_bytes(data)
        if dest.stat().st_size > 50:
            return
    except Exception:
        pass
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{int(cid)}/SDF"
    data = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60
    ).read()
    tmp = dest.with_suffix(".2d.sdf")
    tmp.write_bytes(data)
    run([str(OB), str(tmp), "-O", str(dest), "--gen3d"], 180)
    if not dest.exists() or dest.stat().st_size < 50:
        raise RuntimeError(f"无3D SDF cid={cid}")


def dock_table(pair_df: pd.DataFrame, ligand_col: str, out_full: Path, out_sum: Path) -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    ASCII.mkdir(parents=True, exist_ok=True)
    scache = load_cache()
    rows, fails = [], []
    for _, pr in pair_df.iterrows():
        lig = str(pr[ligand_col])
        gene = str(pr["gene"])
        up = str(pr["uniprot"])
        cid = int(float(pr["pubchem_cid"]))
        tag = f"STD_{gene}__{re.sub(r'[^A-Za-z0-9]+', '', lig)[:20]}"
        try:
            if gene in scache:
                entry_id, ligc, _ = scache[gene][0], scache[gene][1], scache[gene][2]
            else:
                entries = search_entries(up)
                if not entries:
                    raise RuntimeError(f"RCSB 无 {up}")
                entry_id, ligc, site_note = pick_entry(entries)
                scache[gene] = [entry_id, ligc, site_note]
                save_cache(scache)
            pdb = WORK / f"{entry_id}.pdb"
            if not pdb.exists() and not download_pdb(entry_id, pdb):
                raise RuntimeError(f"下载失败 {entry_id}")
            rec_pdb, center, site_note = prepare_receptor(pdb, ligc)
            rec_ascii = ASCII / f"{tag}.rec.pdb"
            shutil.copy2(rec_pdb, rec_ascii)
            rec_pdbqt = ASCII / f"{tag}.rec.pdbqt"
            msg = run([str(OB), str(rec_ascii), "-O", str(rec_pdbqt), "-xr"], 240)
            if not rec_pdbqt.exists():
                raise RuntimeError("受体失败 " + msg[-150:])
            sdf = ASCII / f"{tag}.sdf"
            fetch_pubchem_3d_sdf(cid, sdf)
            lig_pdbqt = ASCII / f"{tag}.lig.pdbqt"
            msg = run([str(OB), str(sdf), "-h", "-O", str(lig_pdbqt)], 180)
            if not lig_pdbqt.exists():
                raise RuntimeError("配体失败 " + msg[-150:])
            for seed in SEEDS:
                outp = ASCII / f"{tag}_s{seed}.pdbqt"
                log = run(
                    [
                        str(VINA),
                        "--receptor",
                        str(rec_pdbqt),
                        "--ligand",
                        str(lig_pdbqt),
                        "--center_x",
                        f"{center[0]:.3f}",
                        "--center_y",
                        f"{center[1]:.3f}",
                        "--center_z",
                        f"{center[2]:.3f}",
                        "--size_x",
                        str(BOX),
                        "--size_y",
                        str(BOX),
                        "--size_z",
                        str(BOX),
                        "--exhaustiveness",
                        str(EXHAUST),
                        "--seed",
                        str(seed),
                        "--cpu",
                        "4",
                        "--out",
                        str(outp),
                    ],
                    900,
                )
                (ASCII / f"{tag}_s{seed}.log").write_text(log, encoding="utf-8")
                m = re.search(r"^\s*\d+\s+(-?\d+\.\d+)\s", log, re.M) or re.search(
                    r"Affinity:\s+(-?\d+\.\d+)", log
                )
                if not m:
                    raise RuntimeError("vina无分数 " + log[-200:])
                kcal = float(m.group(1))
                rows.append(
                    {
                        ligand_col: lig,
                        "gene": gene,
                        "uniprot": up,
                        "pdb": entry_id,
                        "site": site_note,
                        "seed": seed,
                        "affinity_kcal_mol": kcal,
                        "affinity_kJ_mol": round(kcal * 4.184, 2),
                        "pass_threshold_kcal": kcal <= THRESH_KCAL,
                    }
                )
            print(f"[OK] {lig} x {gene} ({entry_id})")
            pd.DataFrame(rows).to_csv(out_full, index=False, encoding="utf-8-sig")
        except Exception as ex:
            fails.append({ligand_col: lig, "gene": gene, "uniprot": up, "error": str(ex)})
            print(f"[FAIL] {lig} x {gene}: {ex}")
    df = pd.DataFrame(rows)
    if len(df):
        g = (
            df.groupby([ligand_col, "gene", "pdb", "site"])
            .agg(
                mean_kcal=("affinity_kcal_mol", "mean"),
                sd_kcal=("affinity_kcal_mol", "std"),
                min_kcal=("affinity_kcal_mol", "min"),
                pass_rate=("pass_threshold_kcal", "mean"),
                n_runs=("seed", "nunique"),
            )
            .reset_index()
            .sort_values("mean_kcal")
        )
        g.to_csv(out_sum, index=False, encoding="utf-8-sig")
        print(g.to_string(index=False))
    if fails:
        pd.DataFrame(fails).to_csv(out_full.with_name(out_full.stem + "_失败.csv"), index=False, encoding="utf-8-sig")


def archive_old() -> None:
    OUT_DOCK.mkdir(parents=True, exist_ok=True)
    ARCH.mkdir(parents=True, exist_ok=True)
    for name in [
        "对接全表.csv",
        "对接汇总.csv",
        "成分对接全表.csv",
        "成分对接汇总.csv",
        "核心成分靶点配对.csv",
    ]:
        p = OUT_DOCK / name
        if p.exists():
            shutil.move(str(p), str(ARCH / name))
            print("archived", name)


def main() -> None:
    archive_old()
    sel = select()
    dock_table(
        sel["c_pairs"],
        "compound",
        OUT_DOCK / "成分对接全表.csv",
        OUT_DOCK / "成分对接汇总.csv",
    )
    dock_table(
        sel["m_pairs"],
        "metabolite",
        OUT_DOCK / "代谢物对接全表.csv",
        OUT_DOCK / "代谢物对接汇总.csv",
    )
    print("DONE", SEL)


if __name__ == "__main__":
    main()
