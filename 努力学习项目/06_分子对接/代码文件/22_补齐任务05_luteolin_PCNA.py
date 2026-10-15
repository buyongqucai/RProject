# -*- coding: utf-8 -*-
"""22_补齐任务05_luteolin_PCNA.py

补齐矩阵格 luteolin × PCNA（1U7B）：重编号后任务 05 此前无任务文件（旧批次 vina_legacy
−4.60±0.53 仅作历史引用）。本次为用户确认的新增计算，协议与兄弟任务完全一致：
  受体 PCNA 1U7B：复用任务 01/09 的受体（_dock_m2m/receptors/1U7B_clean_h.pdbqt）
  与盒子（p2rank rank2 PIP 沟，center_source=p2rank，与 01/09 同源同口径，地图复用
  maps/PCNA/1U7B_clean_h.maps.fld）
  配体 luteolin CID 5280445（复用 _dock_m2m/ligands/5280445_clean_h.pdbqt）
  引擎 AutoDock-GPU（AD4，nrun=20，种子 1/7/42），流程遵 SOP + DockingFrozen +
  CenterSourceRegistry。

产出：序号文件夹/05（受体/配体/output/config/log/task_info，命名同兄弟任务）。
不生成图（big/surface/detail/result 由 pymol_dock_viz_standard.py + 导出钩子 + 拼图另行产出）。

复用 21_多对多3x4批量对接_ADGPU.py 的 run_adgpu_seed / write_task_dir，保证口径一致。
"""
from __future__ import annotations

import importlib.util
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "m2m_batch", HERE / "21_多对多3x4批量对接_ADGPU.py"
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

TASK = 5
COMPOUND = "luteolin"
GENE = "PCNA"

# 与任务 01/09 完全同源同口径的盒子（p2rank rank2，PIP 沟；rg_4_5x 立方 20.6）
BOX = {
    "center": (46.529, -46.185, -10.415),
    "size": (20.6, 20.6, 20.6),
    "center_source": "p2rank",
    "center_detail": "p2rank_rank=2;file=1U7B_clean.pdb_predictions.csv;prob=0.017;d_iface=4.1A",
    "size_method": "rg_4_5x",
    "box_qc": "PASS",
    "fail_codes": "Q1(autosite_unavailable),Q5(p2rank_rank1_d13.8A)",
    "fallback_used": "p2rank",
    "ref_ligand": "",
    "site_residues": (
        "A:40,A:43,A:44,A:45,A:46,A:47,A:123,A:124,A:125,A:126,A:127,A:128,"
        "A:207,A:208,A:211,A:232,A:233,A:234,A:251,A:252,A:253,A:254,A:255"
    ),
}
REC_NOTE = (
    "protein-only (nucleic stripped); AD4 gasteiger; stripped non-target chains "
    "['B'] (FEN1(331-350) PIP-box peptide chain B)"
)


def main() -> int:
    if not mod.ADGPU.is_file():
        raise SystemExit(f"missing {mod.ADGPU}")

    rec = mod.REC_DIR / "1U7B_clean_h.pdbqt"
    lig = mod.LIG_DIR / mod.cid_name(COMPOUND)
    for p in (rec, lig):
        if not p.is_file():
            raise SystemExit(f"missing {p}")

    fld = mod.MAPS_ROOT / "PCNA" / "1U7B_clean_h.maps.fld"
    if not fld.is_file() or fld.stat().st_size < 100:
        raise SystemExit(f"missing maps (reuse 01/09): {fld}")

    run_dir = mod.RUN_ROOT / f"{TASK:02d}_{COMPOUND}_{GENE}"
    energies: dict[int, float] = {}
    for s in mod.SEEDS:
        energies[s] = mod.run_adgpu_seed(run_dir, lig, fld, s)
        print(f"[adgpu] task {TASK:02d} {COMPOUND} x {GENE} seed={s} E={energies[s]:.3f}")

    tdir = mod.write_task_dir(
        TASK, COMPOUND, GENE, BOX, rec, lig, run_dir, energies, REC_NOTE
    )
    vals = list(energies.values())
    mean = statistics.mean(vals)
    sd = statistics.stdev(vals)
    print(f"[done] task_dir={tdir}")
    print(f"[done] seed_affinities=" + ";".join(f"s{s}:{energies[s]:.3f}" for s in mod.SEEDS))
    print(f"[done] mean_kcal={mean:.3f} sd_kcal={sd:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
