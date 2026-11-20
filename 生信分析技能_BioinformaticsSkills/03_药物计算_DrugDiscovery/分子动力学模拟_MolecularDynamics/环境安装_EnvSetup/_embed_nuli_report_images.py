# -*- coding: utf-8 -*-
"""努力学习全流程报告：相对路径图片改为 data URI 嵌入。"""
from __future__ import annotations

import base64
import mimetypes
import re
import shutil
from pathlib import Path

REPORT_DIR = Path(r"E:\RProject\努力学习项目\00_全流程报告\结果文件\报告文件")
DELIV_DIR = Path(r"E:\RProject\努力学习项目\交付文件\00_全流程报告\结果文件\报告文件")
FILES = ("论文版_全流程.html", "方法版_全流程.html")

SRC_RE = re.compile(
    r"""(?P<prefix>src\s*=\s*)(?P<q>['"])(?P<path>(?!data:)(?!https?:)(?!//)[^'"]+)(?P=q)""",
    re.IGNORECASE,
)


def resolve_image(report_path: Path, rel: str) -> Path | None:
    rel = rel.replace("\\", "/").strip()
    rel = rel.split("?", 1)[0].split("#", 1)[0]

    # file:///E:/... 
    if rel.lower().startswith("file:"):
        from urllib.parse import unquote

        local = unquote(rel)
        # strip file:// or file:///
        local = re.sub(r"^file:/+", "", local, flags=re.IGNORECASE)
        # /E:/foo -> E:/foo
        if re.match(r"^/[A-Za-z]:", local):
            local = local[1:]
        local = local.replace("/", "\\")
        p = Path(local)
        if p.is_file():
            return p
        return None

    candidates = [
        (report_path.parent / rel).resolve(),
        (REPORT_DIR.parent / "图片文件" / Path(rel).name).resolve(),
    ]
    mod = REPORT_DIR.parent.parent
    candidates.append((mod / rel.lstrip("./")).resolve())
    # project-relative from 努力学习根
    root = Path(r"E:\RProject\努力学习项目")
    if rel.startswith("../") or rel.startswith("./"):
        candidates.append((report_path.parent / rel).resolve())
    candidates.append((root / rel).resolve())
    for c in candidates:
        try:
            if c.is_file():
                return c
        except OSError:
            continue
    return None


def to_data_uri(img: Path) -> str:
    mime, _ = mimetypes.guess_type(str(img))
    if not mime:
        mime = "image/png" if img.suffix.lower() == ".png" else "application/octet-stream"
    raw = img.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def embed_file(html_path: Path) -> dict:
    text = html_path.read_text(encoding="utf-8")
    stats = {"file": str(html_path), "total": 0, "embedded": 0, "missing": [], "already": 0}

    def repl(m: re.Match) -> str:
        path = m.group("path")
        stats["total"] += 1
        if path.startswith("data:"):
            stats["already"] += 1
            return m.group(0)
        img = resolve_image(html_path, path)
        if img is None:
            stats["missing"].append(path)
            return m.group(0)
        uri = to_data_uri(img)
        stats["embedded"] += 1
        return f'{m.group("prefix")}{m.group("q")}{uri}{m.group("q")}'

    new_text = SRC_RE.sub(repl, text)
    html_path.write_text(new_text, encoding="utf-8")
    stats["out_MB"] = round(html_path.stat().st_size / 1024**2, 2)
    return stats


def main() -> None:
    all_stats = []
    for name in FILES:
        src = REPORT_DIR / name
        if not src.exists():
            print("MISSING", src)
            continue
        st = embed_file(src)
        all_stats.append(st)
        print(
            f"{name}: refs={st['total']} embedded={st['embedded']} "
            f"missing={len(st['missing'])} size={st['out_MB']}MB"
        )
        for m in st["missing"]:
            print("  MISSING:", m)
        # sync delivery
        dst = DELIV_DIR / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print("  synced", dst)

    # note in layout checklist
    note = Path(r"E:\RProject\努力学习项目\存放整理清单_LayoutFix.md")
    if note.exists():
        t = note.read_text(encoding="utf-8")
        line = "\n## 报告图片嵌入（2026-10-16）\n\n全流程论文版/方法版 HTML 的 `<img>` 已改为 `data:image/...;base64,...` 内嵌，单文件可离线打开；交付轨已同步。\n"
        if "报告图片嵌入" not in t:
            note.write_text(t.rstrip() + "\n" + line, encoding="utf-8")


if __name__ == "__main__":
    main()
