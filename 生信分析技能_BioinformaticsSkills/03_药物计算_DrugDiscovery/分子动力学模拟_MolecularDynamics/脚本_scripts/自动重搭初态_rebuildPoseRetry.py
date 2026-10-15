#!/usr/bin/env python3
"""A3 飞散后：自动选无大段缺环结构并重搭一轮初态（A1/A2 优先）。

输出目录含 protein.pdb / lig_h.mol2 / pose_class.txt / rebuild_report.json。
退出码：0=可重跑；2=无法重搭（报告仍写出）。
"""
from __future__ import annotations

import json
import math
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
from openbabel import openbabel as ob
from openbabel import pybel
from scipy.optimize import linear_sum_assignment

SCRIPT_DIR = Path(__file__).resolve().parent
REGISTRY = SCRIPT_DIR / "md重搭登记_PoseRetryRegistry.json"
GAP_EXCLUDE_LEN = 5


def http_json(url: str, data: dict | None = None, timeout: int = 60):
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "md-pose-retry/1.0"},
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def download(url: str, dest: Path, timeout: int = 90):
    urllib.request.urlretrieve(url, dest)


def gaps_from_pdb_text(text: str) -> list[tuple[str, int, int, int]]:
    lines = text.splitlines()
    miss = []
    on = False
    for line in lines:
        if line.startswith("REMARK 465"):
            if "M RES C SSSEQI" in line or "RES C SSSEQI" in line:
                on = True
                continue
            if not on:
                continue
            parts = line[10:].split()
            if len(parts) >= 3 and len(parts[-2]) == 1 and parts[-2].isalpha():
                try:
                    miss.append((parts[-2], int(parts[-1])))
                except ValueError:
                    pass
            continue
        if on:
            on = False
    if not miss:
        ca = defaultdict(list)
        for line in lines:
            if not line.startswith("ATOM") or line[12:16].strip() != "CA":
                continue
            ch = line[21].strip() or "_"
            try:
                ca[ch].append(int(line[22:26]))
            except ValueError:
                continue
        for ch, rs in ca.items():
            rs = sorted(set(rs))
            for i in range(len(rs) - 1):
                if rs[i + 1] - rs[i] > 1:
                    for r in range(rs[i] + 1, rs[i + 1]):
                        miss.append((ch, r))
    by = defaultdict(list)
    for c, r in miss:
        by[c].append(r)
    segs = []
    for c, rs in by.items():
        rs = sorted(set(rs))
        if not rs:
            continue
        a = b = rs[0]
        for x in rs[1:]:
            if x == b + 1:
                b = x
            else:
                segs.append((c, a, b, b - a + 1))
                a = b = x
        segs.append((c, a, b, b - a + 1))
    return segs


def max_gap_len(segs, chain: str | None) -> int:
    best = 0
    for c, _a, _b, L in segs:
        if chain and c != chain and chain != "_":
            # allow other chains; score preferred chain primarily
            if c != chain:
                continue
        best = max(best, L)
    if best == 0 and segs:
        best = max(L for *_x, L in segs)
    return best


def search_pdb_ids(uniprot: str, rows: int = 25) -> list[str]:
    q = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": (
                    "rcsb_polymer_entity_container_identifiers."
                    "reference_sequence_identifiers.database_accession"
                ),
                "operator": "exact_match",
                "value": uniprot,
            },
        },
        "return_type": "entry",
        "request_options": {
            "paginate": {"start": 0, "rows": rows},
            "sort": [{"sort_by": "rcsb_entry_info.resolution_combined", "direction": "asc"}],
        },
    }
    try:
        data = http_json("https://search.rcsb.org/rcsbsearch/v2/query", q)
    except Exception as exc:  # noqa: BLE001
        print(f"RCSB search failed: {exc}", file=sys.stderr)
        return []
    return [x["identifier"] for x in data.get("result_set", [])]


def entry_meta(pdb_id: str) -> dict:
    try:
        return http_json(f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}")
    except Exception:  # noqa: BLE001
        return {}


def _chain_ca_count(pdb_text: str, chain: str) -> int:
    n = 0
    for line in pdb_text.splitlines():
        if (
            line.startswith("ATOM")
            and (line[21].strip() or "_") == chain
            and line[12:16].strip() == "CA"
        ):
            n += 1
    return n


