import os
import time
import urllib.request

url = "https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE197289&format=file&file=GSE197289_snRNA-seq_mouse_raw_counts.RDS.gz"
dest = r"E:\RProject\.scratch\虚拟敲除技能接诊表单_InSilicoKOIntake\data\GSE197289_snRNA-seq_mouse_raw_counts.RDS.gz"
expected = 399656879
if os.path.exists(dest) and os.path.getsize(dest) < expected:
    os.remove(dest)
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
print("open", flush=True)
with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
    total = 0
    t0 = time.time()
    while True:
        chunk = r.read(1024 * 1024)
        if not chunk:
            break
        f.write(chunk)
        total += len(chunk)
        if total % (20 * 1024 * 1024) < 1024 * 1024:
            print(f"bytes {total} elapsed {time.time()-t0:.0f}s", flush=True)
print("FINAL", os.path.getsize(dest), flush=True)
if os.path.getsize(dest) != expected:
    raise SystemExit(f"size mismatch {os.path.getsize(dest)} != {expected}")
print("SIZE_OK")
