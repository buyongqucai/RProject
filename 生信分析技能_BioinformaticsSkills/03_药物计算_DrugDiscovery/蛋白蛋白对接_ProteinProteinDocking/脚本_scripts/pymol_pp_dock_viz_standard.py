# -*- coding: utf-8 -*-
"""
Protein–protein docking PyMOL viz: ST / PT / CJ / QJ

对齐分子对接 pymol_dock_viz_standard.py：
  - 标签：black、font_id=5、size=24、digits=1；unset label_outline/shadow（无白边）
  - surface：ST surface transparency=0.35
  - detail：ST/PT cartoon_transparency 高透明；detail 定稿 PNG 禁止 cmd.png

Usage:
  E:\\pymol\\python.exe pymol_pp_dock_viz_standard.py \\
    --st ST.pdb --pt PT.pdb --out-dir <SERVER>_序号文件夹/N --tag 1

Detail 定稿：分子对接 export_detail_png_from_pse.py（手调标签后）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def log(msg: str) -> None:
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode("gbk", errors="replace").decode("gbk"), flush=True)


def build_qj_cj(cmd, hbond_color: str, residue_color: str) -> bool:
    for name in ("QJ", "CJ"):
        try:
            cmd.delete(name)
        except Exception:
            pass

    def pt_st_pairs(raw):
        out = []
        for pair in raw or []:
            try:
                (m1, i1), (m2, i2) = pair
            except Exception:
                continue
            if {str(m1), str(m2)} == {"PT", "ST"}:
                out.append(((m1, i1), (m2, i2)))
        return out

    pairs = []
    for cutoff in (3.2, 3.5):
        try:
            raw = (
                cmd.find_pairs(
                    "(PT and elem N+O)",
                    "(ST and elem N+O)",
                    mode=2,
                    cutoff=float(cutoff),
                )
                or []
            )
        except Exception:
            raw = []
        pairs = pt_st_pairs(raw)
        if pairs:
            break

    if not pairs:
        try:
            cmd.distance(
                "QJ",
                "(PT and elem N+O)",
                "(ST and elem N+O)",
                quiet=1,
                mode=2,
                label=1,
                reset=1,
            )
            raw = (
                cmd.find_pairs(
                    "(PT and elem N+O)",
                    "(ST and elem N+O)",
                    mode=2,
                    cutoff=3.5,
                )
                or []
            )
            pairs = pt_st_pairs(raw)
        except Exception:
            pairs = []

    if pairs:
        try:
            cmd.delete("QJ")
        except Exception:
            pass
        for (m1, i1), (m2, i2) in pairs:
            cmd.distance(
                "QJ",
                f"(model {m1} and index {int(i1)})",
                f"(model {m2} and index {int(i2)})",
                quiet=1,
                label=1,
            )
        cmd.enable("QJ")
        try:
            cmd.show("dashes", "QJ")
        except Exception:
            pass
        cmd.color(hbond_color, "QJ")
        cmd.set("dash_color", hbond_color)
        cmd.set("dash_width", 1.0)
        try:
            cmd.hide("labels", "QJ")
        except Exception:
            pass
        log(f"  QJ pairs={len(pairs)}")
    else:
        try:
            cmd.delete("QJ")
        except Exception:
            pass
        log("  [warn] QJ empty")

    res_keys = set()
    from pymol import stored

    for (m1, i1), (m2, i2) in pairs:
        for m, i in ((m1, i1), (m2, i2)):
            stored._pp = []
            try:
                cmd.iterate(
                    f"(model {m} and index {int(i)})",
                    "stored._pp.append((chain, resi, resn))",
                )
            except Exception:
                continue
            for t in stored._pp:
                res_keys.add((str(m),) + tuple(t))

    if res_keys:
        sels = []
        for model, chain, resi, resn in res_keys:
            sels.append(f"(model {model} and chain {chain} and resi {resi})")
        cmd.select("CJ", " or ".join(sels))
        cmd.show("sticks", "CJ")
        cmd.color(residue_color, "CJ")
        cmd.disable("CJ")
        log(f"  CJ residues={len(res_keys)}")
        return True
    log("  CJ empty")
    return False


def apply_detail_labels(cmd) -> None:
    """对齐分子对接标签；并关掉 label_bg（默认半透明白底=白边观感）。"""
    cmd.set("label_size", 24)
    cmd.set("label_font_id", 5)
    try:
        cmd.set("label_shadow_mode", 0)
    except Exception:
        pass
    cmd.set("label_outline_color", "black")
    cmd.set("label_color", "black")
    # 白边主因：默认 label_bg_transparency≈0.6 的浅色底
    try:
        cmd.unset("label_bg_color")
    except Exception:
        pass
    cmd.set("label_bg_transparency", 1.0)
    cmd.set("label_bg_outline", 0)
    cmd.set("label_digits", 1)
    cmd.set("label_connector", 0)
    cmd.set("float_labels", 1)
    cmd.set("label_position", (0.0, 0.0, 0.0))
    log("  detail labels: black, bg_transparency=1, outline=black, no white plate")

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


def hide_all_labels(cmd) -> None:
    try:
        cmd.hide("labels", "all")
    except Exception:
        pass
    try:
        cmd.hide("label", "all")
    except Exception:
        pass


def draw_png(cmd, path: Path, width: int = 5040, height: int = 3653, dpi: int = 600) -> None:
    """对齐分子对接 Save Image → Draw(fast)：ray=0。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd.bg_color("white")
    cmd.set("opaque_background", 1)
    cmd.set("ray_opaque_background", 1)
    cmd.png(str(path), width=width, height=height, dpi=dpi, ray=0)
    # flatten alpha → RGB white (Draw 偶发透明通道)
    try:
        from PIL import Image

        im = Image.open(path)
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            rgba = im.convert("RGBA")
            bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            Image.alpha_composite(bg, rgba).convert("RGB").save(path, dpi=(dpi, dpi))
        elif im.mode != "RGB":
            im.convert("RGB").save(path, dpi=(dpi, dpi))
    except Exception as e:
        log(f"  [warn] flatten png: {e}")


