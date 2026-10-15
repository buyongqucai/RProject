# -*- coding: utf-8 -*-
"""Final report HTML aligned with DeliveryStandards SampleReportParadigm CSS tokens."""
from pathlib import Path
from datetime import datetime

OUT = Path(__file__).resolve().parent / "01_最终分析报告_FinalReport.html"
# Figures live in track-B delivery; relative from FinalReport/
FIG = "../../../交付文件/图片"
DELIVERY_HTML = "../../../交付文件/图注与解读说明.html"
STATS = "../../../交付文件/报告/_stats.json"
NET = "../../../交付文件/数据/网络图/网络分析报告.html"

css = """
:root{--ink:#1c2430;--muted:#5a6573;--line:#e6e2d9;--paper:#f4f1ea;--card:#fff;
--accent:#5B8FA8;--ok:#6B8F71;--warn:#C17B7B;--accent2:#8B7BA8;--accent3:#D4A574}
*{box-sizing:border-box}html{font-size:16px}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:'Segoe UI','Source Han Sans SC','Noto Sans SC','Microsoft YaHei',Arial,sans-serif;line-height:1.65}
.wrap{max-width:1100px;margin:0 auto;padding:2rem 1.4rem 4rem}
header.hero{padding:0 0 1.15rem;border-bottom:1px solid var(--line)}
.kicker{font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);font-weight:650;margin:0 0 .35rem}
h1{font-size:1.45rem;font-weight:650;margin:0 0 .45rem;letter-spacing:-.02em;line-height:1.35}
.lead{color:var(--muted);font-size:.98rem;margin:.2rem 0 0}
.pills{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.85rem}
.pill{display:inline-block;padding:.12rem .65rem;border:1px solid var(--line);border-radius:999px;font-size:.78rem;background:var(--card)}
.pill.ok{border-color:#c5d4c8;background:#f3f7f3;color:#3d5c42}
.pill.warn{border-color:#ead3d3;background:#fbf6f6;color:#7a4545}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:.7rem;margin:1.2rem 0 0}
.kpi{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--accent);border-radius:8px;padding:.7rem .85rem}
.kpi b{display:block;font-size:1.12rem;font-variant-numeric:tabular-nums;font-weight:650}
.kpi span{display:block;color:var(--muted);font-size:.75rem;margin-top:.15rem}
nav.toc{margin:1.2rem 0;padding:.85rem 1rem;background:var(--card);border:1px solid var(--line);border-radius:8px;font-size:.9rem}
nav.toc a{color:var(--accent);text-decoration:none;margin-right:1.05rem}
h2{font-size:1.18rem;margin:2rem 0 .7rem;padding-bottom:.35rem;border-bottom:2px solid var(--accent);font-weight:650}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:1rem 1.1rem;margin:.75rem 0}
.callout{background:#fbf6f6;border:1px solid #ead3d3;border-left:4px solid var(--warn);border-radius:8px;padding:.85rem 1rem;margin:1rem 0}
table{width:100%;border-collapse:collapse;font-size:.9rem;margin:.5rem 0}
th,td{border:1px solid var(--line);padding:.45rem .55rem;text-align:left;vertical-align:top}
th{background:#f7f5f0;font-weight:650}
.fig-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem}
.fig-card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.75rem}
.fig-card img{width:100%;height:auto;border:1px solid var(--line);border-radius:4px;background:#fff}
.fig-card h3{font-size:.92rem;margin:.2rem 0 .5rem}
.caption{color:var(--muted);font-size:.82rem;margin:.4rem 0 0}
footer.foot{margin-top:2.5rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--muted);font-size:.82rem}
ul.tight li{margin:.25rem 0}
a.btn{display:inline-block;margin:.35rem .5rem .35rem 0;padding:.35rem .75rem;background:var(--accent);color:#fff;border-radius:6px;text-decoration:none;font-size:.88rem}
"""

