#!/usr/bin/env bash
# build_cyp_heme_topology.sh WORK_DIR
# Shahrokh IC6：tleap 建 HEM+CYP(Fe–S)+蛋白+配体（干体系）→ ParmEd 转 GROMACS → heme_ready.flag
# 溶剂化/离子交给运行复合物MD_runComplexMd.sh（与 MMP9/ADA 一致，0.15 M NaCl）
set -euo pipefail
WORK=${1:?WORK_DIR}
source ~/activate-md.sh
export PATH="${HOME}/miniconda3/envs/md-tools/bin:${HOME}/md-venv/bin:${HOME}/gromacs-gpu/bin:${PATH}"
HEME_DIR="/mnt/e/md_kit/heme_params_shahrokh/heme_params/IC6"
cd "$WORK"

command -v tleap >/dev/null || { echo "FAIL: tleap missing"; exit 1; }
command -v parmed >/dev/null || { echo "FAIL: parmed missing"; exit 1; }
[[ -f "$HEME_DIR/IC6.frcmod" && -f protein.pdb && -f lig_h.mol2 && -f cofactors_HEM.pdb ]] || {
  echo "FAIL: need protein.pdb lig_h.mol2 cofactors_HEM.pdb + Shahrokh IC6"; exit 1
}

cp -f "$HEME_DIR/HEM.mol2" "$HEME_DIR/CYP.mol2" "$HEME_DIR/IC6.frcmod" .

# 配体 GAFF2（对接姿态偶发 <0.5 Å，须 -f；tleap 优先用 NEW.mol2）
if [[ ! -f ligand.acpype/ligand_GMX.itp ]]; then
  cp -f lig_h.mol2 acpype_tmp.mol2
  # -f：允许过近原子（吲哚对接构象常见），否则 acpype 直接 Abort
  if ! acpype -i acpype_tmp.mol2 -n 0 -a gaff2 -o gmx -b ligand -f > acpype_cyp.log 2>&1; then
    echo "FAIL: acpype ligand (see acpype_cyp.log)"
    tail -n 40 acpype_cyp.log
    exit 1
  fi
  rm -f acpype_tmp.mol2
fi
# acpype 产出 GAFF2 类型 mol2（勿用原始 Sybyl C.ar，tleap 不认）
LIG_MOL2=""
for cand in ligand.acpype/ligand_bcc_gaff2.mol2 ligand.acpype/ligand_NEW.mol2 ligand.acpype/ligand_AC.mol2; do
  if [[ -f "$cand" ]]; then LIG_MOL2="$cand"; break; fi
done
[[ -n "$LIG_MOL2" ]] || { echo "FAIL: no GAFF mol2 from acpype"; exit 1; }
LIG_FRCMOD=""
if [[ -f ligand.acpype/ligand_AC.frcmod ]]; then LIG_FRCMOD=ligand.acpype/ligand_AC.frcmod; fi
python3 - "$LIG_MOL2" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
lines = p.read_text(errors="replace").splitlines()
if len(lines) >= 2:
    lines[1] = "LIG"
p.write_text("\n".join(lines) + "\n")
print("lig mol2 (GAFF) ->", p)
PY

# 蛋白 ATOM + HEM；轴向 Cys → CYP
python3 - <<'PY'
from pathlib import Path
work = Path(".")
prot = [ln for ln in work.joinpath("protein.pdb").read_text(errors="replace").splitlines()
        if ln.startswith(("ATOM", "TER"))]
hem = [ln for ln in work.joinpath("cofactors_HEM.pdb").read_text(errors="replace").splitlines()
       if ln.startswith(("HETATM", "ATOM"))]
fe = None
for ln in hem:
    an = ln[12:16].strip().upper()
    if an in ("FE", "FE1") or (len(ln) > 77 and ln[76:78].strip().upper() == "FE"):
        fe = (float(ln[30:38]), float(ln[38:46]), float(ln[46:54]))
        break
if fe is None:
    raise SystemExit("no FE in cofactors_HEM.pdb")

def dist(ln):
    return ((float(ln[30:38]) - fe[0]) ** 2 + (float(ln[38:46]) - fe[1]) ** 2 + (float(ln[46:54]) - fe[2]) ** 2) ** 0.5

