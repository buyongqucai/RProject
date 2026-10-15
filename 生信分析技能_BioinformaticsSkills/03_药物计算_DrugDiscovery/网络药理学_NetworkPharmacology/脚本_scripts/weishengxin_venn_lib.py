# -*- coding: utf-8 -*-
"""微生信韦恩模板库（网药 FROZEN §G）。

几何与配色来自 `01_样例_sample/参考_交付原图/Venn_*.svg`。
项目侧只传入基因集合并指定输出路径；禁止另写 VennDiagram/R 近似顶替交付。
"""
from __future__ import annotations

import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_REF = SKILL_ROOT / "01_样例_sample" / "参考_交付原图"

CHROME_CANDIDATES = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]
CHROME = next((p for p in CHROME_CANDIDATES if p.exists()), None)

COL = {
    "TTD": (0, 102, 0),
    "DrugBank": (90, 155, 212),
    "GeneCards": (241, 90, 96),
    "OMIM": (207, 207, 27),
    "Drugs": (0, 102, 0),
    "Disease": (90, 155, 212),
    "share": (156, 106, 156),
}


def rgb(c: tuple[int, int, int]) -> str:
    return f"rgb({c[0]},{c[1]},{c[2]})"


def _as_set(genes) -> set[str]:
    return {str(g).strip() for g in genes if str(g).strip() and str(g).strip().lower() != "nan"}


def text(x, y, s, *, size="19px", weight="700", fill="#000", opacity=1, anchor="middle", fs=None):
    size_attr = f'font-size="{fs}"' if fs else f'font-size="{size}"'
    return (
        f'<text fill="{fill}" fill-opacity="{opacity}" stroke="none" font-family="Arial" '
        f'{size_attr} font-style="normal" font-weight="{weight}" text-decoration="none" '
        f'x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="alphabetic">{s}</text>'
    )


def bar_rect(x0, x1, y_top, y_bottom, color, opacity=0.5):
    c = rgb(color)
    return (
        f'<path fill="{c}" stroke="{c}" d="M {x0} {y_top} L {x1} {y_top} L {x1} {y_bottom} '
        f'L {x0} {y_bottom} L {x0} {y_top} Z Z" stroke-miterlimit="10" stroke-width="0.75" '
        f'fill-opacity="{opacity}"></path>'
    )


def region_counts_4(sets: dict[str, set[str]], order: list[str]) -> dict[int, int]:
    bits = {n: 1 << i for i, n in enumerate(order)}
    mem: Counter[int] = Counter()
    for g in set().union(*sets.values()):
        m = 0
        for n in order:
            if g in sets[n]:
                m |= bits[n]
        mem[m] += 1
    return dict(mem)


