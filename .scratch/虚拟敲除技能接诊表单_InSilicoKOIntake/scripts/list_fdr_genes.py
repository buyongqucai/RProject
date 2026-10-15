import csv
from collections import defaultdict
p = r"C:\Users\10540\Desktop\琪乐无穷\CPLX2虚拟敲除_Cplx2VirtualKO\结果文件\数据文件\04_扰动基因_五亚群_Cplx2DrAll.csv"
by = defaultdict(list)
with open(p, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if float(row["p.adj"]) < 0.05:
            by[row["subtype"]].append(row["gene"])
for k, v in by.items():
    print(k, v)
