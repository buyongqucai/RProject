# -*- coding: utf-8 -*-
"""清风项目 · 轨 B 交付文件/ 打包（网药 FROZEN §0b 目录树 + 轨 A→轨 B 映射）。
只复制不改像素；入口 HTML 由 09_交付HTML报告_buildHtmlReport.py 生成。
"""
from __future__ import annotations

import shutil
from pathlib import Path

PROJ = Path(r"E:/RProject/清风项目")
FIG_SRC = PROJ / "04_富集与PPI_EnrichPPI" / "03_图片文件_Figures"
TAB = PROJ / "04_富集与PPI_EnrichPPI" / "01_数据文件_Data" / "02_结果数据_ResultTables"
SUITE = TAB / "图谱套件编号表_FigureSuiteTables"
CONTRACT = PROJ / "03_药病交集与网络_OverlapAndNetwork" / "01_数据文件_Data" / "02_结果数据_ResultTables" / "图谱契约数据_FigureContractData"
OV = PROJ / "03_药病交集与网络_OverlapAndNetwork" / "01_数据文件_Data" / "02_结果数据_ResultTables"
DISE = PROJ / "01_疾病靶点_DiseaseTargets" / "01_数据文件_Data" / "02_结果数据_ResultTables"
PPI = TAB / "PPI网络_STRING"
OUT = PROJ / "交付文件"

# 轨 A → 轨 B（§0b 映射表 + 26_build_html_report 引用名）
FIGMAP = {
    "01_韦恩图_DiseaseDatabases_Venn": "图片/韦恩图/疾病数据库可视化韦恩图",
    "02_韦恩图_DrugDisease_Venn": "图片/韦恩图/疾病药物交集韦恩图",
    "03_柱状图_PerHerbDiseaseOverlap_Bar": "图片/补充_技能扩展/单药疾病交集柱状图",
    "04_柱状图_CompoundDiseaseOverlap_Bar": "图片/补充_技能扩展/成分疾病交集柱状图",
    "05_柱状图_CompoundDiseaseOverlapByHerb_Bar": "图片/补充_技能扩展/成分疾病交集按药柱状图",
    "06_气泡图_GO_BPCCMF_Bubble": "图片/富集分析/BPCCMF气泡图",
    "07_柱状图_GO_BPCCMF_Bar": "图片/补充_技能扩展/GO_BPCCMF柱状图",
    "08_棒棒糖图_KEGG_Pathways_Lollipop": "图片/富集分析/KEGG棒棒糖图",
    "09_柱状图_KEGG_Pathways_Bar": "图片/富集分析/KEGG柱状图",
    "10_圈图_KEGG_Circos": "图片/富集分析/KEGG圈图",
    "11_网络图_HerbCompoundTargetPathway_Network": "图片/网络图/药物有效成分疾病靶点通路网络图",
    "12_网络图_HerbCompoundTargetPathway_Ellipse_Network": "图片/网络图/药物有效成分疾病靶点通路网络图_椭圆布局",
    "13_网络图_StringPPI_Network": "图片/PPI/string_vector_graphic",
    "14_网络图_StringPPI_Concentric_Network": "图片/PPI/PPI渐变图",
    "15_网络图_StringPPI_Degree_Network": "图片/PPI/PPI渐变图_Degree",
    "16_交集图_HerbCompound_UpSet": "图片/补充_技能扩展/药味成分交集UpSet图",
    "17_桑基图_HerbCompoundTargetPathway_Sankey": "图片/网络图/药成分靶点通路桑基图",
    "18_桑基图_PerCompound_Filtered_Sankey": "图片/网络图/筛选成分桑基图",
    "19_热图_HerbPathwayCoverage_Heatmap": "图片/补充_技能扩展/药味通路覆盖热图",
}


