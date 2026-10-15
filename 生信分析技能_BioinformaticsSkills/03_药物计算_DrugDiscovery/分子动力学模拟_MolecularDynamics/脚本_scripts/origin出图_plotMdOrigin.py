# -*- coding: utf-8 -*-
"""用本机 Origin（E:\\Origin\\Origin64.exe）绘制 MD 分析图。

不是 matplotlib/ggplot 仿 Origin 样式：本脚本通过 COM / LabTalk
操作 Origin 导入 CSV、建图、导出 PNG/SVG。

工作方式（避免文件占用）：
  每张图 = 启动 Origin → 画一张 → 导出 PNG/SVG → 不保存 .opju → 关闭 Origin
  禁止对 Origin COM Save() 传入绝对路径（UFF 是 E:\\Origin_Data，会拼成
    E:\\Origin_Data\\\"E:/Origin_Data/3HTB/xxx.opju\\\".opju）。

配色对齐 VizStandards journal muted。
FEL：2D 用 plotxyz 243（XYZ 等值线）+ Viridis；3D 对齐论文常见「漏斗+底板」样式：
  matrix → plotm 103 OpenGL glcmap + Jet，显示层 ΔG 封顶（默认 20 kJ/mol）、4× 双线性、
  曲面填色关 mesh、底板投影。不改 kde2d 带宽 / 不改色板逻辑。
柱图：单列数值 + 逐柱着色（禁止对角空表多 series）。

用法：
  python origin出图_plotMdOrigin.py
  python origin出图_plotMdOrigin.py --data-dir E:\\Origin_Data\\3HTB
  python origin出图_plotMdOrigin.py --only RmsdBackbone,ResidueEnergyContrib
  python origin出图_plotMdOrigin.py --layout-only
      # 不启动 Origin，只按图种归到同一文件夹（例：NPT压力图/ 内同时放 CSV 与 PNG/SVG）
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ORIGIN_EXE = Path(r"E:\Origin\Origin64.exe")
DEFAULT_DATA = Path(r"E:\Origin_Data\3HTB")
SAMPLE_RESULT = Path(
    r"E:\RProject\生信分析技能_BioinformaticsSkills\03_药物计算_DrugDiscovery"
    r"\分子动力学模拟_MolecularDynamics\01_样例_sample\代码文件\结果文件"
)
SAMPLE_FIG = SAMPLE_RESULT / "图片文件"  # 旧路径，layout 时迁走
OC_HIDE_CONTOURS = Path(__file__).resolve().parent / "origin隐藏FEL等值线_hideFelContours.c"
# 3D FEL 显示封顶（kJ/mol）：对齐论文 H 面板常见 0–16 量级；不改原始 CSV/KDE
FEL_DG_CLIP_KJ = 20.0

def _load_md_layout():
    import importlib.util
    p = Path(__file__).resolve().parent / "整理样例目录_layoutMdSample.py"
    spec = importlib.util.spec_from_file_location("md_sample_layout", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_MD_LAYOUT = _load_md_layout()

# LabTalk 路径只用 ASCII；拷到样例时再换成中英对照文件名
STEM_ZH = {
    "RmsdProteinLigandComplex": "三线RMSD_RmsdProteinLigandComplex",
    "RmsdBackbone": "骨架RMSD_RmsdBackbone",
    "RmsfCalpha": "残基RMSF_RmsfCalpha",
    "HbondNum": "氢键数_HbondNum",
    "RadiusGyration": "回旋半径_RadiusGyration",
    "Sasa": "溶剂可及表面积_Sasa",
    "ComDistance": "质心距离_ComDistance",
    "NvtTemperature": "NVT温度_NvtTemperature",
    "NptTemperature": "NPT温度_NptTemperature",
    "NptPressure": "NPT压力_NptPressure",
    "NptDensity": "NPT密度_NptDensity",
    "MdPotential": "生产势能_MdPotential",
    "FreeEnergyLandscape": "自由能形貌_FreeEnergyLandscape",
    "FreeEnergyLandscape3D": "自由能形貌3D_FreeEnergyLandscape3D",
    "FreeEnergyRmsdCom": "自由能形貌RMSDx质心_FreeEnergyRmsdCom",
    "FreeEnergyRmsdCom3D": "自由能形貌3D_RMSDx质心_FreeEnergyRmsdCom3D",
    "FreeEnergyRmsdSasa": "自由能形貌RMSDxSASA_FreeEnergyRmsdSasa",
    "FreeEnergyRmsdSasa3D": "自由能形貌3D_RMSDxSASA_FreeEnergyRmsdSasa3D",
    "FreeEnergyLigandProteinRmsd": "自由能形貌配体蛋白RMSD_FreeEnergyLigandProteinRmsd",
    "FreeEnergyLigandProteinRmsd3D": "自由能形貌3D_配体蛋白RMSD_FreeEnergyLigandProteinRmsd3D",
    "BindingEnergyDecomp": "结合能分解_BindingEnergyDecomp",
    "BindingEnergyLabeled": "结合能标注柱_BindingEnergyLabeled",
    "BindingEnergyTable": "结合能表_BindingEnergyTable",
    "ResidueEnergyContrib": "残基能量贡献_ResidueEnergyContrib",
}

# Origin_Data CSV → 各图「图数据」
STEM_DATA_CSV = {
    "RmsdBackbone": ["RMSD_backbone.csv"],
    "RmsdProteinLigandComplex": ["RMSD_protein_ligand_complex.csv"],
    "RmsfCalpha": ["RMSF_calpha.csv"],
    "HbondNum": ["HBonds_protein_ligand.csv"],
    "RadiusGyration": ["Rg.csv"],
    "Sasa": ["SASA.csv"],
    "ComDistance": ["COM_distance.csv"],
    "NvtTemperature": ["NVT_temperature.csv"],
    "NptTemperature": ["NPT_equilibration.csv"],
    "NptPressure": ["NPT_equilibration.csv"],
    "NptDensity": ["NPT_equilibration.csv"],
    "MdPotential": ["MD_potential.csv"],
    "FreeEnergyLandscape": ["FEL_RMSD_Rg_kJmol.csv", "FEL3D_RMSD_Rg_kJmol.csv"],
    "FreeEnergyLandscape3D": ["FEL3D_RMSD_Rg_kJmol.csv", "FEL_RMSD_Rg_kJmol.csv"],
    "FreeEnergyRmsdCom": ["FEL_RMSD_COM_kJmol.csv"],
    "FreeEnergyRmsdCom3D": ["FEL_RMSD_COM_kJmol.csv"],
    "FreeEnergyRmsdSasa": ["FEL_RMSD_SASA_kJmol.csv"],
    "FreeEnergyRmsdSasa3D": ["FEL_RMSD_SASA_kJmol.csv"],
    "FreeEnergyLigandProteinRmsd": ["FEL_LigandProteinRmsd_kJmol.csv"],
    "FreeEnergyLigandProteinRmsd3D": ["FEL_LigandProteinRmsd_kJmol.csv"],
    "BindingEnergyDecomp": ["MMGBSA_binding_decomp.csv"],
    "BindingEnergyLabeled": ["MMGBSA_binding_decomp.csv"],
    "BindingEnergyTable": ["MMGBSA_binding_table.csv"],
    "ResidueEnergyContrib": ["MMGBSA_residue_contrib.csv"],
}

# 非 Origin：LigPlot / PyMOL → 图代码绘图
CODE_PLOT_FILES = {
    "二维相互作用": [
        "二维相互作用_LigPlot2D.png",
        "二维相互作用_LigPlot2D.svg",
        "二维相互作用_LigPlot2D.ps",
    ],
    "轨迹快照": [
        "轨迹快照始_SnapshotStart.png",
        "轨迹快照中_SnapshotMid.png",
        "轨迹快照末_SnapshotEnd.png",
        "轨迹快照拼图_TrajectorySnapshots.png",
    ],
}

# R 数据表英文主题 → 一个或多个图种（按最长键匹配）
THEME_TOPICS: dict[str, list[str]] = {
    "RmsdBackbone": ["骨架RMSD"],
    "RmsdTriCurve": ["三线RMSD"],
    "RmsdProteinLigandComplex": ["三线RMSD"],
    "RmsfCalpha": ["残基RMSF"],
    "HbondNum": ["氢键数"],
    "RadiusGyration": ["回旋半径"],
    "Sasa": ["溶剂可及表面积"],
    "ComDistance": ["质心距离"],
    "NvtTemperature": ["NVT温度"],
    "NptEquilibration": ["NPT温度", "NPT压力", "NPT密度"],
    "NptTemperature": ["NPT温度"],
    "NptPressure": ["NPT压力"],
    "NptDensity": ["NPT密度"],
    "MdPotential": ["生产势能"],
    "FreeEnergyLandscape3D": ["自由能形貌3D"],
    "FreeEnergyRmsdCom3D": ["自由能形貌3D_RMSDx质心"],
    "FreeEnergyRmsdSasa3D": ["自由能形貌3D_RMSDxSASA"],
    "FreeEnergyLigandProteinRmsd3D": ["自由能形貌3D_配体蛋白RMSD"],
    "FreeEnergyLandscape": ["自由能形貌"],
    "FreeEnergyRmsdCom": ["自由能形貌RMSDx质心"],
    "FreeEnergyRmsdSasa": ["自由能形貌RMSDxSASA"],
    "FreeEnergyLigandProteinRmsd": ["自由能形貌配体蛋白RMSD"],
    "BindingEnergyDecomp": ["结合能分解"],
    "BindingEnergyLabeled": ["结合能标注柱"],
    "BindingEnergyTable": ["结合能表"],
    "ResidueEnergyContrib": ["残基能量贡献"],
    "LigPlot2D": ["二维相互作用"],
}


def topic_zh(stem: str) -> str:
    """STEM_ZH 文件名 → 项目中文前缀（骨架RMSD_RmsdBackbone → 骨架RMSD）。"""
    full = STEM_ZH.get(stem, stem)
    last = full.rsplit("_", 1)[-1]
    if last[:1].isascii() and last[:1].isupper():
        return full[: -(len(last) + 1)]
    return full


def figure_dir(result_root: Path, topic: str) -> Path:
    """一图一文件夹：10_NPT压力图/ 内同时放该图数据与图片。"""
    return result_root / _MD_LAYOUT.topic_folder_name(topic)


def _copy_file(src: Path, dest: Path) -> bool:
    if not src.exists() or not src.is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.resolve() == src.resolve():
        return False
    shutil.copy2(src, dest)
    return True

TEST_LEFTOVERS = (
    "SmokeRmsd.png", "SmokeRmsd2.png",
    "FelTest103.png", "FelTest243.png", "FelTestHm.png", "FelTestM226.png",
)

# VizStandards journal muted
C_PROTEIN = "#5B8FA8"
C_LIGAND = "#C17B7B"
C_COMPLEX = "#8B7BA8"
C_GREEN = "#6B8F71"
C_ACCENT = "#D4A574"
C_COM = "#A67C52"
C_DARK = "#2F4F4F"

PALETTE_IDX = {
    C_PROTEIN: 4,
    C_LIGAND: 2,
    C_COMPLEX: 6,
    C_GREEN: 3,
    C_ACCENT: 11,
    C_COM: 8,
    C_DARK: 9,
}


def _pal_idx(hex_color: str) -> int:
    """Origin 色板索引（1=黑，禁止）。color() RGB 对柱填充无效。"""
    return PALETTE_IDX.get(hex_color, 4)


DECOMP_COLORS = {
    "vdw": C_PROTEIN,
    "electrostatic": C_LIGAND,
    "polar solv. (gb)": C_ACCENT,
    "nonpolar solv.": C_GREEN,
    "vdwaals": C_PROTEIN,
    "eel": C_LIGAND,
    "egb": C_ACCENT,
    "esurf": C_GREEN,
    "ggas": C_COMPLEX,
    "gsolv": C_COM,
    "total": C_DARK,
}

COMP_DISPLAY = {
    "vdw": "vdW",
    "electrostatic": "Elec",
    "polar solv. (gb)": "EGB",
    "nonpolar solv.": "ESurf",
    "vdwaals": "VDWAALS",
    "eel": "EEL",
    "egb": "EGB",
    "esurf": "ESURF",
    "ggas": "GGAS",
    "gsolv": "GSOLV",
    "total": "TOTAL",
}


def _rgb(hex_color: str) -> str:
    """Origin custom OCOLOR integer (bit24=1, COLORREF RGB). 折线用。"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return str(r + (g << 8) + (b << 16) + 0x01000000)


