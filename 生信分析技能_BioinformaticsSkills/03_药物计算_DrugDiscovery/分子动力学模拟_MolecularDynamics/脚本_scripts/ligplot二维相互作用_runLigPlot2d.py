# -*- coding: utf-8 -*-
"""LigPlot+ 二维相互作用：跑 ligplot.exe，把官方 ligplot.ps 复绘为出版级 PNG/SVG。

正式图必须是 LigPlot 化学结构（配体骨架、原子色、疏水弧、图例），
禁止配体圆 + 残基方框示意网。LigPlot CPK / 配体键紫 / 疏水砖红 / 氢键橄榄
是该图种惯例，不改成 journal muted。
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Polygon

LIGPLUS = Path(r"E:\LigPlus")
EXE = LIGPLUS / "lib" / "exe_win"
PRM = LIGPLUS / "lib" / "params" / "ligplot.prm"
MD = Path(
    r"E:\RProject\生信分析技能_BioinformaticsSkills\03_药物计算_DrugDiscovery"
    r"\分子动力学模拟_MolecularDynamics\01_样例_sample\工作文件_MdWork\3HTB"
)
RESULT = Path(
    r"E:\RProject\生信分析技能_BioinformaticsSkills\03_药物计算_DrugDiscovery"
    r"\分子动力学模拟_MolecularDynamics\01_样例_sample\代码文件\结果文件"
)
FIG = RESULT / "26_二维相互作用图"
PDB_SRC = MD / "10_轨迹快照_Snapshots" / "轨迹快照末干_SnapshotEndDry.pdb"
OUT = FIG / "26_二维相互作用_LigPlot2D"
TITLE_TEXT = "3HTB / JZ4  (MD end frame)"

PRIMITIVES = {
    "L", "Sphere", "Arc", "Pl4", "Poly4", "Circle", "Ucircle", "Ocircle",
    "Print", "Center", "Gprint", "Fprint", "moveto", "lineto", "stroke",
    "fill", "gsave", "grestore", "G", "W", "D", "Col", "setrgbcolor",
    "setgray", "setlinewidth", "setdash", "show", "newpath", "closepath",
    "bind", "def", "save", "restore", "showpage", "setlinecap",
    "setlinejoin", "translate", "rotate", "scale", "clip", "exch", "dup",
    "pop", "rmoveto", "rlineto", "arc", "arcn", "stringwidth", "findfont",
    "scalefont", "setfont", "currentpoint",
}


def run_ligplot(work: Path) -> None:
    shutil.copy2(PDB_SRC, work / "complex.pdb")
    shutil.copy2(PRM, work / "ligplot.prm")
    subprocess.run(
        [str(EXE / "hbplus.exe"), "-L", "-h", "2.90", "-d", "3.90", "-N",
         str(work / "complex.pdb")],
        cwd=work, capture_output=True,
    )
    subprocess.run(
        [str(EXE / "hbplus.exe"), "-L", "-h", "2.70", "-d", "3.35",
         str(work / "complex.pdb")],
        cwd=work, capture_output=True,
    )
    r = subprocess.run(
        [
            str(EXE / "ligplot.exe"), "complex.pdb", "164", "164", "B",
            "-wkdir", str(work), "-prm", "ligplot.prm", "-ctype", "1",
        ],
        cwd=work, capture_output=True, text=True, encoding="utf-8",
        errors="replace",
    )
    if not (work / "ligplot.ps").exists() and not (work / "ligplot.sum").exists():
        raise RuntimeError(
            f"ligplot failed: {(r.stderr or r.stdout or '')[-600:]}"
        )


def parse_sum(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.search(
            r"\[([A-Z0-9]+)\s+(\d+)\s+(\w)\]\s*->\s*"
            r"\[([A-Z0-9]+)\s+(\d+)\s+(\w)\]\s+"
            r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
            ln,
        )
        if not m:
            m2 = re.search(
                r"([A-Z0-9]{1,4})\s+(\d+)\s+([A-Z])\s+.*?"
                r"([A-Z0-9]{3})\s+(\d+)\s+([A-Z])\s+"
                r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
                ln,
            )
            if not m2:
                continue
            lig, lnum, lch, res, rnum, rch, a, b, c, d = m2.groups()
        else:
            lig, lnum, lch, res, rnum, rch, a, b, c, d = m.groups()
        n_mm, n_ss, n_ms, n_nb = int(a), int(b), int(c), int(d)
        n_h = n_mm + n_ss + n_ms
        rows.append({
            "ligand": f"{lig} {int(lnum)}({lch})",
            "residue": f"{res} {int(rnum)}({rch})",
            "resname": res,
            "resnum": int(rnum),
            "chain": rch,
            "n_hbond": n_h,
            "n_hydrophobic": n_nb,
            "n_other": 0,
            "n_contacts": n_h + n_nb,
        })
    return rows


def rows_from_ps(ps_text: str) -> list[dict]:
    names = re.findall(
        r"\(([A-Za-z][a-z]{2} \d+\([A-Z]\))\)\s+Hydrophnam_size\s+Print",
        ps_text,
    )
    seen: dict[str, int] = {}
    for n in names:
        if n in ("His 53",):
            continue
        seen[n] = seen.get(n, 0) + 1
    rows = []
    for n, c in seen.items():
        m = re.match(r"([A-Za-z]+)\s+(\d+)\(([A-Z])\)", n)
        if not m:
            continue
        aa, num, ch = m.groups()
        rows.append({
            "ligand": "JZ4 164(B)",
            "residue": n,
            "resname": aa.upper(),
            "resnum": int(num),
            "chain": ch,
            "n_hbond": 0,
            "n_hydrophobic": c,
            "n_other": 0,
            "n_contacts": c,
        })
    return rows


def write_csv(rows: list[dict]) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    dest = FIG / "数据表_二维相互作用_LigPlot2D.csv"
    cols = [
        "residue", "resname", "resnum", "chain", "n_hbond",
        "n_hydrophobic", "n_other", "n_contacts", "ligand",
    ]
    lines = [",".join(cols)]
    for r in rows:
        lines.append(",".join(str(r[c]) for c in cols))
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def _tok_line(line: str) -> list:
    if "%" in line:
        line = line.split("%", 1)[0]
    out: list = []
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if c.isspace():
            i += 1
            continue
        if c == "(":
            j = i + 1
            buf: list[str] = []
            while j < n:
                if line[j] == "\\":
                    buf.append(line[j + 1] if j + 1 < n else "")
                    j += 2
                    continue
                if line[j] == ")":
                    break
                buf.append(line[j])
                j += 1
            out.append(("str", "".join(buf)))
            i = j + 1
            continue
        if c in "[]{}":
            out.append(c)
            i += 1
            continue
        if c == "/":
            j = i + 1
            while j < n and not line[j].isspace() and line[j] not in "[]{}()/%":
                j += 1
            out.append(("name", line[i + 1:j]))
            i = j
            continue
        j = i
        while j < n and not line[j].isspace() and line[j] not in "[]{}()/%":
            j += 1
        tok = line[i:j]
        if j == i:
            i += 1
            continue
        i = j
        try:
            out.append(float(tok) if "." in tok else int(tok))
        except ValueError:
            out.append(tok)
    return out


def _consume_brace(toks: list, i: int) -> tuple[list, int]:
    depth, j, inner = 1, i + 1, []
    n = len(toks)
    while j < n and depth:
        if toks[j] == "{":
            depth += 1
            inner.append(toks[j])
        elif toks[j] == "}":
            depth -= 1
            if depth:
                inner.append(toks[j])
        else:
            inner.append(toks[j])
        j += 1
    return inner, j


class _GS:
    __slots__ = ("color", "lw", "dash", "sphcol")

    def __init__(self) -> None:
        self.color = (0.0, 0.0, 0.0)
        self.lw = 0.6
        self.dash = None
        self.sphcol = (0.0, 0.0, 0.0)

    def copy(self) -> "_GS":
        o = _GS()
        o.color, o.lw, o.dash, o.sphcol = self.color, self.lw, self.dash, self.sphcol
        return o


def render_ligplot_ps(ps_path: Path, stem: Path) -> None:
    raw = ps_path.read_text(encoding="latin-1", errors="ignore")
    bb = (29.0, 49.0, 551.0, 781.0)
    boxes = re.findall(
        r"%%BoundingBox:\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", raw,
    )
    if boxes:
        bb = tuple(float(x) for x in boxes[-1])  # type: ignore[assignment]

    rgb: dict[str, tuple[float, float, float]] = {}
    alias: dict[str, str] = {}
    sizes: dict[str, float] = {}
    for m in re.finditer(
        r"/([A-Za-z0-9_]+)\s*\{\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+setrgbcolor\s*\}\s*def",
        raw,
    ):
        rgb[m.group(1)] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
    for m in re.finditer(
        r"/([A-Za-z0-9_]+)\s*\{\s*([A-Za-z0-9_]+)\s*\}\s*def",
        raw,
    ):
        if m.group(1) in PRIMITIVES or m.group(1) == "Sphcol":
            continue
        alias[m.group(1)] = m.group(2)
    for m in re.finditer(
        r"/([A-Za-z0-9_]+)\s*\{\s*([0-9.]+)\s*\}\s*def",
        raw,
    ):
        if m.group(1) not in PRIMITIVES:
            sizes[m.group(1)] = float(m.group(2))

    def resolve_color(name: str) -> tuple[float, float, float]:
        seen: set[str] = set()
        while name in alias and name not in seen:
            seen.add(name)
            name = alias[name]
        return rgb.get(name, (0.0, 0.0, 0.0))

    st = _GS()
    gstack: list[_GS] = []
    stack: list = []
    cur = (0.0, 0.0)
    pending_center = False
    n_draw = 0
    ops: list[tuple] = []

    def apply_name(name: str) -> bool:
        if name in sizes:
            stack.append(sizes[name])
            return True
        if name in rgb or name in alias:
            st.color = resolve_color(name)
            return True
        return False

    def record_def(nm: str, inner: list) -> None:
        if nm in PRIMITIVES:
            return
        if nm == "Sphcol":
            for t in inner:
                if isinstance(t, str) and (t in rgb or t in alias):
                    st.sphcol = resolve_color(t)
                    return
            return
        if len(inner) == 1 and isinstance(inner[0], (int, float)):
            sizes[nm] = float(inner[0])
            return
        if len(inner) == 1 and isinstance(inner[0], str):
            alias[nm] = inner[0]
            return
        if (
            len(inner) >= 4
            and inner[-1] == "setrgbcolor"
            and all(isinstance(inner[k], (int, float)) for k in range(3))
        ):
            rgb[nm] = (float(inner[0]), float(inner[1]), float(inner[2]))

    def run_line(toks: list) -> None:
        nonlocal st, cur, pending_center, n_draw
        i, n = 0, len(toks)
        guard = 0
        while i < n:
            guard += 1
            if guard > 20000:
                raise RuntimeError(f"run_line stuck i={i} n={n} toks={toks[:40]!r}")
            t = toks[i]
            if t == "[":
                arr: list[float] = []
                i += 1
                while i < n and toks[i] != "]":
                    if isinstance(toks[i], (int, float)):
                        arr.append(float(toks[i]))
                    i += 1
                stack.append(arr)
                i += 1
                continue
            if isinstance(t, tuple) and t[0] == "name":
                if i + 1 < n and toks[i + 1] == "{":
                    inner, j = _consume_brace(toks, i + 1)
                    while j < n and toks[j] in ("bind", "def"):
                        j += 1
                    record_def(t[1], inner)
                    i = max(j, i + 1)
                    continue
                i += 1
                continue
            if isinstance(t, (int, float)):
                stack.append(float(t))
                i += 1
                continue
            if isinstance(t, tuple) and t[0] == "str":
                stack.append(t)
                i += 1
                continue
            if not isinstance(t, str):
                i += 1
                continue
            if apply_name(t):
                i += 1
                continue
            if t in ("gsave", "G"):
                gstack.append(st.copy())
            elif t == "grestore":
                if gstack:
                    st = gstack.pop()
            elif t == "setrgbcolor" and len(stack) >= 3:
                b, g, r = float(stack.pop()), float(stack.pop()), float(stack.pop())
                st.color = (r, g, b)
            elif t == "setgray" and stack:
                g = float(stack.pop())
                st.color = (g, g, g)
            elif t in ("setlinewidth", "W") and stack and isinstance(stack[-1], (int, float)):
                st.lw = abs(float(stack.pop()))
            elif t in ("setdash", "D"):
                if t == "setdash" and stack:
                    stack.pop()
                arr = stack.pop() if stack else []
                st.dash = (
                    (arr[0], arr[1])
                    if isinstance(arr, list) and len(arr) >= 2
                    else None
                )
            elif t == "moveto" and len(stack) >= 2:
                y, x = float(stack.pop()), float(stack.pop())
                cur = (x, y)
                pending_center = False
            elif t == "L" and len(stack) >= 4:
                y2, x2, y1, x1 = (float(stack.pop()) for _ in range(4))
                ops.append(("L", x1, y1, x2, y2, st.color, max(st.lw, 0.15), st.dash))
                n_draw += 1
            elif t == "Sphere" and len(stack) >= 3:
                r, y, x = float(stack.pop()), float(stack.pop()), float(stack.pop())
                ops.append(("Sphere", x, y, r, st.sphcol))
                n_draw += 1
            elif t == "Arc" and len(stack) >= 5:
                a2, a1, r, y, x = (float(stack.pop()) for _ in range(5))
                ops.append(("Arc", x, y, r, a1, a2, st.color, max(st.lw, 0.55)))
                n_draw += 1
            elif t in ("Pl4", "Poly4") and len(stack) >= 8:
                pts = [float(stack.pop()) for _ in range(8)]
                xy = [
                    (pts[7], pts[6]), (pts[5], pts[4]),
                    (pts[3], pts[2]), (pts[1], pts[0]),
                ]
                xs = [p[0] for p in xy]
                ys = [p[1] for p in xy]
                # Page-size white plate would cover later bonds; axes are already white.
                if max(xs) - min(xs) < 400 and max(ys) - min(ys) < 400:
                    ops.append(("Pl4", xy, st.color))
                n_draw += 1
                if gstack:
                    st = gstack.pop()
            elif t == "Center":
                if stack and isinstance(stack[-1], (int, float)):
                    stack.pop()
                if stack and isinstance(stack[-1], tuple) and stack[-1][0] == "str":
                    stack.pop()
                pending_center = True
            elif t in ("Print", "show", "Fprint"):
                text = ""
                size = 10.0
                if stack and isinstance(stack[-1], (int, float)):
                    size = float(stack.pop())
                if stack and isinstance(stack[-1], tuple) and stack[-1][0] == "str":
                    text = stack.pop()[1]
                if text.strip() == "complex":
                    text = TITLE_TEXT
                if text:
                    ops.append((
                        "text", cur[0], cur[1], text.strip(),
                        max(size * 0.92, 5.0), st.color, pending_center,
                    ))
                    n_draw += 1
                pending_center = False
            elif t in ("lineto", "rmoveto", "translate", "scale") and len(stack) >= 2:
                stack.pop()
                stack.pop()
            elif t in ("setlinecap", "setlinejoin", "rotate") and stack:
                stack.pop()
            i += 1

    page = False
    nline = 0
    for line in raw.splitlines():
        if line.startswith("%%Page:"):
            page = True
            continue
        if not page:
            continue
        nline += 1
        toks = _tok_line(line)
        if toks:
            run_line(toks)
        if n_draw > 50000:
            raise RuntimeError(f"too many draw ops at page line {nline}")
    nL = sum(1 for o in ops if o[0] == "L")
    print(
        f"LigPlot parsed lines={nline} ops={n_draw} L={nL} "
        f"kinds={ {k: sum(1 for o in ops if o[0]==k) for k in ('L','Sphere','Arc','Pl4','text')} }",
        flush=True,
    )

    w_in = (bb[2] - bb[0]) / 72.0
    h_in = (bb[3] - bb[1]) / 72.0
    fig = plt.figure(figsize=(w_in, h_in), dpi=100)
    ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
    ax.set_xlim(bb[0], bb[2])
    ax.set_ylim(bb[1], bb[3])
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    for zi, op in enumerate(ops, start=2):
        kind = op[0]
        if kind == "L":
            _, x1, y1, x2, y2, col, lw, dash = op
            ls: object = "-"
            if dash:
                ls = (0, (max(float(dash[0]), 0.35), max(float(dash[1]), 0.35)))
            ax.plot(
                [x1, x2], [y1, y2], color=col, lw=lw, ls=ls,
                solid_capstyle="round", zorder=zi,
            )
        elif kind == "Pl4":
            _, xy, fc = op
            ax.add_patch(Polygon(
                xy, closed=True, facecolor=fc, edgecolor="none", zorder=zi,
            ))
        elif kind == "Arc":
            _, x, y, r, a1, a2, col, lw = op
            ax.add_patch(Arc(
                (x, y), 2 * r, 2 * r, angle=0, theta1=a1, theta2=a2,
                color=col, lw=lw, zorder=zi,
            ))
        elif kind == "Sphere":
            _, x, y, r, col = op
            ax.add_patch(Circle(
                (x, y), r, facecolor=col, edgecolor=(0.08, 0.08, 0.08),
                linewidth=0.55, zorder=zi,
            ))
            ax.add_patch(Arc(
                (x + 0.18 * r, y + 0.18 * r), 1.15 * r, 1.15 * r,
                angle=0, theta1=40, theta2=130,
                color=(1, 1, 1), lw=max(0.7, 0.18 * r), zorder=zi + 0.1,
            ))
        elif kind == "text":
            _, x, y, text, size, col, centered = op
            ax.text(
                x, y, text, fontsize=size, color=col,
                ha="center" if centered else "left",
                va="center" if centered else "bottom",
                zorder=zi, fontfamily="Times New Roman", clip_on=False,
            )
    print("LigPlot artists added, saving", flush=True)

    png = stem.with_suffix(".png")
    svg = stem.with_suffix(".svg")
    fig.savefig(png, dpi=600, facecolor="white", pad_inches=0)
    fig.savefig(svg, facecolor="white", pad_inches=0)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-ps", type=Path, default=None,
                    help="Skip ligplot.exe and render this .ps")
    args = ap.parse_args()
    FIG.mkdir(parents=True, exist_ok=True)

    work = None
    if args.from_ps:
        ps = args.from_ps
    else:
        work = Path(tempfile.mkdtemp(prefix="ligplot_draw_"))
        try:
            run_ligplot(work)
            ps = work / "ligplot.ps"
        except Exception as exc:
            cached = OUT.with_suffix(".ps")
            if not cached.exists():
                raise
            print("ligplot.exe failed, using cached PS:", exc)
            ps = cached
            work = None
        if not ps.exists():
            cached = OUT.with_suffix(".ps")
            if cached.exists():
                ps = cached
            else:
                raise FileNotFoundError("ligplot.ps was not produced")

    dest_ps = OUT.with_suffix(".ps")
    if ps.resolve() != dest_ps.resolve():
        try:
            shutil.copy2(ps, dest_ps)
        except PermissionError:
            print("WARN: could not overwrite", dest_ps)
    raw = ps.read_text(encoding="latin-1", errors="ignore")
    rows: list[dict] = []
    if work is not None:
        rows = parse_sum(work / "ligplot.sum")
    if not rows:
        rows = rows_from_ps(raw)
    write_csv(rows)
    render_ligplot_ps(ps, OUT)
    print("WROTE", OUT.with_suffix(".png"))
    if work is not None:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
