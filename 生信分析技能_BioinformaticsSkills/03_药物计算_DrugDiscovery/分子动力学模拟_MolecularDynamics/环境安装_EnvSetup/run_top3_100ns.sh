#!/usr/bin/env bash
# Launch UC top3 MD (metal pairs). CYP1A1/HEME skipped until Shahrokh params ready.
set -euo pipefail
source ~/activate-md.sh
SCRIPT=$(find /mnt/e/RProject -name '运行复合物MD_runComplexMd.sh' 2>/dev/null | head -1)
TOP3=$(find /mnt/e/RProject -type d -name '课题top3输入' 2>/dev/null | head -1)
echo SCRIPT="$SCRIPT"
echo TOP3="$TOP3"
test -f "$SCRIPT" && test -d "$TOP3"
OUT="$HOME/md_runs"
mkdir -p "$OUT" "$OUT/logs"

run_pair() {
  local name="$1" cof="$2"
  local src="$TOP3/$name"
  local wd="$OUT/$name"
  echo "===== PREP $name ====="
  mkdir -p "$wd"
  # keep resume files if production already started
  if [[ ! -f "$wd/protein.pdb" ]]; then
    cp "$src/protein.pdb" "$src/lig_h.mol2" "$src/$cof" "$wd/"
  fi
  cd "$wd"
  export LIGAND_RES=LIG NET_CHARGE=0
  export NS=100 CHUNK_NS=1 MONITOR=1 CHECK_MMGBSA=0
  export COFACTORS_PDB="$wd/$cof"
  nohup bash "$SCRIPT" "$wd" "$wd/protein.pdb" "$wd/lig_h.mol2" \
    > "$OUT/logs/${name}.log" 2>&1 &
  echo "$name PID=$! log=$OUT/logs/${name}.log"
}

# Sequential GPU: start ADA; MMP9 after ADA finishes (caller can re-invoke)
PAIR="${1:-ADA_Adenosine_7RTG}"
case "$PAIR" in
  ADA_Adenosine_7RTG) run_pair ADA_Adenosine_7RTG cofactors_ZN.pdb ;;
  MMP9_Tryptophan_4H3X) run_pair MMP9_Tryptophan_4H3X cofactors_ZN_CA.pdb ;;
  *) echo "unknown pair $PAIR"; exit 1 ;;
esac
echo "tail -f $OUT/logs/${PAIR}.log"
