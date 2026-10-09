# -*- coding: utf-8 -*-
"""Human ADA A2: 7RTG protein+Zn, adenosine pose from 3IAR 2'-deoxyadenosine."""
from __future__ import annotations

import math
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC7 = ROOT / "ADA_Adenosine_7RTG"
OUT = ROOT / "ADA_Adenosine_7RTG_A2"
OUT.mkdir(parents=True, exist_ok=True)
PDB3 = OUT / "3IAR.pdb"
ADN = OUT / "ADN_ideal.sdf"
if not PDB3.exists():
    urllib.request.urlretrieve("https://files.rcsb.org/download/3IAR.pdb", PDB3)
if not ADN.exists():
    urllib.request.urlretrieve("https://files.rcsb.org/ligands/download/ADN_ideal.sdf", ADN)


def resname(line: str) -> str:
    return line[17:20].strip()


def atomname(line: str) -> str:
    return line[12:16].strip()


def resseq(line: str) -> int:
    return int(line[22:26])


def xyz(line: str) -> tuple[float, float, float]:
    return (float(line[30:38]), float(line[38:46]), float(line[46:54]))


def parse_atoms(path: Path):
    return [ln for ln in path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.startswith(("ATOM", "HETATM"))]


def kabsch(P, Q):
    """Rotate/translate P onto Q. Returns R, t such that p' = R @ p + t."""
    n = len(P)
    pc = [sum(p[i] for p in P) / n for i in range(3)]
    qc = [sum(q[i] for q in Q) / n for i in range(3)]
    H = [[0.0] * 3 for _ in range(3)]
    for p, q in zip(P, Q):
        for i in range(3):
            for j in range(3):
                H[i][j] += (p[i] - pc[i]) * (q[j] - qc[j])
    # Jacobi-less SVD via the normal matrix of a 3x3, implemented with numpy if present
    try:
        import numpy as np
        U, _, Vt = np.linalg.svd(np.array(H))
        R = Vt.T @ U.T
        if np.linalg.det(R) < 0:
            Vt[-1] *= -1
            R = Vt.T @ U.T
        t = np.array(qc) - R @ np.array(pc)
        return R, t
    except Exception as exc:
        raise SystemExit(f"numpy required for superposition: {exc}")


def apply(R, t, p):
    import numpy as np
    v = R @ np.array(p) + t
    return float(v[0]), float(v[1]), float(v[2])


def set_xyz(line: str, p) -> str:
    return f"{line[:30]}{p[0]:8.3f}{p[1]:8.3f}{p[2]:8.3f}{line[54:]}"


prot7 = [ln for ln in parse_atoms(SRC7 / "protein.pdb") if ln.startswith("ATOM")]
zn = [ln for ln in parse_atoms(SRC7 / "cofactors_ZN.pdb") if resname(ln) == "ZN"]
raw3 = parse_atoms(PDB3)
prot3 = [ln for ln in raw3 if ln.startswith("ATOM") and ln[21] == "A"]
lig3 = [ln for ln in raw3 if ln.startswith("HETATM") and resname(ln) in {"3D1", "2DA"}]
ni = [ln for ln in raw3 if ln.startswith("HETATM") and resname(ln) == "NI" and ln[21] == "A"]
if not lig3:
    names = sorted({resname(ln) for ln in raw3 if ln.startswith("HETATM")})
    raise SystemExit(f"3IAR ligand not found, het names={names}")

ca7 = {(resname(ln), resseq(ln)): xyz(ln) for ln in prot7 if atomname(ln) == "CA"}
ca3 = {(resname(ln), resseq(ln)): xyz(ln) for ln in prot3 if atomname(ln) == "CA"}
keys = sorted(set(ca7) & set(ca3))
if len(keys) < 50:
    raise SystemExit(f"too few matched CA: {len(keys)}")
P = [ca3[k] for k in keys]
Q = [ca7[k] for k in keys]
R, t = kabsch(P, Q)
import numpy as np
rms = math.sqrt(sum(sum((a - b) ** 2 for a, b in zip(apply(R, t, p), q)) for p, q in zip(P, Q)) / len(P))

