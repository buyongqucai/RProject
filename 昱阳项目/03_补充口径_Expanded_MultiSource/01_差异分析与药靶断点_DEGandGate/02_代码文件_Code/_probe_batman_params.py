import json
import re
from pathlib import Path
import urllib.request

pred = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_预测靶点_MultiPredict"
)
js = (pred / "_batman_api_chunk.js").read_text(encoding="utf-8", errors="ignore")
# print parameter-ish text blocks
for pat in ["parameter", "Parameter", "score", "cid", "PubChem", "JSON", "example", "formData", "axios"]:
    print("PAT", pat, js.lower().count(pat.lower()))

# dump readable strings longer than 20 chars that look like docs
strs = re.findall(r'"([^"]{20,200})"', js)
for s in strs:
    if any(k in s.lower() for k in ["param", "score", "cid", "post", "json", "example", "input", "compound", "gene"]):
        print("STR:", s)

# try POST bodies
url = "http://batman2api.cloudna.cn/queryTcm"
candidates = [
    {"cid": "5280343", "score": 20},
    {"cids": "5280343", "score": 20},
    {"compound": "5280343", "scoreCutoff": 20},
    {"input": "5280343", "score": 20},
    {"pubchem_cid": 5280343, "score": 20},
    {"type": "compound", "item": "5280343", "score": 20},
    {"query": "5280343", "score": 20},
]
for body in candidates:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()[:500]
            print("OK", body, r.status, raw[:200])
    except Exception as e:
        print("FAIL", body, type(e).__name__, e)
