#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一分子对接可视化（ST/PT/CJ/QJ）

氢键（强制）：
  cmd.distance("QJ", "(PT)", "(not PT)", quiet=1, mode=2, label=1, reset=1)

对象：
  ST = 受体口袋 cartoon（big/detail）；surface 视图仅 surface、不要 cartoon
  PT = 最佳姿态配体 sticks
  QJ = 上述 distance 氢键
  CJ = 仅参与 QJ 的受体残基 sticks（橙色）

运行：E:\\pymol\\python.exe C:\\test\\pymol_dock_viz_standard.py --jobs-root ... --all
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dock_export_common import log


def find_obabel() -> Optional[Path]:
    for p in (
        Path(r"E:\OpenBabel-3.1.1\obabel.EXE"),
        Path(r"C:\Program Files\OpenBabel-3.1.1\obabel.exe"),
        Path(shutil.which("obabel") or ""),
    ):
        if p and p.is_file():
            return p
    return None


def extract_best_pose(output_pdbqt: Path, dest: Path) -> Path:
    text = output_pdbqt.read_text(encoding="utf-8", errors="replace")
    if "MODEL" in text:
        parts = re.split(r"(?=MODEL\s+\d+)", text)
        model1 = None
        for p in parts:
            if re.match(r"MODEL\s+1\b", p.strip()) or p.lstrip().startswith("MODEL 1"):
                model1 = p
                break
        if model1 is None:
            for p in parts:
                if p.strip().startswith("MODEL"):
                    model1 = p
                    break
        if model1:
            lines = [
                ln
                for ln in model1.splitlines()
                if not ln.startswith("MODEL") and not ln.startswith("ENDMDL")
            ]
            dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return dest
    shutil.copy2(output_pdbqt, dest)
    return dest


def pose_for_pymol(output_pdbqt: Path, tmp_dir: Path) -> Path:
    """
    Extract MODEL1 then convert PDBQT→PDB for PyMOL.
    PDBQT atom types (OA/A/HD) often make PyMOL invent wrong bonds → 'crushed' sticks.
    Prefer real element PDB; fall back to pdbqt if Open Babel missing.
    """
    pdbqt = tmp_dir / "pose1.pdbqt"
    extract_best_pose(output_pdbqt, pdbqt)
    obabel = find_obabel()
    if obabel is None:
        log("  [warn] obabel not found; loading PDBQT pose (bonds may look wrong)")
        return pdbqt
    pdb = tmp_dir / "pose1.pdb"
    try:
        subprocess.run(
            [str(obabel), str(pdbqt), "-O", str(pdb)],
            check=True,
            capture_output=True,
            text=True,
        )
        if pdb.is_file() and pdb.stat().st_size > 50:
            return pdb
    except Exception as e:
        log(f"  [warn] pdbqt→pdb failed ({e}); using PDBQT")
    return pdbqt


def tilt_detail_view(cmd) -> None:
    """Avoid face-on view of planar aromatics (flavones look 'flat' on screen)."""
    try:
        cmd.turn("x", 42)
        cmd.turn("y", -28)
        cmd.turn("z", 12)
    except Exception:
        pass


def find_receptor(job: Path) -> Optional[Path]:
    recs = [
        p
        for p in job.glob("*_clean_h.pdbqt")
        if re.match(r"^[0-9A-Za-z]{4}_clean_h\.pdbqt$", p.name)
    ]
    return recs[0] if recs else None


