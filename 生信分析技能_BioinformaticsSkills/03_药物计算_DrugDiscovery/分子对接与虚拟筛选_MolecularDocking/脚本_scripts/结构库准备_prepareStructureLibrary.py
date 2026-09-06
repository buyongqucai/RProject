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
  python 结构库准备_prepareStructureLibrary.py --all --workers 8 \
      --protein-table 分子对接_蛋白表_扩展3000.csv \
      --compound-table 分子对接_化合物表_扩展7000.csv
幂等：已存在且非空的产物一律跳过。2026-08-31 起化合物文件以 PubChem CID 命名。
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

OBA = r"E:\OpenBabel-3.1.1\obabel.exe"
UA = {"User-Agent": "Mozilla/5.0 (structure-lib-prep; mailto:local)"}

PDB_RE = re.compile(r"^\d[A-Za-z0-9]{3}$")       # 如 5oaz / 1unq
UP_RE = re.compile(r"^[a-z][a-z0-9]{4,8}$")       # 如 o60488 / p05141

_LOG_LOCK = threading.Lock()
_DL_LOCK = threading.Lock()
_DL_LAST = [0.0]


def rate_limit(min_interval: float = 1.2) -> None:
    """全局下载限速。PubChem 忙碌时 0.45s 仍会 503，默认 1.2s。"""
    with _DL_LOCK:
        wait = min_interval - (time.time() - _DL_LAST[0])
        if wait > 0:
            time.sleep(wait)
        _DL_LAST[0] = time.time()


def safe_name(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", name.strip().lower()).strip("_")
    return re.sub(r"_+", "_", s)


SALT_WORDS = {
    "hydrochloride", "dihydrochloride", "hydrobromide", "hydroiodide",
    "mesylate", "besylate", "tosylate", "ditosylate", "maleate", "malate",
    "fumarate", "succinate", "citrate", "tartrate", "acetate", "propionate",
    "phosphate", "diphosphate", "sulfate", "bisulfate", "nitrate",
    "sodium", "potassium", "calcium", "magnesium", "zinc",
    "chloride", "bromide", "iodide", "fluoride",
    "pamoate", "embonate", "lactate", "gluconate", "stearate",
    "monohydrate", "dihydrate", "trihydrate", "anhydrous",
    "dimeglumine", "meglumine", "besilate",
}


def _body_head(content: bytes) -> bytes:
    return content[:600] if content else b""


def _is_busy(status: int, body: bytes) -> bool:
    if status in (429, 503):
        return True
    h = _body_head(body)
    return b"ServerBusy" in h or b"Too many requests" in h or b"PUGREST.ServerBusy" in h


def _is_not_found(status: int, body: bytes) -> bool:
    if status == 404:
        return True
    h = _body_head(body)
    return b"PUGREST.NotFound" in h or b"Status: 404" in h


def _sdf_looks_ok(dest: Path) -> bool:
    if not dest.exists() or dest.stat().st_size < 200:
        return False
    raw = dest.read_bytes()[:2500]
    if b"ServerBusy" in raw or b"PUGREST" in raw or b"Status: 503" in raw:
        dest.unlink(missing_ok=True)
        return False
    if b"V2000" not in raw and b"V3000" not in raw:
        dest.unlink(missing_ok=True)
        return False
    return True


def stripped_drug_name(name: str) -> str:
    parts = [p for p in re.split(r"[_\-\s]+", name.strip().lower()) if p]
    while parts and parts[-1] in SALT_WORDS:
        parts.pop()
    return " ".join(parts)


def fetch(s: requests.Session, url: str, dest: Path, binary=True, tries=2) -> bool:
    """下载到 dest。404 立即失败；503 只短退 1–2 次，改由上层换源（CACTUS）。"""
    if _sdf_looks_ok(dest):
        return True
    for k in range(tries):
        rate_limit()
        try:
            r = s.get(url, timeout=45)
            body = r.content if binary else (r.text or "").encode()
            if _is_not_found(r.status_code, body):
                return False
            if _is_busy(r.status_code, body) or r.status_code in (500, 502):
                time.sleep(8 * (k + 1))
                continue
            if r.status_code != 200 or len(body) < 200:
                time.sleep(3 * (k + 1))
                continue
            dest.write_bytes(body)
            if _sdf_looks_ok(dest):
                return True
            dest.unlink(missing_ok=True)
        except Exception:
            time.sleep(5 * (k + 1))
    return False


def pubchem_parent_cids(s: requests.Session, cid: str) -> list[str]:
    rate_limit()
    url = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
           f"{cid}/cids/JSON?cids_type=parent")
    try:
        r = s.get(url, timeout=60)
        if _is_busy(r.status_code, r.content) or r.status_code != 200:
            return []
        ids = [str(x) for x in r.json().get("IdentifierList", {}).get("CID", [])]
        return [x for x in ids if x and x != str(cid)]
    except Exception:
        return []


