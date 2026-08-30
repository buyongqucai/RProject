# -*- coding: utf-8 -*-
"""结构库准备：按登记表下载 + 清洗 + 加氢（对齐 DockingPipelineSOP §1/§3）。

目录（--root 默认 D:\\数据库\\分子对接数据库\\test）：
  big/           受体原始 PDB（RCSB；UniProt 条目走 AlphaFold）
  big_clean/     去水/去 HETATM 的 PDB（仅 ATOM 记录）
  big_clean_h/   加氢 PDBQT（obabel -h，gasteiger）
  small/         配体 PubChem 3D SDF（record_type=3d，校验 z-span 非平面）
  small_clean/   校验后 SDF
  small_clean_h/ SDF →(obabel -h)→ MOL2 →(gasteiger)→ PDBQT；禁止 --gen3d

用法：
  python 结构库准备_prepareStructureLibrary.py --pilot 5
  python 结构库准备_prepareStructureLibrary.py --all
幂等：已存在且非空的产物一律跳过。
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import time
from pathlib import Path

import requests

OBA = r"E:\OpenBabel-3.1.1\obabel.exe"
UA = {"User-Agent": "Mozilla/5.0 (structure-lib-prep; mailto:local)"}

PDB_RE = re.compile(r"^\d[A-Za-z0-9]{3}$")       # 如 5oaz / 1unq
UP_RE = re.compile(r"^[a-z][a-z0-9]{4,8}$")       # 如 o60488 / p05141


def safe_name(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", name.strip().lower()).strip("_")
    return re.sub(r"_+", "_", s)


def fetch(s: requests.Session, url: str, dest: Path, binary=True, tries=3) -> bool:
    if dest.exists() and dest.stat().st_size > 100:
        return True
    for k in range(tries):
        try:
            r = s.get(url, timeout=120)
            if r.status_code == 404:
                return False
            r.raise_for_status()
            dest.write_bytes(r.content if binary else r.text.encode())
            return True
        except Exception:
            time.sleep(2 * (k + 1))
    return False


def download_protein(s: requests.Session, struct: str, big: Path) -> str:
    """返回来源标记：rcsb / afv6 / afv4 / FAIL。"""
    dest = big / f"{struct.lower()}.pdb"
    if dest.exists() and dest.stat().st_size > 100:
        return "cached"
    if PDB_RE.match(struct):
        ok = fetch(s, f"https://files.rcsb.org/download/{struct.upper()}.pdb", dest)
        return "rcsb" if ok else "FAIL"
    if UP_RE.match(struct):
        for ver in ("v6", "v4"):
            ok = fetch(s, f"https://alphafold.ebi.ac.uk/files/"
                          f"AF-{struct.upper()}-F1-model_{ver}.pdb", dest)
            if ok:
                return f"af{ver}"
    return "FAIL"


def clean_protein(raw: Path, dest: Path) -> int:
    """仅保留 ATOM / TER / END；去 HETATM（水、配体、离子）。"""
    if dest.exists() and dest.stat().st_size > 100:
        return -1
    n = 0
    with raw.open("r", encoding="utf-8", errors="ignore") as fi, \
            dest.open("w", encoding="utf-8", newline="\n") as fo:
        for line in fi:
            if line.startswith(("ATOM  ", "TER", "END")):
                fo.write(line)
                n += line.startswith("ATOM  ")
    return n


def obabel(args: list[str]) -> tuple[bool, str]:
    p = subprocess.run([OBA, *args], capture_output=True, text=True, timeout=300)
    ok = p.returncode == 0 and not (p.stderr and "0 molecules converted" in p.stderr)
    return ok, (p.stderr or p.stdout or "")[-300:]


def sdf_zspan(sdf: Path) -> float:
    """3D 校验：原子块 z 坐标跨度（平面=0 须拒）。"""
    try:
        txt = sdf.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 0.0
    lines = txt.splitlines()
    if len(lines) < 4:
        return 0.0
    try:
        n_atoms = int(lines[3][0:3])
    except ValueError:
        return 0.0
    zs = []
    for ln in lines[4:4 + n_atoms]:
        try:
            zs.append(float(ln[20:30]))
        except ValueError:
            pass
    return (max(zs) - min(zs)) if zs else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--db", default=r"D:\数据库\分子对接数据库")
    ap.add_argument("--root", default=None, help="默认 <db>\\test")
    args = ap.parse_args()
    db = Path(args.db)
    root = Path(args.root) if args.root else db / "test"
    for d in ("big", "big_clean", "big_clean_h", "small", "small_clean", "small_clean_h"):
        (root / d).mkdir(parents=True, exist_ok=True)

    s = requests.Session()
    s.headers.update(UA)
    log_path = root / "_structure_lib_log.csv"
    write_header = not log_path.exists()
    log_fh = log_path.open("a", newline="", encoding="utf-8-sig")
    log = csv.writer(log_fh)
    if write_header:
        log.writerow(["kind", "key", "stage", "status", "note", "ts"])

    def read_csv_any(path: Path) -> list[dict]:
        raw = path.read_bytes()
        for enc in ("utf-8-sig", "gbk"):
            try:
                return list(csv.DictReader(raw.decode(enc).splitlines()))
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError("unknown", b"", 0, 1, str(path))

    # ---------- 受体 ----------
    proteins = read_csv_any(db / "分子对接_蛋白表.csv")
    structs = []
    seen = set()
    for row in proteins:
        st = (row.get("蛋白质3D结构名称") or "").strip().lower()
        if st and st not in seen:
            seen.add(st)
            structs.append(st)
    if args.pilot:
        structs = structs[: args.pilot]
    print(f"[protein] {len(structs)} structures", flush=True)
    for i, st in enumerate(structs, 1):
        raw = root / "big" / f"{st}.pdb"
        src = download_protein(s, st, root / "big")
        log.writerow(["protein", st, "download", src, "", time.strftime("%F %T")])
        if src == "FAIL":
            print(f"[{i}/{len(structs)}] {st} download FAIL", flush=True)
            continue
        clean = root / "big_clean" / f"{st}_clean.pdb"
        n = clean_protein(raw, clean)
        if n == 0:
            log.writerow(["protein", st, "clean", "FAIL", "0 ATOM", time.strftime("%F %T")])
            continue
        pdbqt = root / "big_clean_h" / f"{st}_clean_h.pdbqt"
        if not (pdbqt.exists() and pdbqt.stat().st_size > 100):
            ok, msg = obabel([str(clean), "-O", str(pdbqt), "-h"])
            log.writerow(["protein", st, "pdbqt", "OK" if ok else "FAIL", msg,
                          time.strftime("%F %T")])
        print(f"[{i}/{len(structs)}] {st} {src}", flush=True)
        time.sleep(0.3)

    # ---------- 配体 ----------
    comps = read_csv_any(db / "分子对接_化合物表.csv")
    ligands = []
    seen = set()
    for row in comps:
        cid = (row.get("活性成分3D结构名称") or "").strip()
        name = safe_name(row.get("活性成分名称") or f"cid_{cid}")
        if cid and cid not in seen:
            seen.add(cid)
            ligands.append((cid, name))
    if args.pilot:
        ligands = ligands[: args.pilot]
    print(f"[ligand] {len(ligands)} compounds", flush=True)
    for i, (cid, name) in enumerate(ligands, 1):
        sdf = root / "small" / f"{name}.sdf"
        ok = fetch(s, f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
                      f"{cid}/SDF?record_type=3d", sdf)
        log.writerow(["ligand", cid, "download", "OK" if ok else "FAIL", name,
                      time.strftime("%F %T")])
        if not ok:
            print(f"[{i}/{len(ligands)}] {name}({cid}) download FAIL", flush=True)
            continue
        clean = root / "small_clean" / f"{name}_clean.sdf"
        z = sdf_zspan(sdf)
        if z < 0.3:
            log.writerow(["ligand", cid, "clean", "FAIL", f"z-span {z:.2f}",
                          time.strftime("%F %T")])
            continue
        if not clean.exists():
            clean.write_bytes(sdf.read_bytes())
        pdbqt = root / "small_clean_h" / f"{name}_clean_h.pdbqt"
        if not (pdbqt.exists() and pdbqt.stat().st_size > 100):
            mol2 = root / "small_clean_h" / f"{name}.mol2"
            ok1, m1 = obabel([str(clean), "-O", str(mol2), "-h"])
            ok2, m2 = (False, "no mol2")
            if ok1 and mol2.exists():
                ok2, m2 = obabel([str(mol2), "-O", str(pdbqt), "-h",
                                  "--partialcharge", "gasteiger"])
                mol2.unlink(missing_ok=True)
            log.writerow(["ligand", cid, "pdbqt", "OK" if ok2 else "FAIL",
                          (m1 + "|" + m2)[-250:], time.strftime("%F %T")])
        print(f"[{i}/{len(ligands)}] {name}({cid})", flush=True)
        time.sleep(0.3)

    log_fh.close()
    total = sum(f.stat().st_size for f in root.rglob("*") if f.is_file())
    print(f"[done] total size = {total / 2**30:.2f} GiB", flush=True)


if __name__ == "__main__":
    main()
