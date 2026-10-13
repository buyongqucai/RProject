import re
import subprocess
from pathlib import Path

PRED = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_预测靶点_MultiPredict"
)
JOB = "261011075421"


def curl(args):
    p = subprocess.run(["curl.exe", "-sS", "-m", "90", "-A", "Mozilla/5.0", *args], capture_output=True)
    return p.returncode, p.stdout


for name, args in [
    ("check", ["-F", f"mid={JOB}", "-o", str(PRED / f"pm_{JOB}_check.html"), "https://www.lilab-ecust.cn/pharmmapper/check.html"]),
    ("getres", ["-F", f"mid={JOB}", "-o", str(PRED / f"pm_{JOB}_getres.html"), "https://www.lilab-ecust.cn/pharmmapper/getres.html"]),
]:
    curl(args)
    t = (PRED / f"pm_{JOB}_{name}.html").read_text(encoding="utf-8", errors="ignore")
    print("====", name, len(t))
    m = re.search(r"Status</strong></label><label[^>]*><strong><span[^>]*>([^<]+)", t)
    print("status", m.group(1) if m else None)
    print("has FitScore", "FitScore" in t)
    print("alerts", re.findall(r"<p>([^<]{5,120})</p>", t)[:8])
    hrefs = re.findall(r'href="([^"]+)"', t)
    print("hrefs", [h for h in hrefs if any(k in h.lower() for k in ["result", "job", "down", "file", "txt", JOB])][:20])
    # dump a window around Status
    i = t.find("Job Status")
    if i >= 0:
        print(re.sub(r"\s+", " ", t[i : i + 1500]))

# getres.js
curl(["-o", str(PRED / "pm_getres.js"), "https://www.lilab-ecust.cn/pharmmapper/js/getres.js"])
js = (PRED / "pm_getres.js").read_text(encoding="utf-8", errors="ignore")
print("JS", js[:2000])