def list_protein_chains(pdb_text: str) -> list[tuple[str, int]]:
    """Return (chain, CA_count) for chains that look like protein (have CA)."""
    counts: dict[str, int] = defaultdict(int)
    for line in pdb_text.splitlines():
        if not line.startswith("ATOM") or line[12:16].strip() != "CA":
            continue
        ch = line[21].strip() or "_"
        counts[ch] += 1
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))


def extract_chain_atoms(pdb_text: str, chain: str) -> str:
    """Extract one polymer chain; prefer protein (CA) over DNA/RNA-only chains."""
    def _extract(ch: str) -> list[str]:
        out = []
        for line in pdb_text.splitlines():
            if line.startswith("ATOM") and (line[21].strip() or "_") == ch:
                out.append(line)
            elif line.startswith("TER") and out:
                # keep going: DNA entries often TER between nucleotides
                if _chain_ca_count("\n".join(out), ch) > 0:
                    break
        return out

    prot_chains = list_protein_chains(pdb_text)
    chosen = chain
    if _chain_ca_count(pdb_text, chain) == 0:
        if prot_chains:
            chosen = prot_chains[0][0]
        else:
            return ""
    out = _extract(chosen)
    if not out and prot_chains:
        chosen = prot_chains[0][0]
        out = _extract(chosen)
    return "\n".join(out) + ("\n" if out else "")


def largest_het_com(pdb_text: str, chain: str) -> tuple[np.ndarray, str] | None:
    groups: dict[tuple[str, str, int], list[list[float]]] = defaultdict(list)
    skip = {
        "HOH",
        "WAT",
        "SOL",
        "SO4",
        "PO4",
        "GOL",
        "EDO",
        "ACT",
        "CL",
        "NA",
        "MG",
        "ZN",
        "CA",
        "MSE",
    }
    for line in pdb_text.splitlines():
        if not line.startswith("HETATM"):
            continue
        ch = line[21].strip() or "_"
        if chain and ch != chain:
            continue
        res = line[17:20].strip()
        if res in skip:
            continue
        try:
            resseq = int(line[22:26])
            xyz = [float(line[30:38]), float(line[38:46]), float(line[46:54])]
        except ValueError:
            continue
        name = line[12:16].strip()
        elem = "".join(c for c in name if c.isalpha())[:1].upper()
        if elem == "H":
            continue
        groups[(ch, res, resseq)].append(xyz)
    if not groups:
        return None
    key = max(groups, key=lambda k: len(groups[k]))
    arr = np.asarray(groups[key], float)
    return arr.mean(0), key[1]


def protein_ca_com(pdb_atom_text: str) -> np.ndarray:
    pts = []
    for line in pdb_atom_text.splitlines():
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            pts.append(
                [float(line[30:38]), float(line[38:46]), float(line[46:54])]
            )
    if not pts:
        raise SystemExit("no CA in extracted protein")
    return np.asarray(pts, float).mean(0)


def pca_axes(X: np.ndarray):
    Xc = X - X.mean(0)
    cov = Xc.T @ Xc / max(len(X) - 1, 1)
    _w, V = np.linalg.eigh(cov)
    V = V[:, ::-1]
    if np.linalg.det(V) < 0:
        V[:, -1] *= -1
    return X.mean(0), V


def heavy(mol):
    coords, z = [], []
    for atom in ob.OBMolAtomIter(mol):
        if atom.GetAtomicNum() == 1:
            continue
        coords.append([atom.GetX(), atom.GetY(), atom.GetZ()])
        z.append(atom.GetAtomicNum())
    return np.asarray(coords, float), z


