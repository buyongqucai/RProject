# -*- coding: utf-8 -*-
"""清风课题双报告（严格遵守 ProjectDualReport §2.1）：

- 同步 交付文件/图片/**/*.png → 本目录 图片文件/
- 论文式：全量嵌图 + 逐图结果分析
- 方法论：全量嵌图 + 逐图「怎么读」分析
- 生成后校验：嵌图数==交付PNG数、坏链=0、报告内无重复
"""
from __future__ import annotations

import html
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DELIVERY = ROOT / "交付文件"
SRC_FIG = DELIVERY / "图片"
LOCAL_FIG = HERE / "图片文件"
STATS = json.loads((DELIVERY / "报告" / "_stats.json").read_text(encoding="utf-8"))
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")

CLAIM = (
    "本报告为<strong>网络药理学计算预测</strong>（in silico），"
    "不是临床试验或诊疗建议；不得表述为「治疗 IPF」或「机制已证实」。"
)

n_dis = STATS["n_disease_union"]
n_drug = STATS["n_drug_targets"]
n_ov = STATS["n_overlap"]
pct = STATS["overlap_pct_of_drug"]
gc40 = STATS["disease_by_db_downstream"]["GeneCards"]
gc_full = STATS["genecards_full"]
top_kegg = {k["id"]: k for k in STATS.get("top_kegg", [])}


def esc(s) -> str:
    return html.escape(str(s))


def sync_figures() -> list[Path]:
    if LOCAL_FIG.exists():
        shutil.rmtree(LOCAL_FIG)
    LOCAL_FIG.mkdir(parents=True)
    outs = []
    for src in sorted(SRC_FIG.rglob("*.png")):
        rel = src.relative_to(SRC_FIG)
        dst = LOCAL_FIG / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        outs.append(rel)
    return outs


# ---- Figure registry: order = scientific narrative; every delivery PNG once ----

