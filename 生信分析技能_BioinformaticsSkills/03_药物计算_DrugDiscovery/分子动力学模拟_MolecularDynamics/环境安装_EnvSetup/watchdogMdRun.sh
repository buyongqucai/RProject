#!/usr/bin/env bash
# MD-WATCHDOG-v1 — process/progress watchdog (parallel to chunk physics monitor).
# Spec: 文档_docs/过程看门狗_MdWatchdog.md
# Usage:
#   bash watchdogMdRun.sh WORKDIR [--target-ns 100] [--poll-sec 120] [--stall-min 20] [--pid-file PATH]
set -u
export LANG=C.UTF-8 LC_ALL=C.UTF-8

WORKDIR=""
TARGET_NS="${TARGET_NS:-100}"
POLL_SEC="${POLL_SEC:-120}"
STALL_MIN="${STALL_MIN:-20}"
PID_FILE="${PID_FILE:-}"
SUCCESS_MAIL="${SUCCESS_MAIL:-0}"
MD_ALERT_SH="${MD_ALERT_SH:-/mnt/e/md_kit/notify_md_alert.sh}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-ns) TARGET_NS="$2"; shift 2 ;;
    --poll-sec) POLL_SEC="$2"; shift 2 ;;
    --stall-min) STALL_MIN="$2"; shift 2 ;;
    --pid-file) PID_FILE="$2"; shift 2 ;;
    --success-mail) SUCCESS_MAIL=1; shift ;;
    -*)
      echo "unknown arg: $1" >&2
      exit 1
      ;;
    *)
      if [[ -z "$WORKDIR" ]]; then WORKDIR="$1"; else echo "extra arg: $1" >&2; exit 1; fi
      shift
      ;;
  esac
done

WORKDIR="${WORKDIR:?need WORKDIR}"
WORKDIR="$(cd "$WORKDIR" && pwd)"
MON="$WORKDIR/monitor"
mkdir -p "$MON" "${HOME}/md_runs/logs"
HB="$MON/heartbeat.json"
WLOG="${HOME}/md_runs/logs/watchdog_$(basename "$WORKDIR").log"

log(){ echo "[$(date '+%F %T')] $*" | tee -a "$WLOG"; }

alert() {
  local reason="$1"
  if [[ -f "$MD_ALERT_SH" ]]; then
    bash "$MD_ALERT_SH" "$reason" "$WORKDIR" || log "WARN alert send failed"
  else
    log "WARN no notify script: $MD_ALERT_SH"
  fi
}

# last Time column (ps) from md.log
read_time_ps() {
  python3 - "$WORKDIR/md.log" <<'PY' 2>/dev/null || echo ""
import sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.is_file():
    print(""); raise SystemExit
t = None
for line in p.read_text(errors="replace").splitlines():
    parts = line.split()
    if len(parts) >= 2:
        try:
            int(parts[0]); t = float(parts[1])
        except ValueError:
            pass
print("" if t is None else f"{t}")
PY
}

mdrun_alive() {
  # any gmx mdrun; refine by open cwd if possible
  if pgrep -f "gmx mdrun" >/dev/null 2>&1; then
    return 0
  fi
  # shell pipeline still wrapping
  if pgrep -f "运行复合物MD_runComplexMd.sh.*$(basename "$WORKDIR")" >/dev/null 2>&1; then
    return 0
  fi
  if pgrep -f "runComplexMd.sh.*$(basename "$WORKDIR")" >/dev/null 2>&1; then
    return 0
  fi
  if [[ -n "$PID_FILE" && -f "$PID_FILE" ]]; then
    local pid
    pid="$(tr -d ' \r\n' < "$PID_FILE" || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  fi
  return 1
}

classify_death() {
  if [[ -f "$MON/ABORT_REASON.txt" ]]; then
    echo "WATCHDOG_DEAD_MONITOR $(head -n1 "$MON/ABORT_REASON.txt")"
    return
  fi
  if grep -qiE 'Won.?t make more than .* backups of md\.gro|GMX_MAXBACKUP' \
      "$WORKDIR/mdrun_md.log" "$WORKDIR/md.log" 2>/dev/null; then
    echo "WATCHDOG_DEAD_BACKUP GMX_MAXBACKUP/md.gro backup Fatal (cpt often OK; resume with GMX_MAXBACKUP=-1)"
    return
  fi
  if grep -qiE 'Fatal error|Segmentation fault' "$WORKDIR/mdrun_md.log" "$WORKDIR/md.log" 2>/dev/null; then
    local snip
    snip="$(grep -iE 'Fatal error|Won.?t make|Segmentation' "$WORKDIR/mdrun_md.log" 2>/dev/null | tail -n3 | tr '\n' ' ')"
    echo "WATCHDOG_DEAD_MDRUN ${snip:-see mdrun_md.log}"
    return
  fi
  echo "WATCHDOG_DEAD_UNKNOWN process gone before target; see mdrun_md.log / pipeline log"
}

