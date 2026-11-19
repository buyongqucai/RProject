"""After HDOCK fetch: package desktop 序号文件夹 + split ST/PT + PyMOL viz for top models."""
from __future__ import annotations

import re
import shutil
import subprocess
import tarfile
from collections import Counter
from pathlib import Path

ROOT = Path(r"E:\RProject\_scratch_ppdock_6I4Q_pairs")
SCRIPTS = Path(
    r"E:\RProject\生信分析技能_BioinformaticsSkills\03_药物计算_DrugDiscovery"
    r"\蛋白蛋白对接_ProteinProteinDocking\脚本_scripts"
)
PYMOL_PY = Path(r"E:\pymol\python.exe")
DESKTOP = Path(r"C:\Users\10540\Desktop")
N_MODELS = 1  # BASELINE: only best pose (model_1); expand only if user asks topN

PAIRS = [
    {
        "key": "ACOX1_DLD",
        "desktop": "ACOX1_DLD_蛋白蛋白对接_序号文件夹",
        "jid": "6aed98eb1bfd8",
        "st_name": "ACOX1",
        "pt_name": "DLD",
        # approximate heavy-atom counts from cleaned uploads (protein+kept HET)
        "st_atoms_hint": 9951,
        "pt_atoms_hint": 7077 + 106,  # protein + FAD if present; HDOCK may drop FAD
    },
    {
        "key": "DLD_SCD",
        "desktop": "DLD_SCD_蛋白蛋白对接_序号文件夹",
        "jid": "6aed98ee37a8c",
        "st_name": "DLD",
        "pt_name": "SCD",
        "st_atoms_hint": 7077 + 106,
        "pt_atoms_hint": 2466 + 2,
    },
]


def ter_segments(pdb: Path) -> list[list[str]]:
    """Split ATOM/HETATM into TER-terminated polymer segments (HDOCK order)."""
    segs: list[list[str]] = []
    cur: list[str] = []
    for L in pdb.read_text(encoding="latin-1", errors="replace").splitlines(True):
        if L.startswith(("ATOM", "HETATM")):
            cur.append(L)
        elif L.startswith("TER") and cur:
            segs.append(cur)
            cur = []
    if cur:
        segs.append(cur)
    return segs


def split_model_st_pt(model: Path, rec: Path, st_out: Path, pt_out: Path) -> dict:
    """HDOCK reuses chain IDs: receptor segments first, then ligand (by TER order)."""
    rec_segs = ter_segments(rec)
    model_segs = ter_segments(model)
    n_rec = len(rec_segs)
    if n_rec < 1 or len(model_segs) <= n_rec:
        raise RuntimeError(
            f"bad TER split model={model.name} rec_segs={n_rec} model_segs={len(model_segs)}"
        )
    st_lines = [L for seg in model_segs[:n_rec] for L in seg]
    pt_lines = [L for seg in model_segs[n_rec:] for L in seg]
    st_out.parent.mkdir(parents=True, exist_ok=True)
    st_out.write_text("".join(st_lines) + "END\n", encoding="utf-8")
    pt_out.write_text("".join(pt_lines) + "END\n", encoding="utf-8")
    info = {
        "rec_segs": n_rec,
        "model_segs": len(model_segs),
        "n_st": len(st_lines),
        "n_pt": len(pt_lines),
        "st_chains": sorted({L[21] for L in st_lines}),
        "pt_chains": sorted({L[21] for L in pt_lines}),
    }
    print(f"  TER split {info}")
    return info


def ensure_raw_models(pair: dict) -> Path:
    raw = ROOT / f"PPDock_{pair['key']}" / "00_服务器原始包_ServerRaw" / f"hdock_{pair['jid']}"
    raw.mkdir(parents=True, exist_ok=True)
    # extract tars if present
    for tar_name in ("all_results.tar.gz", "top10_models.tar.gz", "top100_models.tar.gz"):
        tp = raw / tar_name
        if tp.is_file() and tp.stat().st_size > 1000:
            try:
                with tarfile.open(tp, "r:gz") as tf:
                    tf.extractall(raw / tar_name.replace(".tar.gz", ""))
                print("extracted", tp.name)
            except Exception as e:
                print("extract fail", tp, e)
    return raw


