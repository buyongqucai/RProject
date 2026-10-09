# -*- coding: utf-8 -*-
"""构建 PPI 指标、MCC/MCODE、核心代谢物-靶点对与 G-M-C-T-P 五层网络数据。"""
from __future__ import annotations

import json
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "结果文件" / "数据文件"
MECH = DATA / "机制层"
PAIRS = DATA / "代谢物"
DELIVERY = ROOT.parent / "交付文件" / "数据文件"
GUT = ROOT / "数据文件" / "外部数据库" / "gutMGene_v2" / "Gut Microbe-Microbial metabolite.csv"


def mcode_modules(graph: nx.Graph, haircut: bool = True, degree_cutoff: int = 2,
                  kcore: int = 2, node_score_cutoff: float = 0.2, max_depth: int = 100):
    """MCODE-compatible implementation following BaderLab/MCODEAlgorithm.java."""
    if graph.number_of_nodes() == 0:
        return []

    def density(g: nx.Graph) -> float:
        return nx.density(g) if g.number_of_nodes() > 1 else 0.0

    def highest_kcore(g: nx.Graph):
        best_k, best_graph = 0, None
        k = 1
        while True:
            core = nx.k_core(g, k=k)
            if core.number_of_nodes() == 0:
                break
            best_k, best_graph = k, core
            k += 1
        return best_k, best_graph

    info = {}
    for node in graph.nodes():
        neighborhood = set(graph.neighbors(node)) | {node}
        sub = graph.subgraph(neighborhood).copy()
        core_level, core_graph = highest_kcore(sub)
        core_density = density(core_graph) if core_graph is not None else 0.0
        score = core_density * core_level if len(neighborhood) > degree_cutoff else 0.0
        info[node] = {"neighbors": neighborhood, "score": score, "core_level": core_level,
                      "core_density": core_density, "density": density(sub)}

    seen = set()
    modules = []
    for seed in sorted(graph.nodes(), key=lambda n: (info[n]["score"], graph.degree(n), n), reverse=True):
        if seed in seen:
            continue
        seen_snapshot = set(seen)
        threshold = info[seed]["score"] * (1.0 - node_score_cutoff)
        cluster = set()

        def visit(node, depth):
            if node in seen or depth > max_depth:
                return
            seen.add(node)
            for neighbor in info[node]["neighbors"]:
                if neighbor not in seen and info[neighbor]["score"] >= threshold:
                    cluster.add(neighbor)
                    visit(neighbor, depth + 1)

        visit(seed, 1)
        cluster.add(seed)
        if len(cluster) < 3:
            continue
        cluster_graph = graph.subgraph(cluster).copy()
        if nx.k_core(cluster_graph, k=kcore).number_of_nodes() == 0:
            continue
        if haircut:
            cluster = set(nx.k_core(cluster_graph, k=2).nodes())
            if len(cluster) < 3:
                continue
            cluster_graph = graph.subgraph(cluster).copy()
        score = density(cluster_graph) * cluster_graph.number_of_nodes()
        modules.append({"module": len(modules) + 1, "score": score, "density": density(cluster_graph),
                        "nodes": sorted(cluster), "node_count": len(cluster), "edge_count": cluster_graph.number_of_edges(),
                        "seed": seed, "seen_before_seed": sorted(seen_snapshot),
                        "algorithm": "MCODE-compatible (BaderLab parameters)",
                        "parameters": {"degree_cutoff": degree_cutoff, "kcore": kcore,
                                       "node_score_cutoff": node_score_cutoff, "haircut": haircut,
                                       "fluff": False, "max_depth_from_start": max_depth}})
    return sorted(modules, key=lambda x: x["score"], reverse=True)

