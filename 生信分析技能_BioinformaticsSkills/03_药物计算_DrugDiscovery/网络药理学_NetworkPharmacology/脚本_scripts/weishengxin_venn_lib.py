# -*- coding: utf-8 -*-
"""本地复刻的微生信 jvenn。默认入口是 `render_replica_svg`。

复刻页：`_jvenn_assets/jvenn_runner.html`（同目录 jquery、canvas2svg、jvenn.min.js）。
不要用 R 的 VennDiagram，也不要打开微生信网站。
`render_jvenn_svg` 只在用户点名「用网站」时调用。

引用：Bardou et al. BMC Bioinformatics 2014, 15:293
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_REF = SKILL_ROOT / "01_样例_sample" / "参考_交付原图"
JVENN_ASSETS = Path(__file__).resolve().parent / "_jvenn_assets"

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
    "CTD": (243, 146, 60),
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


# 微生信 jvenn 默认色序（example.html colorDefault）
JVENN_COLORS = ["#006600", "#5a9bd4", "#f15a60", "#cfcf1b", "#ff7500", "#c09853"]


JVENN_EXAMPLE_URL = "https://bioinformatics.com.cn/static/others/jvenn/example.html"

_EXPORT_SVG_JS = r"""
function F(s,e,t,l,r,c,o,i,u){
  if(u){e=parseInt(String(e).replace('px',''))+20;t=parseInt(String(t).replace('px',''))+14;}
  else{e=parseInt(String(e).replace('px',''))+5;t=parseInt(String(t).replace('px',''))+14;}
  return '<text fill="'+l+'" fill-opacity="'+r+'" stroke="none" font-family="'+c+
    '" font-size="'+o+'" font-style="normal" font-weight="'+i+
    '" text-decoration="none" x="'+e+'" y="'+t+
    '" text-anchor="middle" dominant-baseline="alphabetic">'+s+'</text>';
}
const $ = jQuery;
const wrap = $('<div></div>');
const svg = $('#jvenn-container svg').first();
if(!svg.length) return null;
wrap.append(svg.clone());
$('[id^=resultC]').each(function(){
  if($(this).css('display')==='none') return;
  const value = (0===String($(this).html()).indexOf('<span')) ? '?' : $(this).text();
  if(!value) return;
  wrap.children('svg').children('g').append($(F(
    value,$(this).css('left'),$(this).css('top'),$(this).css('color'),$(this).css('opacity'),
    $(this).css('font-family'),$(this).css('font-size'),$(this).css('font-weight'),false
  )));
});
$('[id^=label]').each(function(){
  const html=$(this).text(); if(!html) return;
  wrap.children('svg').children('g').append($(F(
    html,$(this).css('left'),$(this).css('top'),$(this).css('color'),$(this).css('opacity'),
    $(this).css('font-family'),$(this).css('font-size'),$(this).css('font-weight'),true
  )));
});
let serialized = wrap.html();
if(serialized.indexOf('xmlns=')<0){
  serialized = serialized.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"');
}
return serialized;
"""


def expand_svg_canvas(svg: str, pad_x: int = 160, pad_y: int = 36) -> str:
    """把视口向外扩，使画在边缘、text-anchor=middle 的集合名完整落在画面内。"""
    mw = re.search(r'\bwidth="([\d.]+)', svg)
    mh = re.search(r'\bheight="([\d.]+)', svg)
    width = float(mw.group(1)) if mw else 500.0
    height = float(mh.group(1)) if mh else 695.0
    new_w = width + 2 * pad_x
    new_h = height + 2 * pad_y
    view = f'viewBox="-{pad_x} -{pad_y} {new_w:.0f} {new_h:.0f}"'
    if mw:
        svg = svg.replace(mw.group(0), f'width="{new_w:.0f}', 1)
    if mh:
        svg = svg.replace(mh.group(0), f'height="{new_h:.0f}', 1)
    if re.search(r"\bviewBox=", svg):
        svg = re.sub(r'\bviewBox="[^"]*"', view, svg, count=1)
    else:
        svg = svg.replace("<svg", f"<svg {view}", 1)
    return svg


def render_replica_svg(
    series: list[dict],
    *,
    colors: list[str] | None = None,
    display_mode: str = "classic",
    timeout_s: float = 90.0,
) -> str:
    """用本地 HTML 复刻页出 SVG。series 项为 {name, data}。空列表也要传入。"""
    runner = JVENN_ASSETS / "jvenn_runner.html"
    if not runner.exists():
        raise SystemExit(f"missing local jvenn replica: {runner}")
    if CHROME is None:
        raise SystemExit("No Chrome/Edge for local jvenn replica")
    try:
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options as EdgeOptions
        from selenium.webdriver.edge.service import Service as EdgeService
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError as e:
        raise SystemExit("pip install selenium") from e

    payload = {
        "series": [{"name": s["name"], "data": list(s.get("data") or [])} for s in series],
        "colors": colors or [],
        "displayMode": display_mode,
        "fontSize": "14px",
        "fontFamily": "Arial",
    }
    page = runner.read_text(encoding="utf-8").replace(
        "__PAYLOAD__", json.dumps(payload, ensure_ascii=False)
    )
    tmp = JVENN_ASSETS / "_run_payload.html"
    tmp.write_text(page, encoding="utf-8")
    edge = next(
        (p for p in (
            Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        ) if p.exists()),
        None,
    )
    if edge is None:
        raise SystemExit("Edge not found for local jvenn replica")
    opts = EdgeOptions()
    opts.binary_location = str(edge)
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1400,1600")
    opts.add_argument("--hide-scrollbars")
    driver_path = Path(
        r"C:\Users\10540\.cache\selenium\msedgedriver\win64\150.0.4078.144\msedgedriver.exe"
    )
    service = EdgeService(executable_path=str(driver_path)) if driver_path.exists() else EdgeService()
    driver = webdriver.Edge(service=service, options=opts)
    try:
        driver.set_page_load_timeout(timeout_s)
        driver.get(tmp.resolve().as_uri())
        WebDriverWait(driver, timeout_s).until(
            lambda d: d.title == "JVENN_READY" or str(d.title).startswith("JVENN_FAIL")
        )
        if str(driver.title).startswith("JVENN_FAIL"):
            detail = driver.execute_script(
                "return document.getElementById('svg-dump') ? document.getElementById('svg-dump').textContent : ''"
            )
            raise SystemExit(f"local jvenn replica failed: {driver.title} {detail}")
        svg = driver.execute_script(
            "return document.getElementById('svg-dump').textContent"
        ) or ""
    finally:
        driver.quit()
        tmp.unlink(missing_ok=True)
    svg = svg.strip()
    if not svg.startswith("<svg"):
        sm = re.search(r"<svg[\s\S]*</svg>", svg)
        if not sm:
            raise SystemExit(f"local jvenn replica returned no svg: {svg[:300]}")
        svg = sm.group(0)
    return expand_svg_canvas(svg)


def render_jvenn_svg(
    series: list[dict],
    *,
    colors: list[str] | None = None,
    display_mode: str = "classic",
    timeout_s: float = 180.0,
    url: str = JVENN_EXAMPLE_URL,
) -> str:
    """驱动微生信官网 jvenn 页填入列表并导出 SVG（与页面「下载 SVG」同逻辑）。

    权威：https://bioinformatics.com.cn/static/others/jvenn/example.html
    """
    if CHROME is None:
        raise SystemExit("No Chrome/Edge for jvenn headless render")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError as e:
        raise SystemExit("pip install selenium  # required for jvenn render") from e

    # name colors: set via inline style so jvenn reads css('color')
    color_map = {}
    if colors:
        for s, c in zip(series, colors):
            color_map[s["name"]] = c

    opts = Options()
    opts.binary_location = str(CHROME)
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1100,1200")
    opts.add_argument("--hide-scrollbars")
    driver = webdriver.Chrome(options=opts)
    try:
        driver.set_page_load_timeout(timeout_s)
        driver.get(url)
        WebDriverWait(driver, timeout_s).until(
            lambda d: d.execute_script("return !!(window.jQuery && jQuery.fn.jvenn);")
        )
        # classic mode + stats if controls exist
        driver.execute_script(
            """
            const mode = arguments[0];
            // display mode radios/buttons often labeled classic / Edwards
            document.querySelectorAll('input[type=radio],button,a,label').forEach(el => {
              const t = ((el.value||'') + ' ' + (el.textContent||'')).toLowerCase();
              if (mode === 'classic' && t.includes('classic')) { try { el.click(); } catch(e){} }
              if (mode === 'edwards' && t.includes('edward')) { try { el.click(); } catch(e){} }
            });
            """,
            display_mode,
        )
        driver.execute_script(
            """
            const series = arguments[0];
            const colorMap = arguments[1] || {};
            for (let i = 1; i <= 6; i++) {
              const n = document.getElementById('name' + i);
              const a = document.getElementById('area' + i);
              if (n) { n.value = ''; n.style.color = ''; jQuery(n).trigger('change'); }
              if (a) { a.value = ''; jQuery(a).trigger('change'); }
            }
            series.forEach((s, idx) => {
              const i = idx + 1;
              const n = document.getElementById('name' + i);
              const a = document.getElementById('area' + i);
              n.value = s.name;
              if (colorMap[s.name]) n.style.color = colorMap[s.name];
              a.value = (s.data || []).join('\\n');
              jQuery(n).trigger('change');
              jQuery(a).trigger('change');
            });
            """,
            series,
            color_map,
        )
        WebDriverWait(driver, timeout_s).until(
            lambda d: d.execute_script(
                "const c=document.getElementById('jvenn-container');"
                "return !!(c && c.querySelector('svg') && c.innerHTML.length>800);"
            )
        )
        # settle absolute labels
        driver.execute_script("return new Promise(r => setTimeout(r, 1200));")
        svg = driver.execute_script(_EXPORT_SVG_JS)
    finally:
        driver.quit()

    svg = (svg or "").strip()
    if not svg.startswith("<svg"):
        sm = re.search(r"<svg[\s\S]*</svg>", svg or "")
        if not sm:
            raise SystemExit(f"jvenn svg export failed: {str(svg)[:400]}")
        svg = sm.group(0)
    return svg


def build_disease_5db_svg(sets: dict[str, set[str]]) -> str:
    """五库疾病韦恩 = 本地 HTML 复刻 `jvenn_runner.html`。空库也传入。"""
    order = ["GeneCards", "CTD", "OMIM", "TTD", "DrugBank"]
    color_by = {
        "GeneCards": "rgb(241,90,96)",
        "CTD": "rgb(255,117,0)",
        "OMIM": "rgb(207,207,27)",
        "TTD": "rgb(0,102,0)",
        "DrugBank": "rgb(90,155,212)",
    }
    series = []
    colors = []
    for name in order:
        genes = sorted(_as_set(sets.get(name, set())))
        series.append({"name": name, "data": genes})
        colors.append(color_by[name])
    return render_replica_svg(series, colors=colors, display_mode="classic")


def build_two_set_svg(
    set_a,
    set_b,
    name_a: str = "Drugs",
    name_b: str = "Disease",
    col_a: tuple[int, int, int] | None = None,
    col_b: tuple[int, int, int] | None = None,
) -> str:
    """两集韦恩 = 本地 HTML 复刻 `_jvenn_assets/jvenn_runner.html`。"""
    ca = col_a or COL["Drugs"]
    cb = col_b or COL["Disease"]
    return render_replica_svg(
        [
            {"name": name_a, "data": sorted(_as_set(set_a))},
            {"name": name_b, "data": sorted(_as_set(set_b))},
        ],
        colors=[rgb(ca), rgb(cb)],
    )


def rasterize(svg: Path, png: Path) -> None:
    if CHROME is None:
        raise SystemExit("No Chrome/Edge found for headless screenshot")
    raw = svg.read_text(encoding="utf-8")
    mw = re.search(r'\bwidth="([\d.]+)', raw)
    mh = re.search(r'\bheight="([\d.]+)', raw)
    width = int(float(mw.group(1))) if mw else 820
    height = int(float(mh.group(1))) if mh else 780
    html = svg.with_suffix(".preview.html")
    html.write_text(
        "<!DOCTYPE html><html><head><meta charset=utf-8>"
        "<style>html,body{margin:0;padding:0;background:#fff;}"
        f"svg{{display:block;width:{width}px;height:{height}px;}}</style>"
        f"</head><body>{raw}</body></html>",
        encoding="utf-8",
    )
    cmd = [
        str(CHROME),
        "--headless=new",
        "--disable-gpu",
        f"--screenshot={png}",
        f"--window-size={width + 8},{height + 8}",
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
