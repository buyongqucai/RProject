#!/usr/bin/env bash
# 努力学习 Top3：串行生产 MD（NS=100）。同一 GPU 同时只跑一套。
# A3 飞散后自动重搭一轮（共晶/近缘/无大段缺环），再失败则停并发中文邮件。
set -euo pipefail
source "$HOME/activate-md.sh"
mkdir -p "$HOME/md_runs/logs"

SCRIPT=$(find /mnt/e/RProject -path '*分子动力学模拟_MolecularDynamics/脚本_scripts/运行复合物MD_runComplexMd.sh' | head -1)
[[ -n "$SCRIPT" && -f "$SCRIPT" ]] || { echo "FAIL: runComplexMd.sh not found"; exit 1; }
REBUILD=$(find /mnt/e/RProject -path '*分子动力学模拟_MolecularDynamics/脚本_scripts/自动重搭初态_rebuildPoseRetry.py' | head -1)
NOTIFY="${NOTIFY:-/mnt/e/md_kit/notify_md_alert.sh}"
export MD_ALERT_DEFER=1
export MD_ALERT_SH="$NOTIFY"

write_ctx() {
  local wd="$1"
  shift
  mkdir -p "$wd/monitor"
  "$HOME/md-venv/bin/python3" - "$wd/monitor/alert_context.json" "$@" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
ctx = {}
if path.is_file():
    try:
        ctx = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        ctx = {}
# argv: path k v k v ...
args = sys.argv[2:]
for i in range(0, len(args), 2):
    k, v = args[i], args[i + 1]
    if v == "true":
        ctx[k] = True
    elif v == "false":
        ctx[k] = False
    elif v == "null":
        ctx[k] = None
    else:
        ctx[k] = v
path.write_text(json.dumps(ctx, ensure_ascii=False, indent=2), encoding="utf-8")
PY
}

alert_zh() {
  local wd="$1" phase="$2"
  shift 2
  local reason="${*:-}"
  if [[ -x "$NOTIFY" || -f "$NOTIFY" ]]; then
    if [[ -n "$reason" ]]; then
      bash "$NOTIFY" "$wd" --phase "$phase" "$reason" || true
    else
      bash "$NOTIFY" "$wd" --phase "$phase" || true
    fi
  fi
}

repair_protein() {
  local wd="$1"
  local py="$HOME/md-venv/bin/python3"
  "$py" -c "import pdbfixer" 2>/dev/null || uv pip install --python "$py" pdbfixer openmm
  ( cd "$wd" && "$py" <<'PY'
from pdbfixer import PDBFixer
from openmm.app import PDBFile
fixer = PDBFixer(filename="protein.pdb")
fixer.findMissingResidues()
fixer.missingResidues = {}
fixer.findNonstandardResidues()
fixer.replaceNonstandardResidues()
fixer.findMissingAtoms()
fixer.addMissingAtoms()
fixer.addMissingHydrogens(7.0)
with open("protein_fixed.pdb", "w") as fh:
    PDBFile.writeFile(fixer.topology, fixer.positions, fh, keepIds=True)
out = []
for line in open("protein_fixed.pdb"):
    if not line.startswith("ATOM"):
        continue
    name = line[12:16].strip()
    elem = line[76:78].strip() if len(line) >= 78 else ""
    if elem == "H" or (not elem and name.startswith("H")):
        continue
    out.append(line if line.endswith("\n") else line + "\n")
open("protein.pdb", "w").writelines(out)
print("repaired protein heavy atoms", len(out))
PY
  )
}

mapfile -t SYSTEMS < <("$HOME/md-venv/bin/python3" - <<'PY'
from pathlib import Path
import sys
root = Path("/mnt/e/RProject")
candidates = []
for pat in ("*MD*_Top3", "*MD输入_Top3", "*对接姿态_MD输入_Top3"):
    candidates.extend(p for p in root.rglob(pat) if p.is_dir())
seen, ranked = set(), []
for r in sorted(candidates, key=lambda p: (0 if "努力学习" in str(p) else 1, len(str(p)))):
    if r in seen:
        continue
    seen.add(r)
    if any(x.is_dir() for x in r.iterdir()):
        ranked.append(r)
top3 = ranked[0] if ranked else None
if top3 is None:
    raise SystemExit("Top3 input dir not found")
print(f"[queue] top3_root={top3}", file=sys.stderr, flush=True)
order = [
    "ESR2_Anhydroicaritin_1L2J",
    "FOS_quercetin_1A02",
    "PPARG_kaempferol_1FM9",
]
for name in order:
    d = top3 / name
    if d.is_dir() and (d / "protein.pdb").is_file() and (d / "lig_h.mol2").is_file():
        print(f"{name}\t{d}")
PY
)

