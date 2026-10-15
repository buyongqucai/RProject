# -*- coding: utf-8 -*-
"""21_多对多3x4批量对接_ADGPU.py

用户新方案（多对多，不得 1 对 1）：
  3 化合物（quercetin / luteolin / kaempferol）× 4 蛋白（PCNA / DNMT1 / ESR2 / FOS）= 12 对。
  已有 2 对复用旧批次（Vina，seed 1/7/42）原样引用，不重跑不覆盖：
      quercetin×FOS  (任务 01, mean −8.2)
      luteolin×PCNA  (无任务号, mean −4.6)
  新跑 10 对 = AutoDock-GPU（AD4，--nrun 20，3 种子 1/7/42 取均值±SD）。

定心按决策树（文档_docs/技术路线_AutoSite_AutoDockGPU.md §2）：
  有共晶小分子 → cocrystal_meeko（enveloping + padding 5）
  无共晶      → AutoSite（本机未装）→ P2Rank → annotated_site（结构注释界面残基）
每对强制登记 center_source（中心位点方法登记_CenterSourceRegistry.md）。

产出：
  序号文件夹/13..22            每对一个任务目录（config/受体/配体/output/log/task_info）
  结果文件/数据文件/对接/多对多3x4_对接全表.csv      列名沿用 成分对接全表.csv + 登记扩展列
  结果文件/数据文件/对接/多对多3x4_对接汇总.csv      列名沿用 成分对接汇总.csv + 登记扩展列
  结果文件/数据文件/对接/summary_adgpu_多对多3x4.csv 仅新跑 AD-GPU 行（AD-GPU/Vina 分表）
  结果文件/数据文件/对接/矩阵_结合能_多对多3x4.csv   行=化合物 列=蛋白，均值 kcal/mol

引擎 cwd 一律 ASCII（E:\\RProject\\_dock_m2m）；任务目录落在课题工作区。
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------- 路径
PROJ = Path(r"E:\RProject\努力学习项目\06_分子对接")
SEQ_DIR = PROJ / "序号文件夹"
OUT_DOCK = PROJ / "结果文件" / "数据文件" / "对接"
STRUCT_WS = PROJ / "数据文件" / "原始数据" / "RCSB与PubChem_对接结构工作区"
ASCII_ROOT = Path(r"E:\RProject\_dock_m2m")
MAPS_ROOT = ASCII_ROOT / "maps"
REC_DIR = ASCII_ROOT / "receptors"
LIG_DIR = ASCII_ROOT / "ligands"
RUN_ROOT = ASCII_ROOT / "runs"
P2RANK_ROOT = Path(r"E:\p2rank\p2rank_2.5.1")

LIB_SMALL = Path(r"D:\数据库\分子对接数据库\test\small_clean_h")
OB = Path(r"E:\OpenBabel-3.1.1\obabel.exe")
MGL_PY = Path(r"E:\mgltools\python.exe")
PREP_REC = Path(r"E:\mgltools\Lib\site-packages\AutoDockTools\Utilities24\prepare_receptor4.py")
ADGPU = Path(r"E:\AutoDock-GPU\AutoDock-GPU.exe")
WSL_DISTRO = "Ubuntu-24.04"

# ---------------------------------------------------------------- 约定
SEEDS = [1, 7, 42]
NRUN = 20
DEVNUM = 1
THRESH_KCAL = -5.0
PADDING = 5.0
BOX_FLOOR = 20.0

NUCLEIC_RES = {
    "DA", "DC", "DG", "DT", "DI", "A", "C", "G", "T", "U", "I",
    "RA", "RC", "RG", "RU", "ADE", "CYT", "GUA", "THY", "URA",
}

# 化合物（网络图 Degree 前三）
LIGANDS = {
    "quercetin": {"cid": "5280343", "uniprot_by_gene": None},
    "luteolin": {"cid": "5280445", "uniprot_by_gene": None},
    "kaempferol": {"cid": "5280863", "uniprot_by_gene": None},
}

# 蛋白（PPI Degree 前四）；受体复用现有对接工作区（_dock_cmp 的 .rec.pdb 即现批次受体来源）
RECEPTORS = {
    "PCNA": {
        "pdb": "1U7B",
        "uniprot": "P12004",
        "rec_src": Path(r"E:\RProject\_dock_cmp\STD_PCNA__luteolin.rec.pdb"),
        # FEN1(331-350) 肽为非目标结合伙伴，按 SOP §3 清洗剔除后再对接
        "strip_chains": {"B"},
        "partner_chains": {"B"},          # 界面注释来源（保留坐标用于定心，不进受体）
        "interface_chains": {"A"},
        "box_mode": "p2rank_or_annotated",
        "partner_note": "FEN1(331-350) PIP-box peptide chain B",
    },
    "DNMT1": {
        "pdb": "3EPZ",
        "uniprot": "P26358",
        "rec_src": Path(r"E:\RProject\_dock_cmp\STD_DNMT1__3betaHydroxyurs12En2.rec.pdb"),
        "strip_chains": set(),
        "box_mode": "cocrystal",
        "ref_ligand": ("BGC", "A", "702"),
    },
    "ESR2": {
        "pdb": "1L2J",
        "uniprot": "Q92731",
        "rec_src": Path(r"E:\RProject\_dock_cmp\STD_ESR2__Anhydroicaritin.rec.pdb"),
        "strip_chains": set(),
        "box_mode": "cocrystal",
        "ref_ligand": ("ETC", "A", "600"),
    },
    "FOS": {
        "pdb": "1A02",
        "uniprot": "P01100",
        "rec_src": Path(r"E:\RProject\_dock_cmp\STD_FOS__quercetin.rec.pdb"),
        "strip_chains": set(),
        "partner_chains": {"A", "B"},     # 共晶 DNA（受体已剔除，坐标用于界面注释）
        "interface_chains": {"F"},        # FOS 链
        "box_mode": "p2rank_or_annotated",
        "partner_note": "DNA chains A/B (stripped per FROZEN)",
    },
}

# 新跑 10 对：任务号续接 13–22
NEW_PAIRS = [
    (13, "quercetin", "PCNA"),
    (14, "quercetin", "DNMT1"),
    (15, "quercetin", "ESR2"),
    (16, "luteolin", "DNMT1"),
    (17, "luteolin", "ESR2"),
    (18, "luteolin", "FOS"),
    (19, "kaempferol", "PCNA"),
    (20, "kaempferol", "DNMT1"),
    (21, "kaempferol", "ESR2"),
    (22, "kaempferol", "FOS"),
]

# 复用 2 对：原样引用 成分对接全表/汇总（Vina，旧批次）
REUSED_PAIRS = [
    ("quercetin", "FOS", 1),
    ("luteolin", "PCNA", None),
]

MATRIX_COMPOUNDS = ["quercetin", "luteolin", "kaempferol"]
MATRIX_GENES = ["PCNA", "DNMT1", "ESR2", "FOS"]


# ---------------------------------------------------------------- 基础工具
def wsl(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["wsl", "-d", WSL_DISTRO, "--", *args]
    r = subprocess.run(cmd, capture_output=True)
    out = (r.stdout or b"").decode("utf-8", errors="replace")
    err = (r.stderr or b"").decode("utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"wsl failed {args}: {err[-500:]} {out[-500:]}")
    return subprocess.CompletedProcess(r.args, r.returncode, out, err)


def win_to_wsl(p: Path) -> str:
    s = str(p.resolve()).replace("\\", "/")
    return f"/mnt/{s[0].lower()}{s[2:]}" if s[1] == ":" else s


def read_pdb_atom_lines(pdb: Path) -> list[str]:
    return [
        ln for ln in pdb.read_text(errors="ignore").splitlines()
        if ln.startswith(("ATOM", "HETATM"))
    ]


def atom_xyz(ln: str) -> tuple[float, float, float]:
    return (float(ln[30:38]), float(ln[38:46]), float(ln[46:54]))


def res_key(ln: str) -> tuple[str, str, str]:
    return (ln[21].strip(), ln[22:26].strip(), ln[17:20].strip())


def centroid(coords) -> tuple[float, float, float]:
    return (
        sum(c[0] for c in coords) / len(coords),
        sum(c[1] for c in coords) / len(coords),
        sum(c[2] for c in coords) / len(coords),
    )


def heavy_lines(lines: list[str]) -> list[str]:
    return [ln for ln in lines if ln[12:16].strip().startswith("H") is False]


# ---------------------------------------------------------------- 受体准备
def prepare_receptor(gene: str) -> Path:
    """复用现有对接工作区 .rec.pdb（protein-only，核酸/非目标配体已剔），
    重新以 gasteiger 电荷生成 AD4 受体 pdbqt；PCNA 另剔 FEN1 肽链 B（非目标伙伴）。"""
    cfg = RECEPTORS[gene]
    pdb = cfg["pdb"]
    REC_DIR.mkdir(parents=True, exist_ok=True)
    dest = REC_DIR / f"{pdb}_clean_h.pdbqt"
    if dest.is_file() and dest.stat().st_size > 5000:
        return dest

    src_lines = read_pdb_atom_lines(cfg["rec_src"])
    strip = cfg.get("strip_chains", set())
    kept = []
    for ln in src_lines:
        if ln[:6].strip() == "ATOM" and ln[17:20].strip() in NUCLEIC_RES:
            continue
        if ln[21].strip() in strip:
            continue
        kept.append(ln)
    clean_pdb = REC_DIR / f"{pdb}_clean.pdb"
    clean_pdb.write_text("\n".join(kept) + "\n", encoding="utf-8")

    # AD4 受体准备：ADT prepare_receptor4（Gasteiger 电荷 + AD4 原子类型，受体刚性）
    raw_out = REC_DIR / f"{pdb}_adt.pdbqt"
    r = subprocess.run(
        [str(MGL_PY), str(PREP_REC), "-r", str(clean_pdb), "-o", str(raw_out), "-U", "nphs_lps"],
        capture_output=True, text=True,
    )
    if not raw_out.is_file() or raw_out.stat().st_size < 5000:
        # 回退：obabel -xr + gasteiger（部分结构 ADT 解析失败时）
        raw_out2 = REC_DIR / f"{pdb}_oba.pdbqt"
        r2 = subprocess.run(
            [str(OB), str(clean_pdb), "-O", str(raw_out2), "-xr", "--partialcharge", "gasteiger"],
            capture_output=True, text=True,
        )
        if not raw_out2.is_file() or raw_out2.stat().st_size < 5000:
            raise RuntimeError(
                f"receptor prep failed {gene}: ADT={(r.stderr or '')[-200:]} OB={(r2.stderr or '')[-200:]}"
            )
        raw_out = raw_out2
    atoms = [ln for ln in raw_out.read_text(errors="ignore").splitlines()
             if ln.startswith(("ATOM", "HETATM"))]
    dest.write_text("\n".join(atoms) + "\n", encoding="utf-8")
    return dest


def prepare_ligand(compound: str) -> Path:
    """配体从结构库复用（PubChem 3D → 加氢 → PDBQT(gasteiger)，CID 命名）。"""
    cid = LIGANDS[compound]["cid"]
    src = LIB_SMALL / f"{cid}_clean_h.pdbqt"
    if not src.is_file():
        raise FileNotFoundError(f"ligand missing in library: {src}")
    LIG_DIR.mkdir(parents=True, exist_ok=True)
    dest = LIG_DIR / f"{cid}_clean_h.pdbqt"
    if not dest.is_file():
        shutil.copy2(src, dest)
    return dest


def ligand_metrics(pdbqt: Path) -> tuple[float, float]:
    """(Lmax, Rg) over heavy atoms."""
    coords = []
    for ln in pdbqt.read_text(errors="ignore").splitlines():
        if not ln.startswith(("ATOM", "HETATM")):
            continue
        if ln[12:16].strip().startswith("H"):
            continue
        try:
            coords.append(atom_xyz(ln))
        except ValueError:
            continue
    xs, ys, zs = zip(*coords)
    lmax = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    cx, cy, cz = centroid(coords)
    rg = math.sqrt(sum((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2 for x, y, z in coords) / len(coords))
    return lmax, rg


# ---------------------------------------------------------------- 定心定盒
def parse_ref_ligand(raw_pdb: Path, resname: str, chain: str, resi: str):
    coords = []
    for ln in read_pdb_atom_lines(raw_pdb):
        if ln[:6].strip() != "HETATM":
            continue
        if ln[17:20].strip() != resname or ln[21].strip() != chain:
            continue
        if ln[22:26].strip() != resi:
            continue
        if ln[12:16].strip().startswith("H"):
            continue
        coords.append(atom_xyz(ln))
    if len(coords) < 3:
        raise RuntimeError(f"ref ligand {resname}:{chain}:{resi} not in {raw_pdb.name}")
    return coords


def interface_residues(raw_pdb: Path, iface_chains: set, partner_chains: set, cutoff: float = 4.0):
    """结构注释界面：iface_chains 中距 partner_chains 任一原子 ≤ cutoff 的残基。"""
    lines = read_pdb_atom_lines(raw_pdb)
    partner = [atom_xyz(ln) for ln in lines
               if ln[21].strip() in partner_chains and not ln[12:16].strip().startswith("H")]
    if not partner:
        raise RuntimeError(f"partner chains {partner_chains} empty in {raw_pdb.name}")
    hits: dict[tuple[str, str], list] = {}
    for ln in lines:
        if ln[:6].strip() != "ATOM" or ln[21].strip() not in iface_chains:
            continue
        if ln[12:16].strip().startswith("H"):
            continue
        x, y, z = atom_xyz(ln)
        dmin = min((x - px) ** 2 + (y - py) ** 2 + (z - pz) ** 2 for px, py, pz in partner)
        if dmin <= cutoff * cutoff:
            key = (ln[21].strip(), ln[22:26].strip())
            hits.setdefault(key, []).append((x, y, z))
    if not hits:
        raise RuntimeError("no interface residues found")
    allc = [c for cs in hits.values() for c in cs]
    keys = sorted(hits.keys(), key=lambda k: int(k[1]) if k[1].lstrip("-").isdigit() else 0)
    res_str = ",".join(f"{c}:{r}" for c, r in keys)
    return keys, centroid(allc), res_str


def qc_box(center, size, rec_pdbqt: Path) -> tuple[str, str]:
    sx, sy, sz = size
    fails = []
    if sx > 35 or sy > 35 or sz > 35 or sx * sy * sz > 40000:
        fails.append("Q3")
    cx, cy, cz = center
    best = 1e9
    for ln in rec_pdbqt.read_text(errors="ignore").splitlines():
        if not ln.startswith("ATOM") or ln[12:16].strip() != "CA":
            continue
        try:
            x, y, z = atom_xyz(ln)
        except ValueError:
            continue
        best = min(best, math.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2))
    if best > 8.0:
        fails.append("Q2")
    return ("FAIL", ",".join(fails)) if fails else ("PASS", "")


def dist_to_residues(center, keys, raw_pdb: Path) -> float:
    want = set(keys)
    best = 1e9
    for ln in read_pdb_atom_lines(raw_pdb):
        if ln[:6].strip() != "ATOM":
            continue
        k = (ln[21].strip(), ln[22:26].strip())
        if k not in want:
            continue
        x, y, z = atom_xyz(ln)
        d = math.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2 + (z - center[2]) ** 2)
        best = min(best, d)
    return best


def run_p2rank(rec_pdb: Path, out_dir: Path) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    prankbat = P2RANK_ROOT / "prank.bat"
    prank = P2RANK_ROOT / "prank"
    if prankbat.is_file():
        cmd = [str(prankbat), "predict", "-f", str(rec_pdb), "-o", str(out_dir)]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(P2RANK_ROOT))
    elif prank.is_file():
        cmd = ["wsl", "-d", WSL_DISTRO, "--", "bash", win_to_wsl(prank),
               "predict", "-f", win_to_wsl(rec_pdb), "-o", win_to_wsl(out_dir)]
        r = subprocess.run(cmd, capture_output=True, text=True)
    else:
        raise FileNotFoundError("p2rank/prank launcher not found")
    csvs = sorted(out_dir.glob("*_predictions.csv")) or sorted(out_dir.glob("*_pockets.csv"))
    if not csvs:
        raise RuntimeError(f"p2rank produced no pockets csv: {(r.stderr or r.stdout or '')[-300:]}")
    rows = []
    with csvs[0].open(encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh, skipinitialspace=True):
            row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
            try:
                rows.append({
                    "rank": int(float(row.get("rank", ""))),
                    "prob": float(row.get("probability", row.get("score", "nan"))),
                    "center": (float(row["center_x"]), float(row["center_y"]), float(row["center_z"])),
                    "residues": (row.get("residue_ids") or "").strip(),
                    "file": csvs[0].name,
                })
            except (KeyError, ValueError):
                continue
    return sorted(rows, key=lambda r: r["rank"])


def resolve_box(gene: str, rec_pdbqt: Path, lmax: float, rg: float) -> dict:
    cfg = RECEPTORS[gene]
    pdb = cfg["pdb"]
    raw = STRUCT_WS / f"{pdb}.pdb"
    size_floor = max(lmax + 2 * PADDING, BOX_FLOOR)

    if cfg["box_mode"] == "cocrystal":
        resname, chain, resi = cfg["ref_ligand"]
        coords = parse_ref_ligand(raw, resname, chain, resi)
        center = centroid(coords)
        xs, ys, zs = zip(*coords)
        size = (
            max(max(xs) - min(xs) + 2 * PADDING, size_floor),
            max(max(ys) - min(ys) + 2 * PADDING, size_floor),
            max(max(zs) - min(zs) + 2 * PADDING, size_floor),
        )
        qc, codes = qc_box(center, size, rec_pdbqt)
        return {
            "center": center, "size": size,
            "center_source": "cocrystal_meeko",
            "center_detail": f"{resname}:{chain}:{resi}",
            "size_method": "meeko_enveloping",
            "box_qc": qc, "fail_codes": codes, "fallback_used": "",
            "ref_ligand": f"{resname}:{chain}:{resi}", "site_residues": "",
        }

    # 无共晶小分子：AutoSite（本机未装）→ P2Rank → annotated_site
    fail_codes = ["Q1(autosite_unavailable)"]
    iface_keys, iface_center, iface_str = interface_residues(
        raw, cfg["interface_chains"], cfg["partner_chains"]
    )

    pockets = []
    clean_pdb = REC_DIR / f"{pdb}_clean.pdb"
    try:
        pockets = run_p2rank(clean_pdb, ASCII_ROOT / "boxes" / gene / "p2rank")
    except Exception as e:  # noqa: BLE001
        fail_codes.append(f"Q1(p2rank_failed:{e})")

    # 立方盒边长（技术路线 §2 回退规则）
    cubic = max(lmax + 10.0, 4.0 * rg, BOX_FLOOR)

    def as_box(center, size):
        qc, codes = qc_box(center, size, rec_pdbqt)
        return center, size, qc, codes

    for pk in pockets[:3]:
        if pk["rank"] > 3:
            break
        center = pk["center"]
        size = (cubic, cubic, cubic)
        d = dist_to_residues(center, iface_keys, raw)
        if d > 12.0:
            fail_codes.append(f"Q5(p2rank_rank{pk['rank']}_d{d:.1f}A)")
            continue
        center, size, qc, codes = as_box(center, size)
        if qc == "FAIL":
            fail_codes.append(f"{codes}(p2rank_rank{pk['rank']})")
            continue
        return {
            "center": center, "size": size,
            "center_source": "p2rank",
            "center_detail": f"p2rank_rank={pk['rank']};file={pk['file']};prob={pk['prob']:.3f};d_iface={d:.1f}A",
            "size_method": "rg_4_5x",
            "box_qc": qc, "fail_codes": ",".join(fail_codes),
            "fallback_used": "p2rank",
            "ref_ligand": "", "site_residues": iface_str,
        }

    # annotated_site：结构注释界面残基中心（1U7B FEN1 PIP 沟 / 1A02 FOS–DNA 界面）
    center, size, qc, codes = as_box(iface_center, (cubic, cubic, cubic))
    cite = f"{pdb} {cfg['partner_note']} interface"
    return {
        "center": center, "size": size,
        "center_source": "annotated_site",
        "center_detail": f"site_citation={cite}",
        "size_method": "rg_4_5x",
        "box_qc": qc, "fail_codes": ",".join(fail_codes + ([codes] if codes else [])),
        "fallback_used": "annotated_site",
        "ref_ligand": "", "site_residues": iface_str,
    }


# ---------------------------------------------------------------- AutoGrid
def pdbqt_atom_types(pdbqt: Path) -> list[str]:
    types = set()
    for ln in pdbqt.read_text(errors="ignore").splitlines():
        if ln.startswith(("ATOM", "HETATM")):
            types.add(ln.split()[-1])
    return sorted(types)


def write_gpf(gpf: Path, receptor_pdbqt: Path, center, size, spacing=0.375) -> None:
    def odd(n: int) -> int:
        return n + 1 if n % 2 == 0 else n

    nx = odd(max(41, int(round(size[0] / spacing))))
    ny = odd(max(41, int(round(size[1] / spacing))))
    nz = odd(max(41, int(round(size[2] / spacing))))
    rec_types = pdbqt_atom_types(receptor_pdbqt)
    lig_types = sorted(set(rec_types) | {"A", "C", "HD", "N", "NA", "OA", "SA", "F", "Cl", "Br", "I", "P", "S"})
    stem = receptor_pdbqt.stem
    lines = [
        f"npts {nx} {ny} {nz}",
        f"gridfld {stem}.maps.fld",
        f"spacing {spacing:.3f}",
        f"receptor_types {' '.join(rec_types)}",
        f"ligand_types {' '.join(lig_types)}",
        f"receptor {receptor_pdbqt.name}",
        f"gridcenter {center[0]:.3f} {center[1]:.3f} {center[2]:.3f}",
        "smooth 0.5",
    ]
    for t in lig_types:
        lines.append(f"map {stem}.{t}.map")
    lines += [f"elecmap {stem}.e.map", f"dsolvmap {stem}.d.map", "dielectric -0.1465", ""]
    gpf.write_text("\n".join(lines), encoding="utf-8")


def ensure_maps(gene: str, rec_pdbqt: Path, center, size) -> Path:
    maps_dir = MAPS_ROOT / gene
    maps_dir.mkdir(parents=True, exist_ok=True)
    rec_local = maps_dir / rec_pdbqt.name
    if not rec_local.is_file():
        shutil.copy2(rec_pdbqt, rec_local)
    stem = rec_local.stem
    fld = maps_dir / f"{stem}.maps.fld"
    if fld.is_file() and fld.stat().st_size > 100:
        return fld
    gpf = maps_dir / f"{stem}.gpf"
    write_gpf(gpf, rec_local, center, size)
    wsl(["bash", "-c", f"cd {win_to_wsl(maps_dir)} && autogrid4 -p {gpf.name} -l {stem}.glg"])
    if not fld.is_file() or fld.stat().st_size < 100:
        raise RuntimeError(f"AutoGrid failed: {fld}")
    return fld


# ---------------------------------------------------------------- AutoDock-GPU
def parse_adgpu_energies(path: Path) -> list[float]:
    text = path.read_text(encoding="utf-8", errors="replace")
    vals = [float(m) for m in re.findall(r'free_NRG_binding="\s*([-+]?\d+\.?\d*)"', text)]
    if not vals:
        vals = [float(m) for m in re.findall(
            r"<free_NRG_binding>\s*([-+]?\d+\.?\d*)\s*</free_NRG_binding>", text)]
    if not vals:
        vals = [float(m) for m in re.findall(
            r"Estimated Free Energy of Binding\s*=\s*([-+]?\d+\.?\d*)", text)]
    return vals


def run_adgpu_seed(run_dir: Path, ligand: Path, fld: Path, seed: int) -> float:
    run_dir.mkdir(parents=True, exist_ok=True)
    lig_local = run_dir / "ligand.pdbqt"
    if not lig_local.is_file():
        shutil.copy2(ligand, lig_local)
    resnam = f"seed{seed}"
    xml = run_dir / f"{resnam}.xml"
    if xml.is_file():
        vals = parse_adgpu_energies(xml)
        if vals:
            return min(vals)
    cmd = [
        str(ADGPU),
        "--lfile", "ligand.pdbqt",
        "--ffile", str(fld),
        "--nrun", str(NRUN),
        "--seed", str(seed),
        "--resnam", resnam,
        "--devnum", str(DEVNUM),
        "--gbest", "1",
    ]
    r = subprocess.run(cmd, cwd=str(run_dir), capture_output=True, text=True)
    (run_dir / f"{resnam}.stdout.txt").write_text((r.stdout or "") + "\n" + (r.stderr or ""), encoding="utf-8")
    for cand in (xml, run_dir / f"{resnam}.dlg"):
        if cand.is_file():
            vals = parse_adgpu_energies(cand)
            if vals:
                return min(vals)
    raise RuntimeError(f"no energy for seed {seed}: {(r.stdout or '')[-200:]}")


# ---------------------------------------------------------------- 组装
def fmt(x: float) -> str:
    return f"{x:.3f}"


def write_task_dir(task: int, compound: str, gene: str, box: dict, rec_pdbqt: Path,
                   lig_pdbqt: Path, run_dir: Path, energies: dict, source_rec_note: str) -> Path:
    cfg = RECEPTORS[gene]
    pdb = cfg["pdb"]
    tdir = SEQ_DIR / f"{task:02d}"
    tdir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(rec_pdbqt, tdir / f"{pdb}_clean_h.pdbqt")
    shutil.copy2(lig_pdbqt, tdir / f"{cid_name(compound)}")

    best_seed = min(energies, key=lambda s: energies[s])
    best_pose = run_dir / f"seed{best_seed}_best.pdbqt"
    if not best_pose.is_file():
        best_pose = run_dir / f"seed{best_seed}_best_ligand.pdbqt"
    if not best_pose.is_file():
        cands = sorted(run_dir.glob(f"seed{best_seed}*best*.pdbqt"))
        best_pose = cands[0] if cands else None
    if best_pose and best_pose.is_file():
        shutil.copy2(best_pose, tdir / "output.pdbqt")

    # config.txt：AD-GPU + 地图参数
    cx, cy, cz = box["center"]
    sx, sy, sz = box["size"]
    (tdir / "config.txt").write_text("\n".join([
        f"engine = autodock-gpu (AD4)",
        f"receptor = {pdb}_clean_h.pdbqt",
        f"ligand = {cid_name(compound)}",
        f"maps = maps/{gene}/{pdb}_clean_h.maps.fld",
        f"center_x = {cx:.3f}",
        f"center_y = {cy:.3f}",
        f"center_z = {cz:.3f}",
        f"size_x = {sx:.1f}",
        f"size_y = {sy:.1f}",
        f"size_z = {sz:.1f}",
        f"nrun = {NRUN}",
        f"seeds = {','.join(str(s) for s in SEEDS)}",
        f"devnum = {DEVNUM}",
        "",
    ]), encoding="utf-8")

    lines = [f"task={task}", f"protein={gene}", f"pdb={pdb}", f"ligand={compound}",
             f"cid={cid_name(compound).split('_')[0]}",
             f"center_source={box['center_source']}", f"center_detail={box['center_detail']}",
             f"center_x={cx:.3f}", f"center_y={cy:.3f}", f"center_z={cz:.3f}",
             f"size_x={sx:.1f}", f"size_y={sy:.1f}", f"size_z={sz:.1f}",
             f"size_method={box['size_method']}", f"box_qc={box['box_qc']}",
             f"fail_codes={box['fail_codes']}", f"fallback_used={box['fallback_used']}",
             f"ref_ligand={box['ref_ligand']}", f"site_residues={box['site_residues']}",
             f"engine=adgpu", f"nrun={NRUN}",
             "seeds=" + ",".join(str(s) for s in SEEDS),
             "seed_affinities=" + ";".join(f"s{s}:{energies[s]:.3f}" for s in SEEDS),
             f"mean_kcal={statistics.mean(energies.values()):.3f}",
             f"sd_kcal={statistics.stdev(energies.values()):.3f}",
             "receptor_includes_nucleic=no",
             f"receptor_prep={source_rec_note}",
             f"run_dir={run_dir}",
             ""]
    (tdir / "task_info.txt").write_text("\n".join(lines), encoding="utf-8")

    log = [f"task {task} {gene} x {compound} (AutoDock-GPU nrun={NRUN})"]
    for s in SEEDS:
        log.append(f"seed={s} best_free_NRG_binding={energies[s]:.3f} kcal/mol")
        sf = run_dir / f"seed{s}.stdout.txt"
        if sf.is_file():
            log.append(sf.read_text(encoding="utf-8", errors="replace")[-2000:])
    (tdir / "log.txt").write_text("\n".join(log), encoding="utf-8")
    return tdir


def cid_name(compound: str) -> str:
    return f"{LIGANDS[compound]['cid']}_clean_h.pdbqt"


def load_reused_rows():
    """从 成分对接全表/汇总 原样读取 2 对复用结果。"""
    full_rows, sum_rows = [], []
    full_csv = OUT_DOCK / "成分对接全表.csv"
    sum_csv = OUT_DOCK / "成分对接汇总.csv"
    with full_csv.open(encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            for comp, gene, task in REUSED_PAIRS:
                if r["compound"] == comp and r["gene"] == gene:
                    rr = dict(r)
                    rr["task"] = "" if task is None else f"{task:02d}"
                    full_rows.append(rr)
    with sum_csv.open(encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            for comp, gene, task in REUSED_PAIRS:
                if r["compound"] == comp and r["gene"] == gene:
                    rr = dict(r)
                    rr["task"] = "" if task is None else f"{task:02d}"
                    sum_rows.append(rr)
    return full_rows, sum_rows


def load_state() -> dict:
    import json
    p = ASCII_ROOT / "state_rows.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    import json
    p = ASCII_ROOT / "state_rows.json"
    p.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def assemble(new_full: list[dict], new_sum: list[dict]) -> None:
    OUT_DOCK.mkdir(parents=True, exist_ok=True)
    reused_full, reused_sum = load_reused_rows()

    # ---- 全表：列名沿用 成分对接全表.csv + 登记扩展列
    base_cols = ["compound", "gene", "uniprot", "pdb", "site", "seed",
                 "affinity_kcal_mol", "affinity_kJ_mol", "pass_threshold_kcal"]
    ext_cols = ["center_source", "center_detail", "size_method", "box_qc",
                "fallback_used", "engine", "source", "task"]
    rows_full = []
    for r in reused_full:
        rr = {c: r.get(c, "") for c in base_cols}
        rr.update({
            "center_source": "legacy_blind_geometric_center",
            "center_detail": "原批次 site=blind(geometric center)（废止法定心；仅作历史引用）",
            "size_method": "fixed22_legacy", "box_qc": "", "fallback_used": "",
            "engine": "vina_legacy", "source": "复用_旧批次", "task": r.get("task", ""),
        })
        rows_full.append(rr)
    rows_full.extend(new_full)

    with (OUT_DOCK / "多对多3x4_对接全表.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=base_cols + ext_cols)
        w.writeheader()
        for r in rows_full:
            w.writerow({k: r.get(k, "") for k in base_cols + ext_cols})

    # ---- 汇总：列名沿用 成分对接汇总.csv + 登记扩展列
    sum_base = ["compound", "gene", "pdb", "site", "mean_kcal", "sd_kcal",
                "min_kcal", "pass_rate", "n_runs"]
    sum_ext = ["center_source", "center_detail", "size_method", "box_qc",
               "fallback_used", "engine", "source", "task", "task_dir"]
    rows_sum = []
    for r in reused_sum:
        rr = {c: r.get(c, "") for c in sum_base}
        rr.update({
            "center_source": "legacy_blind_geometric_center",
            "center_detail": "原批次 site=blind(geometric center)（废止法定心；仅作历史引用）",
            "size_method": "fixed22_legacy", "box_qc": "", "fallback_used": "",
            "engine": "vina_legacy", "source": "复用_旧批次", "task": r.get("task", ""),
        })
        rows_sum.append(rr)
    rows_sum.extend(new_sum)
    with (OUT_DOCK / "多对多3x4_对接汇总.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=sum_base + sum_ext)
        w.writeheader()
        for r in rows_sum:
            w.writerow({k: r.get(k, "") for k in sum_base + sum_ext})

    # ---- summary_adgpu（仅新跑 AD-GPU 行，SOP §5 schema）
    sop_cols = ["task", "protein", "pdb", "ligand", "ligand_name", "cid",
                "affinity_kcal_mol", "center_source", "center_detail",
                "size_method", "box_qc", "fallback_used", "engine"]
    sop_rows = []
    for r in new_sum:
        sop_rows.append({
            "task": r["task"], "protein": r["gene"], "pdb": r["pdb"],
            "ligand": r["compound"], "ligand_name": r["compound"],
            "cid": LIGANDS[r["compound"]]["cid"],
            "affinity_kcal_mol": r["mean_kcal"],
            "center_source": r["center_source"], "center_detail": r["center_detail"],
            "size_method": r["size_method"], "box_qc": r["box_qc"],
            "fallback_used": r["fallback_used"], "engine": "adgpu",
        })
    with (OUT_DOCK / "summary_adgpu_多对多3x4.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=sop_cols)
        w.writeheader()
        for r in sop_rows:
            w.writerow(r)

    # ---- 3×4 矩阵（行=化合物，列=蛋白；均值 kcal/mol）
    grid = {(r["compound"], r["gene"]): r["mean_kcal"] for r in rows_sum}
    with (OUT_DOCK / "矩阵_结合能_多对多3x4.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["compound"] + MATRIX_GENES)
        for comp in MATRIX_COMPOUNDS:
            w.writerow([comp] + [grid.get((comp, g), "") for g in MATRIX_GENES])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["prep", "dock", "assemble", "all"], default="all")
    ap.add_argument("--genes", default="", help="仅跑指定基因（逗号分隔）；默认全部")
    args = ap.parse_args()

    if not ADGPU.is_file():
        raise SystemExit(f"missing {ADGPU}")
    for root in (ASCII_ROOT, MAPS_ROOT, REC_DIR, LIG_DIR, RUN_ROOT):
        root.mkdir(parents=True, exist_ok=True)

    only = {g.strip() for g in args.genes.split(",") if g.strip()}
    state = load_state()

    boxes: dict[str, dict] = {}
    new_full: list[dict] = []
    new_sum: list[dict] = []

    # -------- 受体/配体/盒子准备
    lmax_by = {}
    for compound in LIGANDS:
        lig = prepare_ligand(compound)
        lmax_by[compound] = ligand_metrics(lig)

    for gene, cfg in RECEPTORS.items():
        rec = prepare_receptor(gene)
        lmax = max(m[0] for m in lmax_by.values())
        rg = max(m[1] for m in lmax_by.values())
        boxes[gene] = resolve_box(gene, rec, lmax, rg)
        b = boxes[gene]
        print(f"[box] {gene} {cfg['pdb']} source={b['center_source']} qc={b['box_qc']} "
              f"center=({b['center'][0]:.2f},{b['center'][1]:.2f},{b['center'][2]:.2f}) "
              f"size=({b['size'][0]:.1f},{b['size'][1]:.1f},{b['size'][2]:.1f})")

    if args.phase == "prep":
        return

    # -------- 对接（10 对 × 3 种子）
    rec_note = {}
    for gene, cfg in RECEPTORS.items():
        note = "protein-only (nucleic stripped); AD4 gasteiger"
        if cfg.get("strip_chains"):
            note += f"; stripped non-target chains {sorted(cfg['strip_chains'])} ({cfg.get('partner_note','')})"
        rec_note[gene] = note

    for task, compound, gene in NEW_PAIRS:
        if only and gene not in only:
            continue
        if str(task) in state:
            print(f"[skip] task {task} already in state")
            continue
        cfg = RECEPTORS[gene]
        pdb = cfg["pdb"]
        b = boxes[gene]
        rec = REC_DIR / f"{pdb}_clean_h.pdbqt"
        lig = LIG_DIR / cid_name(compound)
        run_dir = RUN_ROOT / f"{task:02d}_{compound}_{gene}"
        energies = {}
        if b["center_source"] == "FAIL":
            print(f"[blocked] {task} {compound} x {gene}: centering FAIL")
        else:
            fld = ensure_maps(gene, rec, b["center"], b["size"])
            for s in SEEDS:
                try:
                    energies[s] = run_adgpu_seed(run_dir, lig, fld, s)
                    print(f"[adgpu] task {task} {compound} x {gene} seed={s} E={energies[s]:.3f}")
                except Exception as e:  # noqa: BLE001
                    print(f"[err] task {task} seed {s}: {e}")

        if len(energies) != len(SEEDS):
            print(f"[stop] task {task} {compound} x {gene} incomplete; stop batch here per plan")
            break

        tdir = write_task_dir(task, compound, gene, b, rec, lig, run_dir, energies, rec_note[gene])
        vals = list(energies.values())
        mean = statistics.mean(vals)
        sd = statistics.stdev(vals)
        rows_common = {
            "compound": compound, "gene": gene, "uniprot": cfg["uniprot"], "pdb": pdb,
            "center_source": b["center_source"], "center_detail": b["center_detail"],
            "size_method": b["size_method"], "box_qc": b["box_qc"],
            "fallback_used": b["fallback_used"], "engine": "adgpu",
            "source": "新跑_adgpu", "task": f"{task:02d}",
        }
        full_rows = []
        for s in SEEDS:
            kcal = energies[s]
            full_rows.append({
                "compound": compound, "gene": gene, "uniprot": cfg["uniprot"], "pdb": pdb,
                "site": b["center_detail"], "seed": s,
                "affinity_kcal_mol": f"{kcal:.3f}",
                "affinity_kJ_mol": f"{kcal * 4.184:.2f}",
                "pass_threshold_kcal": str(kcal <= THRESH_KCAL),
                **{k: v for k, v in rows_common.items() if k not in {"compound", "gene", "uniprot", "pdb"}},
            })
        sum_row = {
            "compound": compound, "gene": gene, "pdb": pdb, "site": b["center_detail"],
            "mean_kcal": mean, "sd_kcal": sd, "min_kcal": min(vals),
            "pass_rate": sum(v <= THRESH_KCAL for v in vals) / len(vals),
            "n_runs": len(vals), **rows_common,
            "task_dir": str(tdir),
        }
        state[str(task)] = {"full": full_rows, "sum": sum_row}
        save_state(state)

    # 从 state 组装（跨多次运行合并）
    all_full, all_sum = [], []
    for k in sorted(state.keys(), key=int):
        all_full.extend(state[k]["full"])
        all_sum.append(state[k]["sum"])

    if args.phase == "dock":
        if all_sum:
            assemble(all_full, all_sum)
        return

    assemble(all_full, all_sum)
    print("[done] new pairs:", len(all_sum))


if __name__ == "__main__":
    main()