def build_registry() -> list[dict]:
    """Return ordered figure dicts covering ALL delivery PNGs."""
    items: list[dict] = []

    def add(rel: str, sec: str, title: str, c_p: str, a_p: str, c_m: str, a_m: str):
        items.append(
            {
                "rel": rel.replace("\\", "/"),
                "sec": sec,
                "title": title,
                "cap_p": c_p,
                "ana_p": a_p,
                "cap_m": c_m,
                "ana_m": a_m,
            }
        )

    # R1 disease
    add(
        "韦恩图/疾病数据库可视化韦恩图.png",
        "r1",
        "疾病多库韦恩",
        f"图·疾病多库韦恩（微生信五库：GeneCards全量 {gc_full} / CTD_curated / OMIM / TTD / DrugBank；与药病韦恩同出图链）。",
        f"CTD 在韦恩与下游均用 curated（不用 any）。下游并集 GeneCards≥40（{gc40}）∪ CTD_curated ∪ OMIM ∪ TTD ∪ DrugBank = {n_dis}。"
        f"COPD / CCL12 已剔除。",
        "读图·疾病韦恩：五库含 CTD_curated；微生信双底栏。",
        "椭圆=GeneCards/CTD/OMIM/TTD/DrugBank；GeneCards 韦恩仍为全量，下游用 ≥40。",
    )

    # R2 drug / herb bars
    add(
        "补充_技能扩展/单药疾病交集柱状图.png",
        "r2",
        "单药×疾病交集",
        "图·各药味与疾病下游并集的交集基因数。Per-herb disease-overlap counts.",
        "柱高反映各味药靶点与 IPF 下游集的重叠规模。甘草、蜜麻黄、黄芪、旋覆花贡献大；水蛭仅 known 口径下重叠为 6。"
        "柱高≠药效或重要性排序，只描述计算覆盖。",
        "读图·单药柱状：纵轴是交集基因数。",
        "核对每柱是否与 per_herb 表一致。水蛭偏低来自 BATMAN known 停层，不是「无效」。",
    )
    add(
        "补充_技能扩展/成分疾病交集柱状图.png",
        "r2",
        "成分×疾病交集",
        "图·成分与疾病重叠靶点数分布。Compound–disease overlap target counts.",
        "展示哪些化学成分在疾病重叠靶点上连接更多基因。高连接成分多为黄酮类等跨药共享实体，后续 HCTP 中常以 same* 出现。",
        "读图·成分柱状：注意多药共享成分会抬高计数。",
        "若一名成分对应多味药，解读时回到 HerbCompound 边表，避免把共享成分算成单药专属发现。",
    )
    add(
        "补充_技能扩展/成分疾病交集按药柱状图.png",
        "r2",
        "成分×疾病（按药分面）",
        "图·按药分面的成分–疾病重叠。Compound–disease overlap faceted by herb.",
        "分面显示每味药内部哪些成分驱动与疾病基因的连接。便于区分「该药特异成分」与「跨药重复化学实体」。",
        "读图·按药分面：先找本药独有高峰，再标同名成分。",
        "同名英文成分跨面重复出现时，与 UpSet / same* 命名对照。",
    )
    add(
        "补充_技能扩展/药味成分交集UpSet图.png",
        "r2",
        "药味成分 UpSet",
        "图·多药共享成分 UpSet。Herb–compound intersection UpSet.",
        "UpSet 量化跨药共享成分集合。共享成分会抬高网络中成分节点 Degree（如槲皮素 same15），讨论枢纽时必须声明「多药共有化学实体」。",
        "读图·UpSet：横柱=集合大小，竖点=交集组合。",
        "用于解释 same* 重命名是否合理；不用于疗效比较。",
    )

    # R3 overlap + network
    add(
        "韦恩图/疾病药物交集韦恩图.png",
        "r3",
        "药病交集韦恩",
        f"图·药物靶点（{n_drug}）∩ 疾病下游并集（{n_dis}）= {n_ov}（占药靶 {pct}%）。Drug–disease Venn.",
        f"核心定量结果：{n_ov} 个基因同时出现在方剂靶点空间与 IPF 下游疾病集。"
        f"高重叠支持提出机制假说，不支持临床有效外推。",
        "读图·药病韦恩：两圆标签必须对应下游口径。",
        f"若看见与 {n_ov} 不符的数字，先查是否误用了 GeneCards 全量。",
    )
    add(
        "网络图/药物有效成分疾病靶点通路网络图.png",
        "r3",
        "HCTP 列状网络",
        "图·药–成分–靶–通路（HCTP）列状布局（385 节点 / 2,571 边）。HCTP column layout.",
        "列状布局便于沿 A→B→C→D 阅读。Degree 枢纽含 PTGS2、多药共享槲皮素（same15）、HSP90AA1、ESR1 等。"
        "Degree 高只说明拓扑中心性，不是湿实验验证。",
        "读图·HCTP 列状：从左到右跟边。",
        "成分节点若为 same*，回查重命名表；通路层为 Top 富集代表，不是全部 193 条 KEGG。",
    )
    add(
        "网络图/药物有效成分疾病靶点通路网络图_椭圆布局.png",
        "r3",
        "HCTP 椭圆布局",
        "图·同一 HCTP 网络的椭圆布局投影。HCTP ellipse layout.",
        "与列状图为同一边集的不同投影，用于检查布局依赖的视觉聚集是否稳定。结论仍以表格 Degree / 边表为准。",
        "读图·椭圆布局：勿因视觉簇发明新通路。",
        "两布局冲突时以 network.csv 边表仲裁。",
    )
    add(
        "网络图/药成分靶点通路桑基图.png",
        "r3",
        "药–成分–靶–通路桑基",
        "图·筛选总览桑基（药→成分→靶→通路流量）。Herb–compound–target–pathway Sankey overview.",
        "桑基宽度近似流量，突出哪条药–成分路径汇入主要通路模块。适合总览，不适合读取精确基因名单（名单见结果表）。",
        "读图·桑基：看主流量，不读像素级计数。",
        "过细分支以长表为准；本图为筛选后总览。",
    )
    add(
        "网络图/筛选成分桑基图.png",
        "r3",
        "筛选成分桑基分面",
        "图·前序成分桑基分面。Faceted compound Sankey panels.",
        "分面把高流量成分拆开，便于检查单个成分进入哪些靶/通路。与成分柱状图、UpSet 互相印证。",
        "读图·分面桑基：一次只跟一个面板。",
        "面板标题为成分名/代号；same* 需映射英文名。",
    )
    add(
        "补充_技能扩展/药味通路覆盖热图.png",
        "r3",
        "药味×通路覆盖热图",
        "图·药味对 Top 通路基因的覆盖热图。Herb × pathway coverage heatmap.",
        "颜色深浅表示该药味靶点命中某通路基因的覆盖强度。可用于提出「多药协同作用于同一模块」的假说，不可排序药效。",
        "读图·热图：行=药，列=通路。",
        "注意行和已按 known/TCMSP 口径；水蛭行稀疏符合 known-only。",
    )

    # R4 enrichment
    add(
        "富集分析/BPCCMF气泡图.png",
        "r4",
        "GO 气泡图",
        "图·GO BP/CC/MF 气泡图（横轴 Enrichment，点大小/颜色映射基因数与显著性）。GO BP/CC/MF bubble.",
        "气泡图给出交集基因的功能主题轮廓。优先阅读与炎症、凋亡、细胞外基质/成纤维相关的 BP；"
        "具体条目以富集表 padj 与 geneID 为准。",
        "读图·GO 气泡：X=Enrichment，分面=BP/CC/MF。",
        "技能规定 Y 序按 Enrichment；若观感与表不符，以 CSV 排序复核。",
    )
    add(
        "补充_技能扩展/GO_BPCCMF柱状图.png",
        "r4",
        "GO 柱状图",
        "图·GO BP/CC/MF 柱状互补视图。GO bar chart companion.",
        "柱状图强调 −log10(padj) 或计数对比，便于挑 Top 条目写讨论。与气泡图信息互补，不重复计数。",
        "读图·GO 柱：看显著性排序是否与气泡一致。",
        "只取 padj 过线条目进入主文表述。",
    )
    add(
        "富集分析/KEGG棒棒糖图.png",
        "r4",
        "KEGG 棒棒糖",
        "图·KEGG 通路棒棒糖（显著性排序）。KEGG lollipop.",
        "Top 通路名称含脂质/剪切应力–动脉粥样硬化、AGE-RAGE、肿瘤与感染类。"
        "在 IPF 语境下，这些名称多数应解释为共享炎症–增殖–凋亡模块富集，而不是方剂「抗动脉粥样硬化/抗肿瘤」结论。",
        "读图·KEGG 棒棒糖：先读 padj，再读通路名。",
        "通路名≠疾病诊断；写讨论时改用模块语言（炎症、EMT、血管重塑等）。",
    )
    add(
        "富集分析/KEGG柱状图.png",
        "r4",
        "KEGG 柱状图",
        "图·KEGG 柱状图。KEGG bar chart.",
        "与棒棒糖同一富集表的柱形展示，便于比较 Count。193 条通路项记录在结果表；正文只展开与 IPF 假说相关的轴（如 IL-17、TNF、PI3K-Akt、Apoptosis）。",
        "读图·KEGG 柱：Count 与显著性可能不完全同序。",
        "以 padj 主排序，Count 作支持。",
    )
    add(
        "富集分析/KEGG圈图.png",
        "r4",
        "KEGG 圈图",
        "图·KEGG circlize 圈图（基因–通路连接）。KEGG circos.",
        "圈图展示基因在多通路间的共享。若多条「疾病命名」通路共享同一批核心基因，更支持模块解释而非多种独立疾病指向。",
        "读图·圈图：看丝带是否汇聚到同一基因簇。",
        "汇聚=共享模块信号；不要数丝带当通路数。",
    )

    # KEGG official top20 — paper analysis brief per map
    kegg_notes = {
        "hsa05417": ("脂质与动脉粥样硬化相关通路居 Top，多由炎症/脂质代谢基因驱动；对照 IPF 文献作交叉提示，不作动脉粥样硬化诊断。", "共享炎症模块；慎用病名。"),
        "hsa05418": ("剪切应力/血管相关通路富集，可与肺血管重塑假说对照，仍属计算提示。", "内皮/炎症基因共享常见。"),
        "hsa04933": ("AGE-RAGE 常与炎症交叉出现，作交叉通路提示。", "交叉通路，非糖尿病结论。"),
        "hsa05215": ("前列腺癌等肿瘤通路名：增殖/凋亡基因共享，不作抗肿瘤声称。", "肿瘤病名→共享增殖模块。"),
        "hsa05160": ("肝炎病毒通路名同理，解释为免疫–炎症共享基因。", "感染病名慎读。"),
        "hsa05207": ("化学致癌–受体激活：受体/转录相关基因富集的计算读出。", "勿引申为致癌/抗癌。"),
        "hsa05161": ("乙肝通路名：免疫基因共享。", "感染病名慎读。"),
        "hsa04657": ("IL-17 信号与黏膜/中性粒炎症相关，IPF 模型文献中有成纤维活化讨论点，可作优先假说轴之一。", "优先假说轴：炎症。"),
        "hsa05167": ("疱疹病毒感染通路名：免疫共享。", "感染病名慎读。"),
        "hsa05163": ("巨细胞病毒通路名：免疫共享。", "感染病名慎读。"),
        "hsa04668": ("TNF 信号是炎症–纤维化讨论中的常见轴，可与 IPF 文献对照。", "优先假说轴：TNF。"),
        "hsa05212": ("胰腺癌通路名：增殖/凋亡共享。", "肿瘤病名慎读。"),
        "hsa05205": ("肿瘤蛋白多糖通路：基质/信号共享。", "基质相关可对照纤维化，仍非结论。"),
        "hsa05219": ("膀胱癌通路名：共享模块。", "肿瘤病名慎读。"),
        "hsa05145": ("弓形虫通路名：免疫共享。", "感染病名慎读。"),
        "hsa05208": ("ROS 化学致癌通路：氧化应激基因可对照肺损伤语境，不作致癌结论。", "氧化应激提示。"),
        "hsa01522": ("内分泌抵抗：受体信号共享。", "勿引申内分泌治疗。"),
        "hsa04151": ("PI3K-Akt 为生长/存活常用轴，可与成纤维活化文献对照。", "优先假说轴：PI3K-Akt。"),
        "hsa05223": ("非小细胞肺癌通路名：与肺脏同器官但不等于 IPF 机制证实。", "器官重合≠病种等同。"),
        "hsa04210": ("凋亡通路与细胞命运相关，可纳入炎症–重塑假说网络。", "优先假说轴：Apoptosis。"),
    }

    kegg_files = sorted((SRC_FIG / "KEGG官方通路图").glob("*.png"))
    for i, fp in enumerate(kegg_files, 1):
        name = fp.name  # 01_hsa05417_...
        m = re.match(r"\d+_(hsa\d+)_(.+)\.png$", name)
        kid = m.group(1) if m else name
        desc = m.group(2).replace("_", " ") if m else name
        note_p, note_m = kegg_notes.get(kid, ("官方通路图展示交集基因落位；学术用途。", "看落位；病名慎读。"))
        info = top_kegg.get(kid)
        extra = ""
        if info:
            extra = f" 本课题统计：Count={info['count']}，padj={info['padj']:.2e}。"
        add(
            f"KEGG官方通路图/{name}",
            "r4",
            f"KEGG官方 {kid}",
            f"图·KEGG 官方通路图 {kid}（{desc}）。Official KEGG map.{extra}",
            note_p + extra + " 图像仅学术用途（KEGG 条款）。",
            f"读图·官方图 {kid}：着色基因为本交集命中。",
            note_m + " 勿截图商用；细节基因以 geneID 长表为准。",
        )

    # R5 PPI
    add(
        "PPI/string_vector_graphic.png",
        "r5",
        "STRING 官方图",
        "图·STRING 官方网络矢量图（输入 197 交集基因）。STRING official network image.",
        "官方图给出互作概览。主阈值 score≥900 时节点 173、边 687；25 个基因在该阈值无边（见 PPIQC）。",
        "读图·STRING 官方图：线粗/颜色按官网默认。",
        "与代码布局对照时，以 score900 tsv 边表为准。",
    )
    add(
        "PPI/PPI渐变图.png",
        "r5",
        "PPI 代码布局",
        "图·PPI 代码布局（score≥900）。Coded PPI layout.",
        "代码布局强调核心互作团。可与 Degree 图一起挑选候选枢纽蛋白，供后续对接/实验设计，但本身不是验证。",
        "读图·代码 PPI：关注大度节点与连通片。",
        "无边基因名单必须在局限中交代，避免假装全覆盖。",
    )
    add(
        "PPI/PPI渐变图_Degree.png",
        "r5",
        "PPI Degree 视图",
        "图·PPI Degree 视图。PPI degree view.",
        "Degree 视图突出互作度数分布，便于与 HCTP 枢纽交叉点名（如炎症相关酶/受体）。交叉点名仍属假说生成。",
        "读图·Degree：点数高≠生物学最重要。",
        "结合 Betweenness 等表字段再写候选列表。",
    )

    return items