def main() -> None:
    MECH.mkdir(parents=True, exist_ok=True)
    c_main = set(pd.read_csv(DATA / "C_main_evidence_priority_H_plus_M.csv")["gene"].astype(str).str.upper())
    ppi = pd.read_csv(MECH / "Main_STRING_edges.csv")
    edges = list(zip(ppi["preferredName_A"].astype(str).str.upper(), ppi["preferredName_B"].astype(str).str.upper()))
    graph = nx.Graph()
    graph.add_edges_from(edges)

    metrics = []
    degree = dict(graph.degree())
    between = nx.betweenness_centrality(graph, normalized=True)
    closeness = nx.closeness_centrality(graph)
    stress = nx.betweenness_centrality(graph, normalized=False, weight=None)
    coreness = nx.core_number(graph)
    triangles = nx.triangles(graph)
    for node in graph.nodes():
        mcc_like = degree[node] * triangles[node]
        metrics.append({"gene": node, "degree": degree[node], "betweenness": between[node],
                        "closeness": closeness[node], "stress": stress[node], "triangles": triangles[node],
                        "coreness": coreness[node], "mcc_like_degree_x_triangles": mcc_like})
    metrics_df = pd.DataFrame(metrics).sort_values(["mcc_like_degree_x_triangles", "degree", "betweenness"], ascending=False)
    metrics_df.insert(0, "mcc_rank", range(1, len(metrics_df) + 1))
    metrics_df.to_csv(MECH / "PPI网络指标_MCC排序.csv", index=False, encoding="utf-8-sig")

    modules = mcode_modules(graph)
    module_rows = []
    for mod in modules:
        for rank, gene in enumerate(sorted(mod["nodes"], key=lambda g: (-degree[g], g)), 1):
            module_rows.append({"module": mod["module"], "module_score": mod["score"], "module_density": mod["density"],
                                "module_rank": rank, "gene": gene, "degree": degree[gene],
                                "mcc_like_degree_x_triangles": degree[gene] * triangles[gene]})
    pd.DataFrame(module_rows).to_csv(MECH / "PPI_MCODE模块.csv", index=False, encoding="utf-8-sig")

    # Core metabolite-target pairs
    m = pd.read_csv(PAIRS / "M_主面板靶点.csv")
    panel = pd.read_csv(PAIRS / "代谢物主面板.csv")
    panel_cols = ["metabolite", "pubchem_cid", "canonical_smiles", "evidence_tier", "gmmad2_best_score",
                  "gmmad2_best_alteration", "gmmad2_best_fdr", "decision_reason"]
    pairs = m[m["gene"].astype(str).str.upper().isin(c_main)].merge(panel[panel_cols], on="metabolite", how="left")
    evidence_score_map = {"H": 3.0, "M": 2.0, "H;M": 3.5}
    pairs["evidence_score"] = pairs["evidence_level"].map(lambda x: evidence_score_map.get(str(x), 1.0))
    pairs["gmmad2_abs_score"] = pd.to_numeric(pairs["gmmad2_best_score"], errors="coerce").abs().fillna(0)
    pairs["stp_probability"] = pd.to_numeric(pairs["stp_probability"], errors="coerce").fillna(0) if "stp_probability" in pairs else 0
    pairs["sea_max_tc"] = pd.to_numeric(pairs["query_known_hit_tanimoto"], errors="coerce").fillna(0) if "query_known_hit_tanimoto" in pairs else 0
    pairs["pair_priority_score"] = (pairs["evidence_score"] + pairs["gmmad2_abs_score"] +
                                    pairs["stp_probability"] + pairs["sea_max_tc"])
    gene_mcc = metrics_df.set_index("gene")["mcc_like_degree_x_triangles"].to_dict()
    pairs["target_mcc_like"] = pairs["gene"].map(gene_mcc).fillna(0)
    pairs = pairs.sort_values(["pair_priority_score", "target_mcc_like", "metabolite", "gene"], ascending=[False, False, True, True])
    pairs.to_csv(MECH / "核心代谢物靶点配对.csv", index=False, encoding="utf-8-sig")

    # Five-layer network: gut microbe -> metabolite -> compound -> target -> pathway
    top_pairs = pairs.head(120)
    metabolite_counts = top_pairs.groupby("metabolite")["gene"].nunique().sort_values(ascending=False)
    target_counts = top_pairs.groupby("gene")["metabolite"].nunique().sort_values(ascending=False)
    selected_metabolites = list(metabolite_counts.head(12).index)
    selected_targets = list(target_counts.head(16).index)

    gut = pd.read_csv(GUT)
    gut = gut[gut["human/mouse"].astype(str).str.casefold().eq("human")].copy()
    gm = gut[gut["Metabolite"].isin(selected_metabolites)][["Gut Microbiota", "Metabolite", "PMID", "human/mouse"]].drop_duplicates()
    microbe_counts = gm.groupby("Gut Microbiota")["Metabolite"].nunique().sort_values(ascending=False)
    selected_microbes = list(microbe_counts.head(12).index)
    gm = gm[gm["Gut Microbiota"].isin(selected_microbes)]

    compound = pd.read_csv(DELIVERY / "药物" / "成分靶点.csv")
    compound = compound[compound["target_gene"].astype(str).str.upper().isin(selected_targets)].copy()
    compound["target_gene"] = compound["target_gene"].astype(str).str.upper()
    compound_counts = compound.groupby(["compound_id", "compound_name"])["target_gene"].nunique().sort_values(ascending=False)
    selected_compounds = list(compound_counts.head(12).index)
    compound = compound[[("compound_id", "compound_name") in selected_compounds for _ in range(len(compound))]] if False else compound
    keep_compound = set(selected_compounds)
    compound = compound[[ (r.compound_id, r.compound_name) in keep_compound for r in compound.itertuples() ]]

    kegg = pd.read_csv(MECH / "富集分析" / "Main_KEGG_full.csv")
    kegg = kegg.sort_values("p.adjust").head(10)
    pathway_rows = []
    for _, row in kegg.iterrows():
        genes = [g.strip().upper() for g in str(row.get("geneID", "")).split("/") if g.strip()]
        for gene in genes:
            if gene in selected_targets:
                pathway_rows.append({"pathway_id": row["ID"], "pathway": row["Description"], "gene": gene})
    pathway_edges = pd.DataFrame(pathway_rows)

    node_rows = []
    edge_rows = []
    def add_node(node_id, label, node_type, layer, score):
        node_rows.append({"id": node_id, "label": str(label), "type": node_type, "layer": layer, "score": float(score)})
    def add_edge(source, target, etype, score):
        edge_rows.append({"source": source, "target": target, "edge_type": etype, "score": float(score)})

    for microbe, n in microbe_counts.head(12).items():
        add_node(f"G::{microbe}", microbe, "GutMicrobe", 1, n)
    for metabolite, n in metabolite_counts.head(12).items():
        add_node(f"M::{metabolite}", metabolite, "Metabolite", 2, n)
    for (cid, cname), n in compound_counts.head(12).items():
        add_node(f"C::{cid}", cname, "Compound", 3, n)
    for gene, n in target_counts.head(16).items():
        add_node(f"T::{gene}", gene, "Target", 4, n)
    for _, row in kegg.iterrows():
        add_node(f"P::{row['ID']}", row["Description"], "Pathway", 5, row.get("Count", 0))

    for _, row in gm.iterrows():
        add_edge(f"G::{row['Gut Microbiota']}", f"M::{row['Metabolite']}", "G_M", 1)
    for row in top_pairs.itertuples():
        if row.metabolite in selected_metabolites and row.gene in selected_targets:
            add_edge(f"M::{row.metabolite}", f"T::{row.gene}", "M_T", row.pair_priority_score)
    for row in compound.itertuples():
        if row.target_gene in selected_targets:
            add_edge(f"C::{row.compound_id}", f"T::{row.target_gene}", "C_T", 1)
    for row in pathway_edges.itertuples():
        add_edge(f"T::{row.gene}", f"P::{row.pathway_id}", "T_P", 1)

    nodes_df = pd.DataFrame(node_rows).drop_duplicates("id")
    edges_df = pd.DataFrame(edge_rows).drop_duplicates(["source", "target", "edge_type"])
    nodes_df.to_csv(MECH / "五层网络节点.csv", index=False, encoding="utf-8-sig")
    edges_df.to_csv(MECH / "五层网络边.csv", index=False, encoding="utf-8-sig")

    summary = {
        "c_main_genes": len(c_main), "ppi_nodes": graph.number_of_nodes(), "ppi_edges": graph.number_of_edges(),
        "mcc_top_gene": str(metrics_df.iloc[0]["gene"]) if len(metrics_df) else "",
        "mcode_modules_ge3_nodes": len(modules),
        "core_metabolite_target_pairs": int(len(pairs)),
        "five_layer_nodes": int(len(nodes_df)), "five_layer_edges": int(len(edges_df)),
        "kegg_terms_used": int(len(kegg)),
    }
    (MECH / "机制层构建摘要.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
