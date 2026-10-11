# -*- coding: utf-8 -*-
import re
import shutil
import subprocess
import sys
from pathlib import Path

src = next(Path(r"E:/RProject").rglob("origin出图_plotMdOrigin.py"))
dst = Path(r"E:/Origin_Data/_tools/plotMdOrigin.py")
shutil.copy2(src, dst)
t = src.read_text(encoding="utf-8")
m = re.search(r"OC_HIDE_SRC = r'''(.*?)'''", t, re.S)
if not m:
    raise SystemExit("OC_HIDE_SRC not found")
Path(r"E:/Origin/OriginC/hideFelContours.c").write_text(
    m.group(1).replace("\n", "\r\n"), encoding="ascii"
)
print("synced", src.name, "oc", len(m.group(1)))

py = Path(r"E:/Python3.13.14/python.exe")
only = "FreeEnergyLandscape3D,FreeEnergyRmsdCom3D,FreeEnergyRmsdSasa3D,FreeEnergyLigandProteinRmsd3D"
for proj in ("MMP9_Tryptophan_4H3X", "ADA_Adenosine_7RTG_A2"):
    print("===", proj, flush=True)
    r = subprocess.run(
        [str(py), str(dst), "--data-dir", rf"E:\Origin_Data\{proj}", "--only", only],
        check=False,
    )
    print("exit", r.returncode, flush=True)

# delivery sync
import importlib.util

proj_root = next(p for p in Path(r"E:/RProject").iterdir() if p.is_dir() and "努力" in p.name)
tox = next(p for p in (proj_root / "交付文件").iterdir() if p.is_dir() and "毒" in p.name)
pic = tox / "图片文件" / "分子动力学图_MD"
spec = importlib.util.spec_from_file_location("pm", dst)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ORDER = {
    "自由能形貌3D": 17,
    "自由能形貌3D_RMSDx质心": 18,
    "自由能形貌3D_RMSDxSASA": 19,
    "自由能形貌3D_配体蛋白RMSD": 20,
}
for sysname in ("MMP9_Tryptophan_4H3X", "ADA_Adenosine_7RTG_A2"):
    sdir = Path(r"E:/Origin_Data") / sysname / "OriginFigures"
    for stem in ORDER and list(ORDER.keys()):
        pass
    for stem in (
        "FreeEnergyLandscape3D",
        "FreeEnergyRmsdCom3D",
        "FreeEnergyRmsdSasa3D",
        "FreeEnergyLigandProteinRmsd3D",
    ):
        zh = mod.STEM_ZH[stem]
        topic = mod.topic_zh(stem)
        nn = ORDER[topic]
        folder = pic / sysname / f"{nn:02d}_{topic}图"
        folder.mkdir(parents=True, exist_ok=True)
        for ext in (".png", ".svg"):
            src = sdir / f"{stem}{ext}"
            if not src.exists():
                print("MISSING", src)
                continue
            shutil.copy2(src, folder / f"{nn:02d}_{zh}{ext}")
print("delivery ok")