def build_qj_and_cj(cmd, hbond_color: str, residue_color: str) -> bool:
    """
    QJ: 氢键虚线 = PT–ST 极性重原子（N/O）distance/find_pairs mode=2。
    禁止用全原子 find_pairs 回退（会把 C/Cl… 接触误画成氢键，如 job 9）。
    CJ: 仅 ST 侧成键残基，橙色 sticks。
    """
    try:
        cmd.delete("QJ")
    except Exception:
        pass
    try:
        cmd.delete("CJ")
    except Exception:
        pass

    # 1) 标准命令（记录 ret；可见虚线以下面 N/O 对为准）
    dist_ret = cmd.distance(
        "QJ", "(PT)", "(not PT)", quiet=1, mode=2, label=1, reset=1
    )

    def _pt_st_only(raw_pairs):
        out = []
        for pair in raw_pairs or []:
            try:
                (m1, i1), (m2, i2) = pair
            except Exception:
                continue
            names = {str(m1), str(m2)}
            if "PT" in names and "ST" in names:
                out.append(((m1, i1), (m2, i2)))
        return out

    # 2) 仅 N/O：先 3.2 Å，再放宽到 3.5 Å（重原子氢键常用上限）
    pt_st_pairs = []
    for cutoff in (3.2, 3.5):
        try:
            raw = (
                cmd.find_pairs(
                    "(PT and elem N+O)",
                    "((not PT) and elem N+O)",
                    mode=2,
                    cutoff=float(cutoff),
                )
                or []
            )
        except Exception:
            raw = []
        pt_st_pairs = _pt_st_only(raw)
        if pt_st_pairs:
            break

    # 仍空：直接用 N/O 选择做 distance mode=2（避免全原子污染）
    if not pt_st_pairs:
        try:
            cmd.delete("QJ")
        except Exception:
            pass
        try:
            no_ret = cmd.distance(
                "QJ",
                "(PT and elem N+O)",
                "((not PT) and elem N+O)",
                quiet=1,
                mode=2,
                label=1,
                reset=1,
            )
        except Exception:
            no_ret = 0.0
        try:
            raw = (
                cmd.find_pairs(
                    "(PT and elem N+O)",
                    "((not PT) and elem N+O)",
                    mode=2,
                    cutoff=3.5,
                )
                or []
            )
            pt_st_pairs = _pt_st_only(raw)
        except Exception:
            pt_st_pairs = []
        log(f"  QJ N+O-distance fallback no_ret={no_ret} pairs={len(pt_st_pairs)}")
    else:
        # 3) 用过滤后的 PT–ST N/O 对重写虚线（清除 step1 可能留下的非极性接触）
        try:
            cmd.delete("QJ")
        except Exception:
            pass
        for (m1, i1), (m2, i2) in pt_st_pairs:
            cmd.distance(
                "QJ",
                f"(model {m1} and index {int(i1)})",
                f"(model {m2} and index {int(i2)})",
                quiet=1,
                label=1,
            )

    if "QJ" in cmd.get_names("objects") and pt_st_pairs:
        cmd.enable("QJ")
        try:
            cmd.show("dashes", "QJ")
        except Exception:
            pass
        cmd.color(hbond_color, "QJ")
        cmd.set("dash_color", hbond_color)
        cmd.set("dash_width", 2.5)
        cmd.set("dash_gap", 0.25)
        cmd.set("dash_length", 0.08)
        try:
            cmd.hide("labels", "QJ")
        except Exception:
            pass
        log(f"  QJ pairs={len(pt_st_pairs)} dist_ret={dist_ret}")
    else:
        # 无可靠 N/O 氢键 → 不保留错误虚线
        try:
            cmd.delete("QJ")
        except Exception:
            pass
        log(f"  [warn] QJ empty (no N/O H-bonds) dist_ret={dist_ret}")

    st_sels: List[str] = []
    for (m1, i1), (m2, i2) in pt_st_pairs:
        for m, i in ((m1, i1), (m2, i2)):
            if str(m) == "ST":
                st_sels.append(f"(model ST and index {int(i)})")

    if not st_sels:
        cmd.select("CJ", "none")
        return False

    cmd.select("_qj_st", " or ".join(st_sels))
    cmd.select("CJ", "byres (_qj_st and ST)")
    try:
        cmd.delete("_qj_st")
    except Exception:
        pass

    if cmd.count_atoms("CJ") <= 0:
        return False

    cmd.show("sticks", "CJ")
    cmd.color(residue_color, "CJ")
    cmd.color(residue_color, "CJ and elem C")
    return True