def build_disease_4db_svg(sets: dict[str, set[str]]) -> str:
    """Four-set disease Venn (TTD / DrugBank / GeneCards / OMIM geometry)."""
    order = ["TTD", "DrugBank", "GeneCards", "OMIM"]
    for k in order:
        sets.setdefault(k, set())
    mem = region_counts_4(sets, order)
    r = lambda m: int(mem.get(m, 0))
    sizes = {k: len(sets[k]) for k in order}
    ymax = max(sizes.values()) or 1
    y_base, y_top_axis = 535.0, 450.0
    h_max = y_base - y_top_axis

    def bar_y(n: int) -> float:
        return y_base - (n / ymax) * h_max

    tmpl = SAMPLE_REF.joinpath("Venn_DiseaseDatabases.svg").read_text(encoding="utf-8")
    m = re.search(
        r'(<g transform="translate\(181,238\).*?</g><path fill="none".*?'
        r'<g transform="translate\(320,238\).*?</g>)',
        tmpl,
    )
    if not m:
        parts = re.findall(
            r'<path fill="none" stroke="none"></path><g transform="translate\([^"]+"[^>]*>.*?</g>',
            tmpl,
        )
        ellipse_block = "".join(parts[:4])
    else:
        ellipse_block = m.group(1)

    labels = [
        (60, 204, r(1)),
        (145, 74, r(2)),
        (332, 74, r(4)),
        (435, 204, r(8)),
        (110, 134, r(3)),
        (250, 104, r(6)),
        (390, 134, r(12)),
        (133, 274, r(5)),
        (370, 274, r(10)),
        (250, 354, r(9)),
        (165, 184, r(7)),
        (335, 184, r(14)),
        (185, 304, r(13)),
        (315, 304, r(11)),
        (250, 234, r(15)),
    ]
    label_txt = [text(x, y, str(n), weight="700" if n else "400") for x, y, n in labels]
    names = [
        (25, 84, "TTD", COL["TTD"]),
        (105, 19, "DrugBank", COL["DrugBank"]),
        (370, 19, "GeneCards", COL["GeneCards"]),
        (448, 84, "OMIM", COL["OMIM"]),
    ]
    name_txt = [
        text(x, y, lab, size="14px", weight="400", fill=rgb(c), opacity=0.5)
        for x, y, lab, c in names
    ]
    slots = [
        ("TTD", 70, 142.5, 106.25),
        ("DrugBank", 162.5, 235, 198.75),
        ("GeneCards", 255, 327.5, 291.25),
        ("OMIM", 347.5, 420, 383.75),
    ]
    bars = []
    for name, x0, x1, xc in slots:
        n = sizes[name]
        yt = bar_y(n)
        bars.append(bar_rect(x0, x1, yt, y_base, COL[name]))
        if n / ymax > 0.15:
            bars.append(
                text(x1 - 5, yt + 15, str(n), size="8pt", weight="normal", fill="white", fs="8pt", anchor="end")
            )
        else:
            bars.append(
                text(
                    x1 - 5,
                    yt - 10,
                    str(n),
                    size="8pt",
                    weight="normal",
                    fill=rgb(COL[name]),
                    opacity=0.5,
                    fs="8pt",
                    anchor="end",
                )
            )
        bars.append(text(xc, 550 if name in ("TTD", "GeneCards") else 560, name, size="8pt", weight="normal", fs="8pt"))
        bars.append(
            f'<path fill="none" stroke="rgb(0,0,0)" d="M {xc} 535 L {xc} 540 Z" '
            f'stroke-opacity="0.7" stroke-miterlimit="10" stroke-width="0.4"></path>'
        )

    axis = (
        f'{text(45, 537, "0", size="8pt", weight="normal", fs="8pt", anchor="end")}'
        f'{text(45, 502.5, str(int(round(ymax / 2))), size="8pt", weight="normal", fs="8pt", anchor="end")}'
        f'{text(45, 469, str(ymax), size="8pt", weight="normal", fs="8pt", anchor="end")}'
        '<path fill="none" stroke="rgb(0,0,0)" d="M 50 535 L 50 450 Z" stroke-opacity="0.7" stroke-miterlimit="10"></path>'
        '<path fill="none" stroke="rgb(0,0,0)" d="M 50 535 L 450 535 Z" stroke-opacity="0.7" stroke-miterlimit="10"></path>'
        '<path fill="none" stroke="rgb(0,0,0)" d="M 47 499 L 53 499 Z" stroke-opacity="0.7" stroke-miterlimit="10" stroke-width="0.4"></path>'
        '<path fill="none" stroke="rgb(0,0,0)" d="M 47 465 L 53 465 Z" stroke-opacity="0.7" stroke-miterlimit="10" stroke-width="0.4"></path>'
        '<g><path fill="rgb(0,0,0)" stroke="none" d="M 50 440 L 46 450 L 54 450" fill-opacity="0.7"></path></g>'
        '<g><path fill="rgb(0,0,0)" stroke="none" d="M 460 535 L 450 531 L 450 539" fill-opacity="0.7"></path></g>'
    )

    n1 = sum(v for k, v in mem.items() if bin(k).count("1") == 1)
    n2 = sum(v for k, v in mem.items() if bin(k).count("1") == 2)
    n3 = sum(v for k, v in mem.items() if bin(k).count("1") == 3)
    n4 = sum(v for k, v in mem.items() if bin(k).count("1") == 4)
    total = max(n1 + n2 + n3 + n4, 1)
    x0, x1 = 60.0, 450.0
    w = x1 - x0
    segs = [(2, n2), (1, n1)]
    share = []
    cx = x0
    for k, n in segs:
        if n <= 0:
            continue
        ww = max(w * n / total, 2.0)
        share.append(bar_rect(cx, cx + ww, 600, 620, COL["share"], opacity=0.4 if k == 2 else 0.666))
        mid = cx + ww / 2
        if k == 2:
            share.append(text(mid, 642, str(k), size="8pt", weight="normal", fs="8pt"))
            share.append(text(mid + 6, 642, f"({n})", size="8pt", weight="normal", fs="8pt", anchor="start"))
        else:
            share.append(text(mid, 614, str(n), size="8pt", weight="normal", fill="white", fs="8pt"))
            share.append(text(mid, 654, str(k), size="8pt", weight="normal", fs="8pt"))
        share.append(
            f'<path fill="none" stroke="rgb(0,0,0)" d="M {mid} 625 L {mid} 630 Z" '
            f'stroke-opacity="0.7" stroke-miterlimit="10" stroke-width="0.4"></path>'
        )
        cx += ww
    share.append(
        '<path fill="none" stroke="rgb(0,0,0)" d="M 50 625 L 460 625 Z" stroke-opacity="0.7" stroke-miterlimit="10"></path>'
    )

    title_size = text(250, 442, "Size of each list", size="10pt", weight="normal", fs="10pt").replace(
        'font-style="normal"', 'font-style="italic"'
    )
    title_share = text(
        250,
        585,
        "Number of elements: specific (1) or shared by 2, 3, ... lists",
        size="10pt",
        weight="normal",
        fs="10pt",
    ).replace('font-style="normal"', 'font-style="italic"')

    return (
        f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" width="500" height="695">'
        f"<defs></defs><g>{ellipse_block}"
        f"{title_size}{axis}{''.join(bars)}{title_share}{''.join(share)}"
        f"{''.join(label_txt)}{''.join(name_txt)}</g></svg>"
    )


