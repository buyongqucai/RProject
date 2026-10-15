# -*- coding: utf-8 -*-
"""Build offline HTML report at 交付文件/图注与解读说明.html.

All asset links are relative to 交付文件/ (e.g. 图片/..., 数据/..., 报告/...),
so zipping the whole 交付文件 folder and opening the HTML elsewhere still shows images.
"""
from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学")
OUT = ROOT / "交付文件"
REPORT_DIR = OUT / "报告"
HTML_PATH = OUT / "图注与解读说明.html"  # delivery root — share this folder
HTML_STUB = REPORT_DIR / "图注与解读说明.html"
STATS_JSON = REPORT_DIR / "_stats.json"
STATS_PY = ROOT / "代码文件" / "28_collect_report_stats.py"
KEGG_META = OUT / "图片" / "KEGG官方通路图" / "00_Top20通路图清单.csv"


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def asset(rel: str) -> str:
    """Relative URL from 交付文件/ root (forward slashes)."""
    return esc(str(rel).replace("\\", "/").lstrip("/"))


def fmt_p(p: float | None) -> str:
    if p is None:
        return "—"
    if p < 1e-4:
        return f"{p:.2e}"
    return f"{p:.4g}"


def load_stats() -> dict:
    subprocess.run([sys.executable, str(STATS_PY)], check=False, capture_output=True)
    if STATS_JSON.exists():
        return json.loads(STATS_JSON.read_text(encoding="utf-8"))
    return {}


def fig_card(
    title: str,
    meaning: str,
    howto: str,
    rel_png: str,
    rel_svg: str | None = None,
    note: str | None = None,
    bio: str | None = None,
    stats_line: str | None = None,
) -> str:
    png = OUT / rel_png
    exists = png.exists()
    img = (
        f'<a class="thumb" href="{asset(rel_png)}" target="_blank" rel="noopener">'
        f'<img src="{asset(rel_png)}" alt="{esc(title)}" loading="lazy" /></a>'
        if exists
        else '<div class="missing">图片缺失</div>'
    )
    links = []
    if exists:
        links.append(f'<a href="{asset(rel_png)}" target="_blank">PNG</a>')
    if rel_svg and (OUT / rel_svg).exists():
        links.append(f'<a href="{asset(rel_svg)}" target="_blank">SVG</a>')
    link_html = " · ".join(links) if links else ""
    note_html = f'<p class="note">{esc(note)}</p>' if note else ""
    bio_html = f'<p><span class="tag bio">生物学意义</span>{esc(bio)}</p>' if bio else ""
    stats_html = f'<p class="statline">{stats_line}</p>' if stats_line else ""
    return f"""
<article class="card">
  <div class="card-media">{img}</div>
  <div class="card-body">
    <h3>{esc(title)}</h3>
    {stats_html}
    <p><span class="tag">含义</span>{esc(meaning)}</p>
    <p><span class="tag how">怎么看</span>{esc(howto)}</p>
    {bio_html}
    {note_html}
    <p class="links">{link_html}</p>
  </div>
</article>
"""


def kegg_gallery() -> str:
    if not KEGG_META.exists():
        return "<p class='note'>缺少 00_Top20通路图清单.csv</p>"
    df = pd.read_csv(KEGG_META, encoding="utf-8-sig")
    cards = []
    for _, r in df.iterrows():
        fname = str(r.get("file", ""))
        pid = str(r.get("pathway_id", ""))
        desc = str(r.get("description", ""))
        rank = r.get("rank", "")
        rel = f"图片/KEGG官方通路图/{fname}"
        if not (OUT / rel).exists():
            continue
        cards.append(
            f"""
<div class="kegg-card">
  <a href="{asset(rel)}" target="_blank" rel="noopener">
    <img src="{asset(rel)}" alt="{esc(pid)}" loading="lazy" />
  </a>
  <div class="kegg-meta">
    <strong>#{esc(rank)} {esc(pid)}</strong>
    <span>{esc(desc)}</span>
  </div>
</div>
"""
        )
    return '<div class="kegg-grid">' + "".join(cards) + "</div>"


def stats_dashboard(s: dict) -> str:
    tc = s.get("network_type_counts", {})
    cards = [
        ("药病交集靶点", s.get("n_overlap", "—"), "下游网络/富集核心输入"),
        ("药物靶点并集", s.get("n_drug_targets", "—"), f"占交集 {s.get('overlap_pct_of_drug', '—')}%"),
        ("疾病基因并集", s.get("n_disease_union", "—"), f"交集占病 {s.get('overlap_pct_of_disease', '—')}%"),
        ("有效成分数", s.get("n_compounds", "—"), "进入成分层筛选"),
        ("HCTP 边数", s.get("n_network_edges", "—"), f"A{tc.get('A',0)}/B{tc.get('B',0)}/C{tc.get('C',0)}/D{tc.get('D',0)}"),
        ("KEGG 通路项", s.get("n_kegg_terms", "—"), f"padj<0.05：{s.get('n_kegg_padj05', '—')}"),
        ("GO 条目", s.get("n_go", "—"), "BP/CC/MF 合并表"),
        ("PPI 边 / 蛋白", f"{s.get('n_ppi_edges','—')} / {s.get('n_ppi_proteins','—')}", "STRING 高分互作"),
    ]
    html_cards = "".join(
        f'<div class="metric"><div class="metric-val">{esc(v)}</div>'
        f'<div class="metric-lab">{esc(lab)}</div>'
        f'<div class="metric-sub">{esc(sub)}</div></div>'
        for lab, v, sub in cards
    )
    return f'<div class="metrics">{html_cards}</div>'


