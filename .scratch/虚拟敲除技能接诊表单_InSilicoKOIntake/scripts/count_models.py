import gzip
from collections import Counter
p = r"E:\RProject\.scratch\虚拟敲除技能接诊表单_InSilicoKOIntake\data\GSE197289_snRNA-seq_mouse_barcode_meta.csv.gz"
with gzip.open(p, "rt", encoding="utf-8") as f:
    header = f.readline().strip().split(",")
    print(header)
    i_model = header.index("model")
    i_sub = header.index("subtype")
    c = Counter()
    for line in f:
        parts = line.rstrip("\n").split(",")
        c[(parts[i_model], parts[i_sub])] += 1
for k, v in sorted(c.items(), key=lambda kv: (-kv[1])):
    if v >= 200:
        print(k, v)
