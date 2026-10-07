# -*- coding: utf-8 -*-
"""计算 I2/C、超几何/Jaccard/度加权置换及去 hub 敏感性。"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import hypergeom

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT.parent / "交付文件" / "数据"
DATA = ROOT / "数据"
MET = DATA / "代谢物"

F_PATH = DELIVERY / "药物" / "药物靶点_全药.csv"
D_PATH = DELIVERY / "疾病" / "疾病靶点合并.csv"
I1_PATH = DELIVERY / "药物" / "药物疾病交集.csv"
PPI_PATH = DELIVERY / "PPI" / "string_interactions_short.tsv"
D_PROJECT_COUNT = 1517
PERMUTATIONS = 1000
RNG_SEED = 20261007


def norm_genes(series: pd.Series) -> list[str]:
    return sorted({str(x).strip().upper() for x in series.dropna().astype(str) if str(x).strip()})


def bh_adjust(values: list[float]) -> list[float]:
    p = np.asarray(values, dtype=float)
    order = np.argsort(p)
    ranked = p[order] * len(p) / np.arange(1, len(p) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty_like(ranked)
    out[order] = np.clip(ranked, 0, 1)
    return out.tolist()


def degree_weighted_permutation(i1: set[str], i2: set[str], d_set: set[str], degrees: dict[str, int], n: int = PERMUTATIONS) -> tuple[float, float]:
    genes = sorted(d_set)
    weights = np.asarray([max(1.0, float(degrees.get(g, 0))) for g in genes], dtype=float)
    weights = weights / weights.sum()
    i1_arr = np.asarray([g in i1 for g in genes])
    observed = len(i1 & i2)
    hits = 0
    rng = np.random.default_rng(RNG_SEED)
    for _ in range(n):
        sampled = rng.choice(len(genes), size=len(i2), replace=False, p=weights)
        overlap = int(i1_arr[sampled].sum())
        hits += overlap >= observed
    return (hits + 1) / (n + 1), hits / n


def degree_preserving_stratified_permutation(i1: set[str], i2: set[str], d_set: set[str], degrees: dict[str, int], n: int = PERMUTATIONS) -> tuple[float, float]:
    genes = sorted(d_set)
    values = np.asarray([degrees.get(g, 0) for g in genes], dtype=float)
    positive = values[values > 0]
    if len(positive):
        edges = np.unique(np.quantile(positive, np.linspace(0, 1, 11)))
    else:
        edges = np.asarray([0.0, 1.0])
    bins = np.searchsorted(edges, values, side="right") - 1
    bins = np.clip(bins, 0, len(edges) - 2 if len(edges) > 1 else 0)
    candidates = {int(b): np.asarray([i for i, bb in enumerate(bins) if bb == b]) for b in np.unique(bins)}
    observed_bins = {int(b): int(sum(1 for g in i2 if bins[genes.index(g)] == b)) for b in candidates}
    i1_arr = np.asarray([g in i1 for g in genes])
    observed = len(i1 & i2)
    hits = 0
    rng = np.random.default_rng(RNG_SEED + 1)
    for _ in range(n):
        sampled_idx = []
        for b, count in observed_bins.items():
            pool = candidates[b]
            if count:
                sampled_idx.extend(rng.choice(pool, size=count, replace=False).tolist())
        overlap = int(i1_arr[np.asarray(sampled_idx, dtype=int)].sum()) if sampled_idx else 0
        hits += overlap >= observed
    return (hits + 1) / (n + 1), hits / n

def analyze(label: str, evidence: str, m: pd.DataFrame) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    f_set = set(norm_genes(pd.read_csv(F_PATH)["gene"]))
    d_rows = pd.read_csv(D_PATH)
    d_set = set(norm_genes(d_rows["gene"]))
    i1_set = set(norm_genes(pd.read_csv(I1_PATH)["gene"]))
    genes = norm_genes(m["gene"])
    i2_set = set(genes) & d_set
    c_set = i1_set & i2_set

    i2_df = pd.DataFrame({"gene": sorted(i2_set)})
    c_df = pd.DataFrame({"gene": sorted(c_set)})
    n = len(i2_set)
    k = len(i1_set)
    overlap = len(c_set)
    p = float(hypergeom.sf(overlap - 1, D_PROJECT_COUNT, k, n)) if overlap else 1.0
    jaccard = overlap / len(i1_set | i2_set) if (i1_set | i2_set) else 0.0

    edge_counts: dict[str, int] = {}
    for gene in m["gene"].dropna().astype(str):
        gene = gene.strip().upper()
        edge_counts[gene] = edge_counts.get(gene, 0) + 1
    ppi_counts: dict[str, int] = {}
    if PPI_PATH.exists():
        ppi = pd.read_csv(PPI_PATH, sep="\t")
        cols = {re.sub(r"[^a-z0-9]", "", c.lower()): c for c in ppi.columns}
        a = cols.get("preferrednamea") or cols.get("proteina") or ppi.columns[0]
        b = cols.get("preferrednameb") or cols.get("proteinb") or ppi.columns[1]
        for value in pd.concat([ppi[a], ppi[b]]).dropna().astype(str):
            gene = value.strip().upper()
            ppi_counts[gene] = ppi_counts.get(gene, 0) + 1
    degrees = {g: edge_counts.get(g, 0) + ppi_counts.get(g, 0) for g in d_set}
    perm_p, perm_hits = degree_weighted_permutation(i1_set, i2_set, d_set, degrees)
    strat_perm_p, strat_perm_hits = degree_preserving_stratified_permutation(i1_set, i2_set, d_set, degrees)

    positive_degrees = [v for v in degrees.values() if v > 0]
    threshold = float(np.quantile(positive_degrees, 0.90)) if positive_degrees else 0.0
    hubs = {g for g, value in degrees.items() if value >= threshold and value > 0}
    c_nohub = c_set - hubs
    i2_nohub = i2_set - hubs
    i1_nohub = i1_set - hubs
    p_nohub = float(hypergeom.sf(len(c_nohub) - 1, D_PROJECT_COUNT, len(i1_nohub), len(i2_nohub))) if c_nohub else 1.0

    row = {
        "analysis": label, "evidence": evidence, "F_genes": len(f_set), "D_project_count": D_PROJECT_COUNT,
        "I1_genes": len(i1_set), "M_genes": len(set(genes)), "I2_genes": n, "C_genes": overlap,
        "hypergeom_p": p, "jaccard_I1_I2": jaccard,
        "degree_weighted_permutation_p": perm_p, "perm_ge_observed_hits": perm_hits,
        "degree_preserving_stratified_permutation_p": strat_perm_p, "stratified_perm_ge_observed_hits": strat_perm_hits,
        "permutations": PERMUTATIONS, "hub_degree_threshold_p90": threshold,
        "hub_genes_removed": len(hubs), "C_genes_no_top10pct_hub": len(c_nohub),
        "hypergeom_p_no_top10pct_hub": p_nohub,
        "go_no_go_C_lt_30": overlap < 30,
    }
    return row, i2_df, c_df


def main() -> None:
    results = []
    for label, filename in [
        ("main_evidence_priority", "M_主面板靶点.csv"),
        ("full_gutmgene_human", "M_全库敏感性靶点.csv"),
    ]:
        m = pd.read_csv(MET / filename)
        for evidence, subset in [
            ("H_only", m[m["evidence_level"].eq("H")]),
            ("H_plus_M", m[m["evidence_level"].isin(["H", "M"])]),
        ]:
            row, i2_df, c_df = analyze(label, evidence, subset)
            results.append(row)
            i2_df.to_csv(DATA / f"I2_{label}_{evidence}.csv", index=False, encoding="utf-8-sig")
            c_df.to_csv(DATA / f"C_{label}_{evidence}.csv", index=False, encoding="utf-8-sig")

    stats = pd.DataFrame(results)
    stats["hypergeom_fdr_bh"] = bh_adjust(stats["hypergeom_p"].tolist())
    stats.to_csv(DATA / "双交集统计汇总.csv", index=False, encoding="utf-8-sig")
    summary = {
        "D_project_count_fixed": D_PROJECT_COUNT,
        "permutations": PERMUTATIONS, "rng_seed": RNG_SEED,
        "main_C_H_plus_M": int(stats.loc[(stats.analysis == "main_evidence_priority") & (stats.evidence == "H_plus_M"), "C_genes"].iloc[0]),
        "full_C_H_plus_M": int(stats.loc[(stats.analysis == "full_gutmgene_human") & (stats.evidence == "H_plus_M"), "C_genes"].iloc[0]),
        "colon_expression_filter": "PENDING_EXTERNAL_DATA",
    }
    (DATA / "双交集统计摘要.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(stats.to_string(index=False))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
