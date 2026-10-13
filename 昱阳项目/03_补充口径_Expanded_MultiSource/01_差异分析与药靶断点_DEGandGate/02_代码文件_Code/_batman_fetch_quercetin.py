import json
import re
import urllib.request
from pathlib import Path

pred = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_STP_STITCH_PharmMapper_TargetNet_BATMAN_预测靶点"
)
js = (pred / "_batman_api_chunk.js").read_text(encoding="utf-8", errors="ignore")

# Pull nearby text after "example of POST"
idx = js.lower().find("example of post")
print(js[idx : idx + 1500] if idx >= 0 else "no example")

# Try bodies inferred from docs
url = "http://batman2api.cloudna.cn/queryTcm"
bodies = [
    {
        "clusterName": "yuyang_quercetin",
        "inputType": "compound",
        "userInTcm": ["5280343"],
        "userInScore": 20,
        "userInPvalue": 0.05,
    },
    {
        "clusterName": "yuyang_quercetin",
        "type": "compound",
        "userInTcm": [5280343],
        "userInScore": 20,
        "userInPvalue": 0.05,
    },
    {
        "clusterName": "yuyang",
        "inputType": "compound",
        "userInTcm": "5280343",
        "userInScore": "20",
        "userInPvalue": "0.05",
    },
    {
        "clusterName": "yuyang",
        "tcmType": "compound",
        "userInTcm": ["5280343"],
        "userInScore": 20,
        "userInPvalue": 0.05,
    },
    # from garbled param names in strings: clusterName, and lists
    {
        "clusterName": "yuyang",
        "userInType": "compound",
        "userInTcm": ["5280343"],
        "userInScore": 20,
        "userInPvalue": 0.05,
    },
]

# also extract quoted keys near userIn
keys = sorted(set(re.findall(r"userIn[A-Za-z]+|clusterName|inputType|tcmType", js)))
print("KEYS", keys)

for body in bodies:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read()
            print("OK", body, "len", len(raw), raw[:300])
            (pred / "06_BATMAN_queryTcm_raw.json").write_bytes(raw)
            break
    except Exception as e:
        err = getattr(e, "read", lambda: b"")()
        print("FAIL", body, e, err[:300] if err else "")
