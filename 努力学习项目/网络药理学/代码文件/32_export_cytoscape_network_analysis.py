# -*- coding: utf-8 -*-
"""Export one Cytoscape-style network table + colorful offline HTML report.

Outputs only:
  数据/网络图/网络图数据.csv
  数据/网络图/网络分析报告.html
  数据/网络图/肉桂_无靶点说明.txt
(Removes legacy Top10_*.csv / PNG albums.)
"""
from __future__ import annotations

import json
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

ROOT = Path(r"E:/RProject/努力学习项目/网络药理学/交付文件")
NET_DIR = ROOT / "数据" / "网络图"
DRUG_DIR = ROOT / "数据" / "药物"
FIG_DIR = ROOT / "图片" / "网络图" / "网络分析_Top10"

TYPE_LABEL = {"A": "药物 (A)", "B": "成分 (B)", "C": "靶点 (C)", "D": "通路 (D)"}


def xml_esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def short_label(s: str, n: int = 26) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def load_display_maps() -> tuple[dict[str, str], dict[str, str]]:
    """compound_id -> compound_name; herb_code -> herb_zh."""
    compound_map: dict[str, str] = {}
    herb_map: dict[str, str] = {}
    rename = DRUG_DIR / "成分重命名.csv"
    if rename.exists():
        df = pd.read_csv(rename, encoding="utf-8-sig")
        for _, r in df.iterrows():
            cid = str(r["compound_id"]).strip()
            cname = str(r["compound_name"]).strip()
            if cid and cname and cid not in compound_map:
                compound_map[cid] = cname
            hc = str(r.get("herb_code", "")).strip()
            hz = str(r.get("herb_zh", "")).strip()
            if hc and hz:
                herb_map[hc] = hz
    edges = DRUG_DIR / "草药成分边.csv"
    if edges.exists():
        ed = pd.read_csv(edges, encoding="utf-8-sig")
        for _, r in ed.iterrows():
            hc = str(r["herb_code"]).strip()
            hz = str(r["herb_zh"]).strip()
            if hc and hz:
                herb_map[hc] = hz
    return compound_map, herb_map


def attach_display_names(df: pd.DataFrame, compound_map: dict[str, str], herb_map: dict[str, str]) -> pd.DataFrame:
    """Add display_name: compounds use original molecule names; herbs use Chinese."""
    out = df.copy()

    def one(row) -> str:
        name = str(row["name"])
        t = str(row["type"])
        if t == "B":
            return compound_map.get(name, name)
        if t == "A":
            return herb_map.get(name, name)
        return name

    out["display_name"] = out.apply(one, axis=1)
    return out

# Distinct palettes per chart (each chart looks different; bars within also vary)
PALETTES = {
    "all_Degree": ["#0B6E4F", "#1B9B7A", "#2EBD95", "#4FD1A5", "#73DEBB", "#8FE6C8", "#A8EDD4", "#BFF2DF", "#D4F7E9", "#E8FBF3"],
    "all_BetweennessCentrality": ["#8B1E3F", "#A5274A", "#C0392B", "#D44A3A", "#E05D4E", "#E87366", "#EF8A7E", "#F4A194", "#F8B8AB", "#FCD0C4"],
    "all_ClosenessCentrality": ["#1A5276", "#1F6A9A", "#2874A6", "#3498DB", "#5DADE2", "#7FBCE8", "#A0CCEE", "#BDD9F2", "#D4E6F7", "#EAF2FB"],
    "all_Stress": ["#6B3F1A", "#8A5A2B", "#A66B2F", "#C17B38", "#D4924A", "#E0A85E", "#E8BB78", "#F0CD94", "#F5DCB0", "#FAEBCB"],
    "A_Degree": ["#145A32", "#1E8449", "#27AE60", "#2ECC71", "#58D68D", "#7DCEA0", "#A9DFBF", "#C8EAD6", "#D5F5E3", "#E8F8F0"],
    "A_BetweennessCentrality": ["#0E6655", "#117A65", "#148F77", "#16A085", "#1ABC9C", "#48C9B0", "#76D7C4", "#A3E4D7", "#D1F2EB", "#E8F6F3"],
    "B_Degree": ["#935116", "#B9770E", "#D68910", "#F39C12", "#F5B041", "#F7C25C", "#F8D07A", "#FAD79A", "#FBE2B8", "#FDEBD0"],
    "B_BetweennessCentrality": ["#7D3C98", "#8E44AD", "#9B59B6", "#AF7AC5", "#BB8FCE", "#C39BD3", "#D2B4DE", "#D7BDE2", "#E8DAEF", "#F5EEF8"],
    "C_Degree": ["#641E16", "#7B241C", "#922B21", "#A93226", "#C0392B", "#CD6155", "#D98880", "#E6B0AA", "#F2D7D5", "#F9EBEA"],
    "C_BetweennessCentrality": ["#4A235A", "#5B2C6F", "#6C3483", "#7D3C98", "#8E44AD", "#A569BD", "#BB8FCE", "#D2B4DE", "#E8DAEF", "#F5EEF8"],
    "D_Degree": ["#1C2833", "#2C3E50", "#34495E", "#5D6D7E", "#7F8C8D", "#95A5A6", "#AAB7B8", "#BFC9CA", "#D5DBDB", "#EAEDED"],
    "D_BetweennessCentrality": ["#0E4D64", "#117A8B", "#148F9C", "#17A2B8", "#48C9DB", "#76D7C4", "#7FB3D5", "#A9CCE3", "#D4E6F1", "#EBF5FB"],
}


