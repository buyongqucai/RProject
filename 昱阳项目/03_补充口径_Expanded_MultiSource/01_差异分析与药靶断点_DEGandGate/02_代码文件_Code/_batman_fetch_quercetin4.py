import json
import urllib.error
import urllib.request
from pathlib import Path

pred = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_预测靶点_MultiPredict"
)

urls = [
    "http://batman2api.cloudna.cn/queryTcm",
    "http://bionet.ncpsb.org.cn/api/queryTcm",
    "http://batman2.cloudna.cn/api/queryTcm",
]

bodies = [
    {
        "content": [
            {"clusterName": "quercetin", "type": "compound", "list": ["5280343"]}
        ],
        "pvalue": 0.05,
        "userInScore": 20,
    },
    {
        "content": [
            {"clusterName": "quercetin", "type": "compound", "list": [5280343]}
        ],
        "pvalue": 0.05,
        "userInScore": 20,
    },
    {
        "content": [
            {"clusterName": "LIU WEI DI HUANG TANG", "type": "fufang", "list": ["LIU WEI DI HUANG TANG"]}
        ],
        "pvalue": 0.05,
        "userInScore": 500,
    },
    {
        "content": [
            {"clusterName": "huangqi", "type": "caoyao", "list": ["huangqi"]}
        ],
        "pvalue": 0.05,
        "userInScore": 20,
    },
]

for url in urls:
    for body in bodies:
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
                print("OK", url, body["content"][0]["type"], len(raw))
                (pred / "06_BATMAN_queryTcm_ok.json").write_bytes(raw)
                print(raw[:400])
                raise SystemExit(0)
        except urllib.error.HTTPError as e:
            print("HTTP", e.code, url, body["content"][0]["type"], e.read()[:120])
        except Exception as e:
            print("ERR", url, body["content"][0]["type"], e)

print("done-no-success")