now = datetime.now().strftime("%Y-%m-%d %H:%M")

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>清风项目 · IPF 网络药理学计算预测报告</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
<header class="hero">
  <p class="kicker">Network Pharmacology · DeliveryStandards report</p>
  <h1>水蛭宣痹化纤汤干预特发性肺纤维化（IPF）的潜在机制<br/>网络药理学计算预测报告</h1>
  <p class="lead">in silico 假说生成 · 非临床试验 / 非诊疗建议 · 审核稿 v2026-10-16</p>
  <div class="pills">
    <span class="pill ok">STATUS: COMPLETE</span>
    <span class="pill ok">data_provenance: REAL</span>
    <span class="pill warn">对接未启动</span>
    <span class="pill">9 味药 · IPF</span>
  </div>
  <div class="kpis">
    <div class="kpi"><b>4,269</b><span>疾病下游并集</span></div>
    <div class="kpi"><b>244</b><span>药物靶点并集</span></div>
    <div class="kpi"><b>197</b><span>药病交集</span></div>
    <div class="kpi"><b>385 / 2,571</b><span>HCTP 节点 / 边</span></div>
    <div class="kpi"><b>173 / 687</b><span>PPI≥900 节点 / 边</span></div>
    <div class="kpi"><b>193</b><span>KEGG 通路项</span></div>
  </div>
</header>

<nav class="toc">
  <strong>目录</strong>
  <a href="#sec-q">科学问题</a>
  <a href="#sec-method">方法</a>
  <a href="#sec-data">数据</a>
  <a href="#sec-res">结果</a>
  <a href="#sec-fig">图示</a>
  <a href="#sec-interp">解读</a>
  <a href="#sec-caveat">局限</a>
</nav>

<div class="callout">
  <strong>表述约束：</strong>禁止写成「治疗 IPF」。本报告仅描述计算预测的潜在机制假说。
  客户图文入口请打开
  <a href="{DELIVERY_HTML}">交付文件/图注与解读说明.html</a>
  （统计 JSON：<a href="{STATS}">_stats.json</a>；网络分析：<a href="{NET}">网络分析报告.html</a>）。
</div>

<h2 id="sec-q">1. 科学问题与范围</h2>
<div class="card">
  <p><strong>组方：</strong>水蛭、旋覆花、川芎、桃仁、浙贝母、蜜麻黄、紫苏子、黄芪、甘草（9 味）。</p>
  <p><strong>疾病：</strong>Idiopathic pulmonary fibrosis（IPF；MeSH D054990）。</p>
  <p>构建成分–靶点与疾病基因交集及 HCTP 网络，完成 GO/KEGG 与 STRING PPI，输出标准图册与轨 B 交付包。</p>
  <p><strong>未纳入本版：</strong>分子对接 / MD。</p>
</div>

<h2 id="sec-method">2. 方法</h2>
<div class="card">
  <ul class="tight">
    <li>疾病 5 库双口径（韦恩全量 vs 下游 GeneCards≥40 ∪ CTD curated ∪ OMIM ∪ TTD ∪ DrugBank）。</li>
    <li>药物瀑布：8 味 TCMSP（OB≥30%、DL≥0.18）；水蛭 BATMAN <strong>仅 known</strong>（按药 API + 归属审计）。</li>
    <li>交集 → HCTP → GO/KEGG ORA → STRING（score≥900）。</li>
    <li>出图：网药 FROZEN 01–15 + 高级 16–19 + KEGG 官方 Top20；DeliveryStandards 命名。</li>
  </ul>
  <p><small>sourced：VizStandards · DeliveryStandards · NetworkPharmacology 脚本 01–09</small></p>
</div>

<h2 id="sec-data">3. 数据来源</h2>
<div class="card">
<table>
<thead><tr><th>来源</th><th>要点</th></tr></thead>
<tbody>
<tr><td>GeneCards / CTD / OMIM / TTD / DrugBank</td><td>用户导出；COPD、CCL12 已脚注剔除</td></tr>
<tr><td>DisGeNET</td><td>登录墙，未纳入</td></tr>
<tr><td>TCMSP</td><td>raw 在 <code>02_药物靶点/.../01_TCMSP_…</code></td></tr>
<tr><td>BATMAN-TCM 2.0</td><td>按药实时 API（非全库 browse）；known only</td></tr>
<tr><td>STRING v12</td><td>REST；≥900 主 PPI</td></tr>
</tbody>
</table>
</div>