def per_herb_table(s: dict) -> str:
    rows = []
    for r in s.get("per_herb", []):
        zh = r.get("herb_zh", "")
        no = int(r.get("n_overlap", 0) or 0)
        nt = int(r.get("n_targets", 0) or 0)
        cls = ' class="zero"' if no == 0 else ""
        rows.append(
            f"<tr{cls}><td>{esc(zh)}</td><td>{nt}</td><td><strong>{no}</strong></td></tr>"
        )
    return (
        "<table><thead><tr><th>药味</th><th>靶点数</th><th>与疾病交集</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def top_kegg_table(s: dict) -> str:
    # UC-relevant short notes for known inflammatory pathways
    bio_map = {
        "hsa04657": "IL-17 轴与肠道黏膜炎症、中性粒细胞募集密切相关，UC 常用讨论通路。",
        "hsa04668": "TNF 信号是 UC 病理与抗 TNF 治疗的核心轴。",
        "hsa04620": "TLR 通路参与肠黏膜先天免疫与屏障应答。",
        "hsa04066": "HIF-1 与黏膜缺氧、炎症微环境相关。",
        "hsa04151": "PI3K-Akt 调控细胞存活、增殖与屏障相关信号。",
        "hsa05417": "富集常因共享炎症/脂质代谢基因；解读时对照 UC 文献，勿直接等同动脉粥样硬化。",
        "hsa04933": "AGE-RAGE 常因炎症基因重叠出现；宜作交叉通路提示。",
        "hsa05161": "病毒感染通路多反映 NF-κB/凋亡等共享模块，非指肝炎病因。",
        "hsa05167": "同上，感染类通路多为共享信号模块富集。",
        "hsa05205": "肿瘤相关通路常因增殖/基质基因重叠；作旁证而非肿瘤结论。",
    }
    rows = []
    for i, r in enumerate(s.get("top_kegg", [])[:10], 1):
        pid = r.get("id", "")
        note = bio_map.get(pid, "结合 geneID 与 UC 文献判断是否为共享炎症模块或疾病特异轴。")
        rows.append(
            "<tr>"
            f"<td>{i}</td><td>{esc(pid)}</td><td>{esc(r.get('desc',''))}</td>"
            f"<td>{r.get('count','—')}</td><td>{esc(fmt_p(r.get('pvalue')))}</td>"
            f"<td>{esc(fmt_p(r.get('padj')))}</td><td class='bio-cell'>{esc(note)}</td>"
            "</tr>"
        )
    return (
        "<table class='kegg-table'><thead><tr>"
        "<th>#</th><th>ID</th><th>通路</th><th>基因数</th><th>pvalue</th><th>padj</th><th>生物学解读提示</th>"
        f"</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def db_table(s: dict) -> str:
    full = s.get("disease_by_db_venn_full") or s.get("disease_by_db", {})
    down = s.get("disease_by_db_downstream", {})
    keys = list(dict.fromkeys(list(full.keys()) + list(down.keys())))
    rows = []
    for k in keys:
        rows.append(
            f"<tr><td>{esc(k)}</td>"
            f"<td>{int(full.get(k, 0))}</td>"
            f"<td>{int(down.get(k, 0)) if k in down else '—'}</td></tr>"
        )
    gc_full = s.get("genecards_full", full.get("GeneCards", "—"))
    gc_f = s.get("genecards_filtered_ge40", down.get("GeneCards", "—"))
    cut = s.get("genecards_relevance_cutoff", 40)
    return f"""
<div class="callout warn">
  <p><strong>常见疑问：GeneCards 明明有 {esc(gc_full)}，为什么下游疾病只有 {esc(s.get('n_disease_union'))}、药病交集只有 {esc(s.get('n_overlap'))}？</strong></p>
  <p>这不是算错，而是<strong>两套口径 + 一次药病交集</strong>：</p>
  <ol>
    <li><strong>多库韦恩图</strong>故意用 GeneCards <em>全量导出</em>（{esc(gc_full)}），展示各库覆盖广度。</li>
    <li><strong>下游网络/富集</strong>对 GeneCards 做 Relevance Score ≥ {esc(cut)} 过滤 → 约 <strong>{esc(gc_f)}</strong> 个高相关基因，再与 TTD/DrugBank/OMIM/CTD 取并集得到疾病并集 <strong>{esc(s.get('n_disease_union'))}</strong>。全量 GeneCards 噪声大（弱相关基因极多），不过滤会稀释富集与 PPI，反而不严谨。</li>
    <li><strong>药病交集 291</strong> = 药物靶点并集（{esc(s.get('n_drug_targets'))}）∩ 疾病并集（{esc(s.get('n_disease_union'))}），不是「GeneCards 全量自己与自己交集」。交集变小是因为分子集合不同：方剂靶点有限，不可能覆盖全部疾病基因。</li>
  </ol>
</div>
<table>
  <thead><tr><th>数据库</th><th>韦恩全量口径</th><th>下游过滤口径</th></tr></thead>
  <tbody>{''.join(rows)}</tbody>
</table>
<p class="note">技能规范：韦恩用 VennFull；下游交集/富集用 GeneCards Relevance≥{esc(cut)} ∪ 其他库（见 <code>疾病靶点按库_下游.csv</code> / <code>疾病靶点合并.csv</code>）。</p>
"""


def build() -> None:
    if "Desktop" in str(REPORT_DIR) or "桌面" in str(REPORT_DIR):
        raise SystemExit("Refusing Desktop path")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    s = load_stats()
    tc = s.get("network_type_counts", {})

    sections = [
        {
            "id": "venn",
            "title": "1. 韦恩图",
            "blurb": "先看疾病多库与药病交集规模，确定下游输入。",
            "extra": (
                "<div class='callout'>"
                f"<p><strong>关键数字：</strong>疾病并集 {esc(s.get('n_disease_union'))}；"
                f"药物靶点 {esc(s.get('n_drug_targets'))}；"
                f"<em>药病交集 {esc(s.get('n_overlap'))}</em>"
                f"（占药靶 {esc(s.get('overlap_pct_of_drug'))}%，占病基 "
                f"{esc(s.get('overlap_pct_of_disease'))}%）。"
                "中间交集是后续网络与富集的核心基因集。</p>"
                "<p><strong>生物学意义：</strong>交集靶点提示方剂成分可能直接扰动 UC 相关分子；"
                "独有药物靶点可能为脱靶/其他适应症信号，独有疾病基因则尚未被本方成分覆盖。</p>"
                f"{db_table(s)}</div>"
            ),
            "figs": [
                {
                    "title": "疾病数据库可视化韦恩图",
                    "meaning": "多库疾病基因集合关系（TTD / DrugBank / GeneCards / OMIM 等）",
                    "howto": "看各库独有与两两交集；GeneCards 通常远大于其他库。",
                    "bio": "多库交叉可提高疾病基因可信度；写作时说明并集/交集口径。",
                    "stats_line": f"全量口径示例：GeneCards={s.get('disease_by_db',{}).get('GeneCards','—')}",
                    "png": "图片/韦恩图/疾病数据库可视化韦恩图.png",
                    "svg": "图片/韦恩图/疾病数据库可视化韦恩图.svg",
                },
                {
                    "title": "疾病药物交集韦恩图",
                    "meaning": "药物靶点并集 ∩ 疾病基因",
                    "howto": "中间数字即药病交集；两侧为各集合独有。",
                    "bio": "291 个交集基因是「可能介导疗效」的分子候选，进入 PPI/KEGG/HCTP。",
                    "stats_line": (
                        f"Drugs={s.get('n_drug_targets')} · Disease={s.get('n_disease_union')} · "
                        f"∩={s.get('n_overlap')}"
                    ),
                    "png": "图片/韦恩图/疾病药物交集韦恩图.png",
                    "svg": "图片/韦恩图/疾病药物交集韦恩图.svg",
                },
            ],
        },
        {
            "id": "extra",
            "title": "2. 补充柱状 / UpSet / 热图",
            "blurb": "从单药、成分到通路覆盖，量化各方贡献。",
            "extra": (
                "<div class='callout'>"
                f"<p><strong>药味：</strong>名义 {esc(s.get('n_herbs_nominal'))} 味，"
                f"有靶点 {esc(s.get('n_herbs_with_targets'))} 味；"
                f"成分约 {esc(s.get('n_compounds'))} 个；"
                f"药–成分边 {esc(s.get('n_herb_comp_edges'))}。</p>"
                "<p><strong>生物学意义：</strong>香附/淫羊藿/黄连等交集靶点多，提示其在方剂抗炎轴中贡献更大；"
                "肉桂靶点为 0，流量图中通常不可见，写作时需注明数据缺口而非「无作用」。"
                "UpSet 中 <code>same*</code> 为多药共享成分，常对应「君臣协同」的分子基础；"
                "热图显示各药对 Top 通路的靶点覆盖强度。</p>"
                f"<h4>单药 × 疾病交集</h4>{per_herb_table(s)}</div>"
            ),
            "figs": [
                {
                    "title": "单药疾病交集柱状图",
                    "meaning": "各味药与疾病交集基因数",
                    "howto": "柱越高，该药贡献的交集靶点越多。",
                    "bio": "识别「主贡献药味」，用于讨论方剂配伍中的核心药。",
                    "png": "图片/补充_技能扩展/单药疾病交集柱状图.png",
                    "svg": "图片/补充_技能扩展/单药疾病交集柱状图.svg",
                },
                {
                    "title": "成分疾病交集柱状图",
                    "meaning": "成分层面的药病交集",
                    "howto": "识别枢纽成分（连接多个疾病靶点）。",
                    "bio": "枢纽成分是实验验证与质量标志物的优先候选。",
                    "png": "图片/补充_技能扩展/成分疾病交集柱状图.png",
                    "svg": "图片/补充_技能扩展/成分疾病交集柱状图.svg",
                },
                {
                    "title": "成分疾病交集按药柱状图",
                    "meaning": "按药分面的成分交集",
                    "howto": "看方剂内部差异与各药主导成分。",
                    "bio": "便于论证「某药主要通过某几类成分起效」。",
                    "png": "图片/补充_技能扩展/成分疾病交集按药柱状图.png",
                    "svg": "图片/补充_技能扩展/成分疾病交集按药柱状图.svg",
                },
                {
                    "title": "GO_BPCCMF 柱状图",
                    "meaning": "GO 三大类富集条形",
                    "howto": "配合气泡图看功能主题（炎症、凋亡、信号转导等）。",
                    "bio": f"共 {s.get('n_go','—')} 条 GO 记录；反映交集基因的功能分布。",
                    "stats_line": f"GO 条目 n={s.get('n_go','—')}",
                    "png": "图片/补充_技能扩展/GO_BPCCMF柱状图.png",
                    "svg": "图片/补充_技能扩展/GO_BPCCMF柱状图.svg",
                },
                {
                    "title": "药味成分交集 UpSet 图",
                    "meaning": "多药成分集合交集",
                    "howto": "左侧 Set size；上方柱=特定交集；点阵=参与药味；same* 多为共享成分。",
                    "bio": "共享成分解释多药协同；独有成分解释药味特异性。",
                    "png": "图片/补充_技能扩展/药味成分交集UpSet图.png",
                    "svg": "图片/补充_技能扩展/药味成分交集UpSet图.svg",
                },
                {
                    "title": "药味通路覆盖热图",
                    "meaning": "药味 × Top20 通路的交集靶点覆盖",
                    "howto": "格子数字=经成分链到该通路的不同交集靶点数；颜色越深覆盖越强。",
                    "bio": "若多药同时深色覆盖 TNF/IL-17/TLR 等，支持「多成分–多靶点–炎症轴」叙事。",
                    "png": "图片/补充_技能扩展/药味通路覆盖热图.png",
                    "svg": "图片/补充_技能扩展/药味通路覆盖热图.svg",
                },
            ],
        },
        {
            "id": "enrich",
            "title": "3. 富集分析",
            "blurb": "GO / KEGG：先看显著性与主题，再落到官方通路图。",
            "extra": (
                "<div class='callout'>"
                f"<p><strong>KEGG：</strong>{esc(s.get('n_kegg_terms'))} 条通路项，"
                f"其中 padj&lt;0.05 约 {esc(s.get('n_kegg_padj05'))} 条。"
                "优先报告 IL-17、TNF、TLR、HIF-1、PI3K-Akt 等与 UC/黏膜免疫相关者；"
                "感染/肿瘤类通路常因共享 NF-κB、凋亡模块而富集，需谨慎表述。</p>"
                f"<h4>Top10 KEGG（按 pvalue）</h4>{top_kegg_table(s)}</div>"
            ),
            "figs": [
                {
                    "title": "BPCCMF 气泡图",
                    "meaning": "GO BP/CC/MF 气泡",
                    "howto": "横轴富集程度/基因比，点大小=基因数，颜色=显著性。",
                    "bio": "BP 常出现炎症应答、凋亡、信号转导等主题，支撑机制讨论。",
                    "png": "图片/富集分析/BPCCMF气泡图.png",
                    "svg": "图片/富集分析/BPCCMF气泡图.svg",
                },
                {
                    "title": "KEGG 棒棒糖图",
                    "meaning": "通路富集排序",
                    "howto": "优先看 Top 通路名称与 p / p.adjust。",
                    "bio": "棒棒糖便于论文主图展示「最显著通路名单」。",
                    "png": "图片/富集分析/KEGG棒棒糖图.png",
                    "svg": "图片/富集分析/KEGG棒棒糖图.svg",
                },
                {
                    "title": "KEGG 柱状图",
                    "meaning": "通路富集条形",
                    "howto": "与棒棒糖互补，便于比长度。",
                    "bio": "适合补充材料或并排比较基因数。",
                    "png": "图片/富集分析/KEGG柱状图.png",
                    "svg": "图片/富集分析/KEGG柱状图.svg",
                },
                {
                    "title": "KEGG 圈图",
                    "meaning": "通路–基因弦图",
                    "howto": "外围扇区=通路/基因，弦=归属关系。",
                    "bio": "展示枢纽基因同时属于多条炎症相关通路。",
                    "png": "图片/富集分析/KEGG圈图.png",
                    "svg": "图片/富集分析/KEGG圈图.svg",
                },
            ],
        },
        {
            "id": "network",
            "title": "4. 网络与 PPI",
            "blurb": "HCTP 四层网络 + 桑基流量 + STRING 互作。",
            "extra": (
                "<div class='callout'>"
                f"<p><strong>HCTP 节点：</strong>药(A)={tc.get('A','—')}，"
                f"成分(B)={tc.get('B','—')}，靶点(C)={tc.get('C','—')}，"
                f"通路(D)={tc.get('D','—')}；边={s.get('n_network_edges','—')}。</p>"
                f"<p><strong>PPI：</strong>{s.get('n_ppi_edges','—')} 条高分互作，"
                f"涉及 {s.get('n_ppi_proteins','—')} 个蛋白。</p>"
                "<p><strong>生物学意义：</strong>网络把「药→成分→靶→通路」连成可讲述的作用轴；"
                "桑基带宽反映关联强度；PPI 中 Degree 高的蛋白（如 TNF、AKT1、NFKB1、STAT3 等常见炎症枢纽）"
                "是验证与机制深挖的优先节点。</p></div>"
            ),
            "figs": [
                {
                    "title": "药物有效成分疾病靶点通路网络图",
                    "meaning": "HCTP 四层网络",
                    "howto": "A 药 / B 成分 / C 靶 / D 通路；看枢纽靶点与 same*。",
                    "bio": "整体拓扑展示方剂多成分多靶点特征。",
                    "stats_line": f"边={s.get('n_network_edges')} · C靶={tc.get('C')} · D通路={tc.get('D')}",
                    "png": "图片/网络图/药物有效成分疾病靶点通路网络图.png",
                    "svg": "图片/网络图/药物有效成分疾病靶点通路网络图.svg",
                },
                {
                    "title": "药物有效成分疾病靶点通路网络图（椭圆布局）",
                    "meaning": "同网络的椭圆分层布局",
                    "howto": "层次更清晰，便于答辩展示四层结构。",
                    "bio": "适合作为方法学/结果主图展示「分层作用」。",
                    "png": "图片/网络图/药物有效成分疾病靶点通路网络图_椭圆布局.png",
                    "svg": "图片/网络图/药物有效成分疾病靶点通路网络图_椭圆布局.svg",
                },
                {
                    "title": "药成分靶点通路桑基图",
                    "meaning": "筛选后的四层流量总览（Top 成分/靶/通路）",
                    "howto": "带宽≈关联强度；色带随药味；分列着色。",
                    "bio": "直观讲述主要流量是否汇入 TNF/IL-17 等炎症轴。",
                    "png": "图片/网络图/药成分靶点通路桑基图.png",
                    "svg": "图片/网络图/药成分靶点通路桑基图.svg",
                },
                {
                    "title": "筛选成分桑基图",
                    "meaning": "前 16 成分 4×4 分面",
                    "howto": "每个子图一个成分：药→靶→通路。",
                    "bio": "适合逐成分讲「作用轴」，对应实验验证设计。",
                    "png": "图片/网络图/筛选成分桑基图.png",
                    "svg": "图片/网络图/筛选成分桑基图.svg",
                },
                {
                    "title": "STRING PPI（vector）",
                    "meaning": "STRING 蛋白互作网络",
                    "howto": "看互作紧密模块。",
                    "bio": "模块化提示共调控的炎症/凋亡蛋白群。",
                    "stats_line": f"边={s.get('n_ppi_edges')} · 蛋白={s.get('n_ppi_proteins')}",
                    "png": "图片/PPI/string_vector_graphic.png",
                    "svg": "图片/PPI/string_vector_graphic.svg",
                },
                {
                    "title": "PPI 渐变图",
                    "meaning": "同心/渐变布局 PPI",
                    "howto": "突出核心与外围结构。",
                    "bio": "核心圈蛋白优先作为 hub 讨论。",
                    "png": "图片/PPI/PPI渐变图.png",
                    "svg": "图片/PPI/PPI渐变图.svg",
                },
                {
                    "title": "PPI 渐变图（Degree）",
                    "meaning": "按 Degree 强调中心性",
                    "howto": "节点越大/越突出，连接度越高。",
                    "bio": "高 Degree 靶点常为关键炎症转录/激酶节点。",
                    "png": "图片/PPI/PPI渐变图_Degree.png",
                    "svg": "图片/PPI/PPI渐变图_Degree.svg",
                },
            ],
        },
    ]

    section_html = []
    nav = ['<a href="#overview">0. 关键统计总览</a>', '<a href="#bio">生物学结论提纲</a>']
    for sec in sections:
        nav.append(f'<a href="#{esc(sec["id"])}">{esc(sec["title"])}</a>')
        cards = "".join(
            fig_card(
                f["title"],
                f["meaning"],
                f["howto"],
                f["png"],
                f.get("svg"),
                note=f.get("note"),
                bio=f.get("bio"),
                stats_line=f.get("stats_line"),
            )
            for f in sec["figs"]
        )
        extra = sec.get("extra", "")
        section_html.append(
            f"""
<section id="{esc(sec['id'])}">
  <h2>{esc(sec['title'])}</h2>
  <p class="blurb">{esc(sec['blurb'])}</p>
  {extra}
  <div class="grid">{cards}</div>
</section>
"""
        )
    nav.extend(
        [
            '<a href="#kegg">5. KEGG 官方通路图</a>',
            '<a href="#data">6. 数据与写作</a>',
        ]
    )

    top3 = s.get("per_herb", [])[:3]
    top3_txt = "、".join(
        f"{r.get('herb_zh')}（交集{r.get('n_overlap')}）" for r in top3
    ) or "—"

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>溃疡性结肠炎 · 网络药理学交付报告</title>
<style>
:root {{
  --ink: #1c2a24;
  --muted: #5b6b63;
  --line: #d7e0d9;
  --bg: #f4f1ea;
  --paper: #fffcf7;
  --accent: #1f6f5b;
  --accent-soft: #d8eee6;
  --warn: #8a5a2b;
  --shadow: 0 10px 28px rgba(28, 42, 36, 0.08);
  --radius: 14px;
  --serif: "Source Han Serif SC", "Noto Serif SC", "Songti SC", "STSong", Georgia, serif;
  --sans: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  font-family: var(--sans);
  color: var(--ink);
  background:
    radial-gradient(1200px 600px at 10% -10%, #e8f3ee 0%, transparent 55%),
    radial-gradient(900px 500px at 100% 0%, #efe6d6 0%, transparent 50%),
    var(--bg);
  line-height: 1.65;
}}
.wrap {{
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  gap: 28px;
  max-width: 1320px;
  margin: 0 auto;
  padding: 28px 22px 64px;
}}
nav.toc {{
  position: sticky; top: 18px; align-self: start;
  background: var(--paper); border: 1px solid var(--line);
  border-radius: var(--radius); padding: 18px 16px; box-shadow: var(--shadow);
  max-height: calc(100vh - 36px); overflow: auto;
}}
nav.toc .brand {{ font-family: var(--serif); font-size: 1.05rem; font-weight: 700; margin: 0 0 6px; color: var(--accent); }}
nav.toc .status {{
  display: inline-block; font-size: 0.72rem; color: var(--warn);
  background: #f7ebdc; border-radius: 999px; padding: 2px 8px; margin-bottom: 12px;
}}
nav.toc a {{
  display: block; color: var(--ink); text-decoration: none;
  font-size: 0.9rem; padding: 6px 8px; border-radius: 8px;
}}
nav.toc a:hover {{ background: var(--accent-soft); color: var(--accent); }}
main {{ min-width: 0; }}
header.hero {{
  background: linear-gradient(135deg, #1f6f5b 0%, #2f8f74 48%, #3a6b58 100%);
  color: #f7fffb; border-radius: 18px; padding: 28px 28px 24px;
  box-shadow: var(--shadow); margin-bottom: 22px;
}}
header.hero h1 {{
  font-family: var(--serif); font-size: clamp(1.5rem, 2.4vw, 2.1rem);
  margin: 0 0 10px; letter-spacing: 0.02em;
}}
header.hero p {{ margin: 0; opacity: 0.95; max-width: 78ch; }}
.meta-row {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }}
.chip {{
  background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.22);
  border-radius: 999px; padding: 4px 12px; font-size: 0.82rem;
}}
.chip a {{ color: #fff; }}
section {{
  background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius);
  padding: 22px 22px 8px; margin-bottom: 18px; box-shadow: var(--shadow);
}}
section h2 {{ font-family: var(--serif); margin: 0 0 6px; font-size: 1.35rem; color: var(--accent); }}
section h3, section h4 {{ font-family: var(--serif); color: var(--accent); margin: 14px 0 8px; }}
.blurb {{ color: var(--muted); margin: 0 0 14px; }}
.metrics {{
  display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px; margin: 10px 0 16px;
}}
.metric {{
  background: #fff; border: 1px solid var(--line); border-radius: 12px;
  padding: 12px 12px 10px;
}}
.metric-val {{ font-family: var(--serif); font-size: 1.55rem; font-weight: 700; color: var(--accent); }}
.metric-lab {{ font-size: 0.88rem; font-weight: 600; margin-top: 2px; }}
.metric-sub {{ font-size: 0.78rem; color: var(--muted); margin-top: 2px; }}
.callout {{
  background: #f3faf6; border: 1px solid #cfe5da; border-radius: 12px;
  padding: 12px 14px; margin: 0 0 16px; font-size: 0.94rem;
}}
.callout.warn {{
  background: #fff8ef; border-color: #e8d0a8;
}}
.callout p {{ margin: 0 0 8px; }}
.grid {{
  display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px; margin-bottom: 14px;
}}
.card {{
  border: 1px solid var(--line); border-radius: 12px; overflow: hidden;
  background: #fff; display: flex; flex-direction: column;
}}
.card-media {{
  background: #eef3ef; min-height: 160px;
  display: flex; align-items: center; justify-content: center;
}}
.card-media img {{
  width: 100%; max-height: 360px; object-fit: contain; display: block; background: #fff;
}}
#venn .card-media img {{ max-height: 480px; }}
#venn .grid {{ grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); }}
.card-body {{ padding: 12px 14px 14px; }}
.card-body h3 {{ margin: 0 0 8px; font-size: 1.02rem; font-family: var(--serif); }}
.card-body p {{ margin: 0 0 8px; font-size: 0.9rem; }}
.statline {{
  font-size: 0.8rem !important; color: var(--accent); background: var(--accent-soft);
  border-radius: 6px; padding: 4px 8px !important; display: inline-block;
}}
.tag {{
  display: inline-block; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em;
  color: var(--accent); background: var(--accent-soft); border-radius: 6px;
  padding: 1px 7px; margin-right: 6px; vertical-align: 1px;
}}
.tag.how {{ color: #6b4d2e; background: #f3e6d4; }}
.tag.bio {{ color: #1a4a7a; background: #dceaf7; }}
.note {{ color: var(--muted); font-size: 0.86rem; }}
.links {{ font-size: 0.85rem; }}
.links a {{ color: var(--accent); }}
.missing {{ color: var(--muted); padding: 40px 12px; text-align: center; }}
.kegg-grid {{
  display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px; margin: 8px 0 16px;
}}
.kegg-card {{ border: 1px solid var(--line); border-radius: 10px; overflow: hidden; background: #fff; }}
.kegg-card img {{ width: 100%; height: 150px; object-fit: contain; background: #fafafa; display: block; }}
.kegg-meta {{ padding: 8px 10px 10px; display: flex; flex-direction: column; gap: 2px; font-size: 0.8rem; }}
.kegg-meta span {{ color: var(--muted); }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; margin: 8px 0 12px; }}
th, td {{ border: 1px solid var(--line); padding: 7px 9px; text-align: left; vertical-align: top; }}
th {{ background: #eef6f2; }}
tr.zero td {{ color: var(--muted); }}
.bio-cell {{ font-size: 0.82rem; color: #334; }}
.kegg-table {{ font-size: 0.82rem; }}
ol.writing {{ margin-top: 6px; }}
.bio-box li {{ margin-bottom: 6px; }}
footer {{ color: var(--muted); font-size: 0.85rem; text-align: center; margin-top: 8px; }}
@media (max-width: 920px) {{
  .wrap {{ grid-template-columns: 1fr; }}
  nav.toc {{ position: static; max-height: none; }}
}}
</style>
</head>
<body>
<div class="wrap">
  <nav class="toc" aria-label="目录">
    <p class="brand">交付图注报告</p>
    <span class="status">FROZEN 2026-07-26</span>
    {''.join(nav)}
    <hr style="border:none;border-top:1px solid var(--line);margin:12px 0;" />
    <a href="报告/图注与解读说明.md" target="_blank">Markdown 原文</a>
    <a href="报告/_stats.json" target="_blank">统计 JSON</a>
  </nav>
  <main>
    <header class="hero">
      <h1>溃疡性结肠炎 · 网络药理学交付报告</h1>
      <p>以 12 味药（肉桂靶点为 0）筛选有效成分与疾病靶点交集，构建药–成分–靶点–通路（HCTP）与 PPI，并做 GO/KEGG 富集。本页汇总<strong>关键统计</strong>、<strong>读图方法</strong>与<strong>生物学意义</strong>，数字来自 <code>数据/</code> 实时汇总。图片路径均为相对本目录的 <code>图片/...</code>，请<strong>打包整个「交付文件」文件夹</strong>发送，勿只发单个 HTML。</p>
      <div class="meta-row">
        <span class="chip">交集 {esc(s.get('n_overlap'))} 基因 · KEGG {esc(s.get('n_kegg_terms'))} 项 · HCTP 边 {esc(s.get('n_network_edges'))}</span>
        <span class="chip"><a href="README_轨B说明.txt">轨 B README</a></span>
        <span class="chip"><a href="数据/富集分析/KEGG.csv">KEGG.csv</a></span>
        <span class="chip">分享：整夹打包 → 打开本 HTML</span>
      </div>
    </header>

    <section id="overview">
      <h2>0. 关键统计总览</h2>
      <p class="blurb">可直接写入结果部分的「规模数字」。刷新报告会自动重算。</p>
      {stats_dashboard(s)}
      <div class="callout">
        <p><strong>数据观看入口：</strong></p>
        <ul>
          <li><code>数据/疾病/</code> — 多库疾病基因与并集</li>
          <li><code>数据/药物/</code> — 全药/单药靶点、药病交集、成分边与重命名</li>
          <li><code>数据/网络图/</code> — <code>network.csv</code> / <code>type.csv</code>（A/B/C/D）</li>
          <li><code>数据/富集分析/</code> — <code>KEGG.csv</code>、<code>BPCCMF.csv</code>（含 geneID）</li>
          <li><code>数据/PPI/</code> — STRING 高分互作边</li>
          <li><code>图片/KEGG官方通路图/</code> — Top20 官方通路地图</li>
        </ul>
      </div>
    </section>

    <section id="bio">
      <h2>生物学结论提纲（写作可用）</h2>
      <ol class="bio-box">
        <li><strong>靶点层面：</strong>方剂药物靶点 {esc(s.get('n_drug_targets'))} 与疾病基因 {esc(s.get('n_disease_union'))}
          交集得到 <strong>{esc(s.get('n_overlap'))}</strong> 个候选靶点
          （占药靶 {esc(s.get('overlap_pct_of_drug'))}%），提示存在可观的疾病相关分子重叠。</li>
        <li><strong>药味贡献：</strong>交集靶点领先药味为 {esc(top3_txt)}；
          肉桂当前靶点为 0，讨论时注明数据来源限制。</li>
        <li><strong>成分协同：</strong>约 {esc(s.get('n_compounds'))} 个有效成分进入分析，
          UpSet 中共享成分（same*）支持多药协同，独有成分支持药味特异性。</li>
        <li><strong>通路层面：</strong>KEGG 显著富集项丰富（n={esc(s.get('n_kegg_terms'))}）。
          与 UC 更直接相关的优先讨论：<em>IL-17、TNF、TLR、HIF-1、PI3K-Akt</em>；
          感染/肿瘤类通路多反映共享炎症模块，避免过度因果表述。</li>
        <li><strong>网络叙事：</strong>HCTP（A{tc.get('A','—')}/B{tc.get('B','—')}/C{tc.get('C','—')}/D{tc.get('D','—')}）
          与桑基展示「药→成分→靶→通路」流量；PPI（{esc(s.get('n_ppi_edges'))} 边 /
          {esc(s.get('n_ppi_proteins'))} 蛋白）突出枢纽蛋白互作。</li>
        <li><strong>局限：</strong>本分析为预测性网络药理学证据，需细胞/动物实验与临床文献交叉验证；
          KEGG 官方图仅作通路定位，不替代统计富集图。</li>
      </ol>
    </section>

    {''.join(section_html)}

    <section id="kegg">
      <h2>5. KEGG 官方通路图（Top20）</h2>
      <p class="blurb">富集 pvalue 排名前 20 的 KEGG 官网通路地图。对照 <code>数据/富集分析/KEGG.csv</code> 的 geneID 在图中定位本研究基因。学术使用请遵守 <a href="https://www.kegg.jp/kegg/legal.html" target="_blank" rel="noopener">KEGG 条款</a>。</p>
      <div class="callout">
        <p><strong>怎么用：</strong>在论文/答辩中选 2–4 条与 UC 最相关的通路（如 IL-17、TNF、TLR、HIF-1），
        展示官方图并标出交集基因位置；其余感染/肿瘤类通路作「共享炎症模块」补充即可。</p>
      </div>
      {kegg_gallery()}
    </section>

    <section id="data">
      <h2>6. 数据目录与写作建议</h2>
      <table>
        <thead><tr><th>目录</th><th>典型文件</th><th>用途</th></tr></thead>
        <tbody>
          <tr><td>数据/疾病/</td><td>疾病靶点按库、合并</td><td>多库来源与并集</td></tr>
          <tr><td>数据/药物/</td><td>药物靶点、单药交集、成分边</td><td>成分归属与药病交集</td></tr>
          <tr><td>数据/网络图/</td><td>network.csv、type.csv</td><td>HCTP 边与节点类型 A/B/C/D</td></tr>
          <tr><td>数据/富集分析/</td><td>KEGG.csv、BPCCMF.csv</td><td>富集统计表（含 geneID）</td></tr>
          <tr><td>数据/PPI/</td><td>string_interactions_short.tsv</td><td>高分互作边</td></tr>
        </tbody>
      </table>
      <h3>建议写作顺序</h3>
      <ol class="writing">
        <li>疾病多库与药病交集（韦恩）→ 报出 {esc(s.get('n_overlap'))} 个交集基因</li>
        <li>单药/成分贡献（柱图、UpSet）→ 点名主贡献药味与共享成分</li>
        <li>GO/KEGG 富集 → 点名 IL-17 / TNF / TLR 等</li>
        <li>KEGG 官方通路图佐证关键通路基因位置</li>
        <li>HCTP 网络 + 桑基总览 + 分面桑基</li>
        <li>PPI 说明蛋白互作枢纽</li>
      </ol>
      <h3>重跑入口</h3>
      <table>
        <thead><tr><th>步骤</th><th>脚本</th></tr></thead>
        <tbody>
          <tr><td>汇总统计 JSON</td><td>代码文件/28_collect_report_stats.py</td></tr>
          <tr><td>本 HTML 报告</td><td>代码文件/26_build_html_report.py</td></tr>
          <tr><td>裁韦恩空白</td><td>代码文件/27_trim_venn_whitespace.py</td></tr>
          <tr><td>打包轨 B</td><td>代码文件/11_pack_delivery_archive.py</td></tr>
        </tbody>
      </table>
    </section>
    <footer>由 26_build_html_report.py 生成 · 相对路径引用 图片/ 数据/ 报告/ · 请整夹分享</footer>
  </main>
</div>
</body>
</html>
"""
    HTML_PATH.write_text(doc, encoding="utf-8")
    # Stub in 报告/ so old bookmark still works
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_STUB.write_text(
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='UTF-8'/>"
        "<meta http-equiv='refresh' content='0;url=../图注与解读说明.html'/>"
        "<title>跳转到交付报告</title></head><body>"
        "<p>报告已移至交付根目录：<a href='../图注与解读说明.html'>图注与解读说明.html</a></p>"
        "</body></html>",
        encoding="utf-8",
    )
    print("OK", HTML_PATH, "stub", HTML_STUB, "stats_keys", len(s))


if __name__ == "__main__":
    build()
