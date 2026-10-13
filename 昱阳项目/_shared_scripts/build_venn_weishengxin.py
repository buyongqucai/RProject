# -*- coding: utf-8 -*-
"""昱阳韦恩：调用网药微生信模板库 weishengxin_venn_lib（FROZEN §G）。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

LIB = (
    Path(r"E:/RProject/生信分析技能_BioinformaticsSkills")
    / "03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/脚本_scripts"
)
sys.path.insert(0, str(LIB))
from weishengxin_venn_lib import build_two_set_svg, write_venn_pair  # noqa: E402

YY = Path(r"E:/RProject/昱阳项目")


def _genes(series) -> list[str]:
    return [str(x).strip() for x in series if str(x).strip() and str(x).strip().lower() != "nan"]


def _truthy(s: pd.Series) -> pd.Series:
    if s.dtype == bool:
        return s
    return s.astype(str).str.strip().str.lower().isin(["true", "1", "yes", "t"])


def expanded() -> None:
    arm = YY / "03_补充口径_Expanded_MultiSource"
    gate = arm / "01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/02_结果数据_ResultTables"
    fig = arm / "03_富集与PPI_EnrichPPI/03_图片文件_Figures"
    tab = arm / "03_富集与PPI_EnrichPPI/01_数据文件_Data/02_结果数据_ResultTables"
    fig.mkdir(parents=True, exist_ok=True)
    tab.mkdir(parents=True, exist_ok=True)

    dis = pd.read_csv(gate / "18_疾病基因并集_DEG_CTD_Mouse.csv")
    drug = pd.read_csv(gate / "15_药靶小鼠_DrugTargets_Mouse.csv")
    if "in_DEG" in dis.columns and "in_CTD" in dis.columns:
        deg = _genes(dis.loc[_truthy(dis["in_DEG"]), "gene_mouse"])
        ctd = _genes(dis.loc[_truthy(dis["in_CTD"]), "gene_mouse"])
    else:
        deg_t = pd.read_csv(gate / "05_差异基因_DEG_mainThreshold.csv")
        ctd_t = pd.read_csv(gate / "17_CTD_propofol_genes_mouse.csv")
        deg = _genes(deg_t["gene"])
        gcol = [c for c in ctd_t.columns if "gene" in c.lower()][0]
        ctd = _genes(ctd_t[gcol])

    drug_mm = _genes(drug["gene_mouse"]) if "gene_mouse" in drug.columns else []
    if not drug_mm:
        ortho = pd.read_csv(gate / "14_药靶人鼠映射_DrugOrtholog.csv")
        drug_mm = _genes(ortho["gene_mouse"])
    disease = sorted(set(deg) | set(ctd))

    # drop prior R / hand-rolled stems
    for p in fig.glob("*Venn*"):
        p.unlink(missing_ok=True)
    for p in fig.glob("*韦恩*"):
        p.unlink(missing_ok=True)

    # 04 DEG vs CTD — 微生信两集模板
    write_venn_pair(
        build_two_set_svg(deg, ctd, name_a="DEG", name_b="CTD"),
        fig,
        "04_韦恩图_Disease_DEG_vs_CTD_Venn",
    )
    # 05 Drug vs Disease — 微生信药病模板（标准 Drugs/Disease 标签）
    write_venn_pair(
        build_two_set_svg(drug_mm, disease, name_a="Drugs", name_b="Disease"),
        fig,
        "05_韦恩图_DrugDisease_Venn",
    )

    # 3-set Exp/Pred/DEG：无微生信三圈模板；交付主图为上两张。写计数备查。
    ov = pd.read_csv(gate / "19_药靶与疾病交集_DrugDiseaseOverlap.csv")
    exp_dis = _genes(ov.loc[_truthy(ov["experimental"]), "gene_mouse"]) if "experimental" in ov.columns else []
    pred_dis = _genes(ov.loc[_truthy(ov["predicted"]), "gene_mouse"]) if "predicted" in ov.columns else []
    deg_ov = _genes(ov.loc[_truthy(ov["in_DEG"]), "gene_mouse"]) if "in_DEG" in ov.columns else []

    pd.DataFrame(
        {
            "panel": ["DEG_vs_CTD", "Drug_vs_Disease", "Exp_Pred_DEG_counts_only"],
            "n_a": [len(set(deg)), len(set(drug_mm)), len(set(exp_dis))],
            "n_b": [len(set(ctd)), len(set(disease)), len(set(pred_dis))],
            "n_c": [None, None, len(set(deg_ov))],
            "n_intersect_ab": [
                len(set(deg) & set(ctd)),
                len(set(drug_mm) & set(disease)),
                None,
            ],
            "engine": [
                "weishengxin_two_set",
                "weishengxin_two_set",
                "no_3set_template_counts_only",
            ],
        }
    ).to_csv(tab / "05_Venn_Drug_vs_Disease_counts.csv", index=False, encoding="utf-8-sig")

    (tab / "09_Venn_summary.txt").write_text(
        "\n".join(
            [
                "Venn figures (Expanded) — NetworkPharm FROZEN §G 微生信模板",
                "engine: weishengxin_venn_lib.build_two_set_svg + Chrome rasterize + trim",
                f"04 DEG vs CTD: |DEG|={len(set(deg))} |CTD|={len(set(ctd))} |∩|={len(set(deg) & set(ctd))}",
                f"05 Drug vs Disease: |Drug|={len(set(drug_mm))} |Disease|={len(set(disease))} |∩|={len(set(drug_mm) & set(disease))}",
                f"06 Exp/Pred/DEG: counts only (no 微生信 3-set template); Exp={len(set(exp_dis))} Pred={len(set(pred_dis))} DEG={len(set(deg_ov))}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print("OK expanded weishengxin venns", "Drug∩Disease=", len(set(drug_mm) & set(disease)))


def baseline() -> None:
    arm = YY / "02_未补充口径_Baseline_STPonly"
    gate = arm / "01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/02_结果数据_ResultTables"
    fig = arm / "03_富集与PPI_EnrichPPI/03_图片文件_Figures"
    tab = arm / "03_富集与PPI_EnrichPPI/01_数据文件_Data/02_结果数据_ResultTables"
    fig.mkdir(parents=True, exist_ok=True)
    deg = pd.read_csv(gate / "05_差异基因_DEG_mainThreshold.csv")
    ortho_f = sorted(gate.glob("08_*.csv"))[0]
    ortho = pd.read_csv(ortho_f)
    drug_mm = _genes(ortho["gene_mouse"]) if "gene_mouse" in ortho.columns else _genes(ortho.iloc[:, 1])
    deg_g = _genes(deg["gene"])
    for p in list(fig.glob("*Venn*")) + list(fig.glob("*韦恩*")):
        p.unlink(missing_ok=True)
    write_venn_pair(
        build_two_set_svg(drug_mm, deg_g, name_a="Drugs", name_b="Disease"),
        fig,
        "05_韦恩图_DrugDisease_Venn",
    )
    pd.DataFrame(
        {
            "set": ["Drugs", "Disease(DEG)", "Intersection"],
            "n": [len(set(drug_mm)), len(set(deg_g)), len(set(drug_mm) & set(deg_g))],
        }
    ).to_csv(tab / "09_Venn_Drug_vs_DEG_counts.csv", index=False, encoding="utf-8-sig")
    print("OK baseline weishengxin venn", "∩=", len(set(drug_mm) & set(deg_g)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["expanded", "baseline", "both"], default="both")
    args = ap.parse_args()
    if args.arm in ("expanded", "both"):
        expanded()
    if args.arm in ("baseline", "both"):
        baseline()


if __name__ == "__main__":
    main()
