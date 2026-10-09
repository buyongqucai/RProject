# -*- coding: utf-8 -*-
"""10_复方干预代谢物预测.py

最终交付焦点（2026-10-07 用户确认）：预测复方可能干预哪些代谢物。

口径（与研究计划 SSOT 一致，D=1517 冻结口径不变）：
- F = 复方靶点（636），D = UC 疾病靶点（1517），I₁ = F ∩ D（291）
- M = 代谢物靶点（主面板 466 / 全库敏感性 632），I₂ = M ∩ D
- C = I₁ ∩ I₂ = F ∩ M ∩ D（三源共有靶点；主面板 78 / 全库 126）

判定逻辑（预登记于本脚本与报告，先于查看结果）：
  对每个代谢物 m（靶点集 T_m ⊆ M）：
    n_C = |T_m ∩ C|  —— 与复方在疾病轴上的三源共有靶点数（核心干预信号）
    n_I2 = |T_m ∩ I2| —— 疾病轴汇入数（含不与复方共有的部分）
  分层：
    A 三源核心干预候选：n_C ≥ 1
    B 疾病轴·非复方共有：n_C = 0 且 n_I2 ≥ 1
    C 未汇入疾病轴：其余
  排序：分层 → n_C ↓ → 是否含实证H边 → GMMAD2 UC 显著(FDR<0.05) → |score| ↓ → 配对优先级 ↓

结论边界（项目规范 §2）：全部表述为「候选/提示」；不写疗效、拮抗、减毒或因果结论。
输出：结果文件/数据文件/预测/复方候选干预代谢物_{主面板,全库敏感性}.csv + 干预代谢物预测_摘要.json
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]          # 网络毒理学_菌群代谢物双交集
DELIV = ROOT.parent / "交付文件"                     # 交付数据（F/D/I₁ 源头）
OUT = ROOT / "结果文件" / "数据文件" / "预测"
OUT.mkdir(parents=True, exist_ok=True)

HARMFUL = {"TMAO", "p-Cresol sulfate", "Indoxyl sulfate", "Deoxycholic acid",
           "Lithocholic acid", "LPS", "H2S", "H₂S"}


def norm_name(s: str) -> str:
    return re.sub(r"[\s_\-]+", "", str(s)).lower()


def load() -> dict:
    d = {}
    d["I1"] = set(pd.read_csv(DELIV / "数据文件/药物/药物疾病交集.csv", encoding="utf-8-sig")["gene"].dropna())
    d["C_main"] = set(pd.read_csv(ROOT / "结果文件" / "数据文件" / "C_main_evidence_priority_H_plus_M.csv", encoding="utf-8-sig")["gene"])
    d["C_full"] = set(pd.read_csv(ROOT / "结果文件" / "数据文件" / "C_full_gutmgene_human_H_plus_M.csv", encoding="utf-8-sig")["gene"])
    d["I2_main"] = set(pd.read_csv(ROOT / "结果文件" / "数据文件" / "I2_main_evidence_priority_H_plus_M.csv", encoding="utf-8-sig")["gene"])
    d["I2_full"] = set(pd.read_csv(ROOT / "结果文件" / "数据文件" / "I2_full_gutmgene_human_H_plus_M.csv", encoding="utf-8-sig")["gene"])
    d["M_main"] = pd.read_csv(ROOT / "结果文件" / "数据文件" / "代谢物/M_主面板靶点.csv", encoding="utf-8-sig")
    d["M_full"] = pd.read_csv(ROOT / "结果文件" / "数据文件" / "代谢物/M_全库敏感性靶点.csv", encoding="utf-8-sig")
    d["panel_main"] = pd.read_csv(ROOT / "结果文件" / "数据文件" / "代谢物/代谢物主面板.csv", encoding="utf-8-sig")
    d["panel_full"] = pd.read_csv(ROOT / "结果文件" / "数据文件" / "代谢物/代谢物全库敏感性.csv", encoding="utf-8-sig")
    d["benefit"] = pd.read_csv(ROOT / "结果文件" / "数据文件" / "毒性分层/代谢物有益有害分层.csv", encoding="utf-8-sig")
    d["pairs"] = pd.read_csv(ROOT / "结果文件" / "数据文件" / "机制层/核心代谢物靶点配对.csv", encoding="utf-8-sig")
    d["herb_I1"] = pd.read_csv(DELIV / "数据文件/药物/全量单药疾病交集.csv", encoding="utf-8-sig")
    d["microbe"] = pd.read_csv(ROOT / "数据文件/外部数据库/gutMGene_v2/Gut Microbe-Microbial metabolite.csv",
                               encoding="utf-8-sig", low_memory=False)
    return d


def microbe_index(df: pd.DataFrame) -> dict:
    """代谢物(名/CID) -> 人源菌列表（去重、按证据行数排序）"""
    by_cid, by_name = defaultdict(list), defaultdict(list)
    hum = df[df["human/mouse"].astype(str).str.lower().str.contains("human", na=False)]
    for _, r in hum.iterrows():
        mic = str(r.get("Gut Microbiota", "")).strip()
        if not mic or mic.lower() == "nan":
            continue
        cid, name = r.get("Metabolite PubChem CID"), str(r.get("Metabolite", ""))
        if pd.notna(cid):
            by_cid[str(int(float(cid)))].append(mic)
        by_name[norm_name(name)].append(mic)
    return {f"cid:{k}": sorted(set(v), key=v.index) for k, v in by_cid.items()} | \
           {f"name:{k}": sorted(set(v), key=v.index) for k, v in by_name.items()}


def build(M: pd.DataFrame, panel: pd.DataFrame, C: set, I2: set, I1: set,
          benefit: pd.DataFrame, pairs: pd.DataFrame, herb_I1: pd.DataFrame,
          midx: dict, tag: str) -> pd.DataFrame:
    # 代谢物注释索引
    pinfo = {}
    for _, r in panel.iterrows():
        pinfo[norm_name(r["metabolite"])] = r
    binfo = {norm_name(r["metabolite"]): r for _, r in benefit.iterrows()}
    # 配对优先级（代谢物级 max）
    pair_score = pairs.groupby(pairs["metabolite"].map(norm_name)).agg(
        pair_priority_max=("pair_priority_score", "max"),
        target_mcc_max=("target_mcc_like", "max"),
        n_core_pairs=("gene", "nunique"),
    ) if len(pairs) else pd.DataFrame()
    # 单药疾病交集：herb -> 其 I₁ 集合
    herb_genes = herb_I1.groupby("herb_zh")["gene"].apply(set).to_dict()
    herb_en = herb_I1.drop_duplicates("herb_zh").set_index("herb_zh")["herb_en"].to_dict()

    rows = []
    for met, g in M.groupby("metabolite"):
        nk = norm_name(met)
        genes = set(g["gene"].dropna())
        ev = g["evidence_level"].astype(str).value_counts().to_dict()
        nH, nM = int(ev.get("H", 0)), int(ev.get("M", 0))
        c_hits = sorted(genes & C)
        i2_hits = sorted(genes & I2)
        n_C, n_I2 = len(c_hits), len(i2_hits)
        tier = "A_三源核心干预候选" if n_C else ("B_疾病轴_非复方共有" if n_I2 else "C_未汇入疾病轴")

        p = pinfo.get(nk)
        b = binfo.get(nk)
        # GMMAD2 方向
        if p is not None:
            g_score = p.get("gmmad2_best_score")
            g_alt = p.get("gmmad2_best_alteration")
            g_fdr = p.get("gmmad2_best_fdr")
            ev_tier = p.get("evidence_tier")
            cid = p.get("pubchem_cid")
            mw = p.get("molecular_weight")
        else:
            g_score = g_alt = g_fdr = ev_tier = cid = mw = None
        # 有益/有害下游标注
        b_group = b.get("group") if b is not None else ""
        b_status = b.get("status") if b is not None else ""
        # 菌源
        microbes = midx.get(f"cid:{int(float(cid))}", None) if pd.notna(cid) and str(cid) not in ("", "nan") else None
        if microbes is None:
            microbes = midx.get(f"name:{nk}", [])
        # 与复方共有 C 基因的草药归属
        herbs = []
        if c_hits:
            cs = set(c_hits)
            for hz, gs in herb_genes.items():
                inter = gs & cs
                if inter:
                    herbs.append(f"{hz}({herb_en.get(hz, '')}):{','.join(sorted(inter))}")
        # 配对分数
        ps = pair_score.loc[nk] if len(pair_score) and nk in pair_score.index else None

        sig = pd.notna(g_fdr) and float(g_fdr) < 0.05
        rows.append({
            "metabolite": met,
            "tier": tier,
            "n_C_shared_with_formula": n_C,
            "C_genes": ";".join(c_hits),
            "n_targets_in_I2": n_I2,
            "n_targets_total": len(genes),
            "n_evidence_H": nH,
            "n_evidence_M": nM,
            "evidence_tier": ev_tier,
            "has_experimental_H": nH > 0,
            "gmmad2_uc_score": g_score,
            "gmmad2_uc_alteration": g_alt,
            "gmmad2_uc_fdr": g_fdr,
            "gmmad2_uc_significant": sig,
            "beneficial_harmful_group": b_group,
            "beneficial_harmful_status": b_status,
            "is_harmful_exposure": met in HARMFUL,
            "gut_microbes_human": ";".join(microbes[:8]) if microbes else "",
            "n_gut_microbes": len(microbes) if microbes else 0,
            "formula_herbs_sharing_C": " | ".join(herbs[:6]),
            "n_formula_herbs": len(herbs),
            "pair_priority_max": float(ps["pair_priority_max"]) if ps is not None else None,
            "target_mcc_max": float(ps["target_mcc_max"]) if ps is not None else None,
            "n_core_pairs": int(ps["n_core_pairs"]) if ps is not None else 0,
            "pubchem_cid": cid,
            "molecular_weight": mw,
            "panel": tag,
        })

    df = pd.DataFrame(rows)
    df["_t"] = df["tier"].str[0]
    df["_sig"] = df["gmmad2_uc_significant"].astype(int)
    df["_abs"] = df["gmmad2_uc_score"].abs().fillna(-1)
    df = df.sort_values(
        ["_t", "n_C_shared_with_formula", "has_experimental_H", "_sig", "_abs",
         "pair_priority_max", "n_targets_total"],
        ascending=[True, False, False, False, False, False, False],
    ).drop(columns=["_t", "_sig", "_abs"]).reset_index(drop=True)
    return df


def main() -> None:
    d = load()
    midx = microbe_index(d["microbe"])
    I1 = d["I1"]

    main_df = build(d["M_main"], d["panel_main"], d["C_main"], d["I2_main"], I1,
                    d["benefit"], d["pairs"], d["herb_I1"], midx, "主面板")
    full_df = build(d["M_full"], d["panel_full"], d["C_full"], d["I2_full"], I1,
                    d["benefit"], d["pairs"], d["herb_I1"], midx, "全库敏感性")

    main_df.to_csv(OUT / "复方候选干预代谢物_主面板.csv", index=False, encoding="utf-8-sig")
    full_df.to_csv(OUT / "复方候选干预代谢物_全库敏感性.csv", index=False, encoding="utf-8-sig")

    def summary(df: pd.DataFrame) -> dict:
        a = df[df["tier"].str.startswith("A")]
        return {
            "n_metabolites": int(len(df)),
            "tier_A": int(len(a)),
            "tier_B": int((df["tier"].str.startswith("B")).sum()),
            "tier_C": int((df["tier"].str.startswith("C")).sum()),
            "A_with_experimental_H": int(a["has_experimental_H"].sum()),
            "A_gmmad2_significant": int(a["gmmad2_uc_significant"].sum()),
            "A_harmful": int(a["is_harmful_exposure"].sum()),
            "A_top10": a["metabolite"].head(10).tolist(),
        }

    out = {"口径": "D=1517 冻结；C=I₁∩I₂；预测=候选/提示，无疗效结论",
           "主面板": summary(main_df), "全库敏感性": summary(full_df)}
    (OUT / "干预代谢物预测_摘要.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(out, ensure_ascii=False, indent=2))
    a = main_df[main_df["tier"].str.startswith("A")]
    print("\n=== Tier A 前15（主面板）===")
    cols = ["metabolite", "n_C_shared_with_formula", "C_genes", "n_evidence_H",
            "gmmad2_uc_alteration", "gmmad2_uc_significant", "beneficial_harmful_status"]
    print(a[cols].head(15).to_string(index=False))


if __name__ == "__main__":
    main()
