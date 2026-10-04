# -*- coding: utf-8 -*-
"""按本地 PDF 的章节重写论文式报告与方法论。

本地文献（不粘贴原文）：
  GenKI NAR 2023、VGAE Kipf 2016：结果文件/_跨亚群/GenKI/报告文件/_文献/文献_Papers/
  scTenifoldKnk：五亚群留档/.../虚拟敲除方法学.pdf
数字来自各基因响应表与富集表。无通过的富集柱图不进论文正文。
"""
from __future__ import annotations

import csv
import html
import os
from pathlib import Path

DESK = Path(r"C:\Users\10540\Desktop\琪乐无穷\虚拟敲除")
RESULT = DESK / "结果文件"
OUT = RESULT / "_跨亚群" / "课题报告_ProjectReports" / "报告文件"
OUT.mkdir(parents=True, exist_ok=True)

KNK = "scTenifoldKnk_1.4.3_GPU"
PAPER_GENKI = "../../GenKI/报告文件/_文献/文献_Papers/01_GenKI_NAR2023_gkad450.pdf"
PAPER_VGAE = "../../GenKI/报告文件/_文献/文献_Papers/02_VGAE_Kipf2016_1611.07308.pdf"
PAPER_KNK = "../../../../../五亚群留档/结果文件/_跨亚群/scTenifoldKnk/报告文件/虚拟敲除方法学.pdf"