CSS = """
html{font-size:100%}
body{margin:0;font-family:"Segoe UI","Microsoft YaHei","Noto Sans SC",sans-serif;
font-size:1.05rem;line-height:1.8;color:#1c241f;background:#f3efe6}
.layout{display:grid;grid-template-columns:clamp(13rem,21vw,18rem) minmax(0,1fr);min-height:100vh}
.sidebar{position:sticky;top:0;align-self:start;height:100vh;overflow:auto;background:#24362f;color:#f4efe6;padding:1rem .75rem 2rem}
.sidebar h1{font-size:1.02rem;margin:0 0 .25rem;line-height:1.35}
.sidebar .sub{font-size:.76rem;color:#c5d2cb;margin-bottom:.75rem}
.sidebar a{display:block;color:#e7eee9;text-decoration:none;font-size:.84rem;padding:.36rem .45rem;border-radius:.4rem;border-left:.18rem solid transparent}
.sidebar a:hover{background:rgba(255,255,255,.06)}
.sidebar a.active{background:rgba(216,240,228,.22);border-left-color:#b7e3cc;color:#fff}
.main{min-width:0;max-width:52rem;padding:clamp(1rem,2vw,2rem) clamp(1rem,3vw,2.2rem) 3rem}
.hero{background:#fffdf8;border:1px solid #ddd4c4;border-radius:1rem;padding:1.1rem 1.25rem}
.hero h1{font-size:clamp(1.3rem,2.2vw,1.75rem);line-height:1.3;margin:0 0 .45rem}
.pills{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:.7rem}
.pill{font-size:.75rem;padding:.12rem .55rem;border-radius:999px;border:1px solid #c5d4c8;background:#f3f7f3;color:#3d5c42}
.pill.warn{border-color:#ead3d3;background:#fbf6f6;color:#7a4545}
.note{background:#fff8ea;border-left:.35rem solid #8a6a3a;padding:.8rem 1rem;border-radius:.5rem;margin:1rem 0}
.take{background:#eef6f1;border-left:.35rem solid #2f5d4c;padding:.8rem 1rem;border-radius:.5rem;margin:1rem 0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:.55rem;margin:1rem 0}
.kpi{background:#fff;border:1px solid #ddd4c4;border-top:3px solid #5B8FA8;border-radius:.5rem;padding:.55rem .7rem}
.kpi b{display:block;font-size:1.05rem;font-variant-numeric:tabular-nums}
.kpi span{font-size:.72rem;color:#5c635c}
h2{font-size:clamp(1.12rem,1.6vw,1.35rem);margin:2rem 0 .55rem;border-bottom:2px solid #d5e0d7;padding-bottom:.2rem}
h3{font-size:1.02rem;margin:1.35rem 0 .35rem;color:#24362f}
figure{margin:0.85rem 0 0.35rem;background:#fffdf8;border:1px solid #ddd4c4;border-radius:.8rem;padding:.7rem}
figure img{width:100%;max-width:100%;height:auto;display:block;background:#fff}
figcaption{margin-top:.5rem;background:#f6f3ec;border-left:.25rem solid #2f5d4c;padding:.55rem .7rem;border-radius:.4rem;font-size:.93rem}
.ana{margin:0 0 1.25rem;padding:.75rem .9rem;background:#fff;border:1px solid #e6dfd2;border-radius:.55rem}
.ana strong{color:#2f5d4c}
table{border-collapse:collapse;width:100%;font-size:.9rem;background:#fff;margin:.5rem 0}
th,td{border:1px solid #ddd4c4;padding:.4rem .5rem;vertical-align:top}
th{background:#eef3ef;text-align:left}
.footer{color:#5c635c;font-size:.84rem;margin-top:2.2rem;padding-top:1rem;border-top:1px solid #ddd4c4}
ul.tight li{margin:.2rem 0}
@media (max-width:52rem){.layout{grid-template-columns:1fr}.sidebar{position:relative;height:auto;max-height:40vh}}
"""

