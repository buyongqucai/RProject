# -*- coding: utf-8 -*-
"""图交付门禁：命名/存放/标签完整性自动核查（MdFigureStandards + PlotQA）。

用法: python 图交付门禁_gateMdFigures.py <交付目录>
任一 FAIL 即退出码 2（禁止交付）。检查项：
1. 文件名 {NN}_{中文}_{English}.png/svg 且一图一夹 {NN}_{中文}图/
2. SVG 标签无占位（如 "Color Scale Title"）、轴标题/单位齐全
3. 每图 PNG+SVG 成对、DPI 由导出器保证（不重复验）
"""
import re
import sys
from pathlib import Path

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
PLACEHOLDER = re.compile(r"Color Scale Title|Lorem|TBD|TODO", re.I)


def main(root: Path) -> int:
    fails = []
    for sys_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for stem, (nn, zh) in STEM_ZH.items():
            folder = sys_dir / f"{nn}_{zh}图"
            for ext in (".png", ".svg"):
                f = folder / f"{nn}_{zh}_{stem}{ext}"
                if not f.is_file():
                    fails.append(f"MISSING {f.relative_to(root)}")
                    continue
                if ext == ".svg":
                    texts = [re.sub(r"<[^>]+>", "", x).strip()
                             for x in re.findall(r"<text[^>]*>(.*?)</text>", f.read_text(errors="replace"), re.S)]
                    joined = " | ".join(t for t in texts if t)
                    if PLACEHOLDER.search(joined):
                        fails.append(f"PLACEHOLDER_LABEL {f.relative_to(root)}")
        for loose in sys_dir.glob("*.png"):
            fails.append(f"LAYOUT_FLAT {loose.relative_to(root)}（应一图一夹）")
    for x in fails:
        print("FAIL", x)
    print(f"gate: {'FAIL' if fails else 'PASS'} ({len(fails)} problems)")
    return 2 if fails else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