def _color_lt(hex_color: str) -> str:
    """LabTalk color(R,G,B)。柱图必须用这个，整数 OCOLOR 会被当成色板索引 1=黑。"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"color({r},{g},{b})"


def _rgb_dec(hex_color: str) -> int:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r + (g << 8) + (b << 16)


def _lt_num(x: float) -> str:
    return f"{x:.8g}"


def _read_csv(path: Path) -> list[dict]:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return list(csv.DictReader(raw.decode(enc).splitlines()))
        except UnicodeDecodeError:
            continue
    return []


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="ascii", errors="replace") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def _col(row: dict, *names: str):
    lower = {k.lower().strip('"'): v for k, v in row.items()}
    for n in names:
        if n.lower() in lower and lower[n.lower()] not in (None, ""):
            return lower[n.lower()]
    return None


def _floats(path: Path, *names: str) -> list[float]:
    """每行只取 names 中第一个命中的列（避免 time_ns+residue 双列拼进同一轴）。"""
    out = []
    for r in _read_csv(path):
        v = _col(r, *names)
        if v is None:
            continue
        try:
            out.append(float(v))
        except ValueError:
            continue
    return out


def _write_raw(path: Path, rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="ascii", errors="replace") as fh:
        csv.writer(fh).writerows(rows)


def _bilinear_zoom(mat: list[list[str]], fx: int = 6, fy: int = 6) -> list[list[str]]:
    """显示用双线性加密；不改 kde2d 带宽。纯标准库，避免 Origin mexpand/minterp2 卡住。"""
    ny = len(mat)
    nx = len(mat[0]) if ny else 0
    if nx < 2 or ny < 2 or fx < 2:
        return mat
    z = []
    for row in mat:
        z.append([float(v) for v in row])
    out_ny = ny * fy
    out_nx = nx * fx
    out: list[list[str]] = []
    yden = out_ny - 1
    xden = out_nx - 1
    for i in range(out_ny):
        y = (i / yden) * (ny - 1)
        y0 = int(y)
        y1 = y0 + 1 if y0 + 1 < ny else y0
        wy = y - y0
        row_out = []
        for j in range(out_nx):
            x = (j / xden) * (nx - 1)
            x0 = int(x)
            x1 = x0 + 1 if x0 + 1 < nx else x0
            wx = x - x0
            v = (
                z[y0][x0] * (1 - wx) * (1 - wy)
                + z[y0][x1] * wx * (1 - wy)
                + z[y1][x0] * (1 - wx) * wy
                + z[y1][x1] * wx * wy
            )
            row_out.append(_lt_num(v))
        out.append(row_out)
    return out


def _span(vals: list[float], pad: float = 0.06, include0: bool = False,
          floor0: bool = False) -> tuple[float, float]:
    if not vals:
        return 0.0, 1.0
    lo, hi = min(vals), max(vals)
    if lo == hi:
        delta = abs(lo) * 0.05 if lo else 0.1
        lo, hi = lo - delta, hi + delta
    span = hi - lo
    lo -= span * pad
    hi += span * pad
    if include0:
        lo = min(lo, 0.0)
        hi = max(hi, 0.0)
    if floor0 and min(vals) >= 0:
        lo = 0.0
    return lo, hi


def _comp_key(name: str) -> str:
    return (name or "").strip().lower()


def _comp_label(name: str) -> str:
    return COMP_DISPLAY.get(_comp_key(name), (name or "").strip() or "term")


def prepare_inputs(data_dir: Path, work: Path) -> dict[str, Path]:
    """把 Origin_Data CSV 整理成 Origin 易导入的宽表（无引号表头）。"""
    work.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}

    tri = data_dir / "RMSD_protein_ligand_complex.csv"
    if tri.exists():
        rows = _read_csv(tri)
        by_t: dict[str, dict[str, str]] = {}
        wide_direct: list[list] = []
        for r in rows:
            t = _col(r, "time_ns")
            if t is None:
                continue
            # 宽表：已有 Protein/Ligand/Complex 列
            pcol = _col(r, "Protein", "protein")
            lcol = _col(r, "Ligand", "ligand")
            ccol = _col(r, "Complex", "complex")
            if pcol is not None or lcol is not None:
                wide_direct.append([t, pcol or "", lcol or "", ccol or ""])
                continue
            # 长表：series + rmsd_nm
            s = (_col(r, "series") or "").strip()
            v = _col(r, "rmsd_nm")
            if not s or v is None:
                continue
            by_t.setdefault(t, {})[s] = v
        if wide_direct:
            wide = wide_direct
        else:
            wide = []
            for t in sorted(by_t, key=lambda x: float(x)):
                d = by_t[t]
                wide.append([t, d.get("Protein", ""), d.get("Ligand", ""), d.get("Complex", "")])
        if wide:
            try:
                tmax = max(float(r[0]) for r in wide if r[0] not in ("", None))
            except ValueError:
                tmax = 0.0
            if tmax > 500:
                print(f"[prep] RMSD_tri: time looks like ps (max={tmax:.4g}) → /1000 → ns")
                wide = [[f"{float(r[0])/1000:.8g}", r[1], r[2], r[3]] for r in wide]
        # 统计非空系列，供出图只画有数据的列（禁止空 Complex 列进 plotxy）
        has_p = any((r[1] not in ("", None)) for r in wide)
        has_l = any((r[2] not in ("", None)) for r in wide)
        has_c = any((r[3] not in ("", None)) for r in wide)
        p = work / "RMSD_tri_wide.csv"
        _write_csv(p, ["time_ns", "Protein", "Ligand", "Complex"], wide)
        out["rmsd_tri"] = p
        out["_rmsd_tri_cols"] = {  # type: ignore[assignment]
            "Protein": has_p, "Ligand": has_l, "Complex": has_c,
        }

    # y 列名同时兼容样例（rmsd_nm…）与生产导出（Backbone/SASA/Rg…）
    simple = [
        ("rmsd_bb", "RMSD_backbone.csv", ["time_ns", "Backbone"],
         ("time_ns",), ("rmsd_nm", "Backbone", "backbone")),
        ("rmsf", "RMSF_calpha.csv", ["residue", "RMSF"],
         ("residue",), ("rmsf_nm", "RMSF", "rmsf")),
        ("hbond", "HBonds_protein_ligand.csv", ["time_ns", "Hbonds"],
         ("time_ns",), ("n_hbond", "Hbonds", "hbonds")),
        ("rg", "Rg.csv", ["time_ns", "Rg"],
         ("time_ns",), ("rg_nm", "Rg", "rg")),
        ("sasa", "SASA.csv", ["time_ns", "SASA"],
         ("time_ns",), ("sasa_nm2", "SASA", "sasa")),
        ("com", "COM_distance.csv", ["time_ns", "COM"],
         ("time_ns",), ("dist_nm", "com_nm", "COM", "com")),
        ("nvt", "NVT_temperature.csv", ["time_ns", "Temperature"],
         ("time_ns",), ("temp_K", "Temperature", "temperature")),
        ("pe", "MD_potential.csv", ["time_ns", "Potential"],
         ("time_ns",), ("pot_kj", "Potential", "potential")),
    ]

    for key, fname, header, xnames, ynames in simple:
        src = data_dir / fname
        if not src.exists():
            continue
        rows = _read_csv(src)
        body = []
        for r in rows:
            x = _col(r, *xnames)
            y = _col(r, *ynames)
            if x is None or y is None:
                continue
            body.append([x, y])
        # 防呆：time_ns 若仍是 ps（>500），统一 /1000
        if body and "time_ns" in header:
            try:
                tmax = max(float(r[0]) for r in body if r[0] not in ("", None))
            except ValueError:
                tmax = 0.0
            if tmax > 500:
                print(f"[prep] {fname}: time looks like ps (max={tmax:.4g}) → /1000 → ns")
                body = [[f"{float(r[0])/1000:.8g}", r[1]] for r in body]
        p = work / f"{key}.csv"
        _write_csv(p, header, body)
        if not body:
            print(f"[prep] WARN {fname}: 0 rows after column map (check header names) — skip plot")
            continue
        out[key] = p

    npt = data_dir / "NPT_equilibration.csv"
    if npt.exists():
        rows = _read_csv(npt)
        body = []
        for r in rows:
            t = _col(r, "time_ns")
            if t is None:
                continue
            body.append([
                t,
                _col(r, "temp_K", "Temperature", "temperature") or "",
                _col(r, "press_bar", "Pressure", "pressure") or "",
                _col(r, "density", "Density") or "",
            ])
        if body:
            try:
                tmax = max(float(r[0]) for r in body if r[0] not in ("", None))
            except ValueError:
                tmax = 0.0
            if tmax > 500:
                print(f"[prep] NPT_equilibration.csv: time looks like ps (max={tmax:.4g}) → /1000 → ns")
                body = [[f"{float(r[0])/1000:.8g}", r[1], r[2], r[3]] for r in body]
        p = work / "npt.csv"
        _write_csv(p, ["time_ns", "Temperature", "Pressure", "Density"], body)
        out["npt"] = p
    fel_meta: dict[str, dict] = {}
    for key, fname in [
        ("fel_rg", "FEL3D_RMSD_Rg_kJmol.csv"),
        ("fel_com", "FEL_RMSD_COM_kJmol.csv"),
        ("fel_sasa", "FEL_RMSD_SASA_kJmol.csv"),
        ("fel_lp", "FEL_LigandProteinRmsd_kJmol.csv"),
    ]:
        src = data_dir / fname
        if not src.exists() and key == "fel_rg":
            src = data_dir / "FEL_RMSD_Rg_kJmol.csv"
        if not src.exists():
            continue
        rows = _read_csv(src)
        triples: list[tuple[float, float, float]] = []
        for r in rows:
            x = _col(r, "x", "rmsd", "rmsd_nm")
            y = _col(r, "y", "rg", "rg_nm", "sasa", "com")
            z = _col(r, "dg_kjmol", "dg_kj", "z")
            if x is None or y is None or z is None:
                continue
            try:
                triples.append((float(x), float(y), float(z)))
            except ValueError:
                continue
        if not triples:
            continue
        xs = sorted({t[0] for t in triples})
        ys = sorted({t[1] for t in triples})
        zmap = {(t[0], t[1]): t[2] for t in triples}
        zfill = max(t[2] for t in triples)
        mat = []
        for yv in ys:
            mat.append([_lt_num(zmap.get((xv, yv), zfill)) for xv in xs])
        p_mat = work / f"{key}_mat.csv"
        _write_raw(p_mat, mat)
        out[key] = p_mat
        # 显示加密：不改 kde2d 带宽（SOP）；2D×2、3D×4 减轻 OpenGL 面片折角
        mat2d = _bilinear_zoom(mat, 2, 2)
        p_2d = work / f"{key}_mat2d.csv"
        _write_raw(p_2d, mat2d)
        out[key + "_2d"] = p_2d
        mat3d = _bilinear_zoom(mat, 4, 4)
        # 显示封顶：稀有区 ΔG 飙到数百会压扁漏斗；原始 FEL_*.csv 不动
        clip = float(FEL_DG_CLIP_KJ)
        mat3d = [
            [_lt_num(min(float(v), clip)) for v in row]
            for row in mat3d
        ]
        p_3d = work / f"{key}_mat3d.csv"
        _write_raw(p_3d, mat3d)
        out[key + "_3d"] = p_3d
        fel_meta[key] = {
            "nx": len(xs), "ny": len(ys),
            "nx3": len(mat3d[0]) if mat3d else 0,
            "ny3": len(mat3d),
            "xmin": xs[0], "xmax": xs[-1],
            "ymin": ys[0], "ymax": ys[-1],
            "zmax_clip": clip,
        }
    out["_fel_meta"] = fel_meta  # type: ignore[assignment]

    def _bar_csv(src: Path, dest_name: str, key: str) -> None:
        rows = _read_csv(src)
        body = []
        for r in rows:
            raw = _col(r, "component") or ""
            val = _col(r, "avg_kj") or _col(r, "avg_kcal") or ""
            if not raw or val in (None, ""):
                continue
            keyn = _comp_key(raw)
            hx = DECOMP_COLORS.get(keyn, C_PROTEIN)
            body.append([_comp_label(raw), val, str(_rgb_dec(hx) + 0x01000000), keyn])
        if not body:
            return
        p = work / dest_name
        _write_csv(p, ["Component", "Energy", "Rgb", "key"], body)
        out[key] = p

    if (data_dir / "MMGBSA_binding_decomp.csv").exists():
        _bar_csv(data_dir / "MMGBSA_binding_decomp.csv", "mmgbsa_decomp.csv", "decomp")
    if (data_dir / "MMGBSA_binding_table.csv").exists():
        _bar_csv(data_dir / "MMGBSA_binding_table.csv", "mmgbsa_table.csv", "etable")

    res = data_dir / "MMGBSA_residue_contrib.csv"
    if res.exists():
        rows = _read_csv(res)
        parsed = []
        for r in rows:
            name = _col(r, "residue") or ""
            val = _col(r, "total_kj")
            sd = _col(r, "sd_kj") or "0"
            if not name or val is None:
                continue
            try:
                fv = float(val)
            except ValueError:
                continue
            parsed.append((fv, name, val, sd))
        parsed.sort(key=lambda x: x[0])
        top = parsed[:15]
        p = work / "mmgbsa_residue.csv"
        idx = str(_pal_idx(C_PROTEIN))
        _write_csv(p, ["Residue", "Energy", "ColorIdx"],
                   [[name, val, idx] for _fv, name, val, _sd in top])
        out["residue"] = p

    return out


def _p(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def _layout(left: int = 16, right: int = 8, top: int = 7, bottom: int = 14) -> list[str]:
    return [
        f"layer.left = {left};",
        f"layer.right = {right};",
        f"layer.top = {top};",
        f"layer.bottom = {bottom};",
    ]


# —— 版面修复（2026-10-14）：标签完整显示。页面尺寸不动（page.width 被纵横比锁死，
#    改 page 会连带缩放字号），只调 layer 几何（% of page；layer.right/bottom 是空操作，
#    必须用 width/height）。字号在 _style_xy 里先设好，之后动 layer 不改字号。
def _page_fit(width_pct: float, height_pct: float, left_pct: float, top_pct: float) -> list[str]:
    """layer 几何（% of page）：先尺寸后位置。字号/配色/图种不变。"""
    return [
        f"layer.width = {width_pct};",
        f"layer.height = {height_pct};",
        f"layer.left = {left_pct};",
        f"layer.top = {top_pct};",
    ]


MD_VERIFY_SRC = r'''#include <origin.h>
#pragma labtalk(1)

void md_verify_fit()
{
    FILE* fp = fopen("E:\\Origin_Data\\_verify_log.txt", "a");
    LT_execute("vVPW = page.width; vVPH = page.height;");
    double pw = 0, ph = 0;
    LT_get_var("vVPW", &pw);
    LT_get_var("vVPH", &ph);
    GraphLayer gl = Project.ActiveLayer();
    RECT fr;
    fr.left = 0; fr.top = 0; fr.right = 0; fr.bottom = 0;
    gl.GetAllLinkedLayersFrame(fr);
    double L = fr.left, T = fr.top, R = fr.right, B = fr.bottom;
    int nobj = gl.GraphObjects.Count();
    for (int i = 0; i < nobj && i < 80; i++)
    {
        GraphObject go = gl.GraphObjects(i);
        string nm = go.GetName();
        char* pnm = nm.GetBuffer(0);
        bool skip = (pnm[0] == '_');
        nm.ReleaseBuffer();
        if (skip)
            continue;
        int w = go.Width;
        int h = go.Height;
        if (w <= 0 || h <= 0)
            continue;
        if (go.Left < L) L = go.Left;
        if (go.Top < T) T = go.Top;
        if (go.Left + w > R) R = go.Left + w;
        if (go.Top + h > B) B = go.Top + h;
    }
    int ok = (L >= 0 && T >= 0 && R <= pw && B <= ph) ? 1 : 0;
    LT_set_var("vMdVerifyOK", ok);
    if (fp)
    {
        fprintf(fp, "VERIFY ok=%d page=%.0fx%.0f bbox=L%.0f T%.0f R%.0f B%.0f\n",
                ok, pw, ph, L, T, R, B);
        fclose(fp);
    }
}
'''


def _install_verify_oc() -> None:
    text = MD_VERIFY_SRC.replace("\n", "\r\n")
    origin_c = Path(r"E:\Origin\OriginC\md_dump_geom.c")
    try:
        origin_c.write_text(text, encoding="ascii")
    except OSError:
        pass


def _verify_gate() -> list[str]:
    """导出前版面自检（Origin 内）：对象包围盒须全在 Page 内。
    不合格时借非法属性 ColorScale.title$ 触发 hard fail → 本图产物被弃、绝不交付。"""
    _install_verify_oc()
    return [
        'run.LoadOC("md_dump_geom.c", 16);',
        "md_verify_fit;",
        'if (vMdVerifyOK < 0.5) ColorScale.title$ = "LAYOUT_OVERFLOW";',
    ]


def _spectrum_title(clab: str) -> list[str]:
    """色阶标题在 Origin 内写入（禁止导出后补字）：Color Scale 对象属性。
    实测有效：SPECTRUM1.title$；（label -s 会生成游离标签，禁止；doc -e L 对色阶标题无效）"""
    return [f'SPECTRUM1.title$ = "{clab}";']


def _style_xy(xlab: str, ylab: str, rotate_x: int = 0) -> list[str]:
    L = [
        "page.aa = 1;",
        "label -r gbTitle;",
        "label -r gbSubtitle;",
        "label -r xb;",
        "label -r yl;",
        "layer.x.title.font = font(Arial);",
        "layer.y.title.font = font(Arial);",
        "layer.x.font = font(Arial);",
        "layer.y.font = font(Arial);",
        "layer.x.ptitlesize = 20;",
        "layer.y.ptitlesize = 20;",
        "layer.x.label.pt = 14;",
        "layer.y.label.pt = 14;",
    ]
    if ylab:
        L.append(f'label -yl "{ylab}";')
    if xlab:
        L.append(f'label -xb "{xlab}";')
    if rotate_x:
        L.append(f"layer.x.label.rotate = {rotate_x};")
    return L


def _export(png_dir: Path, stem: str) -> list[str]:
    out = _p(png_dir)
    return [
        f'page.longname$ = "{stem}";',
        "sec -p 0.4;",
        # 勿加 trimming:=0：Origin 2024 会 LT_OK 但不落盘（NO_PNG）
        f'run -xf expG2img type:=0 path:="{out}/" name:="{stem}" res:=600;',
        f'run -xf expG2img type:=5 path:="{out}/" name:="{stem}" ratio:=100;',
        "sec -p 0.8;",
    ]


def _line_color_cmds(n_series: int, colors: list[str], width: int = 1800,
                     step: bool = False) -> list[str]:
    L = []
    for i, hex_c in enumerate(colors[:n_series]):
        oc = _rgb(hex_c)
        L.append(f"layer.plot = {i + 1};")
        L.append(f"set %C -c {oc};")
        L.append(f"set %C -w {width};")
        if step:
            L.append("set %C -l 1;")
        L.append(f"layer.plot{i + 1}.color = {oc};")
    return L


def _hide_legend() -> list[str]:
    # OriginPro 2024：legend.hide / legendend 常弹 TYPE.ERRORS；只删 legend 标签
    return [
        "label -r Legend;",
        "label -r legend;",
        "label -r legend1;",
    ]


def _per_bar_colors(hex_list: list[str]) -> list[str]:
    """单色：layer.plot1.color = color(R,G,B)。
    多色：Energy 右侧 Rgb 列 + color(1, r) Direct RGB（ggplot journal muted）。"""
    lts = [_color_lt(h) for h in hex_list] or [_color_lt(C_PROTEIN)]
    first = lts[0]
    L = [
        "sec -p 0.8;",
        "layer.plot = 1;",
        "set %C -pfp 0;",
        "set %C -k 0;",
        "set %C -pbw 1;",
        "set %C -vw 0;",
        "set %C -pbc 17;",
    ]
    if len(dict.fromkeys(lts)) > 1:
        for i, lt in enumerate(lts, 1):
            L.append(f"col(Rgb)[{i}] = {lt};")
        L += [
            "layer.plot1.color = color(1, r);",
            "set %C -c color(1, r);",
        ]
    else:
        L += [
            f"layer.plot1.color = {first};",
            f"set %C -c {first};",
        ]
    L += _hide_legend()
    return L


def _bar_axis_bottom(y0: float, y1: float, n_bars: int) -> list[str]:
    """类别轴钉在图框底部（% from bottom=0），刻度不贴 y=0。零线单独画。"""
    x1 = max(n_bars, 1) + 0.5
    return [
        f"layer.y.from = {_lt_num(y0)};",
        f"layer.y.to = {_lt_num(y1)};",
        "layer.x.atZero = 0;",
        "layer.x.postype = 1;",
        "layer.x.position = 0;",
        "layer.y.postype = 0;",
        "layer.y.position = 1;",
        f"draw -n ZeroRef -l {{0.5, 0, {_lt_num(x1)}, 0}};",
        "set ZeroRef -c 18;",
        "set ZeroRef -w 500;",
    ]


def _fix_color_scale_title(clab: str, *, use_czt: bool = True) -> list[str]:
    """把模板占位「Color Scale Title」改成单位标题。

    注意：OpenGL 3D FEL 不要 ``set %C -czt``——会把漏斗曲面压成底板平面。
    """
    L = [f'label -cl "{clab}";']
    if use_czt:
        L.append(f'set %C -czt "{clab}";')
    L += [
        f'doc -e L {{if (instr(%H.text$, "Color Scale Title") > 0) %H.text$ = "{clab}";}};',
        f'doc -e L {{if (instr(%H.text$, "Color Scale") > 0) %H.text$ = "{clab}";}};',
        f'doc -e L {{if (instr(%H.text$, "Scale Title") > 0) %H.text$ = "{clab}";}};',
        "sec -p 0.3;",
    ]
    return L


def _set_axis_titles(xlab: str, ylab: str, zlab: str = "", clab: str = "",
                    *, make_xy: bool = True) -> list[str]:
    """替换模板占位符。3D OpenGL 禁止 label -xb/-yl（会在左上角再叠一套字）。"""
    L = []
    if xlab:
        L.append(f'xb.text$ = "{xlab}";')
        if make_xy:
            L.append(f'label -xb "{xlab}";')
        L.append(f'doc -e L {{if (instr(%H.text$, "X Axis Title") > 0) %H.text$ = "{xlab}";}};')
    if ylab:
        L.append(f'yl.text$ = "{ylab}";')
        if make_xy:
            L.append(f'label -yl "{ylab}";')
        L.append(f'doc -e L {{if (instr(%H.text$, "Y Axis Title") > 0) %H.text$ = "{ylab}";}};')
    if zlab:
        L += [
            f'zb.text$ = "{zlab}";',
            f'zf.text$ = "{zlab}";',
            f'doc -e L {{if (instr(%H.text$, "Z Axis Title") > 0) %H.text$ = "{zlab}";}};',
        ]
    if clab:
        L += _fix_color_scale_title(clab)
    return L


def _bar_colors_from(path: Path) -> list[str]:
    rows = _read_csv(path)
    out = []
    for r in rows:
        key = _comp_key(_col(r, "key") or _col(r, "component") or "")
        out.append(DECOMP_COLORS.get(key, C_PROTEIN))
    return out or [C_PROTEIN]


def _viridis() -> list[str]:
    # 禁止 layer.cmap.shown / ztitle：热图与 OpenGL 曲面没有该属性，
    # COM Execute 会弹出 LAYER.CMAP.SHOWN: error setting property value
    return ["set %C -cpal Viridis;"]


def _fel3d_cmap() -> list[str]:
    """3D FEL：论文 H 面板常见蓝(低)→红(高) Jet（soft；失败保留 glcmap 默认）。"""
    return ["set %C -cpal Jet;"]


CMAP_PATCHER = r'''from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
if not path.exists():
    print("[patch-cmap] missing", path)
    raise SystemExit(1)
raw = path.read_text(encoding="utf-8", errors="replace")
text = raw
text = re.sub(
    r"(<(?:ShowLines|LineShow|ShowLine|LineVisible)[^>]*>)(.*?)(</)",
    lambda m: m.group(1) + re.sub(r"[1-9]\d*", "0", m.group(2)) + m.group(3),
    text,
    flags=re.I | re.S,
)
text = re.sub(
    r"(<(?:LineWidth|LineWidths)[^>]*>)(.*?)(</)",
    lambda m: m.group(1) + re.sub(r"[0-9.]+", "0", m.group(2)) + m.group(3),
    text,
    flags=re.I | re.S,
)
text = re.sub(
    r'(Contours[^>]*\bEnable=")1(")',
    r"\g<1>0\g<2>",
    text,
    flags=re.I,
)
text = re.sub(
    r"(<(?:Contours|EnableContours)[^>]*>)\s*1\s*(</)",
    r"\g<1>0\2",
    text,
    flags=re.I,
)
bak = path.with_suffix(".before.xml")
if not bak.exists():
    bak.write_text(raw, encoding="utf-8")
path.write_text(text, encoding="utf-8")
print("[patch-cmap] wrote", path, "changed=" + str(text != raw))
'''


def patch_fel_cmap_xml(path: Path) -> int:
    """把 colormap XML 里的等值线开关/线宽置 0，保留色阶。"""
    if not path.exists():
        print("[patch-cmap] missing", path, flush=True)
        return 1
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = raw
    text = re.sub(
        r"(<(?:ShowLines|LineShow|ShowLine|LineVisible)[^>]*>)(.*?)(</)",
        lambda m: m.group(1) + re.sub(r"[1-9]\d*", "0", m.group(2)) + m.group(3),
        text,
        flags=re.I | re.S,
    )
    text = re.sub(
        r"(<(?:LineWidth|LineWidths)[^>]*>)(.*?)(</)",
        lambda m: m.group(1) + re.sub(r"[0-9.]+", "0", m.group(2)) + m.group(3),
        text,
        flags=re.I | re.S,
    )
    text = re.sub(
        r'(Contours[^>]*\bEnable=")1(")',
        r'\g<1>0\g<2>',
        text,
        flags=re.I,
    )
    text = re.sub(
        r'(<(?:Contours|EnableContours)[^>]*>)\s*1\s*(</)',
        r"\g<1>0\2",
        text,
        flags=re.I,
    )
    bak = path.with_suffix(".before.xml")
    if not bak.exists():
        bak.write_text(raw, encoding="utf-8")
    path.write_text(text, encoding="utf-8")
    print(f"[patch-cmap] wrote {path} changed={text != raw}", flush=True)
    return 0


OC_HIDE_SRC = r'''#include <origin.h>
#pragma labtalk(1)

void hide_fel_contours()
{
    GraphLayer gl = Project.ActiveLayer();
    int n = gl.DataPlots.Count();
    for (int i = 0; i < n; i++)
    {
        DataPlot dp = gl.DataPlots(i);
        if (!dp.IsValid())
            continue;
        Tree trf;
        trf = dp.GetFormat(FPB_ALL, FOB_ALL, true, true);
        trf.Root.Surface.Mesh.Enable.nVal = 0;
        trf.Root.Surface.ColorMap.Contours.Enable.nVal = 0;
        trf.Root.ColorMap.Contours.Enable.nVal = 0;
        trf.Root.ColorMap.ShowGridLines.nVal = 0;
        trf.Root.EnableContour.nVal = 0;
        dp.UpdateThemeIDs(trf.Root);
        dp.ApplyFormat(trf, true, true);
    }
}
'''


def _install_hide_oc(work: Path) -> None:
    text = OC_HIDE_SRC.replace("\n", "\r\n")
    (work / "hideFelContours.c").write_text(text, encoding="ascii")
    origin_c = Path(r"E:\Origin\OriginC\hideFelContours.c")
    try:
        origin_c.write_text(text, encoding="ascii")
    except OSError:
        pass


def _fel3d_hide_lines(work: Path) -> list[str]:
    """只关曲面上黑色 mesh/等高线，不动 Jet 色板。"""
    _install_hide_oc(work)
    return [
        'run.LoadOC("hideFelContours.c", 16);',
        "hide_fel_contours;",
        "layer.plot = 1;",
        "set %C -b3m 0;",
        "set %C -b3t 1;",
        "layer.mesh.enable = 0;",
        "layer.plot1.contlines = 0;",
        "layer.plot = 2;",
        "set %C -b3m 0;",
        "layer.plot2.contlines = 0;",
        "layer.plot = 1;",
        "set %C -b3m 0;",
        "hide_fel_contours;",
    ]


def build_jobs(files: dict[str, Path], png_dir: Path) -> list[tuple[str, list[str]]]:
    """每张图一组 LabTalk（单独 Origin 进程执行）。"""
    jobs: list[tuple[str, list[str]]] = []
    fel_meta: dict[str, dict] = files.get("_fel_meta") or {}  # type: ignore[assignment]

    def add_line(key: str, csv_path: Path, ycols: list[int], colors: list[str],
                 stem: str, xlab: str, ylab: str, *, legend: bool = False,
                 step: bool = False, xnames: tuple[str, ...] = ("time_ns", "residue"),
                 ynames: tuple[str, ...] = (), floor0: bool = False,
                 right: int = 8) -> None:
        iy = ",".join(f"(1,{c})" for c in ycols)
        # X：时间序列只用 time_ns；残基图只用 residue（勿混进同一个 names 列表）
        if "time" in xlab.lower():
            xs = _floats(csv_path, "time_ns")
        elif "residue" in xlab.lower():
            xs = _floats(csv_path, "residue")
        else:
            xs = _floats(csv_path, *xnames)
        if ynames:
            ys = _floats(csv_path, *ynames)
        else:
            ys = []
            rows = _read_csv(csv_path)
            for r in rows:
                vals = list(r.values())
                for c in ycols:
                    if c - 1 < len(vals) and vals[c - 1] not in (None, ""):
                        try:
                            ys.append(float(vals[c - 1]))
                        except ValueError:
                            pass
        if len(xs) < 2 or len(ys) < 2:
            print(f"[jobs] SKIP {stem}: need >=2 points (nx={len(xs)} ny={len(ys)}) in {csv_path.name}")
            return
        x0, x1 = _span(xs, pad=0.02, floor0=("time" in xlab.lower()))
        y0, y1 = _span(ys, pad=0.08, floor0=floor0)
        if abs(x1 - x0) < 1e-9 or abs(y1 - y0) < 1e-12:
            print(f"[jobs] SKIP {stem}: degenerate axis x=[{x0},{x1}] y=[{y0},{y1}]")
            return
        # 时间轴若仍落在 ~1 ns 而数据跨度更大，说明读错列——拒画
        if "time" in xlab.lower() and max(xs) > 2.0 and x1 <= 1.0 + 1e-6:
            print(f"[jobs] SKIP {stem}: x-axis capped at 1 but data max={max(xs):.3g}")
            return
        L = [
            f'newbook name:="{key}" option:=lsname;',
            f'impASC fname:="{_p(csv_path)}" options.names.FNameToBk:=0 options.names.FNameToSht:=0;',
            "sec -p 0.3;",
            f"plotxy iy:=({iy}) plot:=200;",
        ]
        L += _line_color_cmds(len(ycols), colors, step=step)
        L.append("rescale;")
        L.append(f"layer.x.from = {_lt_num(x0)};")
        L.append(f"layer.x.to = {_lt_num(x1)};")
        L.append(f"layer.y.from = {_lt_num(y0)};")
        L.append(f"layer.y.to = {_lt_num(y1)};")
        L += _style_xy(xlab, ylab)
        # 2026-10-14 版面修复：Y 轴标题（横排）与 02 图例完整显示（左/上留白）
        L += _page_fit(56.0, 71.84, 34.2, 9.5)
        if legend:
            L.append("legendupdate;")
            # legend.show 在部分版本也弹 TYPE.ERRORS；有多系列时保留 legendupdate 即可
        else:
            L += _hide_legend()
        L += _verify_gate()
        L += _export(png_dir, stem)
        jobs.append((stem, L))
    def add_simple_bar(key: str, csv_path: Path, stem: str, xlab: str, ylab: str,
                       *, rotate_x: int = 0, labeled: bool = False,
                       horizontal: bool = False, single: str | None = None) -> None:
        yvals = _floats(csv_path, "energy", "total_kj")
        plot = 203
        y0, y1 = _span(yvals, pad=0.16, include0=True)
        n_bars = max(len(yvals), 1)
        bot = 34 if rotate_x else 20
        left = 30
        xlab_pt = 14
        if horizontal:
            bot = 40
            rotate_x = 45
            xlab_pt = 11
        if labeled:
            bot = max(bot, 22)
        lay = _layout(left=left, right=10, top=10, bottom=bot)
        colors = [single] * n_bars if single else _bar_colors_from(csv_path)
        L = [
            f'newbook name:="{key}" option:=lsname;',
            f'impASC fname:="{_p(csv_path)}" options.names.FNameToBk:=0 options.names.FNameToSht:=0;',
            "sec -p 0.4;",
            "wks.col1.type = 4;",
            "wks.col2.type = 2;",
            f"plotxy iy:=(1,2) plot:={plot};",
        ]
        L += _per_bar_colors(colors)
        L.append("set %C -vg 40;")
        L.append("rescale;")
        L += _bar_axis_bottom(y0, y1, n_bars)
        L += lay
        L += _style_xy(xlab, ylab, rotate_x=rotate_x)
        L += _set_axis_titles(xlab, ylab)
        L += [
            "layer.x.atZero = 0;",
            "layer.x.postype = 1;",
            "layer.x.position = 0;",
            "layer.x.showAxes = 3;",
            "layer.y.showAxes = 3;",
            f"layer.x.label.pt = {xlab_pt};",
        ]
        if labeled:
            L += [
                "set %C -dl 1;",
                "layer.plot1.label.pt = 10;",
            ]
        L += _hide_legend()
        L += _export(png_dir, stem)
        jobs.append((stem, L))

    def add_fel2d(key: str, csv_path: Path, stem: str, xlab: str, ylab: str,
                  meta: dict) -> None:
        xmin, xmax = meta["xmin"], meta["xmax"]
        ymin, ymax = meta["ymin"], meta["ymax"]
        L = [
            f'newbook name:="{key}" mat:=1 option:=lsname;',
            f'impASC fname:="{_p(csv_path)}" options.names.FNameToBk:=0 options.names.FNameToSht:=0;',
            "sec -p 0.5;",
            f"matrix -ps X {_lt_num(xmin)} {_lt_num(xmax)};",
            f"matrix -ps Y {_lt_num(ymin)} {_lt_num(ymax)};",
            "sec -p 0.5;",
            "run.section(Plot3D,ContourColor);",
            "sec -p 0.8;",
            "set %C -cmf 1;",
            "set %C -cmg 0;",
            "set %C -cmc 0;",
            "set %C -vg 0;",
        ] + [f"layer.cmap.line{i} = 0;" for i in range(1, 33)] + [
            "layer.CMap.lineColorLink = 1;",
        ]
        L += _viridis()
        # 2026-10-14 版面修复：页面尺寸不动（page.width 被纵横比锁死），调 layer 让
        # 右侧色阶图例/标题与左侧 Y 轴标题全部落在页面内（留 ≥100px 边距）。
        # 顺序：先设字号（_style_xy/ptitlesize），再动 layer 几何（字号不随 layer 缩）
        L += _style_xy(xlab, ylab)
        L += [
            "layer.x.label.rotate = 0;",
            "layer.x.showAxes = 3;",
            "layer.y.showAxes = 3;",
            "layer.x.ptitlesize = 22;",
            "layer.y.ptitlesize = 22;",
        ]
        L += _page_fit(41.5, 53.1, 36, 19.5)
        L += _set_axis_titles(xlab, ylab, clab="G (kJ/mol)", make_xy=True)
        L += _fix_color_scale_title("G (kJ/mol)")
        L += _spectrum_title("G (kJ/mol)")
        L += _verify_gate()
        L += _export(png_dir, stem)
        jobs.append((stem, L))

    def add_fel3d(key: str, csv_path: Path, stem: str, xlab: str, ylab: str,
                  meta: dict) -> None:
        """漏斗曲面 + 底板投影 + ΔG 封顶；曲面上不画黑色 mesh 条纹。"""
        xmin, xmax = meta["xmin"], meta["xmax"]
        ymin, ymax = meta["ymin"], meta["ymax"]
        zclip = float(meta.get("zmax_clip") or FEL_DG_CLIP_KJ)
        L = [
            f'newbook name:="{key}" mat:=1 option:=lsname;',
            f'impASC fname:="{_p(csv_path)}" options.names.FNameToBk:=0 options.names.FNameToSht:=0;',
            "sec -p 0.5;",
            f"matrix -ps X {_lt_num(xmin)} {_lt_num(xmax)};",
            f"matrix -ps Y {_lt_num(ymin)} {_lt_num(ymax)};",
            # 固定：OpenGL glcmap + Jet（勿改非 OpenGL，会丢色阶）
            "plotm im:=<active> plot:=103 ogl:=<new template:=glcmap>;",
            "sec -p 1;",
        ]
        L += _fel3d_cmap()
        L += [
            "set %C -b3m 0;",
            "set %C -b3t 1;",
            "set %C -t 0;",
            "layer.plot1.transparency = 0;",
            "layer.mesh.enable = 0;",
            "layer.plot1.contlines = 0;",
            "page.aa = 1;",
            # 底板投影（填色等高，同样关 mesh）
            "layer -ip103 %C;",
            "sec -p 0.3;",
            "layer.plot = 2;",
            "set %C -spf 1;",
            "set %C -spz 0;",
            "set %C -b3t 1;",
            "set %C -b3m 0;",
            "layer.plot = 1;",
            "set %C -b3m 0;",
            "set %C -b3t 1;",
            # 勿对 OpenGL 图层套 _layout：会压扁/丢掉漏斗曲面，只剩底板
            "layer.view.horizontal = 35;",
            "layer.view.vertical = 25;",
            f"layer.z.from = 0;",
            f"layer.z.to = {_lt_num(zclip)};",
            "layer.x.showGrids = 1;",
            "layer.y.showGrids = 1;",
            "layer.z.showGrids = 1;",
            "label -r gbTitle;",
        ]
        L += _fel3d_hide_lines(csv_path.parent)
        # 3D：轴标题可写，但色阶标题勿用 -czt（会压扁曲面）
        L += _set_axis_titles(xlab, ylab, zlab="G (kJ/mol)", clab="",
                             make_xy=False)
        L += [
            "sec -p 0.4;",
            "layer.plot = 1;",
            "set %C -cpal Jet;",
            "set %C -b3m 0;",
            "set %C -b3t 1;",
            "layer.mesh.enable = 0;",
            "layer.plot1.contlines = 0;",
            "page.aa = 1;",
        ]
        L += _fix_color_scale_title("G (kJ/mol)", use_czt=False)
        # 2026-10-14：色阶标题在 Origin 内写入（3D 只用对象属性，勿 label -s 兜底）
        L += [f'SPECTRUM1.title$ = "G (kJ/mol)";']
        L += _verify_gate()
        L += _export(png_dir, stem)
        jobs.append((stem, L))

    if "rmsd_tri" in files:
        flags = files.get("_rmsd_tri_cols") or {}  # type: ignore[assignment]
        series_spec = [
            (2, C_PROTEIN, "Protein"),
            (3, C_LIGAND, "Ligand"),
            (4, C_COMPLEX, "Complex"),
        ]
        ycols, colors, ynames = [], [], []
        for col, color, name in series_spec:
            # flags 缺失时默认画（兼容旧 prep）
            if flags and not flags.get(name, False):
                continue
            ycols.append(col)
            colors.append(color)
            ynames.append(name)
        if ycols:
            add_line("RMSDtri", files["rmsd_tri"], ycols, colors,
                     "RmsdProteinLigandComplex",
                     "Time (ns)", "RMSD (nm)", legend=True, floor0=True,
                     ynames=tuple(ynames), right=18)
    if "rmsd_bb" in files:
        add_line("RMSDbb", files["rmsd_bb"], [2], [C_PROTEIN],
                 "RmsdBackbone", "Time (ns)", "RMSD (nm)",
                 ynames=("Backbone",), floor0=True)
    if "rmsf" in files:
        add_line("RMSF", files["rmsf"], [2], [C_LIGAND],
                 "RmsfCalpha", "Residue index", "RMSF (nm)",
                 xnames=("residue",), ynames=("RMSF",), floor0=True)
    if "hbond" in files:
        add_line("Hbond", files["hbond"], [2], [C_GREEN],
                 "HbondNum", "Time (ns)", "H-bond number",
                 ynames=("Hbonds",), step=True, floor0=True)
    if "rg" in files:
        add_line("Rg", files["rg"], [2], [C_COMPLEX],
                 "RadiusGyration", "Time (ns)", "Rg (nm)", ynames=("Rg",))
    if "sasa" in files:
        add_line("SASA", files["sasa"], [2], [C_ACCENT],
                 "Sasa", "Time (ns)", "SASA (nm^2)", ynames=("SASA",))
    if "com" in files:
        add_line("COM", files["com"], [2], [C_COM],
                 "ComDistance", "Time (ns)", "COM distance (nm)", ynames=("COM",))
    if "nvt" in files:
        add_line("NVT", files["nvt"], [2], [C_PROTEIN],
                 "NvtTemperature", "Time (ns)", "Temperature (K)",
                 ynames=("Temperature",))
    if "npt" in files:
        add_line("NPTt", files["npt"], [2], [C_LIGAND],
                 "NptTemperature", "Time (ns)", "Temperature (K)",
                 ynames=("Temperature",))
        add_line("NPTp", files["npt"], [3], [C_GREEN],
                 "NptPressure", "Time (ns)", "Pressure (bar)",
                 ynames=("Pressure",))
        add_line("NPTd", files["npt"], [4], [C_COMPLEX],
                 "NptDensity", "Time (ns)", "Density (kg/m^3)",
                 ynames=("Density",))
    if "pe" in files:
        add_line("PE", files["pe"], [2], [C_ACCENT],
                 "MdPotential", "Time (ns)", "Potential (kJ/mol)",
                 ynames=("Potential",))

    fel_map = [
        ("fel_rg", "FreeEnergyLandscape", "FreeEnergyLandscape3D",
         "RMSD (nm)", "Rg (nm)"),
        ("fel_com", "FreeEnergyRmsdCom", "FreeEnergyRmsdCom3D",
         "RMSD (nm)", "COM (nm)"),
        ("fel_sasa", "FreeEnergyRmsdSasa", "FreeEnergyRmsdSasa3D",
         "RMSD (nm)", "SASA (nm^2)"),
        ("fel_lp", "FreeEnergyLigandProteinRmsd", "FreeEnergyLigandProteinRmsd3D",
         "Ligand RMSD (nm)", "Protein RMSD (nm)"),
    ]
    for key, stem2, stem3, xlab, ylab in fel_map:
        if key not in files:
            continue
        meta = fel_meta.get(key) or {}
        add_fel2d(key + "2", files.get(key + "_2d") or files[key], stem2, xlab, ylab, meta)
        add_fel3d(key + "3", files.get(key + "_3d") or files[key], stem3, xlab, ylab, meta)

    if "decomp" in files:
        add_simple_bar("Decomp", files["decomp"], "BindingEnergyDecomp",
                       "", "Energy (kJ/mol)", rotate_x=0)
        add_simple_bar("DecompL", files["decomp"], "BindingEnergyLabeled",
                       "", "Energy (kJ/mol)", rotate_x=0, labeled=True)
    if "etable" in files:
        add_simple_bar("Etable", files["etable"], "BindingEnergyTable",
                       "", "Energy (kJ/mol)", rotate_x=35)
    if "residue" in files:
        add_simple_bar("ResE", files["residue"], "ResidueEnergyContrib",
                       "", "Energy (kJ/mol)", rotate_x=45, horizontal=True, single=C_PROTEIN)

    return jobs


def write_job_ogs(work: Path, stem: str, lines: list[str]) -> Path:
    ogs = work / f"plot_{stem}.ogs"
    # 勿写 type.errors=0：OriginPro 2024 会弹 TYPE.ERRORS: error setting property value
    body = ["[Main]", f"// one Origin session → {stem}"] + lines
    ogs.write_text("\n".join(body) + "\n", encoding="utf-8")
    return ogs


def kill_origin() -> None:
    subprocess.run(
        ["taskkill", "/F", "/IM", "Origin64.exe", "/T"],
        capture_output=True, text=True,
    )
    subprocess.run(
        ["taskkill", "/F", "/IM", "OriginC.exe", "/T"],
        capture_output=True, text=True,
    )
    subprocess.run(
        ["taskkill", "/F", "/IM", "Origin.exe", "/T"],
        capture_output=True, text=True,
    )
    time.sleep(1.5)


def _ps_one_plot(ogs: Path) -> str:
    """COM 桥：捕获 Execute 布尔值 / COM 异常 / LabTalk vErr（@NOE 抑弹窗）。

    官方约定（docs.originlab.com）：
      - Application.Execute → Boolean（False=脚本失败）
      - 花括号 + @NOE=0 + vErr 标志可吞错误并汇报（Error Handling）
      - LTVar('vErr') 读回 LabTalk 数值变量
    Soft 行（删 legend 标签等）失败不计；Hard 行失败则 exit 3。
    """
    ogs_win = str(ogs.resolve())
    exe = str(ORIGIN_EXE)
    py = sys.executable
    return rf"""
