#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HMP2/IBDMDB 菌群臂真实队列验证 — UC vs nonIBD
脚本版本: run_validation.py v1.1 (2026-10-08)

预登记 (pre-registration, 先于看结果写下):
  队列: IBDMDB/HMP2 metagenomics (MetaPhlAn taxonomic_profiles)
  比较: UC vs nonIBD (主分析); CD vs nonIBD 仅用于 guild 参照
  检验: Mann-Whitney U (scipy.stats.mannwhitneyu, alternative='two-sided')
  多重校正: BH-FDR, 覆盖全部受测物种 (guild 单独报告, 不并入 FDR)
  效应量: rank-biserial correlation, r = 2*U/(n1*n2) - 1
           (U 为 UC 组的 U 统计量; r>0 表示 UC 丰度更高/富集, r<0 表示 UC 耗竭)
  受测物种 (contains 匹配 s__ 行):
    丁酸相关: Faecalibacterium_prausnitzii, Roseburia_intestinalis,
              Eubacterium_rectale, Eubacterium_hallii(=Anaerobutyricum_hallii 旧名),
              Anaerostipes_caccae, Anaerostipes_hadrus, Anaerostipes_unclassified,
              Butyricicoccus_pullicaecorum, Coprococcus_comes, Ruminococcus_bromii,
              Anaerobutyricum spp. (预期 not_detected, 表中以 Eubacterium_hallii 计)
    参照对比: Ruminococcus_gnavus, Bilophila_wadsworthia, Escherichia_coli,
              Enterobacteriaceae (科水平物种行求和)
  guild (样本级相对丰度求和): F.prausnitzii + R.intestinalis + E.rectale
              + Anaerostipes(全部物种行) + Butyricicoccus + C.comes
  未检出物种: 标注 not_detected, 不参与统计检验
"""
import json
import gzip
import datetime
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

WORK = "/sessions/admiring-jolly-keller/mnt/outputs/md_micro"
URL_ABUND = "https://g-227ca.190ebd.75bc.data.globus.org/ibdmdb/products/HMP2/MGX/2018-05-04/taxonomic_profiles.tsv.gz"
URL_META = "https://g-227ca.190ebd.75bc.data.globus.org/ibdmdb/metadata/hmp2_metadata_2018-08-20.csv"
SCRIPT_VERSION = "run_validation.py v1.1 (2026-10-08; v1.0 -> v1.1 修复 guild 属水平成员匹配遗漏)"

# ---------- 预登记受测物种: (species_label, match_substrings) ----------
PREREG_SPECIES = [
    ("Faecalibacterium_prausnitzii", ["Faecalibacterium_prausnitzii"]),
    ("Roseburia_intestinalis",       ["Roseburia_intestinalis"]),
    ("Eubacterium_rectale",          ["Eubacterium_rectale"]),
    ("Eubacterium_hallii_(=Anaerobutyricum_hallii)", ["Eubacterium_hallii"]),
    ("Anaerobutyricum_spp",          ["Anaerobutyricum"]),   # 预期 not_detected
    ("Anaerostipes_caccae",          ["Anaerostipes_caccae"]),
    ("Anaerostipes_hadrus",          ["Anaerostipes_hadrus"]),
    ("Anaerostipes_unclassified",    ["Anaerostipes_unclassified"]),
    ("Butyricicoccus_pullicaecorum", ["Butyricicoccus_pullicaecorum"]),
    ("Coprococcus_comes",            ["Coprococcus_comes"]),
    ("Ruminococcus_bromii",          ["Ruminococcus_bromii"]),
    ("Ruminococcus_gnavus",          ["Ruminococcus_gnavus"]),
    ("Bilophila_wadsworthia",        ["Bilophila_wadsworthia"]),
    ("Escherichia_coli",             ["Escherichia_coli"]),
    ("Enterobacteriaceae_family_sum", ["__ENTEROBACTERIACEAE_SUM__"]),  # 特殊: 科水平求和
]

# guild 成分 (样本级求和)
GUILD_MEMBERS = [
    "Faecalibacterium_prausnitzii",
    "Roseburia_intestinalis",
    "Eubacterium_rectale",
    "g__Anaerostipes",       # 属内全部物种行
    "g__Butyricicoccus",     # 属内全部物种行
    "Coprococcus_comes",
]

def bh_fdr(pvals):
    """Benjamini-Hochberg FDR, 自实现."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    q = ranked * n / (np.arange(n) + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    q = np.clip(q, 0, 1)
    out = np.empty(n)
    out[order] = q
    return out

