# -*- coding: utf-8 -*-
"""Build mouse ADA A2 inputs from PDB 1ADD. Do not enlarge the pocket."""
from __future__ import annotations

import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / "ADA_Adenosine_1ADD"
OUT.mkdir(parents=True, exist_ok=True)
raw = OUT / "1ADD.pdb"
if not raw.exists() or raw.stat().st_size < 1000:
    urllib.request.urlretrieve("https://files.rcsb.org/download/1ADD.pdb", raw)

text = raw.read_text(encoding="utf-8", errors="replace").splitlines()


def resname(line: str) -> str:
    return line[17:20].strip()


def atomname(line: str) -> str:
    return line[12:16].strip()


def xyz(line: str) -> tuple[float, float, float]:
    return float(line[30:38]), float(line[38:46]), float(line[46:54])


protein, zinc, lig = [], [], []
for line in text:
    if line.startswith("ATOM") and line[21] == "A" and resname(line) not in {"HOH"}:
        protein.append(line)
    elif line.startswith("HETATM") and resname(line) == "ZN":
        zinc.append(line)
    elif line.startswith("HETATM") and resname(line) == "1DA":
        lig.append(line)

if not protein or not zinc or not lig:
    raise SystemExit(f"parse failed prot={len(protein)} zn={len(zinc)} lig={len(lig)}")

# C1 of 1-deazaadenosine is the atom that is N1 in adenosine. Keep coordinates.
aden = []
for line in lig:
    if atomname(line) == "C1":
        # atom name N1, element N; residue LIG
        line = line[:12] + " N1 " + line[16:17] + "LIG" + line[20:]
        if len(line) >= 78:
            line = line[:76] + " N" + line[78:]
        else:
            line = line.rstrip() + "           N"
    else:
        line = line[:17] + "LIG" + line[20:]
    aden.append(line)

(OUT / "protein.pdb").write_text("\n".join(protein) + "\nEND\n", encoding="utf-8")
(OUT / "cofactors_ZN.pdb").write_text("\n".join(zinc) + "\nEND\n", encoding="utf-8")
(OUT / "lig_adenosine_from_1DA.pdb").write_text("\n".join(aden) + "\nEND\n", encoding="utf-8")

# nearest crystal water to Zn, for the note (not written into the complex)
waters = [l for l in text if l.startswith("HETATM") and resname(l) == "HOH"]
zn = xyz(zinc[0])
c6 = xyz(next(l for l in lig if atomname(l) == "C6"))

def dist(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** 0.5

near = sorted((dist(xyz(w), zn), dist(xyz(w), c6)) for w in waters)[:3]
(OUT / "README_初态.md").write_text(
    """# ADA_Adenosine_1ADD

场景 A2。失败的人源 7RTG 对接初态不续跑。

- 受体：鼠源 ADA，PDB 1ADD 链 A，2.40 Å
- 金属：该晶体的 Zn，坐标不改
- 配体：腺苷。1-脱氮腺苷的 C1 改为 N1，其余重原子坐标不变
- 侧链：保持 1ADD 结合态，不放大口袋
- 水：全部去掉。离 Zn 最近的晶体水会指向 C6，换成腺苷 6-氨基后重叠

结论写成「鼠源 1-脱氮腺苷实验位姿导出的腺苷」，不是腺苷共晶。
"""
    + f"\n最近 3 个水到 Zn / C6 的距离（Å）：{near}\n",
    encoding="utf-8",
)
print(f"protein {len(protein)} zinc {len(zinc)} lig {len(aden)}")
print("nearest waters Zn/C6", near)
