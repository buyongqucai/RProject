# -*- coding: utf-8 -*-
"""12_分子对接.py —— Phase 5：核心对分子对接（Vina，3 次独立重复）

配对来源：结果文件/数据文件/机制层/核心代谢物靶点配对.csv（真实存在对 + Tier A 排名）。
受体结构：RCSB Search API 按 UniProt 精确检索 → 选带合适有机共晶配体的最优 entry；
          口袋中心 = 共晶配体重原子质心；无共晶配体时 = 蛋白几何中心（标注 blind docking）。
配体：代谢物面板 canonical_smiles（PubChem），Open Babel gen3d + 加氢。
重复：3 个独立随机种子（1/7/42），exhaustiveness=8。
阈值：|−20.9 kJ/mol| ≈ −4.99 kcal/mol（计划 §4 Phase 5 中文文献口径）。

输出：结果文件/数据文件/对接/对接全表.csv（每对×3重复）、对接汇总.csv、对接_摘要.json
结论边界：对接=结合候选，不作疗效/毒性结论（项目规范 §2）。
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "结果文件" / "数据文件" / "对接"
WORK = ROOT / "数据文件" / "对接工作区"
OUT.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)

OB = Path.home() / "dockenv/bin/obabel"
VINA = Path.home() / "dockenv/bin/vina"
SEEDS = [1, 7, 42]
EXHAUST = 8
BOX = 22.0                      # Å，共晶口袋 22Å 立方
THRESH_KJ = -20.9
SOLVENT_BLACK = {"SO4", "PO4", "GOL", "EDO", "PEG", "DMS", "ACT", "ACE", "MLI", "TRS",
                 "MPD", "PG4", "1PE", "P6G", "BTB", "FMT", "AZI", "NO3", "NH4", "IOD",
                 "BR", "CL", "NA", "K", "MG", "CA", "MN", "CD", "NI", "CO", "CU"}
COFACTOR_KEEP = {"HEM", "HEB", "HEC", "HEA", "BHC", "VER", "HEX", "OR", "FAD", "FMN",
                 "NAD", "NDP", "ZN", "SF4", "FES", "PLP", "B12", "CBL"}

# (metabolite, gene, uniprot)
PAIRS = [
    ("Butyrate", "PPARG", "P37231"),
    ("Phenylalanine", "PPARG", "P37231"),
    ("Arginine", "NOS3", "P29476"),       # 人 iNOS(P35212) 无 PDB；NOS3 在配对表中同为精氨酸家族高分对
    ("Tryptophan", "MPO", "P05164"),
    ("Indole", "CYP1A1", "P04798"),
    ("4-Hydroxyphenylacetic acid", "CA2", "P00918"),
    ("Adenosine", "ADA", "P00813"),
    ("Tryptophan", "MMP9", "P14780"),
    ("Indole-3-acetic acid", "ACHE", "P22303"),
]


def http_json(url: str, payload: dict | None = None, retries: int = 3) -> dict:
    import time
    last = None
    for i in range(retries):
        try:
            if payload is None:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            else:
                req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                             headers={"Content-Type": "application/json",
                                                      "User-Agent": "Mozilla/5.0"})
            d = json.load(urllib.request.urlopen(req, timeout=30))
            time.sleep(0.12)                     # RCSB 轻限速
            return d
        except Exception as e:                   # 含连接被拒/429/5xx → 退避重试
            last = e
            time.sleep(1.2 * (i + 1))
    raise RuntimeError(f"http失败 {url}: {last}")


STRUCT_CACHE = WORK / "structure_cache.json"


def load_cache() -> dict:
    return json.loads(STRUCT_CACHE.read_text()) if STRUCT_CACHE.exists() else {}


def save_cache(c: dict) -> None:
    STRUCT_CACHE.write_text(json.dumps(c, ensure_ascii=False, indent=1))


def search_entries(uniprot: str) -> list[str]:
    q = {"query": {"type": "terminal", "service": "text",
                   "parameters": {"attribute":
                                  "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                                  "operator": "exact_match", "value": uniprot}},
         "request_options": {"paginate": {"start": 0, "rows": 25}},
         "return_type": "entry"}
    d = http_json("https://search.rcsb.org/rcsbsearch/v2/query", q)
    return [h["identifier"] for h in d.get("result_set", [])]


def search_entries_safe(uniprot: str) -> list[str]:
    try:
        return search_entries(uniprot)
    except Exception:
        return []                                  # 空响应≈无结果（RCSB 对零命中返回空 body）


def bad_pdbs() -> set:
    p = WORK / "bad_pdb.txt"
    return set(p.read_text().split()) if p.exists() else set()


def mark_bad(entry_id: str) -> None:
    p = WORK / "bad_pdb.txt"
    p.write_text((p.read_text() + " " + entry_id).strip() + "\n" if p.exists() else entry_id + "\n")


def pick_entry(entry_ids: list[str]) -> tuple[str, str | None, str]:
    """返回 (entry_id, 共晶有机配体 comp_id, 口袋来源说明)"""
    bad = bad_pdbs()
    entry_ids = [e for e in entry_ids if e not in bad]
    if not entry_ids:
        raise RuntimeError("所有候选结构均不可用")
    best = (None, None, None)   # (score, entry, comp)
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
            break                              # 首个带合适配体的合格结构即用
    if best[1] is None:
        raise RuntimeError("无可用结构")
    return best[1], best[2], ("co-ligand:" + best[2]) if best[2] else "blind(geometric center)"


def download_pdb(entry_id: str, dest: Path) -> bool:
    url = f"https://files.rcsb.org/download/{entry_id}.pdb"   # 仅接受 legacy PDB（cif 候选自动跳过）
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
    """过滤 PDB：保留蛋白+辅因子，去掉水/溶剂/口袋配体；返回 (rec_pdb, center, site_note)"""
    lines = pdb.read_text(errors="ignore").splitlines()
    is_cif = lines and lines[0].startswith("data_")
    kept, het_lig = [], []
    if is_cif:
        raise RuntimeError("mmCIF 回退未实现")   # 候选列表里会优先有 PDB 的 entry
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
            if res in COFACTOR_KEEP:      # 仅保留辅因子；其余杂配体一律去除
                kept.append(ln)
    if het_lig:
        pts = [(float(l[30:38]), float(l[38:46]), float(l[46:54])) for l in het_lig]
        # 多拷贝共晶配体 → 连通分量聚类(4Å，与簇内任一原子相连即入簇)，取最大簇质心
        clusters: list[list[tuple]] = []
        for p in pts:
            for c in clusters:
                if any((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2 <= 16.0
                       for q in c):
                    c.append(p)
                    break
            else:
                clusters.append([p])
        big = max(clusters, key=len)
        center = (sum(p[0] for p in big) / len(big),
                  sum(p[1] for p in big) / len(big),
                  sum(p[2] for p in big) / len(big))
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


def run(cmd: list[str], timeout: int = 300) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return p.stdout + p.stderr


def main() -> None:
    panel = pd.concat([
        pd.read_csv(ROOT / "结果文件" / "数据文件" / "代谢物/代谢物主面板.csv", encoding="utf-8-sig"),
        pd.read_csv(ROOT / "结果文件" / "数据文件" / "代谢物/代谢物全库敏感性.csv", encoding="utf-8-sig"),
    ]).drop_duplicates("metabolite")
    smiles = dict(zip(panel["metabolite"], panel["canonical_smiles"]))

    # 断点续跑：已有 3 次重复的对直接跳过
    res_file = OUT / "对接全表.csv"
    existing = pd.read_csv(res_file, encoding="utf-8-sig") if res_file.exists() else pd.DataFrame()
    done: set = set()
    if len(existing):
        for (m, g), n in existing.groupby(["metabolite", "gene"]).size().items():
            if n >= len(SEEDS):
                done.add((m, g))
        print(f"已有完成对：{len(done)}")

    rows, fails = [], []
    for met, gene, up in PAIRS:
        if (met, gene) in done:
            continue
        tag = f"{gene}__{re.sub(r'[^A-Za-z0-9]+', '', met)[:20]}"
        try:
            smi = smiles.get(met)
            if not isinstance(smi, str) or not smi:
                raise RuntimeError("无 SMILES")
            # 1) 结构（带基因级缓存）
            scache = load_cache()
            if gene in scache:
                entry_id, lig, site_note = scache[gene]
            else:
                entries = search_entries_safe(up)
                if not entries:
                    raise RuntimeError(f"RCSB 无 {up} 结构（或检索空响应）")
                entry_id, lig, site_note = pick_entry(entries)
                scache[gene] = [entry_id, lig, site_note]
                save_cache(scache)
            pdb = WORK / f"{entry_id}.pdb"
            if not pdb.exists() and not download_pdb(entry_id, pdb):
                mark_bad(entry_id)
                scache.pop(gene, None); save_cache(scache)
                raise RuntimeError(f"PDB {entry_id} 下载失败（已标记，重跑将换结构）")
            rec_pdb, center, site_note = prepare_receptor(pdb, lig)
            rec_pdbqt = WORK / f"{tag}.rec.pdbqt"
            msg = run([str(OB), str(rec_pdb), "-O", str(rec_pdbqt), "-xr"], 240)  # -xr 刚性受体，强制重建
            if not rec_pdbqt.exists():
                raise RuntimeError("obabel 受体失败: " + msg[-200:])
            head = rec_pdbqt.read_text(errors="ignore")[:400]
            if "active torsions" in head and not re.search(r"active torsions:\s+0\b", head):
                raise RuntimeError("受体仍含可旋转键（-xr 未生效）")
            # 2) 配体
            lig_pdbqt = WORK / f"{tag}.lig.pdbqt"
            msg = run([str(OB), f'-:{smi}', "--gen3d", "-h", "-O", str(lig_pdbqt)], 180)
            if not lig_pdbqt.exists():
                raise RuntimeError("obabel 配体失败: " + msg[-200:])
            # 防御：gen3d 静默失败时坐标全 0（本构建 "--gen3d fast" 会触发）
            coords = [float(l[30:38]) for l in lig_pdbqt.read_text(errors="ignore").splitlines()
                      if l.startswith("ATOM")]
            if coords and max(abs(c) for c in coords) < 1e-6:
                msg = run([str(OB), f'-:{smi}', "--gen3d", "-h", "-O", str(lig_pdbqt)], 180)  # 覆盖重写
                if not lig_pdbqt.exists():
                    raise RuntimeError("obabel 配体重试失败: " + msg[-200:])
                coords = [float(l[30:38]) for l in lig_pdbqt.read_text(errors="ignore").splitlines()
                          if l.startswith("ATOM")]
                if coords and max(abs(c) for c in coords) < 1e-6:
                    raise RuntimeError("配体坐标全 0（gen3d 失败）")
            # 3) 3 次独立重复
            for seed in SEEDS:
                outp = WORK / f"{tag}_s{seed}.pdbqt"
                log = run([str(VINA), "--receptor", str(rec_pdbqt), "--ligand", str(lig_pdbqt),
                           "--center_x", f"{center[0]:.3f}", "--center_y", f"{center[1]:.3f}",
                           "--center_z", f"{center[2]:.3f}",
                           "--size_x", str(BOX), "--size_y", str(BOX), "--size_z", str(BOX),
                           "--exhaustiveness", str(EXHAUST), "--seed", str(seed), "--cpu", "2",
                           "--out", str(outp)], 600)
                m = re.search(r"^\s*\d+\s+(-?\d+\.\d+)\s", log, re.M) \
                    or re.search(r"Affinity:\s+(-?\d+\.\d+)\s+\(\s*(-?\d+\.\d+)\)", log)
                (WORK / f"{tag}_s{seed}.log").write_text(log, encoding="utf-8")   # 留档排查
                if not m:
                    raise RuntimeError("vina 无亲和力输出(见log): " + log[-300:])
                kcal = float(m.group(1))
                sd = float(m.group(2)) if (m.lastindex or 0) >= 2 else None
                rows.append({"metabolite": met, "gene": gene, "uniprot": up,
                             "pdb": entry_id, "site": site_note,
                             "seed": seed, "exhaustiveness": EXHAUST, "box_A": BOX,
                             "affinity_kcal_mol": kcal, "affinity_sd": sd,
                             "affinity_kJ_mol": round(kcal * 4.184, 2),
                             "pass_threshold_kJ": (kcal * 4.184) <= THRESH_KJ})
            print(f"[OK] {met} x {gene} ({entry_id}, {site_note})")
            # 增量落盘（防单次运行超时丢失）
            pd.concat([existing, pd.DataFrame(rows)], ignore_index=True).to_csv(
                res_file, index=False, encoding="utf-8-sig")
        except Exception as ex:
            fails.append({"metabolite": met, "gene": gene, "uniprot": up, "error": str(ex)})
            print(f"[FAIL] {met} x {gene}: {ex}")

    df = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True) if len(existing) else pd.DataFrame(rows)
    if len(df):
        df = df.drop_duplicates(subset=["metabolite", "gene", "seed"], keep="last")
        df.to_csv(OUT / "对接全表.csv", index=False, encoding="utf-8-sig")
        g = df.groupby(["metabolite", "gene", "pdb", "site"]).agg(
            mean_kJ=("affinity_kJ_mol", "mean"), sd_kJ=("affinity_kJ_mol", "std"),
            min_kJ=("affinity_kJ_mol", "min"),
            pass_rate=("pass_threshold_kJ", "mean"), n_runs=("seed", "nunique"),
        ).reset_index().sort_values("mean_kJ")
        g.to_csv(OUT / "对接汇总.csv", index=False, encoding="utf-8-sig")
        print("\n=== 对接汇总（mean kJ/mol，越低越强）===")
        print(g.to_string(index=False))
    if fails:
        pd.DataFrame(fails).to_csv(OUT / "对接失败清单.csv", index=False, encoding="utf-8-sig")
    (OUT / "对接_摘要.json").write_text(json.dumps(
        {"n_pairs_done": df["gene"].nunique() if len(df) else 0, "n_runs": len(df),
         "threshold_kJ": THRESH_KJ, "fails": fails}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"\n完成 {df['gene'].nunique() if len(df) else 0} 对 / {len(df)} 次运行；失败 {len(fails)}")


if __name__ == "__main__":
    main()