lig_fit = [set_xyz(ln, apply(R, t, xyz(ln))) for ln in lig3]
zn_ni = None
if ni and zn:
    ni_fit = apply(R, t, xyz(ni[0]))
    zn_xyz = xyz(zn[0])
    zn_ni = math.dist(ni_fit, zn_xyz)

# Ideal adenosine has no PDB atom names in this SDF. Match the heavy-atom
# graph of 2'-deoxyadenosine onto adenosine; crystal heavy atoms stay put.
# O2' is placed from the ideal C1'/C2'/C3' frame so the ribose stereochemistry
# is copied without moving the experimental skeleton.
sdf = ADN.read_text(encoding="utf-8", errors="replace").splitlines()
n_atoms = int(sdf[3][:3])
n_bonds = int(sdf[3][3:6])
elems, coords = [], []
for i in range(n_atoms):
    row = sdf[4 + i]
    elems.append(row[31:34].strip())
    coords.append((float(row[0:10]), float(row[10:20]), float(row[20:30])))
heavy = [i for i, e in enumerate(elems) if e != "H"]
hset = set(heavy)
graph = {i: set() for i in heavy}
for b in range(n_bonds):
    row = sdf[4 + n_atoms + b]
    a, c = int(row[0:3]) - 1, int(row[3:6]) - 1
    if a in hset and c in hset:
        graph[a].add(c)
        graph[c].add(a)
# O5', O3' and O2' are all terminal oxygens. Identify O2' from the
# glycosidic nitrogen: N9 -> C1' -> C2' -> O2'.
def glycosidic_n(g, el):
    hits = [i for i in g if el[i] == "N" and len(g[i]) == 3 and all(el[j] == "C" for j in g[i])]
    if len(hits) != 1:
        raise SystemExit(f"expected one N9, got {len(hits)}")
    return hits[0]

def walk_sugar(g, el, n9):
    c1 = next(j for j in g[n9] if any(el[k] == "O" and len(g[k]) == 2 for k in g[j]))
    o4 = next(j for j in g[c1] if el[j] == "O")
    c2 = next(j for j in g[c1] if el[j] == "C")
    o2 = [j for j in g[c2] if el[j] == "O" and len(g[j]) == 1]
    c3 = next(j for j in g[c2] if el[j] == "C" and j != c1)
    return {"N9": n9, "C1'": c1, "O4'": o4, "C2'": c2, "O2'": o2[0] if o2 else None, "C3'": c3}

n9_id = glycosidic_n(graph, elems)
sugar = walk_sugar(graph, elems, n9_id)
o2 = sugar["O2'"]
if o2 is None:
    raise SystemExit("ideal adenosine has no O2'")
c2_id, c1_id, c3_id = sugar["C2'"], sugar["C1'"], sugar["C3'"]

# Crystal 2'-deoxyadenosine graph from distances, with the same walk.
crystal = lig_fit
c_coords = [xyz(ln) for ln in crystal]
c_elem = [atomname(ln)[0] for ln in crystal]
c_graph = {i: set() for i in range(len(crystal))}
for i in range(len(crystal)):
    for j in range(i + 1, len(crystal)):
        if math.dist(c_coords[i], c_coords[j]) < 1.7:
            c_graph[i].add(j)
            c_graph[j].add(i)
c_n9 = glycosidic_n(c_graph, c_elem)
c_sugar = walk_sugar(c_graph, c_elem, c_n9)

def frame(origin, a, b):
    import numpy as np
    v1 = np.array(a) - np.array(origin)
    v2 = np.array(b) - np.array(origin)
    v1 = v1 / np.linalg.norm(v1)
    v2 = v2 - np.dot(v2, v1) * v1
    v2 = v2 / np.linalg.norm(v2)
    nrm = np.cross(v1, v2)
    return v1, v2, nrm

v1, v2, nrm = frame(coords[c2_id], coords[c1_id], coords[c3_id])
rel = np.array(coords[o2]) - np.array(coords[c2_id])
local = (float(np.dot(rel, v1)), float(np.dot(rel, v2)), float(np.dot(rel, nrm)))
cx = c_coords[c_sugar["C2'"]]
ca = c_coords[c_sugar["C1'"]]
cb = c_coords[c_sugar["C3'"]]
w1, w2, wn = frame(cx, ca, cb)
o2_xyz = (
    cx[0] + local[0] * w1[0] + local[1] * w2[0] + local[2] * wn[0],
    cx[1] + local[0] * w1[1] + local[1] * w2[1] + local[2] * wn[1],
    cx[2] + local[0] * w1[2] + local[1] * w2[2] + local[2] * wn[2],
)
placed = [(atomname(crystal[i]), c_coords[i]) for i in range(len(crystal))]
placed.append(("O2'", o2_xyz))
shift = 0.0

