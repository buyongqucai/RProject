#!/usr/bin/env bash
# 过程监控_monitorMdRun.sh — 生产 MD 分块间隙检查；异常非 0 退出（主脚本应停止续跑）
#
# 用法（在含 md.tpr / md.xtc / md.edr / md.log 的工作目录）：
#   source ~/activate-md.sh
#   LIGAND_RES=JZ4 bash 过程监控_monitorMdRun.sh .
#
# 环境变量（可覆盖阈值）：
#   LIGAND_RES=JZ4
#   COM_MAX_NM=2.0          # 蛋白–配体质心距离上限（飞出）
#   COM_JUMP_NM=1.0         # 相对首帧 COM 的增量上限
#   LIG_RMSD_MAX_NM=1.5     # 配体 RMSD 上限
#   BB_RMSD_MAX_NM=1.0      # 骨架 RMSD 上限（可疑展开）
#   TEMP_MIN_K=250  TEMP_MAX_K=350
#   CHECK_MMGBSA=0          # 1=抽查 MM-GBSA；ΔG>0 (kcal/mol) 即停
#   MMGBSA_INTERVAL_NS=5    # 仅当已模拟时长为该值整数倍时抽查（需 md 已有足够帧）
#   PLOT_MONITOR=1          # 写 monitor/*.png 过程草图（非 Origin 金标）
#
# 退出码：0=OK  2=ABORT（已写 monitor/ABORT_REASON.txt）  1=工具/输入失败
set -euo pipefail

WORK="${1:-.}"
cd "$WORK"
LIGAND_RES="${LIGAND_RES:-JZ4}"
COM_MAX_NM="${COM_MAX_NM:-2.0}"
COM_JUMP_NM="${COM_JUMP_NM:-1.0}"
LIG_RMSD_MAX_NM="${LIG_RMSD_MAX_NM:-1.5}"
BB_RMSD_MAX_NM="${BB_RMSD_MAX_NM:-1.0}"
TEMP_MIN_K="${TEMP_MIN_K:-250}"
TEMP_MAX_K="${TEMP_MAX_K:-350}"
CHECK_MMGBSA="${CHECK_MMGBSA:-0}"
MMGBSA_INTERVAL_NS="${MMGBSA_INTERVAL_NS:-5}"
PLOT_MONITOR="${PLOT_MONITOR:-1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MON=monitor
mkdir -p "$MON"

abort() {
  echo "$*" | tee "$MON/ABORT_REASON.txt"
  echo "MONITOR_ABORT: $*"
  # 异常邮件：经 alert_kit（~/.md_alert_to 或 ~/.alert_to）；发送失败不掩盖退出码 2
  NOTIFY="${MD_ALERT_SH:-/mnt/e/md_kit/notify_md_alert.sh}"
  if [[ -f "$NOTIFY" ]]; then
    bash "$NOTIFY" "$*" "$(pwd)" || true
  fi
  exit 2
}

command -v gmx >/dev/null || { echo "FAIL: gmx not on PATH (source ~/activate-md.sh)"; exit 1; }
[[ -f md.tpr ]] || { echo "FAIL: need md.tpr"; exit 1; }
[[ -f md.xtc || -f md.cpt ]] || { echo "FAIL: need md.xtc or md.cpt"; exit 1; }