$ErrorActionPreference = 'Continue'
$exe = '{exe}'
$ogs = '{ogs_win}'
$py = '{py}'
function Test-SoftLt([string]$line) {{
  # 装饰/可选：失败不删图。核心仍 hard（impASC/plotxy/expG2img/轴范围等）
  if ($line -match '^label\s+-r\s+(Legend|legend|legend1)\s*;?\s*$') {{ return $true }}
  if ($line -match '^legendupdate\s*;?\s*$') {{ return $true }}
  if ($line -match '^ColorScale\d*\.title\$') {{ return $true }}
  if ($line -match '^ColorScale\.title\$') {{ return $true }}
  if ($line -match '^layer\.cmap\.zTitle\$') {{ return $true }}
  if ($line -match '^set %C -czt') {{ return $true }}
  if ($line -match '^FelCBarUnit\.') {{ return $true }}
  if ($line -match '^label -r FelCBarUnit') {{ return $true }}
  if ($line -match '^label -s FelCBarUnit') {{ return $true }}
  if ($line -match '^export\.trimming') {{ return $true }}
  if ($line -match '^hide_fel_contours\s*;?\s*$') {{ return $true }}
  if ($line -match '^md_\w+\s*;?\s*$') {{ return $true }}
  if ($line -match '^md_verify_fit\s*;?\s*$') {{ return $true }}
  if ($line -match '^SPECTRUM\d*\.') {{ return $true }}
  if ($line -match '^spectrum\d*\.') {{ return $true }}
  if ($line -match '^ZCOLORS\.') {{ return $true }}
  if ($line -match '^3DCOLOR\.') {{ return $true }}
  if ($line -match '^label -s ') {{ return $true }}
  if ($line -match '^set %C -c[lt] ') {{ return $true }}
  if ($line -match '^run\.LoadOC\("md_') {{ return $true }}
  if ($line -match '^run\.LoadOC\(') {{ return $true }}
  if ($line -match '^layer\.plot\d*\.contlines\s*=') {{ return $true }}
  if ($line -match '^layer\.plot1\.mesh\s*=') {{ return $true }}
  if ($line -match '^layer\.mesh\.enable\s*=') {{ return $true }}
  if ($line -match '^layer\.cmap\.numMajorLevels\s*=') {{ return $true }}
  if ($line -match '^layer\.cmap\.showLines\(') {{ return $true }}
  if ($line -match '^layer\.light\.enable\s*=') {{ return $true }}
  if ($line -match '^page\.antialias\s*=') {{ return $true }}
  if ($line -match '^layer\.cmap\.') {{ return $true }}
  if ($line -match '^layer\.CMap\.') {{ return $true }}
  if ($line -match '^set %C -cm') {{ return $true }}
  if ($line -match '^set %C -cpal Jet\s*;?\s*$') {{ return $true }}
  if ($line -match '^layer\s+-ip103') {{ return $true }}
  if ($line -match '^layer\.plot\s*=') {{ return $true }}
  if ($line -match '^set %C -sp[fz]\s+') {{ return $true }}
  if ($line -match '^layer\.view\.') {{ return $true }}
  if ($line -match '^layer\.z\.(from|to)\s*=') {{ return $true }}
  if ($line -match '^ColorScale\d*\.title\$') {{ return $true }}
  return $false
}}
Get-Process Origin64,OriginC,Origin -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1
Start-Process -FilePath $exe
$deadline = (Get-Date).AddSeconds(45)
do {{
  Start-Sleep -Seconds 2
}} while (-not (Get-Process Origin64 -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline)
Start-Sleep -Seconds 10
$app = $null
foreach ($id in @('Origin.ApplicationSI','Origin.Application')) {{
  try {{ $app = New-Object -ComObject $id; break }} catch {{}}
}}
if ($null -eq $app) {{
  Write-Output 'COM_FAIL no Origin ProgID'
  exit 2
}}
try {{ $app.Visible = 1 }} catch {{}}
# 关闭错误弹窗强制弹出（仍写 Message Log）；属性非法时靠 Execute=False / vErr 捕获
try {{ [void]$app.Execute('@NOE = 0;') }} catch {{}}
$nOk = 0
$nFail = 0
$hardFail = 0
Get-Content -LiteralPath $ogs -Encoding UTF8 | ForEach-Object {{
  $line = $_.Trim()
  if (-not $line) {{ return }}
  if ($line.StartsWith('[')) {{ return }}
  if ($line.StartsWith('//PY_PATCH_FEL_CMAP')) {{
    $xml = $line.Substring(20).Trim()
    $patcher = Join-Path ([IO.Path]::GetDirectoryName($xml)) 'patch_cmap.py'
    Write-Output ("PY_PATCH " + $xml)
    & $py $patcher $xml
    return
  }}
  if ($line.StartsWith('//')) {{ return }}
  $soft = Test-SoftLt $line
  # 花括号 + vErr：出错则跳到 }}，vErr 保持 1（官方 Error Handling）
  $wrapped = "vErr=1; {{ $line `n vErr=0; }}"
  try {{
    $ok = $app.Execute($wrapped)
    $verr = $null
    try {{ $verr = [double]$app.LTVar('vErr') }} catch {{ $verr = -1 }}
    $failed = (-not $ok) -or ($verr -eq 1)
    if ($failed) {{
      Write-Output ("LT_FAIL ok=" + $ok + " vErr=" + $verr + " soft=" + $soft + " | " + $line)
      $script:nFail++
      if (-not $soft) {{ $script:hardFail++ }}
    }} else {{
      Write-Output ("LT_OK | " + $line)
      $script:nOk++
    }}
  }} catch {{
    Write-Output ("LT_EXC soft=" + $soft + " | " + $line + " | " + $_)
    $script:nFail++
    if (-not $soft) {{ $script:hardFail++ }}
  }}
}}
Write-Output ("COM_DONE ok=" + $nOk + " fail=" + $nFail + " hardFail=" + $hardFail)
Start-Sleep -Seconds 2
try {{ $app.Execute('doc.saved = 1') }} catch {{}}
try {{ $app.Exit() }} catch {{}}
Start-Sleep -Seconds 3
Get-Process Origin64,OriginC,Origin -ErrorAction SilentlyContinue | Stop-Process -Force
if ($hardFail -gt 0) {{
  Write-Output ('COM_LT_FAIL hardFail=' + $hardFail)
  exit 3
}}
Write-Output 'COM_EXIT'
"""


def run_one_plot(ogs: Path, png_path: Path, timeout_s: int = 90) -> str:
    if not ORIGIN_EXE.exists():
        return f"MISSING_EXE {ORIGIN_EXE}"
    ps1 = ogs.with_suffix(".ps1")
    ps1.write_text(_ps_one_plot(ogs), encoding="utf-8")
    for ext in (".png", ".svg"):
        old = png_path.with_suffix(ext)
        if old.exists():
            try:
                old.unlink()
            except OSError:
                pass
    kill_origin()
    t0 = time.time()
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass",
             "-File", str(ps1)],
            capture_output=True, text=True, timeout=timeout_s, encoding="utf-8",
            errors="replace",
        )
        msg = (r.stdout or "") + "\n" + (r.stderr or "")
        tail = msg[-4000:] if len(msg) > 4000 else msg
        try:
            print(tail, flush=True)
        except UnicodeEncodeError:
            print(tail.encode("ascii", "backslashreplace").decode("ascii"), flush=True)
        kill_origin()
        fresh = (
            png_path.exists()
            and png_path.stat().st_size > 2000
            and png_path.stat().st_mtime >= t0 - 2
        )
        # 有 LabTalk hard 失败时：即使出了 PNG 也判失败（避免带错轴/错属性的图蒙混过关）
        import re as _re
        m = _re.search(r"hardFail=(\d+)", msg)
        hf = int(m.group(1)) if m else (1 if ("COM_LT_FAIL" in msg or r.returncode == 3) else 0)
        if hf > 0 or "COM_LT_FAIL" in msg or r.returncode == 3:
            if fresh:
                try:
                    png_path.unlink()
                    svg = png_path.with_suffix(".svg")
                    if svg.exists():
                        svg.unlink()
                except OSError:
                    pass
            return f"LT_FAIL hardFail={hf} exit={r.returncode}"
        if "COM_FAIL" in msg:
            return "COM_FAIL"
        if fresh and r.returncode == 0:
            return f"OK {png_path.name} {png_path.stat().st_size}"
        if fresh:
            return f"PNG_BUT_BAD_EXIT exit={r.returncode}"
        return f"NO_PNG exit={r.returncode}"
    except subprocess.TimeoutExpired:
        kill_origin()
        if png_path.exists() and png_path.stat().st_size > 2000:
            return f"TIMEOUT_BUT_PNG {png_path.name}"
        return "TIMEOUT_NO_PNG"
    except Exception as e:
        kill_origin()
        return f"COM_ERROR {e}"


def copy_origin_figures(png_dir: Path, result_root: Path) -> int:
    """Origin PNG/SVG → {主题}图/（中英对照文件名）。"""
    n = 0
    if not png_dir.exists():
        return 0
    for p in png_dir.glob("*.*"):
        if p.suffix.lower() not in {".png", ".svg"}:
            continue
        if p.stem.startswith("Smoke") or p.stem.startswith("FelTest"):
            continue
        zh = STEM_ZH.get(p.stem, p.stem)
        topic = topic_zh(p.stem)
        dest_name = _MD_LAYOUT.numbered_name(topic, f"{zh}{p.suffix}")
        dest = figure_dir(result_root, topic) / dest_name
        if _copy_file(p, dest):
            n += 1
    return n


def copy_topic_data(data_dir: Path, result_root: Path) -> int:
    n = 0
    for stem, names in STEM_DATA_CSV.items():
        dest_dir = figure_dir(result_root, topic_zh(stem))
        dest_dir.mkdir(parents=True, exist_ok=True)
        for name in names:
            src = data_dir / name
            if _copy_file(src, dest_dir / name):
                n += 1
    return n


def topics_for_table(name: str) -> list[str]:
    if name.startswith("审计") or "PlotQA" in name:
        return []
    if "二维相互作用" in name or "LigPlot" in name:
        return ["二维相互作用"]
    for key in sorted(THEME_TOPICS, key=len, reverse=True):
        if key in name:
            return THEME_TOPICS[key]
    return []


def copy_result_tables(old_tab: Path, result_root: Path) -> tuple[int, int]:
    n_data, n_rep = 0, 0
    report = result_root / "报告文件"
    report.mkdir(parents=True, exist_ok=True)
    if not old_tab.exists():
        return 0, 0
    for csvf in old_tab.glob("*.csv"):
        topics = topics_for_table(csvf.name)
        if not topics:
            if csvf.name.startswith("审计") or "PlotQA" in csvf.name:
                if _copy_file(csvf, report / csvf.name):
                    n_rep += 1
            continue
        for topic in topics:
            dest = figure_dir(result_root, topic) / csvf.name
            if _copy_file(csvf, dest):
                n_data += 1
    return n_data, n_rep


def copy_code_plots(old_fig: Path, result_root: Path) -> int:
    n = 0
    if not old_fig.exists():
        return 0
    origin_zh = set(STEM_ZH.values())
    for p in old_fig.iterdir():
        if not p.is_file() or p.suffix.lower() not in {".png", ".svg", ".ps"}:
            continue
        placed = False
        for topic, names in CODE_PLOT_FILES.items():
            base = re.sub(r"^\d{2}_", "", p.name)
            if p.name in names or base in names:
                dest = figure_dir(result_root, topic) / _MD_LAYOUT.numbered_name(topic, base)
                if _copy_file(p, dest):
                    n += 1
                placed = True
                break
        if placed:
            continue
        stem = re.sub(r"^\d{2}_", "", p.stem)
        if stem in STEM_ZH or stem in origin_zh:
            topic = topic_zh(stem)
            dest_name = _MD_LAYOUT.numbered_name(topic, f"{STEM_ZH.get(stem, stem)}{p.suffix}")
            dest = figure_dir(result_root, topic) / dest_name
            if _copy_file(p, dest):
                n += 1
    return n


def rewrite_sample_report(result_root: Path) -> bool:
    sample_root = result_root.parent.parent
    return bool(_MD_LAYOUT.rewrite_report_paths(sample_root, dry=False))


def _rm_tree(path: Path) -> int:
    n = 0
    if not path.exists():
        return 0
    for p in sorted(path.rglob("*"), reverse=True):
        try:
            if p.is_file():
                p.unlink()
                n += 1
            elif p.is_dir():
                p.rmdir()
        except OSError:
            pass
    try:
        path.rmdir()
    except OSError:
        pass
    return n


def _flatten_old_topic_dirs(result_root: Path) -> int:
    """把旧的 {主题}图数据 / 图代码绘图 / 图Origin绘图 并进 {主题}图/。"""
    n = 0
    suffixes = ("图Origin绘图", "图代码绘图", "图数据")
    for d in list(result_root.iterdir()):
        if not d.is_dir():
            continue
        matched = None
        for suf in suffixes:
            if d.name.endswith(suf) and d.name != suf:
                matched = suf
                break
        if not matched:
            continue
        dest = result_root / (d.name[: -len(matched)] + "图")
        dest.mkdir(parents=True, exist_ok=True)
        for p in d.iterdir():
            if p.is_file() and _copy_file(p, dest / p.name):
                n += 1
        n += _rm_tree(d)
    return n


def layout_sample_results(result_root: Path, data_dir: Path) -> dict[str, int]:
    """一图一文件夹：{主题}图/ 内同时放 CSV 与 PNG/SVG。报告仍在 报告文件/。"""
    stats = {"origin": 0, "data": 0, "code": 0, "report": 0, "removed": 0}
    old_fig = result_root / "图片文件"
    old_origin = old_fig / "Origin出图_OriginFigures"
    old_tab = result_root / "数据文件"
    report = result_root / "报告文件"
    report.mkdir(parents=True, exist_ok=True)

    stats["removed"] += _flatten_old_topic_dirs(result_root)

    cache_fig = data_dir / "OriginFigures"
    if cache_fig.exists():
        stats["origin"] += copy_origin_figures(cache_fig, result_root)
    if old_origin.exists():
        stats["origin"] += copy_origin_figures(old_origin, result_root)

    stats["data"] += copy_topic_data(data_dir, result_root)
    n_tab, n_rep = copy_result_tables(old_tab, result_root)
    stats["data"] += n_tab
    stats["report"] += n_rep
    stats["code"] += copy_code_plots(old_fig, result_root)

    for stem in STEM_ZH:
        figure_dir(result_root, topic_zh(stem)).mkdir(parents=True, exist_ok=True)
    for topic in CODE_PLOT_FILES:
        figure_dir(result_root, topic).mkdir(parents=True, exist_ok=True)

    rewrite_sample_report(result_root)

    for old in (old_origin, old_fig, old_tab):
        stats["removed"] += _rm_tree(old)
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(DEFAULT_DATA))
    ap.add_argument("--no-copy", action="store_true")
    ap.add_argument("--layout-only", action="store_true",
                    help="只按图种重组样例结果目录，不启动 Origin")
    ap.add_argument("--only", default="",
                    help="comma-separated stems, e.g. RmsdBackbone,ResidueEnergyContrib")
    ap.add_argument("--patch-cmap", default="",
                    help="internal: zero ShowLines in a saved Origin colormap XML")
    args = ap.parse_args()
    if args.patch_cmap.strip():
        return patch_fel_cmap_xml(Path(args.patch_cmap.strip()))
    data_dir = Path(args.data_dir)
    if args.layout_only:
        stats = layout_sample_results(SAMPLE_RESULT, data_dir)
        print("[layout]", stats, flush=True)
        return 0
    work = data_dir / "_origin_in"
    png_dir = data_dir / "OriginFigures"
    png_dir.mkdir(parents=True, exist_ok=True)
    if not args.only.strip():
        for old in png_dir.glob("*.*"):
            if old.suffix.lower() in {".png", ".svg"}:
                try:
                    old.unlink()
                except OSError:
                    pass
    print("[prep] CSVs →", work, flush=True)
    files = prepare_inputs(data_dir, work)
    keys = [k for k in files if not k.startswith("_") and not k.endswith(("xlab", "ylab"))]
    print("[prep] sheets:", ", ".join(str(k) for k in keys), flush=True)
    jobs = build_jobs(files, png_dir)
    if args.only.strip():
        allow = {s.strip() for s in args.only.split(",") if s.strip()}
        jobs = [(s, L) for s, L in jobs if s in allow]
    print(f"[jobs] {len(jobs)} Origin sessions (one figure each)", flush=True)
    ok_n = 0
    for i, (stem, lines) in enumerate(jobs, 1):
        print(f"\n===== [{i}/{len(jobs)}] {stem} =====", flush=True)
        ogs = write_job_ogs(work, stem, lines)
        timeout = 150 if "FreeEnergy" in stem else 100
        status = run_one_plot(ogs, png_dir / f"{stem}.png", timeout_s=timeout)
        print(f"[origin] {stem}: {status}", flush=True)
        vline = ""
        try:
            vlog = Path(r"E:\Origin_Data\_verify_log.txt")
            if vlog.exists():
                vs = [ln for ln in vlog.read_text(errors="replace").splitlines()
                      if ln.startswith("VERIFY")]
                if vs:
                    vline = vs[-1]
        except OSError:
            pass
        try:
            with open(r"E:\Origin_Data\_verify_report.txt", "a", encoding="utf-8") as fh:
                fh.write(f"{stem}\t{status}\t{vline}\n")
        except OSError:
            pass
        if status.startswith("OK") or status.startswith("TIMEOUT_BUT"):
            ok_n += 1
    pngs = sorted(p for p in png_dir.glob("*.png")
                  if not p.stem.startswith("Smoke") and not p.stem.startswith("FelTest"))
    print(f"\n[png] {len(pngs)} files in {png_dir}  sessions_ok={ok_n}/{len(jobs)}",
          flush=True)
    for p in pngs:
        print(" ", p.name, p.stat().st_size, flush=True)
    if not args.no_copy:
        stats = layout_sample_results(SAMPLE_RESULT, data_dir)
        print(f"[layout] {stats}", flush=True)
    return 0 if ok_n else 1


if __name__ == "__main__":
    sys.exit(main())