def build_two_set_svg(
    set_a,
    set_b,
    name_a: str = "Drugs",
    name_b: str = "Disease",
    col_a: tuple[int, int, int] | None = None,
    col_b: tuple[int, int, int] | None = None,
) -> str:
    """Two-set Venn from Venn_DrugDisease.svg geometry (微生信)."""
    a = _as_set(set_a)
    b = _as_set(set_b)
    ca = col_a or COL["Drugs"]
    cb = col_b or COL["Disease"]
    only_a = len(a - b)
    only_b = len(b - a)
    inter = len(a & b)
    n_a, n_b = len(a), len(b)
    n1, n2 = only_a + only_b, inter
    # 轴顶留空，避免柱顶数字与 Y 轴刻度（ymax）重叠
    ymax = max(int(round(max(n_a, n_b, 1) * 1.12)), max(n_a, n_b, 1) + 1)
    y_base, y_top_axis = 535.0, 450.0
    h_max = y_base - y_top_axis

    def bar_y(n: int) -> float:
        return y_base - (n / ymax) * h_max

    tmpl = SAMPLE_REF.joinpath("Venn_DrugDisease.svg").read_text(encoding="utf-8")
    parts = re.findall(
        r'<path fill="none" stroke="none"></path><g transform="translate\([^"]+"[^>]*>.*?</g>',
        tmpl,
    )
    ellipse_block = "".join(parts[:2])

    labels = [
        text(123, 209, str(only_a)),
        text(357, 209, str(only_b)),
        text(251, 209, str(inter)),
    ]
    names = [
        text(115, 54, name_a, size="14px", weight="400", fill=rgb(ca), opacity=0.5),
        text(380, 54, name_b, size="14px", weight="400", fill=rgb(cb), opacity=0.5),
    ]

    bars = []
    yt = bar_y(n_a)
    bars.append(bar_rect(70, 235, yt, y_base, ca))
    bars.append(
        text(230, yt - 10, str(n_a), size="8pt", weight="normal", fill=rgb(ca), opacity=0.5, fs="8pt", anchor="end")
        if n_a / ymax < 0.15
        else text(230, yt + 15, str(n_a), size="8pt", weight="normal", fill="white", fs="8pt", anchor="end")
    )
    bars.append(text(152.5, 550, name_a, size="8pt", weight="normal", fs="8pt"))
    bars.append(
        '<path fill="none" stroke="rgb(0,0,0)" d="M 152.5 535 L 152.5 540 Z" '
        'stroke-opacity="0.7" stroke-miterlimit="10" stroke-width="0.4"></path>'
    )
    yt2 = bar_y(n_b)
    bars.append(bar_rect(255, 420, yt2, y_base, cb))
    bars.append(text(415, yt2 + 15, str(n_b), size="8pt", weight="normal", fill="white", fs="8pt", anchor="end"))
    bars.append(text(337.5, 550, name_b, size="8pt", weight="normal", fs="8pt"))
    bars.append(
        '<path fill="none" stroke="rgb(0,0,0)" d="M 337.5 535 L 337.5 540 Z" '
        'stroke-opacity="0.7" stroke-miterlimit="10" stroke-width="0.4"></path>'
    )

    axis = (
        f'{text(45, 537, "0", size="8pt", weight="normal", fs="8pt", anchor="end")}'
        f'{text(45, 502.5, str(int(round(ymax / 2))), size="8pt", weight="normal", fs="8pt", anchor="end")}'
        f'{text(45, 469, str(ymax), size="8pt", weight="normal", fs="8pt", anchor="end")}'
        '<path fill="none" stroke="rgb(0,0,0)" d="M 50 535 L 50 450 Z" stroke-opacity="0.7" stroke-miterlimit="10"></path>'
        '<path fill="none" stroke="rgb(0,0,0)" d="M 50 535 L 450 535 Z" stroke-opacity="0.7" stroke-miterlimit="10"></path>'
        '<path fill="none" stroke="rgb(0,0,0)" d="M 47 499 L 53 499 Z" stroke-opacity="0.7" stroke-miterlimit="10" stroke-width="0.4"></path>'
        '<path fill="none" stroke="rgb(0,0,0)" d="M 47 465 L 53 465 Z" stroke-opacity="0.7" stroke-miterlimit="10" stroke-width="0.4"></path>'
        '<g><path fill="rgb(0,0,0)" stroke="none" d="M 50 440 L 46 450 L 54 450" fill-opacity="0.7"></path></g>'
        '<g><path fill="rgb(0,0,0)" stroke="none" d="M 460 535 L 450 531 L 450 539" fill-opacity="0.7"></path></g>'
    )

    total = max(n1 + n2, 1)
    x0, x1 = 60.0, 450.0
    w = x1 - x0
    share = []
    w2 = max(w * n2 / total, 4.0)
    w1 = w - w2
    share.append(bar_rect(x0, x0 + w2, 600, 620, COL["share"], opacity=0.4))
    mid2 = x0 + w2 / 2
    share.append(text(mid2, 642, "2", size="8pt", weight="normal", fs="8pt"))
    share.append(text(mid2 + 6, 642, f"({n2})", size="8pt", weight="normal", fs="8pt", anchor="start"))
    share.append(
        f'<path fill="none" stroke="rgb(0,0,0)" d="M {mid2} 625 L {mid2} 630 Z" '
        f'stroke-opacity="0.7" stroke-miterlimit="10" stroke-width="0.4"></path>'
    )
    share.append(bar_rect(x0 + w2, x0 + w2 + w1, 600, 620, COL["share"], opacity=0.666))
    mid1 = x0 + w2 + w1 / 2
    share.append(text(mid1, 614, str(n1), size="8pt", weight="normal", fill="white", fs="8pt"))
    share.append(text(mid1, 654, "1", size="8pt", weight="normal", fs="8pt"))
    share.append(
        f'<path fill="none" stroke="rgb(0,0,0)" d="M {mid1} 625 L {mid1} 630 Z" '
        f'stroke-opacity="0.7" stroke-miterlimit="10" stroke-width="0.4"></path>'
    )
    share.append(
        '<path fill="none" stroke="rgb(0,0,0)" d="M 50 625 L 460 625 Z" stroke-opacity="0.7" stroke-miterlimit="10"></path>'
    )

    title_size = text(250, 442, "Size of each list", size="10pt", weight="normal", fs="10pt").replace(
        'font-style="normal"', 'font-style="italic"'
    )
    title_share = text(
        250,
        585,
        "Number of elements: specific (1) or shared by 2, 3, ... lists",
        size="10pt",
        weight="normal",
        fs="10pt",
    ).replace('font-style="normal"', 'font-style="italic"')

    return (
        f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" width="500" height="695">'
        f"<defs></defs><g>{ellipse_block}{title_size}{axis}{''.join(bars)}"
        f"{title_share}{''.join(share)}{''.join(labels)}{''.join(names)}</g></svg>"
    )


