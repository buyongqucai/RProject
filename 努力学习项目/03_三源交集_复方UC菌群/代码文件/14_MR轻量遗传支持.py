# -*- coding: utf-8 -*-
"""14_MR轻量遗传支持.py —— Phase 5 MR 的降级执行（公开可得遗传证据）

背景：原计划 MiBioGen→FinnGen 两样本 MR 需全量汇总统计（GB 级 + 授权），本环境不可得；
     按 2026-10-07 修订计划 §4.1 动作 4，降级为公开数据的「遗传支持」层：
  (1) GWAS Catalog v2（免 token）UC 显著位点映射基因 × C/I₁ 超几何重叠（背景=D）
  (2) MiBioGen allHits（18.3MB）清点菌群性状的遗传工具变量（IV）基础

结论边界（项目规范 §2）：只写「遗传支持/假设生成」，不作因果验证、不称完整 MR；
     完整 MiBioGen→FinnGen 两样本 MR 列入后续（计划 §4.1 动作4备注）。

数据访问日期：2026-10-07。
  GWAS Catalog: https://www.ebi.ac.uk/gwas/rest/api/v2/associations?efo_id=MONDO_0005101
  MiBioGen:     https://molgenis26.gcc.rug.nl/downloads/MiBioGen/MBG.allHits.p1e4.txt
输出：结果文件/数据文件/GWAS遗传支持/ + 结果文件/报告文件/报告_MR轻量遗传支持.md（打印摘要）
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pandas as pd
from scipy.stats import hypergeom

ROOT = Path(__file__).resolve().parents[1]
DELIV = ROOT.parent / "交付文件"
OUT = ROOT / "结果文件" / "数据文件" / "GWAS遗传支持"
OUT.mkdir(parents=True, exist_ok=True)
CACHE = ROOT / "数据文件" / "外部数据库" / "GWAS"
CACHE.mkdir(parents=True, exist_ok=True)

GWAS_URL = ("https://www.ebi.ac.uk/gwas/rest/api/v2/associations"
            "?efo_id=MONDO_0005101&page={p}&size=500")
MIBIOGEN_URL = "https://molgenis26.gcc.rug.nl/downloads/MiBioGen/MBG.allHits.p1e4.txt"
P_GWS = 5e-8


def fetch_gwas() -> pd.DataFrame:
    f = CACHE / "UC_gwas_associations.csv"
    if f.exists():
        return pd.read_csv(f, encoding="utf-8-sig")
    rows = []
    for page in range(3):
        u = GWAS_URL.format(p=page)
        d = json.load(urllib.request.urlopen(
            urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))
        for a in d["_embedded"]["associations"]:
            rows.append({
                "p_value": a.get("p_value"),
                "mapped_genes": ";".join(a.get("mapped_genes") or []),
                "risk_snps": ";".join(s.get("rs_id", "") for s in (a.get("snp_allele") or [])),
                "location": ";".join(a.get("locations") or []),
                "accession": a.get("accession_id"),
                "reported_trait": ";".join(a.get("reported_trait") or []),
                "pubmed": a.get("pubmed_id"),
            })
    df = pd.DataFrame(rows)
    df.to_csv(f, index=False, encoding="utf-8-sig")
    return df


def fetch_mibiogen() -> Path:
    f = CACHE / "MBG.allHits.p1e4.txt"
    if not f.exists():
        urllib.request.urlretrieve(MIBIOGEN_URL, f)
    return f


def hyper_p(k: int, K: int, n: int, N: int) -> float:
    """背景宇宙 N，其中成功 K；抽取 n（=C 大小），观察 k → P(X>=k)"""
    if k == 0 or N == 0:
        return 1.0
    return float(hypergeom.sf(k - 1, N, K, n))


def main() -> None:
    D = set(pd.read_csv(DELIV / "数据文件/疾病/疾病靶点合并.csv", encoding="utf-8-sig")["gene"])
    C = set(pd.read_csv(ROOT / "结果文件" / "数据文件" / "C_main_evidence_priority_H_plus_M.csv", encoding="utf-8-sig")["gene"])
    I1 = set(pd.read_csv(DELIV / "数据文件/药物/药物疾病交集.csv", encoding="utf-8-sig")["gene"])

    gwas = fetch_gwas()
    gws = gwas[gwas["p_value"] < P_GWS].copy()
    ug = set()
    for s in gws["mapped_genes"].fillna(""):
        ug |= {g.strip() for g in str(s).split(";") if g.strip()}
    gws_out = gws.assign(genes_list=gws["mapped_genes"])
    gws_out.to_csv(OUT / "UC_GWAS_genomewide_significant.csv", index=False, encoding="utf-8-sig")

    # 主检验：背景 = D（1517，项目口径）
    K = len(ug & D)
    res = {}
    for name, S in [("C_78", C), ("I1_291", I1)]:
        k = len(ug & S)
        p = hyper_p(k, K, len(S), len(D))
        res[name] = {"overlap": k, "set_size": len(S), "universe_D": len(D),
                     "gw_genes_in_D": K, "hypergeom_p_background_D": p,
                     "genes": sorted(ug & S)}
    # 参考：全基因组注释背景（近似用本项目出现过的基因并集作说明性对照）
    all_genes = D | I1 | C | set(gwas["mapped_genes"].fillna("").str.split(";").explode().str.strip())

    # MiBioGen IV 清点（bac=菌群性状，P.weightedSumZ=meta P）
    mb = fetch_mibiogen()
    mg = pd.read_csv(mb, sep="\t", low_memory=False)
    pcol = "P.weightedSumZ" if "P.weightedSumZ" in mg.columns else \
        next((c for c in mg.columns if c.upper().startswith("P")), None)
    rank_col = None
    trait_col = "bac" if "bac" in mg.columns else None
    n_gws = int((mg[pcol] < P_GWS).sum()) if pcol else None
    n_taxa = int(mg[trait_col].nunique()) if trait_col else None
    iv = {"file": mb.name, "rows": int(len(mg)),
          "n_genomewide_sig_P_lt_5e8": n_gws,
          "n_P_lt_1e4": int((mg[pcol] < 1e-4).sum()) if pcol else None,
          "n_traits_with_hits": n_taxa,
          "note": "bac 列为菌群性状（如 class.xxx.id.N）；行=性状×SNP 的 P<1e-4 命中"}
    top = mg.nsmallest(10, pcol) if pcol else pd.DataFrame()
    if len(top):
        cols = [c for c in [trait_col, rank_col, "beta", "se", pcol, "N"] if c and c in top.columns]
        top[cols].to_csv(OUT / "MiBioGen_top10_instruments.csv", index=False, encoding="utf-8-sig")

    summary = {
        "定位": "遗传支持/假设生成，非完整MR、非因果验证",
        "数据访问": "GWAS Catalog v2 (MONDO_0005101) + MiBioGen allHits, 2026-10-07",
        "UC_GWAS关联总数": int(len(gwas)),
        "UC_GWAS全基因组显著关联数": int(len(gws)),
        "UC_GWAS显著映射基因数": len(ug),
        "超几何_背景D1517": res,
        "MiBioGen_IV清点": iv,
    }
    (OUT / "MR轻量_摘要.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2)[:3000])


if __name__ == "__main__":
    main()
