#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一对多分子对接：中心圆环结合能热图 + 外围 result 拼图。

布局参考期刊 graphical abstract（中心环 + 外周扇区）：
  - 圆心：蛋白 / PDB
  - 圆环：每配体一扇区，颜色随 affinity 连续变化，扇区标注结合能
  - 外周：对应 result_N.png（可缺则跳过）

图面 English；标签黑色；PNG+SVG；DPI≥600。

示例：
  python plot_docking_ring_heatmap.py --root "C:/Users/.../杨程茗分子对接"
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import FancyBboxPatch, Wedge
from PIL import Image

from dock_export_common import log


# journal-ish affinity ramp: weak (near 0) → pale；strong (more negative) → deep rose
AFF_CMAP = LinearSegmentedColormap.from_list(
    "dock_aff",
    ["#F5E6D3", "#E8B4A0", "#C17B7B", "#8B3A3A"],
    N=256,
)

# soft sector backgrounds (cycle)
SECTOR_BG = [
    "#F7E8EC",  # pink
    "#E8F0F7",  # blue
    "#F7F0E8",  # peach
    "#EAF3EA",  # green
    "#F0EAF7",  # lilac
]


def short_name(ligand: str, ligand_name: str, max_len: int = 22) -> str:
    aliases = {
        "chalcone_dihydroxy_dimethoxy": "Chalcone derivative",
        "n_acetyltryptophan": "N-acetyltryptophan",
        "quercetin": "Quercetin",
        "luteolin": "Luteolin",
        "centaureidin": "Centaureidin",
    }
    key = (ligand or "").strip()
    if key in aliases:
        return aliases[key]
    prefer = (ligand_name or ligand or "").strip()
    if len(prefer) > max_len and ligand:
        prefer = ligand.replace("_", " ")
    if len(prefer) > max_len:
        prefer = prefer[: max_len - 1] + "…"
    return prefer


def load_summary(root: Path) -> List[dict]:
    path = root / "summary_vina.csv"
    if not path.exists():
        raise FileNotFoundError(f"missing {path}")
    from dock_summary_schema import load_summary_rows

    rows = []
    for row in load_summary_rows(path):
        task = row["task"]
        lig = row.get("ligand", "")
        name = row.get("ligand_name") or lig
        result = root / task / "图片" / f"result_{task}.png"
        if not result.exists():
            alt = list((root / task / "图片").glob("result_*.png"))
            result = alt[0] if alt else None
        rows.append(
            {
                "task": task,
                "protein": row.get("protein") or "Target",
                "pdb": row.get("pdb", ""),
                "ligand": lig,
                "ligand_name": name,
                "label": short_name(lig, name),
                "affinity": row["affinity_kcal_mol"],
                "result": result,
            }
        )
    if not rows:
        raise RuntimeError("no rows in summary_vina.csv")
    return rows


def load_thumb(path: Optional[Path], max_side: int = 1400) -> Optional[Image.Image]:
    if path is None or not path.exists():
        return None
    im = Image.open(path).convert("RGB")
    w, h = im.size
    scale = min(1.0, max_side / max(w, h))
    if scale < 1.0:
        im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    return im


