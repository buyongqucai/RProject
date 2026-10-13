# -*- coding: utf-8 -*-
"""18_活性成分对接.py —— Phase 5b：活性成分 × C 靶点（与代谢物对接统一口径）

逻辑见：结果文件/报告文件/对接选型逻辑_成分与代谢物统一.md
配对表：数据文件/结果数据/对接/核心成分靶点配对.csv
受体：复用代谢物对接 structure_cache（同基因同 PDB/口袋，便于并列）。
引擎：Windows E:\\vina\\vina.exe + E:\\OpenBabel-3.1.1\\obabel.exe
阈值：−20.9 kJ/mol；3 种子；22 Å。结论=结合候选。
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "数据文件" / "结果数据" / "对接"
WORK = ROOT / "数据文件" / "对接工作区"
# Vina/部分 Windows 工具无法打开含中文的路径 → 运行期 I/O 走 ASCII 目录
ASCII = Path(r"E:\RProject\_dock_cmp")
OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)
ASCII.mkdir(parents=True, exist_ok=True)

OB = Path(r"E:\OpenBabel-3.1.1\obabel.exe")
VINA = Path(r"E:\vina\vina.exe")
SEEDS = [1, 7, 42]
EXHAUST = 8
BOX = 22.0
THRESH_KCAL = -5.0  # FROZEN 报告单位 kcal/mol；约合 −20.9 kJ/mol
SOLVENT_BLACK = {
    "SO4", "PO4", "GOL", "EDO", "PEG", "DMS", "ACT", "ACE", "MLI", "TRS",
    "MPD", "PG4", "1PE", "P6G", "BTB", "FMT", "AZI", "NO3", "NH4", "IOD",
    "BR", "CL", "NA", "K", "MG", "CA", "MN", "CD", "NI", "CO", "CU",
}
COFACTOR_KEEP = {
    "HEM", "HEB", "HEC", "HEA", "BHC", "VER", "HEX", "OR", "FAD", "FMN",
    "NAD", "NDP", "ZN", "SF4", "FES", "PLP", "B12", "CBL",
}

STRUCT_CACHE = WORK / "structure_cache.json"
FULL_CSV = OUT / "成分对接全表.csv"
SUM_CSV = OUT / "成分对接汇总.csv"
FAIL_CSV = OUT / "成分对接失败清单.csv"


def http_json(url: str, payload: dict | None = None, retries: int = 3) -> dict:
    import time

    last = None
    for i in range(retries):
        try:
            if payload is None:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            else:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                )
            d = json.load(urllib.request.urlopen(req, timeout=30))
            time.sleep(0.12)
            return d
        except Exception as e:
            last = e
            time.sleep(1.2 * (i + 1))
    raise RuntimeError(f"http失败 {url}: {last}")


def load_cache() -> dict:
    return json.loads(STRUCT_CACHE.read_text(encoding="utf-8")) if STRUCT_CACHE.exists() else {}


def save_cache(c: dict) -> None:
    STRUCT_CACHE.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")


def search_entries(uniprot: str) -> list[str]:
    q = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                "operator": "exact_match",
                "value": uniprot,
            },
        },
        "request_options": {"paginate": {"start": 0, "rows": 25}},
        "return_type": "entry",
    }
    d = http_json("https://search.rcsb.org/rcsbsearch/v2/query", q)
    return [h["identifier"] for h in d.get("result_set", [])]


def pick_entry(entry_ids: list[str]) -> tuple[str, str | None, str]:
    bad_p = WORK / "bad_pdb.txt"
    bad = set(bad_p.read_text().split()) if bad_p.exists() else set()
    entry_ids = [e for e in entry_ids if e not in bad]
    if not entry_ids:
        raise RuntimeError("所有候选结构均不可用")
    best = (None, None, None)
    for eid in entry_ids[:10]:
        try:
            e = http_json(f"https://data.rcsb.org/rest/v1/core/entry/{eid}")
        except Exception:
            continue
        res = (e.get("rcsb_entry_info", {}).get("resolution_combined") or [99.0])[0]
        if res and res > 3.0:
            continue
        lig_ids = e.get("rcsb_entry_container_identifiers", {}).get("non_polymer_entity_ids", []) or []
        found = None
        for lid in lig_ids[:5]:
            try:
                ne = http_json(f"https://data.rcsb.org/rest/v1/core/nonpolymer_entity/{eid}/{lid}")
                cid = (ne.get("rcsb_nonpolymer_entity_container_identifiers") or {}).get("nonpolymer_comp_id")
                if not cid:
                    continue
                cc = http_json(f"https://data.rcsb.org/rest/v1/core/chemcomp/{cid}")
            except Exception:
                continue
            comp = cc.get("chem_comp") or {}
            mw = float(comp.get("formula_weight") or 0)
            formula = comp.get("formula") or ""
            if cid in SOLVENT_BLACK or cid in COFACTOR_KEEP:
                continue
            if "C" not in formula:
                continue
            if not (90 <= mw <= 550):
                continue
            found = cid
            break
        score = (0 if found else 1, res or 99)
        if best[0] is None or score < best[0]:
            best = (score, eid, found)
        if found:
            break
    if best[1] is None:
        raise RuntimeError("无可用结构")
    return best[1], best[2], ("co-ligand:" + best[2]) if best[2] else "blind(geometric center)"


def download_pdb(entry_id: str, dest: Path) -> bool:
    url = f"https://files.rcsb.org/download/{entry_id}.pdb"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=60).read()
        if len(data) > 1000 and b"ATOM" in data[:200000]:
            dest.write_bytes(data)
            return True
    except Exception:
        return False
    return False


def prepare_receptor(pdb: Path, lig_comp: str | None) -> tuple[Path, tuple, str]:
    lines = pdb.read_text(errors="ignore").splitlines()
    if lines and lines[0].startswith("data_"):
        raise RuntimeError("mmCIF 回退未实现")
    kept, het_lig = [], []
    for ln in lines:
        rec = ln[:6].strip()
        if rec == "ATOM":
            kept.append(ln)
        elif rec == "HETATM":
            res = ln[17:20].strip()
            if res == "HOH" or res in SOLVENT_BLACK:
                continue
            if lig_comp and res == lig_comp:
                het_lig.append(ln)
                continue
            if res in COFACTOR_KEEP:
                kept.append(ln)
    if het_lig:
        pts = [(float(l[30:38]), float(l[38:46]), float(l[46:54])) for l in het_lig]
        clusters: list[list[tuple]] = []
        for p in pts:
            for c in clusters:
                if any((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2 <= 16.0 for q in c):
                    c.append(p)
                    break
            else:
                clusters.append([p])
        big = max(clusters, key=len)
        center = (
            sum(p[0] for p in big) / len(big),
            sum(p[1] for p in big) / len(big),
            sum(p[2] for p in big) / len(big),
        )
        note = f"co-ligand:{lig_comp}(largest cluster {len(big)}/{len(pts)})"
    else:
        xs = [float(l[30:38]) for l in kept if l.startswith("ATOM")]
        ys = [float(l[38:46]) for l in kept if l.startswith("ATOM")]
        zs = [float(l[46:54]) for l in kept if l.startswith("ATOM")]
        if not xs:
            raise RuntimeError("无蛋白原子")
        center = (sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs))
        note = "blind(geometric center)"
    rec_pdb = pdb.with_suffix(".rec.pdb")
    rec_pdb.write_text("\n".join(kept) + "\n")
    return rec_pdb, center, note


def run(cmd: list[str], timeout: int = 600) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return (p.stdout or "") + (p.stderr or "")


def fetch_pubchem_3d_sdf(cid: int, dest: Path) -> None:
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{int(cid)}/SDF?record_type=3d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        data = urllib.request.urlopen(req, timeout=60).read()
    except Exception:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{int(cid)}/SDF"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=60).read()
        # 2D → 尝试本地 gen3d（部分分子会失败，调用方再判）
        tmp = dest.with_suffix(".2d.sdf")
        tmp.write_bytes(data)
        msg = run([str(OB), str(tmp), "-O", str(dest), "--gen3d"], 180)
        if not dest.exists() or dest.stat().st_size < 50:
            raise RuntimeError("PubChem 无 3D 且 gen3d 失败: " + msg[-200:])
        return
    if len(data) < 50:
        raise RuntimeError(f"PubChem SDF 空 cid={cid}")
    dest.write_bytes(data)


def main() -> None:
    if not OB.exists() or not VINA.exists():
        raise SystemExit(f"缺少对接工具: OB={OB.exists()} VINA={VINA.exists()}")

    pairs = pd.read_csv(OUT / "核心成分靶点配对.csv", encoding="utf-8-sig")
    if pairs["canonical_smiles"].isna().any():
        raise SystemExit("配对表缺 SMILES，先补全 核心成分靶点配对.csv")

    existing = pd.read_csv(FULL_CSV, encoding="utf-8-sig") if FULL_CSV.exists() else pd.DataFrame()
    done: set = set()
    if len(existing):
        for (c, g), n in existing.groupby(["compound", "gene"]).size().items():
            if n >= len(SEEDS):
                done.add((c, g))
        print(f"已有完成对：{len(done)}")

    rows, fails = [], []
    scache = load_cache()

    import shutil

    for _, pr in pairs.iterrows():
        comp = str(pr["compound"])
        gene = str(pr["gene"])
        up = str(pr["uniprot"])
        cid = int(pr["pubchem_cid"])
        if (comp, gene) in done:
            continue
        tag = f"CMP_{gene}__{re.sub(r'[^A-Za-z0-9]+', '', comp)[:20]}"
        try:
            if gene in scache:
                entry_id, lig, site_note = scache[gene][0], scache[gene][1], scache[gene][2]
            else:
                entries = search_entries(up)
                if not entries:
                    raise RuntimeError(f"RCSB 无 {up} 结构")
                entry_id, lig, site_note = pick_entry(entries)
                scache[gene] = [entry_id, lig, site_note]
                save_cache(scache)

            pdb = WORK / f"{entry_id}.pdb"
            if not pdb.exists() and not download_pdb(entry_id, pdb):
                raise RuntimeError(f"PDB {entry_id} 下载失败")

            # 受体准备可在中文目录；产出拷到 ASCII 再给 Vina
            rec_pdb, center, site_note = prepare_receptor(pdb, lig)
            rec_ascii = ASCII / f"{tag}.rec.pdb"
            shutil.copy2(rec_pdb, rec_ascii)
            rec_pdbqt = ASCII / f"{tag}.rec.pdbqt"
            msg = run([str(OB), str(rec_ascii), "-O", str(rec_pdbqt), "-xr"], 240)
            if not rec_pdbqt.exists():
                raise RuntimeError("obabel 受体失败: " + msg[-200:])

            sdf = ASCII / f"{tag}.sdf"
            fetch_pubchem_3d_sdf(cid, sdf)
            lig_pdbqt = ASCII / f"{tag}.lig.pdbqt"
            msg = run([str(OB), str(sdf), "-h", "-O", str(lig_pdbqt)], 180)
            if not lig_pdbqt.exists():
                raise RuntimeError("obabel 配体失败: " + msg[-200:])
            coords = [
                float(l[30:38])
                for l in lig_pdbqt.read_text(errors="ignore").splitlines()
                if l.startswith("ATOM") or l.startswith("HETATM")
            ]
            if not coords or max(abs(c) for c in coords) < 1e-6:
                raise RuntimeError("配体坐标无效")

            for seed in SEEDS:
                outp = ASCII / f"{tag}_s{seed}.pdbqt"
                log = run(
                    [
                        str(VINA),
                        "--receptor",
                        str(rec_pdbqt),
                        "--ligand",
                        str(lig_pdbqt),
                        "--center_x",
                        f"{center[0]:.3f}",
                        "--center_y",
                        f"{center[1]:.3f}",
                        "--center_z",
                        f"{center[2]:.3f}",
                        "--size_x",
                        str(BOX),
                        "--size_y",
                        str(BOX),
                        "--size_z",
                        str(BOX),
                        "--exhaustiveness",
                        str(EXHAUST),
                        "--seed",
                        str(seed),
                        "--cpu",
                        "4",
                        "--out",
                        str(outp),
                    ],
                    900,
                )
                (ASCII / f"{tag}_s{seed}.log").write_text(log, encoding="utf-8")
                # 同步一份到课题工作区便于留档
                shutil.copy2(ASCII / f"{tag}_s{seed}.log", WORK / f"{tag}_s{seed}.log")
                if outp.exists():
                    shutil.copy2(outp, WORK / f"{tag}_s{seed}.pdbqt")
                m = re.search(r"^\s*\d+\s+(-?\d+\.\d+)\s", log, re.M) or re.search(
                    r"Affinity:\s+(-?\d+\.\d+)\s+\(\s*(-?\d+\.\d+)\)", log
                )
                if not m:
                    raise RuntimeError("vina 无亲和力: " + log[-300:])
                kcal = float(m.group(1))
                sd = float(m.group(2)) if (m.lastindex or 0) >= 2 else None
                rows.append(
                    {
                        "compound": comp,
                        "gene": gene,
                        "uniprot": up,
                        "pdb": entry_id,
                        "site": site_note,
                        "seed": seed,
                        "exhaustiveness": EXHAUST,
                        "box_A": BOX,
                        "affinity_kcal_mol": kcal,
                        "affinity_sd": sd,
                        "affinity_kJ_mol": round(kcal * 4.184, 2),
                        "pass_threshold_kcal": kcal <= THRESH_KCAL,
                    }
                )
            print(f"[OK] {comp} x {gene} ({entry_id}, {site_note})")
            pd.concat([existing, pd.DataFrame(rows)], ignore_index=True).to_csv(
                FULL_CSV, index=False, encoding="utf-8-sig"
            )
        except Exception as ex:
            fails.append({"compound": comp, "gene": gene, "uniprot": up, "error": str(ex)})
            print(f"[FAIL] {comp} x {gene}: {ex}")

    df = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True) if len(existing) or rows else pd.DataFrame()
    if len(df):
        df = df.drop_duplicates(subset=["compound", "gene", "seed"], keep="last")
        df.to_csv(FULL_CSV, index=False, encoding="utf-8-sig")
        g = (
            df.groupby(["compound", "gene", "pdb", "site"])
            .agg(
                mean_kcal=("affinity_kcal_mol", "mean"),
                sd_kcal=("affinity_kcal_mol", "std"),
                min_kcal=("affinity_kcal_mol", "min"),
                pass_rate=("pass_threshold_kcal", "mean"),
                n_runs=("seed", "nunique"),
            )
            .reset_index()
            .sort_values("mean_kcal")
        )
        g["mean_kJ"] = (g["mean_kcal"] * 4.184).round(2)
        g["sd_kJ"] = (g["sd_kcal"] * 4.184).round(2)
        g["min_kJ"] = (g["min_kcal"] * 4.184).round(2)
        g.to_csv(SUM_CSV, index=False, encoding="utf-8-sig")
        print("\n=== 成分对接汇总 (kcal/mol) ===")
        print(g[["compound", "gene", "pdb", "mean_kcal", "sd_kcal", "pass_rate"]].to_string(index=False))
    if fails:
        pd.DataFrame(fails).to_csv(FAIL_CSV, index=False, encoding="utf-8-sig")
    print(f"\n完成；失败 {len(fails)}")


if __name__ == "__main__":
    main()
