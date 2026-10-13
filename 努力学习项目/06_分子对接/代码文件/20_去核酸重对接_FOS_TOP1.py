# -*- coding: utf-8 -*-
"""去核酸后重对接 FOS / TOP1（原受体 ATOM 中残留 DNA）。"""
from __future__ import annotations

import importlib.util
import re
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CODE = Path(__file__).resolve().parent
ASCII = Path(r"E:\RProject\_dock_cmp")
OUT_DOCK = ROOT / "数据文件" / "结果数据" / "对接"
SEL = ROOT / "数据文件" / "结果数据" / "筛选执行_SelectionRun"

# load 19 as module
spec = importlib.util.spec_from_file_location("dock19", CODE / "19_按标准筛选并对接.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# wipe old DNA-containing STD outputs
for p in list(ASCII.glob("STD_FOS__*")) + list(ASCII.glob("STD_TOP1__*")):
    p.unlink()
    print("rm", p.name)

# also wipe workspace rec copies
WORK = m.WORK
for p in list(WORK.glob("1A02.rec.pdb")) + list(WORK.glob("1K4T.rec.pdb")):
    p.unlink(missing_ok=True)

# force re-prepare note in cache kept (same PDB ids)

c_pairs = pd.read_csv(SEL / "配对_成分_Cstar.csv", encoding="utf-8-sig")
m_pairs = pd.read_csv(SEL / "配对_代谢物_Cstar.csv", encoding="utf-8-sig")

redo_c = c_pairs[c_pairs["gene"].isin(["FOS", "TOP1"])].copy()
redo_m = m_pairs[m_pairs["gene"].isin(["FOS", "TOP1"])].copy()
print("redo compound", redo_c[["compound", "gene"]].to_string(index=False))
print("redo metabolite", redo_m[["metabolite", "gene"]].to_string(index=False))

tmp_full = OUT_DOCK / "_tmp_redo_full.csv"
tmp_sum = OUT_DOCK / "_tmp_redo_sum.csv"

frames_full = []
frames_sum = []
if len(redo_c):
    m.dock_table(redo_c, "compound", tmp_full, tmp_sum)
    frames_full.append(pd.read_csv(tmp_full))
    frames_sum.append(pd.read_csv(tmp_sum).assign(ligand_col="compound"))
if len(redo_m):
    m.dock_table(redo_m, "metabolite", tmp_full, tmp_sum)
    # dock_table overwrites; read with ligand name metabolite
    f = pd.read_csv(tmp_full)
    s = pd.read_csv(tmp_sum)
    frames_full.append(f)
    frames_sum.append(s)

# merge back into compound / metabolite tables
comp_full = OUT_DOCK / "成分对接全表.csv"
comp_sum = OUT_DOCK / "成分对接汇总.csv"
met_full = OUT_DOCK / "代谢物对接全表.csv"
met_sum = OUT_DOCK / "代谢物对接汇总.csv"

# redocked compound rows
if len(redo_c):
    # re-run only compounds to get clean files
    m.dock_table(redo_c, "compound", tmp_full, tmp_sum)
    new_cf = pd.read_csv(tmp_full)
    new_cs = pd.read_csv(tmp_sum)
    old_cf = pd.read_csv(comp_full)
    old_cs = pd.read_csv(comp_sum)
    # drop old FOS/TOP1 compound rows
    genes = set(redo_c["gene"])
    ligs = set(redo_c["compound"])
    old_cf = old_cf[~((old_cf["gene"].isin(genes)) & (old_cf["compound"].isin(ligs)))]
    old_cs = old_cs[~((old_cs["gene"].isin(genes)) & (old_cs["compound"].isin(ligs)))]
    pd.concat([old_cf, new_cf], ignore_index=True).to_csv(comp_full, index=False, encoding="utf-8-sig")
    pd.concat([old_cs, new_cs], ignore_index=True).sort_values("mean_kcal").to_csv(
        comp_sum, index=False, encoding="utf-8-sig"
    )
    print("updated compound tables")
    print(new_cs.to_string(index=False))

if len(redo_m):
    m.dock_table(redo_m, "metabolite", tmp_full, tmp_sum)
    new_mf = pd.read_csv(tmp_full)
    new_ms = pd.read_csv(tmp_sum)
    old_mf = pd.read_csv(met_full)
    old_ms = pd.read_csv(met_sum)
    genes = set(redo_m["gene"])
    ligs = set(redo_m["metabolite"])
    old_mf = old_mf[~((old_mf["gene"].isin(genes)) & (old_mf["metabolite"].isin(ligs)))]
    old_ms = old_ms[~((old_ms["gene"].isin(genes)) & (old_ms["metabolite"].isin(ligs)))]
    pd.concat([old_mf, new_mf], ignore_index=True).to_csv(met_full, index=False, encoding="utf-8-sig")
    pd.concat([old_ms, new_ms], ignore_index=True).sort_values("mean_kcal").to_csv(
        met_sum, index=False, encoding="utf-8-sig"
    )
    print("updated metabolite tables")
    print(new_ms.to_string(index=False))

# verify no DNA in new receptors
NA = {"DA", "DC", "DG", "DT", "A", "C", "G", "T", "U"}
for rec in list(ASCII.glob("STD_FOS__*.rec.pdb")) + list(ASCII.glob("STD_TOP1__*.rec.pdb")):
    text = rec.read_text(errors="ignore").splitlines()
    na = sum(1 for ln in text if ln.startswith(("ATOM", "HETATM")) and ln[17:20].strip() in NA)
    print(rec.name, "DNA_atoms", na, "ATOM", sum(1 for ln in text if ln.startswith("ATOM")))

tmp_full.unlink(missing_ok=True)
tmp_sum.unlink(missing_ok=True)
print("DONE")
