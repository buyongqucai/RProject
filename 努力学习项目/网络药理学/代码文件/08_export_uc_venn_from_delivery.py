# -*- coding: utf-8 -*-
"""UC 项目：按技能样例同路径导出微生信韦恩交付图。

技能 SSOT：
  - 疾病多库 / 药病韦恩优先用微生信交付 SVG（非 R np_plot_*_venn）
  - 本脚本对齐 NetworkPharmacology/_export_delivery_venn_figures.py

用法：
  1. 用 微生信上传_基因列表/ 中的 txt 在微生信出图，导出 SVG
  2. 将 SVG 放到 参考_交付原图/ 并命名为：
       Venn_DiseaseDatabases.svg
       Venn_DrugDisease.svg
  3. python 08_export_uc_venn_from_delivery.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent
PROJECT = CODE.parent
REF = PROJECT / "参考_交付原图"
FIG = CODE / "结果文件" / "图片文件"
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
        raise SystemExit(
            f"missing ref dir: {REF}\n"
            "Put 微生信-exported SVGs there first (see 参考_交付原图/README.md)."
        )
    missing = [n for n, _ in PAIRS if not (REF / n).exists()]
    if missing:
        raise SystemExit(
            "微生信交付 SVG 尚未就位（技能要求，禁止用 R 近似冒充交付）:\n  - "
            + "\n  - ".join(missing)
            + f"\n目录: {REF}"
        )
    for src_name, stem in PAIRS:
        src = REF / src_name
        svg_out = FIG / f"{stem}.svg"
        png_out = FIG / f"{stem}.png"
        svg_out.write_bytes(src.read_bytes())
        rasterize(svg_out, png_out)
        print("OK", stem, "svg", svg_out.stat().st_size, "png", png_out.stat().st_size)


if __name__ == "__main__":
    main()
    sys.exit(0)
