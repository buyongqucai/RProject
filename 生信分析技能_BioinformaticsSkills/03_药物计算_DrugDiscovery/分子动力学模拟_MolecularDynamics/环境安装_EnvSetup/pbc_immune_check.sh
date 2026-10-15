#!/usr/bin/env bash
# PBC-免疫指标验证：逐链自RMSD + 配体自RMSD + 蛋白-配体最小镜像距离
set -u
source ~/activate-md.sh
OUT=/home/ywy/pbcchk
mkdir -p "$OUT"
for d in FOS_quercetin_1A02 PPARG_kaempferol_1FM9 ESR2_Anhydroicaritin_1L2J; do
  echo "=== $d ==="
  cd ~/md_runs/$d || continue
  printf 'System\n' | gmx trjconv -s md.tpr -f md.xtc -o "$OUT/${d}_whole.xtc" -pbc mol > "$OUT/${d}_whole.log" 2>&1
  [[ -s "$OUT/${d}_whole.xtc" ]] || { echo "whole FAIL"; continue; }
  printf 'splitch\nq\n' | gmx make_ndx -f md.tpr -o "$OUT/${d}_chains.ndx" > /dev/null 2>&1
  # 每条链自RMSD（链=单分子，-pbc mol 后完整；量纲=链内部形变）
  for g in $(grep '^\[' "$OUT/${d}_chains.ndx" | sed 's/\[//;s/\]//' | grep -i 'chain' | sed 's/^ *//;s/ *$//'); do
    printf '%s\n%s\n' "$g" "$g" | gmx rms -s md.tpr -f "$OUT/${d}_whole.xtc" -n "$OUT/${d}_chains.ndx" \
      -o "$OUT/${d}_$(echo $g | tr -cd 'A-Za-z0-9_').xvg" -tu ns > /dev/null 2>&1
    f="$OUT/${d}_$(echo $g | tr -cd 'A-Za-z0-9_').xvg"
    if [[ -s "$f" ]]; then
      echo -n "  $g self-RMSD max nm: "
      grep -v "^[@#]" "$f" | awk '{if($2>m)m=$2}END{printf "%.3f\n", m}'
    else
      echo "  $g rms FAILED"
    fi
  done
  printf 'LIG\nLIG\n' | gmx rms -s md.tpr -f "$OUT/${d}_whole.xtc" -o "$OUT/${d}_ligself.xvg" -tu ns > /dev/null 2>&1
  echo -n "  LIG self-RMSD max nm: "
  grep -v "^[@#]" "$OUT/${d}_ligself.xvg" | awk '{if($2>m)m=$2}END{printf "%.3f\n", m}'
  printf 'Protein\nLIG\n' | gmx mindist -s md.tpr -f md.xtc -od "$OUT/${d}_mindist2.xvg" > /dev/null 2>&1
  echo -n "  protein-ligand mindist range nm: "
  grep -v "^[@#]" "$OUT/${d}_mindist2.xvg" | awk 'NR==1{mn=$2;mx=$2}{if($2<mn)mn=$2;if($2>mx)mx=$2}END{printf "%.3f %.3f\n", mn, mx}'
done