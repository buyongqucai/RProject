#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一分子对接可视化（ST/PT/CJ/QJ）

氢键（强制）：
  cmd.distance("QJ", "(PT)", "(not PT)", quiet=1, mode=2, label=1, reset=1)

对象：
  ST = 完整受体 cartoon（big/detail）；surface 视图仅 surface、不要 cartoon
       （对接口袋由定心工具+盒子决定；可视化禁止为减负删除 ST 原子）
  PT = 最佳姿态配体 sticks
  QJ = 上述 distance 氢键
  CJ = 仅参与 QJ 的受体残基 sticks（橙色）
  detail：导出前自动旋转选角，尽量减少配体/氢键/残基及标签在 2D 截图中的相互遮挡

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


def _collect_xyz(cmd, selection: str) -> List[Tuple[float, float, float]]:
    """World-space coordinates for atoms in selection (state 1)."""
    from pymol import stored

    stored._dock_xyz = []
    try:
        cmd.iterate_state(
            1,
            selection,
            "stored._dock_xyz.append((float(x), float(y), float(z)))",
        )
    except Exception:
        return []
    return list(stored._dock_xyz)


def _project_xy_depth(
    coords: List[Tuple[float, float, float]], view
) -> List[Tuple[float, float, float]]:
    """
    Project world coords with current get_view() into camera space.
    Returns (sx, sy, depth) per point; larger depth = farther from camera (OpenGL-like).
    """
    if not coords:
        return []
    # Rotation 3x3 is view[0:9] row-major; origin of rotation view[12:15]
    r = [
        [float(view[0]), float(view[1]), float(view[2])],
        [float(view[3]), float(view[4]), float(view[5])],
        [float(view[6]), float(view[7]), float(view[8])],
    ]
    ox, oy, oz = float(view[12]), float(view[13]), float(view[14])
    out: List[Tuple[float, float, float]] = []
    for x, y, z in coords:
        dx, dy, dz = x - ox, y - oy, z - oz
        # camera-space ≈ R * (p - origin); PyMOL view stores camera→model; use R^T for model→cam
        cx = r[0][0] * dx + r[1][0] * dy + r[2][0] * dz
        cy = r[0][1] * dx + r[1][1] * dy + r[2][1] * dz
        cz = r[0][2] * dx + r[1][2] * dy + r[2][2] * dz
        out.append((cx, cy, cz))
    return out


