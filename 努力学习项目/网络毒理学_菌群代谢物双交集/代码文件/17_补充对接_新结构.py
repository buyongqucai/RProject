# -*- coding: utf-8 -*-
"""17_补充对接_新结构.py —— MD 前置：换用野生型受体重对接（2026-10-09 用户确认）

决策（2026-10-09）：
  MMP9: 1GKD(E402Q 突变体) → **4H3X**（WT, 1.76Å, CC27/10B 羟肟酸）重对接 Tryptophan
  ADA : 3IAR(催化位 Ni)     → **7RTG**（人 ADA1 + Zn, 2.59Å, 无共晶配体）对接 Adenosine，
        盒心 = 催化 Zn 位置（无配体可参照）
  CYP1A1: 4I8V 不变（Indole 已对接；HEME 另按 SOP §9.10 参数化）
对接参数与首轮一致：22Å 盒、exhaustiveness 8、种子 1/7/42；受体保留 ZN（去掉 CA/溶剂/水/口袋配体）。
结果追加进 结果文件/数据文件/对接/对接全表.csv 与 对接汇总.csv（pdb 列区分新旧受体）。
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "数据文件" / "对接工作区"
OUT = ROOT / "结果文件" / "数据文件" / "对接"
MDW = Path.home() / "md_inputs"          # 下载的受体 PDB
OB = Path.home() / "dockenv/bin/obabel"
VINA = Path.home() / "dockenv/bin/vina"
SEEDS = [1, 7, 42]
BOX = 22.0
DROP_RES = {"HOH", "GOL", "PEG", "PGO", "NO3", "SO4", "PO4", "EDO", "DMS", "ACT",
            "CL", "NA", "K", "MG", "CA"}          # CA：对接阶段去、MD 阶段另行保留
KEEP_RES = {"ZN", "HEM"}

JOBS = [
    # (tag, pdb, site_res 或 None=用ZN, metabolite)
    ("MMP9__Tryptophan_4H3X", "4H3X", "10B", "Tryptophan"),
    ("ADA__Adenosine_7RTG", "7RTG", None, "Adenosine"),   # 无口袋配体 → 盒心用 ZN
]


def run(cmd, timeout=300) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return p.stdout + p.stderr


def prep_receptor(pdb_file: Path, site_res: str | None, tag: str):
    lines = pdb_file.read_text(errors="ignore").splitlines()
    # 口袋参照：site_res 有机配体 或 ZN
    ref_res = site_res or "ZN"
    ref = [l for l in lines if l.startswith("HETATM") and l[17:20].strip() == ref_res]
    if not ref:
        raise RuntimeError(f"无参照配体 {ref_res}")
    # 连通分量聚类取最大簇（多拷贝时用一拷贝）
    pts = [(float(l[30:38]), float(l[38:46]), float(l[46:54])) for l in ref]
    clusters: list[list[tuple]] = []
    for p in pts:
        for c in clusters:
            if any((p[0]-q[0])**2+(p[1]-q[1])**2+(p[2]-q[2])**2 <= 16 for q in c):
                c.append(p); break
        else:
            clusters.append([p])
    big = max(clusters, key=len)
    center = (sum(x for x, _, _ in big)/len(big), sum(y for _, y, _ in big)/len(big),
              sum(z for _, _, z in big)/len(big))
    kept = []
    for l in lines:
        rec = l[:6].strip()
        if rec == "ATOM":
            kept.append(l)
        elif rec == "HETATM":
            res = l[17:20].strip()
            if res == ref_res and site_res and res == site_res:
                continue                       # 口袋配体去掉（盒心已取）
            if res in KEEP_RES:
                kept.append(l)
            elif res in DROP_RES or res == ref_res:
                continue
            else:
                kept.append(l)                 # 未知杂基保守保留
    rec_pdb = WORK / f"{tag}.rec.pdb"
    rec_pdb.write_text("\n".join(kept) + "\n")
    rec_pdbqt = WORK / f"{tag}.rec.pdbqt"
    msg = run([str(OB), str(rec_pdb), "-O", str(rec_pdbqt), "-xr"], 240)
    if not rec_pdbqt.exists():
        raise RuntimeError("obabel 受体失败 " + msg[-200:])
    return rec_pdbqt, center


def main() -> None:
    # 配体 SMILES（面板）
    panel = pd.concat([
        pd.read_csv(ROOT / "结果文件" / "数据文件" / "代谢物/代谢物主面板.csv", encoding="utf-8-sig"),
        pd.read_csv(ROOT / "结果文件" / "数据文件" / "代谢物/代谢物全库敏感性.csv", encoding="utf-8-sig"),
    ]).drop_duplicates("metabolite")
    smiles = dict(zip(panel["metabolite"], panel["canonical_smiles"]))

    full = pd.read_csv(OUT / "对接全表.csv", encoding="utf-8-sig")
    rows, fails = [], []
    for tag, pdbid, site_res, met in JOBS:
        try:
            smi = smiles[met]
            rec_pdbqt, center = prep_receptor(MDW / f"{pdbid}.pdb", site_res, tag)
            lig_pdbqt = WORK / f"{tag}.lig.pdbqt"
            msg = run([str(OB), f"-:{smi}", "--gen3d", "-h", "-O", str(lig_pdbqt)], 180)
            if not lig_pdbqt.exists():
                raise RuntimeError("配体失败 " + msg[-150:])
            coords = [float(l[30:38]) for l in lig_pdbqt.read_text(errors="ignore").splitlines()
                      if l.startswith("ATOM")]
            if coords and max(abs(c) for c in coords) < 1e-6:
                raise RuntimeError("配体坐标全0")
            site = f"center-from:{site_res or 'ZN'}"
            for seed in SEEDS:
                outp = WORK / f"{tag}_s{seed}.pdbqt"
                log = run([str(VINA), "--receptor", str(rec_pdbqt), "--ligand", str(lig_pdbqt),
                           "--center_x", f"{center[0]:.3f}", "--center_y", f"{center[1]:.3f}",
                           "--center_z", f"{center[2]:.3f}",
                           "--size_x", str(BOX), "--size_y", str(BOX), "--size_z", str(BOX),
                           "--exhaustiveness", "8", "--seed", str(seed), "--cpu", "2",
                           "--out", str(outp)], 600)
                (WORK / f"{tag}_s{seed}.log").write_text(log, encoding="utf-8")
                m = re.search(r"^\s*\d+\s+(-?\d+\.\d+)\s", log, re.M) or \
                    re.search(r"Affinity:\s+(-?\d+\.\d+)", log)
                if not m:
                    raise RuntimeError("vina 无亲和力: " + log[-250:])
                kcal = float(m.group(1))
                rows.append({"metabolite": met, "gene": tag.split("__")[0], "uniprot": "",
                             "pdb": pdbid, "site": site, "seed": seed, "exhaustiveness": 8,
                             "box_A": BOX, "affinity_kcal_mol": kcal, "affinity_sd": None,
                             "affinity_kJ_mol": round(kcal * 4.184, 2),
                             "pass_threshold_kJ": (kcal * 4.184) <= -20.9})
            print(f"[OK] {met} x {tag} ({pdbid})")
        except Exception as e:
            fails.append({"pair": tag, "error": str(e)})
            print(f"[FAIL] {tag}: {e}")

    if rows:
        new = pd.DataFrame(rows)
        full = pd.concat([full, new], ignore_index=True)
        full = full.drop_duplicates(subset=["metabolite", "gene", "pdb", "seed"], keep="last")
        full.to_csv(OUT / "对接全表.csv", index=False, encoding="utf-8-sig")
        g = full.groupby(["metabolite", "gene", "pdb", "site"]).agg(
            mean_kJ=("affinity_kJ_mol", "mean"), sd_kJ=("affinity_kJ_mol", "std"),
            min_kJ=("affinity_kJ_mol", "min"),
            pass_rate=("pass_threshold_kJ", "mean"), n_runs=("seed", "nunique"),
        ).reset_index().sort_values("mean_kJ")
        g.to_csv(OUT / "对接汇总.csv", index=False, encoding="utf-8-sig")
        print("\n=== 新增行 ===")
        print(new.groupby(["metabolite", "gene", "pdb"])["affinity_kJ_mol"]
              .agg(["mean", "std", "count"]).to_string())
    if fails:
        pd.DataFrame(fails).to_csv(OUT / "对接失败清单_新结构.csv", index=False, encoding="utf-8-sig")
        print("失败:", fails)


if __name__ == "__main__":
    main()
