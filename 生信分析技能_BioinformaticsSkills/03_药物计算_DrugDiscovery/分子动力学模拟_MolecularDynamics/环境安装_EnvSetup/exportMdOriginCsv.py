# -*- coding: utf-8 -*-
"""从 GROMACS 工作目录 xvg 导出 Origin 用 CSV（英文列名，落 E:\\Origin_Data\\<项目>）。

用法:
  python 导出Origin数据_exportMdOriginCsv.py --work ~/md_runs/MMP9_Tryptophan_4H3X --project MMP9_Tryptophan_4H3X
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np


def read_xvg(path: Path, *, time_to_ns: bool = False):
    """读 xvg。time_to_ns=True 时按 xaxis 标签把 ps→ns（已是 ns 则不动）。"""
    rows = []
    if not path.is_file():
        return None
    xunit = ""
    for line in path.read_text(errors="replace").splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("@") and "xaxis" in s.lower() and "label" in s.lower():
            # @ xaxis  label "Time (ps)"
            low = s.lower()
            if "(ps)" in low or "ps)" in low:
                xunit = "ps"
            elif "(ns)" in low or "ns)" in low:
                xunit = "ns"
            continue
        if s.startswith("#") or s.startswith("@"):
            continue
        parts = s.split()
        try:
            rows.append([float(x) for x in parts])
        except ValueError:
            continue
    if not rows:
        return None
    arr = np.asarray(rows, dtype=float)
    if time_to_ns and arr.shape[1] >= 1:
        if xunit == "ps" or (xunit == "" and float(np.nanmax(arr[:, 0])) > 500):
            arr = arr.copy()
            arr[:, 0] = arr[:, 0] / 1000.0
    return arr


def write_csv(path: Path, header: list[str], arr):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(",".join(header) + "\n")
        for row in arr:
            cells = []
            for x in row:
                if isinstance(x, str):
                    cells.append(x)
                else:
                    cells.append(f"{float(x):.8g}")
            f.write(",".join(cells) + "\n")


def kde2d_fel(x, y, n=60):
    # Scott bandwidth, same spirit as MASS::kde2d default
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if len(x) < 20:
        return None
    nx = len(x)
    hx = x.std(ddof=1) * nx ** (-1 / 5) * 1.06
    hy = y.std(ddof=1) * nx ** (-1 / 5) * 1.06
    hx = max(hx, 1e-6)
    hy = max(hy, 1e-6)
    gx = np.linspace(x.min(), x.max(), n)
    gy = np.linspace(y.min(), y.max(), n)
    X, Y = np.meshgrid(gx, gy, indexing="xy")
    # vectorized kernel (may be heavy for 100ns; subsample if needed)
    if nx > 4000:
        idx = np.linspace(0, nx - 1, 4000).astype(int)
        x, y = x[idx], y[idx]
        nx = len(x)
    Z = np.zeros_like(X)
    for xi, yi in zip(x, y):
        Z += np.exp(-0.5 * (((X - xi) / hx) ** 2 + ((Y - yi) / hy) ** 2))
    Z /= Z.max()
    Z = np.clip(Z, Z[Z > 0].min() * 1e-3, None)
    kj = 0.0083144621 * 300
    dg = -kj * np.log(Z)
    dg -= dg.min()
    out = []
    for i in range(n):
        for j in range(n):
            out.append((gx[j], gy[i], dg[i, j]))
    return np.asarray(out)


def interp(t_src, y_src, t_dst):
    return np.interp(t_dst, t_src, y_src)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--project", required=True)
    ap.add_argument("--origin-root", type=Path, default=Path(r"E:\Origin_Data"))
    args = ap.parse_args()
    work: Path = args.work
    out = args.origin_root / args.project
    out.mkdir(parents=True, exist_ok=True)

    # 列名与 origin出图_plotMdOrigin.prepare_inputs 样例契约对齐（勿用 Backbone/SASA 短名）
    mapping = [
        ("rmsd_backbone.xvg", "RMSD_backbone.csv", ["time_ns", "rmsd_nm"], [0, 1]),
        ("rmsd_protein.xvg", None, None, None),  # handled in tri
        ("rmsf_calpha.xvg", "RMSF_calpha.csv", ["residue", "rmsf_nm"], [0, 1]),
        ("hbond_num.xvg", "HBonds_protein_ligand.csv", ["time_ns", "n_hbond"], [0, 1]),
        ("gyrate.xvg", "Rg.csv", ["time_ns", "rg_nm"], [0, 1]),
        ("sasa.xvg", "SASA.csv", ["time_ns", "sasa_nm2"], [0, 1]),
        ("com_distance.xvg", "COM_distance.csv", ["time_ns", "dist_nm"], [0, 1]),
        ("energy_nvt_temp.xvg", "NVT_temperature.csv", ["time_ns", "temp_K"], [0, 1]),
        ("energy_md_potential.xvg", "MD_potential.csv", ["time_ns", "pot_kj"], [0, 1]),
    ]
    for src, dst, header, cols in mapping:
        if dst is None:
            continue
        # residue 轴不转时间；其余时间序列统一到 ns
        to_ns = "residue" not in header
        arr = read_xvg(work / src, time_to_ns=to_ns)
        if arr is None or arr.shape[1] <= max(cols):
            print(f"skip {src}")
            continue
        write_csv(out / dst, header, arr[:, cols])
        tmax = float(arr[:, cols[0]].max()) if to_ns else None
        print(f"wrote {dst}" + (f"  t_max={tmax:.4g} ns" if tmax is not None else ""))

    # NPT equilibration wide
    t_temp = read_xvg(work / "energy_npt_temp.xvg", time_to_ns=True)
    t_press = read_xvg(work / "energy_npt_press.xvg", time_to_ns=True)
    t_dens = read_xvg(work / "energy_npt_dens.xvg", time_to_ns=True)
    if t_temp is not None:
        t = t_temp[:, 0]
        press = interp(t_press[:, 0], t_press[:, 1], t) if t_press is not None else np.full_like(t, np.nan)
        dens = interp(t_dens[:, 0], t_dens[:, 1], t) if t_dens is not None else np.full_like(t, np.nan)
        write_csv(
            out / "NPT_equilibration.csv",
            ["time_ns", "temp_K", "press_bar", "density"],
            np.column_stack([t, t_temp[:, 1], press, dens]),
        )
        print("wrote NPT_equilibration.csv")

    # Tri-line RMSD：长表 series+rmsd_nm（与 02_分析出图_plotMdAnalysis.R 契约一致）
    # 禁止用 Protein 冒充 Complex；缺哪条就跳过哪条并告警
    bb = read_xvg(work / "rmsd_backbone.xvg", time_to_ns=True)
    pr = read_xvg(work / "rmsd_protein.xvg", time_to_ns=True)
    lg = read_xvg(work / "rmsd_ligand.xvg", time_to_ns=True)
    cx = read_xvg(work / "rmsd_complex.xvg", time_to_ns=True)
    if pr is not None and lg is not None:
        t = pr[:, 0]
        rows = []
        series_map = [("Protein", pr), ("Ligand", lg)]
        if cx is not None:
            series_map.append(("Complex", cx))
        else:
            print("WARN: rmsd_complex.xvg missing — Complex series omitted (do not fake from Protein)")
        for series, arr in series_map:
            yi = interp(arr[:, 0], arr[:, 1], t)
            for ti, vi in zip(t, yi):
                rows.append([ti, series, vi])
        write_csv(
            out / "RMSD_protein_ligand_complex.csv",
            ["time_ns", "series", "rmsd_nm"],
            rows,
        )
        print(f"wrote RMSD_protein_ligand_complex.csv  series={[s for s,_ in series_map]}")
    else:
        print("WARN: skip RMSD_protein_ligand_complex.csv (need rmsd_protein + rmsd_ligand)")

    # FEL pairs
    rg = read_xvg(work / "gyrate.xvg", time_to_ns=True)
    com = read_xvg(work / "com_distance.xvg", time_to_ns=True)
    sasa = read_xvg(work / "sasa.xvg", time_to_ns=True)
    if bb is not None and rg is not None:
        t = bb[:, 0]
        fel = kde2d_fel(bb[:, 1], interp(rg[:, 0], rg[:, 1], t))
        if fel is not None:
            write_csv(out / "FEL_RMSD_Rg_kJmol.csv", ["x", "y", "dg_kj"], fel)
            write_csv(out / "FEL3D_RMSD_Rg_kJmol.csv", ["x", "y", "dg_kj"], fel)
            print("wrote FEL_RMSD_Rg")
    if bb is not None and com is not None:
        t = bb[:, 0]
        fel = kde2d_fel(bb[:, 1], interp(com[:, 0], com[:, 1], t))
        if fel is not None:
            write_csv(out / "FEL_RMSD_COM_kJmol.csv", ["x", "y", "dg_kj"], fel)
            print("wrote FEL_RMSD_COM")
    if bb is not None and sasa is not None:
        t = bb[:, 0]
        fel = kde2d_fel(bb[:, 1], interp(sasa[:, 0], sasa[:, 1], t))
        if fel is not None:
            write_csv(out / "FEL_RMSD_SASA_kJmol.csv", ["x", "y", "dg_kj"], fel)
            print("wrote FEL_RMSD_SASA")
    if pr is not None and lg is not None:
        fel = kde2d_fel(pr[:, 1], interp(lg[:, 0], lg[:, 1], pr[:, 0]))
        if fel is not None:
            write_csv(out / "FEL_LigandProteinRmsd_kJmol.csv", ["x", "y", "dg_kj"], fel)
            print("wrote FEL_LigandProteinRmsd")

    print(f"DONE → {out}")


if __name__ == "__main__":
    main()
