#!/usr/bin/env python3
"""把 WSL ~/md_runs/<体系> 归档到 努力学习项目/08_分子动力学/数据文件/结果文件/分子动力学_MD/<体系>/。
按 SOP 分阶段入夹（01_输入结构…99_运行日志）；只复制，不改动 WSL 原目录。"""
import shutil
import sys
from pathlib import Path

NAME = sys.argv[1] if len(sys.argv) > 1 else "FOS_quercetin_1A02"
SRC = Path.home() / "md_runs" / NAME
DST = Path("/mnt/e/RProject/努力学习项目/08_分子动力学/数据文件/结果文件/分子动力学_MD") / NAME

STAGES = {
    "input": "01_输入结构_Input",
    "topo": "02_拓扑_Topology",
    "solv": "03_溶剂化离子_Solvation",
    "em": "04_最小化_EnergyMin",
    "nvt": "05_NVT平衡_Nvt",
    "npt": "06_NPT平衡_Npt",
    "prod": "07_生产轨迹_Production",
    "anal": "08_轨迹分析_Analysis",
    "snap": "10_轨迹快照_Snapshots",
    "logs": "99_运行日志_Logs",
}
RULES = {
    "input": ["protein.pdb", "protein_fixed.pdb", "lig_h.mol2"],
    "topo": ["topol.top", "posre.itp", "protein.gro", "complex.gro", "#topol.top.1#", "#topol.top.2#"],
    "solv": ["newbox.gro", "solv.gro", "solv_ions.gro", "ions.tpr", "mdout.mdp", "metal_counts.txt"],
    "em": ["em.tpr", "em.gro", "em.edr", "em.trr", "em.log", "grompp_em.log"],
    "nvt": ["nvt.gro", "nvt.edr", "nvt.cpt", "nvt.log", "grompp_nvt.log", "energy_nvt_temp.xvg"],
    "npt": ["npt.gro", "npt.edr", "npt.cpt", "npt.log", "grompp_npt.log",
            "energy_npt_temp.xvg", "energy_npt_pres.xvg", "energy_md_temp.xvg"],
    "prod": ["md.tpr", "md.xtc", "md.edr", "md.trr", "md.log", "md.cpt", "md_prev.cpt",
             "md.gro", "run_md.mdp", "grompp_md.log", "mdrun_md.log", "mdrun_em.log",
             "mdrun_nvt.log", "mdrun_npt.log", "editconf.log", "genion.log", "grompp_ions.log"],
    "anal": ["rmsd_backbone.xvg", "rmsd_protein.xvg", "rmsd_ligand.xvg", "rmsd_complex.xvg",
             "rmsf_calpha.xvg", "hbond_num.xvg", "gyrate.xvg", "sasa.xvg", "com_distance.xvg",
             "energy_md_potential.xvg", "md_center.xtc", "index.ndx", "index_analysis.ndx",
             "pose_gate.txt"],
}
DIRS = {"topo": ["ligand.acpype"], "anal": ["monitor"]}


def main():
    if not SRC.is_dir():
        raise SystemExit(f"missing source {SRC}")
    for key, folder in STAGES.items():
        (DST / folder).mkdir(parents=True, exist_ok=True)
    for key, names in RULES.items():
        for n in names:
            s = SRC / n
            if s.is_file():
                shutil.copy2(s, DST / STAGES[key] / n)
    for key, dirs in DIRS.items():
        for d in dirs:
            s = SRC / d
            if s.is_dir():
                shutil.copytree(s, DST / STAGES[key] / d, dirs_exist_ok=True)
    logs = DST / STAGES["logs"]
    for s in sorted(SRC.iterdir()):
        if s.is_file() and (s.suffix == ".log" or s.name in ("DONE.txt", "acpype.log")
                            or s.name.endswith(".txt")):
            if any(s.name in v for v in RULES.values()):
                continue
            shutil.copy2(s, logs / s.name)
    for s in sorted(SRC.glob("*.pdb")):
        shutil.copy2(s, DST / STAGES["snap"] / s.name)
    n = sum(1 for _ in DST.rglob("*") if _.is_file())
    print(f"archived {NAME} -> {DST} ({n} files)")


if __name__ == "__main__":
    main()