summary: dict[tuple[str, str, str], dict] = {}
with (RESULT / "_跨亚群" / "富集汇总_EnrichSummary" / "数据文件" / "汇总_响应与富集_Summary.csv").open(encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        summary[(row["engine"], row["subtype"], row["knockout"])] = row

terms: list[dict] = []
tp = RESULT / "_跨亚群" / "富集汇总_EnrichSummary" / "数据文件" / "汇总_富集条目_TermsLong.csv"
if tp.exists():
    with tp.open(encoding="utf-8") as handle:
        terms = list(csv.DictReader(handle))


def esc(x: object) -> str:
    return html.escape("" if x is None else str(x))


def rel(path: Path) -> str:
    return Path(os.path.relpath(path, OUT)).as_posix()


def fig(img: Path, cap: str, after: str) -> str:
    if not img.exists():
        return ""
    return (
        f"<figure><img src='{rel(img)}' alt='{esc(img.name)}'/>"
        f"<figcaption>{cap}</figcaption></figure>"
        f"<p>{after}</p>"
    )


def h2(a: str, t: str) -> str:
    return f'<h2 id="{a}">{t}</h2>'


def h3(a: str, t: str) -> str:
    return f'<h3 id="{a}">{t}</h3>'


def tbl(inner: str) -> str:
    return f"<div class='wrap'><table>{inner}</table></div>"


def imgs(folder: Path, prefixes: list[str]) -> list[Path]:
    out: list[Path] = []
    for p in prefixes:
        out.extend(sorted(folder.glob(p + "*.png")))
        out.extend(sorted(folder.glob(p + "*.jpg")))
    seen, uniq = set(), []
    for f in out:
        if f.exists() and f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq


def pass_figs(st: str, engine: str, gene: str) -> list[Path]:
    gdir = RESULT / st / engine / gene / "图片文件"
    if not gdir.is_dir():
        return []
    return [f for f in sorted(gdir.glob("05_*.png")) if "Empty" not in f.name and "无通过" not in f.name]


CSS = r"""
html{font-size:100%}
body{margin:0;font-family:"Segoe UI","Microsoft YaHei",sans-serif;font-size:1.0625rem;line-height:1.85;color:#1c241f;background:#f3efe6}
.layout{display:grid;grid-template-columns:clamp(14rem,22vw,20rem) minmax(0,1fr);min-height:100vh}
.sidebar{position:sticky;top:0;align-self:start;height:100vh;overflow:auto;background:#24362f;color:#f4efe6;padding:1rem .8rem 2rem}
.sidebar h1{font-size:1.05rem;margin:0 0 .3rem;line-height:1.35}
.sidebar .sub{font-size:.78rem;color:#c5d2cb;margin-bottom:.8rem}
.sidebar a{display:block;color:#e7eee9;text-decoration:none;font-size:.86rem;padding:.38rem .5rem;border-radius:.45rem;border-left:.18rem solid transparent}
.sidebar a.l2{padding-left:1rem;font-size:.78rem;color:#c9d5ce}
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
JS = """<script>(function(){const links=[...document.querySelectorAll('.sidebar a')];
const secs=links.map(a=>document.getElementById(a.getAttribute('href').slice(1))).filter(Boolean);
function on(id){links.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+id));}
const io=new IntersectionObserver(es=>{const v=es.filter(e=>e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio);if(v[0])on(v[0].target.id);},{rootMargin:'-12% 0px -55% 0px',threshold:[0.15,0.4]});
secs.forEach(s=>io.observe(s));if(secs[0])on(secs[0].id);})();</script>"""


def shell(title, side, sub, toc, body: list[str]) -> str:
    nav = []
    for href, label, level in toc:
        cls = " class='l2'" if level > 1 else ""
        nav.append(f"<a href='#{href}'{cls}>{esc(label)}</a>")
    return "\n".join([
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'/>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'/>",
        f"<title>{esc(title)}</title><style>{CSS}</style></head><body>",
        "<div class='layout'><aside class='sidebar'>",
        f"<h1>{esc(side)}</h1><div class='sub'>{esc(sub)}</div>",
        *nav, "</aside><main class='main'>", *body,
        "<p class='footer'>请在琪乐无穷目录内打开，图片用相对路径。正文是计算预测，不是湿实验敲除。</p>",
        "</main></div>", JS, "</body></html>",
    ])


def build_knk_paper() -> Path:
    cross = RESULT / "_跨亚群" / KNK / "图片文件"
    toc = [
        ("src", "本地文献", 1),
        ("intro", "Introduction", 1),
        ("r1", "Result 1 流程", 1),
        ("r2", "Result 2 数据是否可敲", 1),
        ("r3", "Result 3 Cplx2 的扰动基因", 1),
        ("r4", "Result 4 对照扣除", 1),
        ("r5", "Result 5 富集", 1),
        ("disc", "Discussion", 1),
        ("mat", "Materials", 1),
    ]
    body = [
        "<section class='hero'><h1>scTenifoldKnk 虚拟敲除：PEP 与 NF1</h1>",
        "<p>写法对照本地《虚拟敲除方法学》PDF（Osorio 等，<cite>Patterns</cite> 2022）：先 Introduction，再按 Result 分节写案例，方法放在文末。不粘贴论文原文。</p></section>",
        h2("src", "本地文献"),
        f"<p>本报告对照的 PDF 已在桌面，没有重新下载：<a href='{PAPER_KNK}'>虚拟敲除方法学.pdf</a>（五亚群留档中的 scTenifoldKnk 论文）。"
        "该文目录是 Introduction，随后 Result 1 到 Result 7 每个案例单独成节，Discussion 之后才是 PC 回归、虚拟敲除和富集的 Materials。"
        "下面用同样的顺序写本课题在 GSE197289 Control 上的结果。GenKI 不写在这一篇里。</p>",
        h2("intro", "Introduction"),
        "<p>基因敲除实验用基因改造动物比较敲除与野生型，再用表达谱当作分子表型。单细胞数据出现以后，可以在只有野生型计数时，先从细胞构造基因调控网，再在网上做虚拟敲除。"
        "Osorio 等把这件事写成 scTenifoldKnk：对同一群细胞反复抽样，每张样本建一张网，堆成张量；野生型张量与「目标基因出边被置零」的张量做流形对齐；每个基因得到一个扰动距离和校正后的显著性。"
        "他们把这些基因称为 virtual KO perturbed genes，并写明这不是真实敲除动物的差异表达基因。</p>",
        "<p>本课题要问的是：在正常小鼠三叉神经节的两个感觉神经元亚群里，按这套默认流程敲除六个候选基因之后，还有没有通过 FDR 的特异扰动基因，以及这些基因能不能再通过 GO 与 KEGG。"
        "数据是 Yang 等 2022 年偏头痛图谱 GSE197289 的 Control，不是眶下神经慢性缩窄，也不是慢性三叉神经痛模型。亚群只留作者注释里对应 CGRP 的 PEP 和接近 NF200 的 NF1。"
        "六个基因是 Mitf、Bace2、Cplx2、Ppp1r26、Slc28a3、Sh3d21，一次只敲一个。每个亚群另敲一个与 Cplx2 低相关的对照，用来标出非特异信号。</p>",
        "<p>论文在 Trem2、Nkx2-1 等例子里用 FDR&lt;0.05 定义显著扰动基因，再对这个集合做功能注释；有足够基因且能在 STRING 上连起来时才画互作网。"
        "本报告遵守同一条线：不把距离排名靠前但 FDR 不显著的基因写进通路。距离前 50 的探索性富集已移出主结果。</p>",
        h2("r1", "Result 1. 流程"),
        "<p>对应论文 Result 1。虚拟敲除在这里不是删掉表达该基因的细胞，而是改网络。</p>",
        "<p>第一步，从该亚群的原始计数做 scQC，再转到 CPM。第二步，重复 10 次、每次最多抽 500 个细胞，用主成分回归得到一张全连接网，再按分位数留下较强的边。"
        "第三步，10 张网做秩为 3 的稀疏 CP 分解，边权保留 3 位小数，得到野生型张量。第四步，把待敲基因指向其他基因的边写成 0，细胞仍在。"
        "第五步，两个张量对齐到 2 维流形。第六步，dRegulation 给每个基因一个距离、折叠变化和 FDR。FDR&lt;0.05 且不是被敲基因本身，才叫本次的扰动基因。</p>",
    ]
    for f in imgs(cross, ["01_方法", "01_部位"]):
        if "方法" in f.name:
            body.append(fig(f, "图 1. 自绘流程，结构对应论文 Figure 1，不是论文截图。",
                             "读图从建网到 dRegulation。终点是扰动距离和 FDR，不是 Seurat 的差异基因，也不是预先指定的突触通路。"))
        else:
            body.append(fig(f, "图 2. 取材部位示意。",
                             "计数来自三叉神经节。这张图只说明组织，不包含敲除结果。"))
    body += [
        h2("r2", "Result 2. 这批细胞是否允许做虚拟敲除"),
        "<p>论文在做模拟和真实数据之前，先固定野生型矩阵。这里同样先检查亚群和靶基因，否则后面的空结果无法解释。</p>",
        "<p>注释表里 Control 的 PEP 有 780 个细胞，Cplx2 检出 343 个（44.0%）；NF1 有 1765 个细胞，Cplx2 检出 889 个（50.4%）。"
        "两群都多于每张网抽取的 500 个细胞。六个靶基因在两个亚群的检出细胞数都大于 0，所以都敲。"
        "Sh3d21 在 PEP 只有 1 个细胞、在 NF1 只有 6 个，仍然敲，但要预期它在网上几乎没有边。"
        "Hprt1 在矩阵里没有这个符号，Ppia 是内参，两者不敲。</p>",
    ]
    for f in imgs(cross, ["02_", "03_"]):
        if "Violin" in f.name:
            body.append(fig(f, "图 3. 六个靶基因在 PEP 与 NF1 的表达。",
                             "小提琴说明检出稀还是密。Sh3d21 贴在零附近。Cplx2 在两群都铺开，所以它适合作为主问题里的敲除对象，但这不表示通路已经选定。"))
        elif "PepNf1" in f.name or "Umap" in f.name:
            body.append(fig(f, "图 4. PEP 与 NF1 的 UMAP。",
                             "两群分开，才支持按亚群各建一套网。混在一起时不能把后面的距离解释成某一类神经元的结果。"))
        elif "Cplx2" in f.name:
            body.append(fig(f, "图 5. Cplx2 的表达分布。",
                             "颜色深的细胞核表达 Cplx2。广谱表达只说明基因在矩阵里，不说明虚拟敲除之后会有 FDR 显著的邻居。"))
        else:
            body.append(fig(f, "图 6. 靶基因检出率。",
                             "柱高是阳性细胞占该亚群的比例。检出为 0 才不敲。这张图不使用 FDR。"))
    body += [
        "<p>这些图回答的是「能不能敲」。它们不包含扰动距离。若后面没有显著基因，不能回过头来说是亚群没分开。</p>",
        h2("r3", "Result 3. Cplx2 与对照的扰动基因"),
        "<p>对应论文里逐个基因呈现 DR 排名的方式。横轴是按距离的名次，纵轴是调控距离。红色才是 FDR&lt;0.05。"
        "被敲基因自己会因为出边消失而离开野生型流形，解释「谁被扰动」时去掉它。灰点即使距离排在前 15，也只是未通过检验的背景。</p>",
        "<p>PEP 敲除 Cplx2：FDR&lt;0.05 的其他基因是 0 个。对照 Ret 同样是 0 个。"
        "NF1 敲除 Cplx2：通过的其他基因是 Actg1（FDR 约 6.6×10<sup>−32</sup>）和 Ywhag（FDR 约 4.8×10<sup>−26</sup>）。"
        "同一标准敲除对照 Rdx，通过的也是 Ywhag 和 Actg1。因此这两个基因描述的是这一亚群、这一套 10×500 网络下反复出现的移动，不是 Cplx2 独有的后果。</p>",
        "<p>PEP 的 Mitf、Ppp1r26、Sh3d21 在 3 位小数取整后的野生型网里没有出边。敲除不改变网络。若图上仍有很小的距离，按实现说明读作数值噪声，不进入富集。"
        "CPU 与 GPU 用的是同一套 1.4.3 公式。下面以 GPU 目录的图为代表，不把两种实现写成两个生物学结论。</p>",
    ]
    combo = cross / "04_散点图_扰动排名_PepNf1RankScatter.png"
    body.append(fig(combo, "图 7. 各次敲除的扰动排名合看。",
                     "几乎全是灰点。这和「距离前 50 里有很多基因」不矛盾：那些基因没有过 FDR，论文不会把它们当作 perturbed genes。"))
    for st, gene in [("PEP", "Cplx2"), ("PEP", "Ret"), ("NF1", "Cplx2"), ("NF1", "Rdx")]:
        gdir = RESULT / st / KNK / gene / "图片文件"
        for f in sorted(gdir.glob("04_*.png")) if gdir.is_dir() else []:
            kind = "排名散点" if "Scatter" in f.name else "距离前 15 的条图"
            body.append(fig(
                f,
                f"图. {st} · {gene} 的{kind}{'（对照）' if gene in ('Ret','Rdx') else ''}。",
                "只把红色当作扰动基因。NF1 的 Cplx2 与 Rdx 若红条是同一对基因，就不能写 Cplx2 特异。PEP 没有红点，就没有下游通路的输入。",
            ))
    body += [
        h2("r4", "Result 4. 与对照放在一起看"),
        "<p>论文在有一组 FDR 基因、并且它们能在 STRING 上形成连接时，才画以敲除基因为中心的蛋白互作网，并报告互作富集。"
        "这里没有留下 Cplx2 特异的 FDR 伙伴，所以不查询 STRING，也不画蛋白互作子网。下面的边只表示「对虚拟敲除有响应」，不是 STRING 的物理互作。</p>",
    ]
    for f in imgs(cross, ["06_", "07_"]):
        if f.name.startswith("06"):
            body.append(fig(f, "图 8. PEP 敲 Cplx2、NF1 敲 Cplx2、NF1 敲 Rdx 的响应对比。",
                             "PEP 一侧没有节点。NF1 两侧都是 Actg1 和 Ywhag。这张图的结论是共享，不是 Cplx2 的私有网络。"))
        else:
            body.append(fig(f, "图 9. FDR 基因集合的 Jaccard。",
                             "颜色深表示名单重叠高。无出边的 PEP 基因不参与这张热图。它不表示通路相似性。"))
    body += [
        h2("r5", "Result 5. 富集"),
        "<p>论文把功能注释放在扰动基因已经确定之后。输入只能是 FDR&lt;0.05 的其他基因。GO 的生物过程、细胞组分、分子功能分开做，KEGG 用小鼠 mmu。"
        "校正是 Benjamini–Hochberg，p 的上限 0.05，q 的上限 0.2。不把突触囊泡或 SNARE 写进筛选条件。</p>",
        "<p>Actg1 与 Ywhag 两个基因没有产生同时满足上述阈值的 GO 或 KEGG 条目。其余敲除要么没有 FDR 基因，要么没有出边。"
        "因此不存在可以放进正文的通路柱图或气泡图。各基因目录里的 <code>05_富集_无通过条目.txt</code> 记录的是已经计算、没有通过。"
        "按距离取前 50 再做的 enrichGO 会得到一些校正后较小的术语，那不是本文的基因集，不在这一节解释。</p>",
        "<div class='take'><b>这一节的结果。</b>按论文使用的 FDR 门槛，本数据没有 Cplx2 特异的扰动基因，也就没有通过筛选的 GO/KEGG 可以报告。</div>",
        h2("disc", "Discussion"),
        "<p>Osorio 等在巨噬细胞和肺上皮等例子里报告了成组的 FDR 基因，并继续做 STRING 和功能注释。"
        "同一软件、同一 FDR 用在这批正常三叉神经节细胞核上，没有给出 Cplx2 特异的名单。"
        "这不应写成方法失效。它说明在 10 张网、每张最多 500 个细胞、秩 3、3 位小数这套默认设置下，Cplx2 的出边置零没有留下通过多重检验的特异邻居。</p>",
        "<p>若改用未校正的距离前 50 名做富集，图会很多，但那就离开了论文 Result 里「significant DR genes」的定义。"
        "3 位小数会抹掉很弱的边，无出边基因的空结果首先是数值表示。对照 Rdx 重复了 Actg1 和 Ywhag，这两名不能进入 Cplx2 特异结论。"
        "GSE197289 的 Control 不是慢性三叉神经痛模型，本结果也不能写成疾病机制已被验证。GenKI 用的是另一套 KL 与排列，数字不能加到这张 FDR 表上。</p>",
        h2("mat", "Materials"),
        "<p>对应论文文末的方法，而不是把参数藏在图注里。</p>",
        "<p><b>数据。</b>GEO GSE197289，小鼠，<code>model == Control</code>，作者 subtype 为 PEP 或 NF1。不把其他 GSE 拼进同一矩阵。"
        "细胞数与 Cplx2 检出见上文。基因过滤不设 8000 上限：优先留高表达基因，六个靶基因只要检出大于 0 就保留。这是作者在软件讨论中的建议，不是高变基因子集。</p>",
        "<p><b>质控与建网。</b>scQC：文库大小大于 1000，去掉文库异常细胞，线粒体比例低于 0.1，基因检出比例高于 5%，线粒体前缀 <code>mt-</code>。这些是包的默认。"
        "网络数 10、每张最多 500 个细胞、主成分 3、分位数 0.9、张量秩 3，分别对应软件的 nc_nNet、nc_nCells、pcNet 与 td_K。论文写了 CP 分解，没有报告秩的搜索，所以秩不做网格。"
        "边权四舍五入到 3 位是本课题为了压低数值尘埃而固定的，不是论文正文里的搜索项。抽样种子为 1。GPU 只加速 1.4.3 的主成分回归，不改公式；没有 CUDA 时同一公式在 CPU 上跑。</p>",
        "<p><b>敲除与检验。</b>一次一个基因，出边置零。流形对齐维数 2。响应基因：<code>p.adj &lt; 0.05</code> 且不是被敲基因。无出边则不做富集。"
        "对照在该引擎建网基因中取与 Cplx2 绝对 Pearson 相关最低、方差大于 0、且不在六个靶基因里的基因。本实现是 PEP 的 Ret 和 NF1 的 Rdx。</p>",
        "<p><b>富集。</b>clusterProfiler，<code>org.Mm.eg.db</code>。GO 三个本体各自 <code>enrichGO</code>，KEGG 为 <code>enrichKEGG(organism='mmu')</code>。"
        "BH，pvalueCutoff=0.05，qvalueCutoff=0.2。论文示例里的功能注释在显著 DR 基因之后；本课题用的是同一顺序、不同的注释软件。未通过的本体不绘图。</p>",
    ]
    out = OUT / "论文范式报告_scTenifoldKnk.html"
    out.write_text(shell("scTenifoldKnk 论文式报告", "Knk 论文式报告", "按方法学 PDF 的 Result 分节", toc, body), encoding="utf-8")
    return out


def build_genki_paper() -> Path:
    cross = RESULT / "_跨亚群" / "GenKI" / "图片文件"
    toc = [
        ("src", "本地文献", 1),
        ("abs", "Abstract", 1),
        ("intro", "Introduction", 1),
        ("mm", "Materials and Methods", 1),
        ("mm-data", "数据与基因", 2),
        ("mm-grn", "调控网", 2),
        ("mm-vgae", "VGAE 与超参", 2),
        ("mm-ko", "敲除、排列与注释", 2),
        ("res", "Results", 1),
        ("res-fw", "框架", 2),
        ("res-n", "响应规模与对照", 2),
        ("res-c", "案例：NF1 · Cplx2", 2),
        ("res-p", "案例：NF1 · Ppp1r26", 2),
        ("res-m", "案例：NF1 · Mitf", 2),
        ("res-o", "其余敲除", 2),
        ("disc", "Discussion", 1),
    ]
    body = [
        "<section class='hero'><h1>GenKI 虚拟敲除：PEP 与 NF1</h1>",
        "<p>章节对照本地 NAR 2023 PDF：Abstract、Introduction、Materials and Methods、Results、Discussion。案例按该文「一个敲除一段、图后写数字」来写。</p></section>",
        h2("src", "本地文献"),
        f"<p>两篇 PDF 已在 <code>结果文件/_跨亚群/GenKI/报告文件/_文献/文献_Papers/</code>，本报告不重新下载："
        f"<a href='{PAPER_GENKI}'>01_GenKI_NAR2023_gkad450.pdf</a>，"
        f"<a href='{PAPER_VGAE}'>02_VGAE_Kipf2016_1611.07308.pdf</a>。"
        "NAR 正文的方法顺序是：vst 取 top 3000、ScaleData、PC 回归得到全连接网、默认只留绝对权重最高的 15% 并变成布尔图、训练 VGAE、去掉敲除基因的全部边、用潜变量参数的差异给基因排序、再做功能注释。"
        "Kipf 与 Welling 给出 VGAE：编码器输出每个节点的均值和方差，解码器用潜变量重构边。下面用这套顺序写本课题，不把 scTenifoldKnk 的 FDR 混进来。</p>",
        h2("abs", "Abstract"),
        "<p>GenKI 在只有野生型单细胞计数时，用变分图自编码器学习基因及其相互作用的潜变量；虚拟敲除是从调控网删掉目标基因的边，再比较野生型与敲除潜变量（Yang 等，Nucleic Acids Research，2023）。"
        "本工作把该框架用于 GSE197289 小鼠三叉神经节 Control 的 PEP 与 NF1。高变基因 3000 个，边保留绝对权重前 15%，超参数按论文数量级搜索 100 次，零分布为 1000 次不放回的细胞排列。"
        "响应基因要求 KL 进入该次前 5% 且在超过 95% 的排列中出现，并去掉被敲基因自己。</p>",
        "<p>PEP 只有 Mitf 得到 9 个其他响应基因，富集未通过。NF1 上 Cplx2、Ppp1r26、Mitf、Slc28a3 分别有 34、26、18、5 个其他响应基因，对照 Gm15551 有 144 个。"
        "Cplx2 与对照共享 5 个基因（含 Calca 与 Thbs1）。通过 BH p&lt;0.05 且 q&lt;0.2 的是：Ppp1r26 的 36 条 GO 生物过程，Mitf 的 1 条 GO 细胞组分，Cplx2 的 2 条 KEGG。"
        "这些是正常神经节上的计算预测，不是慢性三叉神经痛模型的验证，也不是湿实验敲除的差异基因。</p>",
        h2("intro", "Introduction"),
        "<p>NAR 论文的引言从真实敲除和 CRISPR 写起：功能来自敲除与野生型表型的差别，表达谱常被当作分子表型。单细胞测序提高了细胞分辨率，但也使「每个基因都做动物敲除」更不可行。"
        "因此需要一种只吃野生型矩阵的虚拟敲除。文中比较了 scGen、CPA、CellOracle 和 scTenifoldKnk：前两者需要真实扰动样本，CellOracle 面向转录因子，scTenifoldKnk 把野生型网和虚拟敲除网对齐到同一低维空间。"
        "GenKI 的选择是无监督 VGAE：先学野生型图上的潜变量，再构造一个去掉目标基因边的图，用分布差异给基因排序。</p>",
        "<p>该文强调两件事，本报告都保留。第一，不使用真实敲除样本的信息。第二，功能注释发生在显著扰动基因已经列出之后，而不是先指定通路再回头找基因。"
        "原文用 Enrichr 做注释并在基因足够时画 STRING。本课题的注释软件是 clusterProfiler 的 GO 与 KEGG，这一差别写在方法里，不假装用了 Enrichr。"
        "数据身份仍是偏头痛图谱中的正常三叉神经节。亚群只留 PEP 与 NF1，因为它们对应 CGRP 与 NF200 这一疾病分组，而不是因为 Cplx2 表达高。</p>",
        h2("mm", "Materials and Methods"),
        h3("mm-data", "数据与基因"),
        "<p>计数与作者注释来自 GSE197289，只用 Control。细胞类型沿用原研究标签，本课题不再聚类。PEP 780 个核，NF1 1765 个核。"
        "与 NAR 方法一致的部分：Seurat <code>FindVariableFeatures</code>，<code>selection.method = vst</code>，默认 top 3000；随后 ScaleData，作为 GenKI 的表达输入。"
        "与原文默认不完全相同、但在计划里写明的部分：六个靶基因若不在这 3000 个里且检出细胞数大于 0，则强制补入，避免「不是高变基因所以无法敲除」。"
        "检出为 0 或不在矩阵中的基因不敲。Hprt1 无此符号，不敲。Ppia 是内参，不敲。</p>",
        "<p>低相关对照不沿用 Knk 的 Ret 与 Rdx。它在 GenKI 实际使用的基因集合上重算：与 Cplx2 的绝对 Pearson 相关最小、方差大于 0、且不在六个靶基因中。"
        "得到 PEP 的 Abcc8 和 NF1 的 Gm15551。对照与靶基因共用同一张网和同一套训练好的模型，只是去掉的边不同。</p>",
        h3("mm-grn", "基因调控网"),
        "<p>NAR 的 “Gene regulatory network construction” 使用 scTenifoldNet 的 PC 回归。矩阵是基因×细胞。每次把一个基因当响应、其余基因当解释变量，在前若干主成分上回归，再把系数变回原始基因，拼成 p×p 的全连接邻接矩阵。"
        "全连接网里许多边不是真实调控。原文因此设阈值：默认只保留绝对权重最高的 15%，并说明在一定范围内排序对阈值不敏感，但过严会丢掉可能的边；用户可以按自己的网络改阈值，例如用 poweRlaw 拟合无标度。"
        "本课题首轮不改这 15%（代码 <code>EDGE_PERCENTILE = 85</code>）。阈值不是超参搜索的输出。阈值一变，布尔图就变，学习率、beta 和 weight decay 必须在新图上重搜。布尔图才是 VGAE 的输入。</p>",
        h3("mm-vgae", "VGAE 与超参数"),
        "<p>潜变量是二维二元高斯，优化器 Adam，初始化 Xavier。这些不随搜索改变。边划分约 75% 训练、5% 验证、20% 测试，划分种子 42，来自 GenKI 的 <code>split_data</code>。"
        "Kipf 与 Welling 的模型用编码器给出每个基因的均值和方差，用解码器重构边；训练损失包含重构与 KL 项，KL 项的权重就是 beta。</p>",
        "<p>NAR 的 “Hyperparameters, metrics and implementation” 把学习率、beta、weight decay 当作搜索项，而不是手填一个 README 示例值。"
        "本课题的搜索范围与实例计划一致，且落在原文报告的数量级里：学习率的指数从 −4 到 −1，beta 从 −5 到 −1，weight decay 从 −7 到 −3，再乘 1 到 9 的系数。每个亚群 100 次，种子 8096。"
        "原文在其数据上常得到 beta = 1×10<sup>−4</sup>、weight decay = 9×10<sup>−4</sup>，学习率则随数据集变化。本课题若验证集选中别的值，就用选中值，不把原文的点估计写死。</p>",
        "<p>早停和挑选是本课题在论文搜索范围之内加的停止规则，不是另设一套学习率：最多 100 轮，至少 10 轮；验证平均精度比当前最好高出 0.0001 才算提高；连续 15 轮没有提高则停，并恢复验证最好的权重。"
        "验证停滞 5 轮时学习率乘 0.5，最低到初始学习率的 1/100。100 次试验的挑选分是验证 AP 减去训练 AP 高于验证 AP 的部分。测试集 AP 只记录，不参与挑选。"
        "检测到 CUDA 时，搜索和最终拟合把模型与图放到 GPU；PC 回归建图仍在 CPU。日志字段 <code>fit_device</code> 记录实际设备。</p>",
        h3("mm-ko", "敲除、零分布与功能注释"),
        "<p>敲除不删除细胞。按 NAR 的做法，从布尔图去掉目标基因的边，再用训练好的编码器比较野生型与敲除的潜变量，距离是 KL。"
        "原文用重复抽样看排序是否稳定。本课题的零分布写死为 1000 次不放回排列：每次打乱全部细胞的顺序，每个细胞恰好出现一次，种子 0。"
        "软件 <code>pmt</code> 里的有放回抽样和 README 示例里的 100 次都不作为本课题标准。一个基因进入响应表，当且仅当该次 KL 位于前 5%，且在超过 950 次排列里出现。被敲基因本身不进入富集输入。</p>",
        "<p>其他响应基因少于 5 个时不做超几何检验。不少于 5 个时，用 clusterProfiler 分开做 GO 生物过程、细胞组分、分子功能，以及小鼠 KEGG。"
        "BH，p 上限 0.05，q 上限 0.2。这与课题筛选标准一致，也是「先有基因名单、再注释」；它和 NAR 使用 Enrichr 默认设置不是同一个软件。"
        "对照也通过的术语记为不特异。未通过的本体不画柱图。论文正文因此只放有通过条目的图。</p>",
        h2("res", "Results"),
        h3("res-fw", "框架"),
        "<p>NAR 的 Results 开头用 Figure 1 把框架画出来：野生型网、去掉 KO 基因的边、潜变量差异、再对显著基因做功能注释。"
        "下图是按同一顺序为本课题画的示意，不是论文原图。Enrich 一格包含 GO 三个本体和 KEGG；没有通过的不绘制。</p>",
    ]
    body.append(fig(
        cross / "01_方法示意_GenKIVgaeWorkflow.png",
        "图 1. GenKI 流程示意。",
        "从上到下是输入、基因、调控网、VGAE、搜索、敲除、排列、响应、富集。CUDA 只出现在 VGAE 的训练。富集不是筛选亚群的条件。",
    ))
    body += [
        h3("res-n", "响应基因有多少，对照先看"),
        "<p>NAR 在每个生物学案例里先给出虚拟敲除排出的基因，再谈功能。这里先给全部敲除的规模，因为对照的规模会限制后面所有「特异」二字。</p>",
        "<p>NF1 的对照 Gm15551 有 144 个其他响应基因，KL 最大的是 Calca（约 6.99×10<sup>5</sup>），其余多数 KL 在 10<sup>−7</sup> 量级。"
        "也就是说，在这张 NF1 图上，低相关基因的边被去掉之后，仍会有一份很长的名单通过 top 5% 与 95% 命中。任何与这 144 个基因重叠的名字，都不能单独支持靶基因特异。</p>",
    ]
    for f in imgs(cross, ["04_柱状图_响应基因数", "07_"]):
        if "04_" in f.name:
            body.append(fig(f, "图 2. 各次敲除的其他响应基因数。",
                             "先看 NF1 对照那一根最高的柱。PEP 多数为零。Cplx2 在 PEP 为零、在 NF1 为 34，两个亚群不能写成同一个结论。"))
        else:
            body.append(fig(f, "图 3. 响应名单的 Jaccard。",
                             "这张图比较的是基因集合是否重叠，不是通路。重叠高时，后面的 GO 术语更容易一起出现。"))
    rows = ["<tr><th>亚群</th><th>基因</th><th>角色</th><th>其他响应基因</th><th>通过的富集条目</th><th>最强条目</th></tr>"]
    for st, ctrl in [("PEP", "Abcc8"), ("NF1", "Gm15551")]:
        for gene in ["Mitf", "Bace2", "Cplx2", "Ppp1r26", "Slc28a3", "Sh3d21", ctrl]:
            r = summary.get(("GenKI", st, gene), {})
            if not r:
                continue
            rows.append(
                f"<tr><td>{st}</td><td>{esc(gene)}</td><td>{'对照' if gene==ctrl else '靶基因'}</td>"
                f"<td>{esc(r.get('n_response_excl_ko'))}</td><td>{esc(r.get('n_terms_pass_screen'))}</td>"
                f"<td>{esc(r.get('top_term'))}</td></tr>"
            )
    body.append(tbl("".join(rows)))
    body += [
        h3("res-c", "案例：NF1 敲除 Cplx2"),
        "<p>设置与 NAR 的单个基因案例相同：野生型网已经训练好，只去掉 Cplx2 的边，用 KL 和 1000 次排列排序，再去掉 Cplx2 自己。"
        "其他响应基因 34 个。KL 最高的是 Calca（约 1.19×10<sup>5</sup>）、Cd9（约 5.82×10<sup>4</sup>）、Ntrk3（约 9.37×10<sup>3</sup>）、Ret（约 9.28×10<sup>3</sup>）、Prkcb（约 6.16×10<sup>3</sup>）。"
        "这些名字来自响应表的排序，不是从通路名单里挑回来的。</p>",
        "<p>与 Gm15551 的交集是 5 个基因：2810410L24Rik、Calca、Ces5a、Kcne4、Thbs1。Calca 既是 Cplx2 敲除的第一名，也出现在对照里，因此不能写成 Cplx2 特异。"
        "GO 的三个本体都没有条目同时满足 BH p&lt;0.05 和 q&lt;0.2，所以正文没有 GO 柱图。"
        "KEGG 有 2 条通过，校正 P 都是 0.036：Central carbon metabolism in cancer（3 个基因：Ret、Fgfr1、Ntrk3）和 Proteoglycans in cancer（4 个基因：Fgfr1、Thbs1、Fzd2、Prkcb）。"
        "第二条含有 Thbs1，而 Thbs1 在对照交集里。两条通路的名字来自 KEGG 的癌症地图，落点是受体和信号基因，不能写成虚拟敲除导致肿瘤。</p>",
    ]
    gdir = RESULT / "NF1" / "GenKI" / "Cplx2" / "图片文件"
    for f in sorted(gdir.glob("04_*.png")):
        body.append(fig(
            f,
            "图. NF1 · Cplx2 的 KL " + ("排名。" if "Scatter" in f.name else "条图。"),
            "红点或长条是通过规则的基因。最左或最长的往往包括被敲基因自己；解释其他基因时用响应表里去掉 Cplx2 之后的顺序。Calca 虽强，但与对照共享。",
        ))
    for f in pass_figs("NF1", "GenKI", "Cplx2"):
        body.append(fig(
            f,
            "图. NF1 · Cplx2 通过筛选的 KEGG。",
            "只有这两条。横轴是校正 P 的负对数。Proteoglycans 里的 Thbs1 与对照 Gm15551 的响应基因重叠，这条不能单独支持特异。",
        ))
    body += [
        h3("res-p", "案例：NF1 敲除 Ppp1r26"),
        "<p>其他响应基因 26 个，与 Gm15551 的交集是 0。KL 最高的是 Tmem38b、Chrm3、Hoxd8、Scn5a、Npy1r，数量级约 10<sup>−7</sup>，比 Cplx2 头部的 Calca、Ret 小很多个数量级。"
        "统计过线不等于扰动强。GO 生物过程有 36 条通过，校正 P 最小的是 ureter development（0.0034，3 个基因），其后一批校正 P 约为 0.033，包括上皮细胞增殖的调控、输尿管芽形态发生、中肾管形态发生等。"
        "细胞组分和分子功能没有通过的条目，KEGG 也没有。这些生物过程不是预先指定的疼痛或递质释放术语。因为 KL 弱、条目多，它们放在候选列表里，不排到 Cplx2 那些高 KL 基因的前面。</p>",
    ]
    gdir = RESULT / "NF1" / "GenKI" / "Ppp1r26" / "图片文件"
    for f in list(sorted(gdir.glob("04_*.png"))) + pass_figs("NF1", "GenKI", "Ppp1r26"):
        body.append(fig(
            f,
            "图. NF1 · Ppp1r26。" + ("KL。" if "04_" in f.name else "仅 GO 生物过程中通过的条目，图中最多 8 条。"),
            "36 条里图上只显示校正 P 最小的若干条。没有 CC、MF、KEGG 图，是因为那三个库没有通过，不是漏做。",
        ))
    body += [
        h3("res-m", "案例：NF1 敲除 Mitf"),
        "<p>其他响应基因 18 个，与对照交集为 0。KL 最高约 5.7×10<sup>−5</sup>（Phldb2），其后是 Egfem1、Pcdhb5 等，仍远小于 Cplx2 的头部。"
        "GO 生物过程、分子功能和 KEGG 都没有通过。细胞组分有 1 条：basal part of cell，校正 P 0.028，4 个基因。"
        "一条细胞组分、基因数少，只能记为弱证据，不能提升成肥大细胞或三叉神经痛通路。GenKI 用的是感觉神经元 NF1，不是肥大细胞。</p>",
    ]
    gdir = RESULT / "NF1" / "GenKI" / "Mitf" / "图片文件"
    for f in list(sorted(gdir.glob("04_*.png"))) + pass_figs("NF1", "GenKI", "Mitf"):
        body.append(fig(
            f,
            "图. NF1 · Mitf。" + ("KL。" if "04_" in f.name else "仅通过的 GO 细胞组分。"),
            "只有 basal part of cell 进入正文。不要把未通过的生物过程补画成图。",
        ))
    body += [
        h3("res-o", "其余敲除：做了，但没有可绘制的通路"),
        "<p>PEP 敲除 Mitf：9 个其他响应基因，KL 最高的是 Pcdhb18（约 2.4×10<sup>−7</sup>）。四个富集库都没有通过，所以没有通路图。"
        "PEP 的 Cplx2、Bace2、Ppp1r26、Slc28a3、Sh3d21 和对照 Abcc8 的其他响应基因都是 0，不能从 PEP 写出 Cplx2 特异通路。</p>",
        "<p>NF1 敲除 Slc28a3：5 个其他响应基因（Dvl3、Gm10687、Naip5、Pdgfrl、Ccdc125），与对照无交集，但 GO 与 KEGG 都未通过，不画柱图。"
        "NF1 的 Bace2 与 Sh3d21 响应数为 0，与它们检出细胞很少、网上缺少边相一致。这些敲除的 KL 散点仍在各自基因目录，供核对「规则跑过」；因为没有通过的通路，论文正文不附空的富集图。</p>",
        h2("disc", "Discussion"),
        "<p>NAR 的讨论把 GenKI 写成动物敲除的计算替代，同时用模拟和公开数据说明它能接近真实敲除的功能方向。本数据只能支持更窄的句子："
        "在正常三叉神经节的 NF1 上，按原文的排序规则可以得到响应基因；其中 Cplx2 的高 KL 基因和两条 KEGG 值得留下做实验候选，但必须先扣除与 Gm15551 共享的 Calca、Thbs1 等。"
        "Ppp1r26 的 36 条生物过程来自很弱的 KL，不宜因为条目多就当成主结果。PEP 上 Cplx2 没有其他响应基因。</p>",
        "<p>和 scTenifoldKnk 相比，GenKI 在 NF1 更灵敏，对照也更灵敏。两套定义不能相加，也不能用一边的空结果否定另一边。"
        "CUDA 改变的是 VGAE 放在哪块设备上训练，不改变 15% 边、100 次搜索和 95% 命中的规则。"
        "原文注释用 Enrichr，这里用 clusterProfiler，通路名称的集合不会逐条相同，这是软件差异，要写在方法里。</p>",
        "<p>限制：计算预测；Control 不是慢性三叉神经痛；单核不是每只鼠的独立重复；超参是种子 8096 下的 100 次搜索，换种子会改变具体权重，响应规则不变。"
        "癌症通路的地图名不能写成表型。</p>",
        "<div class='take'><b>可以写进结论的只有这些。</b>NF1 · Ppp1r26 的 GO 生物过程 36 条；NF1 · Mitf 的 GO 细胞组分 1 条；NF1 · Cplx2 的 KEGG 2 条，且其中含与对照共享的 Thbs1。其余敲除没有通过筛选的通路。</div>",
    ]
    out = OUT / "论文范式报告_GenKI.html"
    out.write_text(shell("GenKI 论文式报告", "GenKI 论文式报告", "按 NAR 2023 的目录", toc, body), encoding="utf-8")
    return out


def build_knk_method() -> Path:
    toc = [
        ("s1", "1. 数据来源", 1), ("s2", "2. 数据选择规则", 1), ("s3", "3. 筛选标准", 1),
        ("s4", "4. 代码参数", 1), ("s5", "5. 处理流程", 1), ("s6", "6. 产物代表什么", 1),
        ("s7", "7. 出图", 1), ("s8", "8. 代码怎么用", 1), ("s9", "9. 整合状态", 1),
        ("s10", "10. CUDA", 1), ("s11", "11. 声称边界", 1),
    ]
    body = [
        "<section class='hero'><h1>方法论 · scTenifoldKnk</h1>",
        f"<p>参数对照本地 <a href='{PAPER_KNK}'>虚拟敲除方法学.pdf</a> 文末 Materials，以及 CRAN 包的默认值。改规则以《数据集筛选与M4规程》为准，不要只改本页。</p></section>",
        h2("s1", "1. 数据来源"),
        "<p>主结论只用一条链：NCBI GEO 的 GSE197289，小鼠三叉神经节单核 RNA-seq，文献是 Yang 等 2022 年 <cite>Neuron</cite> 的偏头痛图谱。"
        "本次取 <code>model == Control</code>。文件在桌面 <code>琪乐无穷/虚拟敲除/数据文件</code>：细胞注释 <code>01_细胞注释_CellMeta_GSE197289.csv.gz</code>，计数 <code>02_表达矩阵_Counts_GSE197289.RDS.gz</code>（基因×细胞）。计数不进 git。</p>",
        "<p>为什么不用别的登录号，按 GenKI 计划里那次公开库检索，而不是凭印象。GSE316925 是小鼠三叉神经节、而且是 IoN-CCI，但是 bulk，拆不开细胞。GSE186421 是口面部 CFA 的单细胞，不是慢性缩窄。"
        "GSE131272 是眶下神经部分切断。GSE322600 是 Sp5C 不是三叉神经节。GSE233838 与 E-MTAB-10792 是大鼠。GSE186505 是人外周血。人源记录不进小鼠主结论。"
        "没有把这些矩阵拼在一起再敲。Yang 等 2023 年 <cite>Frontiers in Pharmacology</cite> 写的 IoN-CCI 存放号 SUB13606115，这次 GEO 检索没有返回对应 GSE，因此不把它当成可下载的单细胞输入。</p>",
        "<p>GSE197289 的 Control 是正常三叉神经节。它可以用来做野生型虚拟敲除，不能写成慢性三叉神经痛模型已经有了单细胞验证。</p>",
        h2("s2", "2. 数据选择规则"),
        "<p>硬门槛是小鼠、单细胞或单核计数、主结论的组织是三叉神经节、登录号可回溯。2026-09-29 曾用「Cplx2 检出率至少 10% 且至少 25 个细胞」和「细胞数至少 300」把更多亚群放进来。"
        "2026-10-03 起这两条不再用来增加亚群，也不再用来只敲 Cplx2。</p>",
        "<p>亚群只留 PEP 和 NF1。判断依据是疾病分组：三叉神经痛相关的感觉神经元，标记对应 CGRP 和 NF200。作者注释里 PEP 是肽能，NF1 是有髓、接近 NF200。"
        "NP、TRPM8、cLTMR、NF2、NF3、SST 即使 Cplx2 高也不进。胶质、雪旺、成纤维、血管、免疫和 Injured 不进。细胞数不改选亚群，只说明代表性：每张网抽 500，两群都多于 500。</p>",
        tbl(
            "<tr><th>亚群</th><th>为何留下</th><th>Control 细胞</th><th>Cplx2 检出</th></tr>"
            "<tr><td>PEP</td><td>肽能，对应 CGRP</td><td>780</td><td>343（44.0%）</td></tr>"
            "<tr><td>NF1</td><td>有髓，接近 NF200</td><td>1765</td><td>889（50.4%）</td></tr>"
        ),
        "<p>敲除基因六个，一次一个。检出来自 2026-10-03 对 Control 计数的统计。Mitf：PEP 14/780（1.8%），NF1 65/1765（3.7%），肥大细胞转录因子，两群都敲。"
        "Bace2：23/780（2.9%），126/1765（7.1%），记为 TN 上调，都敲。Cplx2：343/780（44.0%），889/1765（50.4%），都敲。"
        "Ppp1r26：33/780（4.2%），28/1765（1.6%），都敲。Slc28a3：81/780（10.4%），130/1765（7.4%），记为 TN 下调，都敲。"
        "Sh3d21：1/780（0.1%），6/1765（0.3%），有检出所以敲，结果里必须写细胞很少。Hprt1 矩阵无此名（小鼠是 Hprt），不敲。Ppia 虽高表达，但是 qPCR 内参，不敲。</p>",
        "<p>对照不事先指定基因名。在该引擎建网用的基因里，取与 Cplx2 绝对 Pearson 相关最低、方差大于 0、且不在上述六个基因中的一个。"
        "scTenifoldKnk 得到 PEP 的 Ret 和 NF1 的 Rdx。GenKI 的基因集合不同，对照名字不同，不能为了同名而改规则。</p>",
        h2("s3", "3. 筛选标准"),
        "<p>每一关不通过就停在那一关，不把后面的图补出来。</p>",
        "<p><b>数据集。</b>必须是上面锁定的 Control 切片。其他登录号可以记录，不进主结论敲除。</p>",
        "<p><b>能否敲某一个基因。</b>矩阵里有这个符号，并且在该亚群检出细胞数大于 0。不满足则这一对不敲。不用 Cplx2 的检出率决定别的基因敲不敲。</p>",
        "<p><b>scQC。</b>只处理已经切出的亚群矩阵：文库大小超过 1000，去掉文库异常细胞，线粒体比例低于 0.1，基因在细胞中的检出比例高于 5%。这是 <code>scTenifoldKnk(qc=TRUE)</code> 调用 <code>scQC</code> 的默认，不是为三叉神经痛另调的。</p>",
        "<p><b>无出边。</b>野生型边权按 3 位小数取整后，若该基因没有出边，敲除不改变网络。写 <code>说明_无出边.txt</code>，不做富集。图上若还有距离，读作数值噪声。PEP 的 Mitf、Ppp1r26、Sh3d21 属于这一类。</p>",
        "<p><b>响应基因。</b>dRegulation 的 <code>p.adj &lt; 0.05</code>，并且不是被敲基因。论文示例用的就是 FDR&lt;0.05。距离前 40 或前 50 不是标准。不显著的基因可以留在全表里，但不能进富集。</p>",
        "<p><b>富集。</b>对响应基因分别做 GO 生物过程、细胞组分、分子功能，以及 KEGG（mmu）。BH，p=0.05，q=0.2。某一个库没有通过，就不画那个库。两个基因的 Actg1/Ywhag 没有通过任何库。</p>",
        "<p><b>特异。</b>对照敲除也显著的基因或术语可以记录，不写成靶基因特异。NF1 上 Actg1 与 Ywhag 同时属于 Cplx2 和 Rdx。</p>",
        h2("s4", "4. 代码参数：取值、出处、改没改"),
        "<p>下表与 <code>完整版_143GPU_FullVersion/config_配置.py</code> 一致。线程和 GPU 并发不在表里，运行时探测。</p>",
        tbl(
            "<tr><th>参数</th><th>取值</th><th>出处</th><th>本课题</th></tr>"
            "<tr><td>N_NET</td><td>10</td><td>包默认 nc_nNet；论文用多张网而不是一张</td><td>不改</td></tr>"
            "<tr><td>N_CELLS</td><td>500</td><td>包默认 nc_nCells</td><td>细胞不足则 n−1，并说明代表性</td></tr>"
            "<tr><td>MIN_LIB_SIZE</td><td>1000</td><td>scQC 默认</td><td>不改</td></tr>"
            "<tr><td>MIN_PCT</td><td>0.05</td><td>基因检出比例</td><td>不改</td></tr>"
            "<tr><td>MAX_MT_RATIO</td><td>0.1</td><td>线粒体比例</td><td>小鼠前缀 mt-</td></tr>"
            "<tr><td>N_COMP / Q</td><td>3 / 0.9</td><td>pcNet 1.4.3</td><td>不改</td></tr>"
            "<tr><td>张量秩</td><td>3</td><td>软件 td_K；论文写 CP 但没有搜秩</td><td>不做秩的网格</td></tr>"
            "<tr><td>N_DECIMAL</td><td>3</td><td>实现选择，用来压低数值尘埃</td><td>课题锁定，不是论文搜索项</td></tr>"
            "<tr><td>KO_ALIGN_D</td><td>2</td><td>流形对齐维数</td><td>不改</td></tr>"
            "<tr><td>FDR_CUT</td><td>0.05</td><td>论文显著 DR 基因</td><td>不改成 Top50</td></tr>"
            "<tr><td>ENRICH_P / Q</td><td>0.05 / 0.2</td><td>课题富集标准，BH</td><td>四个库都算，未通过不画</td></tr>"
            "<tr><td>SEED</td><td>1</td><td>只固定抽样</td><td>不改</td></tr>"
            "<tr><td>基因上限 8000</td><td>不使用</td><td>作者不主张只留高变基因</td><td>2026-10-03 取消</td></tr>"
            "<tr><td>张量迭代</td><td>最多 1000，容差 1e−5</td><td>官方 tensorDecomposition 的 maxIter / maxError</td><td>不改</td></tr>"
        ),
        "<p>五亚群试跑曾经用 3 张网、200 个细胞、约 1000 个基因、文库 500。那低于上表，只能当试跑，不能当作本报告的正式参数。那些结果在五亚群留档，不进现行虚拟敲除。</p>",
        h2("s5", "5. 处理流程：每一步的输入和输出"),
        "<p><b>导出与质控。</b>输入是注释表和 counts。输出在 <code>结果文件/&lt;亚群&gt;/scTenifoldKnk_1.4.3_GPU/_野生型/数据文件/</code>：CPM、基因名、抽样下标、计时。R 脚本是完整版的 <code>step1_export_qc.R</code>。</p>",
        "<p><b>建网与张量。</b>输入是质控后的 CPM 和 10 组细胞下标。输出是每张网和舍入后的野生型张量。<code>step2_gpu_build.py</code>。有 CUDA 时 SVD 在 GPU，否则 CPU 多进程。</p>",
        "<p><b>敲除。</b>输入是野生型张量。对每个基因把出边置零，做对齐和 dRegulation。输出在 <code>&lt;亚群&gt;/&lt;算法&gt;/&lt;基因&gt;/数据文件/扰动_Dr.csv</code> 和 <code>响应基因_Responsive.csv</code>。<code>step3_ko_enrich.R</code> 同时写 <code>富集_GO.csv</code> 与 <code>富集_KEGG.csv</code>。无出边则写报告目录里的说明，富集表为空。</p>",
        "<p>已有 CPM、网文件或扰动表时，对应步骤跳过。要重算必须删掉那一层产物。</p>",
        h2("s6", "6. 处理后的数据代表什么、怎么看"),
        "<p><code>扰动_Dr.csv</code> 的每一行是一个基因。distance 是对齐之后的调控距离，Z 和 FC 是 dRegulation 的统计量，p.value 未校正，p.adj 是 FDR。"
        "全表里大多数基因的 FDR 不显著。按 distance 从大到小看，只能知道谁动得多，不能知道谁显著。显著的定义只有 p.adj&lt;0.05 且 gene 不是被敲基因。</p>",
        "<p><code>响应基因_Responsive.csv</code> 是 FDR 子集，有的实现仍把被敲基因留在表里。做富集之前删掉它。行数在去掉自身之后若小于 2，超几何检验没有稳定输入，空的富集表是预期结果。</p>",
        "<p><code>富集_GO.csv</code> 只含已经通过 BH 与 q 的行。ontology 或 ONTOLOGY 列标明 BP、CC 或 MF。空文件表示三个本体都算过、都没过。不要把空文件读成「没有跑 GO」。"
        "<code>富集_KEGG.csv</code> 同样只含通过的小鼠通路。Description 里的 cancer 是数据库地图名，要看 gene 列里实际落入的基因。</p>",
        "<p>散点图：横轴排名，纵轴距离，红点是 FDR 通过。灰点再靠左也不是扰动基因。条图若画了前 15 名，灰色长条是距离大但未通过检验。"
        "空的富集柱图不表示「通路不存在于生物学」，只表示这张响应表没有一项通过事先写好的阈值。</p>",
        h2("s7", "7. 出图"),
        "<p>论文式报告收入：流程示意、亚群与表达、Cplx2 与对照的扰动图、响应对比和 Jaccard。不收入未通过筛选的 GO/KEGG 柱图和气泡图。"
        "空态说明留在基因目录的 txt，给审计用，不放进论文正文。探索性 Top50 图若还在，位于 <code>_未采用_探索Top50</code>，不引用。"
        "图面用英文、DPI 至少 600、同时有 PNG 和 SVG。目录是亚群 / 算法 / 基因 / 数据、图片、报告。</p>",
        h2("s8", "8. 代码怎么用"),
        "<p>从原始计数到扰动表和官方富集表的入口是 <code>Knk加速_KnkAccel/完整版_143GPU_FullVersion/run_all_一键运行.py</code>，桌面 <code>虚拟敲除/代码文件/完整版_143GPU_FullVersion/</code> 是副本。"
        "换数据集只改 <code>config_配置.py</code> 顶部的 DATA_DIR 和 RESULT_DIR。亚群或基因不同时再改 SUBTYPES 和 KNOCK_GENES。不要在不改筛选 SSOT 的情况下改 FDR 或 10×500。</p>",
        "<pre>cd 完整版_143GPU_FullVersion\nE:\\Python3.13.14\\python.exe run_all_一键运行.py</pre>",
        "<p>顺序：<code>probe_资源探测.py</code> 写本次 CPU/GPU 计划；<code>step1_export_qc.R</code>；<code>step2_gpu_build.py</code>；<code>step3_ko_enrich.R</code>。"
        "出图和 HTML 不在这一键里面。需要时再运行 <code>38_全基因图册补齐_AllGeneFigures.R</code>、<code>39_富集汇总_SummarizeEnrichment.R</code> 和本脚本。</p>",
        h2("s9", "9. 整合状态"),
        "<p>Knk 从 counts 到 <code>扰动_Dr.csv</code>、<code>响应基因_Responsive.csv</code>、<code>富集_GO.csv</code>、<code>富集_KEGG.csv</code> 已经由 run_all 串好，跳过逻辑也在。"
        "报告 HTML 是后处理：改了图或表之后要重跑 38、39 和 40，不会在敲除结束时自动刷新论文。"
        "GPU 与 CPU 两个目录是同一公式的两种实现，不是两个实验。</p>",
        h2("s10", "10. CUDA"),
        "<p>CUDA 只用于建网时的 leave-one-out SVD，以及探测到 GPU 时的张量步骤。科学参数不因为有 4080 而改变。"
        "没有 CUDA 时 step2 转到 CPU 多进程，FDR 的定义不变。流形对齐和 dRegulation 在 R 里，不把整个敲除都说成 GPU 算法。"
        "这和 GenKI 不同：GenKI 的 CUDA 用在 VGAE 训练，不用在 PC 回归建图。</p>",
        h2("s11", "11. 声称边界"),
        "<p class='note'>输出是 virtual KO 的扰动基因，不是湿实验敲除的 DEG，不是 Seurat 或 limma 的差异分析，也不是慢性三叉神经痛模型的验证。"
        "对照也显著的基因没有靶基因特异性。未通过 FDR 的距离排名不能写成显著通路。</p>",
    ]
    out = OUT / "方法论报告_scTenifoldKnk.html"
    out.write_text(shell("方法论 scTenifoldKnk", "Knk 方法论", "11 节，不收成一张小表", toc, body), encoding="utf-8")
    return out


def build_genki_method() -> Path:
    toc = [
        ("s1", "1. 数据来源", 1), ("s2", "2. 数据选择规则", 1), ("s3", "3. 筛选标准", 1),
        ("s4", "4. 代码参数", 1), ("s5", "5. 处理流程", 1), ("s6", "6. 产物代表什么", 1),
        ("s7", "7. 出图", 1), ("s8", "8. 代码怎么用", 1), ("s9", "9. 整合状态", 1),
        ("s10", "10. CUDA", 1), ("s11", "11. 声称边界", 1),
    ]
    body = [
        "<section class='hero'><h1>方法论 · GenKI</h1>",
        f"<p>对照本地 <a href='{PAPER_GENKI}'>NAR 2023 PDF</a> 的 Materials and Methods，以及 <a href='{PAPER_VGAE}'>VGAE 短文</a>。"
        "数据选择与 Knk 共用筛选规程。响应规则不借用 FDR。</p></section>",
        h2("s1", "1. 数据来源"),
        "<p>与 Knk 同一份桌面计数和注释：GSE197289 小鼠 Control 三叉神经节单核数据。不复制矩阵。"
        "不用的登录号及原因与 Knk 方法论第 1 节相同：IoN-CCI 的 bulk、CFA 单细胞、切断模型、Sp5C、大鼠、人外周血都不进这次虚拟敲除。"
        "NAR 论文自己的例子是其他公开单细胞数据里的真实敲除对照；本课题没有那些敲除样本，只使用野生型 Control，这和 GenKI「可以只有 WT」的设计一致，但不能把原文里 Trem2 等案例的生物学结论搬到三叉神经节。</p>",
        h2("s2", "2. 数据选择规则"),
        "<p>亚群、六个靶基因、检出率和「检出为 0 才不敲」与 Knk 相同，数字见筛选规程，不在这里另算一套。"
        "不同的是进入模型的基因：NAR 默认 vst 的 top 3000，本课题保持这一默认，并强制补入有检出的靶基因。Knk 不设 8000 上限、也不强制只留高变基因；两套基因集合因此不同。</p>",
        "<p>对照必须在 GenKI 这套基因上重算与 Cplx2 的相关。结果是 PEP 的 Abcc8、NF1 的 Gm15551。不要改成 Ret 或 Rdx 来和 Knk 对齐。"
        "对照与六个靶基因共用一张布尔图和一套 VGAE 权重，差别只是哪一个基因的边被去掉。</p>",
        h2("s3", "3. 筛选标准"),
        "<p><b>切片。</b>Control 且 subtype 为 PEP 或 NF1。否则不建图。</p>",
        "<p><b>能否敲。</b>符号在矩阵中且该亚群检出细胞数大于 0。Sh3d21 数量很少但仍敲。Hprt1 与 Ppia 不敲。</p>",
        "<p><b>进图的基因。</b>vst 前 3000，靶基因补入。不是高变基因的其他基因不会因为「可能有趣」被加进来。</p>",
        "<p><b>边。</b>PC 回归全连接权重里，绝对值为前 15% 的才是边。其余不是边。15% 是 NAR 的默认，不是本次搜索出来的。</p>",
        "<p><b>响应基因。</b>该次 KL 位于前 5%，并且在 1000 次不放回排列中出现超过 950 次。去掉被敲基因。这是 NAR 的排序规则在本课题里的固定写法。不使用 p.adj，也不使用距离前 50。</p>",
        "<p><b>是否做富集。</b>其他响应基因少于 5 个则不做超几何检验，写 too_few。不少于 5 个才做 GO 三个本体和 KEGG。</p>",
        "<p><b>通路。</b>每个库单独 BH，p&lt;0.05 且 q&lt;0.2。未通过的库不绘图。对照名单里也有的基因或术语不算靶特异。NF1 · Cplx2 与 Gm15551 共享 5 个基因，其中 Thbs1 落在一条通过的 KEGG 上。</p>",
        h2("s4", "4. 代码参数：取值、论文位置、改没改"),
        tbl(
            "<tr><th>参数</th><th>取值</th><th>论文或软件</th><th>本课题</th></tr>"
            "<tr><td>N_HVG</td><td>3000，vst</td><td>NAR：FindVariableFeatures 默认 top 3000</td><td>不改；靶基因另补</td></tr>"
            "<tr><td>标准化</td><td>ScaleData</td><td>NAR 方法</td><td>不改</td></tr>"
            "<tr><td>建网</td><td>PC 回归</td><td>NAR 引用 scTenifoldNet</td><td>不改成相关矩阵</td></tr>"
            "<tr><td>边阈值</td><td>绝对权重前 15%</td><td>NAR 默认；补充图讨论过其他阈值</td><td>首轮不改。改了必须重搜三项超参</td></tr>"
            "<tr><td>潜变量</td><td>2 维二元高斯</td><td>NAR 固定项；VGAE 编码器给均值和方差</td><td>不搜维数</td></tr>"
            "<tr><td>边划分</td><td>约 75/5/20，种子 42</td><td>GenKI split_data</td><td>不改</td></tr>"
            "<tr><td>学习率</td><td>10<sup>−4</sup> 到 10<sup>−1</sup>，系数 1–9</td><td>NAR 搜索项，随数据变化</td><td>各亚群自己搜</td></tr>"
            "<tr><td>beta</td><td>10<sup>−5</sup> 到 10<sup>−1</sup></td><td>NAR；其四个例子常为 1e−4</td><td>验证集选中什么用什么</td></tr>"
            "<tr><td>weight decay</td><td>10<sup>−7</sup> 到 10<sup>−3</sup></td><td>NAR；其例子常为 9e−4</td><td>同上，不手填 9e−4</td></tr>"
            "<tr><td>试验次数</td><td>100</td><td>课题按论文搜索协议</td><td>不用 README 的单次示例学习率</td></tr>"
            "<tr><td>轮数</td><td>最多 100，至少 10</td><td>课题早停，仍在论文搜索范围内</td><td>验证 AP 提高不足 0.0001 不计；15 轮无提高则停</td></tr>"
            "<tr><td>学习率衰减</td><td>停滞 5 轮 ×0.5</td><td>课题实现</td><td>最低到初始值的 1/100</td></tr>"
            "<tr><td>挑选分</td><td>验证 AP − 过拟合差距</td><td>课题；测试 AP 不参与挑选</td><td>不改</td></tr>"
            "<tr><td>排列</td><td>1000 次不放回，种子 0</td><td>课题写死。软件有放回和 100 次示例不用</td><td>不改</td></tr>"
            "<tr><td>响应</td><td>top 5% 且命中 &gt;95%</td><td>NAR / GenKI get_generank 一类规则</td><td>不改成 FDR</td></tr>"
            "<tr><td>模型种子</td><td>8096</td><td>软件示例，不是搜索项</td><td>写入 STATUS</td></tr>"
            "<tr><td>富集</td><td>BH，p=0.05，q=0.2</td><td>课题标准。NAR 正文用 Enrichr</td><td>改用 clusterProfiler，四个库都算</td></tr>"
        ),
        "<p>烟测脚本把试验、轮数和排列降到很少，只检查路径能否跑通。烟测结果不能当作本方法。</p>",
        h2("s5", "5. 处理流程：输入和输出"),
        "<p><b>导出。</b><code>01_导出亚群计数_ExportSubtype.R</code> 从共用 counts 切出 PEP 与 NF1。输出供 Python 读取，不另存一份矩阵到 GenKI 目录。</p>",
        "<p><b>建图。</b><code>genki_formal.py</code> 在 CPU 上做 top 3000、PC 回归和 15% 阈值。输出包括边、基因名和 <code>wt_graph.npz</code>。每个亚群一张图。</p>",
        "<p><b>搜索与拟合。</b>100 次随机超参。有 CUDA 则在 GPU。选出一组权重后做正式训练。STATUS 记录 beta、学习率、weight decay 和验证 AP。</p>",
        "<p><b>敲除与排列。</b>对每个靶基因和对照去掉对应的边，算 KL，再做 1000 次排列。输出在 <code>结果文件/&lt;亚群&gt;/GenKI/&lt;基因&gt;/数据文件/</code>："
        "<code>KL排序_RankKL.csv</code> 是全基因，<code>响应基因_Responsive.csv</code> 是通过规则的子集。</p>",
        "<p><b>富集。</b>有响应基因时调用 <code>04_焦点通路_EnrichResponse.R</code>，写出 <code>富集_GO.csv</code>（BP+CC+MF）和 BP 镜像 <code>富集_GOBP.csv</code>。"
        "全部基因跑完后 <code>08_KEGG富集_EnrichKEGG.R</code> 写每个基因的 <code>富集_KEGG.csv</code>。少于 5 个基因的写说明、空表。</p>",
        h2("s6", "6. 处理后的数据代表什么、怎么看"),
        "<p><code>KL排序_RankKL.csv</code> 的每一行是图上的一个基因。KL 是野生型潜变量和敲除潜变量的距离。rank 越小，KL 越大。"
        "hit 是 1000 次排列里进入前 5% 的次数，hit_fraction 是这个次数除以 1000。只看 KL 大不大不够：必须同时 hit_fraction&gt;0.95。"
        "被敲基因自己的 KL 通常极大，因为它的边没了，潜变量必然离开野生型。这个大数不解释成「它调控了自己」。</p>",
        "<p><code>响应基因_Responsive.csv</code> 已经是通过规则的基因。做富集前再核对 KO 自己是否还在表里，若在就删掉。"
        "把这张表和对照的表求交。NF1 · Cplx2 与 Gm15551 的交是 2810410L24Rik、Calca、Ces5a、Kcne4、Thbs1。交集里的基因不能支撑特异通路。</p>",
        "<p>富集 CSV 只保存通过阈值的行。GO 表用 ontology 列区分 BP、CC、MF。空表是「这个库算过且没有通过」。"
        "KEGG 的 gene_symbol 列把 Entrez 转回了基因符号，读通路时以它为准，不以通路英文名里的 disease 词为准。</p>",
        "<p>散点：横轴按 KL 的排名，纵轴是 log10(KL)，红是响应规则通过。灰点里的基因名不要写进讨论。"
        "条图只应包含其他响应基因。若一张图把 KO 自己画成最长的条，读的时候把它除外。</p>",
        h2("s7", "7. 出图"),
        "<p>论文式报告放流程示意、响应基因数、Jaccard，以及有通过富集的基因的 KL 图和对应柱图：NF1 的 Cplx2（KEGG）、Ppp1r26（GO BP）、Mitf（GO CC）。"
        "PEP · Mitf 有 9 个响应基因但没有通过的通路，正文用文字说明，不放空柱图。响应数为 0 的基因同样不放空富集图。"
        "图的空态文件可以留在基因目录，供核对脚本确实画过「无通过」。</p>",
        h2("s8", "8. 代码怎么用"),
        "<p>正式入口是 <code>GenKI_GenKI/代码文件/genki_formal.py</code>，桌面 <code>虚拟敲除/代码文件/genki_formal.py</code> 为副本。"
        "它按 PEP 再 NF1 的顺序：导出、建图、搜索、拟合、排列、GO，最后批处理 KEGG。"
        "数据和结果路径目前写在脚本里的桌面常量，还不是 Knk 那种只改两个路径的配置文件。换目录要改脚本常量并在 STATUS 里记一笔。</p>",
        "<pre>cd GenKI_GenKI\\代码文件\n"
        "E:\\Python3.13.14\\python.exe genki_formal.py\n\n"
        "E:\\R-4.6.0\\bin\\Rscript.exe --encoding=UTF-8 04b_批处理GO_BPCCMF.R\n"
        "E:\\R-4.6.0\\bin\\Rscript.exe --encoding=UTF-8 08_KEGG富集_EnrichKEGG.R\n\n"
        "E:\\Python3.13.14\\python.exe 10_方法示意图_GenKIVgaeSchematic.py</pre>",
        "<p>开跑前可以先运行 <code>00_资源上限_CpuCap.py</code>，它只打印这次分到的线程、内存和显存，不加载模型。"
        "内存给系统留物理内存的 25%（最少 4 GB，最多 8 GB）。显卡若在输出桌面，显存留 15%（最少 0.5 GB，最多 1.5 GB）。"
        "建图不用 GPU。搜索时同时进行的 trial 数受剩余显存（每份至少约 1 GB）和线程限制。正式训练和 1000 次排列用一个进程。</p>",
        h2("s9", "9. 整合状态"),
        "<p>科学步骤已经在 <code>genki_formal.py</code> 里串起来：一张亚群网、一套权重、多个基因分别去边、GO 与 KEGG 都有官方阈值。"
        "现行 PEP/NF1 结果就是这条正式路径，不是烟测。</p>",
        "<p>还没有做成和 Knk 完全相同的单目录一键包。路径、Rscript 位置写在 Python 常量里。HTML 报告不在 genki_formal 结束时自动生成，要另跑本脚本。"
        "因此「流程能复现当前结果」成立，「换一台机器只改 DATA_DIR 和 RESULT_DIR」对 GenKI 尚不成立。</p>",
        h2("s10", "10. CUDA"),
        "<p>使用 CUDA 的部分：超参数搜索和最终拟合。代码在 <code>torch.cuda.is_available()</code> 时执行 <code>model.to(cuda)</code>，训练、验证、测试图一并 <code>.to(cuda)</code>。"
        "本机正式日志应以 <code>fit_device=cuda</code> 为准。每一轮进度也可以看到设备名。</p>",
        "<p>不使用 CUDA 的部分：高变基因和 PC 回归建图；排列用的细胞下标在 CPU 上生成。编码时把图送到模型所在设备。"
        "没有 GPU 时训练改到 CPU，15% 边、100 次搜索和 95% 命中不变。"
        "不要把 Knk 的建网 SVD 和 GenKI 的 VGAE 训练说成同一种 GPU 用法。</p>",
        h2("s11", "11. 声称边界"),
        "<p class='note'>方法名称是 GenKI / VGAE 虚拟敲除（Yang 等，2023）。不是 scTenifoldKnk，也不在这篇里宣称优于 Knk。"
        "响应基因不是差异表达基因。GSE197289 Control 不是慢性三叉神经痛模型。对照共享的基因和含有这些基因的通路不具靶基因特异性。"
        "KEGG 癌症地图名不是肿瘤结论。注释软件是 clusterProfiler，不是论文里的 Enrichr。</p>",
    ]
    out = OUT / "方法论报告_GenKI.html"
    out.write_text(shell("方法论 GenKI", "GenKI 方法论", "11 节，对照 NAR PDF", toc, body), encoding="utf-8")
    return out


def build_index(paths: list[Path]) -> Path:
    items = "".join(f"<li><a href='{p.name}'>{esc(p.stem)}</a></li>" for p in paths)
    body = [
        h2("top", "报告"),
        "<p>论文式报告按本地 PDF 的章节写：Knk 用 Result 分节，GenKI 用 NAR 的 Abstract 到 Discussion。"
        "方法论每篇 11 节。没有通过筛选的富集图不在论文正文里。</p>",
        f"<ul>{items}</ul>",
        f"<p>文献：<a href='{PAPER_GENKI}'>GenKI NAR 2023</a>，<a href='{PAPER_VGAE}'>VGAE</a>，"
        f"<a href='{PAPER_KNK}'>scTenifoldKnk 方法学 PDF</a>。</p>",
    ]
    out = OUT / "index_报告入口.html"
    out.write_text(shell("报告入口", "报告入口", "按本地论文重写", [("top", "文件", 1)], body), encoding="utf-8")
    return out


def main() -> None:
    outs = [build_knk_paper(), build_genki_paper(), build_knk_method(), build_genki_method()]
    idx = build_index(outs)
    print("REPORTS_DONE")
    for p in [idx, *outs]:
        print(p, p.stat().st_size)


if __name__ == "__main__":
    main()
