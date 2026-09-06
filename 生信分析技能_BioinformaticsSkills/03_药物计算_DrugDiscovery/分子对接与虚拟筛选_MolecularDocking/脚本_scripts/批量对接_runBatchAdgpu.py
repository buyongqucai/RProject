# -*- coding: utf-8 -*-
"""批量对接：共晶/AutoSite 定盒 → AutoGrid → AutoDock-GPU（nrun=20）。

桌面：努力学习/docking_adgpu/（ASCII）；detail 导出前断点。
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from dock_summary_schema import CANONICAL_COLUMNS  # noqa: E402

ADGPU = Path(r"E:\AutoDock-GPU\AutoDock-GPU.exe")
PYMOL_PY = Path(r"E:\pymol\python.exe")
VIZ_SCRIPT = SCRIPT_DIR / "pymol_dock_viz_standard.py"
HEATMAP_SCRIPT = SCRIPT_DIR / "plot_docking_affinity_heatmap.py"
WSL_HELPER = Path(r"E:\ADFRsuite\adfr_wsl_helpers.sh")
WSL_DISTRO = "Ubuntu-24.04"

GENES = [
    "TP53", "AKT1", "ESR1", "JUN", "TNF", "PRKACA",
    "MAPK3", "EGFR", "MAPK1", "PIK3CA", "FGA",
]
LIGANDS = [
    ("quercetin", "5280343"),
    ("3-Dehydrocholic Acid", "5283956"),
    ("kaempferol", "5280863"),
    ("Higenamine", "114840"),
    ("isorhamnetin", "5281654"),
    ("beta-sitosterol", "222284"),
    ("Liensinine", "160644"),
    ("Neferine", "159654"),
]


def win_to_wsl(p: Path) -> str:
    s = str(p.resolve())
    s = s.replace("\\", "/")
    if len(s) >= 2 and s[1] == ":":
        return f"/mnt/{s[0].lower()}{s[2:]}"
    return s


def wsl_run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["wsl", "-d", WSL_DISTRO, "--", "bash", win_to_wsl(WSL_HELPER), *args]
    r = subprocess.run(cmd, capture_output=True)
    stdout = (r.stdout or b"").decode("utf-8", errors="replace")
    stderr = (r.stderr or b"").decode("utf-8", errors="replace")
    # rebuild as text-like result
    r = subprocess.CompletedProcess(r.args, r.returncode, stdout, stderr)
    if check and r.returncode != 0:
        raise RuntimeError(
            f"WSL helper failed ({args[0]}): {(r.stderr or r.stdout)[-800:]}"
        )
    return r


def find_lib_root(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.is_dir():
            raise SystemExit(f"lib-root not found: {p}")
        return p
    for parent in Path("D:/").iterdir():
        if parent.is_dir() and "数据" in parent.name:
            for child in parent.iterdir():
                if child.is_dir() and "对接数据库" in child.name:
                    return child
    raise SystemExit("未找到 D:/数据库/分子对接数据库")


def protein_table_path(lib: Path) -> Path:
    """Prefer exact 分子对接_蛋白表.csv; never use .bak / 扩展."""
    exact = lib / "分子对接_蛋白表.csv"
    if exact.is_file():
        return exact
    hits = [
        p
        for p in lib.glob("*.csv")
        if "蛋白表" in p.name
        and "扩展" not in p.name
        and ".bak" not in p.name.lower()
        and "before_recenter" not in p.name.lower()
    ]
    if not hits:
        raise SystemExit("库内无 分子对接_蛋白表.csv")
    return hits[0]


def read_csv_auto(path: Path) -> list[dict]:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        text = data.decode("utf-8-sig")
    else:
        for enc in ("utf-8", "gbk", "gb18030"):
            try:
                text = data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = data.decode("utf-8", errors="replace")
    return list(csv.DictReader(text.splitlines()))


# Project genes missing from library table still required for this study
PROJECT_EXTRA = {
    "MAPK3": {
        "entry": "P27361",
        "pdb": "4qtb",
        "ref_ligand": "38Z:A:418",
        "center_method": "cocrystal_single_ligand_COM",
        "center_note": "project override; from prior recenter",
        "cx": float("nan"),
        "cy": float("nan"),
        "cz": float("nan"),
    },
    "FGA": {
        "entry": "P02671",
        "pdb": "p02671_af",
        "ref_ligand": "",
        "center_method": "FAIL_alphafold_no_site",
        "center_note": "AF model: AutoSite required",
        "cx": float("nan"),
        "cy": float("nan"),
        "cz": float("nan"),
    },
}

def lib_dirs(lib: Path) -> dict[str, Path]:
    test = lib / "test"
    root = test if test.is_dir() else lib
    return {
        "big": root / "big",
        "big_clean": root / "big_clean",
        "big_clean_h": root / "big_clean_h",
        "small_clean_h": root / "small_clean_h",
    }


def load_protein_plan(lib: Path) -> dict[str, dict]:
    rows = read_csv_auto(protein_table_path(lib))
    by: dict[str, dict] = {}
    for r in rows:
        keys = list(r.keys())
        gene = (r.get(keys[1]) or "").strip().upper()
        if not gene:
            continue
        try:
            cx = float(r.get(keys[3]) or "nan")
            cy = float(r.get(keys[4]) or "nan")
            cz = float(r.get(keys[5]) or "nan")
        except ValueError:
            cx = cy = cz = float("nan")
        by[gene] = {
            "entry": (r.get(keys[0]) or "").strip(),
            "gene": gene,
            "pdb": (r.get(keys[2]) or "").strip().lower(),
            "cx": cx,
            "cy": cy,
            "cz": cz,
            "ref_ligand": (r.get("ref_ligand") or "").strip(),
            "center_method": (r.get("center_method") or r.get("center_source") or "").strip(),
            "center_note": (r.get("center_note") or "").strip(),
        }
    for gene, extra in PROJECT_EXTRA.items():
        if gene not in by:
            by[gene] = {"gene": gene, **extra}
    return by


def find_raw_pdb(lib: Path, pdb: str) -> Path:
    dirs = lib_dirs(lib)
    for base in (dirs["big"], lib / "big"):
        for name in (f"{pdb}.pdb", f"{pdb.upper()}.pdb", f"{pdb}_af.pdb"):
            p = base / name
            if p.is_file() and p.stat().st_size > 500:
                return p
    raise FileNotFoundError(f"raw pdb missing: {pdb}")


def find_ligand(lib: Path, cid: str) -> Path:
    p = lib_dirs(lib)["small_clean_h"] / f"{cid}_clean_h.pdbqt"
    if not p.is_file():
        raise FileNotFoundError(f"ligand missing: {cid}")
    return p


def ligand_extent(pdbqt: Path) -> float:
    xs, ys, zs = [], [], []
    for ln in pdbqt.read_text(encoding="utf-8", errors="replace").splitlines():
        if not (ln.startswith("ATOM") or ln.startswith("HETATM")):
            continue
        try:
            xs.append(float(ln[30:38]))
            ys.append(float(ln[38:46]))
            zs.append(float(ln[46:54]))
        except ValueError:
            continue
    if not xs:
        return 15.0
    return max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def parse_ref_ligand(spec: str) -> tuple[str, str, str | None]:
    parts = (spec or "").split(":")
    if len(parts) < 2:
        raise ValueError(spec)
    return parts[0], parts[1], (parts[2] if len(parts) >= 3 else None)


def ligand_coords(pdb: Path, ref: str) -> list[tuple[float, float, float]]:
    resname, chain, resi = parse_ref_ligand(ref)
    coords = []
    for ln in pdb.read_text(encoding="utf-8", errors="replace").splitlines():
        if not ln.startswith("HETATM"):
            continue
        if ln[17:20].strip() != resname or ln[21].strip() != chain:
            continue
        if resi is not None and ln[22:26].strip() != resi:
            continue
        name = ln[12:16].strip()
        if name.startswith("H"):
            continue
        try:
            coords.append((float(ln[30:38]), float(ln[38:46]), float(ln[46:54])))
        except ValueError:
            continue
    if len(coords) < 3:
        raise RuntimeError(f"ref ligand {ref} not in {pdb}")
    return coords


def box_from_coords(coords, padding=5.0, lmax=0.0):
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    zs = [c[2] for c in coords]
    center = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)
    floor = max(lmax + 2 * padding, 20.0)
    size = (
        max((max(xs) - min(xs)) + 2 * padding, floor),
        max((max(ys) - min(ys)) + 2 * padding, floor),
        max((max(zs) - min(zs)) + 2 * padding, floor),
    )
    return center, size


def parse_autosite_cluster(clu: Path):
    xs, ys, zs = [], [], []
    for ln in clu.read_text(encoding="utf-8", errors="replace").splitlines():
        if not (ln.startswith("ATOM") or ln.startswith("HETATM")):
            continue
        try:
            xs.append(float(ln[30:38]))
            ys.append(float(ln[38:46]))
            zs.append(float(ln[46:54]))
        except ValueError:
            continue
    if len(xs) < 5:
        return None
    center = (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))
    size = (
        max(max(xs) - min(xs) + 10.0, 20.0),
        max(max(ys) - min(ys) + 10.0, 20.0),
        max(max(zs) - min(zs) + 10.0, 20.0),
    )
    return center, size


def qc_box(center, size, receptor_pdbqt: Path) -> tuple[str, str]:
    sx, sy, sz = size
    fails = []
    if sx > 35 or sy > 35 or sz > 35 or sx * sy * sz > 40000:
        fails.append("Q3")
    cx, cy, cz = center
    best = 1e9
    for ln in receptor_pdbqt.read_text(encoding="utf-8", errors="replace").splitlines():
        if not ln.startswith("ATOM") or ln[12:16].strip() != "CA":
            continue
        try:
            x, y, z = float(ln[30:38]), float(ln[38:46]), float(ln[46:54])
        except ValueError:
            continue
        best = min(best, math.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2))
    if best > 8.0:
        fails.append("Q2")
    return ("FAIL", ",".join(fails)) if fails else ("PASS", "")


def pdbqt_atom_types(pdbqt: Path) -> list[str]:
    types = set()
    for ln in pdbqt.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.startswith("ATOM") or ln.startswith("HETATM"):
            types.add(ln.split()[-1])
    return sorted(types)


def prepare_ad4_receptor(raw_pdb: Path, out_pdbqt: Path) -> Path:
    if out_pdbqt.is_file() and out_pdbqt.stat().st_size > 1000:
        return out_pdbqt
    out_pdbqt.parent.mkdir(parents=True, exist_ok=True)
    wsl_run(["prepare_receptor", win_to_wsl(raw_pdb), win_to_wsl(out_pdbqt)])
    if not out_pdbqt.is_file():
        raise RuntimeError(f"prepare_receptor failed: {out_pdbqt}")
    return out_pdbqt


def resolve_box(lib, gene, plan, ad4_rec, lmax, boxes_root) -> dict:
    pdb = plan["pdb"]
    method = plan.get("center_method", "")
    ref = plan.get("ref_ligand", "")

    # 1) cocrystal
    if ref and not method.startswith("FAIL"):
        raw = find_raw_pdb(lib, pdb.replace("_af", ""))
        coords = ligand_coords(raw, ref)
        center, size = box_from_coords(coords, padding=5.0, lmax=lmax)
        qc, codes = qc_box(center, size, ad4_rec)
        return {
            "center": center,
            "size": size,
            "center_source": "cocrystal_meeko",
            "center_detail": ref,
            "size_method": "meeko_enveloping",
            "box_qc": qc,
            "fail_codes": codes,
            "fallback_used": "",
            "pdb": pdb,
            "blocked": False,
        }

    # 2) AutoSite
    as_dir = boxes_root / gene / "autosite"
    as_dir.mkdir(parents=True, exist_ok=True)
    rec_copy = as_dir / ad4_rec.name
    if not rec_copy.is_file():
        shutil.copy2(ad4_rec, rec_copy)
    wsl_run(["autosite", win_to_wsl(rec_copy), win_to_wsl(as_dir)], check=False)
    clusters = sorted(as_dir.glob("*_cl_001.pdb")) or sorted(as_dir.glob("*_cl_*.pdb"))
    if not clusters:
        # AutoSite sometimes nests under receptor stem folder
        clusters = sorted(as_dir.rglob("*_cl_001.pdb"))
    if not clusters:
        return {
            "center": (float("nan"),) * 3,
            "size": (0, 0, 0),
            "center_source": "FAIL",
            "center_detail": "AutoSite produced no cluster",
            "size_method": "",
            "box_qc": "FAIL",
            "fail_codes": "Q1",
            "fallback_used": "",
            "pdb": pdb,
            "blocked": True,
        }
    parsed = parse_autosite_cluster(clusters[0])
    if not parsed:
        return {
            "center": (float("nan"),) * 3,
            "size": (0, 0, 0),
            "center_source": "FAIL",
            "center_detail": f"empty cluster {clusters[0].name}",
            "size_method": "",
            "box_qc": "FAIL",
            "fail_codes": "Q1",
            "fallback_used": "",
            "pdb": pdb,
            "blocked": True,
        }
    center, size = parsed
    size = tuple(max(s, lmax + 10.0, 20.0) for s in size)
    qc, codes = qc_box(center, size, ad4_rec)
    return {
        "center": center,
        "size": size,
        "center_source": "autosite",
        "center_detail": f"autosite_rank=1;file={clusters[0].name}",
        "size_method": "autosite_box",
        "box_qc": qc,
        "fail_codes": codes,
        "fallback_used": "",
        "pdb": pdb,
        "blocked": False,
    }


def write_gpf(gpf: Path, receptor_pdbqt: Path, center, size, spacing=0.375) -> None:
    nx = max(41, int(round(size[0] / spacing)) | 1)
    ny = max(41, int(round(size[1] / spacing)) | 1)
    nz = max(41, int(round(size[2] / spacing)) | 1)
    if nx % 2 == 0:
        nx += 1
    if ny % 2 == 0:
        ny += 1
    if nz % 2 == 0:
        nz += 1
    rec_types = pdbqt_atom_types(receptor_pdbqt)
    lig_types = sorted(
        set(rec_types)
        | {"A", "C", "HD", "N", "NA", "OA", "SA", "F", "Cl", "Br", "I", "P", "S"}
    )
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


def ensure_maps(maps_dir: Path, ad4_rec: Path, center, size) -> Path:
    maps_dir.mkdir(parents=True, exist_ok=True)
    rec_local = maps_dir / ad4_rec.name
    if not rec_local.is_file():
        shutil.copy2(ad4_rec, rec_local)
    stem = rec_local.stem
    fld = maps_dir / f"{stem}.maps.fld"
    if fld.is_file() and fld.stat().st_size > 100:
        return fld
    gpf = maps_dir / f"{stem}.gpf"
    write_gpf(gpf, rec_local, center, size)
    wsl_run(["autogrid", win_to_wsl(maps_dir), gpf.name])
    if not fld.is_file() or fld.stat().st_size < 100:
        raise RuntimeError(f"AutoGrid failed: {fld}")
    return fld


def parse_adgpu_energy(path: Path) -> float | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'free_NRG_binding="\s*([-+]?\d+\.?\d*)"', text)
    if m:
        return float(m.group(1))
    m = re.search(r"<free_NRG_binding>\s*([-+]?\d+\.?\d*)\s*</free_NRG_binding>", text)
    if m:
        return float(m.group(1))
    m = re.search(r"Estimated Free Energy of Binding\s*=\s*([-+]?\d+\.?\d*)", text)
    if m:
        return float(m.group(1))
    return None


def run_adgpu(task_dir: Path, ligand: Path, fld: Path, nrun: int, devnum: int) -> float | None:
    lig_local = task_dir / "ligand.pdbqt"
    shutil.copy2(ligand, lig_local)
    xml = task_dir / "best.xml"
    dlg = task_dir / "best.dlg"
    out_pose = task_dir / "best_ligand.pdbqt"
    if xml.is_file():
        e = parse_adgpu_energy(xml)
        if e is not None:
            if out_pose.is_file():
                shutil.copy2(out_pose, task_dir / "output.pdbqt")
            return e
    cmd = [
        str(ADGPU),
        "--lfile",
        "ligand.pdbqt",
        "--ffile",
        str(fld),
        "--nrun",
        str(nrun),
        "--resnam",
        "best",
        "--devnum",
        str(devnum),
        "--gbest",
        "1",
    ]
    r = subprocess.run(cmd, cwd=str(task_dir), capture_output=True)
    stdout = (r.stdout or b"").decode("utf-8", errors="replace")
    stderr = (r.stderr or b"").decode("utf-8", errors="replace")
    (task_dir / "adgpu_log.txt").write_text(stdout + "\n" + stderr, encoding="utf-8")
    # --gbest may write best_ligand.pdbqt or ligand_best.pdbqt
    for cand in sorted(task_dir.glob("*.pdbqt")):
        if cand.name in {"ligand.pdbqt"}:
            continue
        if "best" in cand.name.lower():
            shutil.copy2(cand, task_dir / "output.pdbqt")
            break
    if not (task_dir / "output.pdbqt").is_file():
        for cand in fld.parent.glob("*best*.pdbqt"):
            shutil.copy2(cand, task_dir / "output.pdbqt")
            break
    for p in (xml, dlg):
        if p.is_file():
            e = parse_adgpu_energy(p)
            if e is not None:
                return e
    # parse from log (inter+intra line is not free energy of binding; prefer xml)
    m = re.search(
        r"<free_NRG_binding>\s*([-+]?\d+\.?\d*)\s*</free_NRG_binding>",
        stdout,
    )
    if m:
        return float(m.group(1))
    return None


def write_task_info(path: Path, info: dict) -> None:
    path.write_text("\n".join(f"{k}={v}" for k, v in info.items()) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib-root", default=None)
    ap.add_argument("--desktop-parent", default=r"C:\Users\10540\Desktop\努力学习")
    ap.add_argument("--project-ascii", default="docking_adgpu")
    ap.add_argument("--run-dock", action="store_true")
    ap.add_argument("--make-pymol", action="store_true")
    ap.add_argument("--nrun", type=int, default=20)
    ap.add_argument("--devnum", type=int, default=1)
    args = ap.parse_args()

    if not WSL_HELPER.is_file():
        raise SystemExit(f"missing {WSL_HELPER}")
    if not ADGPU.is_file():
        raise SystemExit(f"missing {ADGPU}")

    lib = find_lib_root(args.lib_root)
    root = Path(args.desktop_parent) / args.project_ascii
    root.mkdir(parents=True, exist_ok=True)
    maps_root = root / "maps"
    boxes_root = root / "boxes"
    rec_root = root / "receptors_ad4"
    maps_root.mkdir(exist_ok=True)
    boxes_root.mkdir(exist_ok=True)
    rec_root.mkdir(exist_ok=True)

    plans = load_protein_plan(lib)
    for p in lib.glob("*.csv"):
        if "蛋白表" in p.name and "扩展" not in p.name:
            shutil.copy2(p, root / "分子对接_蛋白表.csv")
            break
    with (root / "分子对接_化合物表.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["活性成分名称", "活性成分重命名", "活性成分3D结构名称"])
        for i, (name, cid) in enumerate(LIGANDS, 1):
            w.writerow([name, i, cid])

    print(f"[info] project={root}")
    box_cache: dict[str, dict] = {}
    ad4_cache: dict[str, Path] = {}
    summary_rows: list[dict] = []
    task = 0

    for gene in GENES:
        if gene not in plans:
            print(f"[skip] {gene} not in protein table")
            continue
        plan = plans[gene]
        pdb = plan["pdb"]
        raw_key = "p02671_af" if gene == "FGA" else pdb
        try:
            raw = find_raw_pdb(lib, raw_key)
        except FileNotFoundError as e:
            print(f"[err] {e}")
            continue
        ad4 = rec_root / f"{gene}_{raw_key}_ad4.pdbqt"
        try:
            if gene not in ad4_cache:
                print(f"[prep] AD4 receptor {gene} ...")
                ad4_cache[gene] = prepare_ad4_receptor(raw, ad4)
        except Exception as e:
            print(f"[err] prepare {gene}: {e}")
            continue
        ad4_rec = ad4_cache[gene]

        for lig_name, cid in LIGANDS:
            task += 1
            tdir = root / str(task)
            tdir.mkdir(exist_ok=True)
            try:
                lig = find_ligand(lib, cid)
            except FileNotFoundError as e:
                print(f"[err] {e}")
                continue
            lmax = ligand_extent(lig)
            if gene not in box_cache:
                print(f"[box] resolve {gene} ...")
                box_cache[gene] = resolve_box(lib, gene, plan, ad4_rec, lmax, boxes_root)
            box = dict(box_cache[gene])
            if not box.get("blocked"):
                sx, sy, sz = box["size"]
                need = lmax + 10.0
                box["size"] = (max(sx, need), max(sy, need), max(sz, need))

            # receptors for docking logs + PyMOL naming contract
            shutil.copy2(ad4_rec, tdir / ad4_rec.name)
            pdb_tag = (box.get("pdb") or pdb).lower()
            if gene == "FGA" or "af" in pdb_tag:
                stem = "p02671_af" if gene == "FGA" else (
                    pdb_tag if pdb_tag.endswith("_af") else f"{pdb_tag}_af"
                )
                pymol_rec = tdir / f"{stem}_clean_h.pdbqt"
            else:
                pymol_rec = tdir / f"{pdb_tag}_clean_h.pdbqt"
            shutil.copy2(ad4_rec, pymol_rec)

            info = {
                "task": task,
                "protein": gene,
                "pdb": box.get("pdb", pdb),
                "ligand": lig_name.replace(" ", "_"),
                "cid": cid,
                "center_source": box["center_source"],
                "center_detail": box["center_detail"],
                "size_method": box["size_method"],
                "box_qc": box["box_qc"],
                "fail_codes": box.get("fail_codes", ""),
                "fallback_used": box.get("fallback_used", ""),
                "engine": "adgpu",
                "nrun": args.nrun,
            }
            if not box.get("blocked"):
                info.update(
                    {
                        "center_x": f"{box['center'][0]:.3f}",
                        "center_y": f"{box['center'][1]:.3f}",
                        "center_z": f"{box['center'][2]:.3f}",
                        "size_x": f"{box['size'][0]:.1f}",
                        "size_y": f"{box['size'][1]:.1f}",
                        "size_z": f"{box['size'][2]:.1f}",
                    }
                )
            write_task_info(tdir / "task_info.txt", info)

            aff = ""
            if box.get("blocked") or box["center_source"] == "FAIL":
                print(f"[blocked] {task} {gene} x {lig_name}")
            elif args.run_dock:
                try:
                    mdir = maps_root / f"{gene}_{box['center_source']}"
                    fld = ensure_maps(mdir, ad4_rec, box["center"], box["size"])
                    energy = run_adgpu(tdir, lig, fld, args.nrun, args.devnum)
                    aff = "" if energy is None else f"{energy:.3f}"
                    print(
                        f"[ok] {task} {gene} {lig_name} {box['center_source']} E={aff}"
                    )
                except Exception as e:
                    print(f"[err] {task} {gene} {lig_name}: {e}")

            row = {
                "task": str(task),
                "protein": gene,
                "pdb": box.get("pdb", pdb),
                "ligand": lig_name.replace(" ", "_"),
                "ligand_name": lig_name,
                "cid": cid,
                "affinity_kcal_mol": float(aff) if aff else "",
                "center_source": box["center_source"],
                "center_detail": box["center_detail"],
                "size_method": box["size_method"],
                "box_qc": box["box_qc"],
                "fallback_used": box.get("fallback_used", ""),
                "engine": "adgpu",
            }
            summary_rows.append(row)

    sum_path = root / "summary_adgpu.csv"
    with sum_path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CANONICAL_COLUMNS)
        w.writeheader()
        for r in summary_rows:
            w.writerow({k: r.get(k, "") for k in CANONICAL_COLUMNS})

    numeric = [r for r in summary_rows if isinstance(r.get("affinity_kcal_mol"), float)]
    if numeric and HEATMAP_SCRIPT.is_file():
        subprocess.run(
            [sys.executable, str(HEATMAP_SCRIPT), "--root", str(root)], check=False
        )

    bp = root / "BREAKPOINT_等待手调detail标签.txt"
    bp.write_text(
        "已生成对接结果与（若开启）PyMOL big/surface/detail.pse（含首轮 detail PNG）。\n"
        "请手调各任务 detail-*.pse 标签后，再运行 export_detail_png_from_pse.py 与 result 拼图。\n"
        "手调后的 detail 禁止再用 cmd.png；须走截图导出。\n",
        encoding="utf-8",
    )

    if args.make_pymol and PYMOL_PY.is_file() and VIZ_SCRIPT.is_file():
        subprocess.run(
            [str(PYMOL_PY), str(VIZ_SCRIPT), "--jobs-root", str(root), "--all"],
            check=False,
        )
        print("[breakpoint] stop before detail export —", bp)

    print(f"[done] tasks={task} summary={sum_path}")


if __name__ == "__main__":
    main()
