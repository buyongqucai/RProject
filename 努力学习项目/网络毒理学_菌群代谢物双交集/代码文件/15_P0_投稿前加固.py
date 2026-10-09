# -*- coding: utf-8 -*-
"""15_P0_投稿前加固.py —— P0-1 高危D子集敏感性 + P0-2 UC vs 克罗恩特异性对照

预登记（在计算交集前确定）：
- HC-D（高置信疾病靶点）= D(1517) 中被 ≥2 个来源库支持的基因（来源：GeneCards/TTD/DrugBank/OMIM/CTD，
  见 交付文件/数据文件/疾病/疾病靶点按库.csv）。分布：≥1库1364、≥2库153、≥3库8 → 取 ≥2（n=153）。
- Open Targets 关联分数阈值 ≥0.1（主），≥0.3（严格对照）；UC=MONDO_0005101，CD=MONDO_0005011（OLS4 核验）。
- 结论边界：特异性/敏感性均为方法学稳健性检查，不改变冻结口径 D=1517 主分析。

输出：结果文件/数据文件/P0加固/ + 控制台摘要
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pandas as pd
from scipy.stats import fisher_exact, hypergeom

ROOT = Path(__file__).resolve().parents[1]
DELIV = ROOT.parent / "交付文件"
OUT = ROOT / "结果文件" / "数据文件" / "P0加固"
OUT.mkdir(parents=True, exist_ok=True)
OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"
N_SRC_MIN = 2
OT_CUTS = (0.1, 0.3)


def hyper_p(k: int, K: int, n: int, N: int) -> float:
    return float(hypergeom.sf(k - 1, N, K, n)) if k and N else 1.0


# ---------- P0-1 ----------
def hc_sensitivity() -> dict:
    src = pd.read_csv(DELIV / "数据文件/疾病/疾病靶点按库.csv", encoding="utf-8-sig")
    D = set(pd.read_csv(DELIV / "数据文件/疾病/疾病靶点合并.csv", encoding="utf-8-sig")["gene"])
    F = set(pd.read_csv(DELIV / "数据文件/药物/药物靶点_全药.csv", encoding="utf-8-sig")["gene"])
    I1 = set(pd.read_csv(DELIV / "数据文件/药物/药物疾病交集.csv", encoding="utf-8-sig")["gene"])
    Mdf = pd.read_csv(ROOT / "结果文件" / "数据文件" / "代谢物/M_主面板靶点.csv", encoding="utf-8-sig")
    M = set(Mdf["gene"])
    C = set(pd.read_csv(ROOT / "结果文件" / "数据文件" / "C_main_evidence_priority_H_plus_M.csv", encoding="utf-8-sig")["gene"])

    nsrc = src.groupby("gene")["source"].nunique()
    HC = {g for g in D if nsrc.get(g, 0) >= N_SRC_MIN}
    assert HC <= D

    I1_hc, I2_hc = F & HC, M & HC
    C_hc = I1_hc & I2_hc                     # == C ∩ HC-D
    p = hyper_p(len(C_hc), len(I1_hc), len(I2_hc), len(HC))
    jac = len(C_hc & C) / len(C_hc | C) if (C_hc | C) else 0.0

    # Tier A 稳定性（主面板，H+M）
    tierA = pd.read_csv(ROOT / "结果文件" / "数据文件" / "预测/复方候选干预代谢物_主面板.csv", encoding="utf-8-sig")
    a = tierA[tierA["tier"].str.startswith("A")].copy()
    hc_str = {g.upper() for g in C_hc}
    a["n_C_hc"] = a["C_genes"].fillna("").apply(
        lambda s: sum(1 for g in str(s).split(";") if g and g.upper() in hc_str))
    still = a[a["n_C_hc"] > 0]
    lost = sorted(a.loc[a["n_C_hc"] == 0, "metabolite"].tolist())
    top20_hc = still.sort_values("n_C_hc", ascending=False)["metabolite"].head(10).tolist()

    res = {
        "预登记": f"HC-D = D中≥{N_SRC_MIN}库支持",
        "HC_D_n": len(HC), "I1_hc": len(I1_hc), "I2_hc": len(I2_hc),
        "C_hc": len(C_hc), "C_retention": f"{len(C_hc)}/{len(C)}",
        "hypergeom_p_universe_HC_D": p,
        "jaccard_C_hc_vs_C": round(jac, 3),
        "C_hc_genes": sorted(C_hc),
        "TierA_原": int(len(a)), "TierA_HC下仍A": int(len(still)),
        "TierA_丢失": lost, "TierA_HC下Top10": top20_hc,
    }
    pd.DataFrame({"gene": sorted(C_hc)}).to_csv(OUT / "C_HC_D子集.csv", index=False,
                                                encoding="utf-8-sig")
    return res


# ---------- P0-2 ----------
def ot_targets(doid: str) -> set[str]:
    q = """
    query($efoId: String!, $idx: Int!, $size: Int!) {
      disease(efoId: $efoId) {
        associatedTargets(page: {index: $idx, size: $size}) {
          count
          rows { score target { approvedSymbol } }
        }
      }
    }"""
    genes: set[str] = set()
    idx, size = 0, 1000
    while True:
        payload = {"query": q, "variables": {"efoId": doid, "idx": idx, "size": size}}
        req = urllib.request.Request(OT_URL, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "Mozilla/5.0"})
        d = json.load(urllib.request.urlopen(req, timeout=60))
        at = (d.get("data", {}).get("disease") or {}).get("associatedTargets") or {}
        rows = at.get("rows") or []
        for r in rows:
            if r["score"] >= OT_CUTS[0] and r["target"]["approvedSymbol"]:
                genes.add(r["target"]["approvedSymbol"])
        idx += 1
        if not rows or idx * size >= (at.get("count") or 0):
            break
    return genes


def ot_targets_scored(doid: str) -> dict[str, float]:
    q = """
    query($efoId: String!, $idx: Int!, $size: Int!) {
      disease(efoId: $efoId) {
        associatedTargets(page: {index: $idx, size: $size}) {
          count
          rows { score target { approvedSymbol } }
        }
      }
    }"""
    out: dict[str, float] = {}
    idx, size = 0, 1000
    while True:
        payload = {"query": q, "variables": {"efoId": doid, "idx": idx, "size": size}}
        req = urllib.request.Request(OT_URL, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "Mozilla/5.0"})
        d = json.load(urllib.request.urlopen(req, timeout=60))
        at = (d.get("data", {}).get("disease") or {}).get("associatedTargets") or {}
        rows = at.get("rows") or []
        for r in rows:
            s = r["target"]["approvedSymbol"]
            if s:
                out[s] = max(out.get(s, 0.0), float(r["score"]))
        idx += 1
        if not rows or idx * size >= (at.get("count") or 0):
            break
    return out


def specificity() -> dict:
    C = set(pd.read_csv(ROOT / "结果文件" / "数据文件" / "C_main_evidence_priority_H_plus_M.csv", encoding="utf-8-sig")["gene"])
    I1 = set(pd.read_csv(DELIV / "数据文件/药物/药物疾病交集.csv", encoding="utf-8-sig")["gene"])
    D = set(pd.read_csv(DELIV / "数据文件/疾病/疾病靶点合并.csv", encoding="utf-8-sig")["gene"])

    uc = ot_targets_scored("MONDO_0005101")
    cd = ot_targets_scored("MONDO_0005011")
    res = {"UC_OT_all": len(uc), "CD_OT_all": len(cd)}
    U = set(uc) | set(cd)

    for cut in OT_CUTS:
        Uset, Cset = {g for g, s in uc.items() if s >= cut}, {g for g, s in cd.items() if s >= cut}
        inter = Uset & Cset
        tag = f"score_ge_{cut}"
        block = {"UC_n": len(Uset), "CD_n": len(Cset),
                 "UC∩CD": len(inter),
                 "C_in_UC": len(C & Uset), "C_in_CD": len(C & Cset),
                 "C_pct_UC": round(100 * len(C & Uset) / len(C), 1),
                 "C_pct_CD": round(100 * len(C & Cset) / len(C), 1),
                 "I1_in_UC": len(I1 & Uset), "I1_in_CD": len(I1 & Cset),
                 "D_in_UC": len(D & Uset), "D_in_CD": len(D & Cset)}
        # 宇宙 = OT两病并集内全部基因；C 在 UC/CD 各自的超几何
        N = len(U)
        block["hypergeom_C_in_UC"] = hyper_p(len(C & Uset), len(Uset), len(C), N)
        block["hypergeom_C_in_CD"] = hyper_p(len(C & Cset), len(Cset), len(C), N)
        # C 是否偏好 UC 而非 CD（Fisher 双侧）
        a = len(C & (Uset - Cset)); b = len(C & (Cset - Uset))
        c = len((C - Uset) & (Cset - Uset)) if False else len((U - C) & (Uset - Cset))
        d_ = len((U - C) & (Cset - Uset))
        # 简明2×2：行=C/非C（在U内），列=仅UC/仅CD（互斥化处理各自成员）
        only_uc = Uset - Cset; only_cd = Cset - Uset
        t = [[len(C & only_uc), len(C & only_cd)],
             [len((U - C) & only_uc), len((U - C) & only_cd)]]
        odds, p_f = fisher_exact(t)
        block["fisher_C_UC_vs_CD"] = {"table": t, "odds_ratio": odds, "p": p_f}
        res[tag] = block

    # D 集合在两病上的对称比较（补充）
    res["D_vs_both_ge_0.1"] = {
        "D_in_UC": len(D & {g for g, s in uc.items() if s >= 0.1}),
        "D_in_CD": len(D & {g for g, s in cd.items() if s >= 0.1}),
    }
    (OUT / "UC_CD_OT靶点集.json").write_text(json.dumps(
        {"UC_ge0.1": sorted(g for g, s in uc.items() if s >= 0.1),
         "CD_ge0.1": sorted(g for g, s in cd.items() if s >= 0.1)},
        ensure_ascii=False), encoding="utf-8")
    return res


def main() -> None:
    r1 = hc_sensitivity()
    print("=== P0-1 高危D子集敏感性 ===")
    print(json.dumps(r1, ensure_ascii=False, indent=1))
    r2 = specificity()
    print("=== P0-2 UC vs CD 特异性（Open Targets）===")
    print(json.dumps(r2, ensure_ascii=False, indent=1))
    (OUT / "P0_加固结果.json").write_text(
        json.dumps({"P0_1_HC_D": r1, "P0_2_UC_CD": r2}, ensure_ascii=False, indent=2),
        encoding="utf-8")


if __name__ == "__main__":
    main()
