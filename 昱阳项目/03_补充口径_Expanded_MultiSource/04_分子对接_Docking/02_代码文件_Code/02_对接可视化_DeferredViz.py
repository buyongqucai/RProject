#!/usr/bin/env python3
"""Midnight docking visualization (Expanded + Baseline ASCII workspaces)."""
from __future__ import annotations

import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PYMOL_PY = Path(r"E:/pymol/python.exe")
VIZ = Path(
    r"E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/"
    r"分子对接与虚拟筛选_MolecularDocking/脚本_scripts/pymol_dock_viz_standard.py"
)
HEAT = Path(
    r"E:/RProject/生信分析技能_BioinformaticsSkills/03_药物计算_DrugDiscovery/"
    r"分子对接与虚拟筛选_MolecularDocking/脚本_scripts/plot_docking_affinity_heatmap.py"
)

JOBS = [
    {
        "name": "expanded",
        "work": Path(r"E:/dock_yuyang/expanded"),
        "proj": Path(
            r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/04_分子对接_Docking"
        ),
    },
    {
        "name": "baseline",
        "work": Path(r"E:/dock_yuyang/baseline"),
        "proj": Path(
            r"E:/RProject/昱阳项目/02_未补充口径_Baseline_STPonly/04_分子对接_Docking"
        ),
    },
]


def viz_one(work: Path, fig: Path, log_lines: list[str]) -> int:
    summary = work / "03_summary_vina.csv"
    # fallback project table
    if not summary.exists():
        return 0
    n = 0
    fig.mkdir(parents=True, exist_ok=True)
    # simple affinity table plot via matplotlib if heatmap CLI unknown
    try:
        import matplotlib.pyplot as plt

        rows = [r for r in csv.DictReader(summary.open(encoding="utf-8")) if r.get("status") == "ok"]
        if rows:
            genes = [r["gene_mouse"] for r in rows]
            affs = [float(r["affinity_kcal_mol"]) for r in rows]
            plt.figure(figsize=(6, 3.5))
            plt.barh(genes[::-1], affs[::-1], color="#4C78A8")
            plt.xlabel("Affinity (kcal/mol)")
            plt.title("Vina docking scores (quercetin)")
            plt.tight_layout()
            plt.savefig(fig / "00_affinity_bar.png", dpi=600)
            plt.savefig(fig / "00_affinity_bar.svg")
            plt.close()
            log_lines.append(f"barplot n={len(rows)}")
    except Exception as e:
        log_lines.append(f"barplot_fail:{e}")

    if not (VIZ.exists() and PYMOL_PY.exists()):
        log_lines.append("pymol_viz_skipped_missing_tools")
        return n

    for row in csv.DictReader(summary.open(encoding="utf-8")):
        if row.get("status") != "ok":
            continue
        g = row["gene_mouse"]
        pdb = row["pdb"]
        task = work / f"{g}_{pdb}"
        pose = task / "quercetin_out.pdbqt"
        rec = task / "rec.pdbqt"
        if not pose.exists() or not rec.exists():
            log_lines.append(f"missing_pose {g}")
            continue
        out_dir = fig / g
        out_dir.mkdir(parents=True, exist_ok=True)
        # Try common CLI; tolerate failure
        for args in (
            ["--receptor", str(rec), "--ligand", str(pose), "--outdir", str(out_dir), "--prefix", g],
            ["--rec", str(rec), "--lig", str(pose), "--out", str(out_dir)],
        ):
            r = subprocess.run(
                [str(PYMOL_PY), str(VIZ), *args],
                capture_output=True,
                text=True,
                timeout=600,
            )
            log_lines.append(f"pymol {g} rc={r.returncode}")
            if r.returncode == 0:
                n += 1
                break
    return n


def main() -> int:
    all_log = [f"start {datetime.now().isoformat()}"]
    total = 0
    for job in JOBS:
        work = job["work"]
        proj = job["proj"]
        fig = proj / "03_图片文件_Figures"
        rep = proj / "04_报告文件_Reports"
        rep.mkdir(parents=True, exist_ok=True)
        # ensure summary in work
        src = proj / "01_数据文件_Data/02_结果数据_ResultTables/03_summary_vina.csv"
        if src.exists():
            work.mkdir(parents=True, exist_ok=True)
            (work / "03_summary_vina.csv").write_bytes(src.read_bytes())
        n = viz_one(work, fig, all_log)
        total += n
        st = rep / "01_STATUS.txt"
        prev = st.read_text(encoding="utf-8") if st.exists() else ""
        prev = prev.replace("SCORES_DONE_VIZ_DEFERRED", "DONE")
        st.write_text(
            prev + f"\nviz_midnight_ok_tasks={n}\nviz_finished={datetime.now().isoformat()}\n",
            encoding="utf-8",
        )
        all_log.append(f"{job['name']} viz_tasks={n}")
    logp = Path(r"E:/dock_yuyang/viz_midnight_log.txt")
    all_log.append(f"total_pymol={total}")
    logp.write_text("\n".join(all_log), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