def rasterize(svg: Path, png: Path) -> None:
    if CHROME is None:
        raise SystemExit("No Chrome/Edge found for headless screenshot")
    html = svg.with_suffix(".preview.html")
    html.write_text(
        "<!DOCTYPE html><html><head><meta charset=utf-8>"
        "<style>html,body{margin:0;padding:0;background:#fff;}"
        "svg{display:block;width:500px;height:695px;}</style>"
        f"</head><body>{svg.read_text(encoding='utf-8')}</body></html>",
        encoding="utf-8",
    )
    cmd = [
        str(CHROME),
        "--headless=new",
        "--disable-gpu",
        f"--screenshot={png}",
        "--window-size=520,720",
        "--hide-scrollbars",
        "--force-device-scale-factor=2",
        html.resolve().as_uri(),
    ]
    subprocess.run(cmd, capture_output=True, check=False)
    html.unlink(missing_ok=True)
    if not png.exists() or png.stat().st_size < 1000:
        raise SystemExit(f"rasterize failed: {png}")
    from PIL import Image, ImageChops

    im = Image.open(png)
    rgb_im = im.convert("RGB")
    bg = Image.new("RGB", rgb_im.size, (255, 255, 255))
    diff = ImageChops.difference(rgb_im, bg)
    gray = diff.convert("L").point(lambda p: 255 if p > 5 else 0)
    bbox = gray.getbbox()
    if bbox:
        pad = 16
        l, t, r, b = bbox
        im = im.crop(
            (
                max(0, l - pad),
                max(0, t - pad),
                min(rgb_im.width, r + pad),
                min(rgb_im.height, b + pad),
            )
        )
        im.save(png, optimize=True)


def write_venn_pair(svg_text: str, out_dir: Path, stem: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    svg_path = out_dir / f"{stem}.svg"
    png_path = out_dir / f"{stem}.png"
    svg_path.write_text(svg_text, encoding="utf-8")
    rasterize(svg_path, png_path)
    return svg_path, png_path
