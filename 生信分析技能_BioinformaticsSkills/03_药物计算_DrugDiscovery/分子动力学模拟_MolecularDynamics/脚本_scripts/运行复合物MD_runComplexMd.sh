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
#   NS=1                生产时长 ns(演示 1；正式研究 50–100)
#   CHUNK_NS=1          生产分块长度 ns（块间过程监控；断点 -cpi 续跑）
#   MONITOR=1           1=每块结束后跑 过程监控_monitorMdRun.sh；异常 exit 2 即停
#   CHECK_MMGBSA=0      传给监控：1=按间隔抽查 MM-GBSA，ΔG>0 即停
#   COFACTORS_PDB=      可选；ZN/CA 等 HETATM（§9.10.3 非键合 +2，晶体坐标）
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
NS=${NS:-1}
CHUNK_NS=${CHUNK_NS:-1}
MONITOR=${MONITOR:-1}
CHECK_MMGBSA=${CHECK_MMGBSA:-0}
COFACTORS_PDB=${COFACTORS_PDB:-}
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
MDP_DIR=${MDP_DIR:-"$SCRIPT_DIR/mdp模板_mdps"}
ACPYPE_BIN=${ACPYPE_BIN:-$HOME/md-venv/bin}
# UV acpype first; AmberTools (conda md-tools) + GPU gmx must already be on PATH via ~/activate-md.sh
export PATH="$ACPYPE_BIN:$HOME/gromacs-gpu/bin:$PATH"
NDX_ARG=()   # 有金属时填 -n index.ndx，使 ZN/CA 并入 Water_and_ions 温控组

log(){ echo "[$(date +%H:%M:%S)] $*"; }
cd "$WORK_DIR"

# ---- 01 配体 GAFF2 拓扑(acpype → antechamber AM1-BCC + parmchk2) ----
if [[ ! -f ligand.acpype/ligand_GMX.itp ]]; then
  log "01 acpype 配体拓扑 (GAFF2, 净电荷 $NET_CHARGE)"
  rm -rf ligand.acpype acpype_tmp.mol2
  cp "$LIGAND_MOL2" acpype_tmp.mol2
  acpype -i acpype_tmp.mol2 -n "$NET_CHARGE" -a gaff2 -o gmx -b ligand > acpype.log 2>&1
  rm -f acpype_tmp.mol2
fi
LIG_ITP=ligand.acpype/ligand_GMX.itp
LIG_GRO=ligand.acpype/ligand_GMX.gro
[[ -f $LIG_ITP && -f $LIG_GRO ]] || { log "FAIL: acpype 未产出 $LIG_ITP"; exit 1; }
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
  log "02 pdb2gmx 蛋白拓扑 (amber99sb-ildn/tip3p)"
  gmx pdb2gmx -f "$PROTEIN_PDB" -o protein.gro -p topol.top -i posre.itp \
      -ff amber99sb-ildn -water tip3p -ignh > pdb2gmx.log 2>&1
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

# ---- 04 盒子 + 溶剂化 + 离子 ----
if [[ ! -f solv_ions.gro ]]; then
  log "04 editconf/solvate/genion (0.15 M NaCl 中和)"
  # 防重入：solvate/genion 会向 topol.top 追加 SOL/NA/CL 行，重跑前剔除旧行
  sed -i '/^SOL[ \t]/d; /^NA[ \t]/d; /^CL[ \t]/d' topol.top
  gmx editconf -f complex.gro -o newbox.gro -bt dodecahedron -d 1.0 > editconf.log 2>&1
  gmx solvate -cp newbox.gro -cs spc216 -p topol.top -o solv.gro > solvate.log 2>&1
  # -maxwarn 1: 加离子前体系净电荷非零是预期状态（genion 随即中和），仅此步放行该警告
  gmx grompp -f "$MDP_DIR/ions.mdp" -c solv.gro -p topol.top -o ions.tpr -maxwarn 1 > grompp_ions.log 2>&1
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

# ---- 05 能量最小化 ----
if [[ ! -f em.gro ]]; then
  log "05 能量最小化"
  gmx grompp -f "$MDP_DIR/em.mdp" -c solv_ions.gro -p topol.top -o em.tpr \
      "${NDX_ARG[@]}" > grompp_em.log 2>&1
  gmx mdrun -v -deffnm em > mdrun_em.log 2>&1
fi

# ---- 06 渲染 mdp 模板（__LIG__ → 实际配体残基名；温控/分析全用默认组，免索引文件） ----
for m in nvt npt md; do
  sed "s/__LIG__/$LIGAND_RES/g" "$MDP_DIR/$m.mdp" > "run_$m.mdp"
done

# ---- 07 NVT ----
if [[ ! -f nvt.gro ]]; then
  log "07 NVT 100 ps"
  gmx grompp -f run_nvt.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr \
      "${NDX_ARG[@]}" > grompp_nvt.log 2>&1
  gmx mdrun -v -deffnm nvt > mdrun_nvt.log 2>&1
fi

# ---- 08 NPT ----
if [[ ! -f npt.gro ]]; then
  log "08 NPT 100 ps"
  gmx grompp -f run_npt.mdp -c nvt.gro -r nvt.gro -t nvt.cpt -p topol.top -o npt.tpr \
      "${NDX_ARG[@]}" > grompp_npt.log 2>&1
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
        "${NDX_ARG[@]}" > grompp_md.log 2>&1
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
    if [[ -f md.cpt ]]; then
      gmx mdrun -v -deffnm md -cpi md.cpt -cpo md.cpt -nsteps "$REMAIN_STEPS" \
        >> mdrun_md.log 2>&1
    else
      gmx mdrun -v -deffnm md -cpo md.cpt -nsteps "$REMAIN_STEPS" \
        >> mdrun_md.log 2>&1
    fi
    if [[ "$MONITOR" == "1" ]]; then
      log "09 monitor after chunk"
      LIGAND_RES="$LIGAND_RES" CHECK_MMGBSA="$CHECK_MMGBSA" \
        bash "$SCRIPT_DIR/过程监控_monitorMdRun.sh" . || {
          RC=$?
          log "ABORT monitor exit=$RC — see monitor/ABORT_REASON.txt (fix with md.cpt)"
          exit "$RC"
        }
    fi
  done
  if [[ ! -f md.gro && -f md.cpt ]]; then
    gmx mdrun -v -deffnm md -cpi md.cpt -cpo md.cpt -nsteps 0 >> mdrun_md.log 2>&1 || true
  fi
else
  log "09 生产已满 ${CUR0} ns >= ${NS} ns，跳过"
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
printf "Protein\n$LIGAND_RES\n" | gmx hbond -s md.tpr -f md_center.xtc \
    -num hbond_num.xvg > hbond.log 2>&1 || true
printf 'Protein\n' | gmx gyrate -s md.tpr -f md_center.xtc \
    -o gyrate.xvg > gyrate.log 2>&1 || true

log "DONE: $(ls *.xvg 2>/dev/null | tr '\n' ' ')"
log "样例归档（分类目录+中英对照）: python 整理样例目录_layoutMdSample.py"