def zoom_complete(cmd, selection: str, buffer: float) -> None:
    """完整入画：orient + zoom + 大幅放宽 slab，避免 ribbon/残基被近裁剪切黑。"""
    cmd.set("orthoscopic", 1)
    try:
        cmd.zoom(selection, float(buffer), complete=1)
    except TypeError:
        cmd.zoom(selection, float(buffer))
    cmd.orient(selection)
    try:
        cmd.zoom(selection, float(buffer), complete=1)
    except TypeError:
        cmd.zoom(selection, float(buffer))
    # get_view()[15]/[16] = front/rear clip；成倍放宽
    try:
        v = list(cmd.get_view())
        if len(v) >= 17:
            front, rear = float(v[15]), float(v[16])
            mid = 0.5 * (front + rear)
            half = max(abs(rear - front) * 3.0, 120.0)
            v[15] = mid - half
            v[16] = mid + half
            cmd.set_view(v)
    except Exception:
        try:
            cmd.clip("near", -500)
            cmd.clip("far", 500)
        except Exception:
            pass


def hide_all_labels(cmd) -> None:
    """big / surface：不显示任何标签。"""
    try:
        cmd.hide("labels", "all")
    except Exception:
        pass
    if "QJ" in cmd.get_names("objects"):
        try:
            cmd.hide("labels", "QJ")
        except Exception:
            pass
    if cmd.count_atoms("CJ") > 0:
        try:
            cmd.label("CJ and name CA", "")
        except Exception:
            pass
    for name in list(cmd.get_names("objects")):
        if str(name).startswith(("HBLab", "ResLab")):
            try:
                cmd.delete(name)
            except Exception:
                pass


def apply_detail_labels(cmd) -> None:
    """detail：残基 CA + QJ 氢键长度（1 位小数）；默认字体、字号 24；不外推（用户自行拖动）。"""
    # 清理旧版伪原子标签
    for name in list(cmd.get_names("objects")):
        if str(name).startswith(("HBLab", "ResLab")):
            try:
                cmd.delete(name)
            except Exception:
                pass

    cmd.set("label_size", 24)
    # PyMOL 默认字体为 label_font_id=5（勿用 7）
    cmd.set("label_font_id", 5)
    try:
        cmd.unset("label_outline_color")
        cmd.unset("label_shadow_mode")
    except Exception:
        pass
    cmd.set("label_color", "black")
    cmd.set("label_digits", 1)  # 氢键距离一位小数
    cmd.set("label_connector", 0)
    cmd.set("float_labels", 1)  # 便于在 .pse 里拖动
    cmd.set("label_position", (0.0, 0.0, 0.0))
    log("  detail labels: font_id=5 (default), size=24, digits=1, no offset")

    if cmd.count_atoms("CJ") > 0:
        cmd.label("CJ and name CA", '"%s%s" % (resn, resi)')
        cmd.show("label", "CJ and name CA")

    if "QJ" in cmd.get_names("objects"):
        try:
            cmd.show("labels", "QJ")
        except Exception:
            try:
                cmd.show("label", "QJ")
            except Exception:
                pass