cys_sg = []
for ln in prot:
    if not ln.startswith("ATOM"):
        continue
    if ln[17:20].strip() == "CYS" and ln[12:16].strip() in ("SG", "S"):
        cys_sg.append((dist(ln), ln))
cys_sg.sort()
if not cys_sg or cys_sg[0][0] > 3.5:
    raise SystemExit(f"no axial Cys SG near FE (best={cys_sg[0][0] if cys_sg else None})")
target = cys_sg[0][1]
resseq = target[22:26]
chain = target[21]
out = []
for ln in prot:
    if ln.startswith("ATOM") and ln[21] == chain and ln[22:26] == resseq and ln[17:20].strip() == "CYS":
        ln = ln[:17] + "CYP" + ln[20:]
    out.append(ln)
for ln in hem:
    if ln.startswith("HETATM"):
        ln = "ATOM  " + ln[6:]
    out.append(ln)
out.append("END")
work.joinpath("protein_heme_cyp.pdb").write_text("\n".join(out) + "\n")
print(f"axial CYP resseq={resseq.strip()} chain={chain} Fe-SG={cys_sg[0][0]:.2f} A")
PY

# 干体系：蛋白+HEM+CYP + combine 配体；溶剂化留给 GROMACS
cat > leap_cyp.in <<EOF
source leaprc.protein.ff14SB
source leaprc.gaff2
loadamberparams IC6.frcmod
EOF
if [[ -n "$LIG_FRCMOD" ]]; then
  echo "loadamberparams ${LIG_FRCMOD}" >> leap_cyp.in
fi
cat >> leap_cyp.in <<EOF
HEM = loadmol2 HEM.mol2
CYP = loadmol2 CYP.mol2
LIG = loadmol2 ${LIG_MOL2}
set LIG name "LIG"
mol = loadpdb protein_heme_cyp.pdb
bond mol.CYP.SG mol.HEM.FE
savepdb mol check_heme.pdb
mol = combine { mol LIG }
charge mol
check mol
saveamberparm mol cyp_complex.prmtop cyp_complex.inpcrd
savepdb mol cyp_complex_dry.pdb
quit
EOF

tleap -f leap_cyp.in > tleap_cyp.log 2>&1 || {
  echo "tleap failed; see tleap_cyp.log"
  tail -n 60 tleap_cyp.log
  exit 1
}

[[ -f cyp_complex.prmtop && -f cyp_complex.inpcrd ]] || {
  echo "no prmtop"; tail -n 40 tleap_cyp.log; exit 1
}

# ParmEd 4.x：CLI `gromacs write` 已废弃 → Python API + editconf
python3 - <<'PY' > parmed_cyp.log 2>&1
import parmed as pmd
from pathlib import Path
parm = pmd.load_file("cyp_complex.prmtop", "cyp_complex.inpcrd")
gtop = pmd.gromacs.GromacsTopologyFile.from_structure(parm)
gtop.write("topol_heme.top")
parm.save("cyp_complex_for_gro.pdb", overwrite=True)
print("top+pdb ok", len(parm.atoms))
PY
gmx editconf -f cyp_complex_for_gro.pdb -o complex_heme.gro > editconf_heme.log 2>&1 || {
  echo "editconf failed"; tail -n 20 editconf_heme.log; exit 1
}
# acpype/Amber 配体残基名常为 UNL → 统一 LIG
python3 - <<'PY'
from pathlib import Path
p = Path("topol_heme.top")
t = p.read_text(errors="replace")
n = t.count("UNL")
if n:
    p.write_text(t.replace("UNL", "LIG"))
    print(f"renamed UNL->LIG ({n} hits)")
PY

[[ -s topol_heme.top && -s complex_heme.gro ]] || {
  echo "parmed/gmx convert failed"; tail -n 40 parmed_cyp.log; exit 1
}

echo "---- [ molecules ] ----"
awk '/\[ *molecules *\]/{p=1;print;next} p&&/^\[/{exit} p{print}' topol_heme.top || true

echo "ok $(date -Iseconds)" > heme_ready.flag
echo "HEME_TOPOLOGY_READY"
ls -la heme_ready.flag complex_heme.gro topol_heme.top cyp_complex.prmtop