JS = """
(function(){const links=[...document.querySelectorAll('.sidebar a[href^="#"]')];
const secs=links.map(a=>document.getElementById(a.getAttribute('href').slice(1))).filter(Boolean);
function on(id){links.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+id));}
const io=new IntersectionObserver(es=>{const v=es.filter(e=>e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio);if(v[0])on(v[0].target.id);},{rootMargin:'-12% 0px -55% 0px',threshold:[0.12,0.35]});
secs.forEach(s=>io.observe(s));if(secs[0])on(secs[0].id);})();
"""


def page(title: str, side: str, sub: str, nav: list[tuple[str, str]], body: str) -> str:
    nav_html = "".join(f"<a href='#{hid}'>{esc(txt)}</a>" for hid, txt in nav)
    return (
        f"<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'/>"
        f"<meta name='viewport' content='width=device-width, initial-scale=1'/>"
        f"<title>{esc(title)}</title><style>{CSS}</style></head><body>"
        f"<div class='layout'><aside class='sidebar'><h1>{esc(side)}</h1>"
        f"<div class='sub'>{esc(sub)}</div>{nav_html}"
        f"<div class='sub' style='margin-top:1rem'>姊妹页</div>"
        f"<a href='00_报告入口_index.html'>报告入口</a>"
        f"<a href='01_论文式报告_PaperStyle.html'>论文式报告</a>"
        f"<a href='02_方法论报告_Methodology.html'>方法论报告</a>"
        f"</aside><main class='main'>{body}</main></div>"
        f"<script>{JS}</script></body></html>"
    )