def _occlusion_score(
    cmd,
    pt_xyz: List[Tuple[float, float, float]],
    ca_xyz: List[Tuple[float, float, float]],
) -> float:
    """
    Higher = better for a 2D screenshot: ligand in front, key points spread on screen,
    fewer near-overlaps between ligand COM / residue CAs (proxy for label/stick clash).
    """
    try:
        view = cmd.get_view()
    except Exception:
        return float("-inf")
    pt_p = _project_xy_depth(pt_xyz, view)
    ca_p = _project_xy_depth(ca_xyz, view)
    if not pt_p:
        return float("-inf")

    def mean_depth(pts):
        return sum(p[2] for p in pts) / len(pts)

    # Prefer ligand closer to camera than residue CAs (smaller cz in this convention)
    depth_term = 0.0
    if ca_p:
        depth_term = mean_depth(ca_p) - mean_depth(pt_p)

    lig_com = (
        sum(p[0] for p in pt_p) / len(pt_p),
        sum(p[1] for p in pt_p) / len(pt_p),
    )
    anchors = [lig_com] + [(p[0], p[1]) for p in ca_p]
    # Also sample a few PT heavy atoms so ligand shape isn't a single point
    step = max(1, len(pt_p) // 8)
    anchors.extend((p[0], p[1]) for p in pt_p[::step])

    min_d = 1e9
    clash = 0
    for i in range(len(anchors)):
        for j in range(i + 1, len(anchors)):
            dx = anchors[i][0] - anchors[j][0]
            dy = anchors[i][1] - anchors[j][1]
            d = (dx * dx + dy * dy) ** 0.5
            if d < min_d:
                min_d = d
            if d < 1.2:
                clash += 1

    # Spread: mean distance from ligand COM to CAs
    spread = 0.0
    if ca_p:
        spread = sum(
            ((p[0] - lig_com[0]) ** 2 + (p[1] - lig_com[1]) ** 2) ** 0.5 for p in ca_p
        ) / len(ca_p)

    return 4.0 * depth_term + 2.5 * min_d + 1.0 * spread - 3.0 * clash


def optimize_detail_camera(cmd, has_cj: bool) -> None:
    """
    Before detail PNG/.pse: sample orientations so ligand / H-bonds / CJ residues
    (and later their labels) are less mutually occluded in the 2D screenshot.
    Does not delete atoms; only rotates the camera (turn).
    """
    # Focus framing on interaction core first
    if has_cj and cmd.count_atoms("CJ") > 0:
        core = "PT or CJ"
    else:
        core = "PT"
    try:
        cmd.orient(core)
    except Exception:
        pass
    try:
        cmd.zoom(core, 4.0, complete=1)
    except TypeError:
        try:
            cmd.zoom(core, 4.0)
        except Exception:
            pass

    pt_xyz = _collect_xyz(cmd, "PT and not elem H")
    if not pt_xyz:
        pt_xyz = _collect_xyz(cmd, "PT")
    ca_sel = "CJ and name CA" if (has_cj and cmd.count_atoms("CJ") > 0) else ""
    ca_xyz = _collect_xyz(cmd, ca_sel) if ca_sel else []

    base = list(cmd.get_view())
    best_view = list(base)
    best_score = _occlusion_score(cmd, pt_xyz, ca_xyz)

    # 选角颗粒度：每 20°。绕 x、y 各扫一圈（约 36 个），不做 20×20 全组合。
    step = 20
    turns = [(a, 0, 0) for a in range(0, 360, step)]
    turns += [(0, a, 0) for a in range(step, 360, step)]

    for tx, ty, tz in turns:
        try:
            cmd.set_view(base)
            if tx:
                cmd.turn("x", float(tx))
            if ty:
                cmd.turn("y", float(ty))
            if tz:
                cmd.turn("z", float(tz))
            sc = _occlusion_score(cmd, pt_xyz, ca_xyz)
            if sc > best_score:
                best_score = sc
                best_view = list(cmd.get_view())
        except Exception:
            continue

    try:
        cmd.set_view(best_view)
    except Exception:
        pass
    log(f"  detail camera: occlusion_score={best_score:.3f} (auto-orient)")


def find_receptor(job: Path) -> Optional[Path]:
    """Locate rigid receptor pdbqt: PDBID_clean_h or uniprot_af_clean_h; skip CID ligands."""
    recs = []
    for p in job.glob("*_clean_h.pdbqt"):
        name = p.name
        if re.match(r"^[0-9A-Za-z]{4}_clean_h\.pdbqt$", name):
            recs.append(p)
        elif re.match(r"^[0-9a-z]+_af_clean_h\.pdbqt$", name, re.I):
            recs.append(p)
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
        # 与 detail 截图细虚线一致；过粗（如 2.5）在 big/surface 远景会显得像粗棒
        cmd.set("dash_width", 1.0)
        cmd.set("dash_gap", 0.35)
        cmd.set("dash_length", 0.06)
        try:
            cmd.set("dash_radius", 0.025)
        except Exception:
            pass
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


def zoom_complete(cmd, selection: str, buffer: float, do_orient: bool = True) -> None:
    """
    完整入画（相机操作，不是删原子）：
    - 对当前仍显示/选中的对象做 orient + zoom(complete)，让它们都进入画面；
    - 再放宽 near/far clip（slab），避免丝带/残基被前后裁切面切黑。
    不等于「只留口袋」；全链 ST 时画面可以很远。
    do_orient=False：仅缩放+放宽 clip，保留已选好的旋转角（detail 防遮挡后使用）。
    """
    cmd.set("orthoscopic", 1)
    if do_orient:
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


def save_draw_png(cmd, path: Path, width: int, height: int, dpi: int) -> None:
    """
    对齐 PyMOL 图形界面 Save Image → Draw (fast)：
    ray=0（禁止 Ray）；尺寸/DPI 与对话框一致。
    不用超大离屏 ray；detail 定稿 PNG 不走此函数（见截图导出）。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # Draw：先按目标像素 draw，再写出（与 GUI Draw 同路径；ray 必须为 0）
    try:
        cmd.draw(int(width), int(height), antialias=1, quiet=1)
    except TypeError:
        try:
            cmd.draw(int(width), int(height))
        except Exception:
            pass
    cmd.png(str(path), width=int(width), height=int(height), dpi=int(dpi), ray=0)


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
    skip_detail: bool = False,
) -> bool:
    seq = job.name
    receptor = find_receptor(job)
    output = job / "output.pdbqt"
    if receptor is None or not output.exists():
        log(f"[FAIL] missing receptor/output in {job}")
        return False

    img = job / "图片"
    img.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix=f"dock_viz_{seq}_"))
    pose = pose_for_pymol(output, tmp_dir)

    # detail PNG 不在此用 cmd.png 定稿；skip_detail 时不强制 detail.pse（保留手调）
    targets = [
        img / f"big-{seq}.png",
        img / f"surface-{seq}.png",
        job / f"big-{seq}.pse",
        job / f"surface-{seq}.pse",
    ]
    if not skip_detail:
        targets.append(job / f"detail-{seq}.pse")
    legacy_tmp = job / "_png_tmp"
    if legacy_tmp.exists():
        shutil.rmtree(legacy_tmp, ignore_errors=True)

    def setup_session() -> None:
        cmd.reinitialize()
        cmd.bg_color("white")
        cmd.set("ray_opaque_background", 1)
        cmd.set("ray_trace_mode", 0)
        cmd.set("antialias", 1)  # 与 GUI Draw 常用设置接近；勿盲目拉高
        cmd.set("depth_cue", 0)
        cmd.set("orthoscopic", 1)
        cmd.set("stick_radius", 0.18)
        cmd.set("label_digits", 1)
        try:
            cmd.set("use_shaders", 1)
        except Exception:
            pass

    def load_complex() -> bool:
        """只 load 一次；后续 big/surface/detail 只改显示，不 reinitialize。"""
        setup_session()
        cmd.load(str(receptor), "ST")
        cmd.load(str(pose), "PT")
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
        cmd.color(protein_color, "ST")
        cmd.show("cartoon", "ST")
        cmd.hide("sticks", "ST")
        if has_cj:
            cmd.show("sticks", "CJ")
            cmd.color(residue_color, "CJ")
            cmd.color(residue_color, "CJ and elem C")
            cmd.enable("QJ")
        if ligand_spectrum.lower() == "rainbow":
            cmd.spectrum("count", "rainbow", "PT and elem C")
        else:
            cmd.color(ligand_spectrum, "PT")
        cmd.show("sticks", "PT")
        cmd.set("cartoon_transparency", 0.0, "ST")
        return has_cj

    def scene_selection(has_cj: bool) -> str:
        parts = ["ST", "PT"]
        if has_cj and cmd.count_atoms("CJ") > 0:
            parts.append("CJ")
        return " or ".join(parts)

    def refresh_pt_cj(has_cj: bool) -> None:
        if has_cj and cmd.count_atoms("CJ") > 0:
            cmd.show("sticks", "CJ")
            cmd.color(residue_color, "CJ")
            cmd.color(residue_color, "CJ and elem C")
            if "QJ" in cmd.get_names("objects"):
                cmd.enable("QJ")
                try:
                    cmd.show("dashes", "QJ")
                except Exception:
                    pass
        cmd.show("sticks", "PT")
        if ligand_spectrum.lower() == "rainbow":
            cmd.spectrum("count", "rainbow", "PT and elem C")
        else:
            cmd.color(ligand_spectrum, "PT")

    # ---- 一次加载 ----
    has_cj = load_complex()
    sel = scene_selection(has_cj)

    # ---- big：cartoon；Draw(fast) 参数 ----
    hide_all_labels(cmd)
    cmd.hide("surface", "ST")
    cmd.show("cartoon", "ST")
    cmd.set("cartoon_transparency", 0.0, "ST")
    refresh_pt_cj(has_cj)
    zoom_complete(cmd, sel, buffer=8.0)
    save_draw_png(cmd, img / f"big-{seq}.png", width, height, dpi)
    cmd.save(str(job / f"big-{seq}.pse"))
    log(f"  wrote big Draw {width}x{height} dpi={dpi} ray=0")

    # ---- surface：仅 surface；同一会话 ----
    hide_all_labels(cmd)
    cmd.hide("cartoon", "ST")
    cmd.hide("sticks", "ST")
    cmd.show("surface", "ST")
    cmd.set("transparency", 0.35, "ST")
    refresh_pt_cj(has_cj)
    zoom_complete(cmd, sel, buffer=8.0)
    save_draw_png(cmd, img / f"surface-{seq}.png", width, height, dpi)
    cmd.save(str(job / f"surface-{seq}.pse"))
    log(f"  wrote surface Draw {width}x{height} dpi={dpi} ray=0")

    if skip_detail:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        if legacy_tmp.exists():
            shutil.rmtree(legacy_tmp, ignore_errors=True)
        ok = all(p.exists() and p.stat().st_size > 100 for p in targets)
        log(f"[{'ok' if ok else 'FAIL'}] viz {seq} (big/surface only)")
        return ok

    # ---- detail：自动选角 + 标签 → 只存 .pse；PNG 留给截图导出（防标签变小）----
    cmd.hide("surface", "ST")
    cmd.show("cartoon", "ST")
    cmd.set("cartoon_transparency", 0.85, "ST")
    refresh_pt_cj(has_cj)
    if has_cj and cmd.count_atoms("CJ") > 0:
        detail_sel = "PT or CJ"
    else:
        detail_sel = "PT or ST"
    optimize_detail_camera(cmd, has_cj=has_cj)
    apply_detail_labels(cmd)
    zoom_complete(cmd, detail_sel, buffer=8.0, do_orient=False)
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
    cmd.save(str(job / f"detail-{seq}.pse"))
    log(f"  wrote detail.pse only (no cmd.png; use screenshot export after hand-tune)")

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
    summary = None
    for base in (jobs_root.parent, jobs_root):
        for name in ("summary_adgpu.csv", "summary_vina.csv"):
            p = base / name
            if p.is_file():
                summary = p
                break
        if summary is not None:
            break
    if summary is not None:
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
    ap.add_argument("--width", type=int, default=5040, help="big/surface width (px); GUI Draw default")
    ap.add_argument("--height", type=int, default=3653, help="big/surface height (px); GUI Draw default")
    ap.add_argument(
        "--detail-size",
        type=int,
        default=4500,
        help="unused for first-pass detail PNG (screenshot export); kept for CLI compat",
    )
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument(
        "--skip-detail",
        action="store_true",
        help="only write big/surface; do not overwrite hand-tuned detail.pse",
    )
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
                skip_detail=args.skip_detail,
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
