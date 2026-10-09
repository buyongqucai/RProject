# -*- coding: utf-8 -*-
"""16_方向一致性分析.py —— P1-2 三层方向一致性（代谢物丰度方向 × 代谢物→靶点作用方向 × 靶点疾病表达方向）

三层数据（全部既有）：
  ① 代谢物在 UC 中的丰度方向：GMMAD2 best alteration（面板表，Increase/Decrease）
  ② 代谢物→基因 实验作用方向：gutMGene H 边 alteration（activation/inhibition；仅 H 边有方向）
  ③ 基因在 UC 中的表达方向：GEO 双队列 logFC（仅采用 direction_consistent=TRUE 的基因；主队列 GSE92415）

判定（预登记）：对代谢物 m 的每个共有 C 基因 g——
  action = sign(①) × sign(②)   # 代谢物 UC 丰度变化按其作用方向“推”基因的方向
  action == sign(③) → concordant（同向：代谢物变化方向与疾病中该基因变化一致）
  action != sign(③) → discordant（反向）；② 或 ③ 缺失/不一致 → unknown
分层：仅 Tier A 代谢物；同时标记 HC-D 稳健核心。

结论边界：三层一致性是**方向提示**，不是疗效/调控结论（项目规范 §2）；
gutMGene 作用方向多来自体外/细胞实验，GMMAD2 丰度≠产生速率，横断面不能推因果。
输出：结果文件/数据文件/方向一致性/
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "结果文件" / "数据文件" / "方向一致性"
OUT.mkdir(parents=True, exist_ok=True)


def sgn(x: float) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


def main() -> None:
    tierA = pd.read_csv(ROOT / "结果文件" / "数据文件" / "预测/复方候选干预代谢物_主面板.csv", encoding="utf-8-sig")
    a = tierA[tierA["tier"].str.startswith("A")].copy()
    geo = pd.read_csv(ROOT / "结果文件" / "数据文件" / "GEO验证/GEO_core_gene_consistency.csv", encoding="utf-8-sig")
    mtab = pd.read_csv(ROOT / "结果文件" / "数据文件" / "代谢物/M_主面板靶点.csv", encoding="utf-8-sig")

    geo_ix = {r["gene"]: r for _, r in geo.iterrows()}
    # H 边方向：(metabolite, gene) -> +1 activation / -1 inhibition
    h = mtab[(mtab.evidence_level == "H") & mtab.alteration.notna()]
    edge_dir = {(str(r.metabolite).lower(), r.gene): (1 if r.alteration == "activation" else -1)
                for r in h.itertuples()}

    rows = []
    for r in a.itertuples():
        alt = str(r.gmmad2_uc_alteration)
        m_sign = 1 if alt.lower() == "increase" else (-1 if alt.lower() == "decrease" else None)
        c_genes = [g for g in str(r.C_genes).split(";") if g]
        n_con = n_dis = n_unk_edge = n_unk_geo = 0
        for g in c_genes:
            e = edge_dir.get((str(r.metabolite).lower(), g))
            grow = geo_ix.get(g)
            geo_consistent = grow is not None and bool(grow["direction_consistent"])
            if geo_consistent:
                g_sign = sgn(float(grow["logFC_GSE92415"]))
            else:
                g_sign = None
            if m_sign is None or e is None:
                n_unk_edge += 1
                verdict = "unknown_edge" if e is None else "unknown_metabolite_dir"
            elif g_sign is None:
                n_unk_geo += 1
                verdict = "unknown_geo"
            else:
                conc = (m_sign * e) == g_sign
                n_con += conc
                n_dis += (not conc)
                verdict = "concordant" if conc else "discordant"
            rows.append({"metabolite": r.metabolite, "gene": g, "tier": r.tier,
                         "in_HC_D_robust_core": bool(r.in_HC_D_robust_core),
                         "metabolite_dir_UC": alt, "edge_effect": e,
                         "gene_logFC_GSE92415": (float(grow["logFC_GSE92415"])
                                                 if grow is not None else None),
                         "gene_logFC_GSE75214": (float(grow["logFC_GSE75214"])
                                                 if grow is not None else None),
                         "gene_direction_consistent": geo_consistent,
                         "verdict": verdict})
        if n_con + n_dis == 0:
            label = "方向未知（仅预测边/方向缺失）"
        elif n_dis == 0:
            label = "方向一致（同向）"
        elif n_con == 0:
            label = "方向相反（反向）"
        else:
            label = "方向混合"
        rows.append({"metabolite": r.metabolite, "gene": "__SUMMARY__", "tier": r.tier,
                     "in_HC_D_robust_core": bool(r.in_HC_D_robust_core),
                     "metabolite_dir_UC": alt, "edge_effect": None,
                     "gene_logFC_GSE92415": None, "gene_logFC_GSE75214": None,
                     "gene_direction_consistent": None, "verdict": label,
                     "n_concordant": n_con, "n_discordant": n_dis,
                     "n_unknown_edge": n_unk_edge, "n_unknown_geo": n_unk_geo})

    det = pd.DataFrame(rows)
    det.to_csv(OUT / "方向一致性_配对明细.csv", index=False, encoding="utf-8-sig")
    summ = det[det.gene == "__SUMMARY__"].copy()
    summ.to_csv(OUT / "方向一致性_代谢物汇总.csv", index=False, encoding="utf-8-sig")

    known = summ[summ.verdict.str.startswith(("方向一致", "方向相反", "方向混合"))]
    dist = summ.verdict.value_counts().to_dict()
    summary = {
        "TierA代谢物": int(len(summ)),
        "判定分布": {k: int(v) for k, v in dist.items()},
        "有可判定方向的代谢物": int(len(known)),
        "方向一致者": known.loc[known.verdict.str.startswith("方向一致"), "metabolite"].tolist(),
        "方向相反者": known.loc[known.verdict.str.startswith("方向相反"), "metabolite"].tolist(),
        "方向混合者": known.loc[known.verdict.str.startswith("方向混合"), "metabolite"].tolist(),
        "边界": "方向提示，不作调控/疗效结论",
    }
    (OUT / "方向一致性_摘要.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
