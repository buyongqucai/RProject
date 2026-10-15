# -*- coding: utf-8 -*-
"""临时：把重导出的 PNG/SVG 按 MdFigureStandards 一图一夹交付到新层级图册。"""
import shutil
import sys
from pathlib import Path

SRC = Path(r"E:\Origin_Data")
DST = Path(r"E:\RProject\努力学习项目\08_分子动力学\结果文件\图片文件\分子动力学图_MD")

STEM_ZH = {
    "RmsdBackbone": ("01", "骨架RMSD"), "RmsdProteinLigandComplex": ("02", "三线RMSD"),
    "RmsfCalpha": ("03", "残基RMSF"), "HbondNum": ("04", "氢键数"),
    "RadiusGyration": ("05", "回旋半径"), "Sasa": ("06", "溶剂可及表面积"),
    "ComDistance": ("07", "质心距离"), "NvtTemperature": ("08", "NVT温度"),
    "NptTemperature": ("09", "NPT温度"), "NptPressure": ("10", "NPT压力"),
    "NptDensity": ("11", "NPT密度"), "MdPotential": ("12", "生产势能"),
    "FreeEnergyLandscape": ("13", "自由能形貌"), "FreeEnergyLandscape3D": ("14", "自由能形貌3D"),
    "FreeEnergyRmsdCom": ("15", "自由能形貌RMSDx质心"), "FreeEnergyRmsdCom3D": ("16", "自由能形貌3D_RMSDx质心"),
    "FreeEnergyRmsdSasa": ("17", "自由能形貌RMSDxSASA"), "FreeEnergyRmsdSasa3D": ("18", "自由能形貌3D_RMSDxSASA"),
    "FreeEnergyLigandProteinRmsd": ("19", "自由能形貌配体蛋白RMSD"),
    "FreeEnergyLigandProteinRmsd3D": ("20", "自由能形貌3D_配体蛋白RMSD"),
}


def main() -> int:
    n_ok = n_miss = 0
    for sys_dir in sorted(p for p in DST.iterdir() if p.is_dir()):
        figs = SRC / sys_dir.name / "OriginFigures"
        if not figs.is_dir():
            print("MISSING OriginFigures", sys_dir.name)
            continue
        for stem, (nn, zh) in STEM_ZH.items():
            folder = sys_dir / f"{nn}_{zh}图"
            folder.mkdir(parents=True, exist_ok=True)
            for ext in (".png", ".svg"):
                src = figs / f"{stem}{ext}"
                dst = folder / f"{nn}_{zh}_{stem}{ext}"
                if not src.is_file():
                    print("MISSING", sys_dir.name, src.name)
                    n_miss += 1
                    continue
                shutil.copy2(src, dst)
                n_ok += 1
    print(f"delivered={n_ok} missing={n_miss}")
    return 0 if n_miss == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
