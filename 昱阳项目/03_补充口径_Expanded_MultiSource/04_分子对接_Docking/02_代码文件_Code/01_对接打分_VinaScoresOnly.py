#!/usr/bin/env python3
"""Docking SCORES only (Vina). ASCII workdir to avoid path encoding issues.

Visualization deferred to midnight job.
"""
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
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/04_分子对接_Docking"
)
RAW = PROJ / "01_数据文件_Data/01_初始数据_RawInitial"
TAB = PROJ / "01_数据文件_Data/02_结果数据_ResultTables"
REP = PROJ / "04_报告文件_Reports"
# ASCII-only workspace (Vina/OpenBabel choke on CJK paths)
WORK = Path(r"E:/dock_yuyang/expanded")
LIG_SRC = RAW / "quercetin.pdbqt"
LIG = WORK / "quercetin.pdbqt"
PRIO = TAB / "02_对接优先级_DockPriority.csv"
VINA = Path(r"E:/vina/vina.exe")
OBABEL = Path(r"E:/OpenBabel-3.1.1/obabel.exe")
TOP_N = 5

# Non-cocrystal centers from AutoSite (ADFR prepare_receptor + autosite_rank=1).
# Recompute via E:/dock_yuyang/rerun_vina_autosite.py — do not use annotated_site.
TARGETS = {
    "Akt1": {
        "gene_human": "AKT1",
        "pdb": "3cqw",
        "center": (12.373, -7.632, 20.615),
        "size": (26, 30, 22),
        "center_source": "autosite",
        "center_detail": "autosite_rank=1;file=rec_adfr_cl_001.pdb",
    },
    "Egfr": {
        "gene_human": "EGFR",
        "pdb": "1m17",
        "center": (22.0, 0.5, 53.0),
        "size": (22, 22, 22),
        "center_source": "cocrystal",
        "center_detail": "EGFR TK AQ4 site (1M17)",
    },
    "Src": {
        "gene_human": "SRC",
        "pdb": "2src",
        "center": (33.074, 43.399, 64.574),
        "size": (25, 25, 22),
        "center_source": "autosite",
        "center_detail": "autosite_rank=1;file=rec_adfr_cl_001.pdb",
    },
    "Gsk3b": {
        "gene_human": "GSK3B",
        "pdb": "1h8f",
        "center": (4.234, -5.618, 17.105),
        "size": (27, 35, 30),
        "center_source": "autosite",
        "center_detail": "autosite_rank=1;file=rec_adfr_cl_001.pdb;size_capped35",
    },
    "Hif1a": {
        "gene_human": "HIF1A",
        "pdb": "4h6j",
        "center": (6.203, -28.268, -21.192),
        "size": (22, 23, 22),
        "center_source": "autosite",
        "center_detail": "autosite_rank=1;file=rec_adfr_cl_001.pdb",
    },
}


def download_pdb(pdb_id: str, out: Path) -> None:
    url = f"https://files.rcsb.org/download/{pdb_id.upper()}.pdb"
    urllib.request.urlretrieve(url, out)


def write_protein_only(src: Path, dst: Path) -> None:
    lines = []
    for ln in src.read_text(encoding="utf-8", errors="ignore").splitlines():
        if ln.startswith("ATOM") or ln.startswith("TER") or ln.startswith("END"):
            lines.append(ln)
    dst.write_text("\n".join(lines) + "\n", encoding="ascii", errors="ignore")


