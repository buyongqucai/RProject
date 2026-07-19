# -*- coding: utf-8 -*-
"""将参考_交付原图中的微生信韦恩 SVG 复制为样例结果，并用 Chrome headless 导出 PNG。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SAMPLE = Path(__file__).resolve().parent / "01_样例_sample"
REF = SAMPLE / "参考_交付原图"
FIG = SAMPLE / "代码文件" / "结果文件" / "图片文件"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

PAIRS = [
    ("Venn_DiseaseDatabases.svg", "01_韦恩图_DiseaseDatabases_Venn"),
    ("Venn_DrugDisease.svg", "02_韦恩图_DrugDisease_Venn"),
]


def rasterize(svg: Path, png: Path, width_px: int = 2000, height_px: int = 2800) -> None:
    html = svg.with_suffix(".preview.html")
    svg_text = svg.read_text(encoding="utf-8")
    html.write_text(
        "<!DOCTYPE html><html><head><meta charset=utf-8>"
        "<style>html,body{margin:0;padding:24px;background:#fff;}"
        "svg{display:block;margin:0 auto;width:900px;height:auto;}</style>"
        f"</head><body>{svg_text}</body></html>",
        encoding="utf-8",
    )
    cmd = [
        str(CHROME),
        "--headless=new",
        "--disable-gpu",
        f"--screenshot={png}",
        f"--window-size={width_px},{height_px}",
        "--hide-scrollbars",
        "--force-device-scale-factor=2",
        html.resolve().as_uri(),
    ]
    subprocess.run(cmd, capture_output=True, check=False)
    html.unlink(missing_ok=True)
    if not png.exists() or png.stat().st_size < 1000:
        raise SystemExit(f"rasterize failed: {png}")


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    if not REF.exists():
        raise SystemExit(f"missing ref dir: {REF}")
    for src_name, stem in PAIRS:
        src = REF / src_name
        if not src.exists():
            raise SystemExit(f"missing {src}")
        svg_out = FIG / f"{stem}.svg"
        png_out = FIG / f"{stem}.png"
        svg_out.write_bytes(src.read_bytes())
        rasterize(svg_out, png_out)
        print("OK", stem, "svg", svg_out.stat().st_size, "png", png_out.stat().st_size)


if __name__ == "__main__":
    main()
    sys.exit(0)