def viz_one(
    job: Path,
    protein_color: str,
    residue_color: str,
    hbond_color: str,
    ligand_spectrum: str,
    width: int,
    height: int,
    detail_size: int,
    dpi: int,
    cmd,
) -> bool:
    seq = job.name
    receptor = find_receptor(job)
    output = job / "output.pdbqt"
    if receptor is None or not output.exists():
        log(f"[FAIL] missing receptor/output in {job}")
        return False

    img = job / "图片"
    img.mkdir(parents=True, exist_ok=True)
    # pose 临时文件放系统临时目录；禁止保留任务内 _png_tmp
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"dock_viz_{seq}_"))
    pose = pose_for_pymol(output, tmp_dir)

    targets = [
        img / f"big-{seq}.png",
        img / f"surface-{seq}.png",
        img / f"detail-{seq}.png",
        job / f"big-{seq}.pse",
        job / f"surface-{seq}.pse",
        job / f"detail-{seq}.pse",
    ]
    # 清理历史遗留
    legacy_tmp = job / "_png_tmp"
    if legacy_tmp.exists():
        shutil.rmtree(legacy_tmp, ignore_errors=True)

    def base_load() -> bool:
        cmd.reinitialize()
        cmd.bg_color("white")
        cmd.set("ray_opaque_background", 1)
        cmd.set("ray_trace_mode", 0)
        cmd.set("antialias", 2)
        cmd.set("depth_cue", 0)
        cmd.set("orthoscopic", 1)
        cmd.set("stick_radius", 0.18)
        cmd.set("label_digits", 1)  # 氢键距离一位小数（创建 QJ 前设定）

        cmd.load(str(receptor), "ST")
        cmd.load(str(pose), "PT")

        # 口袋裁剪（性能）；显示时仍完整框住 ST/PT/CJ/QJ
        cmd.select("pocket", "ST within 14 of PT")
        cmd.remove("ST and not pocket")
        cmd.hide("everything")

        if ligand_spectrum.lower() == "rainbow":
            cmd.spectrum("count", "rainbow", "PT and elem C")
        else:
            cmd.color(ligand_spectrum, "PT")
        cmd.show("sticks", "PT")

        has_cj = build_qj_and_cj(cmd, hbond_color=hbond_color, residue_color=residue_color)
        if has_cj:
            log(f"  CJ atoms={cmd.count_atoms('CJ')}")
        else:
            log(f"  [warn] no QJ-linked CJ for job {seq}")

        # ST 整链上色后再刷 CJ：禁止先橙后青（会把 CJ 盖成蛋白色）
        cmd.color(protein_color, "ST")
        cmd.show("cartoon", "ST")
        cmd.hide("sticks", "ST")
        if has_cj:
            cmd.show("sticks", "CJ")
            cmd.color(residue_color, "CJ")
            cmd.color(residue_color, "CJ and elem C")
            cmd.enable("QJ")
        # 配体最后再强调一次，避免被其它 color 误伤
        if ligand_spectrum.lower() == "rainbow":
            cmd.spectrum("count", "rainbow", "PT and elem C")
        else:
            cmd.color(ligand_spectrum, "PT")
        cmd.show("sticks", "PT")
        cmd.set("cartoon_transparency", 0.0, "ST")
        return has_cj

    def scene_selection(has_cj: bool) -> str:
        # QJ 为 measurement 对象，不能加入 zoom/orient 选择式
        parts = ["ST", "PT"]
        if has_cj and cmd.count_atoms("CJ") > 0:
            parts.append("CJ")
        return " or ".join(parts)

    def save_png(path: Path, w: int, h: int):
        cmd.png(str(path), width=int(w), height=int(h), dpi=dpi, ray=0)

    # ---- big：完整显示 ST cartoon + CJ + PT + QJ；无标签 ----
    has_cj = base_load()
    hide_all_labels(cmd)
    sel = scene_selection(has_cj)
    zoom_complete(cmd, sel, buffer=8.0)
    save_png(img / f"big-{seq}.png", width, height)
    cmd.save(str(job / f"big-{seq}.pse"))

    # ---- surface：仅 ST surface（不要 cartoon）+ CJ/PT/QJ；无标签 ----
    has_cj = base_load()
    cmd.hide("cartoon", "ST")
    cmd.hide("sticks", "ST")
    cmd.show("surface", "ST")
    cmd.set("transparency", 0.35, "ST")
    if has_cj:
        cmd.show("sticks", "CJ")
        cmd.color(residue_color, "CJ")
        cmd.color(residue_color, "CJ and elem C")
        cmd.enable("QJ")
    cmd.show("sticks", "PT")
    if "QJ" in cmd.get_names("objects"):
        cmd.enable("QJ")
        try:
            cmd.show("dashes", "QJ")
        except Exception:
            pass
    hide_all_labels(cmd)
    sel = scene_selection(has_cj)
    zoom_complete(cmd, sel, buffer=8.0)
    save_png(img / f"surface-{seq}.png", width, height)
    cmd.save(str(job / f"surface-{seq}.pse"))

    # ---- detail：1:1；滚轮式拉远囊括配体/残基/氢键/标签 ----
    has_cj = base_load()
    cmd.hide("surface", "ST")
    cmd.show("cartoon", "ST")
    cmd.set("cartoon_transparency", 0.85, "ST")
    if has_cj:
        cmd.show("sticks", "CJ")
        cmd.color(residue_color, "CJ")
        cmd.color(residue_color, "CJ and elem C")
        cmd.enable("QJ")
    cmd.show("sticks", "PT")
    if "QJ" in cmd.get_names("objects"):
        cmd.enable("QJ")
        try:
            cmd.show("dashes", "QJ")
        except Exception:
            pass
    if has_cj and cmd.count_atoms("CJ") > 0:
        detail_sel = "PT or CJ"
    else:
        detail_sel = "PT or ST"
    # 先构图再贴标签，避免标签计入过紧包围盒
    zoom_complete(cmd, detail_sel, buffer=8.0)
    tilt_detail_view(cmd)
    apply_detail_labels(cmd)
    try:
        cmd.zoom(detail_sel, 4.0, complete=1)
    except TypeError:
        cmd.zoom(detail_sel, 4.0)
    try:
        v = list(cmd.get_view())
        if len(v) >= 17:
            front, rear = float(v[15]), float(v[16])
            mid = 0.5 * (front + rear)
            half = max(abs(rear - front) * 2.5, 100.0)
            v[15] = mid - half
            v[16] = mid + half
            cmd.set_view(v)
    except Exception:
        pass
    save_png(img / f"detail-{seq}.png", detail_size, detail_size)
    cmd.save(str(job / f"detail-{seq}.pse"))

    shutil.rmtree(tmp_dir, ignore_errors=True)
    if legacy_tmp.exists():
        shutil.rmtree(legacy_tmp, ignore_errors=True)

    ok = all(p.exists() and p.stat().st_size > 100 for p in targets)
    log(f"[{'ok' if ok else 'FAIL'}] viz {seq}")
    return ok