<h2 id="sec-res">4. 关键结果</h2>
<div class="card">
  <ul class="tight">
    <li>药病交集 <strong>197</strong> = 244 ∩ 4,269（占药靶 80.7%）。</li>
    <li>单药∩疾病：甘草 166、蜜麻黄 165、黄芪 150、旋覆花 148、紫苏子 98、浙贝母 36、桃仁 32、川芎 23、水蛭 6。</li>
    <li>HCTP 枢纽 Degree：PTGS2 136、槲皮素（same15）121、HSP90AA1 96、ESR1 89 等。</li>
    <li>KEGG Top 含 hsa05417 / hsa05418 / AGE-RAGE 等；感染与肿瘤通路名称为共享模块富集，不作病因结论。</li>
  </ul>
</div>

<h2 id="sec-fig">5. 代表图（相对路径）</h2>
<p><a class="btn" href="{DELIVERY_HTML}">打开完整图注报告</a></p>
<div class="fig-grid">
  <article class="fig-card">
    <h3>01 疾病靶点韦恩（5 库）</h3>
    <img src="{FIG}/韦恩图/疾病数据库可视化韦恩图.png" alt="Disease Venn"/>
    <p class="caption">全量口径韦恩；下游过滤数字见 KPI。</p>
  </article>
  <article class="fig-card">
    <h3>02 药病交集韦恩</h3>
    <img src="{FIG}/韦恩图/疾病药物交集韦恩图.png" alt="Drug-disease Venn"/>
    <p class="caption">药物靶点 ∩ 疾病下游并集 = 197。</p>
  </article>
  <article class="fig-card">
    <h3>11 HCTP 列状网络</h3>
    <img src="{FIG}/网络图/药物有效成分疾病靶点通路网络图.png" alt="HCTP columns"/>
    <p class="caption">A 药 / B 成分 / C 靶 / D 通路。</p>
  </article>
  <article class="fig-card">
    <h3>14 PPI（STRING≥900）</h3>
    <img src="{FIG}/PPI/PPI渐变图.png" alt="PPI concentric"/>
    <p class="caption">173 节点 · 687 边。</p>
  </article>
</div>

<h2 id="sec-interp">6. 结果解读</h2>
<div class="card">
  <ul class="tight">
    <li>高重叠率支持「方剂靶点空间与 IPF 基因空间可计算相交」的假说，不等于疗效。</li>
    <li>枢纽与富集提示炎症 / 应激 / 凋亡模块；请对照 IPF 文献（TGF-β、成纤维、EMT、肺血管），勿直接采用动脉粥样硬化或肿瘤通路病名。</li>
    <li>水蛭仅 known 进入主网；凝血相关交集基因为交叉假说线索。</li>
  </ul>
  <p><strong>未证明：</strong>临床疗效、剂量、安全性、因果靶点。</p>
</div>

<h2 id="sec-caveat">7. 局限</h2>
<div class="card">
  <ul class="tight">
    <li>无湿实验、无对接。</li>
    <li>BATMAN「全库 browse + 按药筛」路径在技能中标为<strong>待验证</strong>；清风未使用。</li>
    <li>KEGG 官方图按条款仅限学术用途。</li>
  </ul>
</div>

<footer class="foot">
生成时间：{now} · 报告规范：统一交付规范_DeliveryStandards · 出图规范：统一可视化规范_VizStandards · 领域：网络药理学_NetworkPharmacology · 版本 v2026-10-16 审核稿
</footer>
</div>
</body>
</html>
"""

OUT.write_text(html, encoding="utf-8")
print("wrote", OUT)