run_production() {
  local name="$1" src="$2" wd="$3" pose_class="$4" log="$5"
  mkdir -p "$wd"
  cd "$wd"
  # 新初态：清掉旧搭体系产物；保留 monitor 对照可先归档
  if [[ ! -f complex.gro ]]; then
    rm -f topol.top protein.gro posre.itp pdb2gmx.log solv.gro newbox.gro ions.tpr em.gro nvt.gro npt.gro
    cp -f "$src/protein.pdb" "$src/lig_h.mol2" "$wd/"
    echo "[queue] $(date -Is) repair protein $name"
    if ! repair_protein "$wd" >>"$log" 2>&1; then
      mkdir -p "$wd/monitor"
      echo "protein repair (pdbfixer) failed for $name" > "$wd/monitor/ABORT_REASON.txt"
      return 1
    fi
  else
    echo "[queue] $(date -Is) resume $name (complex.gro present)"
  fi
  export LIGAND_RES=LIG NET_CHARGE=0 NS=100 CHUNK_NS=1 MONITOR=1 CHECK_MMGBSA=0
  export POSE_CLASS="$pose_class" MD_ALERT_DEFER=1
  echo "[queue] $(date -Is) START $name POSE_CLASS=$POSE_CLASS NS=$NS -> $log"
  set +e
  bash "$SCRIPT" "$wd" "$wd/protein.pdb" "$wd/lig_h.mol2" >>"$log" 2>&1
  local rc=$?
  set -e
  echo "[queue] $(date -Is) END $name rc=$rc"
  return "$rc"
}

handle_failure_with_one_retry() {
  local name="$1" src="$2" wd="$3" log="$4"
  local reason
  if [[ -f "$wd/monitor/ABORT_REASON.txt" ]]; then
    reason="$(cat "$wd/monitor/ABORT_REASON.txt")"
  else
    reason="流水线失败（见 $log）"
  fi

  # 已是重搭产物：不再重试
  if [[ "$name" == *_retry1 || -f "$wd/monitor/RETRY1_DONE.txt" ]]; then
    write_ctx "$wd" \
      auto_rebuild_attempted true \
      auto_rebuild_ok true \
      will_retry false \
      will_retry_again false \
      original_system "${name%_retry1}" \
      rebuild_reason_zh "本目录已是第 1 轮自动重搭产物，仍失败，不再重试。"
    alert_zh "$wd" final "$reason"
    return 1
  fi

  if [[ -z "${REBUILD:-}" || ! -f "$REBUILD" ]]; then
    write_ctx "$wd" \
      auto_rebuild_attempted false \
      auto_rebuild_ok false \
      will_retry false \
      will_retry_again false \
      rebuild_reason_zh "未找到自动重搭脚本，无法重试。"
    alert_zh "$wd" no_retry "$reason"
    return 1
  fi

  local out_src="${src}_retry1"
  local out_wd="${HOME}/md_runs/${name}_retry1"
  local out_log="${HOME}/md_runs/logs/${name}_retry1.log"
  mkdir -p "$wd/monitor" "$(dirname "$out_src")"
  echo "[queue] $(date -Is) auto-rebuild attempt for $name -> $out_src"
  set +e
  "$HOME/md-venv/bin/python3" "$REBUILD" "$name" "$src" "$out_src" >"$wd/monitor/rebuild_stdout.txt" 2>&1
  local brc=$?
  set -e

  local report="$out_src/rebuild_report.json"
  local rebuild_zh chosen pose_class
  rebuild_zh="自动重搭失败，详见 monitor/rebuild_stdout.txt"
  chosen=""
  pose_class="A2"
  if [[ -f "$report" ]]; then
    rebuild_zh="$("$HOME/md-venv/bin/python3" -c "import json;print(json.load(open('$report',encoding='utf-8')).get('reason_zh',''))" 2>/dev/null || true)"
    chosen="$("$HOME/md-venv/bin/python3" -c "import json;print(json.load(open('$report',encoding='utf-8')).get('chosen_pdb') or '')" 2>/dev/null || true)"
    pose_class="$("$HOME/md-venv/bin/python3" -c "import json;print(json.load(open('$report',encoding='utf-8')).get('pose_class') or 'A2')" 2>/dev/null || true)"
  fi

  if [[ $brc -ne 0 || ! -f "$out_src/protein.pdb" || ! -f "$out_src/lig_h.mol2" ]]; then
    write_ctx "$wd" \
      auto_rebuild_attempted true \
      auto_rebuild_ok false \
      will_retry false \
      will_retry_again false \
      rebuild_reason_zh "${rebuild_zh:-未能生成新初态}" \
      chosen_pdb "${chosen:-}"
    # 同步一份到原目录报告
    [[ -f "$report" ]] && cp -f "$report" "$wd/monitor/rebuild_report.json" || true
    alert_zh "$wd" no_retry "$reason"
    return 1
  fi

  write_ctx "$wd" \
    auto_rebuild_attempted true \
    auto_rebuild_ok true \
    will_retry true \
    will_retry_again false \
    chosen_pdb "$chosen" \
    rebuild_reason_zh "$rebuild_zh" \
    original_system "$name"
  cp -f "$report" "$wd/monitor/rebuild_report.json"
  alert_zh "$wd" will_retry "$reason"

  # 干净重跑目录
  rm -rf "$out_wd"
  mkdir -p "$out_wd/monitor"
  write_ctx "$out_wd" \
    auto_rebuild_attempted true \
    auto_rebuild_ok true \
    will_retry false \
    will_retry_again false \
    chosen_pdb "$chosen" \
    rebuild_reason_zh "$rebuild_zh" \
    original_system "$name"
  echo "$rebuild_zh" > "$out_wd/monitor/RETRY1_DONE.txt"
  set +e
  run_production "${name}_retry1" "$out_src" "$out_wd" "$pose_class" "$out_log"
  local rrc=$?
  set -e
  if [[ $rrc -eq 0 ]]; then
    write_ctx "$out_wd" will_retry false will_retry_again false
    # 成功也可通知？用户只要异常邮件；成功写 DONE 即可
    return 0
  fi
  local rreason
  if [[ -f "$out_wd/monitor/ABORT_REASON.txt" ]]; then
    rreason="$(cat "$out_wd/monitor/ABORT_REASON.txt")"
  else
    rreason="第 1 轮自动重搭后的生产仍失败（见 $out_log）"
  fi
  write_ctx "$out_wd" \
    auto_rebuild_attempted true \
    auto_rebuild_ok true \
    will_retry false \
    will_retry_again false \
    chosen_pdb "$chosen" \
    rebuild_reason_zh "已完成 1 轮自动重搭（$chosen）并重跑，仍然失败，停止。${rebuild_zh}"
  alert_zh "$out_wd" final "$rreason"
  # 原目录也留最终说明
  write_ctx "$wd" \
    auto_rebuild_attempted true \
    auto_rebuild_ok true \
    will_retry false \
    will_retry_again false \
    chosen_pdb "$chosen" \
    rebuild_reason_zh "已完成 1 轮自动重搭并重跑，仍然失败，停止。"
  return 1
}

