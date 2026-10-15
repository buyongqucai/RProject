#!/usr/bin/env bash
# Launch Top3 MD queue in background (safe from pgrep self-match).
set -euo pipefail
mkdir -p "$HOME/md_runs/logs"
LOG="$HOME/md_runs/logs/queue_nuli_top3.log"
# kill only real queue PIDs (exact script path as argv)
while read -r pid; do
  [[ -n "$pid" ]] || continue
  cmd=$(ps -p "$pid" -o args= 2>/dev/null || true)
  case "$cmd" in
    *"/mnt/e/md_kit/queue_nuli_top3_md.sh"*) kill "$pid" 2>/dev/null || true ;;
  esac
done < <(pgrep -f '/mnt/e/md_kit/queue_nuli_top3_md.sh' || true)
sleep 1
nohup bash /mnt/e/md_kit/queue_nuli_top3_md.sh >>"$LOG" 2>&1 &
echo "QUEUE_PID=$!"
sleep 55
echo "===QUEUE_TAIL==="
tail -n 80 "$LOG"
echo "===PROCS==="
ps -eo pid,etime,cmd | grep -E 'queue_nuli_top3_md|rebuildPose|运行复合物MD|gmx |mdrun|acpype|pdb2gmx|pdbfixer' | grep -v grep || echo none
