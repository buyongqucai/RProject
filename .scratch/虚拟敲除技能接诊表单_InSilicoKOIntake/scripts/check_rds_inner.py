import gzip
p = r"E:\RProject\.scratch\虚拟敲除技能接诊表单_InSilicoKOIntake\data\GSE197289_snRNA-seq_mouse_raw_counts.RDS.gz"
with gzip.open(p, "rb") as f:
    b = f.read(80)
print(list(b[:40]))
print(b[:40])