def fig_block(rel: str, title: str, caption: str, analysis: str, fig_id: str) -> str:
    src = f"图片文件/{rel}"
    return (
        f"<h3 id='{fig_id}'>{esc(title)}</h3>"
        f"<figure><img src='{esc(src)}' alt='{esc(title)}'/>"
        f"<figcaption>{caption}</figcaption></figure>"
        f"<div class='ana'><strong>分析：</strong>{analysis}</div>"
    )


def main() -> None:
    synced = sync_figures()
    synced_set = {p.as_posix() for p in synced}
    reg = build_registry()
    reg_rels = [x["rel"] for x in reg]

    missing = [r for r in reg_rels if r not in synced_set]
    extra = sorted(synced_set - set(reg_rels))
    if missing:
        raise SystemExit(f"registry missing files: {missing}")
    if extra:
        raise SystemExit(f"delivery PNGs not in registry: {extra}")
    if len(reg_rels) != len(set(reg_rels)):
        raise SystemExit("duplicate in registry")

    # group by section for paper
    sec_order = [
        ("r1", "结果一 · 疾病靶点"),
        ("r2", "结果二 · 药物成分与单药覆盖"),
        ("r3", "结果三 · 药病交集与 HCTP 网络"),
        ("r4", "结果四 · GO/KEGG 富集与官方通路图"),
        ("r5", "结果五 · STRING PPI"),
    ]

    paper_nav = [
        ("abs", "摘要（结论先行）"),
        ("q", "研究问题"),
        ("design", "数据与设计"),
        *[(sid, title) for sid, title in sec_order],
        ("disc", "讨论"),
        ("lim", "局限"),
        ("meth", "方法摘要"),
    ]

    per = STATS.get("per_herb", [])
    per_rows = "".join(
        f"<tr><td>{esc(r['herb_zh'])}</td><td>{r['n_targets']}</td><td>{r['n_overlap']}</td></tr>"
        for r in per
    )

    paper_parts = [
        f"""
<div class='hero'>
  <h1>论文式报告 · 水蛭宣痹化纤汤干预 IPF 的潜在机制</h1>
  <p>网络药理学计算预测 · 交付图册全量嵌图并逐图分析（课题双报告范式 §2.1）</p>
  <div class='pills'>
    <span class='pill'>STATUS: COMPLETE</span>
    <span class='pill'>data_provenance: REAL</span>
    <span class='pill'>嵌图 {len(reg)} 张</span>
    <span class='pill warn'>对接未启动</span>
  </div>
  <div class='kpis'>
    <div class='kpi'><b>{n_dis}</b><span>疾病下游并集</span></div>
    <div class='kpi'><b>{n_drug}</b><span>药物靶点并集</span></div>
    <div class='kpi'><b>{n_ov}</b><span>药病交集</span></div>
    <div class='kpi'><b>385 / 2571</b><span>HCTP 节点/边</span></div>
    <div class='kpi'><b>173 / 687</b><span>PPI≥900</span></div>
    <div class='kpi'><b>{len(reg)}</b><span>正文嵌图数</span></div>
  </div>
</div>
<div class='note'>{CLAIM}</div>
<h2 id='abs'>摘要（结论先行）</h2>
<div class='take'>
<p>九味<strong>水蛭宣痹化纤汤</strong>与<strong>IPF</strong>的网络药理学计算显示：疾病下游并集 <strong>{n_dis}</strong>、药物靶点 <strong>{n_drug}</strong>、药病交集 <strong>{n_ov}</strong>（占药靶 {pct}%）。
HCTP 385 节点 / 2,571 边；STRING≥900 为 173 / 687；富集提示炎症–应激–凋亡等共享模块。
水蛭仅 BATMAN known 入主网。<strong>未证明疗效或因果靶点</strong>。下文按流程嵌入全部 {len(reg)} 张交付图并逐图分析。</p>
</div>
<h2 id='q'>研究问题</h2>
<p>预测方剂干预 IPF 的潜在靶点与通路机制，形成可核对假说。可写「潜在机制（计算预测）」；不可写「治疗 IPF」。</p>
<h2 id='design'>数据与设计</h2>
<p>疾病五库双口径；8 味 TCMSP（OB≥30%、DL≥0.18）；水蛭 BATMAN known（按药 API）。
交集→HCTP→GO/KEGG→STRING。单药覆盖表：</p>
<table><tr><th>药味</th><th>靶点</th><th>∩疾病</th></tr>{per_rows}</table>
"""
    ]

    for sid, title in sec_order:
        paper_parts.append(f"<h2 id='{sid}'>{esc(title)}</h2>")
        for i, it in enumerate([x for x in reg if x["sec"] == sid], 1):
            paper_parts.append(
                fig_block(it["rel"], f"{title.split('·')[-1].strip()} · {it['title']}", it["cap_p"], it["ana_p"], f"{sid}-f{i}")
            )

    paper_parts.append(
        f"""
<h2 id='disc'>讨论</h2>
<ul class='tight'>
<li>高重叠率支持机制假说生成，不支持疗效外推。</li>
<li>HCTP/PPI 枢纽与富集模块指向炎症–应激–凋亡轴；肿瘤/感染通路名按共享模块解读。</li>
<li>共享成分（UpSet / same*）会抬高成分 Degree，须与药味特异靶点区分。</li>
<li>水蛭 known 规模小，凝血相关基因为交叉假说线索。</li>
</ul>
<h2 id='lim'>局限</h2>
<ul class='tight'>
<li>无湿实验、无对接/MD；DisGeNET 未纳入。</li>
<li>BATMAN 全库 browse 路径待验证；本课题仅按药 API + known。</li>
<li>KEGG 官方图仅学术用途。</li>
</ul>
<h2 id='meth'>方法摘要</h2>
<p>细节见 <a href='02_方法论报告_Methodology.html'>方法论报告</a>（同图册的读图向分析）。数字以 <code>交付文件/报告/_stats.json</code> 为准。</p>
<p class='footer'>生成 {NOW} · ProjectDualReport §2.1 · 嵌图 {len(reg)}/{len(synced)} · 坏链校验见生成日志</p>
"""
    )

    # methodology
    meth_nav = [
        ("m0", "声明"),
        ("m1", "分析路线与阈值"),
        ("m2", "软件脚本"),
        ("m3", "质控"),
        ("m4", "图册阅读（全量嵌图）"),
        ("m5", "分工"),
    ]
    meth_parts = [
        f"""
<div class='hero'>
  <h1>方法论报告 · 清风网药</h1>
  <p>路线 / 阈值 / QC + 交付图册全量「怎么读」分析（与论文式同图源、不同叙述）</p>
  <div class='pills'>
    <span class='pill'>嵌图 {len(reg)} 张</span>
    <span class='pill warn'>计算预测</span>
  </div>
</div>
<div class='note' id='m0'>{CLAIM}</div>
<h2 id='m1'>分析路线与阈值</h2>
<ol>
<li>疾病：五库；韦恩=GeneCards全量；下游=≥40∪CTD curated∪OMIM∪TTD∪DrugBank → {n_dis}</li>
<li>药物：TCMSP OB≥30% DL≥0.18（8 味）；水蛭 BATMAN known only</li>
<li>交集 {n_ov} → HCTP → ORA → STRING score≥900（173/687）</li>
</ol>
<h2 id='m2'>软件与脚本</h2>
<p><code>04_富集与PPI_EnrichPPI/02_代码文件_Code/01–09</code>；本脚本 <code>03_生成课题双报告_buildDualReports.py</code>。
图文件已同步至报告目录 <code>图片文件/</code>。</p>
<h2 id='m3'>质控</h2>
<ul class='tight'>
<li>剔 COPD 非基因；剔 CCL12 小鼠基因</li>
<li>BATMAN 混条审计；Hirudin→F2 预测边旁路</li>
<li>STRING≥900 无边基因 25 个见 PPIQC</li>
</ul>
<h2 id='m4'>图册阅读指南（全量嵌图）</h2>
<p>以下与论文式使用<strong>同一批 PNG</strong>，每图说明「看什么 / 不看什么」。报告内不重复同一路径。</p>
"""
    ]
    for i, it in enumerate(reg, 1):
        meth_parts.append(fig_block(it["rel"], f"读图 {i:02d} · {it['title']}", it["cap_m"], it["ana_m"], f"m4-f{i}"))

    meth_parts.append(
        f"""
<h2 id='m5'>与论文式分工</h2>
<p><a href='01_论文式报告_PaperStyle.html'>论文式</a>=结果叙事；本页=方法与读图；轨 B 图注页=仪表盘补强。权威数字=_stats.json。</p>
<p class='footer'>生成 {NOW} · ProjectDualReport §2.1 · 嵌图 {len(reg)}</p>
"""
    )

    (HERE / "01_论文式报告_PaperStyle.html").write_text(
        page("论文式报告 · 清风", "论文式报告", f"全量嵌图 {len(reg)}", paper_nav, "".join(paper_parts)),
        encoding="utf-8",
    )
    (HERE / "02_方法论报告_Methodology.html").write_text(
        page("方法论报告 · 清风", "方法论报告", f"读图 {len(reg)}", meth_nav, "".join(meth_parts)),
        encoding="utf-8",
    )

    index = f"""<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'/>
<meta name='viewport' content='width=device-width, initial-scale=1'/>
<title>清风 · 报告入口</title>
<style>
body{{margin:0;font-family:"Segoe UI","Microsoft YaHei",sans-serif;background:#f3efe6;color:#1c241f;line-height:1.7}}
.wrap{{max-width:820px;margin:0 auto;padding:2rem 1.2rem}}
.card{{background:#fffdf8;border:1px solid #ddd4c4;border-radius:1rem;padding:1.2rem;margin:1rem 0}}
a.btn{{display:inline-block;margin:.35rem .45rem 0 0;padding:.55rem 1rem;background:#2f5d4c;color:#fff;text-decoration:none;border-radius:.5rem}}
.note{{background:#fff8ea;border-left:.35rem solid #8a6a3a;padding:.8rem 1rem;border-radius:.5rem}}
</style></head><body><div class='wrap'>
<h1>清风项目 · 课题报告入口</h1>
<div class='note'>{CLAIM}</div>
<div class='card'>
<p>规范：课题双报告范式 §2.1（交付图册全量嵌图 + 逐图分析）。本包嵌图 <strong>{len(reg)}</strong> 张。</p>
<a class='btn' href='01_论文式报告_PaperStyle.html'>01 论文式报告</a>
<a class='btn' href='02_方法论报告_Methodology.html'>02 方法论报告</a>
</div>
<p style='color:#5c635c;font-size:.9rem'>{NOW} · REAL · COMPLETE</p>
</div></body></html>"""
    (HERE / "00_报告入口_index.html").write_text(index, encoding="utf-8")

    # validate links
    for name in ["01_论文式报告_PaperStyle.html", "02_方法论报告_Methodology.html"]:
        text = (HERE / name).read_text(encoding="utf-8")
        srcs = re.findall(r"src=['\"]([^'\"]+)['\"]", text)
        assert len(srcs) == len(reg), (name, len(srcs), len(reg))
        assert len(srcs) == len(set(srcs)), f"dup in {name}"
        bad = [s for s in srcs if not (HERE / s).exists()]
        if bad:
            raise SystemExit(f"bad links in {name}: {bad[:5]}")

    (HERE / "清风项目分析报告.md").write_text(
        f"# 课题双报告（§2.1 全量嵌图）\n\n"
        f"- 入口：`00_报告入口_index.html`\n"
        f"- 论文式 / 方法论：各嵌图 **{len(reg)}** 张并逐图分析\n"
        f"- 图目录：`图片文件/`（自交付文件同步）\n",
        encoding="utf-8",
    )
    (HERE / "STATUS.md").write_text(
        f"# STATUS\n\n- 2026-10-16：双报告按 ProjectDualReport §2.1 重生成；嵌图 {len(reg)}/{len(synced)}；坏链 0。\n",
        encoding="utf-8",
    )
    print("OK figs", len(reg), "synced", len(synced))


if __name__ == "__main__":
    main()