# ---- log hard fails ----
# 只扫 "Started mdrun" 之后。文件开头会回显 mdp，lincs-warnangle 含子串 nan，
# 全文件 grep 会把正常 1 ns 块误判成 NaN（ADA 7RTG 2026-10-09 实测）。
if [[ -f md.log ]]; then
  if awk '
    /Started mdrun/ {on=1}
    on && /Fatal error|Segmentation fault/ {bad=1}
    on && (/(^|[^A-Za-z])[Nn][Aa][Nn]([^A-Za-z]|$)/ || /-nan/ || /#IND/) {bad=1}
    END {exit bad?2:0}
  ' md.log; then
    :
  else
    abort "md.log after Started mdrun contains NaN/Fatal — stop and inspect topology/constraints"
  fi
fi

# ---- center trajectory snapshot for metrics (idempotent overwrite monitor copies) ----
XTC=md.xtc
if [[ ! -f "$XTC" ]]; then
  echo "WARN: md.xtc missing yet; skip geometry checks (only edr/log)"
else
  printf 'Protein\nSystem\n' | gmx trjconv -s md.tpr -f md.xtc -o "$MON/md_center.xtc" \
    -pbc mol -center -ur compact > "$MON/trjconv.log" 2>&1 || true
  if [[ -f "$MON/md_center.xtc" ]]; then
    printf 'Backbone\nBackbone\n' | gmx rms -s md.tpr -f "$MON/md_center.xtc" \
      -o "$MON/rmsd_backbone.xvg" -tu ns > "$MON/rms_bb.log" 2>&1 || true
    printf "Backbone\n${LIGAND_RES}\n" | gmx rms -s md.tpr -f "$MON/md_center.xtc" \
      -o "$MON/rmsd_ligand.xvg" -tu ns > "$MON/rms_lig.log" 2>&1 || true
    printf "Protein\n${LIGAND_RES}\n" | gmx distance -s md.tpr -f "$MON/md_center.xtc" \
      -select "com of group Protein plus com of group ${LIGAND_RES}" \
      -oav "$MON/com_distance.xvg" > "$MON/com.log" 2>&1 \
      || printf "Protein\n${LIGAND_RES}\n" | gmx distance -s md.tpr -f "$MON/md_center.xtc" \
           -oav "$MON/com_distance.xvg" > "$MON/com.log" 2>&1 || true
  fi
fi

# ---- edr: 温度与势能分文件抽取 ----
# 实测（ADA energy_TP.xvg）：一次选 Temperature+Potential 时，xvg 列序是
# Potential, Temperature，与交互输入顺序相反。分文件后每份只有 time + 一项。
if [[ -f md.edr ]]; then
  printf 'Temperature\n0\n' | gmx energy -f md.edr -o "$MON/energy_T.xvg" \
    > "$MON/energy_T.log" 2>&1 || true
  printf 'Potential\n0\n' | gmx energy -f md.edr -o "$MON/energy_P.xvg" \
    > "$MON/energy_P.log" 2>&1 || true
fi

# ---- threshold checks (python) ----
export MON LIGAND_RES COM_MAX_NM COM_JUMP_NM LIG_RMSD_MAX_NM BB_RMSD_MAX_NM TEMP_MIN_K TEMP_MAX_K PLOT_MONITOR
python3 - <<'PY'
import os, sys, re
from pathlib import Path

mon = Path(os.environ["MON"])
reasons = []

def read_xvg(p):
    rows = []
    if not Path(p).is_file():
        return rows
    for line in Path(p).read_text(errors="replace").splitlines():
        if not line or line[0] in "#@":
            continue
        parts = line.split()
        if len(parts) >= 2:
            try:
                rows.append([float(x) for x in parts[:4]])
            except ValueError:
                pass
    return rows

def col_by_legend(path, name):
    """返回 (列下标, 数值列表)。找不到 legend 时用第 1 列（time 之后）。"""
    if not path.is_file():
        return None, [], []
    idx = None
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        m = re.match(r'@\s*s(\d+)\s+legend\s+"([^"]+)"', line)
        if m and m.group(2).lower() == name.lower():
            idx = int(m.group(1)) + 1
            continue
        if not line or line[0] in "#@":
            continue
        parts = line.split()
        if len(parts) >= 2:
            try:
                rows.append([float(x) for x in parts[:6]])
            except ValueError:
                pass
    if idx is None:
        idx = 1
    vals = [r[idx] for r in rows if len(r) > idx]
    return idx, vals, rows

def median(vals):
    if not vals:
        return None
    s = sorted(vals)
    return s[len(s) // 2]

bb = read_xvg(mon / "rmsd_backbone.xvg")
lig = read_xvg(mon / "rmsd_ligand.xvg")
com = read_xvg(mon / "com_distance.xvg")
ti, temps, t_rows = col_by_legend(mon / "energy_T.xvg", "Temperature")
pi, pots, p_rows = col_by_legend(mon / "energy_P.xvg", "Potential")

bb_max = max((r[1] for r in bb), default=None)
lig_max = max((r[1] for r in lig), default=None)
com_vals = [r[1] for r in com]
com_max = max(com_vals) if com_vals else None
com0 = com_vals[0] if com_vals else None
com_jump = (com_max - com0) if (com_max is not None and com0 is not None) else None

bb_lim = float(os.environ["BB_RMSD_MAX_NM"])
lig_lim = float(os.environ["LIG_RMSD_MAX_NM"])
com_lim = float(os.environ["COM_MAX_NM"])
com_jump_lim = float(os.environ["COM_JUMP_NM"])
tmin = float(os.environ["TEMP_MIN_K"])
tmax = float(os.environ["TEMP_MAX_K"])

if bb_max is not None and bb_max > bb_lim:
    reasons.append(f"backbone RMSD max {bb_max:.3f} nm > {bb_lim} nm (possible unfold)")
if lig_max is not None and lig_max > lig_lim:
    reasons.append(f"ligand RMSD max {lig_max:.3f} nm > {lig_lim} nm (ligand fly/dissociate)")
if com_max is not None and com_max > com_lim:
    reasons.append(f"COM distance max {com_max:.3f} nm > {com_lim} nm (receptor-ligand separation)")
if com_jump is not None and com_jump > com_jump_lim:
    reasons.append(f"COM jump {com_jump:.3f} nm > {com_jump_lim} nm vs first frame")

# 温度必须像开尔文。ADA 2 ns 实测约 296–303 K。
# 若中位数是势能量级（约 -4.9e5），按解析错误停，避免再报成「温度 -492803 K」。
t_med = median(temps)
t_recent = None
if temps:
    tail = temps[-20:]
    t_recent = sum(tail) / len(tail)
    if t_med is None or not (150 <= t_med <= 450):
        reasons.append(
            f"PARSE temperature series median {t_med} is not Kelvin — check energy_T.xvg legend"
        )
    elif t_recent < tmin or t_recent > tmax:
        reasons.append(f"Temperature recent mean {t_recent:.1f} K outside [{tmin},{tmax}]")

# 势能：本体系平衡在约 -4.9e5 kJ/mol，帧间起伏约 ±2e3。
# 停机条件用相对漂移，不用绝对值 >1e9（那一档在正常能量下永远不触发）。
p_med = median(pots)
p_recent = None
if pots:
    p_tail = pots[-20:]
    p_recent = sum(p_tail) / len(p_tail)
    if any((x != x) for x in p_tail):
        reasons.append("Potential NaN in recent frames")
    elif p_med is not None and abs(p_med) > 1:
        rel = abs(p_recent - p_med) / abs(p_med)
        if rel > 0.5 or (p_med < 0 < p_recent):
            reasons.append(
                f"Potential recent {p_recent:.3g} drifted >50% from median {p_med:.3g} kJ/mol"
            )

summary = mon / "LAST_CHECK.txt"
lines = [
    f"bb_rmsd_max_nm={bb_max}",
    f"lig_rmsd_max_nm={lig_max}",
    f"com_max_nm={com_max}",
    f"com_jump_nm={com_jump}",
    f"temp_recent_K={t_recent}",
    f"temp_median_K={t_med}",
    f"pot_recent={p_recent}",
    f"pot_median={p_med}",
]
summary.write_text("\n".join(lines) + "\n", encoding="utf-8")

if os.environ.get("PLOT_MONITOR", "1") == "1":
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        def plot_xy(rows, idx_y, title, ylab, out):
            if not rows:
                return
            x = [r[0] for r in rows]
            y = [r[idx_y] for r in rows if len(r) > idx_y]
            x = x[:len(y)]
            fig, ax = plt.subplots(figsize=(5, 3), dpi=120)
            ax.plot(x, y, color="#5B8FA8", lw=1.2)
            ax.set_xlabel("Time (ns or ps as in xvg)")
            ax.set_ylabel(ylab)
            ax.set_title(title + " [monitor draft]")
            fig.tight_layout()
            fig.savefig(out)
            plt.close(fig)
        plot_xy(bb, 1, "Backbone RMSD", "nm", mon / "01_monitor_RmsdBackbone.png")
        plot_xy(lig, 1, "Ligand RMSD", "nm", mon / "02_monitor_RmsdLigand.png")
        plot_xy(com, 1, "COM distance", "nm", mon / "07_monitor_ComDistance.png")
        if t_rows and t_recent is not None and t_med is not None and 150 <= t_med <= 450:
            plot_xy(t_rows, ti, "Temperature", "K", mon / "08_monitor_Temperature.png")
        if p_rows and p_recent is not None:
            plot_xy(p_rows, pi, "Potential", "kJ/mol", mon / "12_monitor_Potential.png")
    except Exception as e:
        (mon / "plot_warn.txt").write_text(str(e), encoding="utf-8")

if reasons:
    (mon / "ABORT_REASON.txt").write_text("\n".join(reasons) + "\n", encoding="utf-8")
    print("MONITOR_ABORT:")
    for r in reasons:
        print(" -", r)
    sys.exit(2)
print("MONITOR_OK", "; ".join(lines))
sys.exit(0)
PY
MON_RC=$?

# Python 判定飞出时直接 sys.exit(2)，不会经过上面的 abort()。
# 不在这里补叫，42 ns 那次就不会发信（2026-10-09 ADA）。
if [[ "$MON_RC" -eq 2 && -f "$MON/ABORT_REASON.txt" ]]; then
  abort "$(cat "$MON/ABORT_REASON.txt")"
fi

# ---- optional MM-GBSA probe (positive ΔG => abort) ----
if [[ "$CHECK_MMGBSA" == "1" && -f md.xtc && "$MON_RC" -eq 0 ]]; then
  LAST_NS=$(awk 'NF>=2 && $1!~/^[@#]/ {t=$1} END{print t+0}' "$MON/rmsd_backbone.xvg" 2>/dev/null || echo 0)
  DO_PROBE=$(LAST_NS="$LAST_NS" IV="$MMGBSA_INTERVAL_NS" python3 -c 'import os; last=float(os.environ["LAST_NS"]); iv=float(os.environ["IV"]); print(1 if last>=iv and abs(last/iv-round(last/iv))<0.25 else 0)')
  if [[ "$DO_PROBE" == "1" ]]; then
    echo "MMGBSA probe at ~${LAST_NS} ns ..."
    printf 'q\n' | gmx make_ndx -f md.tpr -o "$MON/index.ndx" > "$MON/ndx.log" 2>&1 || true
    LIG_G=13
    MMPBSA_BIN="${MMPBSA_BIN:-$HOME/md-venv/bin/gmx_MMPBSA}"
    IN="$SCRIPT_DIR/mmpbsa模板_mmpbsa.in"
    CT="$MON/md_center.xtc"; [[ -f "$CT" ]] || CT=md.xtc
    if [[ -x "$MMPBSA_BIN" && -f "$IN" ]]; then
      "$MMPBSA_BIN" -O -i "$IN" -cs md.tpr -ct "$CT" -ci "$MON/index.ndx" -cg 1 "$LIG_G" -cp topol.top \
        -o "$MON/FINAL_RESULTS_MMPBSA.dat" -do "$MON/FINAL_DECOMP_MMPBSA.dat" \
        > "$MON/mmgbsa_probe.log" 2>&1 || true
      DG=$(awk '/DELTA TOTAL/ {print $(NF-1)}' "$MON/FINAL_RESULTS_MMPBSA.dat" 2>/dev/null | tail -1)
      if [[ -n "${DG:-}" ]]; then
        if python3 -c "import sys; sys.exit(0 if float('${DG}')>0 else 1)"; then
          abort "MM-GBSA DELTA TOTAL ≈ ${DG} kcal/mol is positive — stop and inspect pose/topology"
        fi
        echo "MMGBSA_OK DELTA TOTAL=${DG} kcal/mol" | tee -a "$MON/LAST_CHECK.txt"
      fi
    fi
  fi
fi

exit "$MON_RC"
