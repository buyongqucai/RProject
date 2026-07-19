# -*- coding: utf-8 -*-
"""Patch NetPharm 01_run_sample.R for numbered stems / tables."""
from pathlib import Path

p = Path(
    r"E:\RProject\生信分析技能_BioinformaticsSkills"
    r"\03_药物计算_DrugDiscovery\网络药理学_NetworkPharmacology"
    r"\01_样例_sample\代码文件\01_run_sample.R"
)
text = p.read_text(encoding="utf-8")

# Table renames (write targets)
tab_map = {
    '"全部单药靶点_AllHerbTargets.csv"': '"04_全部单药靶点_AllHerbTargets.csv"',
    '"全部单药疾病交集_AllHerbDiseaseOverlaps.csv"': '"05_全部单药疾病交集_AllHerbDiseaseOverlaps.csv"',
    '"疾病靶点按库_DiseaseGenesByDB.csv"': '"10_疾病靶点按库_DiseaseGenesByDB.csv"',
    '"疾病靶点按库_VennFull_DiseaseGenesByDB.csv"': '"11_疾病靶点按库_VennFull_DiseaseGenesByDB.csv"',
    '"药物疾病交集_DrugDiseaseOverlap.csv"': '"02_药物疾病交集_DrugDiseaseOverlap.csv"',
    '"单药疾病交集汇总_PerHerbOverlapSummary.csv"': '"03_单药疾病交集汇总_PerHerbOverlapSummary.csv"',
    '"网络边_network.csv"': '"17_网络边_network.csv"',
    '"网络节点类型_type.csv"': '"18_网络节点类型_type.csv"',
    '"成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv"': '"06_成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv"',
    '"成分疾病交集汇总_CompoundDiseaseOverlapSummary.csv"': '"07_成分疾病交集汇总_CompoundDiseaseOverlapSummary.csv"',
    '"网络边_CompoundGene_Cytoscape.csv"': '"15_网络边_CompoundGene_Cytoscape.csv"',
    '"网络节点_CompoundGene_Cytoscape.csv"': '"16_网络节点_CompoundGene_Cytoscape.csv"',
    '"成分疾病交集质控_CompoundOverlapQC.csv"': '"08_成分疾病交集质控_CompoundOverlapQC.csv"',
    '"交集核对_OverlapIntegrity.csv"': '"12_交集核对_OverlapIntegrity.csv"',
    '"外部图断点清单_ExternalFigureBreakpoints.csv"': '"21_外部图断点清单_ExternalFigureBreakpoints.csv"',
    '"PPI互作_StringInteractions_score900.tsv"': '"19_PPI互作_StringInteractions_score900.tsv"',
}
for a, b in tab_map.items():
    text = text.replace(a, b)

# Audit numbered
text = text.replace(
    'out_path = file.path(tab_dir, delivery_audit_name(skill_en, "post"))',
    'out_path = file.path(tab_dir, delivery_with_order(delivery_audit_name(skill_en, "post"), 1))',
)
text = text.replace(
    'audit_path <- file.path(tab_dir, delivery_audit_name(skill_en, "post"))',
    'audit_path <- file.path(tab_dir, delivery_with_order(delivery_audit_name(skill_en, "post"), 1))',
)
text = text.replace(
    "<code>外部图断点清单_ExternalFigureBreakpoints.csv</code>",
    "<code>21_外部图断点清单_ExternalFigureBreakpoints.csv</code>",
)