def build_graph() -> tuple[nx.Graph, dict[str, str]]:
    edges = pd.read_csv(NET_DIR / "network.csv", encoding="utf-8-sig")
    types = pd.read_csv(NET_DIR / "type.csv", encoding="utf-8-sig")
    tmap = dict(zip(types["term"].astype(str), types["type"].astype(str)))
    G = nx.Graph()
    for _, r in edges.iterrows():
        G.add_edge(str(r["ID"]), str(r["SYMBOL"]))
    for n in tmap:
        if n not in G:
            G.add_node(n)
    return G, tmap


def topological_coefficient(G: nx.Graph, n) -> float:
    nbrs = list(G.neighbors(n))
    if len(nbrs) < 2:
        return 0.0
    s = 0.0
    pairs = 0
    for i in range(len(nbrs)):
        for j in range(i + 1, len(nbrs)):
            a, b = nbrs[i], nbrs[j]
            shared = len(set(G.neighbors(a)) & set(G.neighbors(b)))
            denom = min(G.degree(a), G.degree(b))
            if denom > 0:
                s += shared / denom
                pairs += 1
    return s / pairs if pairs else 0.0


def stress_centrality(G: nx.Graph) -> dict:
    stress = {n: 0 for n in G}
    for s in G.nodes():
        parents = {s: []}
        dist = {s: 0}
        sigma = {s: 1}
        queue = [s]
        order = []
        i = 0
        while i < len(queue):
            v = queue[i]
            i += 1
            order.append(v)
            for w in G.neighbors(v):
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                    parents[w] = [v]
                    sigma[w] = sigma[v]
                elif dist[w] == dist[v] + 1:
                    parents[w].append(v)
                    sigma[w] += sigma[v]
        for w in reversed(order[1:]):
            for v in parents.get(w, []):
                c = sigma[v]
                if v != s:
                    stress[v] += c
    return stress