def find_models(raw: Path) -> list[Path]:
    models: list[Path] = []
    for p in sorted(raw.rglob("model_*.pdb")):
        if p.stat().st_size < 500:
            continue
        # skip empty placeholders like model_00
        if re.search(r"model_0+\.pdb$", p.name, re.I):
            continue
        models.append(p)
    if not models:
        for p in sorted(raw.rglob("*.pdb")):
            if p.stat().st_size < 500:
                continue
            if p.name.lower().startswith("top"):
                continue
            if p.name.lower() in ("rec.pdb", "lig.pdb", "receptor.pdb", "ligand.pdb"):
                continue
            if p.name.lower().startswith(("rec_", "lig_")):
                continue
            models.append(p)
    # unique by name; prefer larger / deeper extracted copies over empty root stubs
    by_name: dict[str, Path] = {}
    for p in models:
        prev = by_name.get(p.name)
        if prev is None or p.stat().st_size > prev.stat().st_size:
            by_name[p.name] = p

    def key(name: str):
        m = re.search(r"model[_-]?(\d+)", name, re.I)
        return (0, int(m.group(1))) if m else (1, name)

    ordered = [by_name[k] for k in sorted(by_name, key=key)]
    return ordered


def run_pymol(st: Path, pt: Path, out_dir: Path, tag: str) -> None:
    cmd = [
        str(PYMOL_PY),
        str(SCRIPTS / "pymol_pp_dock_viz_standard.py"),
        "--st",
        str(st),
        "--pt",
        str(pt),
        "--out-dir",
        str(out_dir),
        "--tag",
        tag,
    ]
    print("PYMOL", " ".join(cmd))
    subprocess.run(cmd, check=True)


def package_one(pair: dict) -> None:
    raw = ensure_raw_models(pair)
    models = find_models(raw)
    if not models:
        raise SystemExit(f"No models for {pair['key']} under {raw}")
    desk = DESKTOP / pair["desktop"]
    desk.mkdir(parents=True, exist_ok=True)
    # copy raw pack
    server_raw = desk / "00_服务器原始包_ServerRaw"
    if server_raw.exists():
        shutil.rmtree(server_raw)
    shutil.copytree(raw, server_raw)
    use = models[:N_MODELS]
    # write scores stub from Hdock.out if any
    hdock_out = next(raw.rglob("Hdock.out"), None) or next(raw.rglob("*.out"), None)
    if hdock_out:
        shutil.copy2(hdock_out, desk / hdock_out.name)
    rec = raw / "rec.pdb"
    if not rec.is_file():
        rec = next(raw.glob("rec_*.pdb"), None)
    if rec is None or not Path(rec).is_file():
        raise SystemExit(f"missing rec.pdb under {raw}")
    rec = Path(rec)

    for i, model in enumerate(use, start=1):
        task = desk / str(i)
        img = task / "图片"
        if task.exists():
            shutil.rmtree(task)
        task.mkdir(parents=True, exist_ok=True)
        img.mkdir(exist_ok=True)
        model_dst = task / f"model_{i}.pdb"
        shutil.copy2(model, model_dst)
        st_pdb = task / f"ST_{pair['st_name']}.pdb"
        pt_pdb = task / f"PT_{pair['pt_name']}.pdb"
        info = split_model_st_pt(model_dst, rec, st_pdb, pt_pdb)
        (task / "task_info.txt").write_text(
            f"pair={pair['key']}\nmodel={model.name}\n"
            f"st_chains={info['st_chains']}\npt_chains={info['pt_chains']}\n"
            f"n_st={info['n_st']}\tn_pt={info['n_pt']}\n"
            f"hdock={pair['jid']}\nsplit=TER_receptor_first\n",
            encoding="utf-8",
        )
        if PYMOL_PY.is_file():
            run_pymol(st_pdb, pt_pdb, task, str(i))
        else:
            print("WARN no pymol at", PYMOL_PY)
    print("DONE", desk)


def main() -> None:
    for pair in PAIRS:
        fetch_done = ROOT / f"PPDock_{pair['key']}" / "02_submit" / "FETCH_DONE.txt"
        raw = ROOT / f"PPDock_{pair['key']}" / "00_服务器原始包_ServerRaw" / f"hdock_{pair['jid']}"
        if not fetch_done.is_file() and not any(raw.glob("*.pdb")) and not any(raw.glob("*.tar.gz")):
            print("SKIP not fetched yet:", pair["key"])
            continue
        print("=== package", pair["key"], "===")
        package_one(pair)


if __name__ == "__main__":
    main()
