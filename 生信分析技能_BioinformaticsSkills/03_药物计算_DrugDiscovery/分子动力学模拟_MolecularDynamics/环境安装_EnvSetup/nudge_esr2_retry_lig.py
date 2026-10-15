#!/usr/bin/env python3
"""ESR2 retry 初态微调：配体沿逃离方向平移至 min 距离 0.055–0.12 nm（解 clash 0.038）。"""
import numpy as np
from pathlib import Path

SRC = Path("/mnt/e/RProject/努力学习项目/08_分子动力学/数据文件/原始数据/RCSB与对接姿态_MD输入_Top3/ESR2_Anhydroicaritin_1L2J_retry1")
prot = []
for l in (SRC / "protein.pdb").read_text().splitlines():
    if l.startswith("ATOM"):
        elem = l[76:78].strip() if len(l) >= 78 else ""
        name = l[12:16].strip()
        if elem == "H" or name.startswith("H"):
            continue
        prot.append([float(l[30:38]), float(l[38:46]), float(l[46:54])])
prot = np.array(prot)

mol2 = SRC / "lig_h.mol2"
lines = mol2.read_text().splitlines()
ia = lines.index("@<TRIPOS>ATOM")
ib = lines.index("@<TRIPOS>BOND")
head = lines[: ia + 1]
atom_lines = lines[ia + 1 : ib]
tail = lines[ib:]
pts, recs = [], []
for l in atom_lines:
    p = l.split()
    pts.append([float(p[2]), float(p[3]), float(p[4])])
    recs.append(p)
pts = np.array(pts)
heavy = np.array([not r[1].startswith("H") for r in recs])

def min_dist(P, Q):
    d = np.linalg.norm(P[:, None, :] - Q[None, :, :], axis=2)
    i, j = np.unravel_index(np.argmin(d), d.shape)
    return d[i, j], P[i]

lig_com = pts[heavy].mean(0)
d, nearest = min_dist(pts[heavy], prot)
print(f"initial min dist {d:.3f} A")  # 门禁：nm 下限 0.05 = 0.5 A
if d < 0.55:
    direction = lig_com - nearest
    direction = direction / (np.linalg.norm(direction) + 1e-9)
    shift = 0.0
    while d < 0.6 and shift < 2.0:
        shift += 0.05
        moved = pts[heavy] + direction * shift
        d, _ = min_dist(moved, prot)
    print(f"shifted {shift:.2f} A -> min dist {d:.3f} A")
    pts[heavy] += direction * shift
    pts[~heavy] += direction * shift
out_atoms = []
for p, r in zip(pts, recs):
    out_atoms.append(
        f"{int(r[0]):>7d} {r[1]:<8s} {p[0]:>10.4f} {p[1]:>10.4f} {p[2]:>10.4f} {r[5]:<6s} {r[6]:>3s} {r[7]:<6s} {r[8] if len(r) > 8 else '0.0000':>10s}"
    )
mol2.write_text("\n".join(head + out_atoms + tail) + "\n")
d2, _ = min_dist(pts[heavy], prot)
print(f"final min dist {d2:.3f} A -> {mol2}")
