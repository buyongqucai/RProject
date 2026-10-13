import csv
import json
import re
import subprocess
from pathlib import Path

PRED = Path(
    r"E:/RProject/昱阳项目/03_补充口径_Expanded_MultiSource/"
    r"01_差异分析与药靶断点_DEGandGate/01_数据文件_Data/"
    r"01_初始数据_RawInitial/04_预测靶点_MultiPredict"
)
JOB = "261011075421"
html_path = PRED / f"pm_{JOB}_result.html"
t = html_path.read_text(encoding="utf-8", errors="ignore")

# download result.js
subprocess.run(
    [
        "curl.exe",
        "-sS",
        "-m",
        "60",
        "-A",
        "Mozilla/5.0",
        "-o",
        str(PRED / "pm_result.js"),
        "https://www.lilab-ecust.cn/pharmmapper/js/result.js",
    ],
    check=False,
)
js = (PRED / "pm_result.js").read_text(encoding="utf-8", errors="ignore")
print("result.js len", len(js))
for m in re.finditer(r".{0,40}(?:json|txt|csv|download|fetch|ajax|\.js|\.gz).{0,80}", js, re.I):
    s = m.group(0)
    if "google" in s.lower():
        continue
    print("JSCTX", s[:160])

# find script blobs / JSON in HTML
for pat in [
    r"var\s+\w+\s*=\s*(\[[\s\S]{100,}?\]);",
    r"(\{\s*\"pdb\"[\s\S]{0,200})",
    r"results/[0-9]+[^\"']+",
    r"jobfile/[^\"']+",
    r"data/[^\s\"']+",
]:
    ms = re.findall(pat, t)
    print("PAT", pat[:40], "n", len(ms))
    for x in ms[:5]:
        print(" ", str(x)[:200])

# candidate data URLs
cands = [
    f"https://www.lilab-ecust.cn/pharmmapper/results/{JOB}.json",
    f"https://www.lilab-ecust.cn/pharmmapper/results/{JOB}.txt",
    f"https://www.lilab-ecust.cn/pharmmapper/results/{JOB}.csv",
    f"https://www.lilab-ecust.cn/pharmmapper/results/{JOB}_result.txt",
    f"https://www.lilab-ecust.cn/pharmmapper/results/{JOB}/result.txt",
    f"https://www.lilab-ecust.cn/pharmmapper/results/{JOB}/summary.txt",
    f"https://www.lilab-ecust.cn/pharmmapper/results/{JOB}/targets.txt",
]
# also from HTML
cands += [
    "https://www.lilab-ecust.cn" + u if u.startswith("/") else u
    for u in re.findall(r'["\']([^"\']*(?:results|jobfile|data)/[^"\']+)["\']', t + js)
]

for u in sorted(set(cands)):
    out = PRED / f"_probe_{abs(hash(u)) % 10**8}.bin"
    p = subprocess.run(
        [
            "curl.exe",
            "-sS",
            "-m",
            "60",
            "-A",
            "Mozilla/5.0",
            "-L",
            "-o",
            str(out),
            "-w",
            "%{http_code}|%{size_download}|%{content_type}",
            u,
        ],
        capture_output=True,
    )
    print(p.stdout.decode(), u[:140])

# Look for embedded base64 or large arrays
arr = re.search(r"id=\"d0\"[^>]*>\s*([\s\S]*?)</", t)
print("d0", bool(arr), (arr.group(1)[:100] if arr else ""))

# textarea / pre with data
for m in re.finditer(r"<(pre|textarea|script)[^>]*>([\s\S]{200,}?)</\1>", t, re.I):
    tag, body = m.group(1), m.group(2)
    if "function" in body[:80] and tag == "script":
        # maybe data assignment
        if "pdb" in body.lower() or "fit" in body.lower():
            print("SCRIPT dataish", body[:300])
    elif tag != "script":
        print(tag, "len", len(body), body[:200])
