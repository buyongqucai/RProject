#!/usr/bin/env bash
# 运行复合物MD_runComplexMd.sh — 蛋白-配体复合物 GROMACS MD 全流程（WSL2/Linux 内运行）
#
# 流程: pdb2gmx(蛋白, AMBER99SB-ILDN+TIP3P) → acpype/antechamber(配体 GAFF2)
#       → 复合物合并 → editconf/solvate/genion → EM → NVT → NPT → 生产 MD
#       → trjconv PBC 校正 → RMSD/RMSF/氢键/回旋半径
#
# 用法:
#   bash 运行复合物MD_runComplexMd.sh WORK_DIR PROTEIN_PDB LIGAND_MOL2 [选项]
# 选项(环境变量):
#   LIGAND_RES=JZ4      配体残基名(三字母)
#   NET_CHARGE=0        配体净电荷(antechamber -n)
#   NS=100              生产时长 ns（默认 100=生产级；烟测/演示须显式 NS≤1）
#   CHUNK_NS=1          生产分块长度 ns（块间过程监控；断点 -cpi 续跑）
#   MONITOR=1           1=每块结束后跑 过程监控_monitorMdRun.sh；异常 exit 2 即停
#   CHECK_MMGBSA=0      传给监控：1=按间隔抽查 MM-GBSA，ΔG>0 即停
#   POSE_CLASS=A3       初态场景 A1/A2/A3/A4（未设则记 A3）；门禁见 SOP §9.0.2 / §9.0.3
#   GAP_EXCLUDE_LEN=5   连续缺失 ≥ 此值则排除（大段 loop）
#   GAP_NEAR_LEN=3      口袋附近连续缺失 ≥ 此值则排除
#   GAP_NEAR_NM=1.5     「口袋附近」= 缺口端点 CA 到配体 COM 的距离上限（nm）
#   GMX_MAXBACKUP=5     同名输出备份上限（默认 5；-1=覆盖不备份）。chunk 反复写 md.gro，勿用官方默认 99
#   COFACTORS_PDB=      可选；ZN/CA 等 HETATM（§9.10.3 非键合 +2，晶体坐标）
#   USE_PREBUILT_COMPLEX=0  1=已有 complex.gro+topol.top（CYP HEME tleap/ParmEd），跳过 01–03
#   MDP_DIR=...         mdp 模板目录(默认取脚本同目录 mdp模板_mdps)
#   ACPYPE_BIN=~/md-venv/bin   acpype（UV）；antechamber 须已在 PATH（conda env md-tools）
#
# 依赖: 先 source ~/activate-md.sh；gmx + acpype + antechamber 均在 PATH
set -euo pipefail

WORK_DIR=${1:?用法: runComplexMd.sh WORK_DIR PROTEIN_PDB LIGAND_MOL2}
PROTEIN_PDB=${2:?缺蛋白 PDB}
LIGAND_MOL2=${3:?缺配体 mol2(须已加氢)}
LIGAND_RES=${LIGAND_RES:-JZ4}
NET_CHARGE=${NET_CHARGE:-0}
NS=${NS:-100}
CHUNK_NS=${CHUNK_NS:-1}
MONITOR=${MONITOR:-1}
CHECK_MMGBSA=${CHECK_MMGBSA:-0}
COFACTORS_PDB=${COFACTORS_PDB:-}
USE_PREBUILT_COMPLEX=${USE_PREBUILT_COMPLEX:-0}
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
MDP_DIR=${MDP_DIR:-"$SCRIPT_DIR/mdp模板_mdps"}
ACPYPE_BIN=${ACPYPE_BIN:-$HOME/md-venv/bin}
# UV acpype first; AmberTools (conda md-tools) + GPU gmx must already be on PATH via ~/activate-md.sh
export PATH="$ACPYPE_BIN:$HOME/gromacs-gpu/bin:$PATH"
# 分块反复写 md.gro：默认覆盖不备份；续跑靠 md.cpt
export GMX_MAXBACKUP="${GMX_MAXBACKUP:--1}"
NDX_ARG=()   # 有金属时填 -n index.ndx，使 ZN/CA 并入 Water_and_ions 温控组

log(){ echo "[$(date +%H:%M:%S)] $*"; }
# 是否 GMX_MAXBACKUP / md.gro 备份上限 Fatal（物理未坏，可清备份续跑）
is_gro_backup_fatal() {
  grep -qiE 'Won.?t make more than .* backups of md\.gro|GMX_MAXBACKUP' \
    mdrun_md.log md.log 2>/dev/null || return 1
  return 0
}

prune_md_gro_backups() {
  rm -f '#md.gro.'* '#md1.gro.'* 2>/dev/null || true
}

