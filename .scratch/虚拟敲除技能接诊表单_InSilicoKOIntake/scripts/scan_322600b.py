import gzip

path = r"E:\RProject\.scratch\虚拟敲除技能接诊表单_InSilicoKOIntake\data\GSE322600_feature_counts.tsv.gz"
with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
    header = None
    for line in f:
        if line.startswith("#"):
            continue
        header = line.rstrip("\n").split("\t")
        break
    print("ncols", len(header))
    print("first_fields", header[:6])
    samples = header[6:] if header[0] == "Geneid" else header[1:]
    # featureCounts: Geneid Chr Start End Strand Length then samples
    print("n_samples", len(samples))
    print("sample0", samples[0][:80] if samples else None)
    n_cion = sum("cion" in s.lower() for s in samples)
    n_sham = sum("sham" in s.lower() for s in samples)
    print("cion", n_cion, "sham", n_sham)
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if parts[0] in ("Cplx2", "CPLX2") or (len(parts) > 7 and parts[0] == "Cplx2"):
            vals = [float(x) for x in parts[-len(samples):]]
            nd = sum(v > 0 for v in vals)
            print("Cplx2 n", len(vals), "detected", nd, "rate", round(nd / len(vals), 4))
            break
        if parts[0] == "Cplx2":
            break
    else:
        # second pass if gene name is not first col
        pass
print("done")
