# -*- coding: utf-8 -*-
from pathlib import Path

BIO = Path(r"E:\RProject\生信分析技能_BioinformaticsSkills")
deg = next(BIO.rglob("*DEG-UMAP*/01_样例_sample"))
code = deg / "代码文件"
rs = code / "run_sample.R"
rs01 = code / "01_run_sample.R"
print("sample", deg)
if rs.exists() and not rs01.exists():
    rs.rename(rs01)
    print("renamed run_sample -> 01_run_sample")
target = rs01 if rs01.exists() else rs
text = target.read_text(encoding="utf-8")
text2 = text.replace('normalizePath("run_sample.R"', 'normalizePath("01_run_sample.R"')
# ensure paths after PlotNaming
idx_p = text2.find("paths <- delivery_sample_paths")
idx_s = text2.find("PlotNaming.R")
print("paths_idx", idx_p, "src_idx", idx_s, "nested", (code / "结果文件").is_dir())
if idx_p >= 0 and idx_s >= 0 and idx_p < idx_s:
    print("WARNING: paths before source — manual check needed")
if text2 != text:
    target.write_text(text2, encoding="utf-8")
    print("wrote self-path fix")
else:
    print("no text change")
