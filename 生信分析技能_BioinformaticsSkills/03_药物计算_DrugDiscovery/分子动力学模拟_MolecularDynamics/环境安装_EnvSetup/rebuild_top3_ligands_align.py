#!/usr/bin/env python3
"""Rebuild lig_h.mol2: PubChem 3D + PCA/Hungarian align onto Vina MODEL1 pose."""
from __future__ import annotations

from pathlib import Path
import urllib.request

import numpy as np
from openbabel import openbabel as ob
from openbabel import pybel
from scipy.optimize import linear_sum_assignment

TOP3 = Path(
    "/mnt/e/RProject/努力学习项目/08_分子动力学/数据文件/原始数据/RCSB与对接姿态_MD输入_Top3"
)
JOBS = [
    ("ESR2_Anhydroicaritin_1L2J", "14583584"),
    ("FOS_quercetin_1A02", "5280343"),
    ("PPARG_kaempferol_1FM9", "5280863"),
]


def extract_model1_pdbqt(src: Path, dst: Path) -> None:
    lines, in_model, done = [], False, False
    for line in src.read_text().splitlines():
        if line.startswith("MODEL"):
            if in_model:
                break
            in_model = True
            lines.append(line)
            continue
        if not in_model:
            continue
        lines.append(line)
        if line.startswith("ENDMDL"):
            done = True
            break
    if not done:
        raise SystemExit(f"no MODEL1 in {src}")
    dst.write_text("\n".join(lines) + "\n")


def heavy(mol):
    coords, znums = [], []
    for atom in ob.OBMolAtomIter(mol):
        if atom.GetAtomicNum() == 1:
            continue
        coords.append([atom.GetX(), atom.GetY(), atom.GetZ()])
        znums.append(atom.GetAtomicNum())
    return np.asarray(coords, float), znums


def pca_axes(X: np.ndarray):
    Xc = X - X.mean(0)
    cov = Xc.T @ Xc / max(len(X) - 1, 1)
    _w, V = np.linalg.eigh(cov)
    V = V[:, ::-1]
    if np.linalg.det(V) < 0:
        V[:, -1] *= -1
    return X.mean(0), V


def rms_after(R, t, P, eP, Q, eQ) -> float:
    X = P @ R + t
    terms = []
    for z in set(eP):
        ip = [i for i, z0 in enumerate(eP) if z0 == z]
        iq = [i for i, z0 in enumerate(eQ) if z0 == z]
        cost = np.linalg.norm(X[ip][:, None, :] - Q[iq][None, :, :], axis=2)
        r, c = linear_sum_assignment(cost)
        terms.extend(cost[a, b] ** 2 for a, b in zip(r, c))
    return float(np.sqrt(np.mean(terms)))


def best_pca_align(P, eP, Q, eQ):
    cp, Vp = pca_axes(Q)
    cr, Vr = pca_axes(P)
    best = None
    for sx in (1, -1):
        for sy in (1, -1):
            for sz in (1, -1):
                S = np.diag([sx, sy, sz])
                R = Vr @ S @ Vp.T
                if np.linalg.det(R) < 0:
                    continue
                t = cp - cr @ R
                rms = rms_after(R, t, P, eP, Q, eQ)
                if best is None or rms < best[0]:
                    best = (rms, R, t)
    return best


def apply_rt(mol, R, t):
    for atom in ob.OBMolAtomIter(mol):
        v = np.array([atom.GetX(), atom.GetY(), atom.GetZ()])
        v2 = v @ R + t
        atom.SetVector(float(v2[0]), float(v2[1]), float(v2[2]))


def fetch_sdf(cid: str, out: Path):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d"
    urllib.request.urlretrieve(url, out)


def rebuild(sysname: str, cid: str):
    d = TOP3 / sysname
    pose_multi = d / "pose_best.pdbqt"
    lig = d / "lig_h.mol2"
    bak = d / "lig_h.mol2.bak_badgeom"
    if lig.exists() and not bak.exists():
        bak.write_bytes(lig.read_bytes())

    m1 = Path(f"/tmp/{sysname}_m1.pdbqt")
    extract_model1_pdbqt(pose_multi, m1)
    pose = next(pybel.readfile("pdbqt", str(m1)))
    Q, eQ = heavy(pose.OBMol)

    sdf = Path(f"/tmp/pubchem_{cid}.sdf")
    fetch_sdf(cid, sdf)
    ref = next(pybel.readfile("sdf", str(sdf)))
    ref.OBMol.AddHydrogens()
    P, eP = heavy(ref.OBMol)
    if len(P) != len(Q):
        raise SystemExit(f"{sysname}: heavy {len(P)} vs pose {len(Q)}")

    rms, R, t = best_pca_align(P, eP, Q, eQ)
    apply_rt(ref.OBMol, R, t)
    ref.write("mol2", str(lig), overwrite=True)
    lines = lig.read_text().splitlines()
    if len(lines) >= 2:
        lines[1] = cid
    lig.write_text("\n".join(lines) + "\n")
    print(f"OK {sysname} cid={cid} heavy={len(Q)} align_rmsd={rms:.3f} A -> {lig}")
    if rms > 1.5:
        raise SystemExit(f"{sysname}: align RMSD too high ({rms:.3f})")


def main():
    for name, cid in JOBS:
        rebuild(name, cid)


if __name__ == "__main__":
    main()