def pug_sdf_3d(s: requests.Session, cid: str, dest: Path) -> bool:
    return fetch(
        s,
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d",
        dest,
    )


def pug_sdf_3d_name(s: requests.Session, name: str, dest: Path) -> bool:
    if not name or len(name) < 3:
        return False
    q = requests.utils.quote(name)
    return fetch(
        s,
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{q}/SDF?record_type=3d",
        dest,
        tries=3,
    )


def cactus_sdf_3d(s: requests.Session, query: str, dest: Path) -> bool:
    """NIH CACTUS 3D SDF，避开 PubChem PUG 限流。"""
    if not query or len(query) < 3:
        return False
    q = requests.utils.quote(query.strip())
    return fetch(
        s,
        f"https://cactus.nci.nih.gov/chemical/structure/{q}/file?format=sdf&get3d=True",
        dest,
        tries=3,
    )


def download_ligand_sdf(s: requests.Session, cid: str, name: str, dest: Path) -> str:
    """返回来源标记；失败返回空串。PubChem 3D → CACTUS 名称 → 母体 CID → 2D。"""
    if _sdf_looks_ok(dest) and sdf_zspan(dest) >= 0.3:
        return "cached_3d"
    if dest.exists():
        dest.unlink(missing_ok=True)
    dname = stripped_drug_name(name)
    tokens = set(re.split(r"[_\-\s]+", name.strip().lower()))
    is_salt = bool(tokens & SALT_WORDS)
    if not is_salt and pug_sdf_3d(s, cid, dest):
        return "3d"
    if dname and cactus_sdf_3d(s, dname, dest):
        return f"cactus:{dname}"
    for pcid in pubchem_parent_cids(s, cid)[:2]:
        if pug_sdf_3d(s, pcid, dest):
            return f"parent3d:{pcid}"
    if dname and pug_sdf_3d_name(s, dname, dest):
        return f"name3d:{dname}"
    if cactus_sdf_3d(s, cid, dest):
        return f"cactus_cid:{cid}"
    if fetch(s, f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF",
             dest, tries=2):
        return "2d"
    return ""


def download_protein(s: requests.Session, struct: str, big: Path) -> str:
    """返回来源标记：rcsb / rcsb-cif / afv6 / afv4 / FAIL。"""
    dest = big / f"{struct.lower()}.pdb"
    if dest.exists() and dest.stat().st_size > 100:
        return "cached"
    if PDB_RE.match(struct):
        ok = fetch(s, f"https://files.rcsb.org/download/{struct.upper()}.pdb", dest)
        if ok:
            return "rcsb"
        cif = big / f"{struct.lower()}.cif"
        ok_cif = fetch(s, f"https://files.rcsb.org/download/{struct.upper()}.cif", cif)
        if ok_cif:
            ok_conv, _ = obabel([str(cif), "-O", str(dest)])
            if ok_conv and dest.exists() and dest.stat().st_size > 100:
                return "rcsb-cif"
        return "FAIL"
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