fail_setup() {
  local reason="$1"
  mkdir -p monitor
  echo "$reason" > monitor/ABORT_REASON.txt
  log "FAIL: $reason"
  if [[ "${MD_ALERT_DEFER:-0}" == "1" ]]; then
    exit 1
  fi
  local cand
  for cand in "$SCRIPT_DIR/../环境安装_EnvSetup/notify_md_alert.sh" /mnt/e/md_kit/notify_md_alert.sh; do
    if [[ -f "$cand" ]]; then
      bash "$cand" "$(pwd)" --phase final "$reason" || true
      break
    fi
  done
  exit 1
}
# §9.0.3 主链缺口：大段 loop / 口袋附近缺环则排除（不砌缺失残基）
qc_protein_gaps() {
  python3 - "$1" "${2:-}" <<'PY'
import math, os, sys
from pathlib import Path
from collections import defaultdict

pdb_path = Path(sys.argv[1])
lig_path = Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else None
gap_ex = int(os.environ.get("GAP_EXCLUDE_LEN", "5"))
gap_near = int(os.environ.get("GAP_NEAR_LEN", "3"))
near_nm = float(os.environ.get("GAP_NEAR_NM", "1.5"))
near_a = near_nm * 10.0

def parse_remark465(lines):
    # REMARK 465     M RES C SSSEQI
    gaps = []  # list of (chain, resseq)
    on = False
    for line in lines:
        if line.startswith("REMARK 465"):
            if "M RES C SSSEQI" in line or "RES C SSSEQI" in line:
                on = True
                continue
            if not on:
                continue
            body = line[10:].strip()
            if not body or body.startswith("M ") and "RES" in body:
                continue
            parts = body.split()
            # formats: "M RES C SSSEQI" data rows like "  ALA A  45" or with model
            if len(parts) >= 3 and parts[-2].isalpha() and len(parts[-2]) == 1:
                try:
                    resseq = int(parts[-1])
                except ValueError:
                    continue
                gaps.append((parts[-2], resseq))
            elif len(parts) >= 4:
                try:
                    resseq = int(parts[-1])
                except ValueError:
                    continue
                chain = parts[-2]
                if len(chain) == 1:
                    gaps.append((chain, resseq))
        elif on and not line.startswith("REMARK 465"):
            on = False
    return gaps

def stretches(pairs):
    by = defaultdict(list)
    for c, r in pairs:
        by[c].append(r)
    out = []
    for c, rs in by.items():
        rs = sorted(set(rs))
        if not rs:
            continue
        a = b = rs[0]
        for x in rs[1:]:
            if x == b + 1:
                b = x
            else:
                out.append((c, a, b, b - a + 1))
                a = b = x
        out.append((c, a, b, b - a + 1))
    return out

def gaps_from_ca_jumps(lines):
    ca = defaultdict(list)  # chain -> [(resseq, x,y,z)]
    for line in lines:
        if not (line.startswith("ATOM") or line.startswith("HETATM")):
            continue
        if line[12:16].strip() != "CA":
            continue
        chain = line[21].strip() or "_"
        try:
            resseq = int(line[22:26])
            xyz = (float(line[30:38]), float(line[38:46]), float(line[46:54]))
        except ValueError:
            continue
        ca[chain].append((resseq, xyz))
    miss = []
    ends = {}  # (chain,start,end) -> (xyz_start, xyz_end)
    for c, rows in ca.items():
        rows = sorted(rows, key=lambda t: t[0])
        # unique resseq keep first CA
        uniq = []
        seen = set()
        for r, xyz in rows:
            if r in seen:
                continue
            seen.add(r)
            uniq.append((r, xyz))
        for i in range(len(uniq) - 1):
            r0, xyz0 = uniq[i]
            r1, xyz1 = uniq[i + 1]
            if r1 - r0 > 1:
                for r in range(r0 + 1, r1):
                    miss.append((c, r))
                ends[(c, r0 + 1, r1 - 1)] = (xyz0, xyz1)
    return miss, ends

def lig_com(path: Path):
    if not path or not path.is_file():
        return None
    text = path.read_text(errors="replace").splitlines()
    coords = []
    if path.suffix.lower() == ".mol2":
        in_a = False
        for line in text:
            if line.startswith("@<TRIPOS>ATOM"):
                in_a = True
                continue
            if line.startswith("@<TRIPOS>"):
                in_a = False
                continue
            if not in_a or not line.strip():
                continue
            p = line.split()
            if len(p) < 5:
                continue
            elem = "".join(ch for ch in p[1] if ch.isalpha())[:1].upper()
            if elem == "H":
                continue
            coords.append(tuple(map(float, p[2:5])))
    else:
        for line in text:
            if not (line.startswith("ATOM") or line.startswith("HETATM")):
                continue
            name = line[12:16].strip()
            elem = "".join(ch for ch in name if ch.isalpha())[:1].upper()
            if elem == "H":
                continue
            try:
                coords.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
            except ValueError:
                continue
    if not coords:
        return None
    n = len(coords)
    return (sum(c[0] for c in coords) / n, sum(c[1] for c in coords) / n, sum(c[2] for c in coords) / n)

lines = pdb_path.read_text(errors="replace").splitlines()
miss465 = parse_remark465(lines)
miss_jump, jump_ends = gaps_from_ca_jumps(lines)
source = "REMARK465" if miss465 else "CA_resseq_jump"
miss = miss465 if miss465 else miss_jump
segs = stretches(miss)
com = lig_com(lig_path)

Path("monitor").mkdir(exist_ok=True)
rep = [f"source={source}", f"n_missing_residues={len(miss)}", f"n_segments={len(segs)}"]
exclude = []
for c, a, b, L in segs:
    rep.append(f"gap\tchain={c}\tstart={a}\tend={b}\tlength={L}")
    if L >= gap_ex:
        exclude.append(f"long_gap chain {c} {a}-{b} len={L} (>={gap_ex})")
        continue
    if L >= gap_near and com is not None:
        xyz0 = xyz1 = None
        key = (c, a, b)
        if key in jump_ends:
            xyz0, xyz1 = jump_ends[key]
        else:
            # REMARK465：用缺口两端已有残基的 CA
            ca_map = {}
            for line in lines:
                if not line.startswith("ATOM"):
                    continue
                if line[12:16].strip() != "CA":
                    continue
                ch = line[21].strip() or "_"
                try:
                    rr = int(line[22:26])
                    ca_map[(ch, rr)] = (
                        float(line[30:38]),
                        float(line[38:46]),
                        float(line[46:54]),
                    )
                except ValueError:
                    continue
            xyz0 = ca_map.get((c, a - 1))
            xyz1 = ca_map.get((c, b + 1))
        if xyz0 is not None and xyz1 is not None:
            dmin = min(math.dist(xyz0, com), math.dist(xyz1, com))
            rep.append(f"near_check\tchain={c}\t{a}-{b}\tmin_end_CA_to_lig_A={dmin:.2f}")
            if dmin <= near_a:
                exclude.append(
                    f"pocket_gap chain {c} {a}-{b} len={L} end_CA_to_lig={dmin/10:.2f} nm (<= {near_nm} nm)"
                )
        elif L >= gap_near:
            rep.append(f"near_check\tchain={c}\t{a}-{b}\tskipped_no_flanking_CA")

Path("monitor/protein_gaps.txt").write_text("\n".join(rep) + "\n")
print("\n".join(rep))
if exclude:
    sys.exit("EXCLUDE: " + "; ".join(exclude))
print("protein gap QC OK")
PY
}
# §9.0.2 配体几何：重叠或离散原子不得进 acpype
qc_ligand_mol2() {
  python3 - "$1" <<'PY'
import sys
from pathlib import Path
p = Path(sys.argv[1])
text = p.read_text(errors="replace").splitlines()
n_header = None
atoms = []
in_atom = False
for line in text:
    if line.startswith("@<TRIPOS>MOLECULE"):
        in_atom = False
        continue
    if line.startswith("@<TRIPOS>ATOM"):
        in_atom = True
        continue
    if line.startswith("@<TRIPOS>"):
        in_atom = False
        continue
    if n_header is None and line.strip() and line.split()[0].isdigit() and len(line.split()) >= 1:
        # second numeric header line: natom nbond ...
        parts = line.split()
        if len(parts) >= 2 and parts[1].isdigit():
            n_header = int(parts[0])
        continue
    if in_atom and line.strip():
        parts = line.split()
        if len(parts) < 6:
            continue
        try:
            x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
        except ValueError:
            continue
        elem = "".join(c for c in parts[1] if c.isalpha())[:1].upper() or "C"
        atoms.append((elem, x, y, z))
if n_header is not None and n_header != len(atoms):
    sys.exit(f"mol2 atom count header {n_header} != ATOM rows {len(atoms)}")
heavy = [(x, y, z) for e, x, y, z in atoms if e != "H"]
if len(heavy) < 2:
    sys.exit("mol2 has <2 heavy atoms")
import math
dmin = 1e9
isolated = 0
for i, a in enumerate(heavy):
    nearest = 1e9
    for j, b in enumerate(heavy):
        if i == j:
            continue
        d = math.dist(a, b)
        if d < dmin:
            dmin = d
        if d < nearest:
            nearest = d
    if nearest > 3.0:
        isolated += 1
if dmin < 0.5:
    sys.exit(f"mol2 heavy atoms closer than 0.5 A (min={dmin:.3f})")
if isolated:
    sys.exit(f"mol2 has {isolated} heavy atoms with no neighbor within 3.0 A")
print(f"mol2 QC OK heavy={len(heavy)} min_dist={dmin:.3f} A")
PY
}
# §9.0.2 初态接触：配体须贴着蛋白，且没有原子重叠
qc_pose_contact() {
  python3 - "$LIGAND_RES" <<'PY'
import sys
from pathlib import Path
lig = sys.argv[1]
lines = Path("complex.gro").read_text().splitlines()
n = int(lines[1])
prot, ligand = [], []
skip = {"SOL", "NA", "CL", "WAT", "HOH", "ZN", "CA", "MG"}
for line in lines[2:2+n]:
    res = line[5:10].strip()
    try:
        xyz = (float(line[20:28]), float(line[28:36]), float(line[36:44]))
    except ValueError:
        continue
    if res == lig:
        ligand.append(xyz)
    elif res not in skip:
        prot.append(xyz)
if not prot or not ligand:
    sys.exit(f"complex.gro missing protein ({len(prot)}) or ligand {lig} ({len(ligand)})")
dmin = 1e9
for a in ligand:
    for b in prot:
        d = ((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2) ** 0.5
        if d < dmin:
            dmin = d
Path("monitor").mkdir(exist_ok=True)
Path("monitor/pose_gate.txt").write_text(
    f"min_heavy_distance_nm={dmin:.4f}\nligand_atoms={len(ligand)}\nprotein_atoms={len(prot)}\n"
)
print(f"pose contact min={dmin:.3f} nm")
if dmin < 0.05:
    sys.exit(f"protein-ligand clash {dmin:.3f} nm < 0.05 nm")
if dmin > 0.60:
    sys.exit(f"ligand not in contact {dmin:.3f} nm > 0.60 nm")
PY
}
cd "$WORK_DIR"
mkdir -p monitor
POSE_CLASS=${POSE_CLASS:-A3}
echo "$POSE_CLASS" > monitor/pose_class.txt
if [[ "$POSE_CLASS" != "A1" && "$POSE_CLASS" != "A2" && "$POSE_CLASS" != "A3" && "$POSE_CLASS" != "A4" ]]; then
  fail_setup "POSE_CLASS=$POSE_CLASS 不是 A1/A2/A3/A4"
fi
log "00 初态场景 POSE_CLASS=$POSE_CLASS（SOP §9.0.1 / 门禁 §9.0.2）"

if [[ "$USE_PREBUILT_COMPLEX" == "1" ]]; then
  [[ -f complex.gro && -f topol.top ]] || {
    log "FAIL: USE_PREBUILT_COMPLEX=1 但缺 complex.gro / topol.top"; exit 1
  }
  log "00 预构建复合物（跳过 01–03）：complex.gro + topol.top"
  grep -Eiq "LIG|${LIGAND_RES}" topol.top \
    || { log "FAIL: topol.top 未见配体 ${LIGAND_RES}/LIG"; exit 1; }
else
# ---- 01 配体 GAFF2 拓扑(acpype → antechamber AM1-BCC + parmchk2) ----
if [[ ! -f ligand.acpype/ligand_GMX.itp ]]; then
  log "01 mol2 几何门禁"
  if ! qc_ligand_mol2 "$LIGAND_MOL2" > mol2_qc.log 2>&1; then
    fail_setup "ligand mol2 geometry failed: $(tail -n 1 mol2_qc.log)"
  fi
  log "01 acpype 配体拓扑 (GAFF2, 净电荷 $NET_CHARGE)"
  rm -rf ligand.acpype acpype_tmp.mol2
  cp "$LIGAND_MOL2" acpype_tmp.mol2
  acpype -i acpype_tmp.mol2 -n "$NET_CHARGE" -a gaff2 -o gmx -b ligand > acpype.log 2>&1
  rm -f acpype_tmp.mol2
fi
LIG_ITP=ligand.acpype/ligand_GMX.itp
LIG_GRO=ligand.acpype/ligand_GMX.gro
[[ -f $LIG_ITP && -f $LIG_GRO ]] || { log "FAIL: acpype 未产出 $LIG_ITP"; exit 1; }
# 拓扑连通性门禁：任一原子零键即熔断（幽灵原子会1ns内飞散，ESR2 2026-10-13 实测）
python3 - "$LIG_ITP" <<'PY' || fail_setup "ligand topology has zero-bond atoms"
import re, sys
t = open(sys.argv[1]).read()
def sect(name):
    m = re.search(r"\[ *" + name + r" *\](.*?)(\[ |\Z)", t, re.S)
    return m.group(1) if m else ""
atoms = [l.split() for l in sect("atoms").splitlines() if l.strip() and not l.strip().startswith(";")]
bonds = [l.split() for l in sect("bonds").splitlines() if l.strip() and not l.strip().startswith(";")]
deg = {}
for a in atoms:
    if len(a) >= 5:
        deg[int(a[0])] = 0
for b in bonds:
    if len(b) >= 2:
        for k in (0, 1):
            i = int(b[k])
            if i in deg:
                deg[i] += 1
zeros = [i for i, d in deg.items() if d == 0]
if zeros:
    print("ZERO-BOND atoms:", zeros, file=sys.stderr)
    sys.exit(1)
print(f"topology connectivity OK ({len(atoms)} atoms, {len(bonds)} bonds)")
PY
# acpype 的 moleculetype 名取自 -b 基名而非残基名；统一改名为 $LIGAND_RES 以对齐 topol.top
awk -v r="$LIGAND_RES" '
  /\[ moleculetype \]/ {f=1; print; next}
  f==1 && /^[ \t]*;/   {print; next}
  f==1 && NF>=2        {$1=r; f=0; print; next}
  {print}' "$LIG_ITP" > "$LIG_ITP.tmp" && mv "$LIG_ITP.tmp" "$LIG_ITP"
grep -q "^$LIGAND_RES " <(awk '/\[ moleculetype \]/{f=1;next} f&&NF&&!/^;/{print;exit}' "$LIG_ITP") \
  && log "01 配体 moleculetype=$LIGAND_RES OK" || { log "FAIL: moleculetype 改名失败"; exit 1; }
# mol2 子结构名常为 A1 等；统一 gro + itp 残基名为 $LIGAND_RES
# （仅改 gro 不够：genion/mdrun 会按 itp [atoms] 的 resid 写回 A1）
python3 - "$LIG_GRO" "$LIG_ITP" "$LIGAND_RES" <<'PY'
import sys, re
from pathlib import Path
gro, itp, res = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
lines = gro.read_text().splitlines()
n = int(lines[1])
out = [lines[0], lines[1]]
for line in lines[2:2 + n]:
    out.append(f"{line[0:5]}{res:<5s}{line[10:]}")
out.append(lines[2 + n])
gro.write_text("\n".join(out) + "\n")
# itp [atoms]: nr type resnr resid atom ...
text = itp.read_text().splitlines()
o, in_atoms = [], False
for line in text:
    if re.match(r"\[\s*atoms\s*\]", line):
        in_atoms = True
        o.append(line)
        continue
    if in_atoms and line.strip().startswith("["):
        in_atoms = False
    if in_atoms and line.strip() and not line.strip().startswith(";"):
        parts = line.split()
        if len(parts) >= 5 and parts[0].isdigit():
            parts[3] = res
            # 保留常见 acpype 列宽风格
            line = f"{int(parts[0]):6d}{parts[1]:>3s}{int(parts[2]):7d}{parts[3]:>7s}{parts[4]:>7s}{int(parts[5]):7d}{float(parts[6]):11.5f}{float(parts[7]):11.5f}"
            if len(parts) > 8:
                line += "  " + " ".join(parts[8:])
    o.append(line)
itp.write_text("\n".join(o) + "\n")
print(f"ligand gro+itp residue -> {res}")
PY

# ---- 02 蛋白拓扑(pdb2gmx) ----
if [[ ! -f protein.gro ]]; then
  if [[ ! -f monitor/PROTEIN_GAP_OK.txt ]]; then
    log "02 蛋白主链缺口门禁（SOP §9.0.3）"
    if ! qc_protein_gaps "$PROTEIN_PDB" "$LIGAND_MOL2" > protein_gaps.log 2>&1; then
      fail_setup "protein gap gate failed: $(tail -n 1 protein_gaps.log)"
    fi
    cp -f monitor/protein_gaps.txt monitor/PROTEIN_GAP_OK.txt
    log "02 protein gaps OK ($(grep -c '^gap' monitor/protein_gaps.txt || true) segments reported)"
  fi
  log "02 pdb2gmx 蛋白拓扑 (amber99sb-ildn/tip3p)"
  set +e
  gmx pdb2gmx -f "$PROTEIN_PDB" -o protein.gro -p topol.top -i posre.itp \
      -ff amber99sb-ildn -water tip3p -ignh > pdb2gmx.log 2>&1
  P2G_RC=$?
  set -e
  if [[ $P2G_RC -ne 0 || ! -s topol.top || ! -f protein.gro ]]; then
    reason="pdb2gmx failed (rc=$P2G_RC)"
    if grep -q "Fatal error" pdb2gmx.log 2>/dev/null; then
      reason="$(grep -A2 'Fatal error' pdb2gmx.log | tr '\n' ' ')"
    fi
    fail_setup "$reason"
  fi
fi

# ---- 03 合并复合物 complex.gro + topol.top 接入配体（+可选金属辅因子）----
if [[ ! -f complex.gro ]]; then
  log "03 合并蛋白+配体坐标${COFACTORS_PDB:+ +辅因子}"
  python3 - "$LIG_GRO" "${COFACTORS_PDB:-}" <<'PY'
import sys, re
prot = open("protein.gro").read().splitlines()
lig  = open(sys.argv[1]).read().splitlines()
cof_path = sys.argv[2] if len(sys.argv) > 2 else ""
title = prot[0]
np_, nl = int(prot[1]), int(lig[1])
patoms = prot[2:2+np_]
latoms = lig[2:2+nl]
box = prot[2+np_]
# 金属：PDB Å → gro nm；残基名去空格后只保留 ZN/CA/MG（amber99sb-ildn ions.itp）
metal_atoms, metal_counts = [], {}
allowed = {"ZN", "CA", "MG"}
if cof_path:
    for line in open(cof_path, errors="replace"):
        if not (line.startswith("HETATM") or line.startswith("ATOM")):
            continue
        res = line[17:20].replace(" ", "")
        if res not in allowed:
            continue
        name = (line[12:16].strip() or res)[:5]
        x = float(line[30:38]) / 10.0
        y = float(line[38:46]) / 10.0
        z = float(line[46:54]) / 10.0
        metal_counts[res] = metal_counts.get(res, 0) + 1
        # resnr 从蛋白后编号；atom 序号稍后统一重编
        metal_atoms.append((res, name, x, y, z))
# 顺序：Protein → 金属 → 配体（与 topol [molecules] 一致）
atoms_out = list(patoms)
res0 = 1
# 从蛋白最后残基号续编
if patoms:
    try:
        res0 = int(patoms[-1][0:5]) + 1
    except Exception:
        res0 = np_ + 1
for i, (res, name, x, y, z) in enumerate(metal_atoms):
    # gro: %5d%-5s%5s%5d%8.3f%8.3f%8.3f
    atoms_out.append(f"{res0+i:5d}{res:<5s}{name:>5s}{0:5d}{x:8.3f}{y:8.3f}{z:8.3f}")
atoms_out.extend(latoms)
# 重编原子序号 1..N
renum = []
for i, line in enumerate(atoms_out, 1):
    renum.append(f"{line[:15]}{i%100000:5d}{line[20:]}")
with open("complex.gro", "w") as fh:
    fh.write(title + "\n")
    fh.write(f"{len(renum)}\n")
    fh.write("\n".join(renum) + "\n")
    fh.write(box + "\n")
with open("metal_counts.txt", "w") as fh:
    for k in ("ZN", "CA", "MG"):
        if metal_counts.get(k):
            fh.write(f"{k} {metal_counts[k]}\n")
print("metals", metal_counts)
PY
fi
if ! grep -q "ligand_GMX.itp" topol.top; then
  log "03 topol.top 接入配体 itp + molecules"
  sed -i "s|^\(#include .*forcefield.itp.*\)$|\1\n#include \"ligand.acpype/ligand_GMX.itp\"|" topol.top
  # 金属在配体之前写入 [molecules]（与 complex.gro 顺序一致：Protein | ZN/CA | LIG）
  if [[ -f metal_counts.txt ]]; then
    while read -r mname mcount; do
      [[ -n "${mname:-}" ]] || continue
      printf '%-20s %s\n' "$mname" "$mcount" >> topol.top
      log "03 topol 辅因子 $mname x$mcount (非键合 +2)"
    done < metal_counts.txt
  fi
  printf '%-20s %s\n' "$LIGAND_RES" "1" >> topol.top
fi
grep -q "$LIGAND_RES" topol.top || { log "FAIL: topol.top 未登记配体"; exit 1; }
fi  # end USE_PREBUILT_COMPLEX else

# ParmEd 拓扑常无离子 atomtype/moleculetype；补 amber99 风格 NA/CL（与 tip3p 兼容）
ensure_ion_types() {
  if grep -Eq '^[[:space:]]*NA[[:space:]]+[0-9]' topol.top 2>/dev/null; then
    return 0
  fi
  log "04+ 注入 NA/CL atomtypes + moleculetypes（预构建拓扑）"
  python3 - <<'PY'
from pathlib import Path
p = Path("topol.top")
t = p.read_text(errors="replace")
block_at = """
; --- ions for genion (injected) ---
[ atomtypes ]
; name  at.num   mass     charge  ptype     sigma      epsilon
NA          11   22.98977  0.0000  A   3.32840e-01  1.15897e-02
CL          17   35.45300  0.0000  A   4.40104e-01  4.18400e-01

"""
block_mol = """
[ moleculetype ]
; name  nrexcl
NA               1
[ atoms ]
;  nr  type  resnr  resid  atom  cgnr  charge   mass
   1   NA     1     NA     NA    1     1.0000   22.98977

[ moleculetype ]
; name  nrexcl
CL               1
[ atoms ]
;  nr  type  resnr  resid  atom  cgnr  charge   mass
   1   CL     1     CL     CL    1    -1.0000   35.45300

"""
if "[ atomtypes ]" in t and "NA" not in t.split("[ atomtypes ]", 1)[1][:800]:
    t = t.replace("[ atomtypes ]", "[ atomtypes ]\nNA          11   22.98977  0.0000  A   3.32840e-01  1.15897e-02\nCL          17   35.45300  0.0000  A   4.40104e-01  4.18400e-01\n", 1)
else:
    # 插到第一个 [ moleculetype ] 前
    idx = t.find("[ moleculetype ]")
    if idx < 0:
        raise SystemExit("no [ moleculetype ] in topol.top")
    t = t[:idx] + block_at + t[idx:]
if "\nNA               1\n" not in t and "[ moleculetype ]\n; name  nrexcl\nNA" not in t:
    idx = t.find("[ system ]")
    if idx < 0:
        raise SystemExit("no [ system ]")
    t = t[:idx] + block_mol + t[idx:]
p.write_text(t)
print("ion types injected")
PY
}

# ---- 03b 初态接触（溶剂化之前；已通过则不重复）----
if [[ -f complex.gro && ! -f monitor/POSE_GATE_OK.txt ]]; then
  log "03b 蛋白–配体接触门禁"
  if ! qc_pose_contact > pose_gate.log 2>&1; then
    fail_setup "pose contact failed: $(tail -n 1 pose_gate.log)"
  fi
  cp -f monitor/pose_gate.txt monitor/POSE_GATE_OK.txt
  log "03b $(tail -n 1 pose_gate.log)"
fi

# ---- 04 盒子 + 溶剂化 + 离子 ----
if [[ ! -f solv_ions.gro ]]; then
  log "04 editconf/solvate/genion (0.15 M NaCl 中和)"
  # 防重入：solvate/genion 会向 topol.top 追加 SOL/NA/CL 行，重跑前剔除旧行
  sed -i '/^SOL[ \t]/d; /^NA[ \t]/d; /^CL[ \t]/d' topol.top
  # 中和前必有「net charge」警告；对接/补原子结构偶发长排除距离 → 默认允许 2 条
  MAXWARN_IONS=${MAXWARN_IONS:-2}
  if [[ "$USE_PREBUILT_COMPLEX" == "1" ]]; then
    MAXWARN_IONS=10
    ensure_ion_types
  fi
  # topol 被重建后若仍留着旧 solv.gro，原子数会对不上 → 强制重溶剂化
  if [[ -f solv.gro ]] && ! grep -qE '^SOL[[:space:]]' topol.top; then
    log "04 solv.gro 与 topol 不同步（缺 SOL 行），删除后重溶剂化"
    rm -f solv.gro newbox.gro
  fi
  if [[ ! -f solv.gro ]]; then
    gmx editconf -f complex.gro -o newbox.gro -bt dodecahedron -d 1.0 > editconf.log 2>&1
    gmx solvate -cp newbox.gro -cs spc216 -p topol.top -o solv.gro > solvate.log 2>&1
  fi
  if [[ "$USE_PREBUILT_COMPLEX" == "1" ]]; then ensure_ion_types; fi
  set +e
  gmx grompp -f "$MDP_DIR/ions.mdp" -c solv.gro -p topol.top -o ions.tpr -maxwarn "$MAXWARN_IONS" > grompp_ions.log 2>&1
  IONS_RC=$?
  set -e
  if [[ $IONS_RC -ne 0 || ! -f ions.tpr ]]; then
    reason="grompp ions failed (rc=$IONS_RC, maxwarn=$MAXWARN_IONS); see grompp_ions.log"
    mkdir -p monitor
    echo "$reason" > monitor/ABORT_REASON.txt
    log "FAIL: $reason"
    for cand in "$SCRIPT_DIR/../环境安装_EnvSetup/notify_md_alert.sh" /mnt/e/md_kit/notify_md_alert.sh; do
      [[ -f "$cand" ]] && { bash "$cand" "$reason" "$(pwd)" || true; break; }
    done
    exit 1
  fi
  echo SOL | gmx genion -s ions.tpr -o solv_ions.gro -p topol.top \
      -pname NA -nname CL -neutral -conc 0.15 > genion.log 2>&1
fi

# ---- 04b 有金属时重建 index：ZN/CA/MG 并入 Water_and_ions，避免温控组漏原子 ----
if [[ -f metal_counts.txt && ! -f index.ndx ]]; then
  log "04b make_ndx：金属并入 Water_and_ions"
  python3 - "$LIGAND_RES" <<'PY'
import sys
lig = sys.argv[1]
lines = open("solv_ions.gro").read().splitlines()
n = int(lines[1])
atoms = lines[2:2+n]
prot, lig_ix, wai, bb, ca = [], [], [], [], []
metal_res = {"ZN", "CA", "MG"}
solvent_res = {"SOL", "NA", "CL", "WAT", "HOH"} | metal_res
for i, line in enumerate(atoms, 1):
    res = line[5:10].strip()
    aname = line[10:15].strip()
    if res == lig:
        lig_ix.append(i)
    elif res in solvent_res:
        wai.append(i)
    else:
        prot.append(i)
        # 蛋白骨架；残基名 CA(钙)已在 solvent_res，不会进此支
        if aname in ("N", "CA", "C", "O"):
            bb.append(i)
        if aname == "CA":
            ca.append(i)
def dump(name, ids):
    out = [f"[ {name} ]"]
    for j in range(0, len(ids), 15):
        out.append(" ".join(str(x) for x in ids[j:j+15]))
    return "\n".join(out)
sys_ids = list(range(1, n + 1))
text = "\n".join([
    dump("System", sys_ids),
    dump("Protein", prot),
    dump("Backbone", bb),
    dump("C-alpha", ca),
    dump(lig, lig_ix),
    dump("Water_and_ions", wai),
]) + "\n"
open("index.ndx", "w").write(text)
print(f"index: Protein={len(prot)} BB={len(bb)} CA={len(ca)} {lig}={len(lig_ix)} WAI={len(wai)} N={n}")
PY
fi
if [[ -f index.ndx ]]; then
  NDX_ARG=(-n index.ndx)
fi

MAXWARN_GMX=${MAXWARN_GMX:-2}
if [[ "$USE_PREBUILT_COMPLEX" == "1" ]]; then MAXWARN_GMX=10; fi

# ---- 05 能量最小化 ----
if [[ ! -f em.gro ]]; then
  log "05 能量最小化"
  gmx grompp -f "$MDP_DIR/em.mdp" -c solv_ions.gro -p topol.top -o em.tpr \
      "${NDX_ARG[@]}" -maxwarn "$MAXWARN_GMX" > grompp_em.log 2>&1
  gmx mdrun -v -deffnm em > mdrun_em.log 2>&1
fi
if [[ -f em.gro ]]; then
  if ! grep -q "converged to Fmax" em.log 2>/dev/null \
     && ! grep -q "converged to Fmax" mdrun_em.log 2>/dev/null; then
    fail_setup "EM did not converge to Fmax (see em.log); do not start NVT"
  fi
fi

# ---- 06 渲染 mdp 模板（__LIG__ → 实际配体残基名；温控/分析全用默认组，免索引文件） ----
for m in nvt npt md; do
  sed "s/__LIG__/$LIGAND_RES/g" "$MDP_DIR/$m.mdp" > "run_$m.mdp"
done

# ---- 07 NVT ----
if [[ ! -f nvt.gro ]]; then
  log "07 NVT 100 ps"
  gmx grompp -f run_nvt.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr \
      "${NDX_ARG[@]}" -maxwarn "$MAXWARN_GMX" > grompp_nvt.log 2>&1
  gmx mdrun -v -deffnm nvt > mdrun_nvt.log 2>&1
fi

# ---- 08 NPT ----
if [[ ! -f npt.gro ]]; then
  log "08 NPT 100 ps"
  gmx grompp -f run_npt.mdp -c nvt.gro -r nvt.gro -t nvt.cpt -p topol.top -o npt.tpr \
      "${NDX_ARG[@]}" -maxwarn "$MAXWARN_GMX" > grompp_npt.log 2>&1
  gmx mdrun -v -deffnm npt > mdrun_npt.log 2>&1
fi

# ---- 09 生产 MD（分块 + 断点 -cpi；块间过程监控，异常即停）----
# dt=0.002 ps → 1 ns = 500000 步
NSTEPS=$(awk -v ns="$NS" 'BEGIN{printf "%d", ns*1000/0.002}')
CHUNK_STEPS=$(awk -v ns="$CHUNK_NS" 'BEGIN{s=int(ns*1000/0.002); if(s<1000)s=1000; print s}')
# 已完成 ns：md.log 最后 Time(ps)/1000；无则 0（可断点续跑；md.gro 存在也不跳过未满 NS）
done_ns() {
  if [[ -f md.log ]]; then
    awk '/^[[:space:]]*[0-9]+[[:space:]]+[0-9.]+/ {
      if ($1+0==$1 && $2+0==$2) t=$2
    } END { if (t!="") printf "%.6f", t/1000; else print 0 }' md.log
  elif [[ -f md.xtc ]]; then
    gmx check -f md.xtc 2>&1 | awk 'BEGIN{t=0} /time/{
      for(i=1;i<=NF;i++) if($i=="time" && $(i+1)+0==$(i+1)) t=$(i+1)
    } END{printf "%.6f", t/1000}'
  else
    echo 0
  fi
}
CUR0=$(done_ns); CUR0=${CUR0:-0}
NEED_PROD=$(awk -v c="$CUR0" -v t="$NS" 'BEGIN{print (c+1e-6>=t)?0:1}')
if [[ "$NEED_PROD" == "1" ]]; then
  log "09 生产 MD ${NS} ns (done=${CUR0} ns; chunk=${CHUNK_NS} ns / ${CHUNK_STEPS} steps; MONITOR=$MONITOR)"
  sed -i "s/^nsteps .*/nsteps          = $NSTEPS/" run_md.mdp
  if [[ ! -f md.tpr ]]; then
    gmx grompp -f run_md.mdp -c npt.gro -t npt.cpt -p topol.top -o md.tpr \
        "${NDX_ARG[@]}" -maxwarn "$MAXWARN_GMX" > grompp_md.log 2>&1
  fi
  while true; do
    CUR=$(done_ns)
    CUR=${CUR:-0}
    DONE=$(awk -v c="$CUR" -v t="$NS" 'BEGIN{print (c+1e-6>=t)?1:0}')
    if [[ "$DONE" == "1" ]]; then
      log "09 production reached ${CUR} ns >= ${NS} ns"
      break
    fi
    REMAIN_STEPS=$(awk -v c="$CUR" -v t="$NS" -v cs="$CHUNK_STEPS" 'BEGIN{
      left=(t-c)*1000/0.002; if(left<1) left=1;
      n=cs; if(n>left) n=left; printf "%d", n
    }')
    log "09 mdrun chunk ~from ${CUR} ns (+${REMAIN_STEPS} steps)"
    # 块前清 gro 备份，避免 MAXBACKUP 在块末写 md.gro 时 Fatal（SOP：轨迹/cpt 仍在）
    prune_md_gro_backups
    set +e
    if [[ -f md.cpt ]]; then
      gmx mdrun -v -deffnm md -cpi md.cpt -cpo md.cpt -nsteps "$REMAIN_STEPS" \
        >> mdrun_md.log 2>&1
    else
      gmx mdrun -v -deffnm md -cpo md.cpt -nsteps "$REMAIN_STEPS" \
        >> mdrun_md.log 2>&1
    fi
    MDRC=$?
    set -e
    if [[ "$MDRC" -ne 0 ]]; then
      if is_gro_backup_fatal; then
        log "WARN mdrun exit=$MDRC GMX_MAXBACKUP/md.gro backups — prune + GMX_MAXBACKUP=-1, continue; cpt kept"
        prune_md_gro_backups
        export GMX_MAXBACKUP=-1
        pipeline_alert "GMX_MAXBACKUP md.gro backup Fatal at ~${CUR} ns non-physics; auto-prune and continue with GMX_MAXBACKUP=-1"
        # 本块积分往往已写完 cpt；不重跑本块步数，直接进监控/下一块
      else
        log "ABORT mdrun exit=$MDRC — see mdrun_md.log / md.log"
        pipeline_alert "gmx mdrun failed exit=$MDRC at ~${CUR} ns not backup-limit; see mdrun_md.log"
        exit "$MDRC"
      fi
    fi
    if [[ "$MONITOR" == "1" ]]; then
      log "09 monitor after chunk"
      LIGAND_RES="$LIGAND_RES" CHECK_MMGBSA="$CHECK_MMGBSA" \
        bash "$SCRIPT_DIR/过程监控_monitorMdRun.sh" . || {
          RC=$?
          log "ABORT monitor exit=$RC — see monitor/ABORT_REASON.txt (fix with md.cpt)"
          # monitor 内 abort() 已尝试发信；此处再兜一层防路径缺失
          pipeline_alert "MONITOR abort exit=$RC — see monitor/ABORT_REASON.txt"
          exit "$RC"
        }
    fi
  done
  # 终态坐标：优先从轨迹抽末帧（避免再触发 gro 备份上限）
  if [[ ! -f md.gro && -f md.xtc && -f md.tpr ]]; then
    END_PS=$(awk -v ns="$NS" 'BEGIN{printf "%.3f", ns*1000}')
    log "09 trjconv dump ${END_PS} ps → md.gro (GMX_MAXBACKUP=$GMX_MAXBACKUP)"
    echo 0 | gmx trjconv -s md.tpr -f md.xtc -o md.gro -dump "$END_PS" \
      > trjconv_final_gro.log 2>&1 || true
  fi
  if [[ ! -f md.gro && -f md.cpt ]]; then
    gmx mdrun -v -deffnm md -cpi md.cpt -cpo md.cpt -nsteps 0 >> mdrun_md.log 2>&1 || true
  fi