def analyze(G: nx.Graph, tmap: dict[str, str]) -> pd.DataFrame:
    betweenness = nx.betweenness_centrality(G, normalized=True)
    closeness = nx.closeness_centrality(G, wf_improved=True)
    clustering = nx.clustering(G)
    avg_neigh = nx.average_neighbor_degree(G)
    stress = stress_centrality(G)

    components = list(nx.connected_components(G))
    ecc, aspl, radiality = {}, {}, {}
    for comp in components:
        sub = G.subgraph(comp).copy()
        if len(comp) == 1:
            n = next(iter(comp))
            ecc[n] = aspl[n] = radiality[n] = 0
            continue
        e = nx.eccentricity(sub)
        diam = max(e.values())
        for n in comp:
            ecc[n] = e[n]
            lengths = nx.single_source_shortest_path_length(sub, n)
            others = [d for t, d in lengths.items() if t != n]
            aspl[n] = float(np.mean(others)) if others else 0.0
            radiality[n] = (diam - aspl[n] + 1) / diam if diam > 0 else 0.0

    rows = []
    for n in G.nodes():
        deg = G.degree(n)
        rows.append(
            {
                "AverageShortestPathLength": aspl.get(n, 0.0),
                "BetweennessCentrality": betweenness.get(n, 0.0),
                "ClosenessCentrality": closeness.get(n, 0.0),
                "ClusteringCoefficient": clustering.get(n, 0.0),
                "Degree": int(deg),
                "Eccentricity": int(ecc.get(n, 0)),
                "IsSingleNode": "true" if deg == 0 else "false",
                "name": n,
                "NeighborhoodConnectivity": float(avg_neigh.get(n, 0.0)),
                "NumberOfDirectedEdges": 0,
                "NumberOfUndirectedEdges": int(deg),
                "PartnerOfMultiEdgedNodePairs": 0,
                "Radiality": radiality.get(n, 0.0),
                "selected": "false",
                "SelfLoops": 0,
                "shared name": n,
                "Stress": int(stress.get(n, 0)),
                "TopologicalCoefficient": topological_coefficient(G, n),
                "type": tmap.get(n, ""),
            }
        )
    cols = [
        "AverageShortestPathLength",
        "BetweennessCentrality",
        "ClosenessCentrality",
        "ClusteringCoefficient",
        "Degree",
        "Eccentricity",
        "IsSingleNode",
        "name",
        "NeighborhoodConnectivity",
        "NumberOfDirectedEdges",
        "NumberOfUndirectedEdges",
        "PartnerOfMultiEdgedNodePairs",
        "Radiality",
        "selected",
        "SelfLoops",
        "shared name",
        "Stress",
        "TopologicalCoefficient",
        "type",
    ]
    return pd.DataFrame(rows)[cols].sort_values(["Degree", "BetweennessCentrality"], ascending=False)


def top_payload(df: pd.DataFrame, metric: str, n: int = 10) -> dict:
    top = df.nlargest(n, metric)
    labels = []
    for _, r in top.iterrows():
        disp = str(r.get("display_name", r["name"]))
        code = str(r["name"])
        # chart: prefer original name; keep code in tooltip-ish suffix only if different
        if str(r["type"]) == "B" and disp != code:
            labels.append(disp)
        elif str(r["type"]) == "A" and disp != code:
            labels.append(disp)
        else:
            labels.append(code)
    return {
        "labels": labels,
        "codes": [str(r["name"]) for _, r in top.iterrows()],
        "types": [str(r["type"]) for _, r in top.iterrows()],
        "values": [
            float(r[metric]) if not isinstance(r[metric], (int, np.integer)) else int(r[metric])
            for _, r in top.iterrows()
        ],
    }


def write_rg_note(df: pd.DataFrame):
    rg = df[df["name"] == "RG"]
    lines = [
        "肉桂（RG）为何无靶点 / 网络度为 0",
        "=" * 40,
        "",
        "结论：数据缺口（BLOCKED_EXTERNAL），不是「肉桂无药理作用」。",
        "",
        "证据链：",
        "1. TCMSP肉桂有效成分.xlsx — 仅表头，无有效成分行",
        "2. TCMSP肉桂有效成分靶点表.xlsx — 空表",
        "3. 肉桂靶点基因.xlsx — 仅 UniProt 两列，缺成分–基因映射列",
        "4. 解析器要求第5列为基因；列数<5 → 靶点=0",
        "5. 未走 HERB→SwissTargetPrediction 补全",
        "6. type.csv 保留 RG，但 network.csv 无边 → Degree=0",
        "",
    ]
    if not rg.empty:
        r = rg.iloc[0]
        lines.append(
            f"本分析 RG：Degree={r['Degree']}, Betweenness={r['BetweennessCentrality']}, IsSingleNode={r['IsSingleNode']}"
        )
    (NET_DIR / "肉桂_无靶点说明.txt").write_text("\n".join(lines), encoding="utf-8")


def cleanup_old_top10():
    for f in NET_DIR.glob("Top10_*.csv"):
        f.unlink(missing_ok=True)
    html_old = NET_DIR / "网络分析_Top10图册.html"
    if html_old.exists():
        html_old.unlink()
    if FIG_DIR.exists():
        for f in FIG_DIR.glob("*"):
            f.unlink(missing_ok=True)
        try:
            FIG_DIR.rmdir()
        except OSError:
            pass


