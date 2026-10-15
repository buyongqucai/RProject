import os
import time
import urllib.request

url = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE197nnn/GSE197289/suppl/GSE197289_snRNA-seq_mouse_raw_counts.RDS.gz"
dest = r"E:\RProject\.scratch\虚拟敲除技能接诊表单_InSilicoKOIntake\data\GSE197289_snRNA-seq_mouse_raw_counts.RDS.gz"
expected = 399656879
if os.path.exists(dest) and os.path.getsize(dest) != expected:
    os.remove(dest)
print("start", flush=True)
req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
t0 = time.time()
with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as f:
    total = 0
    last = t0
    while True:
        chunk = r.read(4 * 1024 * 1024)
        if not chunk:
            break
        f.write(chunk)
        total += len(chunk)
        now = time.time()
        if now - last > 15:
            print(f"{total}/{expected} {total/expected:.1%} { (total/(now-t0))/1e6:.2f} MB/s", flush=True)
            last = now
print("FINAL", os.path.getsize(dest), flush=True)
if os.path.getsize(dest) != expected:
    raise SystemExit("size mismatch")
print("SIZE_OK")