def place_ligand_at(cid: str, target_com: np.ndarray, out_mol2: Path, ref_mol2: Path | None):
    sdf = Path(f"/tmp/pubchem_{cid}.sdf")
    download(
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d",
        sdf,
    )
    mol = next(pybel.readfile("sdf", str(sdf)))
    mol.OBMol.AddHydrogens()
    P, eP = heavy(mol.OBMol)
    # optional: align shape to previous lig_h if present
    if ref_mol2 and ref_mol2.is_file():
        try:
            ref = next(pybel.readfile("mol2", str(ref_mol2)))
            Q, eQ = heavy(ref.OBMol)
            if len(P) == len(Q):
                cp, Vp = pca_axes(Q)
                cr, Vr = pca_axes(P)
                best = None
                for sx in (1, -1):
                    for sy in (1, -1):
                        for sz in (1, -1):
                            R = Vr @ np.diag([sx, sy, sz]) @ Vp.T
                            if np.linalg.det(R) < 0:
                                continue
                            t = cp - cr @ R
                            X = P @ R + t
                            terms = []
                            for z in set(eP):
                                ip = [i for i, z0 in enumerate(eP) if z0 == z]
                                iq = [i for i, z0 in enumerate(eQ) if z0 == z]
                                cost = np.linalg.norm(
                                    X[ip][:, None, :] - Q[iq][None, :, :], axis=2
                                )
                                r, c = linear_sum_assignment(cost)
                                terms.extend(cost[a, b] ** 2 for a, b in zip(r, c))
                            rms = float(np.sqrt(np.mean(terms)))
                            if best is None or rms < best[0]:
                                best = (rms, R, t)
                if best:
                    R, t = best[1], best[2]
                    for atom in ob.OBMolAtomIter(mol.OBMol):
                        v = np.array([atom.GetX(), atom.GetY(), atom.GetZ()])
                        v2 = v @ R + t
                        atom.SetVector(float(v2[0]), float(v2[1]), float(v2[2]))
                    P, _ = heavy(mol.OBMol)
        except Exception:  # noqa: BLE001
            pass
    shift = target_com - P.mean(0)
    for atom in ob.OBMolAtomIter(mol.OBMol):
        atom.SetVector(
            atom.GetX() + float(shift[0]),
            atom.GetY() + float(shift[1]),
            atom.GetZ() + float(shift[2]),
        )
    mol.write("mol2", str(out_mol2), overwrite=True)
    lines = out_mol2.read_text().splitlines()
    if len(lines) >= 2:
        lines[1] = str(cid)
    out_mol2.write_text("\n".join(lines) + "\n")


