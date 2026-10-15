# -*- coding: utf-8 -*-
"""构建昱阳项目·未补充口径基线分析报告（自包含 HTML + md）。不伪造富集图；真实图内嵌 base64。"""
import os, base64, io, sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

ARM = r'E:\RProject\昱阳项目\02_未补充口径_Baseline_STPonly'
OUT = r'E:\RProject\昱阳项目\01_分析报告_AnalysisReport\03_最终报告_FinalReport'
HTML_OUT = os.path.join(OUT, '02_未补充口径_基线分析报告_Baseline_STPonly.html')
MD_OUT = os.path.join(OUT, '02_未补充口径_基线分析报告_Baseline_STPonly.md')
MAXSIDE = 1800

def b64(path):
    im = Image.open(path)
    if im.mode in ('RGBA', 'P', 'LA'):
        im = im.convert('RGB')
    w, h = im.size
    if max(w, h) > MAXSIDE:
        s = MAXSIDE / max(w, h)
        im = im.resize((int(w * s), int(h * s)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format='JPEG', quality=82, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()

FIG = {
    'pca':    os.path.join(ARM, '01_差异分析与药靶断点_DEGandGate/03_图片文件_Figures/01_PCA质控_PcaQc.png'),
    'volcano':os.path.join(ARM, '01_差异分析与药靶断点_DEGandGate/03_图片文件_Figures/02_火山图_Volcano.png'),
    'heat':   os.path.join(ARM, '01_差异分析与药靶断点_DEGandGate/03_图片文件_Figures/03_差异基因热图_DegHeatmap.png'),
    'venn':   os.path.join(ARM, '03_富集与PPI_EnrichPPI/03_图片文件_Figures/05_韦恩图_DrugDisease_Venn.png'),
    'ppi':    os.path.join(ARM, '03_富集与PPI_EnrichPPI/03_图片文件_Figures/13_网络图_StringPPI_Degree_Network.png'),
    'aff':    os.path.join(ARM, '04_分子对接_Docking/03_图片文件_Figures/矩阵_结合能热图_DockingAffinityHeatmap.png'),
    'dbig':   os.path.join(ARM, '04_分子对接_Docking/03_图片文件_Figures/01_Alox15/big-01.png'),
    'dsurf':  os.path.join(ARM, '04_分子对接_Docking/03_图片文件_Figures/01_Alox15/surface-01.png'),
    'ddet':   os.path.join(ARM, '04_分子对接_Docking/03_图片文件_Figures/01_Alox15/图片/detail-01.png'),
}
IMG = {k: b64(v) for k, v in FIG.items()}

def fig(key, caption, width=None):
    st = f' style="width:{width}"' if width else ''
    return (f'<figure class="fig"><img src="{IMG[key]}"{st} alt="{caption}"/>'
            f'<figcaption>{caption}</figcaption></figure>')

CSS = """
:root{--ink:#1c2430;--muted:#5a6573;--line:#e6e2d9;--paper:#f4f1ea;--card:#fff;--accent:#5B8FA8;--ok:#6B8F71;--warn:#C17B7B;--bad:#b25b5b;--accent2:#8B7BA8}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:'Segoe UI','Source Han Sans SC','Noto Sans SC','Microsoft YaHei',Arial,sans-serif;line-height:1.7}
.wrap{max-width:1040px;margin:0 auto;padding:2.2rem 1.5rem 4.5rem}
header.hero{border-bottom:1px solid var(--line);padding-bottom:1.2rem}
.kicker{font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:700}
h1{font-size:1.75rem;margin:.35rem 0 .5rem;letter-spacing:-.02em;line-height:1.3}
.lead{color:var(--muted);font-size:1.02rem;margin:.2rem 0 0}
.pills{display:flex;flex-wrap:wrap;gap:.42rem;margin-top:.95rem}
.pill{padding:.16rem .7rem;border:1px solid var(--line);border-radius:999px;font-size:.78rem;background:var(--card)}
.pill.warn{border-color:#ead3d3;background:#fbf6f6;color:#7a4545}
.pill.ok{border-color:#c5d4c8;background:#f3f7f3;color:#3d5c42}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.75rem;margin:1.3rem 0 .3rem}
.kpi{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--accent);border-radius:9px;padding:.75rem .9rem}
.kpi b{display:block;font-size:1.35rem;font-variant-numeric:tabular-nums;line-height:1.2}
.kpi span{display:block;color:var(--muted);font-size:.78rem;margin-top:.15rem}
h2{font-size:1.28rem;margin:2.4rem 0 .5rem;padding-top:1.1rem;border-top:1px solid var(--line)}
h2 .no{color:var(--accent);font-weight:700;margin-right:.45rem}
h3{font-size:1.05rem;margin:1.4rem 0 .4rem}
p{margin:.55rem 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem 1.15rem;margin:1rem 0}
.callout{border-left:4px solid var(--warn);background:#fbf6f6;border-radius:0 8px 8px 0;padding:.85rem 1.1rem;margin:1rem 0}
.callout.bad{border-left-color:var(--bad)}
.callout.ok{border-left-color:var(--ok);background:#f3f7f3}
.callout .t{font-weight:700;margin-bottom:.25rem}
table{width:100%;border-collapse:collapse;margin:.9rem 0;font-size:.9rem;background:var(--card)}
th,td{border:1px solid var(--line);padding:.5rem .65rem;text-align:left;vertical-align:top}
th{background:#efeae1;font-weight:650}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tr:nth-child(even) td{background:#faf8f4}
figure.fig{margin:1.15rem 0;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.7rem}
figure.fig img{width:100%;display:block;border-radius:6px}
figcaption{color:var(--muted);font-size:.83rem;margin-top:.55rem;padding:0 .3rem}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media(max-width:720px){.grid2{grid-template-columns:1fr}}
code{background:#efeae1;padding:.08rem .32rem;border-radius:4px;font-size:.85em}
ul{margin:.55rem 0;padding-left:1.25rem}li{margin:.28rem 0}
footer{margin-top:3rem;padding-top:1.1rem;border-top:1px solid var(--line);color:var(--muted);font-size:.82rem}
.small{font-size:.83rem;color:var(--muted)}
"""

def sec(no, title, body):
    return f'<h2><span class="no">{no}</span>{title}</h2>\n{body}'

# ---------- Sections ----------
hero = f"""
<header class="hero">
  <div class="kicker">昱阳项目 · 未补充口径基线 · Baseline STP × DEG</div>
  <h1>槲皮素干预丙泊酚神经毒性：未补充口径（仅 SwissTargetPrediction × DEG）基线分析报告</h1>
  <p class="lead">保守"最小假设"口径：药物靶点仅取 SwissTargetPrediction（概率&gt;0，无实验补充），疾病侧仅取 GSE106799 差异基因。
  本报告如实呈现该口径结果，作为补充口径（多源药靶 × DEG∪CTD）的<strong>阴性对照</strong>。</p>
  <div class="pills">
    <span class="pill warn">口径：未补充 Baseline</span>
    <span class="pill">药靶：SwissTargetPrediction</span>
    <span class="pill">疾病：DEG 120</span>
    <span class="pill warn">交集：1（Alox15）</span>
    <span class="pill warn">富集：0 显著条目</span>
    <span class="pill ok">对接：ALOX15 −8.3</span>
    <span class="pill">MD：未执行（用户要求不做）</span>
  </div>
  <div class="kpis">
    <div class="kpi"><b>120</b><span>DEG（82↑ / 38↓，名义 P&lt;0.05）</span></div>
    <div class="kpi"><b>99 / 85</b><span>STP 药靶（人源 / 小鼠同源）</span></div>
    <div class="kpi"><b>1</b><span>药靶 ∩ DEG（Alox15）</span></div>
    <div class="kpi"><b>0</b><span>富集显著条目（FDR&lt;0.05）</span></div>
    <div class="kpi"><b>−8.3</b><span>对接亲和力 kcal/mol（ALOX15）</span></div>
  </div>
</header>
"""

s1 = sec('1', '口径定位与核心结论', f"""
<div class="callout bad"><div class="t">核心结论（诚实）</div>
未补充口径下，槲皮素 SwissTargetPrediction 预测靶点与丙泊酚差异基因的交集<strong>仅 1 个基因 Alox15</strong>；
DEG 无任何基因过 FDR&lt;0.05，功能富集（GO/KEGG）在 FDR&lt;0.05 <strong>无显著条目</strong>。
故本口径<strong>不足以支持</strong>"槲皮素经某通路干预丙泊酚神经毒性"的机制假说——它是一个<strong>阴性对照</strong>，
用以说明"仅靠 STP 预测靶点 + DEG 交集"证据不足，需多源补充。</div>
<p>本口径刻意保守：药靶仅取 SwissTargetPrediction（无实验/多源），疾病仅取 DEG（不含 CTD 补充）。
它回答的问题是——"在最小假设下，槲皮素与丙泊酚神经毒性能建立多强的可关联性？"答案是：关联性极弱。</p>
<div class="card small"><strong>为何需要补充口径：</strong>补充口径将药靶扩为（实验 ∪ 预测）、疾病扩为（DEG ∪ CTD）后，
交集升至 <strong>57</strong>，并筛到 Akt1/Bax/Casp3/Egfr 等注释良好的核心靶点，富集出凋亡/缺氧等强信号。
两口径对照，正说明本基线的证据缺口。</div>
""")

s2 = sec('2', '差异表达分析（GSE106799）', f"""
<p>数据来源：GEO <code>GSE106799</code>（平台 GPL24261，Affymetrix），丙泊酚神经毒性模型小鼠。
limma 差异分析，阈值 <strong>|logFC| ≥ 1 且 P.Value &lt; 0.05（名义 P）</strong>，得 DEG <strong>120</strong>（上调 82 / 下调 38）。</p>
<div class="callout"><div class="t">统计诚实性说明</div>
本 DEG 按<strong>名义 P&lt;0.05</strong>筛选（网药惯例）；<strong>无任何基因过 FDR&lt;0.05</strong>（adjP 0.15–0.79）。
且多数为 <code>Olfr/Vmn/Rik</code> 等注释稀疏的新基因。这是后续富集阴性的主因，特此明示，不加粉饰。</div>
<h3>差异基因代表</h3>
<table><thead><tr><th>方向</th><th>基因</th><th class="num">logFC</th><th class="num">P.Value</th><th class="num">adj.P.Val</th></tr></thead><tbody>
<tr><td rowspan="4">上调 Top</td><td>Cldn8</td><td class="num">+2.91</td><td class="num">6.1e-03</td><td class="num">0.556</td></tr>
<tr><td>1700008P02Rik</td><td class="num">+2.81</td><td class="num">3.3e-02</td><td class="num">0.745</td></tr>
<tr><td>Bbs10</td><td class="num">+2.59</td><td class="num">2.3e-02</td><td class="num">0.706</td></tr>
<tr><td>Prr23a</td><td class="num">+2.52</td><td class="num">1.9e-02</td><td class="num">0.679</td></tr>
<tr><td rowspan="4">下调 Top</td><td>Ddx3y</td><td class="num">−3.04</td><td class="num">4.7e-02</td><td class="num">0.793</td></tr>
<tr><td>Olig3</td><td class="num">−2.58</td><td class="num">1.3e-02</td><td class="num">0.623</td></tr>
<tr><td>Npas4</td><td class="num">−2.06</td><td class="num">8.7e-05</td><td class="num">0.332</td></tr>
<tr><td>Egr4</td><td class="num">−1.95</td><td class="num">8.7e-06</td><td class="num">0.155</td></tr>
</tbody></table>
<p class="small">注：Npas4 / Egr4 为神经活动即时早期基因，其下调具神经毒性相关性；但整体 DEG 仍偏弱（无 FDR 显著）。</p>
<div class="grid2">{fig('pca','图 1　PCA 质控：样本按处理分组聚类。')}{fig('volcano','图 2　火山图：红/蓝为上调/下调 DEG（|logFC|≥1 & P&lt;0.05）。')}</div>
{fig('heat','图 3　差异基因热图：DEG 表达模式（z-score）。')}
""")

s3 = sec('3', '药靶与交集断点', f"""
<p>药靶：槲皮素（Quercetin, CID 5280343）经 <strong>SwissTargetPrediction</strong>（Homo sapiens, Probability&gt;0）得 100 行→
<strong>99 个人源基因</strong>；小鼠同源映射 <strong>85</strong> 个。与 DEG(120) 取交集：</p>
<div class="callout bad"><div class="t">交集 = 1</div>
唯一交集基因 <strong>Alox15</strong>（人源 ALOX15，花生四烯酸 15-脂氧合酶），在 DEG 中<strong>上调</strong>（logFC +1.01，P=0.011）。
STP 仅预测靶点、覆盖有限；交集 1 表明"STP 口径"下槲皮素对丙泊酚转录响应的覆盖极低。</div>
{fig('venn','图 4　韦恩图：槲皮素 STP 药靶（小鼠 85）vs 丙泊酚 DEG（120），交集 1（Alox15）。','70%')}
<div class="card small">口径说明：STP 为<strong>计算预测</strong>靶点（非实验验证），其预测空间本身有限，
故交集极小既是真实的，也提示必须引入实验/多源靶点（见补充口径）。</div>
""")

s4 = sec('4', '功能富集（诚实阴性结果）', f"""
<p>因交集 &lt;15，按既定断点逻辑对<strong>全 DEG(120)</strong>做 ORA（GO BP/CC/MF + KEGG）。
基因映射：120 → 98 个 ENTREZID（映射率 81.7%），未映射者为 Gm*/Rik/Olfr 等新基因。</p>
<div class="callout bad"><div class="t">富集结果：FDR&lt;0.05 下 0 条显著</div>
GO BP / CC / MF 与 KEGG 在 FDR&lt;0.05 <strong>均无显著条目</strong>。放宽到 p.adj&lt;0.2 也仅零散不显著条目
（雌性性别分化、眼发育、肾小管分化、视黄醇代谢等，p.adj≈0.17），主题离散、与神经毒性<strong>不相干</strong>，无稳健功能信号。
<em>（诊断脚本 _diag_enrich.R 已核实：KEGG 注释在线加载成功，非联网失败；enrichGO 非报错——是真阴性。）</em></div>
<div class="callout"><div class="t">为何不作富集图</div>
0 显著条目下不绘制气泡/棒棒糖/圈图——<strong>不以噪声冒充机制</strong>。仅以上表说明阴性，符合诚实呈现原则。</div>
<div class="card small"><strong>阴性主因：</strong>① DEG 多为注释稀疏的新基因（Olfr/Vmn/Rik）；② DEG 本身无 FDR 显著基因，
统计上偏弱；③ 无药靶侧过滤（交集仅 1，无法像补充口径那样借 Akt1/Bax/Casp3 等富集出凋亡/缺氧）。</div>
""")

s5 = sec('5', 'PPI 网络（背景参考）', f"""
<p>因 overlap&lt;3，PPI 输入退化为 top50 DEG，经 STRING（小鼠 10090，score≥400）建网。
得到<strong>稀疏、低分</strong>互作网络（最高 degree 仅 3，Olfr961），非药靶-疾病核心网络。</p>
{fig('ppi','图 5　STRING PPI 度网络（top DEG）：节点大小/颜色示意度数；网络稀疏、低置信，仅作背景参考。')}
<div class="card small">诚实说明：该网络由 DEG 兜底（非交集靶点），互作分数低、连通稀疏，
不构成"关键靶点网络"，仅作差异基因背景关系参考。</div>
""")

s6 = sec('6', '分子对接（唯一交集靶点 ALOX15）', f"""
<p>对交集唯一基因 <strong>Alox15</strong>（ALOX15，PDB <code>1lox</code>）与槲皮素（CID 5280343）做分子对接。
AutoSite 自动选口袋（rank=1），box 尺寸上限 35 Å，Vina 打分，box_qc=PASS。</p>
<div class="callout ok"><div class="t">对接结果</div>
槲皮素 × ALOX15 结合能 <strong>−8.3 kcal/mol</strong>，提示可结合。</div>
<div class="grid2">{fig('dbig','图 6　ALOX15–槲皮素对接姿态（整体）。')}{fig('dsurf','图 7　ALOX15 表面口袋与配体（表面视图）。')}</div>
{fig('ddet','图 8　ALOX15 活性位点细节（关键残基与配体相互作用）。')}
{fig('aff','图 9　结合能矩阵热图：ALOX15–槲皮素 −8.3 kcal/mol。')}
<div class="callout"><div class="t">局限</div>
本口径仅 1 个靶点（交集=1），<strong>不足以支撑"多靶点"网络药理结论</strong>；仅代表槲皮素可结合 ALOX15。
结合能为打分函数估计，非亲和力金标准。按用户要求<strong>未做分子动力学（MD）</strong>。</div>
""")

s7 = sec('7', '解读、口径红线与口径对照', f"""
<h3>口径红线（必须遵守）</h3>
<ul>
<li>本口径为<strong>阴性/最小假设</strong>基线，<strong>不得</strong>据此得出"槲皮素经 X 通路干预丙泊酚神经毒性"的机制结论。</li>
<li>富集 0 显著、交集 1——这是真实且有意义的阴性结果，不得用放宽阈值/换基因集"造"出显著通路。</li>
<li>对接仅 ALOX15 单靶点，不等于多靶点药理；未做 MD，构象稳定性未验证。</li>
<li>结论只在"STP-only × DEG-only"口径内成立，不可外推到补充口径。</li>
</ul>
<h3>基线（未补充）vs 补充口径 对照</h3>
<table><thead><tr><th>维度</th><th>未补充口径（本报告）</th><th>补充口径（主线）</th></tr></thead><tbody>
<tr><td>药靶来源</td><td>仅 SwissTargetPrediction</td><td>实验 ∪ 预测（多源）</td></tr>
<tr><td>疾病来源</td><td>仅 DEG</td><td>DEG ∪ CTD</td></tr>
<tr><td>药靶数</td><td class="num">99 人 / 85 鼠</td><td class="num">549 人源并集</td></tr>
<tr><td>疾病数</td><td class="num">120</td><td class="num">298</td></tr>
<tr><td><strong>交集</strong></td><td class="num"><strong>1（Alox15）</strong></td><td class="num"><strong>57</strong></td></tr>
<tr><td>富集（FDR&lt;0.05）</td><td>0 条显著</td><td>凋亡/缺氧等强信号</td></tr>
<tr><td>对接</td><td>ALOX15（1 靶点）</td><td>AKT1/EGFR/SRC/GSK3B/HIF1A（5 靶点）</td></tr>
<tr><td>MD</td><td>未执行</td><td>执行中</td></tr>
<tr><td>定位</td><td><strong>阴性对照</strong></td><td>主分析</td></tr>
</tbody></table>
""")

s8 = sec('8', '口径审计表（可溯源）', """
<table><thead><tr><th>项目</th><th>值</th><th>来源脚本/文件</th></tr></thead><tbody>
<tr><td>DEG 数</td><td class="num">120（82↑/38↓）</td><td>01 模块 05_差异基因_DEG_mainThreshold.csv</td></tr>
<tr><td>DEG 阈值</td><td>|logFC|≥1 &amp; P&lt;0.05（名义）</td><td>02_GSE106799差异分析_RunDEG.R</td></tr>
<tr><td>DEG 过 FDR&lt;0.05</td><td class="num">0</td><td>04_全基因差异_AllGenes_limma.csv</td></tr>
<tr><td>STP 药靶</td><td class="num">99 人 / 85 鼠</td><td>05_从STP生成基因列表…StpGenesAndGate.R</td></tr>
<tr><td>交集</td><td class="num">1（Alox15）</td><td>09_药靶与DEG交集_QuercetinDegOverlap.csv</td></tr>
<tr><td>ORA 输入</td><td>Full_DEG 120（映射 98）</td><td>03 模块 01_一轮富集与PPI_EnrichAndPPI.R</td></tr>
<tr><td>富集显著项</td><td class="num">0（FDR&lt;0.05）</td><td>02_GO_BP.csv / 04_KEGG.csv（=no_significant_terms）</td></tr>
<tr><td>富集核实</td><td>真阴性（非报错/非离线）</td><td>_diag_enrich.R</td></tr>
<tr><td>对接</td><td>ALOX15 −8.3 kcal/mol</td><td>04 模块 03_summary_vina.csv</td></tr>
</tbody></table>
<p class="small">生成脚本：<code>04_基线报告_buildBaselineReport.py</code>（本文件同目录）。图为项目真实产物内嵌，无外部引用。</p>
""")

body = (hero + s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 +
        '<footer>昱阳项目 · 未补充口径基线分析报告 · 生成于 2026-10-15 · '
        '口径：SwissTargetPrediction × DEG（阴性对照）· 未做 MD<br>'
        '本报告为自包含 HTML，图片已内嵌，可直接分享源文件。</footer>')

html = ("<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'/>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'/>"
        "<title>昱阳项目·未补充口径基线分析报告（STP×DEG）</title>"
        f"<style>{CSS}</style></head><body><div class='wrap'>{body}</div></body></html>")
with open(HTML_OUT, 'w', encoding='utf-8') as f:
    f.write(html)

# ---- markdown draft ----
md = """# 昱阳项目 · 未补充口径基线分析报告（SwissTargetPrediction × DEG）

> 保守"最小假设"口径，作为补充口径（多源）之**阴性对照**。未做 MD。

## 1. 核心结论（诚实）
- 药靶 ∩ DEG = **1**（Alox15）；DEG 无基因过 FDR<0.05；GO/KEGG 富集在 FDR<0.05 **0 条显著**。
- 本口径**不足以支持**"槲皮素经某通路干预丙泊酚神经毒性"的机制假说——它是**阴性对照**。
- 意义：说明"仅 STP 靶点 + DEG 交集"证据不足，需多源补充（→ 补充口径交集 57、富集凋亡/缺氧）。

## 2. 差异表达（GSE106799）
- 阈值 |logFC|≥1 & P<0.05（名义），DEG 120（82↑/38↓）。**无基因过 FDR<0.05**（adjP 0.15–0.79）。
- 上调 Top：Cldn8 +2.91、1700008P02Rik +2.81、Bbs10 +2.59；下调 Top：Ddx3y −3.04、Olig3 −2.58、Npas4 −2.06、Egr4 −1.95。
- Npas4/Egr4（神经活动即时早期基因）下调，具神经毒性相关性；但整体偏弱。
- 图：PCA、火山、热图。

## 3. 药靶与交集断点
- STP 槲皮素（Prob>0）：99 人源 / 85 小鼠同源。∩ DEG = **1（Alox15，上调 +1.01，P=0.011）**。
- 图：韦恩（Drug 85 vs DEG 120，交集 1）。

## 4. 功能富集（诚实阴性）
- ORA 输入 Full_DEG 120（映射 98 ENTREZID，81.7%）。GO BP/CC/MF + KEGG 在 FDR<0.05 **0 条显著**。
- 放宽 p.adj<0.2 仅零散不显著条目（性别分化/眼发育/肾小管/视黄醇代谢，p.adj≈0.17），与神经毒性不相干。
- **不作富集图**（不以噪声冒充机制）。诊断核实：真阴性，非报错/非离线（_diag_enrich.R）。
- 阴性主因：DEG 多为 Olfr/Vmn/Rik 新基因、无 FDR 显著、无药靶侧过滤。

## 5. PPI（背景参考）
- overlap<3 → top50 DEG 建 STRING 网；稀疏低分（最高 degree 3，Olfr961），非核心网络。

## 6. 分子对接（ALOX15）
- Alox15（1lox）× 槲皮素，AutoSite pocket，Vina，**−8.3 kcal/mol**。图：big/surface/detail + 结合能热图。
- 仅 1 靶点，不足以支撑多靶点结论；未做 MD。

## 7. 口径红线
- 不得据此得出机制结论；不得用放宽阈值造显著通路；单靶点≠多靶点药理；未 MD；结论不外推。

## 8. 基线 vs 补充口径
| 维度 | 未补充（本报告） | 补充（主线） |
|---|---|---|
| 药靶 | 仅 STP | 实验∪预测 |
| 疾病 | 仅 DEG | DEG∪CTD |
| 交集 | **1（Alox15）** | **57** |
| 富集 | 0 显著 | 凋亡/缺氧强信号 |
| 对接 | ALOX15（1） | AKT1/EGFR/SRC/GSK3B/HIF1A（5） |
| MD | 未执行 | 执行中 |
| 定位 | **阴性对照** | 主分析 |

---
生成脚本：`04_基线报告_buildBaselineReport.py`。图为项目真实产物。
"""
with open(MD_OUT, 'w', encoding='utf-8') as f:
    f.write(md)

print('HTML:', HTML_OUT, os.path.getsize(HTML_OUT) // 1024, 'KB')
print('MD  :', MD_OUT, os.path.getsize(MD_OUT) // 1024, 'KB')