def main():
    # ---------- 读取丰度表 ----------
    with gzip.open(f"{WORK}/taxonomic_profiles.tsv.gz", "rt") as fh:
        abundance = pd.read_csv(fh, sep="\t", index_col=0)
    abundance.index = abundance.index.astype(str)
    # 只保留物种行 (含 s__ 且不再含更深层级)
    sp_rows = abundance[abundance.index.str.contains("s__") &
                        ~abundance.index.str.contains(r"\|t__", regex=True)]
    species_lookup = {}
    for clade in sp_rows.index:
        sp = clade.split("|s__")[-1]
        species_lookup.setdefault(sp, []).append(clade)

    # ---------- 读取元数据 ----------
    meta = pd.read_csv(f"{WORK}/hmp2_metadata.csv", low_memory=False)
    mg = meta[meta["data_type"] == "metagenomics"].copy()
    mg = mg[mg["diagnosis"].isin(["UC", "nonIBD", "CD"])]
    samples = [s for s in abundance.columns if s in set(mg["External ID"])]
    diag = mg.set_index("External ID")["diagnosis"]
    uc = [s for s in samples if diag[s] == "UC"]
    ctrl = [s for s in samples if diag[s] == "nonIBD"]
    cd = [s for s in samples if diag[s] == "CD"]
    print(f"matched samples: {len(samples)} | UC={len(uc)} nonIBD={len(ctrl)} CD={len(cd)}")

    def get_row_vector(label, substrings):
        """返回样本级丰度向量; 未检出返回 None."""
        if substrings == ["__ENTEROBACTERIACEAE_SUM__"]:
            rows = [c for c in sp_rows.index
                    if "|f__Enterobacteriaceae|" in c and "Viruses" not in c]
            if not rows:
                return None, []
            return sp_rows.loc[rows].sum(axis=0), rows
        rows = []
        for sub in substrings:
            if sub.startswith("g__"):
                # 属水平: 匹配完整 clade 串中的 g__<genus>|
                rows.extend([c for c in sp_rows.index if sub + "|" in c])
                continue
            for sp_key, clades in species_lookup.items():
                if sub in sp_key:
                    rows.extend(clades)
        if not rows:
            return None, []
        rows = list(dict.fromkeys(rows))  # 去重
        return sp_rows.loc[rows].sum(axis=0), rows

    # ---------- 物种检验 ----------
    results = []
    for label, subs in PREREG_SPECIES:
        vec, matched = get_row_vector(label, subs)
        if vec is None:
            results.append(dict(species=label, n_UC=len(uc), n_ctrl=len(ctrl),
                                median_UC=np.nan, median_ctrl=np.nan,
                                detection_UC=0.0, detection_ctrl=0.0,
                                U=np.nan, p=np.nan, FDR_BH=np.nan,
                                rank_biserial=np.nan, direction="not_detected"))
            continue
        x = vec[uc].values.astype(float)
        y = vec[ctrl].values.astype(float)
        med_x, med_y = np.median(x), np.median(y)
        det_x, det_y = float((x > 0).mean()), float((y > 0).mean())
        if (x == 0).all() and (y == 0).all():
            results.append(dict(species=label, n_UC=len(x), n_ctrl=len(y),
                                median_UC=0.0, median_ctrl=0.0,
                                detection_UC=0.0, detection_ctrl=0.0,
                                U=np.nan, p=np.nan, FDR_BH=np.nan,
                                rank_biserial=np.nan, direction="not_detected"))
            continue
        U, p = mannwhitneyu(x, y, alternative="two-sided")
        r = 2 * U / (len(x) * len(y)) - 1   # r>0: UC 富集; r<0: UC 耗竭
        results.append(dict(species=label, n_UC=len(x), n_ctrl=len(y),
                            median_UC=med_x, median_ctrl=med_y,
                            detection_UC=det_x, detection_ctrl=det_y,
                            U=U, p=p, FDR_BH=np.nan, rank_biserial=r,
                            direction="enriched_in_UC" if r > 0 else "depleted_in_UC"))
    df = pd.DataFrame(results)
    tested = df["p"].notna()
    df.loc[tested, "FDR_BH"] = bh_fdr(df.loc[tested, "p"].values)
    df.to_csv(f"{WORK}/species_test_results.csv", index=False)

    # ---------- guild ----------
    guild_rows = []
    gvec, gmatched = get_row_vector("guild", GUILD_MEMBERS)
    for case_label, case_samples in [("UC_vs_nonIBD", uc), ("CD_vs_nonIBD", cd)]:
        x = gvec[case_samples].values.astype(float)
        y = gvec[ctrl].values.astype(float)
        U, p = mannwhitneyu(x, y, alternative="two-sided")
        r = 2 * U / (len(x) * len(y)) - 1
        guild_rows.append(dict(
            guild="butyrate_producer_guild", comparison=case_label,
            n_case=len(x), n_ctrl=len(y),
            median_case=np.median(x), median_ctrl=np.median(y),
            detection_case=float((x > 0).mean()), detection_ctrl=float((y > 0).mean()),
            U=U, p=p, rank_biserial=r,
            direction="enriched_in_case" if r > 0 else "depleted_in_case"))
    gdf = pd.DataFrame(guild_rows)
    gdf.to_csv(f"{WORK}/guild_summary.csv", index=False)

    # ---------- run_meta ----------
    run_meta = dict(
        script_version=SCRIPT_VERSION,
        run_date=datetime.date.today().isoformat(),
        abundance_url=URL_ABUND, metadata_url=URL_META,
        download_date="2026-10-08",
        n_samples_matched=len(samples),
        group_n=dict(UC=len(uc), nonIBD=len(ctrl), CD=len(cd)),
        test="Mann-Whitney U two-sided (scipy.stats.mannwhitneyu)",
        fdr="Benjamini-Hochberg over tested species (guild reported separately)",
        effect_size="rank-biserial r = 2U/(n1*n2)-1; r>0 = higher in UC",
        n_preregistered_species=len(PREREG_SPECIES),
        n_tested=int(tested.sum()),
        n_not_detected=int((df["direction"] == "not_detected").sum()),
        guild_members=GUILD_MEMBERS,
        notes="Multiple samples per participant; sample-level analysis (limitation).",
    )
    with open(f"{WORK}/run_meta.json", "w") as fh:
        json.dump(run_meta, fh, indent=2, ensure_ascii=False)

    # ---------- 控制台摘要 ----------
    pd.set_option("display.width", 200)
    print("\n=== species ===")
    print(df.to_string(index=False))
    print("\n=== guild ===")
    print(gdf.to_string(index=False))

if __name__ == "__main__":
    main()
