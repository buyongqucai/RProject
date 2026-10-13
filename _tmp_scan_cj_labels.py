# -*- coding: utf-8 -*-
import __main__

__main__.pymol_argv = ["pymol", "-cq"]
import pymol
from pymol import cmd, stored

pymol.finish_launching()

import sys
from pathlib import Path

sys.path.insert(
    0,
    r"E:\RProject\生信分析技能_BioinformaticsSkills\03_药物计算_DrugDiscovery\分子对接与虚拟筛选_MolecularDocking\脚本_scripts",
)
from pymol_dock_viz_standard import apply_detail_labels, build_qj_and_cj

jobs_root = (
    Path(r"E:/RProject")
    / "\u52aa\u529b\u5b66\u4e60\u9879\u76ee"
    / "06_\u5206\u5b50\u5bf9\u63a5"
    / "\u5e8f\u53f7\u6587\u4ef6\u5939"
)
report = []
fixed = []
for job in sorted(jobs_root.iterdir()):
    if not job.is_dir() or not job.name.isdigit():
        continue
    pse = job / f"detail-{job.name}.pse"
    if not pse.is_file():
        continue
    cmd.reinitialize()
    cmd.load(str(pse))
    if cmd.count_atoms("CJ") <= 0:
        build_qj_and_cj(cmd, hbond_color="yellow", residue_color="orange")
    stored.res = []
    cmd.iterate("CJ", "stored.res.append((chain,resn,resi))")
    allres = sorted(set(stored.res))
    stored.ca = []
    cmd.iterate("CJ and name CA", "stored.ca.append((chain,resn,resi))")
    missing = [r for r in allres if r not in set(stored.ca)]
    if missing:
        report.append(f"{job.name}: missing CA labels for {missing}")
        try:
            cmd.label("all", "")
        except Exception:
            pass
        apply_detail_labels(cmd)
        cmd.save(str(pse))
        fixed.append(job.name)
    else:
        report.append(f"{job.name}: ok ({len(allres)} CJ residues)")

Path(r"E:/RProject/_tmp_scan_cj.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
print("fixed", fixed)
print("\n".join(report))
