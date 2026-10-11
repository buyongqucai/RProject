#!/usr/bin/env bash
set -euo pipefail
WORK=${1:?work dir}
LIGAND_RES=${2:-LIG}
PROJECT=${3:-$(basename "$WORK")}
export PATH="${HOME}/md-venv/bin:${HOME}/gromacs-gpu/bin:${PATH}"
export LIGAND_RES
WIN_PY='E:\Python3.13.14\python.exe'
EXPORT_PY_WIN='E:\md_kit\exportMdOriginCsv.py'
cd "$WORK"
source ~/activate-md.sh
if [[ "${FORCE_EXTRA:-0}" == "1" ]]; then
  rm -f rmsd_complex.xvg hbond_num.xvg
fi
bash /mnt/e/md_kit/extraMdAnalysis.sh
if [[ ! -s sasa.xvg ]]; then
  printf "Protein\n" | gmx sasa -s md.tpr -f md_center.xtc -o sasa.xvg -tu ns > sasa.log 2>&1 || true
fi
MISSING=0
for f in rmsd_protein.xvg rmsd_ligand.xvg rmsd_complex.xvg rmsd_backbone.xvg gyrate.xvg sasa.xvg com_distance.xvg; do
  if [[ ! -s "$f" ]]; then echo "ERROR: required analysis missing: $f" >&2; MISSING=1; fi
done
if [[ ! -s hbond_num.xvg ]]; then echo "WARN: hbond_num.xvg missing" >&2; fi
if [[ "$MISSING" -ne 0 ]]; then echo "EXTRA_EXPORT_ABORT $PROJECT" >&2; exit 2; fi
WORK_WIN="$(wslpath -w "$WORK")"
powershell.exe -NoProfile -Command \
  "& '${WIN_PY}' '${EXPORT_PY_WIN}' --work '${WORK_WIN}' --project '${PROJECT}' --origin-root 'E:\Origin_Data'"
echo EXTRA_EXPORT_DONE "$PROJECT"