def obabel(args: list[str], timeout: int = 180) -> tuple[bool, str]:
    try:
        p = subprocess.run(
            [OBA, *args], capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        return False, f"timeout {timeout}s"
    except Exception as e:
        return False, str(e)[:200]
    msg = (p.stderr or p.stdout or "")
    # 勿把 "20 molecules converted" 误判为 0（子串坑）
    zero = bool(re.search(r"(^|\D)0 molecules converted", msg))
    ok = p.returncode == 0 and not zero
    return ok, msg[-300:]


def sdf_xyz_spans(sdf: Path) -> tuple[float, float, float]:
    """原子块 x/y/z 跨度。平面芳香分子 z≈0 但 xy 仍是合法 3D 记录。"""
    try:
        txt = sdf.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 0.0, 0.0, 0.0
    lines = txt.splitlines()
    if len(lines) < 4:
        return 0.0, 0.0, 0.0
    try:
        n_atoms = int(lines[3][0:3])
    except ValueError:
        return 0.0, 0.0, 0.0
    xs, ys, zs = [], [], []
    for ln in lines[4:4 + n_atoms]:
        try:
            xs.append(float(ln[0:10]))
            ys.append(float(ln[10:20]))
            zs.append(float(ln[20:30]))
        except ValueError:
            pass
    def span(v: list[float]) -> float:
        return (max(v) - min(v)) if v else 0.0
    return span(xs), span(ys), span(zs)


def sdf_zspan(sdf: Path) -> float:
    """3D 校验：原子块 z 坐标跨度。"""
    return sdf_xyz_spans(sdf)[2]


def sdf_accept_3d(sdf: Path) -> tuple[bool, str]:
    """放行：z-span≥0.3，或平面分子但 xy 跨度均 >1 Å。"""
    x, y, z = sdf_xyz_spans(sdf)
    if z >= 0.3:
        return True, f"z-span {z:.2f}"
    if x > 1.0 and y > 1.0:
        return True, f"planar xy {x:.2f}/{y:.2f} z {z:.2f}"
    return False, f"flat z-span {z:.2f} xy {x:.2f}/{y:.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--db", default=r"D:\数据库\分子对接数据库")
    ap.add_argument("--root", default=None, help=r"默认 <db>\test")
    ap.add_argument("--protein-table", default=None,
                    help=r"默认 <db>\分子对接_蛋白表.csv")
    ap.add_argument("--compound-table", default=None,
                    help=r"默认 <db>\分子对接_化合物表.csv")
    ap.add_argument("--workers", type=int, default=1,
                    help="并行线程数（obabel 为子进程，可并行）")
    ap.add_argument("--skip-proteins", action="store_true")
    ap.add_argument("--skip-ligands", action="store_true")
    ap.add_argument("--max-gb", type=float, default=38.0,
                    help="库总大小上限（GiB），超过即停止派发新任务")
    args = ap.parse_args()
    db = Path(args.db)
    root = Path(args.root) if args.root else db / "test"
    for d in ("big", "big_clean", "big_clean_h", "small", "small_clean", "small_clean_h"):
        (root / d).mkdir(parents=True, exist_ok=True)

    s = requests.Session()
    s.trust_env = False
    s.headers.update(UA)
    log_path = root / "_structure_lib_log.csv"
    write_header = not log_path.exists()
    log_fh = log_path.open("a", newline="", encoding="utf-8-sig")
    log = csv.writer(log_fh)
    if write_header:
        log.writerow(["kind", "key", "stage", "status", "note", "ts"])

    def log_row(*vals) -> None:
        with _LOG_LOCK:
            log.writerow(vals)
            log_fh.flush()

    def over_cap() -> bool:
        total = sum(f.stat().st_size for f in root.rglob("*") if f.is_file())
        return total / 2**30 > args.max_gb

    def read_csv_any(path: Path) -> list[dict]:
        raw = path.read_bytes()
        for enc in ("utf-8-sig", "gbk"):
            try:
                return list(csv.DictReader(raw.decode(enc).splitlines()))
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError("unknown", b"", 0, 1, str(path))

    def do_protein(st: str, i: int, n_all: int) -> None:
        try:
            raw = root / "big" / f"{st}.pdb"
            if not (raw.exists() and raw.stat().st_size > 100):
                rate_limit()
            src = download_protein(s, st, root / "big")
            log_row("protein", st, "download", src, "", time.strftime("%F %T"))
            if src == "FAIL":
                print(f"[{i}/{n_all}] {st} download FAIL", flush=True)
                return
            raw = root / "big" / f"{st}.pdb"
            clean = root / "big_clean" / f"{st}_clean.pdb"
            n = clean_protein(raw, clean)
            if n == 0:
                log_row("protein", st, "clean", "FAIL", "0 ATOM", time.strftime("%F %T"))
                return
            pdbqt = root / "big_clean_h" / f"{st}_clean_h.pdbqt"
            if not (pdbqt.exists() and pdbqt.stat().st_size > 100):
                ok, msg = obabel([str(clean), "-O", str(pdbqt), "-h"])
                log_row("protein", st, "pdbqt", "OK" if ok else "FAIL", msg,
                        time.strftime("%F %T"))
                if not ok:
                    print(f"[{i}/{n_all}] {st} pdbqt FAIL {msg[-80:]}", flush=True)
                    return
            print(f"[{i}/{n_all}] {st} {src}", flush=True)
        except Exception as e:
            log_row("protein", st, "error", "FAIL", str(e)[:200], time.strftime("%F %T"))
            print(f"[{i}/{n_all}] {st} ERROR {e}", flush=True)

    def do_ligand(cid: str, name: str, i: int, n_all: int) -> None:
        stem = cid  # 2026-08-31 起：化合物文件一律以 PubChem CID 命名
        sdf = root / "small" / f"{stem}.sdf"
        pdbqt_ready = root / "small_clean_h" / f"{stem}_clean_h.pdbqt"
        if pdbqt_ready.exists() and pdbqt_ready.stat().st_size > 100:
            print(f"[{i}/{n_all}] {name}({cid}) cached", flush=True)
            return
        try:
            src = download_ligand_sdf(s, cid, name, sdf)
            log_row("ligand", cid, "download",
                    ("OK_" + src) if src else "FAIL", name,
                    time.strftime("%F %T"))
            if not src:
                print(f"[{i}/{n_all}] {name}({cid}) download FAIL", flush=True)
                return
        except Exception as e:
            log_row("ligand", cid, "download", "FAIL", str(e)[:200], time.strftime("%F %T"))
            print(f"[{i}/{n_all}] {name}({cid}) ERROR {e}", flush=True)
            return
        try:
            clean = root / "small_clean" / f"{stem}_clean.sdf"
            ok3d, note3d = sdf_accept_3d(sdf)
            if not ok3d:
                log_row("ligand", cid, "clean", "FAIL", note3d,
                        time.strftime("%F %T"))
                return
            if "planar" in note3d:
                log_row("ligand", cid, "clean", "planar_ok", note3d,
                        time.strftime("%F %T"))
            if not clean.exists():
                clean.write_bytes(sdf.read_bytes())
            pdbqt = root / "small_clean_h" / f"{stem}_clean_h.pdbqt"
            if pdbqt.exists() and pdbqt.stat().st_size <= 100:
                pdbqt.unlink(missing_ok=True)
            if not (pdbqt.exists() and pdbqt.stat().st_size > 100):
                mol2 = root / "small_clean_h" / f"{stem}.mol2"
                ok1, m1 = obabel([str(clean), "-O", str(mol2), "-h"])
                ok2, m2 = (False, "no mol2")
                if ok1 and mol2.exists():
                    mol2_txt = mol2.read_text(encoding="utf-8", errors="ignore")
                    if re.search(r"\bSi\b", mol2_txt) or "siloxane" in name.lower():
                        mol2.unlink(missing_ok=True)
                        log_row("ligand", cid, "pdbqt", "SKIP_unsupported",
                                "Si/Vina", time.strftime("%F %T"))
                        print(f"[{i}/{n_all}] {name}({cid}) SKIP Si", flush=True)
                        return
                    ok2, m2 = obabel([str(mol2), "-O", str(pdbqt), "-h",
                                      "--partialcharge", "gasteiger"])
                    mol2.unlink(missing_ok=True)
                log_row("ligand", cid, "pdbqt", "OK" if ok2 else "FAIL",
                        (m1 + "|" + m2)[-250:], time.strftime("%F %T"))
            print(f"[{i}/{n_all}] {name}({cid}) {src}", flush=True)
        except Exception as e:
            log_row("ligand", cid, "error", "FAIL", str(e)[:200], time.strftime("%F %T"))
            print(f"[{i}/{n_all}] {name}({cid}) ERROR {e}", flush=True)

    # ---------- 受体 ----------
    if not args.skip_proteins:
        proteins = read_csv_any(Path(args.protein_table) if args.protein_table
                                else db / "分子对接_蛋白表.csv")
        structs = []
        seen = set()
        for row in proteins:
            st = (row.get("蛋白质3D结构名称") or "").strip().lower()
            if st and st not in seen:
                seen.add(st)
                structs.append(st)
        if args.pilot:
            structs = structs[: args.pilot]
        print(f"[protein] {len(structs)} structures, workers={args.workers}", flush=True)
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {}
            for i, st in enumerate(structs, 1):
                if over_cap():
                    print("[cap] 超过库大小上限，停止派发新蛋白任务", flush=True)
                    break
                futs[ex.submit(do_protein, st, i, len(structs))] = st
            for fut in as_completed(futs):
                fut.result()

    # ---------- 配体 ----------
    if not args.skip_ligands:
        comps = read_csv_any(Path(args.compound_table) if args.compound_table
                             else db / "分子对接_化合物表.csv")
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
        print(f"[ligand] {len(ligands)} compounds, workers={args.workers}", flush=True)
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {}
            for i, (cid, name) in enumerate(ligands, 1):
                if over_cap():
                    print("[cap] 超过库大小上限，停止派发新配体任务", flush=True)
                    break
                futs[ex.submit(do_ligand, cid, name, i, len(ligands))] = cid
            for fut in as_completed(futs):
                fut.result()

    log_fh.close()
    total = sum(f.stat().st_size for f in root.rglob("*") if f.is_file())
    print(f"[done] total size = {total / 2**30:.2f} GiB", flush=True)


if __name__ == "__main__":
    main()
