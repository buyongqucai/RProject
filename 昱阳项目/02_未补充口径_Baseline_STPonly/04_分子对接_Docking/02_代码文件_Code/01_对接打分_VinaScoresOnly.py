#!/usr/bin/env python3
"""Baseline arm docking SCORES only: Alox15 (sole STP×DEG overlap). Viz deferred."""
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

PROJ = Path(
    r"E:/RProject/昱阳项目/02_未补充口径_Baseline_STPonly/04_分子对接_Docking"
)
RAW_LIG = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/04_分子对接_Docking/"
    r"01_数据文件_Data/01_初始数据_RawInitial/quercetin.pdbqt"
)
TAB = PROJ / "01_数据文件_Data/02_结果数据_ResultTables"
REP = PROJ / "04_报告文件_Reports"
WORK = Path(r"E:/dock_yuyang/baseline")
LIG = WORK / "quercetin.pdbqt"
VINA = Path(r"E:/vina/vina.exe")
OBABEL = Path(r"E:/OpenBabel-3.1.1/obabel.exe")

META = {
    "gene_mouse": "Alox15",
    "gene_human": "ALOX15",
    "pdb": "1lox",
    "center": (-2.766, 141.27, 46.666),
    "size": (35, 26, 23),
    "center_source": "autosite",
    "center_detail": "autosite_rank=1;file=rec_adfr_cl_001.pdb;size_capped35",
}


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RAW_LIG, LIG)
    task = WORK / f"{META['gene_mouse']}_{META['pdb']}"
    task.mkdir(parents=True, exist_ok=True)
    pdb_raw = task / f"{META['pdb']}.pdb"
    pdb_prot = task / f"{META['pdb']}_prot.pdb"
    rec = task / "rec.pdbqt"
    out_qt = task / "quercetin_out.pdbqt"
    log = task / "vina.log"
    conf = task / "conf.txt"
    if not pdb_raw.exists():
        urllib.request.urlretrieve(
            f"https://files.rcsb.org/download/{META['pdb'].upper()}.pdb", pdb_raw
        )
    lines = [
        ln
        for ln in pdb_raw.read_text(encoding="utf-8", errors="ignore").splitlines()
        if ln.startswith("ATOM") or ln.startswith("TER") or ln.startswith("END")
    ]
    pdb_prot.write_text("\n".join(lines) + "\n", encoding="ascii", errors="ignore")
    subprocess.run(
        [str(OBABEL), str(pdb_prot), "-O", str(rec), "-xr"],
        capture_output=True,
        check=False,
    )
    cx, cy, cz = META["center"]
    sx, sy, sz = META["size"]
    conf.write_text(
        "\n".join(
            [
                f"receptor = {rec.as_posix()}",
                f"ligand = {LIG.as_posix()}",
                f"center_x = {cx}",
                f"center_y = {cy}",
                f"center_z = {cz}",
                f"size_x = {sx}",
                f"size_y = {sy}",
                f"size_z = {sz}",
                "exhaustiveness = 8",
                "num_modes = 9",
            ]
        )
        + "\n",
        encoding="ascii",
    )
    subprocess.run(
        [str(VINA), "--config", str(conf), "--out", str(out_qt), "--log", str(log)],
        capture_output=True,
        text=True,
    )
    text = log.read_text(encoding="utf-8", errors="ignore") if log.exists() else ""
    m = re.search(r"^\s*1\s+(-?\d+\.\d+)", text, re.M)
    aff = float(m.group(1)) if m else None
    row = {
        **{k: META[k] for k in ("gene_mouse", "gene_human", "pdb", "center_source", "center_detail")},
        "affinity_kcal_mol": aff,
        "center_x": cx,
        "center_y": cy,
        "center_z": cz,
        "engine": "vina",
        "ligand": "quercetin_CID5280343",
        "workdir": str(task),
        "status": "ok" if aff is not None else "parse_fail",
    }
    out_csv = TAB / "03_summary_vina.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        w.writeheader()
        w.writerow(row)
    (task / "task_info.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
    (REP / "01_STATUS.txt").write_text(
        "\n".join(
            [
                "STATUS: SCORES_DONE_VIZ_DEFERRED",
                "step: 04_Docking",
                "phase: C",
                "arm: 02_未补充口径_Baseline_STPonly",
                f"tasks_ok: {1 if aff is not None else 0}/1",
                f"affinity: {aff}",
                "viz: deferred with Expanded midnight job or separate",
                f"updated: {datetime.now().isoformat(timespec='minutes')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print("baseline dock", aff)


if __name__ == "__main__":
    main()