def draw_ring_dashboard(
    rows: List[dict],
    out_stem: Path,
    dpi: int = 600,
    fig_inches: float = 14.0,
) -> Tuple[Path, Path]:
    n = len(rows)
    protein = rows[0]["protein"]
    pdb = rows[0]["pdb"]
    affs = np.array([r["affinity"] for r in rows], dtype=float)
    # more negative = stronger → map to high end of cmap
    vmin, vmax = float(affs.min()), float(affs.max())
    if abs(vmax - vmin) < 1e-6:
        vmax = vmin + 0.5
    norm = Normalize(vmin=vmin, vmax=vmax)
    # invert: strongest (min) → 1.0
    def aff_to_color(a: float):
        t = 1.0 - norm(a)  # strong → dark
        return AFF_CMAP(t)

    fig, ax = plt.subplots(figsize=(fig_inches, fig_inches), dpi=dpi)
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-1.35, 1.35)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # radii (data units)
    r_hub = 0.28
    r_ring_in = 0.32
    r_ring_out = 0.58
    r_label = 0.70
    r_panel = 1.05
    panel_w, panel_h = 0.52, 0.30

    # start at top, clockwise
    start0 = 90.0
    sweep = 360.0 / n

    for i, row in enumerate(rows):
        # wedge angles: matplotlib Wedge uses CCW from east; we want CW from north
        # angle_from: start of sector going CCW
        a0 = start0 - i * sweep
        a1 = a0 - sweep
        theta1, theta2 = min(a0, a1), max(a0, a1)
        mid = (a0 + a1) / 2.0
        mid_rad = math.radians(mid)

        # outer soft sector background (pie slice)
        bg = patches.Wedge(
            (0, 0),
            1.32,
            theta1,
            theta2,
            width=1.32 - (r_ring_out + 0.02),
            facecolor=SECTOR_BG[i % len(SECTOR_BG)],
            edgecolor="white",
            linewidth=2.0,
            alpha=0.95,
            zorder=0,
        )
        ax.add_patch(bg)

        # affinity ring wedge
        color = aff_to_color(row["affinity"])
        ring = Wedge(
            (0, 0),
            r_ring_out,
            theta1,
            theta2,
            width=r_ring_out - r_ring_in,
            facecolor=color,
            edgecolor="white",
            linewidth=2.5,
            zorder=3,
        )
        ax.add_patch(ring)

        # affinity value on ring
        rr = (r_ring_in + r_ring_out) / 2.0
        ax.text(
            rr * math.cos(mid_rad),
            rr * math.sin(mid_rad),
            f"{row['affinity']:.1f}",
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="#000000",
            zorder=5,
        )

        # ligand short name outside ring
        ax.text(
            r_label * math.cos(mid_rad),
            r_label * math.sin(mid_rad),
            row["label"],
            ha="center",
            va="center",
            fontsize=8,
            color="#000000",
            zorder=5,
            wrap=True,
        )

        # result panel
        cx = r_panel * math.cos(mid_rad)
        cy = r_panel * math.sin(mid_rad)
        box = FancyBboxPatch(
            (cx - panel_w / 2, cy - panel_h / 2),
            panel_w,
            panel_h,
            boxstyle="round,pad=0.01,rounding_size=0.02",
            facecolor="white",
            edgecolor="#B0B0B0",
            linewidth=1.2,
            zorder=4,
        )
        ax.add_patch(box)

        thumb = load_thumb(row["result"], max_side=1600)
        if thumb is not None:
            # slight inset
            extent = [
                cx - panel_w / 2 + 0.015,
                cx + panel_w / 2 - 0.015,
                cy - panel_h / 2 + 0.015,
                cy + panel_h / 2 - 0.015,
            ]
            ax.imshow(thumb, extent=extent, aspect="auto", zorder=5, interpolation="lanczos")
        else:
            ax.text(
                cx,
                cy,
                f"result_{row['task']}\n(missing)",
                ha="center",
                va="center",
                fontsize=7,
                color="#000000",
                zorder=5,
            )

        # connector tick from ring to panel
        ax.plot(
            [(r_ring_out + 0.01) * math.cos(mid_rad), (r_panel - panel_h * 0.55) * math.cos(mid_rad)],
            [(r_ring_out + 0.01) * math.sin(mid_rad), (r_panel - panel_h * 0.55) * math.sin(mid_rad)],
            color="#888888",
            lw=0.8,
            zorder=2,
            solid_capstyle="round",
        )

    # hub
    hub = plt.Circle((0, 0), r_hub, facecolor="white", edgecolor="#444444", linewidth=2.0, zorder=6)
    ax.add_patch(hub)
    hub_title = protein if not pdb else f"{protein}\n({pdb})"
    ax.text(
        0,
        0.04,
        hub_title,
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        color="#000000",
        zorder=7,
    )
    ax.text(
        0,
        -0.14,
        "Affinity\n(kcal/mol)",
        ha="center",
        va="center",
        fontsize=7,
        color="#000000",
        zorder=7,
    )

    # colorbar
    sm = plt.cm.ScalarMappable(
        cmap=AFF_CMAP,
        norm=Normalize(vmin=0, vmax=1),
    )
    sm.set_array([])
    cax = fig.add_axes([0.88, 0.22, 0.02, 0.28])
    cb = fig.colorbar(sm, cax=cax)
    cb.set_ticks([0, 0.5, 1])
    cb.set_ticklabels(
        [f"{vmax:.1f}\n(weaker)", "", f"{vmin:.1f}\n(stronger)"],
        fontsize=6,
    )
    cb.set_label("Binding energy", fontsize=7)
    cb.ax.yaxis.set_tick_params(length=0)
    for t in cb.ax.get_yticklabels():
        t.set_color("#000000")

    ax.set_title(
        "One-to-many docking: ring affinity map + pose results",
        fontsize=12,
        color="#000000",
        pad=8,
    )

    out_stem.parent.mkdir(parents=True, exist_ok=True)
    png = out_stem.with_suffix(".png")
    svg = out_stem.with_suffix(".svg")
    fig.savefig(png, dpi=dpi, bbox_inches="tight", facecolor="white", edgecolor="none")
    fig.savefig(svg, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
    return png, svg


def main() -> None:
    ap = argparse.ArgumentParser(description="Docking ring heatmap + result dashboard")
    ap.add_argument("--root", type=Path, required=True, help="docking project root")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output stem (default: <root>/圆环_一对多对接结合能_DockingRingHeatmap)",
    )
    ap.add_argument("--dpi", type=int, default=600)
    args = ap.parse_args()
    root = args.root.resolve()
    rows = load_summary(root)
    out = args.out or (root / "圆环_一对多对接结合能_DockingRingHeatmap")
    png, svg = draw_ring_dashboard(rows, out, dpi=args.dpi)
    log(f"PNG {png}")
    log(f"SVG {svg}")
    log(f"n={len(rows)} protein={rows[0]['protein']} pdb={rows[0]['pdb']}")


if __name__ == "__main__":
    main()
