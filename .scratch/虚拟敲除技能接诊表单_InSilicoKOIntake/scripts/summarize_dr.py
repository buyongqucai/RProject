import csv
import os
root = r"C:\Users\10540\Desktop\琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\代码文件\结果文件\数据文件"
path = os.path.join(root, "04_扰动基因_五亚群_Cplx2DrAll.csv")
by = {}
with open(path, encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        g = row["subtype"]
        by.setdefault(g, [])
        if row["gene"] == "Cplx2":
            continue
        if float(row["p.adj"]) < 0.05:
            by[g].append((row["gene"], float(row["p.adj"]), float(row["FC"])))
for g, items in by.items():
    items.sort(key=lambda x: x[1])
    print(g, "n_sig", len(items))
    for it in items[:8]:
        print(" ", it)