def prepare_rigid_receptor(pdb_prot: Path, pdbqt: Path) -> None:
    cmd = [str(OBABEL), str(pdb_prot), "-O", str(pdbqt), "-xr"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not pdbqt.exists() or pdbqt.stat().st_size < 1000:
        raise RuntimeError(f"obabel -xr failed: {r.stderr[-500:]}")
    head = pdbqt.read_text(encoding="utf-8", errors="ignore")[:500]
    if "active torsions" in head.lower():
        raise RuntimeError("receptor still has active torsions; not rigid")


def run_vina(conf: Path, out_pdbqt: Path, log: Path) -> float | None:
    cmd = [
        str(VINA),
        "--config",
        str(conf),
        "--out",
        str(out_pdbqt),
        "--log",
        str(log),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    text = (log.read_text(encoding="utf-8", errors="ignore") if log.exists() else "")
    text += "\n" + (r.stdout or "") + "\n" + (r.stderr or "")
    m = re.search(r"^\s*1\s+(-?\d+\.\d+)", text, re.M)
    return float(m.group(1)) if m else None


def pick_genes() -> list[str]:
    rows = list(csv.DictReader(PRIO.open(encoding="utf-8")))
    genes = []
    for r in rows:
        g = r.get("gene") or ""
        if g in TARGETS and g not in genes:
            genes.append(g)
        if len(genes) >= TOP_N:
            break
    return genes or list(TARGETS)[:TOP_N]


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LIG_SRC, LIG)

    results = []
    for g in pick_genes():
        meta = TARGETS[g]
        task = WORK / f"{g}_{meta['pdb']}"
        task.mkdir(parents=True, exist_ok=True)
        pdb_raw = task / f"{meta['pdb']}.pdb"
        pdb_prot = task / f"{meta['pdb']}_prot.pdb"
        rec = task / "rec.pdbqt"
        out_qt = task / "quercetin_out.pdbqt"
        log = task / "vina.log"
        conf = task / "conf.txt"
        info = {
            "gene_mouse": g,
            "gene_human": meta["gene_human"],
            "pdb": meta["pdb"],
            "center_source": meta["center_source"],
            "center_detail": meta["center_detail"],
            "engine": "vina",
            "ligand": "quercetin_CID5280343",
            "workdir": str(task),
            "status": "pending",
        }
        try:
            if not pdb_raw.exists() or pdb_raw.stat().st_size < 500:
                print("download", meta["pdb"], flush=True)
                download_pdb(meta["pdb"], pdb_raw)
            write_protein_only(pdb_raw, pdb_prot)
            print("prepare", g, flush=True)
            prepare_rigid_receptor(pdb_prot, rec)
            cx, cy, cz = meta["center"]
            sx, sy, sz = meta["size"]
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
                        "energy_range = 3",
                    ]
                )
                + "\n",
                encoding="ascii",
            )
            (task / "task_info.json").write_text(
                json.dumps({**info, "center": [cx, cy, cz]}, indent=2), encoding="utf-8"
            )
            print("vina", g, flush=True)
            aff = run_vina(conf, out_qt, log)
            info["affinity_kcal_mol"] = aff
            info["center_x"], info["center_y"], info["center_z"] = cx, cy, cz
            info["status"] = "ok" if aff is not None else "parse_fail"
            print("  affinity", aff, flush=True)
        except Exception as e:
            info["status"] = f"error:{e}"
            info["affinity_kcal_mol"] = None
            print("FAIL", g, e, flush=True)
        results.append(info)

    out_csv = TAB / "03_summary_vina.csv"
    fields = [
        "gene_mouse",
        "gene_human",
        "pdb",
        "affinity_kcal_mol",
        "center_source",
        "center_detail",
        "center_x",
        "center_y",
        "center_z",
        "engine",
        "ligand",
        "workdir",
        "status",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)

    # mirror summary into ASCII work for midnight viz
    shutil.copy2(out_csv, WORK / "03_summary_vina.csv")

    ok = sum(1 for r in results if r.get("status") == "ok")
    (REP / "01_STATUS.txt").write_text(
        "\n".join(
            [
                "STATUS: SCORES_DONE_VIZ_DEFERRED",
                "step: 04_Docking",
                "phase: C",
                "arm: 03_补充口径_Expanded_MultiSource",
                f"engine: vina @ {VINA}",
                f"workdir_ascii: {WORK}",
                f"tasks_ok: {ok}/{len(results)}",
                f"summary: {out_csv}",
                "viz: scheduled midnight (see schtasks YuYangDockVizMidnight)",
                f"updated: {datetime.now().isoformat(timespec='minutes')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print("DONE ok", ok, "/", len(results))


if __name__ == "__main__":
    main()
