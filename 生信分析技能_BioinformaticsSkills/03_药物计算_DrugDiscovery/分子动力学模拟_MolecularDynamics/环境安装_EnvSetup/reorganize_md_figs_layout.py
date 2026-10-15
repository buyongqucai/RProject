# -*- coding: utf-8 -*-
"""按 MdFigureStandards 重排交付目录：一图一夹 {NN}_{中文}图/ + 文件 {NN}_{中文}_{English}.png/svg。
纯移动/改名（FROZEN 允许路径迁移与 NN_ 前缀），不改视觉。"""
import shutil
from pathlib import Path

STEM_ZH = {
    "RmsdBackbone": ("01", "骨架RMSD"),
    "RmsdProteinLigandComplex": ("02", "三线RMSD"),
    "RmsfCalpha": ("03", "残基RMSF"),
    "HbondNum": ("04", "氢键数"),
    "RadiusGyration": ("05", "回旋半径"),
    "Sasa": ("06", "溶剂可及表面积"),
    "ComDistance": ("07", "质心距离"),
    "NvtTemperature": ("08", "NVT温度"),
    "NptTemperature": ("09", "NPT温度"),
    "NptPressure": ("10", "NPT压力"),
    "NptDensity": ("11", "NPT密度"),
    "MdPotential": ("12", "生产势能"),
    "FreeEnergyLandscape": ("13", "自由能形貌"),
    "FreeEnergyLandscape3D": ("14", "自由能形貌3D"),
    "FreeEnergyRmsdCom": ("15", "自由能形貌RMSDx质心"),
    "FreeEnergyRmsdCom3D": ("16", "自由能形貌3D_RMSDx质心"),
    "FreeEnergyRmsdSasa": ("17", "自由能形貌RMSDxSASA"),
    "FreeEnergyRmsdSasa3D": ("18", "自由能形貌3D_RMSDxSASA"),
    "FreeEnergyLigandProteinRmsd": ("19", "自由能形貌配体蛋白RMSD"),
    "FreeEnergyLigandProteinRmsd3D": ("20", "自由能形貌3D_配体蛋白RMSD"),
}

ROOT = Path(r"E:\RProject\努力学习项目\08_分子动力学\文档文件\图片文件\分子动力学图_MD")
SRC = Path(r"E:\Origin_Data")
# 先从 OriginFigures 拷最新 PNG/SVG 扁平入项目目录，再统一改名入夹
for sys_dir in sorted(ROOT.iterdir()):
    if not sys_dir.is_dir():
        continue
    figs = SRC / sys_dir.name / "OriginFigures"
    if figs.is_dir():
        for f in figs.glob("*"):
            if f.suffix.lower() in (".png", ".svg"):
                shutil.copy2(f, sys_dir / f.name)
for sys_dir in sorted(ROOT.iterdir()):
    if not sys_dir.is_dir():
        continue
    for stem, (nn, zh) in STEM_ZH.items():
        folder = sys_dir / f"{nn}_{zh}图"
        moved = 0
        for ext in (".png", ".svg"):
            src = sys_dir / f"{stem}{ext}"
            if not src.is_file():
                continue
            folder.mkdir(exist_ok=True)
            dst = folder / f"{nn}_{zh}_{stem}{ext}"
            shutil.move(str(src), str(dst))
            moved += 1
        if moved:
            print(f"{sys_dir.name}: {nn}_{zh}图 <- {moved} files")
print("layout done")