def render_views(
    st_pdb: Path,
    pt_pdb: Path,
    out_dir: Path,
    tag: str,
    *,
    st_color: str,
    pt_color: str,
    residue_color: str,
    hbond_color: str,
    # 透明度对齐分子对接语义：surface 0.35；detail ST 0.85；PP 双侧 cartoon 均透明
    big_cartoon_tr: float = 0.60,
    surface_tr: float = 0.35,
    detail_st_tr: float = 0.85,
    detail_pt_tr: float = 0.75,
) -> None:
    from pymol import cmd

    cmd.reinitialize()
    cmd.load(str(st_pdb), "ST")
    cmd.load(str(pt_pdb), "PT")
    cmd.hide("everything", "all")
    cmd.show("cartoon", "ST")
    cmd.show("cartoon", "PT")
    cmd.color(st_color, "ST")
    cmd.color(pt_color, "PT")
    cmd.bg_color("white")
    cmd.set("opaque_background", 1)

    has_cj = build_qj_cj(cmd, hbond_color, residue_color)
    img = out_dir / "图片"
    img.mkdir(parents=True, exist_ok=True)

    # ---- big：双侧 cartoon 半透明 + CJ/QJ；无标签 ----
    hide_all_labels(cmd)
    cmd.hide("surface", "all")
    cmd.show("cartoon", "ST or PT")
    cmd.set("cartoon_transparency", float(big_cartoon_tr), "ST")
    cmd.set("cartoon_transparency", float(big_cartoon_tr), "PT")
    if has_cj:
        cmd.enable("CJ")
        cmd.show("sticks", "CJ")
        cmd.color(residue_color, "CJ")
    if "QJ" in cmd.get_names("objects"):
        cmd.enable("QJ")
        try:
            cmd.show("dashes", "QJ")
        except Exception:
            pass
    try:
        cmd.orient("ST or PT")
        cmd.zoom("ST or PT", 2.0)
    except Exception:
        pass
    cmd.save(str(out_dir / f"big-{tag}.pse"))
    draw_png(cmd, img / f"big-{tag}.png")
    log(f"  wrote big-{tag}.pse/png (cartoon_tr={big_cartoon_tr})")

    # ---- surface：ST surface(tr=0.35) + PT cartoon；无标签 ----
    hide_all_labels(cmd)
    cmd.hide("everything", "ST")
    cmd.show("surface", "ST")
    cmd.color(st_color, "ST")
    cmd.set("transparency", float(surface_tr), "ST")
    cmd.show("cartoon", "PT")
    cmd.set("cartoon_transparency", float(big_cartoon_tr), "PT")
    if has_cj:
        cmd.enable("CJ")
        cmd.show("sticks", "CJ")
        cmd.color(residue_color, "CJ")
    if "QJ" in cmd.get_names("objects"):
        cmd.enable("QJ")
    cmd.save(str(out_dir / f"surface-{tag}.pse"))
    draw_png(cmd, img / f"surface-{tag}.png")
    log(f"  wrote surface-{tag}.pse/png (surface_tr={surface_tr})")

    # ---- detail：高透明 cartoon + 标签；只写 .pse（定稿 PNG → 分子对接截图导出）----
    hide_all_labels(cmd)
    cmd.hide("surface", "all")
    cmd.show("cartoon", "ST or PT")
    cmd.set("cartoon_transparency", float(detail_st_tr), "ST")
    cmd.set("cartoon_transparency", float(detail_pt_tr), "PT")
    cmd.color(st_color, "ST")
    cmd.color(pt_color, "PT")
    if has_cj:
        cmd.enable("CJ")
        cmd.show("sticks", "CJ")
        cmd.color(residue_color, "CJ")
    if "QJ" in cmd.get_names("objects"):
        cmd.enable("QJ")
        try:
            cmd.show("dashes", "QJ")
        except Exception:
            pass
    apply_detail_labels(cmd)
    core = "PT or CJ" if has_cj and cmd.count_atoms("CJ") > 0 else "PT"
    try:
        cmd.orient(core)
        cmd.zoom(core, 4.0)
    except Exception:
        pass
    cmd.save(str(out_dir / f"detail-{tag}.pse"))
    log(f"  wrote detail-{tag}.pse only (hand-tune → export_detail_png_from_pse)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--st", type=Path, required=True)
    ap.add_argument("--pt", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--tag", default="1")
    ap.add_argument("--st-color", default="cyan")
    ap.add_argument("--pt-color", default="salmon")
    ap.add_argument("--residue-color", default="orange")
    ap.add_argument("--hbond-color", default="yellow")
    args = ap.parse_args()
    if not args.st.is_file() or not args.pt.is_file():
        log("ERROR: --st/--pt must exist")
        sys.exit(1)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    try:
        import pymol  # noqa: F401
    except ImportError:
        log("ERROR: run with E:\\pymol\\python.exe (PyMOL Python)")
        sys.exit(2)
    render_views(
        args.st,
        args.pt,
        args.out_dir,
        args.tag,
        st_color=args.st_color,
        pt_color=args.pt_color,
        residue_color=args.residue_color,
        hbond_color=args.hbond_color,
    )
    log("done")


if __name__ == "__main__":
    main()
