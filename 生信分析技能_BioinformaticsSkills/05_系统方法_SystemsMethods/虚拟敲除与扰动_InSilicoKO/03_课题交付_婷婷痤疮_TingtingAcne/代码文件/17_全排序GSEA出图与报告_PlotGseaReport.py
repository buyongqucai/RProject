# -*- coding: utf-8 -*-
"""Tingting ranked-GSEA figures and detailed HTML report."""
from __future__ import annotations

import html
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RES = Path(r"C:\Users\10540\Desktop\婷婷\虚拟敲除\结果文件")
GSEA = RES / "_跨亚群" / "GSEA全排序_RankedGSEA"
DATA = GSEA / "数据文件"
FIG = GSEA / "图片文件"
REP = GSEA / "报告文件"
RPT = RES / "_跨亚群" / "课题报告_ProjectReports" / "报告文件"
for d in (DATA, FIG, REP, RPT):
    d.mkdir(parents=True, exist_ok=True)

NAVY = "#24362f"
ACC = "#2f5d4c"
BLUE = "#4C78A8"
RED = "#C17B7B"
GOLD = "#D4A72C"


def save(fig, stem: str) -> None:
    fig.savefig(FIG / f"{stem}.png", dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(FIG / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fmt_p(x) -> str:
    if pd.isna(x):
        return "NA"
    x = float(x)
    return "<1e-300" if x == 0 else f"{x:.3g}"


def table(df: pd.DataFrame, cols: list[str], max_rows: int = 30) -> str:
    if df.empty:
        return "<p class='empty'>No rows.</p>"
    d = df.loc[:, [c for c in cols if c in df.columns]].head(max_rows).copy()
    for c in d.columns:
        if c in {"pvalue", "padj", "qvalue"}:
            d[c] = d[c].map(fmt_p)
        elif c in {"NES", "rank_spearman"}:
            d[c] = pd.to_numeric(d[c], errors="coerce").map(lambda v: "NA" if pd.isna(v) else f"{v:.3f}")
    th = "".join(f"<th>{html.escape(str(c))}</th>" for c in d.columns)
    rows = []
    for _, r in d.iterrows():
        rows.append("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in r.tolist()) + "</tr>")
    return f"<div class='wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"


def fig(rel: str, caption: str) -> str:
    return f"<figure><img src='{rel}' alt=''/><figcaption>{html.escape(caption)}</figcaption></figure>"


results = pd.read_csv(DATA / "08_GSEA全量结果_AllRankedGsea.csv")
summary = pd.read_csv(DATA / "08_GSEA分析摘要_GseaSummary.csv")
spec = pd.read_csv(DATA / "08_GSEA特异性诊断_AHR对照_Specificity.csv")
audit = pd.read_csv(DATA / "08_GSEA基因映射审计_IDMappingAudit.csv")
config = pd.read_csv(DATA / "08_GSEA运行参数_GseaRunConfig.csv")
ranked = pd.read_csv(DATA / "08_GSEA排名基因表_RankedGenes.csv")

# Figure 1: rank-pair specificity.
pairs = [
    ("TREM2 macrophage", "scTenifoldKnk_1.4.3_GPU", "AHR", "MGAT4A", "distance"),
    ("M2-like macrophage", "scTenifoldKnk_1.4.3_GPU", "AHR", "BID", "distance"),
    ("TREM2 macrophage", "GenKI", "AHR", "DHRS9", "KL"),
    ("M2-like macrophage", "GenKI", "AHR", "FEN1", "KL"),
]
fig1, axes = plt.subplots(2, 2, figsize=(10, 8))
for ax, (subtype, engine, target, control, metric) in zip(axes.ravel(), pairs):
    a = ranked[(ranked.subtype == subtype) & (ranked.engine == engine) &
               (ranked.target_or_control == target) & (ranked.rank_metric == metric)].copy()
    b = ranked[(ranked.subtype == subtype) & (ranked.engine == engine) &
               (ranked.target_or_control == control) & (ranked.rank_metric == metric)].copy()
    a["rank_a"] = a.score.rank(ascending=False, method="min")
    b["rank_b"] = b.score.rank(ascending=False, method="min")
    m = a[["entrez", "rank_a"]].merge(b[["entrez", "rank_b"]], on="entrez")
    n = max(len(m), 1)
    rho = m.rank_a.corr(m.rank_b, method="spearman")
    top_overlap = len(set(a.nlargest(20, "score").entrez) & set(b.nlargest(20, "score").entrez))
    ax.scatter(m.rank_a / n, m.rank_b / n, s=5, alpha=0.28, color=BLUE, edgecolors="none")
    ax.plot([0, 1], [0, 1], color="#888888", lw=1, ls="--")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel(f"{target} rank percentile")
    ax.set_ylabel(f"{control} rank percentile")
    ax.set_title(f"{subtype.replace(' macrophage', '')} | {engine.replace('scTenifoldKnk_1.4.3_GPU', 'Knk')}\nSpearman={rho:.3f}; top-20 overlap={top_overlap}/20", fontsize=10)
fig1.suptitle("Target-versus-control rank specificity", fontsize=15, fontweight="bold")
fig1.tight_layout(rect=[0, 0, 1, 0.96])
save(fig1, "08_GSEA特异性诊断_AHR与对照_Specificity")

# Figure 2: strict counts.
plot_sum = summary.copy()
plot_sum["analysis"] = plot_sum.engine.str.replace("scTenifoldKnk_1.4.3_GPU", "Knk", regex=False) + "\n" + plot_sum.subtype.str.replace(" macrophage", "", regex=False) + "\n" + plot_sum.target_or_control + "\n" + plot_sum.rank_metric
pivot = plot_sum.pivot_table(index="analysis", columns="collection", values="strict_pass", aggfunc="sum", fill_value=0)
pivot = pivot.reindex(columns=[c for c in ["GO-BP", "GO-CC", "GO-MF", "KEGG"] if c in pivot.columns], fill_value=0)
fig2, ax = plt.subplots(figsize=(11, 6.5))
im = ax.imshow(pivot.values, cmap="YlGnBu", aspect="auto")
ax.set_xticks(range(len(pivot.columns)), pivot.columns)
ax.set_yticks(range(len(pivot.index)), pivot.index, fontsize=8)
for i in range(pivot.shape[0]):
    for j in range(pivot.shape[1]):
        ax.text(j, i, int(pivot.values[i, j]), ha="center", va="center", color="black", fontsize=8)
ax.set_title("Number of GSEA terms passing padj<0.05 and q<0.2")
fig2.colorbar(im, ax=ax, label="passing terms")
fig2.tight_layout()
save(fig2, "08_GSEA严格通过数_StrictPassCount")

# Figure 3: top target terms.
target = results[(results.role.isin(["target_primary", "target_secondary"])) & (results.strict_pass == True)].copy()
top_rows = []
for _, grp in target.groupby(["engine", "subtype", "rank_metric", "role"], sort=False):
    top_rows.append(grp.sort_values(["padj", "pvalue"]).head(3))
top = pd.concat(top_rows, ignore_index=True) if top_rows else pd.DataFrame()
if not top.empty:
    top["analysis"] = top.engine.str.replace("scTenifoldKnk_1.4.3_GPU", "Knk", regex=False) + " | " + top.subtype.str.replace(" macrophage", "", regex=False) + " | " + top.rank_metric
    top["term_label"] = top.collection + " | " + top.Description.str.slice(0, 52)
    mat = top.pivot_table(index="term_label", columns="analysis", values="NES", aggfunc="first")
    score = top.assign(neglog=top.padj.map(lambda x: -math.log10(max(float(x), 1e-300)))).pivot_table(index="term_label", columns="analysis", values="neglog", aggfunc="first")
    mat = mat.loc[score.max(axis=1).sort_values(ascending=False).index]
    score = score.loc[mat.index]
    fig3, ax = plt.subplots(figsize=(12, max(5, 0.32 * len(mat))))
    im = ax.imshow(score.values, cmap="magma", aspect="auto")
    ax.set_xticks(range(len(mat.columns)), mat.columns, rotation=28, ha="right", fontsize=8)
    ax.set_yticks(range(len(mat.index)), mat.index, fontsize=8)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat.values[i, j]
            if not pd.isna(v):
                ax.text(j, i, f"NES {v:.2f}", ha="center", va="center", color="black", fontsize=7, bbox=dict(facecolor="white", alpha=0.72, edgecolor="none", pad=1.2))
    ax.set_title("Top FDR-passing target GSEA terms (fill: -log10 padj; label: NES)")
    fig3.colorbar(im, ax=ax, label="-log10(padj)")
    fig3.tight_layout()
    save(fig3, "08_GSEA_NES热图_TopTerms_NesHeatmap")

curve_images = sorted(FIG.glob("08_GSEA曲线_*_*.png"))
primary = results[(results.role == "target_primary")].sort_values(["padj", "pvalue"])
secondary = results[(results.role == "target_secondary")].sort_values(["padj", "pvalue"])
controls = results[(results.role == "control")].sort_values(["padj", "pvalue"])
z_sens = results[(results.role == "target_sensitivity")].sort_values(["padj", "pvalue"])

# Shared pathway comparison.
def shared_terms(engine: str, metric: str, subtype_a: str, subtype_b: str) -> list[str]:
    a = set(results[(results.engine == engine) & (results.rank_metric == metric) & (results.subtype == subtype_a) & (results.strict_pass == True)].pathway)
    b = set(results[(results.engine == engine) & (results.rank_metric == metric) & (results.subtype == subtype_b) & (results.strict_pass == True)].pathway)
    desc = results.drop_duplicates("pathway").set_index("pathway").Description.to_dict()
    return sorted(desc.get(x, x) for x in a & b)

knk_shared = shared_terms("scTenifoldKnk_1.4.3_GPU", "distance", "TREM2 macrophage", "M2-like macrophage")
genki_shared = shared_terms("GenKI", "KL", "TREM2 macrophage", "M2-like macrophage")

primary_count = int((results.role == "target_primary").sum())
primary_strict = int(((results.role == "target_primary") & (results.strict_pass == True)).sum())
secondary_strict = int(((results.role == "target_secondary") & (results.strict_pass == True)).sum())
control_strict = int(((results.role == "control") & (results.strict_pass == True)).sum())

body = f"""
<div class='hero'>
  <h1>全排序 GSEA 详细报告</h1>
  <p class='sub'>GSE175817 · 婷婷痤疮 · AHR 虚拟敲除 · scTenifoldKnk / GenKI</p>
  <div class='take'><strong>最终判断：</strong>
  全排序 GSEA 找到了统计显著条目，但没有得到一个可跨亚群、跨引擎稳定支持的 AHR 特异研究通路。
  scTenifoldKnk 主排名主要落在翻译/核糖体/结构分子；GenKI 只在 M2-like 给出胞外囊泡、受体配体和免疫相关候选主题。
  因此本报告把这些写成<strong>候选主题</strong>，不把任何单条通路定为最终机制。</div>
</div>

<h2 id='s1'>1. 执行摘要</h2>
<ul>
  <li>共分析4个 AHR 目标排名和4个对照排名，结果表 {len(results):,} 行。</li>
  <li>目标排名中通过 <code>padj&lt;0.05 且 q&lt;0.2</code> 的条目共 {primary_strict + secondary_strict} 条；对照排名也有 {control_strict} 条，说明“统计通过”不自动等于“AHR特异”。</li>
  <li>scTenifoldKnk distance 主分析有显著条目，但 TREM2 与 M2-like 的核心共同主题是 translation / ribosome / structural molecule activity。</li>
  <li>GenKI TREM2 没有严格通过条目；GenKI M2-like 有54条，最稳定主题为 extracellular exosome/vesicle、signaling receptor regulator/ligand、immune response。</li>
  <li>特异性诊断：Knk AHR 与对照的响应基因完全重合，distance 排名 Spearman 为0.838和0.910；GenKI M2 的 AHR 与 FEN1 响应基因不重合、排名相关0.427，特异性相对更好。</li>
</ul>

<h2 id='s2'>2. 数据、排名和统计口径</h2>
<p>本分析没有重新运行虚拟敲除，而是使用已完成的完整排名：</p>
<ul>
  <li>scTenifoldKnk：完整 <code>扰动_Dr.csv</code>，主排名 <code>distance</code>；剔除 AHR。distance 是 WT/KO 网络流形扰动距离，<strong>不是表达上下调</strong>。</li>
  <li>scTenifoldKnk 敏感性：<code>Z</code> 标准化扰动距离，<code>scoreType='std'</code>；正 NES 只表示相对扰动较高。</li>
  <li>GenKI：完整 <code>KL排序_RankKL.csv</code>，独立探索性 GSEA；KL 是分布差异/扰动量，<strong>不是 DEG 统计量</strong>。</li>
  <li>对照：Knk MGAT4A/BID，GenKI DHRS9/FEN1，用于判断目标排名是否具有特异性。</li>
</ul>
<p>基因集来自 GO BP/CC/MF 与 KEGG hsa。主阈值为 BH <code>padj&lt;0.05</code> 且 Storey q-value <code>&lt;0.2</code>；<code>minGSSize=10</code>、<code>maxGSSize=500</code>、<code>nPermSimple=1000</code>、<code>eps=0</code>。</p>
{table(config, ['parameter', 'value'], 30)}
{table(audit, ['engine','subtype','target_or_control','rank_metric','role','input_rows','mapped_symbols','duplicate_entrez_removed','final_rank_genes'], 20)}

<h2 id='s3'>3. 靶基因特异性诊断</h2>
{fig('../../GSEA全排序_RankedGSEA/图片文件/08_GSEA特异性诊断_AHR与对照_Specificity.png', 'AHR 与对照基因的完整排名散点。点越接近对角线，说明删除任意目标/对照都会得到相似排名。')}
{table(spec, ['engine','subtype','target','control','rank_metric','target_responsive','control_responsive','responsive_jaccard','rank_spearman','top20_overlap'], 10)}
<p><strong>解读：</strong>Knk 的响应基因重合度为1，且排名高度相关，支持“当前响应主要为共同网络/管家信号”的判断。GenKI M2 的目标与对照响应基因不重合，排名相关较低，提示 GenKI M2 的全排名信号比 Knk 更有目标特异性。</p>

<h2 id='s4'>4. scTenifoldKnk 全排序 GSEA</h2>
{fig('../../GSEA全排序_RankedGSEA/图片文件/08_GSEA严格通过数_StrictPassCount.png', '各分析与基因集集合的严格通过条目数。')}
<p>主排名 <code>distance</code> 的严格通过条目并不少，但前列条目高度集中于翻译、核糖体、核糖核蛋白复合体、结构分子活性和核仁。KEGG 的“Coronavirus disease”不应解释为感染证据；其基因集包含大量核糖体/宿主翻译基因，属于宽泛宿主反应条目。</p>
{table(primary, ['subtype','collection','pathway','Description','size','NES','pvalue','padj','qvalue'], 25)}
<p><strong>跨亚群共同通过条目：</strong>{html.escape('；'.join(knk_shared) if knk_shared else '无')}</p>

<h2 id='s5'>5. GenKI 独立探索性 GSEA</h2>
<p>GenKI TREM2 × AHR 在四个基因集集合中均无严格通过条目。M2-like × AHR 出现胞外外泌体/胞外囊泡、信号受体调节/配体活性、免疫反应等主题，并有少量 KEGG 炎症/感染相关条目。</p>
{table(secondary, ['subtype','collection','pathway','Description','size','NES','pvalue','padj','qvalue'], 30)}
<p><strong>跨亚群共同通过条目：</strong>{html.escape('；'.join(genki_shared) if genki_shared else '无')}</p>
<p>由于 TREM2 与 M2-like 没有共同严格条目，这些结果只能定位为<strong>M2-like 特异的候选主题</strong>，不能写成整个巨噬细胞群的稳定机制。</p>

<h2 id='s6'>6. Z 排名敏感性分析</h2>
<p>Z 与 distance 来自同一扰动距离，主要改变排名权重和双侧标准化。敏感性分析出现更多显著条目，但仍以 ribosome、translation、myoblast/syncytium fusion 为主。其作用是检查统计稳健性，不提供上下调方向。</p>
{table(z_sens, ['subtype','collection','pathway','Description','size','NES','pvalue','padj','qvalue'], 25)}

<h2 id='s7'>7. 对照基因 GSEA</h2>
<p>对照并非始终空结果：Knk MGAT4A 出现过氧化物酶体/乙醛代谢，BID 出现凋亡/p53；GenKI DHRS9 出现 ER 膜/脂蛋白结合，FEN1 无严格通过条目。对照能产生具有自身生物学含义的通路，因此 AHR 结果必须与对照并读。</p>
{table(controls, ['engine','subtype','target_or_control','collection','pathway','Description','size','NES','pvalue','padj','qvalue'], 30)}

<h2 id='s8'>8. GSEA 曲线</h2>
<p>以下曲线来自当前排名中统计最靠前的目标条目。图中 <code>FDR-pass</code> 只说明统计通过，不证明 AHR 因果调控。</p>
{''.join(fig(f"../../GSEA全排序_RankedGSEA/图片文件/{p.name}", p.stem.replace('08_GSEA曲线_', '')) for p in curve_images)}

<h2 id='s9'>9. 候选主题与不可写结论</h2>
<h3>可以写</h3>
<ul>
  <li>scTenifoldKnk 高扰动端稳定富集翻译、核糖体和结构分子相关基因集。</li>
  <li>GenKI 在 M2-like 中提示胞外囊泡/外泌体、受体配体和免疫反应相关候选主题。</li>
  <li>两类引擎的通路级结果不完全一致，说明不同网络扰动定义对结果影响较大。</li>
  <li>所有结果均为网络虚拟敲除的计算预测。</li>
</ul>
<h3>不能写</h3>
<ul>
  <li>AHR 敲除激活或抑制上述通路。</li>
  <li>“Coronavirus disease”代表真实病毒感染。</li>
  <li>核糖体条目是 AHR 特异机制。</li>
  <li>GenKI M2 候选主题已经跨亚群、跨引擎验证。</li>
  <li>虚拟敲除结果等同于湿实验 KO 或 Seurat DEG。</li>
</ul>

<h2 id='s10'>10. 结论</h2>
<div class='take'>
<p><strong>1. scTenifoldKnk 单独是否足够？</strong>不够。虽然全排序 GSEA 有显著条目，但主要是翻译/核糖体/结构分子，而且 AHR 与对照排名高度相似。</p>
<p><strong>2. 是否选出了合适通路？</strong>没有单一通路达到“跨亚群、跨引擎、对照过滤后稳定”的标准。GenKI M2 提供了胞外囊泡—受体/免疫信号这一候选主题，但只在 M2-like 成立。</p>
<p><strong>3. GenKI 是否有价值？</strong>有。它提供了与 Knk 不同、且目标/对照区分更好的 M2-like 信号；但 TREM2 为空，仍不能写成统一机制。</p>
<p><strong>4. 当前最诚实的研究表述：</strong>AHR 虚拟敲除提示核糖体/翻译层面的共同网络扰动；GenKI 在 M2-like 中进一步提示胞外囊泡与受体免疫信号候选主题。上述主题需要匹配对照、网络稳定性和独立数据验证。</p>
</div>

<h2 id='s11'>11. 文件与复现</h2>
<ul>
  <li>分析脚本：<code>16_全排序GSEA_RankGsea.R</code></li>
  <li>报告脚本：<code>17_全排序GSEA出图与报告_PlotGseaReport.py</code></li>
  <li>完整结果：<code>08_GSEA全量结果_AllRankedGsea.csv</code></li>
  <li>严格通过条目：<code>08_GSEA通过条目_PassedGsea.csv</code></li>
  <li>映射审计、运行参数、SessionInfo 均在 GSEA 数据/报告目录。</li>
</ul>
<p class='footer'>本报告区分 ORA 与 GSEA、scTenifoldKnk 与 GenKI、目标与对照。计算预测，不作湿实验因果结论。</p>
"""

page = f"""<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width, initial-scale=1'/>
<title>全排序 GSEA 报告</title><style>
html{{font-size:100%}} body{{margin:0;font-family:'Segoe UI','Microsoft YaHei',sans-serif;line-height:1.78;color:#1c241f;background:#f3efe6}}
.layout{{display:grid;grid-template-columns:clamp(14rem,22vw,20rem) minmax(0,1fr);min-height:100vh}}
.sidebar{{position:sticky;top:0;align-self:start;height:100vh;overflow:auto;background:{NAVY};color:#f4efe6;padding:1rem .8rem 2rem}}
.sidebar h1{{font-size:1.05rem;margin:0 0 .3rem}} .sidebar .sub{{font-size:.78rem;color:#c5d2cb;margin-bottom:.8rem}}
.sidebar a{{display:block;color:#e7eee9;text-decoration:none;font-size:.86rem;padding:.38rem .5rem;border-radius:.45rem}}
.sidebar a:hover{{background:rgba(216,240,228,.14)}} .main{{max-width:76rem;padding:clamp(1rem,2vw,2rem) clamp(1rem,3vw,2.6rem) 4rem}}
.hero{{background:#fffdf8;border:1px solid #ddd4c4;border-radius:1rem;padding:1.25rem 1.4rem}}
.hero h1{{font-size:clamp(1.55rem,2.5vw,2.15rem);margin:.1rem 0 .35rem}} .sub{{color:#5c635c}}
.take{{background:#eef6f1;border-left:.38rem solid {ACC};padding:.85rem 1rem;border-radius:.55rem;margin:1rem 0}}
h2{{font-size:clamp(1.18rem,1.8vw,1.48rem);margin:2.1rem 0 .65rem;border-bottom:2px solid #d5e0d7;padding-bottom:.35rem}}
h3{{margin:1.25rem 0 .4rem;color:{NAVY}}} figure{{margin:1.15rem 0;background:#fffdf8;border:1px solid #ddd4c4;border-radius:.85rem;padding:.75rem}}
figure img{{width:100%;max-width:100%;height:auto;display:block}} figcaption{{margin-top:.55rem;color:#4e554f;font-size:.92rem}}
.wrap{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;font-size:.88rem;background:#fff}}
th,td{{border:1px solid #d8d8d0;padding:.42rem .52rem;vertical-align:top;word-break:break-word}}
th{{background:#eef3ef;text-align:left;position:sticky;top:0}} code{{background:#e9ece9;padding:.08rem .28rem;border-radius:.35rem}}
.empty{{color:#777;font-style:italic}} .footer{{color:#5c635c;border-top:1px solid #d5d5cc;margin-top:2rem;padding-top:1rem}}
@media(max-width:54rem){{.layout{{grid-template-columns:1fr}} .sidebar{{position:relative;height:auto;max-height:38vh}}}}
</style></head><body><div class='layout'><aside class='sidebar'>
<h1>全排序 GSEA</h1><div class='sub'>GSE175817 · AHR · Knk / GenKI</div>
<a href='#s1'>1. 执行摘要</a><a href='#s2'>2. 数据与口径</a><a href='#s3'>3. 特异性</a><a href='#s4'>4. scTenifoldKnk</a>
<a href='#s5'>5. GenKI</a><a href='#s6'>6. Z 敏感性</a><a href='#s7'>7. 对照</a><a href='#s8'>8. GSEA 曲线</a>
<a href='#s9'>9. 可写/不可写</a><a href='#s10'>10. 结论</a><a href='#s11'>11. 复现</a>
</aside><main class='main'>{body}</main></div></body></html>"""

report_path = RPT / "全排序GSEA报告_RankedGsea.html"
report_path.write_text(page, encoding="utf-8")

# Update report entrance once.
index = RPT / "index_报告入口.html"
if index.exists():
    txt = index.read_text(encoding="utf-8")
    link = "<li><a href='全排序GSEA报告_RankedGsea.html'>全排序GSEA报告_RankedGsea</a></li>"
    if "全排序GSEA报告_RankedGsea.html" not in txt:
        txt = txt.replace("</ul>", link + "</ul>", 1)
        index.write_text(txt, encoding="utf-8")

status = f"""status=PASS
analysis=ranked GSEA
target_results_rows={(results.role != 'control').sum()}
control_results_rows={(results.role == 'control').sum()}
strict_target={primary_strict + secondary_strict}
strict_control={control_strict}
primary=scTenifoldKnk distance scoreType=pos
sensitivity=scTenifoldKnk Z scoreType=std
secondary=GenKI KL scoreType=pos
thresholds=padj<0.05 and qvalue<0.2
conclusion=no single AHR pathway stable across subtype and engine
claim=computational prediction only
"""
(REP / "STATUS_全排序GSEA_RankedGsea.txt").write_text(status, encoding="utf-8")

print(f"REPORT_DONE {report_path}")
print(f"FIGURES {len(list(FIG.glob('*.png')))}")
print(f"TARGET_STRICT {primary_strict + secondary_strict} CONTROL_STRICT {control_strict}")