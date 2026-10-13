#!/usr/bin/env bash
# MD 异常 → 中文纯文本告警（alert_kit / QQ SMTP）
# 用法：
#   bash notify_md_alert.sh <工作目录> 
#     读取 monitor/alert_context.json（若有）+ ABORT_REASON.txt 生成正文
#   bash notify_md_alert.sh <工作目录> --phase final|will_retry|no_retry
# 兼容旧调用：bash notify_md_alert.sh "<reason>" "<workdir>"
set -u

PHASE="final"
WORKDIR=""
REASON_OVERRIDE=""

if [[ "${1:-}" == /* || "${1:-}" == [A-Za-z]:* || -d "${1:-}" ]]; then
  WORKDIR="${1}"
  shift || true
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --phase) PHASE="${2:-final}"; shift 2 ;;
      *) REASON_OVERRIDE="$1"; shift ;;
    esac
  done
else
  # legacy: reason workdir
  REASON_OVERRIDE="${1:-MD monitor abort}"
  WORKDIR="${2:-$(pwd)}"
fi

TO_FILE=""
if [[ -s "${HOME}/.md_alert_to" ]]; then
  TO_FILE="${HOME}/.md_alert_to"
elif [[ -s "${HOME}/.alert_to" ]]; then
  TO_FILE="${HOME}/.alert_to"
fi
LOG="${HOME}/md_runs/logs/alert.log"
mkdir -p "${HOME}/md_runs/logs" "$WORKDIR/monitor"

# 中文翻译常见英文监控句
REASON_RAW="${REASON_OVERRIDE:-}"
if [[ -z "$REASON_RAW" && -f "$WORKDIR/monitor/ABORT_REASON.txt" ]]; then
  REASON_RAW="$(cat "$WORKDIR/monitor/ABORT_REASON.txt")"
fi
REASON_ZH="$(
python3 - "$REASON_RAW" <<'PY'
import sys
t = sys.argv[1] if len(sys.argv) > 1 else ""
repl = [
    ("backbone RMSD max", "骨架 RMSD 最大值"),
    ("ligand RMSD max", "配体 RMSD 最大值"),
    ("COM distance max", "蛋白–配体质心距离最大值"),
    ("COM jump", "质心距离相对首帧突增"),
    ("possible unfold", "可疑展开"),
    ("ligand fly/dissociate", "配体飞散/解离"),
    ("receptor-ligand separation", "受体–配体分离"),
    ("md.log after Started mdrun contains NaN/Fatal", "生产段日志出现 NaN/Fatal"),
    ("pipeline exit=", "流水线退出码="),
    ("protein repair (pdbfixer) failed", "蛋白补原子（pdbfixer）失败"),
    ("protein gap gate failed", "蛋白主链缺口门禁未通过"),
    ("ligand mol2 geometry failed", "配体 mol2 几何门禁未通过"),
    ("pose contact failed", "蛋白–配体接触门禁未通过"),
    ("EM did not converge", "能量最小化未收敛"),
    ("grompp ions failed", "加离子前 grompp 失败"),
    ("pdb2gmx failed", "pdb2gmx 失败"),
]
for a, b in repl:
    t = t.replace(a, b)
print(t.strip() or "（未写明原因，请查看 monitor/ABORT_REASON.txt）")
PY
)"

CTX="$WORKDIR/monitor/alert_context.json"
BODY="$WORKDIR/monitor/alert_body.txt"
NAME="$(basename "$WORKDIR")"

python3 - "$BODY" "$WORKDIR" "$NAME" "$PHASE" "$REASON_ZH" "$CTX" <<'PY'
import json, sys
from pathlib import Path
body, wd, name, phase, reason_zh, ctxp = sys.argv[1:7]
ctx = {}
p = Path(ctxp)
if p.is_file():
    try:
        ctx = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        ctx = {}

attempted = ctx.get("auto_rebuild_attempted")
ok = ctx.get("auto_rebuild_ok")
will_retry = ctx.get("will_retry")
will_more = ctx.get("will_retry_again")
chosen = ctx.get("chosen_pdb")
rebuild_zh = ctx.get("rebuild_reason_zh") or ctx.get("reason_zh") or ""
orig = ctx.get("original_system") or name

def yn(v):
    if v is True: return "是"
    if v is False: return "否"
    return "未记录"

lines = []
lines.append("【分子动力学异常通知】")
lines.append("")
lines.append(f"体系目录：{name}")
lines.append(f"完整路径：{wd}")
lines.append("")
lines.append("一、异常停止原因（中文）")
for row in str(reason_zh).splitlines() or ["（无）"]:
    lines.append(f"  {row}")
lines.append("")
lines.append("二、自动重搭（共晶/近缘/无大段缺环结构）")
lines.append(f"  是否已进行自动重搭：{yn(attempted)}")
if attempted is True:
    lines.append(f"  自动重搭是否成功生成新初态：{yn(ok)}")
    if chosen:
        lines.append(f"  选用替代 PDB：{chosen}")
    if rebuild_zh:
        lines.append(f"  重搭说明：{rebuild_zh}")
lines.append(f"  本轮是否还会启动重试生产：{yn(will_retry)}")
lines.append(f"  之后是否还会再自动重试：{yn(will_more if will_more is not None else False)}")
lines.append("")
lines.append("三、处理规则")
lines.append("  · 对接姿态（A3）飞散后，最多自动重搭并重跑 1 轮。")
lines.append("  · 不从飞散后的 md.cpt 续跑同一对接初态。")
lines.append("  · 一轮后仍失败则停止，等待人工换结构/换姿态。")
lines.append("")
if phase == "will_retry":
    lines.append("四、当前状态：即将开始第 1 轮自动重搭后的生产 MD。")
elif phase == "no_retry":
    lines.append("四、当前状态：无法自动重搭或规则不允许重试，任务停止。")
else:
    lines.append("四、当前状态：流程已停止（见上）。")
lines.append("")
lines.append("请查看 monitor/ABORT_REASON.txt 与 logs/。保留 md.cpt 作对照，勿直接续跑。")
Path(body).write_text("\n".join(lines) + "\n", encoding="utf-8")
print(Path(body).read_text(encoding="utf-8"))
PY

case "$PHASE" in
  will_retry) SUBJ="MD将自动重搭一轮 ${NAME}" ;;
  no_retry)   SUBJ="MD已停止（无法/不再重试） ${NAME}" ;;
  *)          SUBJ="MD异常停止 ${NAME}" ;;
esac

DEDUP_KEY="${PHASE}|${NAME}|$(echo "$REASON_ZH" | tr '\n' ' ' | head -c 160)"
STAMP="$WORKDIR/monitor/ALERT_SENT.txt"
export ALERT_LOG="$LOG"
export ALERT_DEDUP_FILE="$STAMP"
NOTIFY="${ALERT_KIT_SH:-/mnt/e/alert_kit/notify_alert.sh}"
chmod +x "$NOTIFY" 2>/dev/null || true
ARGS=(-s "$SUBJ" -f "$BODY" -k "$DEDUP_KEY")
if [[ -n "$TO_FILE" ]]; then
  TO="$(tr -d '\r' < "$TO_FILE" | head -n1)"
  ARGS+=(-t "$TO")
fi
if "$NOTIFY" "${ARGS[@]}"; then
  echo "$(date '+%F %T') sent phase=$PHASE $NAME" >> "$LOG"
  exit 0
fi
echo "$(date '+%F %T') send failed phase=$PHASE $NAME" >> "$LOG"
exit 1
