#!/usr/bin/env bash
# MD monitor abort → global alert_kit (QQ SMTP).
# Canonical runtime: E:\md_kit\notify_md_alert.sh
# Auth via E:\alert_kit\qq_auth_path.txt. Failures are logged.
set -u
REASON="${1:-MD monitor abort}"
WORKDIR="${2:-$(pwd)}"
TO_FILE=""
if [[ -s "${HOME}/.md_alert_to" ]]; then
  TO_FILE="${HOME}/.md_alert_to"
elif [[ -s "${HOME}/.alert_to" ]]; then
  TO_FILE="${HOME}/.alert_to"
fi
LOG="${HOME}/md_runs/logs/alert.log"
mkdir -p "${HOME}/md_runs/logs"
STAMP="$WORKDIR/monitor/ALERT_SENT.txt"
mkdir -p "$WORKDIR/monitor"
if [[ -f "$STAMP" ]] && grep -Fxq "$REASON" "$STAMP"; then
  echo "$(date '+%F %T') skip duplicate" >> "$LOG"
  exit 0
fi
BODY="$WORKDIR/monitor/alert_body.txt"
{
  echo "分子动力学监控异常，模拟已停止。"
  echo
  echo "时间: $(date '+%F %T %z')"
  echo "目录: $WORKDIR"
  echo "原因:"
  echo "$REASON"
  echo
  if [[ -f "$WORKDIR/md.log" ]]; then
    python3 - "$WORKDIR/md.log" <<'PY'
import sys
from pathlib import Path
t = None
for line in Path(sys.argv[1]).read_text(errors="replace").splitlines():
    parts = line.split()
    if len(parts) >= 2:
        try:
            int(parts[0]); t = float(parts[1])
        except ValueError:
            pass
if t is not None:
    print(f"轨迹时间: {t/1000:.3f} ns")
PY
  fi
  echo
  echo "日志: ${HOME}/md_runs/logs/"
  echo "续跑前请先看 monitor/ABORT_REASON.txt，不要删 md.cpt。"
} > "$BODY"
SUBJ="MD监控异常 $(basename "$WORKDIR")"
export ALERT_LOG="$LOG"
export ALERT_DEDUP_FILE="$STAMP"
NOTIFY="${ALERT_KIT_SH:-/mnt/e/alert_kit/notify_alert.sh}"
chmod +x "$NOTIFY" 2>/dev/null || true
ARGS=(-s "$SUBJ" -f "$BODY" -k "$REASON")
if [[ -n "$TO_FILE" ]]; then
  TO="$(tr -d '\r' < "$TO_FILE" | head -n1)"
  ARGS+=(-t "$TO")
fi
if "$NOTIFY" "${ARGS[@]}"; then
  exit 0
fi
echo "$(date '+%F %T') send failed via alert_kit" >> "$LOG"
exit 1