run_one() {
  local name="$1" src="$2"
  local wd="$HOME/md_runs/$name"
  local log="$HOME/md_runs/logs/${name}.log"
  if [[ -f "$wd/DONE.txt" ]]; then
    echo "[queue] $(date -Is) skip $name (DONE.txt)"
    return 0
  fi
  if [[ -f "$HOME/md_runs/${name}_retry1/DONE.txt" ]]; then
    echo "[queue] $(date -Is) skip $name (retry1 DONE.txt)"
    return 0
  fi
  # 已最终失败（含重搭后失败）：跳过
  if [[ -f "$wd/monitor/FINAL_STOP.txt" || -f "$HOME/md_runs/${name}_retry1/monitor/FINAL_STOP.txt" ]]; then
    echo "[queue] $(date -Is) skip $name (FINAL_STOP)"
    return 0
  fi
  # 旧行为：有 ABORT 且未尝试重搭 → 现在改为进入重搭；若已有 retry1 目录且已 abort → skip
  if [[ -d "$HOME/md_runs/${name}_retry1" && -f "$HOME/md_runs/${name}_retry1/monitor/ABORT_REASON.txt" ]]; then
    echo "[queue] $(date -Is) skip $name (retry1 already aborted)"
    return 0
  fi
  if [[ -f "$wd/md.cpt" && -f "$wd/md.log" ]] && grep -q "Writing checkpoint, step 50000000" "$wd/md.log" 2>/dev/null; then
    echo "[queue] $(date -Is) skip $name (100ns checkpoint present)"
    return 0
  fi

  # 若首轮已 abort 且尚无 retry1：只走重搭，不续跑坏 cpt
  if [[ -f "$wd/monitor/ABORT_REASON.txt" && ! -d "${src}_retry1" && "${FORCE_RERUN:-0}" != "1" ]]; then
    echo "[queue] $(date -Is) $name has ABORT; try one auto-rebuild (no resume of bad cpt)"
    if handle_failure_with_one_retry "$name" "$src" "$wd" "$log"; then
      return 0
    fi
    echo stopped > "$wd/monitor/FINAL_STOP.txt"
    return 1
  fi

  mkdir -p "$wd/monitor"
  set +e
  run_production "$name" "$src" "$wd" "${POSE_CLASS:-A3}" "$log"
  local rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    return 0
  fi
  if handle_failure_with_one_retry "$name" "$src" "$wd" "$log"; then
    return 0
  fi
  echo stopped > "$wd/monitor/FINAL_STOP.txt"
  return 1
}

echo "[queue] $(date -Is) nuli Top3 production queue; systems=${#SYSTEMS[@]}"
fail=0
for line in "${SYSTEMS[@]}"; do
  name="${line%%$'\t'*}"
  src="${line#*$'\t'}"
  if ! run_one "$name" "$src"; then
    fail=1
    echo "[queue] $(date -Is) stop queue after failure on $name"
    break
  fi
done
if [[ $fail -eq 0 ]]; then
  echo "[queue] $(date -Is) ALL_DONE"
else
  echo "[queue] $(date -Is) STOPPED_WITH_FAILURE"
  exit 1
fi
