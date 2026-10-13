from pathlib import Path
import re

root = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_STP_STITCH_PharmMapper_TargetNet_BATMAN_预测靶点"
)

# download more chunks if needed
patterns = ["queryTarget", "queryTcm", "compound", "userInScore", "content", "caoyao", "fufang"]
for f in sorted(root.glob("*.js")):
    if not f.name.startswith("_b"):
        continue
    t = f.read_text(encoding="utf-8", errors="ignore")
    hits = [p for p in patterns if p in t]
    if "axios.post" in t or "queryTarget" in t or ("content" in t and "clusterName" in t):
        print("FILE", f.name, "size", len(t), "hits", hits)
        for key in ["axios.post", "queryTarget", "clusterName", "type:\"compound\"", "type:'compound'"]:
            i = 0
            c = 0
            while c < 3:
                j = t.find(key, i)
                if j < 0:
                    break
                print("---", key, "---")
                print(t[max(0, j - 250) : j + 350])
                i = j + 1
                c += 1
