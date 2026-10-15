#!/usr/bin/env python3
"""ESR2 lig_h.mol2 手术：剔除零键幽灵原子，保留成键骨架坐标，再由 obabel 补氢。"""
import re
import subprocess
import sys

SRC = "/mnt/e/RProject/努力学习项目/08_分子动力学/数据文件/原始数据/RCSB与对接姿态_MD输入_Top3/ESR2_Anhydroicaritin_1L2J/lig_h.mol2"
CORE = "/home/ywy/esr2_core.mol2"
FIXED = "/home/ywy/esr2_lig_fixed.mol2"

txt = open(SRC).read()
parts = re.split(r"(@<TRIPOS>\w+)", txt)
blocks = {}
i = 1
while i < len(parts):
    blocks[parts[i].replace("@<TRIPOS>", "").strip()] = parts[i + 1]
    i += 2

atom_lines = [l for l in blocks["ATOM"].splitlines() if l.strip()]
bond_lines = [l for l in blocks["BOND"].splitlines() if l.strip() and l.split()[1].isdigit()]

deg = {}
for l in atom_lines:
    deg[int(l.split()[0])] = 0
bonds = []
for l in bond_lines:
    p = l.split()
    a, b, tp = int(p[1]), int(p[2]), p[3]
    deg[a] += 1
    deg[b] += 1
    bonds.append((a, b, tp))

dropped = [i for i in sorted(deg) if deg[i] == 0]
keep_ids = [i for i in sorted(deg) if deg[i] > 0]
print("keep atoms:", len(keep_ids), "drop(zero-bond):", dropped)
remap = {old: new for new, old in enumerate(keep_ids, 1)}

out_atoms = []
for l in atom_lines:
    p = l.split()
    if int(p[0]) not in remap:
        continue
    chg = p[8] if len(p) > 8 else "0.0000"
    out_atoms.append(
        f"{remap[int(p[0])]:>7d} {p[1]:<8s} {p[2]:>10s} {p[3]:>10s} {p[4]:>10s} {p[5]:<6s} {p[6]:>3s} {p[7]:<6s} {chg:>10s}"
    )
out_bonds = []
for n, (a, b, tp) in enumerate(bonds, 1):
    if a in remap and b in remap:
        out_bonds.append(f"{n:>6d} {remap[a]:>5d} {remap[b]:>5d} {tp}")

name = (blocks["MOLECULE"].splitlines() or ["LIG"])[0].strip() or "LIG"
with open(CORE, "w") as f:
    f.write("@<TRIPOS>MOLECULE\n")
    f.write(f"{name}\n {len(out_atoms)} {len(out_bonds)} 1 0 0\nSMALL\nUSER_CHARGES\n\n")
    f.write("@<TRIPOS>ATOM\n" + "\n".join(out_atoms) + "\n")
    f.write("@<TRIPOS>BOND\n" + "\n".join(out_bonds) + "\n")
print("wrote core:", len(out_atoms), "atoms", len(out_bonds), "bonds")

r = subprocess.run(["obabel", CORE, "-O", FIXED, "-h"], capture_output=True, text=True)
print(r.stderr.strip().splitlines()[-1] if r.stderr else "obabel ok")

t = open(FIXED).read()
a = re.search(r"@<TRIPOS>ATOM(.*?)@<TRIPOS>BOND", t, re.S).group(1).splitlines()
b = [l for l in re.search(r"@<TRIPOS>BOND(.*)", t, re.S).group(1).splitlines()
     if l.strip() and l.split()[1].isdigit()]
els = {}
for l in a:
    if l.strip():
        e = l.split()[5].split(".")[0]
        els[e] = els.get(e, 0) + 1
print("fixed mol2: atoms", len([x for x in a if x.strip()]), "bonds", len(b), "elements", els)

# 连通性终检
deg2 = {}
for l in a:
    if l.strip():
        deg2[int(l.split()[0])] = 0
for l in b:
    p = l.split()
    deg2[int(p[1])] += 1
    deg2[int(p[2])] += 1
zeros = [i for i, d in deg2.items() if d == 0]
print("zero-bond atoms in fixed:", zeros)
sys.exit(1 if zeros else 0)
