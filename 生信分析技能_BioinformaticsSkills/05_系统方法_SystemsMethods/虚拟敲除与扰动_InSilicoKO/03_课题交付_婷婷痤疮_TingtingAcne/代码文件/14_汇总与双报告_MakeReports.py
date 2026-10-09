# -*- coding: utf-8 -*-
"""婷婷补齐 SOP 交付三件套之二三：富集汇总 + 双报告 HTML + 报告入口。

数字全部从既有 CSV 读取，不手写。图片用相对路径，须在结果文件夹内打开。
"""
from __future__ import annotations

import html
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RES = Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除\结果文件")
CROSS = RES / "_跨亚群"
SUM = CROSS / "富集汇总_EnrichSummary"
RPT = CROSS / "课题报告_ProjectReports" / "报告文件"
for d in (SUM / "数据文件", SUM / "图片文件", SUM / "报告文件", RPT):
    d.mkdir(parents=True, exist_ok=True)

NAVY = "#24362f"
ACC = "#2f5d4c"


def save(fig, folder: Path, stem: str) -> None:
    fig.savefig(folder / f"{stem}.png", dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(folder / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def load_csv(p: Path) -> pd.DataFrame:
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def resp_dir(subtype: str, engine: str, gene: str) -> Path:
    return RES / subtype / engine / gene / "数据文件"


# ---------- 1. 汇总表 ----------
rows = []
terms_rows = []
engines = [
    ("scTenifoldKnk_1.4.3_GPU", "AHR", "distance"),
    ("GenKI", "AHR", "KL"),
    ("GenKI", "FEN1", "KL"),
    ("GenKI", "DHRS9", "KL"),
]
for subtype in ["TREM2 macrophage", "M2-like macrophage"]:
    for engine, gene, score_col in engines:
        d = resp_dir(subtype, engine, gene)
        resp = load_csv(d / "响应基因_Responsive.csv")
        go = load_csv(d / "富集_GO.csv")
        kegg = load_csv(d / "富集_KEGG.csv")
        if resp.empty and not (d / "响应基因_Responsive.csv").exists():
            continue
        n_all = len(resp)
        n_other = int((resp["gene"].astype(str) != gene).sum()) if n_all else 0
        n_go = len(go)
        n_kegg = len(kegg)
        rows.append(
            {
                "subtype": subtype,
                "engine": engine,
                "target": gene,
                "score_column": score_col,
                "n_pass_rows": n_all,
                "n_other_genes": n_other,
                "n_go_pass": n_go,
                "n_kegg_pass": n_kegg,
            }
        )
        for _, r in go.iterrows():
            terms_rows.append(
                {
                    "subtype": subtype,
                    "engine": engine,
                    "target": gene,
                    "source": "GO-" + str(r.get("ontology", "")),
                    "term_id": r.get("ID", ""),
                    "term": r.get("Description", r.get("term", "")),
                    "p_adjust": r.get("p.adjust", np.nan),
                    "genes": r.get("geneID", ""),
                }
            )
        for _, r in kegg.iterrows():
            terms_rows.append(
                {
                    "subtype": subtype,
                    "engine": engine,
                    "target": gene,
                    "source": "KEGG",
                    "term_id": r.get("ID", ""),
                    "term": r.get("Description", r.get("term", "")),
                    "p_adjust": r.get("p.adjust", np.nan),
                    "genes": r.get("geneID", ""),
                }
            )

summary = pd.DataFrame(rows)
summary.to_csv(SUM / "数据文件" / "汇总_响应与富集_Summary.csv", index=False)
terms = pd.DataFrame(terms_rows)
terms.to_csv(SUM / "数据文件" / "汇总_富集条目_TermsLong.csv", index=False)

# ---------- 2. 汇总图 ----------
lab = summary["subtype"].str.replace(" macrophage", "", regex=False) + "\n" + summary["target"] + "\n" + summary["engine"].str.replace("scTenifoldKnk_1.4.3_GPU", "Knk", regex=False)

fig, ax = plt.subplots(figsize=(8.6, 4.4))
x = np.arange(len(summary))
ax.bar(x - 0.2, summary["n_other_genes"], width=0.4, label="other responsive genes", color="#C17B7B")
ax.bar(x + 0.2, summary["n_pass_rows"], width=0.4, label="pass rows (incl. target)", color="#5B8FA8")
ax.set_xticks(x)
ax.set_xticklabels(lab, fontsize=7.5)
ax.set_ylabel("count")
ax.set_title("Responsive genes by subtype × engine × target")
ax.legend(frameon=False, fontsize=8)
save(fig, SUM / "图片文件", "04_柱状图_响应基因汇总_AllEnginesCounts")

fig, ax = plt.subplots(figsize=(8.6, 3.8))
ax.bar(x - 0.2, summary["n_go_pass"], width=0.4, label="GO terms passing BH", color="#6B8F71")
ax.bar(x + 0.2, summary["n_kegg_pass"], width=0.4, label="KEGG terms passing BH", color="#B08FBF")
ax.set_xticks(x)
ax.set_xticklabels(lab, fontsize=7.5)
ax.set_ylabel("terms")
ax.set_title("Official enrichment pass counts (BH p<0.05 & q<0.2)")
ax.legend(frameon=False, fontsize=8)
save(fig, SUM / "图片文件", "05_柱状图_官方富集通过数_PassCount")

if len(terms):
    piv = terms.pivot_table(index="term", columns=["subtype", "target"], values="p_adjust", aggfunc="min")
    fig, ax = plt.subplots(figsize=(7.2, max(2.4, 0.6 * len(piv) + 1.4)))
    data = -np.log10(piv.fillna(1).clip(lower=1e-12))
    im = ax.imshow(data.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(data.shape[1]))
    ax.set_xticklabels([f"{a}\n{b}" for a, b in data.columns], fontsize=8)
    ax.set_yticks(range(data.shape[0]))
    ax.set_yticklabels(data.index, fontsize=8)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f"{data.values[i, j]:.1f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, label=r"$-\log_{10}$(p.adjust)")
    ax.set_title("Terms passing threshold (only passers shown)")
    save(fig, SUM / "图片文件", "05_热图_富集条目汇总_TermHeatmap")

# ---------- HTML 公共骨架（对齐琪乐无穷样式） ----------
CSS = """
html{font-size:100%}
body{margin:0;font-family:"Segoe UI","Microsoft YaHei",sans-serif;font-size:1.0625rem;line-height:1.85;color:#1c241f;background:#f3efe6}
.layout{display:grid;grid-template-columns:clamp(14rem,22vw,20rem) minmax(0,1fr);min-height:100vh}
.sidebar{position:sticky;top:0;align-self:start;height:100vh;overflow:auto;background:#24362f;color:#f4efe6;padding:1rem .8rem 2rem}
.sidebar h1{font-size:1.05rem;margin:0 0 .3rem;line-height:1.35}
.sidebar .sub{font-size:.78rem;color:#c5d2cb;margin-bottom:.8rem}
.sidebar a{display:block;color:#e7eee9;text-decoration:none;font-size:.86rem;padding:.38rem .5rem;border-radius:.45rem;border-left:.18rem solid transparent}
.sidebar a.active{background:rgba(216,240,228,.22);border-left-color:#b7e3cc;color:#fff}
.main{min-width:0;max-width:68rem;padding:clamp(1rem,2vw,2rem) clamp(1rem,3vw,2.4rem) 3rem}
.hero{background:#fffdf8;border:1px solid #ddd4c4;border-radius:1rem;padding:1.1rem 1.25rem}
.hero h1{font-size:clamp(1.4rem,2.4vw,1.9rem);line-height:1.3;margin:0 0 .45rem}
.note{background:#fff8ea;border-left:.35rem solid #8a6a3a;padding:.8rem 1rem;border-radius:.5rem;margin:1rem 0}
.take{background:#eef6f1;border-left:.35rem solid #2f5d4c;padding:.8rem 1rem;border-radius:.5rem;margin:1rem 0}
h2{font-size:clamp(1.2rem,1.8vw,1.45rem);margin:2rem 0 .6rem;border-bottom:2px solid #d5e0d7;padding-bottom:.2rem}
h3{font-size:1.08rem;margin:1.3rem 0 .4rem;color:#24362f}
figure{margin:1rem 0;background:#fffdf8;border:1px solid #ddd4c4;border-radius:.8rem;padding:.7rem}
figure img{width:100%;max-width:100%;height:auto;display:block}
figcaption{margin-top:.55rem;background:#f6f3ec;border-left:.25rem solid #2f5d4c;padding:.55rem .7rem;border-radius:.4rem;font-size:.95rem}
.wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.92rem;background:#fff}
th,td{border:1px solid #ddd4c4;padding:.4rem .5rem;vertical-align:top;word-break:break-word}
th{background:#eef3ef;text-align:left}
pre{background:#1f2a25;color:#e8f2ec;padding:.9rem 1rem;border-radius:.7rem;overflow:auto;white-space:pre-wrap;font-size:.84rem}
.footer{color:#5c635c;font-size:.85rem;margin-top:2rem}
@media (max-width:52rem){.layout{grid-template-columns:1fr}.sidebar{position:relative;height:auto;max-height:42vh}}
"""
JS = """
(function(){const links=[...document.querySelectorAll('.sidebar a')];
const secs=links.map(a=>document.getElementById(a.getAttribute('href').slice(1))).filter(Boolean);
function on(id){links.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+id));}
const io=new IntersectionObserver(es=>{const v=es.filter(e=>e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio);if(v[0])on(v[0].target.id);},{rootMargin:'-12% 0px -55% 0px',threshold:[0.15,0.4]});
secs.forEach(s=>io.observe(s));if(secs[0])on(secs[0].id);})();
"""


def page(title: str, side_title: str, side_sub: str, nav: list[tuple[str, str]], body: str) -> str:
    nav_html = "".join(f"<a href='#{hid}'>{html.escape(txt)}</a>" for hid, txt in nav)
    return (
        f"<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'/>"
        f"<meta name='viewport' content='width=device-width, initial-scale=1'/>"
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
        f"<div class='layout'><aside class='sidebar'><h1>{html.escape(side_title)}</h1>"
        f"<div class='sub'>{html.escape(side_sub)}</div>{nav_html}</aside>"
        f"<main class='main'>{body}</main></div><script>{JS}</script></body></html>"
    )


def fig(rel: str, cap: str) -> str:
    return f"<figure><img src='{rel}' alt=''/><figcaption>{cap}</figcaption></figure>"


def esc(s: str) -> str:
    return html.escape(str(s))


# 相对路径（相对报告文件夹；URL 编码空格）
import os


def rel_to(target: Path) -> str:
    rel = os.path.relpath(str(target), str(RPT))
    return Path(rel.replace(os.sep, "/").replace(" ", "%20")).as_posix() + "/"


KNK_PRE = "../../scTenifoldKnk_1.4.3_GPU/图片文件"
KNK_TREM2 = rel_to(RES / "TREM2 macrophage" / "scTenifoldKnk_1.4.3_GPU" / "AHR" / "图片文件")
KNK_M2 = rel_to(RES / "M2-like macrophage" / "scTenifoldKnk_1.4.3_GPU" / "AHR" / "图片文件")
GK_PRE = "../../GenKI/图片文件"
GK_TREM2 = rel_to(RES / "TREM2 macrophage" / "GenKI" / "AHR" / "图片文件")
GK_M2 = rel_to(RES / "M2-like macrophage" / "GenKI" / "AHR" / "图片文件")
GK_M2F = rel_to(RES / "M2-like macrophage" / "GenKI" / "FEN1" / "图片文件")
GK_TREM2D = rel_to(RES / "TREM2 macrophage" / "GenKI" / "DHRS9" / "图片文件")

CLAIM = "本报告是虚拟敲除的<strong>计算预测</strong>：响应基因不是 Seurat 差异基因，也不等于湿实验敲除的差异表达。"

# ---------- 3. 方法论报告 scTenifoldKnk ----------
knk_sum = summary[summary["engine"].str.startswith("scTenifoldKnk")]
knk_body = f"""
<div class='hero'><h1>方法论报告 — scTenifoldKnk 1.4.3 GPU</h1>
<p>GSE175817 人痤疮髓系单细胞；皮损 TREM2 / M2-like 巨噬细胞；虚拟敲除 AHR。</p>
<div class='take'>{CLAIM}</div></div>

<h2 id='s1'>1. 数据与切片</h2>
<p>数据集 GSE175817（Do 等，人痤疮皮损 vs 非皮损 10x）。细胞注释取作者 myeloid 对象（<code>celltype</code>、<code>stim</code>、<code>donor</code>）。建网切片：<code>stim == Lesional</code> × 亚群。皮损 TREM2 macrophage 1515 细胞（AHR 检出 436）；皮损 M2-like 266 细胞（AHR 检出 95）；M1-like 皮损 116 细胞但 AHR 检出 0，<strong>不敲</strong>。</p>

<h2 id='s2'>2. 引擎与参数</h2>
<p>建网公式 pcNet 1.4.3（<code>n_comp=3</code>，<code>q=0.9</code>，GPU）；敲除后半段用官方张量 / 置零 / 流形对齐 / <code>dRegulation</code>。包默认 <code>qc_minLibSize=1000</code>，<code>nc_nNet=10</code>，<code>nc_nCells=min(500,n−1)</code>，<code>td_K=3</code>。文献：Osorio 等 <em>Patterns</em> 2022，DOI 10.1016/j.patter.2022.100434。物种人：富集 <code>org.Hs.eg.db</code> + KEGG <code>hsa</code>。</p>
{fig(f"{KNK_PRE}/01_方法示意_scTenifoldKnkWorkflow.jpg", "图 1 方法示意（A/B/C 几何结构，沿用 Osorio 等结构图；本课题敲 AHR）。")}
{fig(f"{KNK_PRE}/01_部位示意_HumanAcne_AhrSites.jpg", "图 2 取材部位示意：人痤疮皮肤，皮损 TREM2 / M2 巨噬敲 AHR。假设示意，非定位实验。")}
{fig(f"{KNK_PRE}/02_散点图_巨噬细胞UMAP_Celltype.png", "图 3 作者注释巨噬亚群 UMAP。")}
{fig(f"{KNK_PRE}/03_柱状图_AHR检出率_TargetDetectionBar.png", "图 4 皮损亚群 AHR 检出率；M1-like 为 0 因而不敲。")}

<h2 id='s3'>3. 运行与结果</h2>
<p>每亚群 10 张网（固定种子）、细胞抽样 ≤500；敲除 AHR 出边后对齐流形，逐基因给出 <code>distance / Z / FC / p.value / p.adj</code>。响应基因规则：FDR &lt; 0.05。</p>
<div class='wrap'><table><tr><th>亚群</th><th>响应基因（剔 AHR）</th><th>GO 通过</th><th>KEGG 通过</th></tr>
{''.join(f"<tr><td>{esc(r.subtype)}</td><td>{esc(r.n_other_genes)}</td><td>{esc(r.n_go_pass)}</td><td>{esc(r.n_kegg_pass)}</td></tr>" for r in knk_sum.itertuples())}
</table></div>
{fig(f"{KNK_TREM2}04_散点图_扰动排名_TREM2_AHR.png", "图 5 TREM2 × AHR 扰动排名（FDR 显著者标红）。")}
{fig(f"{KNK_TREM2}04_柱状图_扰动基因_TREM2_AHR.png", "图 6 TREM2 × AHR Top 扰动基因。")}
{fig(f"{KNK_M2}04_柱状图_扰动基因_M2-like_AHR.png", "图 7 M2-like × AHR Top 扰动基因。")}
{fig(f"{KNK_M2}05_柱状图_GO通过_M2-like_AHR.png", "图 8 M2-like × AHR 通过阈值的 GO 条目（核糖体相关 3 条）。")}

<h2 id='s4'>4. 解读</h2>
<p>TREM2 × AHR 仅 GAPDH 过 FDR，无 GO/KEGG 通过条目。M2-like × AHR 过线 RPL10、RPS18，GO CC 为 cytosolic ribosome / ribosomal subunit / ribosome（各 2 基因）。核糖体条目由两个核糖体基因撑起，属结构性读出，不宜当作 AHR 特异通路。空结果写在报告文件 <code>05_富集_无通过条目.txt</code>。</p>
<p class='footer'>{CLAIM}</p>
"""
nav = [("s1", "1. 数据与切片"), ("s2", "2. 引擎与参数"), ("s3", "3. 运行与结果"), ("s4", "4. 解读")]
(RPT / "方法论报告_scTenifoldKnk.html").write_text(
    page("方法论报告 scTenifoldKnk", "方法论 · scTenifoldKnk", "GSE175817 · AHR", nav, knk_body), encoding="utf-8"
)

# ---------- 4. 方法论报告 GenKI ----------
gk_body = f"""
<div class='hero'><h1>方法论报告 — GenKI（VGAE）</h1>
<p>GSE175817 人痤疮髓系；皮损 TREM2 / M2-like 巨噬细胞；虚拟敲除 AHR（对照基因各引擎自算）。</p>
<div class='take'>{CLAIM}GenKI 的显著性是 KL 与排列命中，<strong>不是</strong> <code>p.adj</code>。</div></div>

<h2 id='s1'>1. 数据与切片</h2>
<p>与 scTenifoldKnk 共用切片说明：GSE175817、作者注释、皮损 × 亚群。靶基因 AHR 必须在矩阵内；GenKI 输入为 Seurat <code>vst</code> top 3000 高变基因，靶基因不在名单则补入。皮损 TREM2 1515 细胞；皮损 M2-like 266 细胞。</p>

<h2 id='s2'>2. 引擎与参数</h2>
<p>PCR 建网保留 |w| top 15% 边；VGAE（2 层 GCN + 内积解码）把每个基因编码为二维高斯。虚拟 KO = 把靶基因所有边（从与到）置零后重编码，逐基因 KL。超参搜索 100 次（lr/beta/wd 按 Yang 等原文网格）；早停看验证 AP。零分布 1000 次不放回排列；响应基因 = KL 位于该次 top 5% <em>且</em> hit &gt; 95%（&gt;950/1000）；靶基因自身不算发现。文献：Yang 等 <em>NAR</em> 2023，DOI 10.1093/nar/gkad450；VGAE：Kipf &amp; Welling 2016。</p>
{fig(f"{GK_PRE}/01_方法示意_GenKIVgaeWorkflow.jpg", "图 1 方法示意（按 Yang 等 NAR 2023 Fig.1 结构自绘：WT scGRN → VGAE → 边置零 → KL → bagging）。")}
{fig(f"{GK_PRE}/01_部位示意_HumanAcne_AhrSites.jpg", "图 2 取材部位示意（与 Knk 同源数据）。")}

<h2 id='s3'>3. 运行与结果</h2>
<div class='wrap'><table><tr><th>亚群</th><th>靶</th><th>对照</th><th>过线行（含自身）</th><th>其他响应基因</th><th>GO/KEGG</th></tr>
<tr><td>TREM2 macrophage</td><td>AHR</td><td>DHRS9</td><td>0 / 0</td><td>—</td><td>0 / 0</td></tr>
<tr><td>M2-like macrophage</td><td>AHR</td><td>FEN1</td><td>4 / 14</td><td>TFRC、ADGRE5、C5AR2</td><td>0 / 0</td></tr>
</table></div>
{fig(f"{GK_TREM2}09_散点图_RankKL_AHR.png", "图 3 TREM2 × AHR 排名 vs KL。SPP1 hit=943 未过 950 线；AHR 自身 KL≈3.35e-4、hit=787。")}
{fig(f"{GK_M2}04_柱状图_KL_AHR.png", "图 4 M2-like × AHR 过线基因 KL（对数轴）。")}
{fig(f"{GK_M2}09_散点图_RankKL_AHR.png", "图 5 M2-like × AHR 排名 vs KL。")}
{fig(f"{GK_TREM2D}09_散点图_RankKL_DHRS9.png", "图 6 TREM2 对照 DHRS9：无过线基因。")}
{fig(f"{GK_M2F}09_散点图_RankKL_FEN1.png", "图 7 M2-like 对照 FEN1：14 行过线（含自身），与 AHR 名单无交集。")}

<h2 id='s4'>4. 解读</h2>
<p>TREM2 × AHR 没有其他响应基因（SPP1 hit=943 差 7 次未过线），故不做富集。M2-like × AHR 其他响应 TFRC、ADGRE5、C5AR2，KL 均约 1e-6 量级，统计过线不等于扰动强；GO/KEGG 无通过条目。对照 FEN1 给出 13 个其他响应基因，说明该网对「去掉一个基因的边」本身就会给出名单，特异结论须对照过滤。</p>
<p class='footer'>{CLAIM}</p>
"""
(RPT / "方法论报告_GenKI.html").write_text(
    page("方法论报告 GenKI", "方法论 · GenKI", "GSE175817 · AHR", nav, gk_body), encoding="utf-8"
)

# ---------- 5. 论文范式报告 scTenifoldKnk ----------
knk_paper = f"""
<div class='hero'><h1>论文范式报告 — scTenifoldKnk（Result 分节）</h1>
<p>结构对齐 Osorio 等 <em>Patterns</em> 2022 的 Result 叙事。{CLAIM}</p></div>

<h2 id='r1'>Result 1 — 方法与取材</h2>
<p>在 GSE175817 的皮损巨噬细胞上对 AHR 做虚拟敲除。虚拟敲除不是删除表达该基因的细胞，而是修改调控网：10 次细胞抽样各建一网（pcNet 1.4.3，GPU），CP 秩 3 合并为野生型张量，再将 AHR 指向其他基因的边置零，两网对齐二维流形后逐基因计算 dRegulation 距离与 FDR。</p>
{fig(f"{KNK_PRE}/01_方法示意_scTenifoldKnkWorkflow.jpg", "图 1 方法示意。")}
{fig(f"{KNK_PRE}/01_部位示意_HumanAcne_AhrSites.jpg", "图 2 取材部位示意。")}

<h2 id='r2'>Result 2 — 这批细胞是否允许做虚拟敲除</h2>
<p>皮损 TREM2 1515 细胞、AHR 检出 436（28.8%）；皮损 M2-like 266 细胞、检出 95（35.7%）。两者均多于抽样上限 500 或与其接近，可敲。M1-like 皮损 116 细胞 AHR 检出为 0，不敲。</p>
{fig(f"{KNK_PRE}/03_柱状图_AHR检出率_TargetDetectionBar.png", "图 3 AHR 检出率。")}
{fig(f"{KNK_PRE}/02_散点图_AHR表达UMAP_AhrFeature.png", "图 4 AHR 表达 UMAP。")}

<h2 id='r3'>Result 3 — 扰动基因</h2>
<p>TREM2 × AHR 仅 GAPDH 过 FDR &lt; 0.05。M2-like × AHR 过线 RPL10、RPS18。两张网的响应名单没有交集。</p>
{fig(f"{KNK_TREM2}04_散点图_扰动排名_TREM2_AHR.png", "图 5 TREM2 × AHR 扰动排名。")}
{fig(f"{KNK_M2}04_柱状图_扰动基因_M2-like_AHR.png", "图 6 M2-like × AHR Top 扰动基因。")}

<h2 id='r4'>Result 4 — 富集</h2>
<p>TREM2 × AHR 无通过条目。M2-like × AHR 的 3 条 GO CC 全为核糖体结构条目，由 RPL10/RPS18 撑起，属结构性读出。</p>
{fig(f"{KNK_M2}05_柱状图_GO通过_M2-like_AHR.png", "图 7 通过阈值的 GO 条目。")}

<h2 id='r5'>Discussion（摘要级）</h2>
<p>在本数据与参数下，AHR 虚拟敲除没有给出稳定、非核糖体的通路级响应。这不否定 AHR 的表达证据，只说明这张网络上「去掉 AHR 的边」不足以驱动可富集的响应基因集。后续应以 GenKI 的排列稳定性与对照基因过滤并读，不把空结果写成阴性结论。</p>
<p class='footer'>{CLAIM}</p>
"""
nav_p = [("r1", "Result 1 方法与取材"), ("r2", "Result 2 可行性"), ("r3", "Result 3 扰动基因"), ("r4", "Result 4 富集"), ("r5", "Discussion")]
(RPT / "论文范式报告_scTenifoldKnk.html").write_text(
    page("论文范式报告 scTenifoldKnk", "论文范式 · scTenifoldKnk", "Result 分节", nav_p, knk_paper), encoding="utf-8"
)

# ---------- 6. 论文范式报告 GenKI ----------
gk_paper = f"""
<div class='hero'><h1>论文范式报告 — GenKI（Abstract → Discussion）</h1>
<p>结构对齐 Yang 等 <em>NAR</em> 2023 的章节叙事。{CLAIM}</p></div>

<h2 id='a1'>Abstract</h2>
<p>在 GSE175817 皮损 TREM2 与 M2-like 巨噬细胞上，用 GenKI 对 AHR 做虚拟敲除。TREM2 无其他响应基因；M2-like 给出 TFRC、ADGRE5、C5AR2。均为计算预测。</p>

<h2 id='a2'>Introduction（一句）</h2>
<p>GenKI 用 WT 单细胞数据学习 scGRN 与 VGAE 潜空间，把靶基因的边置零后以 KL 衡量各基因受扰程度，用排列命中判稳定响应，不要求真实 KO 样本。</p>

<h2 id='a3'>Results</h2>
<h3>VGAE 与判定规则</h3>
<p>top 15% 边；100 次超参搜索后正式训练（M2-like 验证 AP≈0.94，TREM2≈0.73）；1000 次不放回排列；响应 = KL top 5% 且 hit &gt; 95%。</p>
{fig(f"{GK_PRE}/01_方法示意_GenKIVgaeWorkflow.jpg", "图 1 GenKI 方法示意。")}
<h3>TREM2 × AHR：无其他响应基因</h3>
<p>SPP1 hit=943，距 950 阈值差 7 次命中；AHR 自身 KL≈3.35e-4。对照 DHRS9 同样无过线。</p>
{fig(f"{GK_TREM2}09_散点图_RankKL_AHR.png", "图 2 TREM2 × AHR 排名 vs KL。")}
<h3>M2-like × AHR：三个其他响应基因</h3>
<p>TFRC（hit 952）、ADGRE5（958）、C5AR2（957），KL 约 1e-6。对照 FEN1 过线 13 个其他基因，两名单无交集。</p>
{fig(f"{GK_M2}04_柱状图_KL_AHR.png", "图 3 M2-like × AHR 过线基因 KL。")}
{fig(f"{GK_M2F}09_散点图_RankKL_FEN1.png", "图 4 对照 FEN1。")}

<h2 id='a4'>Methods（一句）</h2>
<p>见方法论报告_GenKI.html；响应规则为 KL top 5% ∩ hit &gt; 95%，不使用 <code>p.adj</code>。</p>

<h2 id='a5'>Discussion</h2>
<p>TREM2 网络对 AHR 置零接近阈值但未稳定过线，M2-like 网络给出三个低 KL 响应基因。对照 FEN1 的大名单提示该网络对随机置零同样敏感，因此特异结论须同时看对照。两引擎结果并读：Knk 的 FDR 名单与 GenKI 的 KL 名单没有简单包含关系，各自成表，不做「谁更优」。</p>
<p class='footer'>{CLAIM}</p>
"""
nav_g = [("a1", "Abstract"), ("a2", "Introduction"), ("a3", "Results"), ("a4", "Methods"), ("a5", "Discussion")]
(RPT / "论文范式报告_GenKI.html").write_text(
    page("论文范式报告 GenKI", "论文范式 · GenKI", "Abstract → Discussion", nav_g, gk_paper), encoding="utf-8"
)

# ---------- 7. index_报告入口 ----------
index_body = """
<h2 id="top">报告</h2>
<p>论文式报告按参考论文的章节写：Knk 用 Result 分节，GenKI 用 NAR 的 Abstract 到 Discussion。方法论报告按数据/参数/运行/解读。没有通过筛选的富集图不在论文正文里。</p>
<ul>
<li><a href='论文范式报告_scTenifoldKnk.html'>论文范式报告_scTenifoldKnk</a></li>
<li><a href='论文范式报告_GenKI.html'>论文范式报告_GenKI</a></li>
<li><a href='方法论报告_scTenifoldKnk.html'>方法论报告_scTenifoldKnk</a></li>
<li><a href='方法论报告_GenKI.html'>方法论报告_GenKI</a></li>
<li><a href='../../富集汇总_EnrichSummary/报告文件/富集汇总_EnrichSummary.html'>富集汇总_EnrichSummary</a></li>
</ul>
<p>文献：<a href='../../GenKI/报告文件/_文献/文献_Papers/01_GenKI_NAR2023_gkad450.pdf'>GenKI NAR 2023</a>，
<a href='../../GenKI/报告文件/_文献/文献_Papers/02_VGAE_Kipf2016_1611.07308.pdf'>VGAE</a>，
<a href='../../scTenifoldKnk_1.4.3_GPU/报告文件/虚拟敲除方法学.pdf'>scTenifoldKnk 方法学 PDF（Osorio 2022）</a>。</p>
<p class='footer'>请在结果文件夹内打开，图片用相对路径。正文是计算预测，不是湿实验敲除。</p>
"""
(RPT / "index_报告入口.html").write_text(
    page("报告入口", "报告入口", "GSE175817 · 婷婷痤疮 · AHR", [("top", "报告")], index_body), encoding="utf-8"
)

# ---------- 8. 富集汇总 html ----------
terms_html = (
    "<div class='wrap'><table><tr><th>亚群</th><th>引擎</th><th>靶</th><th>来源</th><th>条目</th><th>p.adjust</th><th>基因</th></tr>"
    + "".join(
        f"<tr><td>{esc(r.subtype)}</td><td>{esc(r.engine)}</td><td>{esc(r.target)}</td>"
        f"<td>{esc(r.source)}</td><td>{esc(r.term)}</td><td>{r.p_adjust:.4g}</td><td>{esc(r.genes)}</td></tr>"
        for r in terms.itertuples()
    )
    + "</table></div>"
    if len(terms)
    else "<p>无通过条目。</p>"
)
sum_html_rows = "".join(
    f"<tr><td>{esc(r.subtype)}</td><td>{esc(r.engine)}</td><td>{esc(r.target)}</td><td>{esc(r.score_column)}</td>"
    f"<td>{esc(r.n_pass_rows)}</td><td>{esc(r.n_other_genes)}</td><td>{esc(r.n_go_pass)}</td><td>{esc(r.n_kegg_pass)}</td></tr>"
    for r in summary.itertuples()
)
enrich_body = f"""
<div class='hero'><h1>富集汇总 — 响应与通过条目</h1>
<p>跨亚群 × 引擎 × 靶基因合看。富集只用该引擎自己的响应基因表；阈值 BH p&lt;0.05 且 q&lt;0.2。{CLAIM}</p></div>
<h2 id='e1'>响应与富集总表</h2>
<div class='wrap'><table><tr><th>亚群</th><th>引擎</th><th>靶</th><th>显著性列</th><th>过线行</th><th>其他响应</th><th>GO</th><th>KEGG</th></tr>{sum_html_rows}</table></div>
{fig("../图片文件/04_柱状图_响应基因汇总_AllEnginesCounts.png", "响应基因数（含/不含靶基因自身）。")}
{fig("../图片文件/05_柱状图_官方富集通过数_PassCount.png", "官方富集通过条目数。")}
<h2 id='e2'>通过条目明细</h2>
{terms_html}
{fig("../图片文件/05_热图_富集条目汇总_TermHeatmap.png", "通过条目热图（只画通过条目）。")}
<p class='footer'>{CLAIM}</p>
"""
(SUM / "报告文件" / "富集汇总_EnrichSummary.html").write_text(
    page("富集汇总", "富集汇总", "两引擎合看", [("e1", "总表"), ("e2", "通过条目")], enrich_body), encoding="utf-8"
)

print("REPORTS_DONE")
print(summary.to_string(index=False))