def build_html(df: pd.DataFrame) -> str:
    def svg_bar_chart(title: str, payload: dict, colors: list[str], chart_id: str) -> str:
        labels = payload["labels"]
        codes = payload.get("codes", labels)
        types = payload["types"]
        values = payload["values"]
        if not values:
            return f'<div class="card"><h3>{title}</h3><p class="empty">无数据</p></div>'
        w, h = 620, 320
        left, right, top, bot = 210, 42, 16, 36
        plot_w = w - left - right
        plot_h = h - top - bot
        vmax = max(values) if max(values) > 0 else 1
        n = len(values)
        gap = 6
        bh = max(10, (plot_h - gap * (n - 1)) / n)
        bars = []
        for i, (lab, code, typ, val) in enumerate(zip(labels, codes, types, values)):
            y = top + i * (bh + gap)
            bw = plot_w * (val / vmax)
            color = colors[i % len(colors)]
            txt = f"{val:.4g}" if isinstance(val, float) else str(val)
            shown = short_label(lab, 28)
            tip = lab if lab == code else f"{lab} ({code})"
            label = f"{shown} [{typ}]"
            bars.append(
                f'<g>'
                f'<title>{xml_esc(tip)}</title>'
                f'<rect x="{left}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="5" fill="{color}"/>'
                f'<text x="{left - 8}" y="{y + bh * 0.72:.1f}" text-anchor="end" class="ylab">{xml_esc(label)}</text>'
                f'<text x="{left + bw + 6:.1f}" y="{y + bh * 0.72:.1f}" class="vlab">{xml_esc(txt)}</text>'
                f"</g>"
            )
        axis = f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#C9B8A0" stroke-width="1"/>'
        return (
            f'<div class="card" id="{chart_id}">'
            f"<h3>{title}</h3>"
            f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{xml_esc(title)}">{axis}{"".join(bars)}</svg>'
            f"</div>"
        )

    chart_html = []
    for metric, title, key in [
        ("Degree", "全网 Top10 · Degree", "all_Degree"),
        ("BetweennessCentrality", "全网 Top10 · Betweenness", "all_BetweennessCentrality"),
        ("ClosenessCentrality", "全网 Top10 · Closeness", "all_ClosenessCentrality"),
        ("Stress", "全网 Top10 · Stress", "all_Stress"),
    ]:
        chart_html.append(svg_bar_chart(title, top_payload(df, metric), PALETTES[key], key))

    for t in ["A", "B", "C", "D"]:
        sub = df[df["type"] == t]
        if sub.empty:
            continue
        for metric in ["Degree", "BetweennessCentrality"]:
            key = f"{t}_{metric}"
            short = "Betweenness" if metric.startswith("Between") else metric
            chart_html.append(
                svg_bar_chart(
                    f"{TYPE_LABEL[t]} Top10 · {short}",
                    top_payload(sub, metric),
                    PALETTES[key],
                    key,
                )
            )

    n_nodes = len(df)
    n_iso = int((df["IsSingleNode"] == "true").sum())
    type_counts = df["type"].value_counts().to_dict()
    rg_deg = int(df.loc[df["name"] == "RG", "Degree"].iloc[0]) if (df["name"] == "RG").any() else None

    show_cols = [
        "name",
        "display_name",
        "type",
        "Degree",
        "BetweennessCentrality",
        "ClosenessCentrality",
        "Stress",
        "ClusteringCoefficient",
        "NeighborhoodConnectivity",
        "AverageShortestPathLength",
        "Radiality",
        "Eccentricity",
        "TopologicalCoefficient",
        "IsSingleNode",
    ]
    table_rows = []
    for _, r in df.iterrows():
        row = {}
        for c in show_cols:
            v = r[c] if c in r.index else ""
            if isinstance(v, (float, np.floating)):
                row[c] = round(float(v), 6)
            elif isinstance(v, (int, np.integer)):
                row[c] = int(v)
            else:
                row[c] = str(v)
        table_rows.append(row)

    table_json = json.dumps(table_rows, ensure_ascii=False)
    type_json = json.dumps({TYPE_LABEL.get(k, k): int(v) for k, v in type_counts.items()}, ensure_ascii=False)
    charts_block = "\n".join(chart_html)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>HCTP 网络分析报告</title>
