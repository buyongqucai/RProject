# -*- coding: utf-8 -*-
"""Pack UC NetPharm atlas into project-local 交付文件/ (Track B Chinese names).

Does NOT write to Desktop. Source of truth = Track A stems under 代码文件/结果文件/.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")
FIG = ROOT / "代码文件" / "结果文件" / "图片文件"
TAB = ROOT / "代码文件" / "结果文件" / "数据文件"
DATA = ROOT / "数据文件"
OUT = ROOT / "交付文件"

# Track A stem (no ext) -> Track B relative path (no ext)
FIG_MAP = {
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

# Track B data tree: 数据/{疾病,药物,网络图,富集分析,PPI}/
DATA_MAP = [
    # 疾病
    (DATA / "疾病靶点按库_VennFull_DiseaseGenesByDB.csv", "数据/疾病/疾病靶点按库.csv"),
    (DATA / "疾病靶点按库_DiseaseGenesByDB.csv", "数据/疾病/疾病靶点按库_下游.csv"),
    (DATA / "疾病靶点合并_DiseaseGenesUnion.csv", "数据/疾病/疾病靶点合并.csv"),
    # 药物（汇总）
    (DATA / "药物去重基因_DrugGenesUnion.csv", "数据/药物/药物靶点合并.csv"),
    (DATA / "药物靶点_全药_AllHerbTargets.csv", "数据/药物/药物靶点_全药.csv"),
    (DATA / "药物疾病交集_DrugDiseaseOverlap.csv", "数据/药物/药物疾病交集.csv"),
    (DATA / "单药疾病交集汇总_PerHerbOverlapSummary.csv", "数据/药物/单药疾病交集汇总.csv"),
    (DATA / "全量单药疾病交集_AllHerbDiseaseOverlaps.csv", "数据/药物/全量单药疾病交集.csv"),
    (DATA / "药物成分靶点_CompoundTargets.csv", "数据/药物/成分靶点.csv"),
    (DATA / "草药成分边_HerbCompoundEdges.csv", "数据/药物/草药成分边.csv"),
    (DATA / "成分重命名_CompoundRenameMap.csv", "数据/药物/成分重命名.csv"),
    # 网络 / 富集 / PPI
    (TAB / "06_成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv", "数据/网络图/药物疾病交集靶点.csv"),
    (TAB / "19_PPI互作_StringInteractions_score900.tsv", "数据/PPI/string_interactions_short.tsv"),
    (DATA / "网络边_network.csv", "数据/网络图/network.csv"),
    (DATA / "网络节点类型_type.csv", "数据/网络图/type.csv"),
    (DATA / "富集KEGG_TopPathways.csv", "数据/富集分析/KEGG.csv"),
    (DATA / "富集GO_BPCCMF_Bubble.csv", "数据/富集分析/BPCCMF.csv"),
    (DATA / "富集GO_BPCCMF.csv", "数据/富集分析/BPCCMF.csv"),
]

# code -> 中文 short name for per-herb Track B files
HERB_CODE_ZH = {
    "BanXia": "半夏",
    "FuLing": "茯苓",
    "MuXiang": "木香",
    "HuangLian": "黄连",
    "GanJiang": "干姜",
    "YinYangHuo": "淫羊藿",
    "HuangQin": "黄芩",
    "RouGui": "肉桂",
    "RenShen": "人参",
    "BaiZhu": "白术",
    "XiangFu": "香附",
    "ZongLvTan": "棕榈炭",
}


def copy_fig(stem: str, dest_rel: str) -> None:
    for ext in (".svg", ".png"):
        src = FIG / f"{stem}{ext}"
        if not src.exists():
            continue
        dst = OUT / f"{dest_rel}{ext}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print("FIG", src.name, "->", dst.relative_to(OUT).as_posix())


def copy_data(src: Path, rel: str) -> None:
    if not src.exists():
        print("SKIP missing", src)
        return
    dst = OUT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print("DATA", src.name, "->", rel)


def pack_per_herb() -> None:
    """Copy 药物_{code}_*.csv → 数据/药物/单药/{中文}_靶点|疾病交集.csv"""
    for code, zh in HERB_CODE_ZH.items():
        pairs = [
            (DATA / f"药物_{code}_靶点基因_HerbTargets.csv", f"数据/药物/单药/{zh}_靶点.csv"),
            (DATA / f"药物_{code}_疾病交集_HerbDiseaseOverlap.csv", f"数据/药物/单药/{zh}_疾病交集.csv"),
        ]
        for src, rel in pairs:
            copy_data(src, rel)


def main() -> None:
    if "Desktop" in str(OUT) or "桌面" in str(OUT):
        raise SystemExit("Refusing to write to Desktop")
    # Safety: only allow project-local 交付文件 under 努力学习项目/网络药理学
    out_n = OUT.resolve()
    root_n = ROOT.resolve()
    if root_n not in out_n.parents and out_n != root_n / "交付文件":
        # OUT must be ROOT/交付文件
        if out_n != (root_n / "交付文件"):
            raise SystemExit(f"Refusing unexpected pack target: {out_n}")
    OUT.mkdir(parents=True, exist_ok=True)
    # Ensure empty disease/drug dirs exist even if a source is missing
    for sub in ("数据/疾病", "数据/药物", "数据/药物/单药"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    # Dropped figures (user cancelled): remove stale Track B copies
    for rel in (
        "图片/网络图/核心靶点子网络图.svg",
        "图片/网络图/核心靶点子网络图.png",
    ):
        stale = OUT / rel
        if stale.exists():
            stale.unlink()
            print("DROP", rel)
    for stem, rel in FIG_MAP.items():
        copy_fig(stem, rel)
    for src, rel in DATA_MAP:
        copy_data(src, rel)
    pack_per_herb()
    # Sync KEGG official maps cache → delivery (if download already ran)
    kegg_cache = FIG / "KEGG官方通路图"
    kegg_out = OUT / "图片" / "KEGG官方通路图"
    if kegg_cache.exists():
        kegg_out.mkdir(parents=True, exist_ok=True)
        for f in kegg_cache.iterdir():
            if f.is_file():
                shutil.copy2(f, kegg_out / f.name)
                print("KEGG", f.name, "->", (kegg_out / f.name).relative_to(OUT).as_posix())
    report_dir = OUT / "报告"
    report_dir.mkdir(parents=True, exist_ok=True)
    readme = OUT / "README_轨B说明.txt"
    readme.write_text(
        "轨 B 客户归档（由 11_pack_delivery_archive.py 从轨 A / 数据文件 复制）。\n"
        "目录：图片/（含 KEGG官方通路图）、数据/、报告/、图注与解读说明.html。\n"
        "发给别人：请打包整个交付文件文件夹，打开根目录 图注与解读说明.html（相对路径含图）。\n"
        "规范状态：FROZEN（2026-07-26）。禁止把本目录当作桌面写出路径。\n",
        encoding="utf-8",
    )
    print("DONE", OUT)


if __name__ == "__main__":
    main()