def select_jobs(
    jobs_root: Path, only: Optional[List[str]], top: Optional[int], do_all: bool
) -> List[Path]:
    jobs = sorted(
        [p for p in jobs_root.iterdir() if p.is_dir() and p.name.isdigit()],
        key=lambda p: int(p.name),
    )
    if only:
        return [p for p in jobs if p.name in only]
    if do_all or top is None:
        return jobs
    summary = jobs_root.parent / "summary_vina.csv"
    if not summary.exists():
        summary = jobs_root / "summary_vina.csv"
    if summary.exists():
        from dock_summary_schema import load_summary_rows

        rows = [(r["affinity_kcal_mol"], r["task"]) for r in load_summary_rows(summary)]
        rows = [(e, sid) for e, sid in rows if sid.isdigit()]
        rows.sort(key=lambda x: x[0])
        ids = {sid for _, sid in rows[:top]}
        return [p for p in jobs if p.name in ids]
    return jobs[:top]


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Standard docking PyMOL visualization")
    ap.add_argument("--jobs-root", required=True)
    ap.add_argument("--only", default="", help="comma-separated job ids")
    ap.add_argument("--top", type=int, default=None, help="top-N strongest affinities")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--protein-color", default="cyan")
    ap.add_argument("--residue-color", default="orange")
    ap.add_argument("--hbond-color", default="yellow")
    ap.add_argument("--ligand-spectrum", default="rainbow", help="rainbow or solid color")
    ap.add_argument("--width", type=int, default=9120, help="big/surface width")
    ap.add_argument("--height", type=int, default=4164, help="big/surface height")
    ap.add_argument(
        "--detail-size",
        type=int,
        default=6000,
        help="detail square size (1:1, width=height)",
    )
    ap.add_argument("--dpi", type=int, default=600)
    args = ap.parse_args(argv)

    root = Path(args.jobs_root)
    only = [x.strip() for x in args.only.split(",") if x.strip()] or None
    jobs = select_jobs(root, only, args.top, args.all)
    if not jobs:
        log("no jobs")
        return 1

    ok_n = 0
    import __main__

    __main__.pymol_argv = ["pymol", "-cq"]
    from pymol import cmd
    import pymol

    pymol.finish_launching()
    for job in jobs:
        log(f"[pymol] {job}")
        try:
            if viz_one(
                job,
                protein_color=args.protein_color,
                residue_color=args.residue_color,
                hbond_color=args.hbond_color,
                ligand_spectrum=args.ligand_spectrum,
                width=args.width,
                height=args.height,
                detail_size=args.detail_size,
                dpi=args.dpi,
                cmd=cmd,
            ):
                ok_n += 1
        except Exception as e:
            log(f"[FAIL] viz exception job={job.name}: {e}")
    try:
        cmd.quit()
    except Exception:
        pass
    log(f"DONE {ok_n}/{len(jobs)}")
    return 0 if ok_n == len(jobs) else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
