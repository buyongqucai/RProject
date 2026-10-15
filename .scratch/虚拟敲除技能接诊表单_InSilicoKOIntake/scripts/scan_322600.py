import gzip

path = r"E:\RProject\.scratch\虚拟敲除技能接诊表单_InSilicoKOIntake\data\GSE322600_feature_counts.tsv.gz"
with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
    header = f.readline().rstrip("\n").split("\t")
    print("n_cols", len(header))
    print("header_head", header[:8])
    found = False
    for i, line in enumerate(f):
        parts = line.rstrip("\n").split("\t")
        g = parts[0].strip('"')
        if g in ("Cplx2", "CPLX2"):
            vals = []
            for x in parts[1:]:
                if x == "":
                    continue
                vals.append(float(x))
            nd = sum(v > 0 for v in vals)
            print("gene", g, "n", len(vals), "detected", nd, "rate", round(nd / max(len(vals), 1), 4))
            found = True
            break
    print("found", found, "rows", i)