def rebuild(system: str, src_dir: Path, out_dir: Path) -> int:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    meta = reg.get(system)
    if not meta:
        # infer from name GENE_ligand_PDB
        parts = system.split("_")
        meta = {
            "gene": parts[0],
            "uniprot": "",
            "ligand_cid": "",
            "failed_pdb": parts[-1] if parts else "",
            "prefer_chain": "A",
            "ligand_name_zh": parts[1] if len(parts) > 1 else "",
        }
    report = {
        "system": system,
        "source_dir": str(src_dir),
        "auto_rebuild_attempted": True,
        "auto_rebuild_ok": False,
        "pose_class": None,
        "chosen_pdb": None,
        "reason_zh": "",
        "candidates": [],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    uniprot = meta.get("uniprot") or ""
    cid = str(meta.get("ligand_cid") or "")
    chain = meta.get("prefer_chain") or "A"
    failed = (meta.get("failed_pdb") or "").upper()
    if not uniprot:
        report["reason_zh"] = "登记表缺少 UniProt，无法自动检索共晶/近缘结构。"
        (out_dir / "rebuild_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(report["reason_zh"])
        return 2
    if not cid:
        report["reason_zh"] = "登记表缺少配体 PubChem CID，无法重搭配体坐标。"
        (out_dir / "rebuild_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(report["reason_zh"])
        return 2

    ids = [i for i in search_pdb_ids(uniprot) if i.upper() != failed]
    report["candidates"] = ids[:15]
    best = None
    cache = Path("/tmp/md_pose_retry_pdb")
    cache.mkdir(exist_ok=True)
    for pdb_id in ids[:15]:
        pdb_path = cache / f"{pdb_id}.pdb"
        if not pdb_path.is_file():
            try:
                download(f"https://files.rcsb.org/download/{pdb_id}.pdb", pdb_path)
            except Exception as exc:  # noqa: BLE001
                report.setdefault("download_errors", []).append(f"{pdb_id}:{exc}")
                continue
        text = pdb_path.read_text(errors="replace")
        prot_chains = list_protein_chains(text)
        if not prot_chains:
            continue  # DNA/RNA-only or empty — skip
        use_chain = chain if _chain_ca_count(text, chain) > 0 else prot_chains[0][0]
        segs = gaps_from_pdb_text(text)
        gap_len = max_gap_len(segs, use_chain)
        if gap_len >= GAP_EXCLUDE_LEN:
            continue
        em = entry_meta(pdb_id)
        resol = None
        try:
            resol = (em.get("rcsb_entry_info") or {}).get("resolution_combined")
            if isinstance(resol, list):
                resol = resol[0] if resol else None
        except Exception:  # noqa: BLE001
            resol = None
        het = largest_het_com(text, use_chain)
        n_ca = _chain_ca_count(text, use_chain)
        score = (
            0 if het else 1,
            resol if resol is not None else 99.0,
            gap_len,
            -n_ca,  # prefer longer protein chain when tied
            pdb_id,
        )
        cand = {
            "pdb": pdb_id,
            "gap_max": gap_len,
            "resolution": resol,
            "has_het": bool(het),
            "het_res": het[1] if het else None,
            "use_chain": use_chain,
            "n_ca": n_ca,
            "score": score,
        }
        if best is None or score < best["score"]:
            best = {**cand, "text": text, "het": het}

    if best is None:
        report["reason_zh"] = (
            f"UniProt {uniprot} 下未找到含蛋白主链（CA）且通过缺口门禁"
            f"（连续缺失<{GAP_EXCLUDE_LEN}）的替代 PDB。"
        )
        (out_dir / "rebuild_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(report["reason_zh"])
        return 2

    prot = extract_chain_atoms(best["text"], best.get("use_chain") or chain)
    if not prot.strip() or _chain_ca_count(prot, best.get("use_chain") or chain) == 0:
        # extract_chain_atoms may remap chain; verify CA on whole text
        try:
            protein_ca_com(prot)
        except SystemExit:
            report["reason_zh"] = (
                f"替代结构 {best['pdb']} 提取结果无蛋白 CA（可能是核酸链）。"
            )
            (out_dir / "rebuild_report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return 2
    (out_dir / "protein.pdb").write_text(prot, encoding="utf-8")

    if best["het"] is not None:
        target_com = best["het"][0]
        pose_class = "A2"
        note = (
            f"近缘/口袋配体参照 {best['het'][1]}@{best['pdb']} "
            f"链{best.get('use_chain') or chain}"
        )
    else:
        target_com = protein_ca_com(prot)
        pose_class = "A2"
        note = (
            f"无共晶小分子，配体放到蛋白 CA 质心附近（弱初态）"
            f"@{best['pdb']} 链{best.get('use_chain') or chain}"
        )

    ref_lig = src_dir / "lig_h.mol2"
    place_ligand_at(cid, np.asarray(target_com, float), out_dir / "lig_h.mol2", ref_lig)
    (out_dir / "pose_class.txt").write_text(pose_class + "\n", encoding="utf-8")
    (out_dir / "RETRY_FROM.txt").write_text(
        f"from={system}\nfailed_pdb={failed}\nchosen_pdb={best['pdb']}\n"
        f"pose_class={pose_class}\nnote={note}\n",
        encoding="utf-8",
    )
    report.update(
        {
            "auto_rebuild_ok": True,
            "pose_class": pose_class,
            "chosen_pdb": best["pdb"],
            "resolution": best["resolution"],
            "gap_max": best["gap_max"],
            "note": note,
            "reason_zh": (
                f"已自动重搭：排除原结构 {failed or '原对接初态'}，改用 {best['pdb']} "
                f"（最大连续缺环 {best['gap_max']}，分辨率 {best['resolution']}）。{note}。"
            ),
        }
    )
    # drop huge text
    (out_dir / "rebuild_report.json").write_text(
        json.dumps({k: v for k, v in report.items() if k != "text"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(report["reason_zh"])
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 4:
        print(
            "usage: rebuildPoseRetry.py SYSTEM_NAME SRC_DIR OUT_DIR",
            file=sys.stderr,
        )
        return 2
    return rebuild(argv[1], Path(argv[2]), Path(argv[3]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
