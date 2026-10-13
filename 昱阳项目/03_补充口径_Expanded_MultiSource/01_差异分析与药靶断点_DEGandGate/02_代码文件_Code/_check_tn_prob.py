import re
from collections import Counter
from pathlib import Path

t = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_STP_STITCH_PharmMapper_TargetNet_BATMAN_预测靶点/_targetnet_result.html"
).read_text(encoding="utf-8", errors="ignore")
# last numeric cell in each data row often Prob
probs = []
for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", t, re.I | re.S):
    cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", m.group(1), re.I | re.S)
    clean = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
    if len(clean) >= 4 and re.fullmatch(r"[01](?:\.\d+)?", clean[-1] or ""):
        probs.append(float(clean[-1]))
print("n", len(probs), "nonzero", sum(1 for p in probs if p > 0))
if probs:
    print("max", max(probs), "min", min(probs))
    print("top", Counter(round(p, 3) for p in probs).most_common(8))
