# -*- coding: utf-8 -*-
"""[DEPRECATED] 旧 Vina 批处理。默认主路径请用 批量对接_runBatchAdgpu.py（AutoDock-GPU）。

保留仅作可选对照；勿用本脚本的默认 --size 22 作为正式交付。
若必须跑 Vina 对照：须自行按盒子协议定边，并写 summary_vina.csv（勿覆盖 summary_adgpu.csv）。

detail 出图后默认在「手调标签」前停止（--stop-before-detail-export）。

用法示例（对照）：
  python 批量对接_runBatchDocking.py --desktop-name PDAC_docking --run-vina --make-pymol
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from dock_summary_schema import CANONICAL_COLUMNS  # noqa: E402

OBA = Path(r"E:\OpenBabel-3.1.1\obabel.exe")
VINA = Path(r"E:\vina\vina.exe")
UA = {"User-Agent": "batch-docking; local"}


def write_summary_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CANONICAL_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CANONICAL_COLUMNS})


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


def safe_slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", name.strip()).strip("_")
    return re.sub(r"_+", "_", s)


def read_csv_auto(path: Path) -> list[dict]:
    raw = path.read_bytes()[:4]
    enc = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "gbk"
    try:
        text = path.read_text(encoding=enc)
    except UnicodeDecodeError:
        text = path.read_text(encoding="gb18030")
    return list(csv.DictReader(text.splitlines()))


def protein_table_path(lib: Path) -> Path:
    hits = [p for p in lib.glob("*.csv") if "蛋白表" in p.name and "扩展" not in p.name]
    if not hits:
        raise SystemExit("库内无 分子对接_蛋白表.csv")
    return hits[0]


def compound_cid_map(lib: Path) -> dict[str, str]:
    """name.lower() -> CID"""
    out: dict[str, str] = {}
    for p in lib.glob("*.csv"):
        if "化合物表" in p.name and "扩展" not in p.name:
            for r in read_csv_auto(p):
                keys = list(r.keys())
                name = r.get(keys[0], "")
                cid = r.get(keys[2], "") if len(keys) >= 3 else ""
                if name and cid and str(cid).isdigit():
                    out[name.strip().lower()] = str(cid)
        if "CID" in p.name:
            for r in read_csv_auto(p):
                name = r.get(list(r.keys())[0], "")
                cid = r.get("CID") or r.get("cid") or ""
                if name and str(cid).isdigit():
                    out[name.strip().lower()] = str(cid)
    return out


def protein_rows_by_gene(lib: Path) -> dict[str, dict]:
    rows = read_csv_auto(protein_table_path(lib))
    keys = list(rows[0].keys())
    gene_k, pdb_k = keys[1], keys[2]
    cx, cy, cz = keys[3], keys[4], keys[5]
    entry_k = keys[0]
    by: dict[str, dict] = {}
    for r in rows:
        g = (r.get(gene_k) or "").strip().upper()
        if not g or g in by:
            continue
        by[g] = {
            "gene": g,
            "entry": (r.get(entry_k) or "").strip(),
            "pdb": (r.get(pdb_k) or "").strip().lower(),
            "cx": float(r[cx]),
            "cy": float(r[cy]),
            "cz": float(r[cz]),
        }
    return by


def lib_dirs(lib: Path) -> dict[str, Path]:
    test = lib / "test"
    root = test if test.is_dir() else lib
    return {
        "root": root,
        "big": root / "big",
        "big_clean": root / "big_clean",
        "big_clean_h": root / "big_clean_h",
        "small": root / "small",
        "small_clean": root / "small_clean",
        "small_clean_h": root / "small_clean_h",
    }


def ensure_ligand_pdbqt(lib: Path, cid: str, session: requests.Session) -> Path:
    dirs = lib_dirs(lib)
    for d in dirs.values():
        if isinstance(d, Path):
            d.mkdir(parents=True, exist_ok=True)
    dest = dirs["small_clean_h"] / f"{cid}_clean_h.pdbqt"
    if dest.is_file() and dest.stat().st_size > 200:
        return dest
    sdf = dirs["small"] / f"{cid}.sdf"
    if not sdf.is_file() or sdf.stat().st_size < 200:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d"
        r = session.get(url, timeout=60)
        r.raise_for_status()
        if b"V2000" not in r.content and b"V3000" not in r.content:
            raise RuntimeError(f"PubChem 3D SDF bad for CID {cid}")
        sdf.write_bytes(r.content)
    clean = dirs["small_clean"] / f"{cid}_clean.sdf"
    shutil.copy2(sdf, clean)
    mol2 = dirs["small_clean_h"] / f"{cid}_clean_h.mol2"
    if not OBA.is_file():
        raise SystemExit(f"Open Babel not found: {OBA}")
    # SDF -h → MOL2 → PDBQT；禁止 --gen3d
    subprocess.run(
        [str(OBA), str(clean), "-h", "-O", str(mol2)],
        check=True, capture_output=True, text=True,
    )
    subprocess.run(
        [str(OBA), str(mol2), "-O", str(dest), "--partialcharge", "gasteiger"],
        check=True, capture_output=True, text=True,
    )
    if not dest.is_file() or dest.stat().st_size < 100:
        raise RuntimeError(f"failed ligand pdbqt {cid}")
    return dest


def hetatm_centroid(pdb_path: Path) -> tuple[float, float, float] | None:
    xs, ys, zs = [], [], []
    for ln in pdb_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not ln.startswith("HETATM"):
            continue
        res = ln[17:20].strip()
        if res in {"HOH", "WAT", "DOD", "NA", "CL", "MG", "ZN", "CA", "K", "SO4", "PO4", "GOL", "EDO", "PEG"}:
            continue
        try:
            xs.append(float(ln[30:38]))
            ys.append(float(ln[38:46]))
            zs.append(float(ln[46:54]))
        except ValueError:
            continue
    if len(xs) < 5:
        return None
    return sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)


def atom_centroid(pdb_path: Path) -> tuple[float, float, float]:
    xs, ys, zs = [], [], []
    for ln in pdb_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not ln.startswith("ATOM"):
            continue
        try:
            xs.append(float(ln[30:38]))
            ys.append(float(ln[38:46]))
            zs.append(float(ln[46:54]))
        except ValueError:
            continue
    if not xs:
        raise RuntimeError(f"no ATOM in {pdb_path}")
    return sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)


def rigidify_receptor_pdbqt(src: Path, dest: Path | None = None) -> Path:
    """Strip ROOT/BRANCH/TORSDOF/REMARK — Vina receptors must be rigid ATOM-only."""
    dest = dest or src
    atoms = []
    for ln in src.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.startswith("ATOM") or ln.startswith("HETATM"):
            atoms.append(ln)
    if len(atoms) < 50:
        raise RuntimeError(f"too few ATOM lines in receptor {src}: {len(atoms)}")
    dest.write_text("\n".join(atoms) + "\n", encoding="utf-8")
    return dest


def _obabel_receptor_to_ascii_tmp(clean_pdb: Path) -> Path:
    """obabel often fails writing under non-ASCII paths; use %TEMP% then return rigid pdbqt."""
    import tempfile

    tmpdir = Path(tempfile.gettempdir()) / "vina_receptor_prep"
    tmpdir.mkdir(parents=True, exist_ok=True)
    stem = clean_pdb.stem.replace("_clean", "")
    out = tmpdir / f"{stem}_rigid.pdbqt"
    raw_out = tmpdir / f"{stem}_oba.pdbqt"
    for flag in (["-xr"], []):
        cmd = [str(OBA), str(clean_pdb), "-h", *flag, "-O", str(raw_out), "--partialcharge", "gasteiger"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and raw_out.is_file() and raw_out.stat().st_size > 500:
            rigidify_receptor_pdbqt(raw_out, out)
            raw_out.unlink(missing_ok=True)
            return out
    raise RuntimeError(f"obabel receptor prep failed for {clean_pdb}: {(r.stderr or '')[:400]}")


def ensure_receptor_pdbqt(
    lib: Path, pdb: str, session: requests.Session
) -> tuple[Path, tuple[float, float, float] | None]:
    dirs = lib_dirs(lib)
    for d in ("big", "big_clean", "big_clean_h"):
        dirs[d].mkdir(parents=True, exist_ok=True)
    pdb = pdb.lower()
    dest = dirs["big_clean_h"] / f"{pdb}_clean_h.pdbqt"
    raw = dirs["big"] / f"{pdb}.pdb"
    if not raw.is_file() or raw.stat().st_size < 500:
        url = f"https://files.rcsb.org/download/{pdb.upper()}.pdb"
        r = session.get(url, timeout=90)
        if r.status_code != 200 or len(r.content) < 500:
            raise RuntimeError(f"RCSB download failed {pdb}: {r.status_code}")
        raw.write_bytes(r.content)
    center = hetatm_centroid(raw)
    clean = dirs["big_clean"] / f"{pdb}_clean.pdb"
    if not clean.is_file() or clean.stat().st_size < 500:
        lines = []
        for ln in raw.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.startswith("ATOM"):
                lines.append(ln)
            elif ln.startswith("TER") or ln.startswith("END"):
                lines.append(ln)
        clean.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if dest.is_file() and dest.stat().st_size > 500:
        text = dest.read_text(encoding="utf-8", errors="replace")
        if "ROOT" in text or "BRANCH" in text or "TORSDOF" in text:
            # prefer strip ATOM from existing (fast; works even if path is non-ASCII)
            rigidify_receptor_pdbqt(dest)
        # else already rigid
    else:
        if not OBA.is_file():
            raise SystemExit(f"Open Babel not found: {OBA}")
        rigid = _obabel_receptor_to_ascii_tmp(clean)
        dest.write_bytes(rigid.read_bytes())

    if center is None:
        center = atom_centroid(clean)
    return dest, center


def ensure_alphafold_receptor(
    lib: Path, uniprot: str, session: requests.Session
) -> tuple[Path, tuple[float, float, float]]:
    dirs = lib_dirs(lib)
    for d in ("big", "big_clean", "big_clean_h"):
        dirs[d].mkdir(parents=True, exist_ok=True)
    tag = uniprot.lower()
    dest = dirs["big_clean_h"] / f"{tag}_af_clean_h.pdbqt"
    raw = dirs["big"] / f"{tag}_af.pdb"
    if not raw.is_file() or raw.stat().st_size < 500:
        ok = False
        for ver in ("v6", "v4"):
            url = f"https://alphafold.ebi.ac.uk/files/AF-{uniprot.upper()}-F1-model_{ver}.pdb"
            r = session.get(url, timeout=90)
            if r.status_code == 200 and len(r.content) > 500:
                raw.write_bytes(r.content)
                ok = True
                break
        if not ok:
            raise RuntimeError(f"AlphaFold download failed {uniprot}")
    clean = dirs["big_clean"] / f"{tag}_af_clean.pdb"
    if not clean.is_file():
        lines = [
            ln
            for ln in raw.read_text(encoding="utf-8", errors="replace").splitlines()
            if ln.startswith("ATOM") or ln.startswith("TER") or ln.startswith("END")
        ]
        clean.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if dest.is_file() and dest.stat().st_size > 500:
        text = dest.read_text(encoding="utf-8", errors="replace")
        if "ROOT" in text or "BRANCH" in text or "TORSDOF" in text:
            rigidify_receptor_pdbqt(dest)
    else:
        rigid = _obabel_receptor_to_ascii_tmp(clean)
        dest.write_bytes(rigid.read_bytes())
    return dest, atom_centroid(clean)


def write_config(
    path: Path,
    receptor: Path,
    ligand: Path,
    center: tuple[float, float, float],
    size: float = 22.0,
    exhaustiveness: int = 8,
    num_modes: int = 9,
) -> None:
    cx, cy, cz = center
    text = "\n".join(
        [
            f"receptor = {receptor.name}",
            f"ligand = {ligand.name}",
            f"center_x = {cx:.3f}",
            f"center_y = {cy:.3f}",
            f"center_z = {cz:.3f}",
            f"size_x = {size:.1f}",
            f"size_y = {size:.1f}",
            f"size_z = {size:.1f}",
            f"exhaustiveness = {exhaustiveness}",
            f"num_modes = {num_modes}",
            "energy_range = 3",
            "out = output.pdbqt",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def parse_best_affinity(log_path: Path) -> float | None:
    if not log_path.is_file():
        return None
    text = log_path.read_text(encoding="utf-8", errors="replace")
    # vina table: mode | affinity | ...
    for ln in text.splitlines():
        m = re.match(r"^\s*1\s+(-?\d+\.\d+)", ln)
        if m:
            return float(m.group(1))
    return None


def run_vina(task_dir: Path) -> float | None:
    """Run AutoDock Vina in task_dir.

    Windows Vina builds often fail on non-ASCII cwd/paths — project root must be ASCII.
    Pass relative --config/--log so argv stays ASCII when cwd is ASCII.
    """
    if not VINA.is_file():
        raise SystemExit(f"Vina not found: {VINA}")
    logf = task_dir / "log.txt"
    out = task_dir / "output.pdbqt"
    if out.is_file() and logf.is_file():
        aff = parse_best_affinity(logf)
        if aff is not None:
            return aff
    # relative names: avoids Unicode absolute paths in argv
    cmd = [str(VINA), "--config", "config.txt", "--log", "log.txt"]
    subprocess.run(cmd, cwd=str(task_dir), check=True, capture_output=True, text=True)
    return parse_best_affinity(logf)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib-root", default=None)
    # Windows AutoDock Vina 对非 ASCII 路径极易失败；桌面工程名必须用英文
    ap.add_argument("--desktop-name", default="PDAC_compounds_docking")
    ap.add_argument("--project-root", default=None, help="覆盖桌面路径（须 ASCII）")
    ap.add_argument("--run-vina", action="store_true")
    ap.add_argument("--make-pymol", action="store_true")
    ap.add_argument("--stop-before-detail-export", action="store_true", default=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--exhaustiveness", type=int, default=8)
    ap.add_argument("--size", type=float, default=22.0)
    args = ap.parse_args()

    lib = find_lib_root(args.lib_root)
    desk = Path.home() / "Desktop"
    root = Path(args.project_root) if args.project_root else desk / args.desktop_name
    root.mkdir(parents=True, exist_ok=True)
    (root / ".gitignore").write_text("_png_tmp/\nThumbs.db\n.DS_Store\n", encoding="utf-8")

    # --- ligands ---
    name_to_cid_override = {
        "quercetin": "5280343",
        "3-Dehydrocholic Acid": "5283956",
        "kaempferol": "5280863",
        "Higenamine": "114840",
        "isorhamnetin": "5281654",
        "beta-sitosterol": "222284",
        "Liensinine": "160644",
        "Neferine": "159654",
    }
    cmap = compound_cid_map(lib)
    ligands = []
    for name, cid0 in name_to_cid_override.items():
        cid = cmap.get(name.lower()) or cid0
        ligands.append({"name": name, "cid": str(cid), "slug": safe_slug(name)})

    # --- proteins ---
    by_gene = protein_rows_by_gene(lib)
    # Prefer first hit PDB from table; extras for missing genes
    extra = {
        "MAPK3": {"gene": "MAPK3", "entry": "P27361", "pdb": "4qtb", "cx": None, "cy": None, "cz": None},
        "FGA": {"gene": "FGA", "entry": "P02671", "pdb": "AF-P02671", "cx": None, "cy": None, "cz": None},
    }
    genes = [
        "TP53", "AKT1", "ESR1", "JUN", "TNF", "PRKACA", "MAPK3", "EGFR", "MAPK1", "PIK3CA", "FGA",
    ]
    proteins = []
    for g in genes:
        if g in by_gene:
            proteins.append(by_gene[g])
        elif g in extra:
            proteins.append(extra[g])
        else:
            raise SystemExit(f"missing protein mapping: {g}")

    session = requests.Session()
    session.headers.update(UA)

    # prepare ligand files
    lig_paths = {}
    for lig in ligands:
        print(f"[ligand] {lig['name']} CID={lig['cid']}")
        lig_paths[lig["cid"]] = ensure_ligand_pdbqt(lib, lig["cid"], session)

    # prepare receptors
    rec_paths = {}
    centers = {}
    for p in proteins:
        g = p["gene"]
        if g == "FGA":
            print(f"[receptor] FGA AlphaFold {p['entry']}")
            path, cen = ensure_alphafold_receptor(lib, p["entry"], session)
            # AF whole-chain COM is large; use a tighter box around COM still, size kept
            rec_paths[g] = path
            centers[g] = cen
            p["pdb"] = path.stem.replace("_clean_h", "")
        else:
            pdb = p["pdb"]
            print(f"[receptor] {g} {pdb}")
            path, cen_guess = ensure_receptor_pdbqt(lib, pdb, session)
            rec_paths[g] = path
            if p.get("cx") is not None:
                centers[g] = (float(p["cx"]), float(p["cy"]), float(p["cz"]))
            else:
                centers[g] = cen_guess
                p["cx"], p["cy"], p["cz"] = cen_guess

    # write registry tables
    prot_csv = root / "分子对接_蛋白表.csv"
    with prot_csv.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["entry号", "蛋白质靶点", "蛋白质3D结构名称", "x center", "y center", "z center"],
        )
        w.writeheader()
        for p in proteins:
            cx, cy, cz = centers[p["gene"]]
            w.writerow(
                {
                    "entry号": p.get("entry", ""),
                    "蛋白质靶点": p["gene"],
                    "蛋白质3D结构名称": Path(rec_paths[p["gene"]]).name.replace("_clean_h.pdbqt", "").replace("_af_clean_h.pdbqt", "_af"),
                    "x center": f"{cx:.3f}",
                    "y center": f"{cy:.3f}",
                    "z center": f"{cz:.3f}",
                }
            )

    comp_csv = root / "分子对接_化合物表.csv"
    with comp_csv.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["活性成分名称", "活性成分重命名", "活性成分3D结构名称"])
        w.writeheader()
        for i, lig in enumerate(ligands, 1):
            w.writerow(
                {
                    "活性成分名称": lig["name"],
                    "活性成分重命名": str(i),
                    "活性成分3D结构名称": lig["cid"],
                }
            )

    # create tasks: protein-major order
    tasks = []
    n = 0
    for p in proteins:
        for lig in ligands:
            n += 1
            tasks.append({"n": n, "protein": p, "ligand": lig})

    summary_rows = []
    for t in tasks:
        n = t["n"]
        p = t["protein"]
        lig = t["ligand"]
        g = p["gene"]
        td = root / str(n)
        td.mkdir(parents=True, exist_ok=True)
        (td / "图片").mkdir(exist_ok=True)
        rec_src = rec_paths[g]
        lig_src = lig_paths[lig["cid"]]
        rec_dst = td / rec_src.name
        lig_dst = td / lig_src.name
        # always refresh receptor from lib (may have been rigidified after first assemble)
        shutil.copy2(rec_src, rec_dst)
        if not lig_dst.exists() or lig_dst.stat().st_size < 100:
            shutil.copy2(lig_src, lig_dst)
        # drop failed prior logs so vina retries; keep successful output.pdbqt
        if not (td / "output.pdbqt").is_file():
            (td / "log.txt").unlink(missing_ok=True)
        write_config(
            td / "config.txt",
            rec_dst,
            lig_dst,
            centers[g],
            size=args.size,
            exhaustiveness=args.exhaustiveness,
        )
        (td / "task_info.txt").write_text(
            f"task={n}\nprotein={g}\npdb={rec_dst.stem}\nligand={lig['name']}\ncid={lig['cid']}\n",
            encoding="utf-8",
        )
        aff = None
        if args.run_vina:
            print(f"[vina] {n}/{len(tasks)} {g} x {lig['name']}")
            try:
                aff = run_vina(td)
            except subprocess.CalledProcessError as e:
                print(f"  FAIL vina: {e}")
                (td / "log.txt").write_text((e.stderr or "") + "\n" + (e.stdout or ""), encoding="utf-8")
        else:
            aff = parse_best_affinity(td / "log.txt")
        summary_rows.append(
            {
                "task": str(n),
                "protein": g,
                "pdb": rec_dst.stem.replace("_clean_h", "").replace("_af_clean_h", "_af"),
                "ligand": lig["slug"],
                "ligand_name": lig["name"],
                "cid": lig["cid"],
                "affinity_kcal_mol": "" if aff is None else f"{aff:.3f}",
            }
        )

    write_summary_csv(root / "summary_vina.csv", summary_rows)

    # affinity matrix xlsx-like csv
    mat_path = root / "矩阵_结合能_DockingAffinityMatrix.csv"
    prot_names = [p["gene"] for p in proteins]
    lig_names = [l["name"] for l in ligands]
    grid = {g: {ln: "" for ln in lig_names} for g in prot_names}
    for r in summary_rows:
        grid[r["protein"]][r["ligand_name"]] = r["affinity_kcal_mol"]
    with mat_path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["protein"] + lig_names)
        for g in prot_names:
            w.writerow([g] + [grid[g][ln] for ln in lig_names])

    readme = root / "文件夹内容说明.txt"
    readme.write_text(
        "\n".join(
            [
                f"项目：{root.name}",
                "结构来源优先：D:\\数据库\\分子对接数据库",
                f"任务数：{len(tasks)} = {len(proteins)} 蛋白 × {len(ligands)} 化合物",
                "流程：组装任务 → Vina → PyMOL big/surface/detail.pse",
                "【断点】detail 标签手调：请打开各任务 detail-N.pse 调整残基/氢键标签位置。",
                "手调完成后告知 Agent，再运行 export_detail_png_from_pse.py 与 result 拼图。",
                "禁止在手调前对 detail 使用 cmd.png 重渲。",
                "",
            ]
        ),
        encoding="utf-8",
    )

    if args.make_pymol:
        pymol_py = Path(r"E:\pymol\python.exe")
        viz = SCRIPT_DIR / "pymol_dock_viz_standard.py"
        if not pymol_py.is_file():
            raise SystemExit(f"PyMOL python not found: {pymol_py}")
        print("[pymol] generating big/surface/detail for all tasks ...")
        subprocess.run(
            [str(pymol_py), str(viz), "--jobs-root", str(root), "--all"],
            check=True,
        )
        print("[BREAKPOINT] detail.pse 已生成。请人工调整各任务 图片旁的 detail-N.pse 标签位置。")
        print("完成后回复：detail 标签已调好，继续导出/拼图。")
        stop = root / "BREAKPOINT_等待手调detail标签.txt"
        stop.write_text(
            "断点：PyMOL detail-N.pse 已生成。\n"
            "请在每个任务目录打开 detail-N.pse，手调残基/氢键标签位置并保存。\n"
            "保存后回复 Agent「detail 已调好」；再运行 export_detail_png_from_pse.py + result 拼图。\n"
            "在此之前不要跑 export/result。\n",
            encoding="utf-8",
        )

    print(f"DONE project={root}")
    print(f"tasks={len(tasks)} summary={root / 'summary_vina.csv'}")


if __name__ == "__main__":
    main()