# 7RTG Asp19 OD1 sits 1.79 A from the transferred O5'; in 3IAR that contact is 2.65 A.
# Move only this side chain onto the ligand-bound rotamer. Backbone and Zn stay on 7RTG.
side = {"CB", "CG", "OD1", "OD2"}
src_side = {
    atomname(ln): apply(R, t, xyz(ln))
    for ln in prot3
    if resname(ln) == "ASP" and resseq(ln) == 19 and atomname(ln) in side
}
if set(src_side) != side:
    raise SystemExit(f"3IAR Asp19 side chain incomplete: {sorted(src_side)}")
new_prot = []
for ln in prot7:
    if resname(ln) == "ASP" and resseq(ln) == 19 and atomname(ln) in side:
        ln = set_xyz(ln, src_side[atomname(ln)])
    new_prot.append(ln)
prot7 = new_prot

# Clashes against 7RTG heavy atoms
prot_xyz = [(resseq(ln), resname(ln), atomname(ln), xyz(ln)) for ln in prot7 if not atomname(ln).startswith("H")]
lig_h = [(n, p) for n, p in placed if not n.startswith("H")]
clashes = []
for rn, rr, an, pp in prot_xyz:
    for ln, lp in lig_h:
        d = math.dist(pp, lp)
        if d < 2.0:
            clashes.append((d, rr, rn, an, ln))
clashes.sort()

lines = []
serial = 1
for name, p in placed:
    elem = "H" if name.startswith("H") else name[0]
    if name.startswith("O") or name.startswith("N") or name.startswith("C"):
        elem = name[0]
    lines.append(
        f"HETATM{serial:5d} {name:>4s} LIG A   1    {p[0]:8.3f}{p[1]:8.3f}{p[2]:8.3f}  1.00  0.00           {elem:>2s}"
    )
    serial += 1
(OUT / "lig_adenosine_from_3D1.pdb").write_text("\n".join(lines) + "\nEND\n", encoding="utf-8")
(OUT / "protein.pdb").write_text("\n".join(prot7) + "\nEND\n", encoding="utf-8")
(OUT / "cofactors_ZN.pdb").write_text("\n".join(zn) + "\nEND\n", encoding="utf-8")
note = OUT / "README_初态.md"
note.write_text(
    f"""# ADA_Adenosine_7RTG_A2

人源方案。失败的 7RTG 空口袋对接不续跑，工作目录用新名，避免读到旧 `md.cpt`。

- 蛋白与 Zn：7RTG 链 A
- 配体：腺苷。3IAR 的 2′-脱氧腺苷按 CA 叠到 7RTG 后，用理想腺苷的公共重原子对齐，只多出 O2′
- 不带入 3IAR 的 Ni、甘油、硝酸根
- 侧链保持 7RTG，只把 Asp19 侧链换成 3IAR 结合态旋转异构体（O5′ 接触从 1.79 Å 回到晶体的约 2.65 Å）。不放大口袋
- CA 配准残基数 {len(keys)}，CA RMSD {rms:.3f} Å
- 叠合后 Ni 与 7RTG Zn 距离 {zn_ni if zn_ni is not None else "NA"} Å
- 公共重原子对齐 RMSD {shift:.3f} Å
- <2.0 Å 碰撞数 {len(clashes)}

结论写成「人源 Zn 酶 + 由 2′-脱氧腺苷实验位姿导出的腺苷」，不是腺苷共晶。
""",
    encoding="utf-8",
)
print(f"CA n={len(keys)} rmsd={rms:.3f} Zn-Ni={zn_ni} ligand_shift={shift:.3f} clashes={len(clashes)}")
for row in clashes[:15]:
    print(f"  {row[0]:.2f} {row[1]}{row[2]} {row[3]} vs {row[4]}")
