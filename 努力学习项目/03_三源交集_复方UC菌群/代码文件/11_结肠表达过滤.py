# -*- coding: utf-8 -*-
"""11_结肠表达过滤.py —— Phase 2 遗留敏感性（风险 1 对策③：结肠组织表达限定）

数据源：GTEx v8 gene median TPM（RNASeQC v1.1.9），
  https://storage.googleapis.com/adult-gtex/bulk-gex/v8/rna-seq/GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.9_gene_median_tpm.gct.gz
  访问日期：2026-10-07；56,200 基因 × 54 组织。

预登记判定：基因在结肠（Colon - Transverse 或 Colon - Sigmoid）任一段 median TPM ≥ 1 视为结肠表达。
输出：结果文件/数据文件/敏感性/结肠表达过滤_{基因表,干预候选稳定性}.csv + 结肠过滤_摘要.json
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DELIV = ROOT.parent / "交付文件"
CAND_GTEX = [                                       # 依次寻找 GTEx GCT（沙盒/本机两套路径）
    ROOT / "数据文件/外部数据库/GTEx/GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.9_gene_median_tpm.gct.gz",
    Path.home() / "extdata" / "gtex_median_tpm.gct.gz",
]
GTEx = next((p for p in CAND_GTEX if p.exists()), CAND_GTEX[0])
OUT = ROOT / "结果文件" / "数据文件" / "敏感性"
OUT.mkdir(parents=True, exist_ok=True)
TPM_CUT = 1.0


def load_sets() -> dict:
    return {
        "I1": set(pd.read_csv(DELIV / "数据文件/药物/药物疾病交集.csv", encoding="utf-8-sig")["gene"]),
        "C_main": set(pd.read_csv(ROOT / "结果文件" / "数据文件" / "C_main_evidence_priority_H_plus_M.csv", encoding="utf-8-sig")["gene"]),
        "C_full": set(pd.read_csv(ROOT / "结果文件" / "数据文件" / "C_full_gutmgene_human_H_plus_M.csv", encoding="utf-8-sig")["gene"]),
        "I2_main": set(pd.read_csv(ROOT / "结果文件" / "数据文件" / "I2_main_evidence_priority_H_plus_M.csv", encoding="utf-8-sig")["gene"]),
    }


def gtex_colon(genes: set[str]) -> pd.DataFrame:
    want = {g.upper() for g in genes}
    rows = []
    with gzip.open(GTEx, "rt", encoding="utf-8") as fh:
        fh.readline()                      # #1.2
        fh.readline()                      # dims
        header = fh.readline().rstrip("\n").split("\t")
        idx = {c: i for i, c in enumerate(header)}
        cols = [c for c in ("Colon - Transverse", "Colon - Sigmoid") if c in idx]
        for line in fh:
            p = line.rstrip("\n").split("\t")
            sym = p[1].upper()             # Description = gene symbol
            if sym in want:
                vals = [float(p[idx[c]]) for c in cols]
                rows.append({"gene": p[1], **{c: v for c, v in zip(cols, vals)},
                             "colon_max_tpm": max(vals) if vals else 0.0})
    df = pd.DataFrame(rows)
    df["gene_key"] = df["gene"].str.upper()
    # 同名多 Ensembl 行 → 取最大 TPM
    df = df.sort_values("colon_max_tpm", ascending=False).drop_duplicates("gene_key")
    df["colon_expressed_tpm_ge_1"] = df["colon_max_tpm"] >= TPM_CUT
    return df.drop(columns=["gene_key"])


def main() -> None:
    s = load_sets()
    universe = s["I1"] | s["C_main"] | s["C_full"] | s["I2_main"]
    gx = gtex_colon(universe)
    gx.to_csv(OUT / "结肠表达过滤_基因表.csv", index=False, encoding="utf-8-sig")
    expressed = set(gx.loc[gx["colon_expressed_tpm_ge_1"], "gene"])

    def n_pass(x: set) -> dict:
        m = len(x & expressed)
        return {"n": len(x), "n_colon_expressed": m, "pct": round(100 * m / max(len(x), 1), 1)}

    summary = {
        "阈值": f"结肠(横/乙状任一段) median TPM ≥ {TPM_CUT}",
        "数据源": "GTEx v8 gene median TPM (2026-10-07 访问)",
        "I1_291": n_pass(s["I1"]),
        "C_main_78": n_pass(s["C_main"]),
        "C_full_126": n_pass(s["C_full"]),
        "I2_main": n_pass(s["I2_main"]),
    }

    # 干预代谢物候选稳定性：用结肠表达的 C 重算 n_C 与 Tier A 归属
    stab = []
    for tag, mfile, cset in [
        ("主面板", "复方候选干预代谢物_主面板.csv", s["C_main"]),
        ("全库敏感性", "复方候选干预代谢物_全库敏感性.csv", s["C_full"]),
    ]:
        df = pd.read_csv(ROOT / "结果文件" / "数据文件" / "预测" / mfile)
        c_colon = cset & expressed
        df["n_C_colon"] = df["C_genes"].fillna("").apply(
            lambda x: len([g for g in str(x).split(";") if g and g.upper() in {e.upper() for e in c_colon}]))
        df["still_tier_A_colon"] = (df["tier"].str.startswith("A")) & (df["n_C_colon"] > 0)
        was_a = df["tier"].str.startswith("A")
        summary[f"{tag}_TierA"] = {
            "原A": int(was_a.sum()),
            "结肠过滤后仍A": int(df["still_tier_A_colon"].sum()),
            "丢失A": sorted(df.loc[was_a & ~df["still_tier_A_colon"], "metabolite"].tolist()),
            "排名前10稳定": df.sort_values("n_C_colon", ascending=False)["metabolite"].head(10).tolist() ==
                          df.sort_values("n_C_shared_with_formula", ascending=False)["metabolite"].head(10).tolist(),
        }
        df.to_csv(OUT / f"结肠表达过滤_干预候选稳定性_{tag}.csv", index=False, encoding="utf-8-sig")

    (OUT / "结肠过滤_摘要.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
