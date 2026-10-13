import gzip

path = r"E:\RProject\.scratch\虚拟敲除技能接诊表单_InSilicoKOIntake\data\GSE322600_feature_counts.tsv.gz"
with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
    for line in f:
        if line.startswith("#"):
            continue
        header = line.rstrip("\n").split("\t")
        break
    samples = header[7:]
    labels = ["cion" if "cion" in s.lower() else "sham" if "sham" in s.lower() else "other" for s in samples]
    print("n_neurons", len(samples), "cion", labels.count("cion"), "sham", labels.count("sham"))
    found = False
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 8:
            continue
        if parts[6] == "Cplx2":
            vals = [float(x) for x in parts[7:]]
            for lab in ("cion", "sham", "all"):
                if lab == "all":
                    vv = vals
                else:
                    vv = [v for v, l in zip(vals, labels) if l == lab]
                nd = sum(v > 0 for v in vv)
                print(lab, "n", len(vv), "detected", nd, "rate", round(nd / len(vv), 4), "mean", round(sum(vv) / len(vv), 2))
            found = True
            break
    print("found", found)
