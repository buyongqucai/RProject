import re
from pathlib import Path

p = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_预测靶点_MultiPredict/_batman_search_chunk.js"
)
t = p.read_text(encoding="utf-8", errors="ignore")
idx = t.find("queryTcm")
print("count", t.count("queryTcm"))
while idx >= 0:
    print(t[max(0, idx - 400) : idx + 400])
    print("====")
    idx = t.find("queryTcm", idx + 1)
