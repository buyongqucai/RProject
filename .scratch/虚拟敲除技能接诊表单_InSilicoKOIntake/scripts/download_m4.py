import os
import urllib.request

dest = r"E:\RProject\.scratch\虚拟敲除技能接诊表单_InSilicoKOIntake\data"
os.makedirs(dest, exist_ok=True)
files = [
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE197nnn/GSE197289/suppl/GSE197289_snRNA-seq_mouse_barcode_meta.csv.gz",
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE131nnn/GSE131272/suppl/GSE131272_D0-10x.csv.gz",
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE131nnn/GSE131272/suppl/GSE131272_D2-10x.csv.gz",
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE322nnn/GSE322600/suppl/GSE322600_feature_counts.tsv.gz",
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE197nnn/GSE197289/suppl/GSE197289_snRNA-seq_mouse_raw_counts.RDS.gz",
]
for u in files:
    name = u.split("/")[-1]
    path = os.path.join(dest, name)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        print("skip", name, os.path.getsize(path))
        continue
    print("get", name, flush=True)
    urllib.request.urlretrieve(u, path)
    print("done", name, os.path.getsize(path), flush=True)
print("ALL_DONE")
