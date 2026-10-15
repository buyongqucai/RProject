#!/usr/bin/env python3
"""WSL MD 计算数据轻量归档：轨迹大件（xtc/trr/edr）不归档，其余（topol/tpr/cpt/gro/xvg/日志/monitor）入
E:\\RProject\\努力学习项目\\08_分子动力学\\结果文件\\数据文件\\分子动力学_MD\\<体系>\\（沿用分阶段布局）。
跑完返回清单，供随后删除 ~/md_runs。"""
import shutil
from pathlib import Path

SRC = Path.home() / "md_runs"
DST = Path("/mnt/e/RProject/努力学习项目/08_分子动力学/结果文件/数据文件/分子动力学_MD")
SKIP_EXT = {".xtc", ".trr", ".edr"}

copied, skipped_bytes, failed = 0, 0, 0
for sys_dir in sorted(SRC.iterdir()):
    if not sys_dir.is_dir() or sys_dir.name in ("logs", "mdp_templates"):
        continue
    out = DST / sys_dir.name
    if (out / "_flat").is_dir():
        shutil.rmtree(out / "_flat")  # 清掉上次中断的半成品，重归档
    for f in sorted(sys_dir.rglob("*")):
        if not f.is_file():
            continue
        low = f.name.lower()
        if f.suffix.lower() in SKIP_EXT or ".xtc" in low or ".trr" in low or ".edr" in low \
                or f.name.startswith("#") or f.name.endswith("#"):
            skipped_bytes += f.stat().st_size
            continue
        rel = f.relative_to(sys_dir)
        d = out / "_flat" / rel.parent
        d.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(f, d / f.name)
            copied += 1
        except OSError as e:
            failed += 1
            print(f"  SKIP-FAIL {f}: {e}")
    print(f"{sys_dir.name}: -> {out/'_flat'}")
# 日志与模板也留底
for extra in ("logs",):
    s = SRC / extra
    if s.is_dir():
        for f in s.rglob("*"):
            if f.is_file():
                d = DST / "_md_logs" / f.relative_to(s).parent
                d.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, d / f.name)
                copied += 1
print(f"light-archive done: copied {copied} files, failed {failed}, skipped trajectories {skipped_bytes/1e9:.1f} GB")
