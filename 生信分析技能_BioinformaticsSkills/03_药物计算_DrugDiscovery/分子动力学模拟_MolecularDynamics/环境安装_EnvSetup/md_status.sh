#!/usr/bin/env bash
# One-shot status for MD-WATCHDOG-v1 heartbeat + process.
# Usage: bash md_status.sh WORKDIR
set -u
WORKDIR="${1:?need WORKDIR}"
WORKDIR="$(cd "$WORKDIR" && pwd)"
HB="$WORKDIR/monitor/heartbeat.json"
echo "WORKDIR=$WORKDIR"
if [[ -f "$HB" ]]; then
  echo "--- heartbeat.json ---"
  cat "$HB"
else
  echo "heartbeat: (none yet)"
fi
echo "--- process ---"
if pgrep -af "gmx mdrun" 2>/dev/null | head -n5; then
  :
else
  echo "no gmx mdrun"
fi
if [[ -f "$WORKDIR/DONE.txt" ]]; then
  echo "--- DONE.txt ---"
  head -n5 "$WORKDIR/DONE.txt"
fi
if [[ -f "$WORKDIR/monitor/ABORT_REASON.txt" ]]; then
  echo "--- ABORT_REASON ---"
  cat "$WORKDIR/monitor/ABORT_REASON.txt"
fi
