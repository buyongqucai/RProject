#!/usr/bin/env bash
# Pre-genion + launch CYP1A1 100 ns (ASCII-only paths for WSL/PowerShell)
set -euo pipefail
source ~/activate-md.sh
export PATH="${HOME}/md-venv/bin:${HOME}/gromacs-gpu/bin:${HOME}/miniconda3/envs/md-tools/bin:${PATH}"
export GMX_MAXBACKUP="${GMX_MAXBACKUP:-5}"

WORK="${HOME}/md_runs/CYP1A1_Indole_4I8V"
MDP="${HOME}/md_runs/mdp_templates"
RUN_SH="/mnt/e/md_kit/runComplexMd.sh"
LOG="${HOME}/md_runs/logs/CYP1A1_Indole_4I8V.log"
mkdir -p "$(dirname "$LOG")" "$MDP"

# Ensure mdp templates exist (ASCII path)
if [[ ! -f "$MDP/ions.mdp" ]]; then
  python3 - <<'PY'
from pathlib import Path
import shutil
dst = Path.home() / "md_runs" / "mdp_templates"
dst.mkdir(parents=True, exist_ok=True)
found = None
for r in [Path("/mnt/e/RProject"), Path("/mnt/e/md_kit")]:
    if not r.exists():
        continue
    for p in r.rglob("ions.mdp"):
        found = p.parent
        break
    if found:
        break
if not found:
    raise SystemExit("ions.mdp not found")
for f in found.iterdir():
    if f.suffix == ".mdp":
        shutil.copy2(f, dst / f.name)
print("mdp from", found)
PY
fi

cd "$WORK"
[[ -f complex.gro ]] || cp -f complex_heme.gro complex.gro
[[ -f topol.top ]] || cp -f topol_heme.top topol.top

# Ensure tip3p SOL + OW/HW + ions in ParmEd-style topol
python3 - <<'PY'
from pathlib import Path
import re
p = Path("topol.top")
raw = p.read_text(errors="replace").replace("UNL", "LIG")
nsol = sum(
    1 for ln in Path("solv.gro").read_text().splitlines()[2:-1]
    if len(ln) >= 10 and ln[5:10].strip() == "SOL"
) // 3
extras = []
sec = raw.split("[ atomtypes ]", 1)[1].split("[", 1)[0] if "[ atomtypes ]" in raw else ""
at = {
    "OW": "OW           8   16.00000  0.0000  A   3.15061e-01  6.36386e-01",
    "HW": "HW           1    1.00800  0.0000  A   0.00000e+00  0.00000e+00",
    "NA": "NA          11   22.98977  0.0000  A   3.32840e-01  1.15897e-02",
    "CL": "CL          17   35.45300  0.0000  A   4.40104e-01  4.18400e-01",
}
for name, line in at.items():
    if not re.search(rf"^{name}\s", sec, re.M):
        extras.append(line)
if extras:
    raw = raw.replace("[ atomtypes ]", "[ atomtypes ]\n" + "\n".join(extras) + "\n", 1)

need_sol = not re.search(r"^SOL\s+2\s*$", raw, re.M)
if need_sol or "\nSOL              2\n" not in raw:
    # remove prior injected blocks between last protein mol and [ system ]
    sol_na_cl = """
[ moleculetype ]
; molname nrexcl
SOL              2

[ atoms ]
; id  at type  res nr  res name  at name  cg nr  charge    mass
    1   OW         1     SOL      OW       1     -0.834     16.00000
    2   HW         1     SOL      HW1      1      0.417      1.00800
    3   HW         1     SOL      HW2      1      0.417      1.00800

[ settles ]
; OW  funct  doh     dhh
1     1      0.09572 0.15139

[ exclusions ]
1 2 3
2 1 3
3 1 2

[ moleculetype ]
; name  nrexcl
NA               1

[ atoms ]
    1   NA     1     NA     NA    1     1.0000   22.98977

[ moleculetype ]
; name  nrexcl
CL               1

[ atoms ]
    1   CL     1     CL     CL    1    -1.0000   35.45300

"""
    if "[ moleculetype ]\n; molname nrexcl\nSOL" not in raw and re.search(r"^SOL\s+2\s*$", raw, re.M) is None:
        sys_idx = raw.find("[ system ]")
        raw = raw[:sys_idx].rstrip() + "\n" + sol_na_cl + raw[sys_idx:]

# molecules: drop SOL/NA/CL counts then re-add SOL if not yet ionized
mol_i = raw.find("[ molecules ]")
pre, rest = raw[:mol_i], raw[mol_i:]
lines = rest.splitlines()
out = []
for ln in lines:
    if re.match(r"^(SOL|NA|CL)\s+", ln):
        continue
    out.append(ln)
if not Path("solv_ions.gro").exists():
    out.append(f"SOL                  {nsol}")
raw = pre + "\n".join(out) + "\n"
p.write_text(raw)
print("topol patched nsol=", nsol, "extras=", extras)
PY

if [[ ! -f solv_ions.gro ]]; then
  echo "[$(date -Iseconds)] grompp ions + genion"
  gmx grompp -f "$MDP/ions.mdp" -c solv.gro -p topol.top -o ions.tpr -maxwarn 10 > grompp_ions.log 2>&1
  echo SOL | gmx genion -s ions.tpr -o solv_ions.gro -p topol.top \
      -pname NA -nname CL -neutral -conc 0.15 > genion.log 2>&1
  ls -la solv_ions.gro
  tail -8 genion.log
fi

# Prefer ASCII-mirrored runComplexMd if present; else resolve via python
if [[ ! -x "$RUN_SH" && ! -f "$RUN_SH" ]]; then
  RUN_SH=$(python3 - <<'PY'
from pathlib import Path
for p in Path("/mnt/e/RProject").rglob("运行复合物MD_runComplexMd.sh"):
    print(p)
    break
else:
    for p in Path("/mnt/e/md_kit").rglob("*runComplexMd*"):
        print(p)
        break
PY
)
fi
# Sync ASCII copy of run script for MDP_DIR override
if [[ -f "$RUN_SH" ]]; then
  :
else
  echo "FAIL: runComplexMd.sh not found"; exit 1
fi

export LIGAND_RES=LIG NET_CHARGE=0 NS=100 CHUNK_NS=1 MONITOR=1 CHECK_MMGBSA=0
export USE_PREBUILT_COMPLEX=1
export MDP_DIR="$MDP"
export GMX_MAXBACKUP=5

echo "RUNNING $(date -Iseconds)" > "$WORK/CYP_STATUS.txt"
echo "[$(date -Iseconds)] start production NS=$NS USE_PREBUILT_COMPLEX=1 MDP_DIR=$MDP_DIR"
exec > >(tee -a "$LOG") 2>&1
bash "$RUN_SH" "$WORK" "$WORK/protein.pdb" "$WORK/lig_h.mol2"
echo "[$(date -Iseconds)] CYP DONE"
echo "DONE $(date -Iseconds)" > "$WORK/CYP_STATUS.txt"
