# -*- coding: utf-8 -*-
"""把最终报告 HTML 里的图片全部内嵌为 base64 data URI（单文件可发送）。
- 全量内嵌，不改相对/绝对路径为别的引用
- 仅对超大图（>1.5MB 或最长边>2000px）等比缩到最长边 2000px，保持可观看清晰度
- 终检：内嵌后不得残留任何本地 src/href 引用
"""
from __future__ import annotations
import re, os, sys, base64, io, html as _html
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
HTML_PATH = r'E:\RProject\昱阳项目\01_分析报告_AnalysisReport\03_最终报告_FinalReport\01_最终分析报告_FinalReport.html'
BASE = os.path.dirname(HTML_PATH)
MAX_SIDE = 2000
BIG_BYTES = int(1.5 * 1024 * 1024)
MIME = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.bmp': 'image/bmp'}

t = open(HTML_PATH, encoding='utf-8').read()
img_re = re.compile(r"(<img\b[^>]*?\bsrc\s*=\s*)(['\"])([^'\"]+)\2", re.S | re.I)

stats = {'n': 0, 'src_bytes': 0, 'out_bytes': 0, 'downscaled': [], 'missing': []}

def embed(m):
    head, quote, src = m.group(1), m.group(2), m.group(3)
    if src.startswith('data:') or src.lower().startswith(('http:', 'https:')):
        return m.group(0)
    ap = os.path.normpath(os.path.join(BASE, src.replace('/', os.sep)))
    if not os.path.exists(ap):
        stats['missing'].append(src)
        return m.group(0)
    raw = open(ap, 'rb').read()
    ext = os.path.splitext(ap)[1].lower()
    mime = MIME.get(ext, 'image/png')
    out_raw = raw
    if ext != '.svg':
        img = Image.open(io.BytesIO(raw))
        w, h = img.size
        need = (max(w, h) > MAX_SIDE) or (len(raw) > BIG_BYTES)
        if need:
            img = img.convert('RGBA') if img.mode in ('P', 'LA') else img
            ratio = MAX_SIDE / max(w, h)
            if ratio < 1:
                img = img.resize((max(1, round(w * ratio)), max(1, round(h * ratio))), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format='PNG', optimize=True)
            out_raw = buf.getvalue()
            stats['downscaled'].append((os.path.basename(ap), len(raw), len(out_raw), f'{w}x{h}', f'{img.size[0]}x{img.size[1]}'))
    b64 = base64.b64encode(out_raw).decode('ascii')
    stats['n'] += 1
    stats['src_bytes'] += len(raw)
    stats['out_bytes'] += len(out_raw)
    return f"{head}{quote}data:{mime};base64,{b64}{quote}"

new = img_re.sub(embed, t)

# 终检：残留本地引用？
residual = []
for mm in re.finditer(r"\b(?:src|href)\s*=\s*(['\"])([^'\"]+)\1", new, re.I):
    v = mm.group(2)
    if v.startswith(('data:', 'http:', 'https:', '#', 'mailto:')):
        continue
    residual.append(v[:80])

open(HTML_PATH, 'w', encoding='utf-8').write(new)

print(f"embedded images : {stats['n']}")
print(f"missing (left)  : {len(stats['missing'])} {stats['missing']}")
print(f"src image bytes : {stats['src_bytes']/1048576:.1f} MB")
print(f"embedded bytes  : {stats['out_bytes']/1048576:.1f} MB")
print(f"final HTML size : {os.path.getsize(HTML_PATH)/1048576:.1f} MB")
print(f"downscaled      : {len(stats['downscaled'])}")
for name, a, b, d0, d1 in stats['downscaled']:
    print(f"   {name}: {a/1048576:.1f}MB->{b/1048576:.2f}MB  {d0}->{d1}")
print(f"residual local refs: {len(residual)}")
for r in residual:
    print('   ', r)
print('OK' if not stats['missing'] and not residual else 'CHECK')
