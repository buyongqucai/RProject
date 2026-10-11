#!/bin/bash
set -euo pipefail
source ~/activate-md.sh
export FORCE_EXTRA=1
bash /mnt/e/md_kit/run_extra_then_export.sh /home/ywy/md_runs/MMP9_Tryptophan_4H3X LIG MMP9_Tryptophan_4H3X
bash /mnt/e/md_kit/run_extra_then_export.sh /home/ywy/md_runs/ADA_Adenosine_7RTG_A2 LIG ADA_Adenosine_7RTG_A2
echo ALL_EXTRA_DONE