def cp(src: Path, dst: Path) -> bool:
    if not src.exists():
        print("MISS", src)
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def main() -> None:
    if "Desktop" in str(OUT) or "桌面" in str(OUT):
        raise SystemExit("Refusing Desktop path")

    # ---- 图片：轨 A → 轨 B（png + svg 同名） ----
    n_fig = 0
    for stem, rel in FIGMAP.items():
        for ext in ("png", "svg"):
            if cp(FIG_SRC / f"{stem}.{ext}", OUT / f"{rel}.{ext}"):
                n_fig += 1

    # ---- 数据 ----
    pairs = [
        (CONTRACT / "疾病靶点按库_VennFull_DiseaseGenesByDB.csv", "数据/疾病/疾病靶点按库.csv"),
        (CONTRACT / "疾病靶点按库_DiseaseGenesByDB.csv", "数据/疾病/疾病靶点按库_下游.csv"),
        (CONTRACT / "疾病靶点合并_DiseaseGenesUnion.csv", "数据/疾病/疾病靶点合并.csv"),
        (DISE / "疾病靶点质控_DiseaseQC.csv", "数据/疾病/疾病靶点质控_DiseaseQC.csv"),
        (CONTRACT / "药物去重基因_DrugGenesUnion.csv", "数据/药物/药物靶点合并.csv"),
        (CONTRACT / "药物疾病交集_DrugDiseaseOverlap.csv", "数据/药物/药物疾病交集.csv"),
        (CONTRACT / "单药疾病交集汇总_PerHerbOverlapSummary.csv", "数据/药物/单药疾病交集汇总.csv"),
        (CONTRACT / "成分重命名_CompoundRenameMap.csv", "数据/药物/成分重命名.csv"),
        (CONTRACT / "药物成分靶点_CompoundTargets.csv", "数据/药物/药物成分靶点.csv"),
        (TAB / "KEGG通路富集_EnrichKEGG.csv", "数据/富集分析/KEGG.csv"),
        (TAB / "交集功能富集_GO_BP_EnrichGOBP.csv", "数据/富集分析/GO_BP.csv"),
        (TAB / "交集功能富集_GO_CC_EnrichGOCC.csv", "数据/富集分析/GO_CC.csv"),
        (TAB / "交集功能富集_GO_MF_EnrichGOMF.csv", "数据/富集分析/GO_MF.csv"),
        (TAB / "ID映射_SYMBOL2ENTREZ.csv", "数据/富集分析/ID映射_SYMBOL2ENTREZ.csv"),
        (CONTRACT / "富集GO_BPCCMF_Bubble.csv", "数据/富集分析/GO_BPCCMF_Bubble.csv"),
        (CONTRACT / "富集KEGG_TopPathways.csv", "数据/富集分析/富集KEGG_TopPathways.csv"),
        (CONTRACT / "网络边_network.csv", "数据/网络图/network.csv"),
        (CONTRACT / "网络节点类型_type.csv", "数据/网络图/type.csv"),
        (OV / "网络节点属性_NetworkNodes.csv", "数据/网络图/网络节点属性_NetworkNodes.csv"),
        (OV / "网络边_HerbCompoundTargetPathway_Cytoscape.csv", "数据/网络图/网络边_HerbCompoundTargetPathway_Cytoscape.csv"),
        (OV / "网络节点_HerbCompoundTargetPathway_Cytoscape.csv", "数据/网络图/网络节点_HerbCompoundTargetPathway_Cytoscape.csv"),
        (SUITE / "15_网络边_CompoundGene_Cytoscape.csv", "数据/网络图/网络边_CompoundGene_Cytoscape.csv"),
        (SUITE / "16_网络节点_CompoundGene_Cytoscape.csv", "数据/网络图/网络节点_CompoundGene_Cytoscape.csv"),
        (SUITE / "06_成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv", "数据/网络图/成分疾病交集靶点.csv"),
        (SUITE / "07_成分疾病交集汇总_CompoundDiseaseOverlapSummary.csv", "数据/网络图/成分疾病交集汇总.csv"),
        (PPI / "PPI互作_StringInteractions_score900.tsv", "数据/PPI/string_interactions_short.tsv"),
        (PPI / "PPI互作_StringInteractions.tsv", "数据/PPI/string_interactions_full.tsv"),
        (PPI / "PPI节点度表_STRING900.csv", "数据/PPI/PPI节点度表_STRING900.csv"),
        (PPI / "PPI质控_PPIQC.csv", "数据/PPI/PPI质控_PPIQC.csv"),
    ]
    n_data = 0
    for src, rel in pairs:
        if cp(src, OUT / rel):
            n_data += 1

    # 单药 18 文件 → 数据/药物/单药/
    n_single = 0
    for f in sorted(CONTRACT.glob("药物_H_*")):
        if cp(f, OUT / "数据" / "药物" / "单药" / f.name):
            n_single += 1

    # 草药成分边：补 herb_zh 列（§J3 显示名映射用）
    import csv as _csv
    with open(CONTRACT / "草药成分边_HerbCompoundEdges.csv", encoding="utf-8-sig", newline="") as fh:
        hc_rows = list(_csv.DictReader(fh))
    with open(OUT / "数据/药物/草药成分边.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = _csv.DictWriter(fh, fieldnames=["herb_code", "compound_id", "herb_zh", "herb"])
        w.writeheader()
        for r in hc_rows:
            w.writerow({"herb_code": r["herb_code"], "compound_id": r["compound_id"],
                        "herb_zh": r["herb"], "herb": r["herb"]})

    # BPCCMF 合并表（ONTOLOGY 列显式补写）
    import csv
    rows = []
    for ont in ("BP", "CC", "MF"):
        p = TAB / f"交集功能富集_GO_{ont}_EnrichGO{ont}.csv"
        with open(p, encoding="utf-8-sig", newline="") as fh:
            rd = csv.DictReader(fh)
            for r in rd:
                r["ONTOLOGY"] = ont
                rows.append(r)
    if rows:
        keys = list(rows[0].keys())
        with open(OUT / "数据/富集分析/BPCCMF.csv", "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)

    # README
    (OUT / "README_轨B说明.txt").write_text(
        "清风项目 · 轨 B 客户交付包（网络药理学 FROZEN §0b 目录树）\n"
        "=====================================================\n"
        "方剂：水蛭宣痹化纤汤（水蛭/旋覆花/川芎/桃仁/浙贝母/蜜麻黄/紫苏子/黄芪/甘草）\n"
        "疾病：特发性肺纤维化 IPF（MeSH D054990）\n"
        "\n"
        "分享方式：整夹打包本 交付文件/ 目录；对方打开根目录 图注与解读说明.html 即可（全部相对路径）。\n"
        "\n"
        "目录：\n"
        "  图注与解读说明.html   ← 分享入口（统计仪表盘 + 各图解读 + KEGG Top20 画廊）\n"
        "  图片/                 ← 韦恩图 / 富集分析 / 网络图 / PPI / 补充_技能扩展 / KEGG官方通路图\n"
        "  数据/                 ← 疾病 / 药物(含单药/) / 网络图(含网络分析报告.html) / 富集分析 / PPI\n"
        "  报告/                 ← 图注与解读说明.md / _stats.json / stub\n"
        "\n"
        "口径（重要）：GeneCards 双口径——韦恩全量 9786（仅图01展示覆盖广度），\n"
        "下游过滤 Relevance>=40（4253）∪CTD_curated(22)∪OMIM(100)∪TTD(33)∪DrugBank(38)=疾病并集 4269；\n"
        "药病交集 197 = 药物靶点并集 244 ∩ 疾病并集 4269。\n"
        "验证脚注：GeneCards 原始导出 9787 行剔除非基因条目 COPD 1 条（9786）；\n"
        "CTD 直接证据 23 条剔除小鼠基因 CCL12 1 条（22 人类基因）；两处剔除均不改变主并集 4269。\n"
        "水蛭为 BATMAN-TCM 2.0 已知靶点（F2/F10/SERPINC1/SELL/SELP/HPSE，Fragmin→F2 为 HIT 证据）；\n"
        "Hirudin（水蛭素）→F2 为预测边（0.89 非 known），经用户确认不纳入主交付，仅存预测参考表。\n"
        "KEGG 官方通路图仅学术用途，遵守 https://www.kegg.jp/kegg/legal.html 。\n",
        encoding="utf-8",
    )
    print(f"DONE figs={n_fig} data={n_data} single={n_single} -> {OUT}")


if __name__ == "__main__":
    main()
