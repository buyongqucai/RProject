import os
p = r"E:\RProject\.scratch\虚拟敲除技能接诊表单_InSilicoKOIntake\data"
for n in os.listdir(p):
    fp = os.path.join(p, n)
    print(n, os.path.getsize(fp))
    if n.endswith("RDS.gz"):
        with open(fp, "rb") as f:
            print("magic", list(f.read(8)))
