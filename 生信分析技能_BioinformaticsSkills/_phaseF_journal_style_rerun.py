# -*- coding: utf-8 -*-
"""Re-run all skill samples so they inherit journal theme from VizStandards."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(r"E:\RProject\生信分析技能_BioinformaticsSkills")
RSCRIPT = "Rscript"
OUT = ROOT / "07_分类验证_Validation" / "journal_style_rerun_log.csv"


def main() -> None:
    scripts = sorted(ROOT.rglob("01_样例_sample/代码文件/run_sample.R"))
    rows = ["skill_path,status,returncode"]
    ok = fail = 0
    for i, sp in enumerate(scripts, 1):
        skill = sp.parents[2].relative_to(ROOT).as_posix()
        print(f"[{i}/{len(scripts)}] {skill}", flush=True)
        try:
            r = subprocess.run(
                [RSCRIPT, str(sp)],
                cwd=str(sp.parent),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
            )
            rc = r.returncode
            status_file = sp.parents[1] / "结果文件" / "报告文件" / "STATUS.txt"
            st = "UNKNOWN"
            if status_file.exists():
                st = status_file.read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
            if rc == 0:
                ok += 1
            else:
                fail += 1
                err = (r.stderr or r.stdout or "")[-400:].replace("\n", " ")
                print("  FAIL", err, flush=True)
            rows.append(f"\"{skill}\",{st},{rc}")
        except Exception as e:
            fail += 1
            rows.append(f"\"{skill}\",ERROR,1")
            print("  EXC", e, flush=True)
    OUT.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"DONE ok={ok} fail={fail} log={OUT}")


if __name__ == "__main__":
    main()