write_hb() {
  local state="$1" ns="$2" detail="$3"
  local alive=0
  mdrun_alive && alive=1
  python3 - "$HB" "$state" "$ns" "$alive" "$TARGET_NS" "$detail" <<'PY'
import json, sys
from datetime import datetime, timezone
path, state, ns, alive, target, detail = sys.argv[1:7]
try:
    ns_f = float(ns) if ns not in ("", "None") else None
except ValueError:
    ns_f = None
obj = {
    "watchdog": "MD-WATCHDOG-v1",
    "state": state,
    "alive": bool(int(alive)),
    "done_ns": ns_f,
    "target_ns": float(target),
    "detail": detail,
    "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
}
open(path, "w", encoding="utf-8").write(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
PY
}

is_complete() {
  local ns_ps="$1"
  if [[ -f "$WORKDIR/DONE.txt" ]]; then
    if grep -qE 'DONE: production' "$WORKDIR/DONE.txt" 2>/dev/null; then
      return 0
    fi
  fi
  if [[ -n "$ns_ps" ]]; then
    python3 - "$ns_ps" "$TARGET_NS" <<'PY'
import sys
ps, tgt = float(sys.argv[1]), float(sys.argv[2])
raise SystemExit(0 if ps/1000.0 >= tgt * 0.99 else 1)
PY
    return $?
  fi
  return 1
}

log "START MD-WATCHDOG-v1 workdir=$WORKDIR target=${TARGET_NS}ns poll=${POLL_SEC}s stall=${STALL_MIN}min"
LAST_PS=""
LAST_PROGRESS_EPOCH="$(date +%s)"

while true; do
  PS_NOW="$(read_time_ps)"
  NS_NOW=""
  if [[ -n "$PS_NOW" ]]; then
    NS_NOW="$(python3 -c "print('{:.6f}'.format(float('$PS_NOW')/1000.0))")"
  fi

  if is_complete "$PS_NOW"; then
    write_hb "COMPLETE" "${NS_NOW:-}" "target reached or DONE.txt"
    log "COMPLETE done_ns=${NS_NOW:-?} target=$TARGET_NS"
    if [[ "$SUCCESS_MAIL" == "1" ]]; then
      alert "WATCHDOG_COMPLETE reached ~${NS_NOW:-?} ns (target $TARGET_NS)"
    fi
    exit 0
  fi

  if mdrun_alive; then
    if [[ -n "$PS_NOW" ]]; then
      if [[ "$PS_NOW" != "$LAST_PS" ]]; then
        LAST_PS="$PS_NOW"
        LAST_PROGRESS_EPOCH="$(date +%s)"
      fi
    fi
    NOW_E="$(date +%s)"
    STALL_SEC=$((STALL_MIN * 60))
    if [[ -n "$LAST_PS" ]] && (( NOW_E - LAST_PROGRESS_EPOCH >= STALL_SEC )); then
      write_hb "STALLED" "${NS_NOW:-}" "no Time advance for ${STALL_MIN} min"
      alert "WATCHDOG_STALLED no md.log Time advance for ${STALL_MIN} min (last ~${NS_NOW:-?} ns)"
      # keep watching; may recover
      LAST_PROGRESS_EPOCH="$NOW_E"
    else
      write_hb "RUNNING" "${NS_NOW:-}" "mdrun alive"
    fi
  else
    # dead / between chunks: short grace — chunk monitor gap can be ~1–3 min without mdrun
    write_hb "CHECKING" "${NS_NOW:-}" "no mdrun this poll; grace/recheck"
    sleep 90
    PS_NOW="$(read_time_ps)"
    NS_NOW=""
    if [[ -n "$PS_NOW" ]]; then
      NS_NOW="$(python3 -c "print('{:.6f}'.format(float('$PS_NOW')/1000.0))")"
    fi
    if is_complete "$PS_NOW"; then
      write_hb "COMPLETE" "${NS_NOW:-}" "complete after grace"
      log "COMPLETE after grace"
      exit 0
    fi
    if mdrun_alive; then
      write_hb "RUNNING" "${NS_NOW:-}" "mdrun back after grace"
      LAST_PROGRESS_EPOCH="$(date +%s)"
      sleep "$POLL_SEC"
      continue
    fi
    REASON="$(classify_death)"
    write_hb "DEAD_ERROR" "${NS_NOW:-}" "$REASON"
    log "DEAD_ERROR $REASON"
    alert "$REASON"
    exit 1
  fi

  sleep "$POLL_SEC"
done