else
  log "09 生产已满 ${CUR0} ns >= ${NS} ns，跳过"
  if [[ ! -f md.gro && -f md.xtc && -f md.tpr ]]; then
    END_PS=$(awk -v c="$CUR0" 'BEGIN{printf "%.3f", c*1000}')
    log "09 trjconv dump ${END_PS} ps → md.gro (post-hoc finalize)"
    echo 0 | gmx trjconv -s md.tpr -f md.xtc -o md.gro -dump "$END_PS" \
      > trjconv_final_gro.log 2>&1 || true
  fi
fi

# ---- 10 PBC 校正 + 分析（默认组：Backbone/C-alpha/Protein/$LIGAND_RES） ----
if [[ ! -f md_center.xtc ]]; then
  log "10 trjconv PBC 校正"
  printf 'Protein\nSystem\n' | gmx trjconv -s md.tpr -f md.xtc -o md_center.xtc \
      -pbc mol -center -ur compact > trjconv.log 2>&1
fi
log "10 RMSD/RMSF/氢键/回旋半径"
printf 'Backbone\nBackbone\n' | gmx rms -s md.tpr -f md_center.xtc \
    -o rmsd_backbone.xvg -tu ns > rms.log 2>&1 || true
printf 'C-alpha\n' | gmx rmsf -s md.tpr -f md_center.xtc \
    -o rmsf_calpha.xvg -res > rmsf.log 2>&1 || true
