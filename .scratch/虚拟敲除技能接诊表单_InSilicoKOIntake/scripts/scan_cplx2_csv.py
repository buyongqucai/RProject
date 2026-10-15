import gzip

def scan(path, gene="Cplx2"):
    print("FILE", path)
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        header = f.readline().strip().split(",")
        ncells = len(header) - 1
        print("n_cells", ncells)
        found = False
        for i, line in enumerate(f):
            g = line.split(",", 1)[0].strip().strip('"')
            if g == gene:
                vals = [int(float(x)) for x in line.strip().split(",")[1:] if x != ""]
                nd = sum(v > 0 for v in vals)
                print(gene, "n", len(vals), "detected", nd, "rate", round(nd / len(vals), 4), "mean", round(sum(vals) / len(vals), 4))
                found = True
                break
        print("found", found, "rows_scanned", i)

base = r"E:\RProject\.scratch\虚拟敲除技能接诊表单_InSilicoKOIntake\data"
scan(base + r"\GSE131272_D0-10x.csv.gz")
scan(base + r"\GSE131272_D2-10x.csv.gz")