# Figure order map: (theme_or_unique, order)
# Replace delivery_save_plot / delivery_stem calls carefully
replacements = [
    (
        'delivery_save_plot(p_venn_dis, skill_en, "venn", "DiseaseDatabases", 6.5, 8.0, fig_dir, bio_root)',
        'delivery_save_plot(p_venn_dis, skill_en, "venn", "DiseaseDatabases", 6.5, 8.0, fig_dir, bio_root, order = 1)',
    ),
    (
        'delivery_save_plot(p_venn_dd, skill_en, "venn", "DrugDisease", 6.0, 7.2, fig_dir, bio_root)',
        'delivery_save_plot(p_venn_dd, skill_en, "venn", "DrugDisease", 6.0, 7.2, fig_dir, bio_root, order = 2)',
    ),
    (
        'delivery_save_plot(p_herb, skill_en, "bar", "PerHerbDiseaseOverlap", 6.0, 4.8, fig_dir, bio_root)',
        'delivery_save_plot(p_herb, skill_en, "bar", "PerHerbDiseaseOverlap", 6.0, 4.8, fig_dir, bio_root, order = 3)',
    ),
    (
        'delivery_stem(skill_en, "venn", "DiseaseDatabases")',
        'delivery_stem(skill_en, "venn", "DiseaseDatabases", order = 1)',
    ),
    (
        'delivery_stem(skill_en, "venn", "DrugDisease")',
        'delivery_stem(skill_en, "venn", "DrugDisease", order = 2)',
    ),
    (
        'delivery_stem(skill_en, "bar", "PerHerbDiseaseOverlap")',
        'delivery_stem(skill_en, "bar", "PerHerbDiseaseOverlap", order = 3)',
    ),
    (
        'delivery_save_plot(p_ct, skill_en, "bar", "CompoundDiseaseOverlap", 14.0, h_ct, fig_dir, bio_root)',
        'delivery_save_plot(p_ct, skill_en, "bar", "CompoundDiseaseOverlap", 14.0, h_ct, fig_dir, bio_root, order = 4)',
    ),
    (
        'delivery_stem(skill_en, "bar", "CompoundDiseaseOverlap")',
        'delivery_stem(skill_en, "bar", "CompoundDiseaseOverlap", order = 4)',
    ),
    (
        'p_ct_h, skill_en, "bar", "CompoundDiseaseOverlapByHerb", 14.0, h_ct_h, fig_dir, bio_root',
        'p_ct_h, skill_en, "bar", "CompoundDiseaseOverlapByHerb", 14.0, h_ct_h, fig_dir, bio_root, order = 5',
    ),
    (
        'delivery_stem(skill_en, "bar", "CompoundDiseaseOverlapByHerb")',
        'delivery_stem(skill_en, "bar", "CompoundDiseaseOverlapByHerb", order = 5)',
    ),
    (
        'delivery_save_plot(p_go_b, skill_en, "bubble", "GO_BPCCMF", 10.0, 9.5, fig_dir, bio_root)',
        'delivery_save_plot(p_go_b, skill_en, "bubble", "GO_BPCCMF", 10.0, 9.5, fig_dir, bio_root, order = 6)',
    ),
    (
        'delivery_save_plot(p_go_bar, skill_en, "bar", "GO_BPCCMF", 11.0, 7.5, fig_dir, bio_root)',
        'delivery_save_plot(p_go_bar, skill_en, "bar", "GO_BPCCMF", 11.0, 7.5, fig_dir, bio_root, order = 7)',
    ),
    (
        'delivery_stem(skill_en, "bubble", "GO_BPCCMF")',
        'delivery_stem(skill_en, "bubble", "GO_BPCCMF", order = 6)',
    ),
    (
        'delivery_stem(skill_en, "bar", "GO_BPCCMF")',
        'delivery_stem(skill_en, "bar", "GO_BPCCMF", order = 7)',
    ),
    (
        'delivery_save_plot(p_kegg_l, skill_en, "lollipop", "KEGG_Pathways", 10.5, 8.5, fig_dir, bio_root)',
        'delivery_save_plot(p_kegg_l, skill_en, "lollipop", "KEGG_Pathways", 10.5, 8.5, fig_dir, bio_root, order = 8)',
    ),
    (
        'delivery_save_plot(p_kegg_b, skill_en, "bar", "KEGG_Pathways", 10.5, 8.5, fig_dir, bio_root)',
        'delivery_save_plot(p_kegg_b, skill_en, "bar", "KEGG_Pathways", 10.5, 8.5, fig_dir, bio_root, order = 9)',
    ),
    (
        'delivery_stem(skill_en, "lollipop", "KEGG_Pathways")',
        'delivery_stem(skill_en, "lollipop", "KEGG_Pathways", order = 8)',
    ),
    (
        'delivery_stem(skill_en, "bar", "KEGG_Pathways")',
        'delivery_stem(skill_en, "bar", "KEGG_Pathways", order = 9)',
    ),
    (
        'circ_stem <- delivery_stem(skill_en, "circos", "KEGG")',
        'circ_stem <- delivery_stem(skill_en, "circos", "KEGG", order = 10)',
    ),
    (
        'p_hctp, skill_en, "network", "HerbCompoundTargetPathway",\n      12.5, 9.5, fig_dir, bio_root',
        'p_hctp, skill_en, "network", "HerbCompoundTargetPathway",\n      12.5, 9.5, fig_dir, bio_root, order = 11',
    ),
    (
        'delivery_stem(skill_en, "network", "HerbCompoundTargetPathway")',
        'delivery_stem(skill_en, "network", "HerbCompoundTargetPathway", order = 11)',
    ),
    (
        'stem_ppi <- delivery_stem(skill_en, "network", "StringPPI")',
        'stem_ppi <- delivery_stem(skill_en, "network", "StringPPI", order = 13)',
    ),
    (
        'p_ppi, skill_en, "network", "StringPPI_Concentric", 11.0, 10.0, fig_dir, bio_root',
        'p_ppi, skill_en, "network", "StringPPI_Concentric", 11.0, 10.0, fig_dir, bio_root, order = 14',
    ),
    (
        'delivery_stem(skill_en, "network", "StringPPI_Concentric")',
        'delivery_stem(skill_en, "network", "StringPPI_Concentric", order = 14)',
    ),
    (
        'delivery_save_plot(p_ppi, skill_en, "network", "StringPPI", 11.0, 10.0, fig_dir, bio_root)',
        'delivery_save_plot(p_ppi, skill_en, "network", "StringPPI", 11.0, 10.0, fig_dir, bio_root, order = 13)',
    ),
]

for a, b in replacements:
    if a not in text:
        print("MISSING:", a[:80])
    else:
        text = text.replace(a, b)

p.write_text(text, encoding="utf-8")
print("patched", p.name)