<style>
:root {{
  --bg: #F3EEE4;
  --card: #FFFCFA;
  --ink: #1C2A24;
  --muted: #5B6B63;
  --line: #D4C4AE;
  --teal: #1A4F42;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
  background:
    radial-gradient(900px 420px at 10% -10%, #d9efe6 0%, transparent 55%),
    radial-gradient(700px 380px at 100% 0%, #f0d9c8 0%, transparent 50%),
    var(--bg);
  color: var(--ink);
}}
header {{
  padding: 28px 32px 22px;
  background: linear-gradient(135deg, #12352E, #1A4F42 55%, #2F6B5A);
  color: #F4FFF9;
}}
header h1 {{ margin: 0 0 8px; font-size: 1.55rem; font-weight: 700; }}
header p {{ margin: 0; opacity: .9; line-height: 1.55; max-width: 960px; }}
.wrap {{ max-width: 1280px; margin: 0 auto; padding: 22px 18px 48px; }}
.stats {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px; margin-bottom: 18px;
}}
.stat {{
  background: var(--card); border: 1px solid var(--line);
  border-radius: 14px; padding: 14px 16px;
}}
.stat .k {{ font-size: .82rem; color: var(--muted); }}
.stat .v {{ font-size: 1.4rem; font-weight: 700; margin-top: 4px; color: var(--teal); }}
.note {{
  background: #FFF7ED; border: 1px solid #E8C9A0; border-left: 4px solid #C17B38;
  border-radius: 12px; padding: 14px 16px; margin-bottom: 20px; color: #5B4632; line-height: 1.55;
}}
.grid {{
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px;
}}
@media (max-width: 960px) {{ .grid {{ grid-template-columns: 1fr; }} }}
.card {{
  background: var(--card); border: 1px solid var(--line); border-radius: 16px;
  padding: 12px 14px 8px; box-shadow: 0 8px 24px rgba(40,30,20,.05);
}}
.card h3 {{ margin: 0 0 6px; font-size: .98rem; color: var(--teal); }}
.card svg {{ width: 100%; height: auto; display: block; }}
.ylab {{ font-size: 11px; fill: #1C2A24; }}
.vlab {{ font-size: 11px; fill: #5B6B63; }}
.section-title {{ margin: 26px 0 12px; font-size: 1.12rem; color: var(--teal); }}
.toolbar {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 12px; }}
.toolbar input, .toolbar select {{
  border: 1px solid var(--line); border-radius: 10px; padding: 8px 12px; background: #fff; font: inherit;
}}
.table-wrap {{
  overflow: auto; max-height: 560px; border: 1px solid var(--line);
  border-radius: 14px; background: var(--card);
}}
table {{ width: 100%; border-collapse: collapse; font-size: .86rem; }}
th, td {{ padding: 8px 10px; border-bottom: 1px solid #EADFC8; text-align: left; white-space: nowrap; }}
th {{ position: sticky; top: 0; background: #E8F2ED; color: var(--teal); cursor: pointer; z-index: 1; }}
tr:hover td {{ background: #F7F3EB; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: .75rem; font-weight: 600; }}
.badge.A {{ background: #D5F5E3; color: #145A32; }}
.badge.B {{ background: #FDEBD0; color: #935116; }}
.badge.C {{ background: #F5B7B1; color: #641E16; }}
.badge.D {{ background: #D5DBDB; color: #1C2833; }}
footer {{ margin-top: 24px; color: var(--muted); font-size: .85rem; }}
code {{ background: rgba(0,0,0,.05); padding: 1px 6px; border-radius: 6px; }}
</style>
</head>
<body>
<header>
  <h1>HCTP 网络 · Cytoscape 风格分析报告</h1>
  <p>完整指标见同目录 <code>网络图数据.csv</code>（一表含全部节点；<code>name</code> 仍为网络代号以便对接 Cytoscape）。报告中成分显示<strong>原始化合物名称</strong>，药物显示中文药名。各 Top10 图使用不同色系。</p>
</header>
<div class="wrap">
  <div class="stats">
    <div class="stat"><div class="k">节点数</div><div class="v">{n_nodes}</div></div>
    <div class="stat"><div class="k">孤立节点</div><div class="v">{n_iso}</div></div>
    <div class="stat"><div class="k">肉桂 RG · Degree</div><div class="v">{rg_deg if rg_deg is not None else "—"}</div></div>
    <div class="stat"><div class="k">药物 A</div><div class="v">{type_counts.get("A", 0)}</div></div>
    <div class="stat"><div class="k">成分 B</div><div class="v">{type_counts.get("B", 0)}</div></div>
    <div class="stat"><div class="k">靶点 C</div><div class="v">{type_counts.get("C", 0)}</div></div>
    <div class="stat"><div class="k">通路 D</div><div class="v">{type_counts.get("D", 0)}</div></div>
  </div>
  <div class="note">
    <strong>肉桂（RG）：</strong>Degree = 0 源于上游数据缺口（TCMSP 有效成分为空等），不是「无药理作用」。详见 <code>肉桂_无靶点说明.txt</code>。
  </div>

  <h2 class="section-title">各部分 Top10 柱状图（配色差异）</h2>
  <div class="grid">
{charts_block}
  </div>

  <h2 class="section-title">完整网络分析大表</h2>
  <div class="toolbar">
    <input id="q" type="search" placeholder="搜索代号 / 化合物名 / 药名…" style="min-width:240px"/>
    <select id="typeFilter">
      <option value="">全部类型</option>
      <option value="A">药物 A</option>
      <option value="B">成分 B</option>
      <option value="C">靶点 C</option>
      <option value="D">通路 D</option>
    </select>
    <span id="count" style="color:var(--muted)"></span>
  </div>
  <div class="table-wrap">
    <table id="tbl"><thead></thead><tbody></tbody></table>
  </div>
  <footer>类型计数：<span id="typeCounts"></span> · 数据文件：网络图数据.csv</footer>
</div>
<script>
const ROWS = {table_json};
const TYPE_COUNTS = {type_json};
const COLS = {json.dumps(show_cols, ensure_ascii=False)};
document.getElementById('typeCounts').textContent = Object.entries(TYPE_COUNTS).map(([k,v]) => k + '=' + v).join(' · ');
const thead = document.querySelector('#tbl thead');
const tbody = document.querySelector('#tbl tbody');
let sortKey = 'Degree', sortAsc = false;
function renderHead() {{
  thead.innerHTML = '<tr>' + COLS.map(c => '<th data-k="'+c+'">'+c+'</th>').join('') + '</tr>';
  thead.querySelectorAll('th').forEach(th => {{
    th.onclick = () => {{
      const k = th.dataset.k;
      if (sortKey === k) sortAsc = !sortAsc;
      else {{ sortKey = k; sortAsc = (k === 'name' || k === 'type' || k === 'IsSingleNode'); }}
      renderBody();
    }};
  }});
}}
function filtered() {{
  const q = document.getElementById('q').value.trim().toLowerCase();
  const t = document.getElementById('typeFilter').value;
  return ROWS.filter(r => {{
    if (t && r.type !== t) return false;
    if (q && !(String(r.name).toLowerCase().includes(q) || String(r.display_name||'').toLowerCase().includes(q))) return false;
    return true;
  }}).sort((a,b) => {{
    const av=a[sortKey], bv=b[sortKey];
    if (typeof av === 'number' && typeof bv === 'number') return sortAsc ? av-bv : bv-av;
    return sortAsc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
  }});
}}
function renderBody() {{
  const rows = filtered();
  document.getElementById('count').textContent = '显示 ' + rows.length + ' / ' + ROWS.length;
  tbody.innerHTML = rows.map(r => '<tr>' + COLS.map(c => {{
    if (c === 'type') return '<td><span class="badge '+r[c]+'">'+r[c]+'</span></td>';
    return '<td>'+r[c]+'</td>';
  }}).join('') + '</tr>').join('');
}}
document.getElementById('q').oninput = renderBody;
document.getElementById('typeFilter').onchange = renderBody;
renderHead(); renderBody();
</script>
</body>
</html>
"""


def main():
    cleanup_old_top10()
    G, tmap = build_graph()
    df = analyze(G, tmap)
    compound_map, herb_map = load_display_maps()
    df = attach_display_names(df, compound_map, herb_map)
    # Cytoscape-compatible export keeps original columns only
    cyto_cols = [c for c in df.columns if c != "display_name"]
    out_csv = NET_DIR / "网络图数据.csv"
    df[cyto_cols].to_csv(out_csv, index=False, encoding="utf-8-sig")
    # optional companion with display names for reading
    df.to_csv(NET_DIR / "网络图数据_含显示名.csv", index=False, encoding="utf-8-sig")
    write_rg_note(df)
    out_html = NET_DIR / "网络分析报告.html"
    out_html.write_text(build_html(df), encoding="utf-8")
    n_mapped = int(((df["type"] == "B") & (df["display_name"] != df["name"])).sum())
    print("OK", out_csv)
    print("OK", out_html, "nodes", len(df), "compounds_named", n_mapped)


if __name__ == "__main__":
    main()
