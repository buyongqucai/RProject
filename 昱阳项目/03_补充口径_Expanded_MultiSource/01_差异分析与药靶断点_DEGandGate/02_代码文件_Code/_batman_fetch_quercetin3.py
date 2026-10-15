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
idx = js.find("three options")
print("THREE:", js[idx : idx + 1200] if idx >= 0 else "none")
print("OPTS", sorted(set(re.findall(r'"(fufang|herb|danwei|chengfen|compound|formula|ingredient)"', js))))

url = "http://batman2api.cloudna.cn/queryTcm"


def post(body, as_form=False):
    if as_form:
        import urllib.parse

        data = urllib.parse.urlencode({"data": json.dumps(body)}).encode()
        headers = {"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"}
    else:
        data = json.dumps(body).encode()
        headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


# sanity: official-like fufang example
bodies = [
    {
        "content": [
            {
                "clusterName": "LIU WEI DI HUANG TANG",
                "type": "fufang",
                "list": ["LIU WEI DI HUANG TANG"],
            }
        ],
        "pvalue": 0.05,
        "userInScore": 500,
    },
    {
        "content": [{"clusterName": "quercetin", "type": "danwei", "list": ["5280343"]}],
        "pvalue": 0.05,
        "userInScore": 20,
    },
    {
        "content": [{"clusterName": "quercetin", "type": "herb", "list": ["quercetin"]}],
        "pvalue": 0.05,
        "userInScore": 20,
    },
    {
        "content": [{"clusterName": "quercetin", "type": "chengfen", "list": [5280343]}],
        "pvalue": 0.05,
        "userInScore": 20,
    },
]

for i, body in enumerate(bodies):
    for as_form in (False, True):
        try:
            raw = post(body, as_form=as_form)
            print("OK", i, "form" if as_form else "json", len(raw), raw[:250])
            (pred / "06_BATMAN_ok.json").write_bytes(raw)
            raise SystemExit(0)
        except Exception as e:
            print("FAIL", i, "form" if as_form else "json", e)
