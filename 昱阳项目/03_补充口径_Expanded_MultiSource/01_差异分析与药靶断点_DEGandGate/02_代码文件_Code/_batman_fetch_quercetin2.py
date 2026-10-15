import json
import urllib.request
from pathlib import Path

pred = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_STP_STITCH_PharmMapper_TargetNet_BATMAN_预测靶点"
)
url = "http://batman2api.cloudna.cn/queryTcm"

type_opts = ["compound", "chengfen", "ingredient", "CID", "cid", "yaowu"]
cid_opts = ["5280343", 5280343]
score_opts = [20, 500]

for typ in type_opts:
    for cid in cid_opts:
        for score in score_opts:
            body = {
                "content": [
                    {
                        "clusterName": "quercetin",
                        "type": typ,
                        "list": [cid],
                    }
                ],
                "pvalue": 0.05,
                "userInScore": score,
            }
            data = json.dumps(body).encode()
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    raw = r.read()
                    out = pred / f"06_BATMAN_queryTcm_{typ}_{score}.json"
                    out.write_bytes(raw)
                    print("OK", typ, cid, score, "len", len(raw), raw[:200])
                    raise SystemExit(0)
            except SystemExit:
                raise
            except Exception as e:
                print("FAIL", typ, cid, score, e)

print("all failed")
