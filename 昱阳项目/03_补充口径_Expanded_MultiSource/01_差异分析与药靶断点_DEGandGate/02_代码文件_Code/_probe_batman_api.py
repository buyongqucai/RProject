import re
from pathlib import Path

pred = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_STP_STITCH_PharmMapper_TargetNet_BATMAN_预测靶点"
)
js = (pred / "_batman_api_chunk.js").read_text(encoding="utf-8", errors="ignore")
urls = sorted(set(re.findall(r"https?://[^\\\"\s<>]+", js)))
print("URLS:")
for u in urls:
    print(u)
print("--- APICTX ---")
for m in re.finditer(r".{0,80}(?:Api|api|downloadApi|request).{0,120}", js):
    s = m.group(0).replace("\n", " ")
    print(s[:200])
