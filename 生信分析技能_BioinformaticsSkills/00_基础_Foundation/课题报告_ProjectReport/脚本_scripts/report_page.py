# -*- coding: utf-8 -*-
"""课题终局 HTML 外壳。生成报告时调用 page() / figure_blocks()，不要另写顶栏窄页。"""
from __future__ import annotations

import html
import re
from typing import Sequence

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
figure{margin:1rem 0 .55rem;background:#fffdf8;border:1px solid #ddd4c4;border-radius:.8rem;padding:.7rem}
figure img{width:100%;max-width:100%;height:auto;display:block}
figcaption{margin-top:.55rem;background:#f6f3ec;border-left:.25rem solid #2f5d4c;padding:.55rem .7rem;border-radius:.4rem;font-size:.95rem}
.fig-panel{display:grid;gap:.7rem;margin:0 0 1.75rem}
.fig-block{border:1px solid #ddd4c4;border-radius:.75rem;padding:.8rem .95rem;background:#fff}
.fig-block h4{margin:0 0 .5rem;font-size:.98rem;line-height:1.35;color:#1c241f}
.fig-block p{margin:.4rem 0}
.fig-block ul,.fig-block ol{margin:.35rem 0 .25rem 1.15rem;padding:0}
.fig-block li{margin:.2rem 0}
.fig-block.setup{border-left:.3rem solid #7A8B9A;background:#f5f7f9}
.fig-block.findings{border-left:.3rem solid #5B8FA8;background:#f4f8fb}
.fig-block.takeaway{border-left:.3rem solid #6B8F71;background:#f3f8f4}
.fig-block.boundary{border-left:.3rem solid #C17B7B;background:#fbf5f5}
.fig-block.legend{border-left:.3rem solid #5B8FA8;background:#f4f8fb}
.fig-block.protocol{border-left:.3rem solid #D4A574;background:#fbf7f0}
.fig-block.params{border-left:.3rem solid #8B7BA8;background:#f7f5fa}
.fig-block.pitfall{border-left:.3rem solid #C17B7B;background:#fbf5f5}
.fig-block.chain{border-left:.3rem solid #6E7F8D;background:#f6f7f8}
/* 兼容旧块名（迁移期） */
.fig-block.result{border-left:.3rem solid #5B8FA8;background:#f4f8fb}
.fig-block.meaning{border-left:.3rem solid #6B8F71;background:#f3f8f4}
.fig-block.provenance{border-left:.3rem solid #D4A574;background:#fbf7f0}
.fig-block.read{border-left:.3rem solid #7A8B9A;background:#f5f7f9}
.fig-block.misread{border-left:.3rem solid #C17B7B;background:#fbf5f5}
.fig-block .tag{display:inline-block;font-size:.72rem;font-weight:700;letter-spacing:.02em;padding:.08rem .45rem;border-radius:999px;margin-right:.35rem;vertical-align:middle}
.fig-block.setup .tag,.fig-block.read .tag{background:#dde3e8;color:#3a4650}
.fig-block.findings .tag,.fig-block.legend .tag,.fig-block.result .tag{background:#d7e8f0;color:#2a4d5c}
.fig-block.takeaway .tag,.fig-block.meaning .tag{background:#d9eadc;color:#2f5d4c}
.fig-block.boundary .tag,.fig-block.pitfall .tag,.fig-block.misread .tag{background:#f0d9d9;color:#6a3a3a}
.fig-block.protocol .tag,.fig-block.provenance .tag{background:#f0e2cc;color:#6a4e28}
.fig-block.params .tag,.fig-block.chain .tag{background:#e4dceb;color:#4a3d5c}
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

REQUIRED = {
    "paper": [
        "abs", "question", "design", "discussion", "limits", "methods-brief",
    ],
    "method": [
        "declare", "route", "thresholds", "scripts", "qc", "guide", "division",
    ],
    "index": [],
}

# 每图强制块（与报告要求 §3.3 对齐；高分刊 Results/Methods 分区）
REQUIRED_FIG_BLOCKS = {
    "paper": ("setup", "findings", "takeaway", "boundary"),
    "method": ("legend", "protocol", "params", "pitfall"),
}

ALLOWED_BLOCK_KINDS = {
    "setup",
    "findings",
    "takeaway",
    "boundary",
    "legend",
    "protocol",
    "params",
    "pitfall",
    "chain",
    # 旧名保留校验通过前的迁移调用
    "result",
    "meaning",
    "provenance",
    "read",
    "misread",
}


def page(title: str, side_title: str, side_sub: str, nav: list[tuple[str, str]], body: str) -> str:
    nav_html = "".join(
        f"<a href='#{hid}'>{html.escape(txt)}</a>" for hid, txt in nav
    )
    return (
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'/>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'/>"
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
        f"<div class='layout'><aside class='sidebar'><h1>{html.escape(side_title)}</h1>"
        f"<div class='sub'>{html.escape(side_sub)}</div>{nav_html}</aside>"
        f"<main class='main'>{body}</main></div><script>{JS}</script></body></html>"
    )


def _as_body_html(body: str | Sequence[str]) -> str:
    """纯文本 → <p>；已含 HTML 标签则原样拼接（调用方负责转义）。"""
    if isinstance(body, (list, tuple)):
        parts = []
        for item in body:
            s = str(item).strip()
            if not s:
                continue
            if s.startswith("<"):
                parts.append(s)
            else:
                parts.append(f"<p>{html.escape(s)}</p>")
        return "".join(parts)
    s = str(body).strip()
    if s.startswith("<"):
        return s
    # 多段用空行分开
    paras = [p.strip() for p in re.split(r"\n\s*\n", s) if p.strip()]
    if not paras:
        return f"<p>{html.escape(s)}</p>"
    return "".join(f"<p>{html.escape(p)}</p>" for p in paras)


def figure_blocks(
    src: str,
    caption: str,
    blocks: Sequence[dict],
) -> str:
    """相对路径图 + 图注 + 分块分析。

    blocks: 每项 {"kind": "result"|"meaning"|"provenance"|"read"|"misread"|"chain",
                  "title": str, "body": str | list[str]}
    body 为纯文本时自动转义并包 <p>；若以 < 开头则视为已构造的安全 HTML 片段。
    """
    if len(blocks) < 4:
        raise ValueError("figure_blocks requires >= 4 blocks (paper/method §3.3)")
    panel_parts = []
    for b in blocks:
        kind = str(b.get("kind", "")).strip()
        if kind not in ALLOWED_BLOCK_KINDS:
            raise ValueError(f"unknown fig block kind: {kind}")
        title = str(b.get("title", "")).strip() or kind
        body = _as_body_html(b.get("body", ""))
        panel_parts.append(
            f"<section class='fig-block {html.escape(kind)}'>"
            f"<h4><span class='tag'>{html.escape(kind)}</span>{html.escape(title)}</h4>"
            f"{body}</section>"
        )
    return (
        f"<figure><img src='{html.escape(src, quote=True)}' alt=''/>"
        f"<figcaption>{html.escape(caption)}</figcaption></figure>"
        f"<div class='fig-panel'>{''.join(panel_parts)}</div>"
    )


def figure(src: str, caption: str, analysis: str) -> str:
    """兼容旧调用：请改用 figure_blocks（论文式 4 块 / 方法论 4 块）。"""
    return figure_blocks(
        src,
        caption,
        [
            {"kind": "setup", "title": "问题与设计要点", "body": analysis},
            {"kind": "findings", "title": "主要发现", "body": "（请改为 figure_blocks）"},
            {"kind": "takeaway", "title": "直接解读", "body": "（请改为 figure_blocks）"},
            {"kind": "boundary", "title": "边界（不能证明什么）", "body": "（请改为 figure_blocks）"},
        ],
    )


# 图块推诿 / 过度甩锅（§3.3.0）
_FIG_HANDOFF_PAT = re.compile(
    r"(见方法论同图|见 protocol/params|详见脚本|不在论文式展开|"
    r"不在此处展开|细节阈值与脚本名见|参数见脚本|可复现步骤见方法论|"
    r"设计要点见本课题|见方法论。)",
    re.I,
)


def _plain_len(html_frag: str) -> int:
    t = re.sub(r"<[^>]+>", "", html_frag)
    t = re.sub(r"\s+", "", t)
    return len(t)


def check_html(text: str, kind: str, forbidden: str = "") -> None:
    """缺侧栏、缺必写章节、图后无分块、绝对路径或禁词 → 失败。"""
    if "class='sidebar'" not in text and 'class="sidebar"' not in text:
        raise SystemExit(f"{kind}: page is not the sidebar shell")
    if "IntersectionObserver" not in text:
        raise SystemExit(f"{kind}: sidebar has no section observer")
    for hid in REQUIRED[kind]:
        if f"id='{hid}'" not in text and f'id="{hid}"' not in text:
            raise SystemExit(f"{kind}: missing section #{hid}")
    if kind in {"paper", "method"}:
        if "<img " not in text:
            raise SystemExit(f"{kind}: no embedded figure")
        if re.search(r"</figure>\s*(?!<div class='fig-panel'>|<div class=\"fig-panel\">)", text):
            raise SystemExit(f"{kind}: a figure is not followed by fig-panel blocks")
        if re.search(r"<h2[^>]*>\s*图\s*</h2>", text):
            raise SystemExit(f"{kind}: figures are dumped under one heading")
        n_fig = len(re.findall(r"<figure>", text))
        n_panel = len(re.findall(r"class='fig-panel'|class=\"fig-panel\"", text))
        if n_fig != n_panel:
            raise SystemExit(f"{kind}: figure/panel count mismatch ({n_fig} vs {n_panel})")
        for req in REQUIRED_FIG_BLOCKS[kind]:
            n_blk = len(re.findall(rf"fig-block {re.escape(req)}", text))
            if n_blk < n_fig:
                raise SystemExit(
                    f"{kind}: missing fig-block '{req}' on some figures ({n_blk}/{n_fig})"
                )
        # 充实度：禁止推诿句；每块汉字过短则失败
        m = _FIG_HANDOFF_PAT.search(text)
        if m:
            raise SystemExit(f"{kind}: fig-block handoff wording forbidden: {m.group(0)}")
        for blk in re.finditer(
            r"<section class='fig-block [^']+'>(.*?)</section>", text, flags=re.S
        ):
            body = blk.group(1)
            # 标题 h4 后正文
            after = re.split(r"</h4>", body, maxsplit=1)
            content = after[1] if len(after) > 1 else body
            if _plain_len(content) < 80:
                raise SystemExit(f"{kind}: a fig-block is too short (<80 chars plain text)")
    if kind == "paper" and "id='r-" not in text and 'id="r-' not in text:
        raise SystemExit(f"{kind}: no result section")
    if forbidden and forbidden in text:
        raise SystemExit(f"{kind}: forbidden wording")
    if re.search(r"[A-Za-z]:[\\/]", text):
        raise SystemExit(f"{kind}: absolute drive path in HTML")