# GROMACS 2024+ 新 hbond 对 GAFF 配体常失败；优先 legacy
if ! printf "Protein\n$LIGAND_RES\n" | gmx hbond-legacy -s md.tpr -f md_center.xtc \
    -num hbond_num.xvg > hbond.log 2>&1; then
  printf "Protein\n$LIGAND_RES\n" | gmx hbond -s md.tpr -f md_center.xtc \
      -num hbond_num.xvg >> hbond.log 2>&1 || true
fi
printf 'Protein\n' | gmx gyrate -s md.tpr -f md_center.xtc \
    -o gyrate.xvg > gyrate.log 2>&1 || true

# 10b 绘图数据导出（2026-10-14 挂接：此前只算 4 项速检，SASA/COM/平衡曲线与
# Origin CSV 靠归档前手动补算，导致"跑完了没有绘图数据"。幂等；失败不撤销 DONE）。
if [[ "${EXPORT_FIG_DATA:-1}" == "1" ]]; then
  log "10b 补算+导出绘图数据（SASA/COM/三线RMSD/平衡曲线 → Origin CSV）"
  bash "$SCRIPT_DIR/补算必备分析_extraMdAnalysis.sh" >> extra_analysis.log 2>&1 \
    || log "WARN 补算必备分析失败 — see extra_analysis.log"
  PYBIN="$HOME/md-venv/bin/python3"; [[ -x "$PYBIN" ]] || PYBIN=python3
  if [[ -d /mnt/e/Origin_Data ]]; then
    "$PYBIN" "$SCRIPT_DIR/导出Origin数据_exportMdOriginCsv.py" \
      --work "$WORK_DIR" --project "$(basename "$WORK_DIR")" \
      --origin-root /mnt/e/Origin_Data >> export_csv.log 2>&1 \
      || log "WARN Origin CSV 导出失败 — see export_csv.log"
    log "10b CSV → /mnt/e/Origin_Data/$(basename "$WORK_DIR")/（Origin 本机绘图另跑 origin出图_plotMdOrigin.py）"
  else
    log "10b 跳过 CSV 导出（无 /mnt/e/Origin_Data；Windows 直跑 导出Origin数据_exportMdOriginCsv.py）"
  fi
fi

# 可选终检（不改生产轨迹；失败只记日志，不撤销 DONE）
if [[ "$MONITOR" == "1" && -f md.xtc ]]; then
  log "10 final monitor on full trajectory"
  LIGAND_RES="$LIGAND_RES" CHECK_MMGBSA="$CHECK_MMGBSA" \
    bash "$SCRIPT_DIR/过程监控_monitorMdRun.sh" . \
    && log "10 final MONITOR_OK" \
    || log "WARN final monitor exit=$? — see monitor/ABORT_REASON.txt"
fi

FINAL_NS=$(done_ns); FINAL_NS=${FINAL_NS:-$CUR0}
{
  echo "DONE: production ${FINAL_NS} ns (target ${NS} ns); GMX_MAXBACKUP=$GMX_MAXBACKUP"
  date -Iseconds
  ls *.xvg 2>/dev/null | tr '\n' ' '
  echo
} | tee DONE.txt
log "DONE: $(ls *.xvg 2>/dev/null | tr '\n' ' ')"
log "样例归档（分类目录+中英对照）: python 整理样例目录_layoutMdSample.py"
