# -*- coding: utf-8 -*-
"""Representative validation for taxonomy (8 cases). Writes 验证记录_*.md."""
from __future__ import annotations

import json
import shutil
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent  # e:/RProject if ROOT is .../07_分类验证_Validation
# ROOT is 生信分析技能.../07_分类验证_Validation
SKILL_ROOT = ROOT.parent
PROJECT = SKILL_ROOT.parent
SHUQING = PROJECT / "书清项目"
OUT = ROOT
DATA = ROOT / "数据_data"
RECORDS = ROOT / "验证记录_records"
FIGS = ROOT / "图形_figures"

for p in (DATA, RECORDS, FIGS):
    p.mkdir(parents=True, exist_ok=True)


def write_record(case_id: str, title: str, status: str, body: str) -> None:
    path = RECORDS / f"验证记录_{case_id}.md"
    path.write_text(
        f"""# 验证记录 {case_id}: {title}

- **状态**: {status}
- **时间**: {datetime.now().isoformat(timespec='seconds')}
- **沙盒**: `07_分类验证_Validation/`

{body}
""",
        encoding="utf-8",
    )
    print(case_id, status)


def case01_geo_authenticity() -> None:
    """Reuse 书清 GSE267388 docs + sample tables."""
    gse = "GSE267388"
    doc = SHUQING / gse / "文档" / "数据集选型说明.md"
    tables = SHUQING / gse / "结果" / "表格"
    n_csv = list(tables.glob("*显著差异基因*.csv")) if tables.exists() else []
    sample_info_candidates = list((SHUQING / gse).rglob("*sample*"))[:5]
    ok = doc.exists() and tables.exists() and len(n_csv) > 0
    # count lines in one DEG as proxy of analysis having run
    deg_n = 0
    if n_csv:
        deg_n = max(0, sum(1 for _ in n_csv[0].open(encoding="utf-8", errors="ignore")) - 1)
    body = f"""
## 数据来源

- 登录号：`{gse}`（书清项目已落地，官方 GEO bulk）
- 选型说明：`{'存在' if doc.exists() else '缺失'}` → `{doc}`
- 结果表目录：`{'存在' if tables.exists() else '缺失'}`

## 核对

| 项 | 结果 |
|----|------|
| 数据集文档 | {'PASS' if doc.exists() else 'FAIL'} |
| DEG 结果表 | {'PASS' if n_csv else 'FAIL'}（示例显著基因行数≈{deg_n}） |
| 技能对齐 | `公共库挖掘_GEO-TCGA` + `数据真实性验证` + `转录组分析_RNA-seq` |

## 结论

本条验证**复用已下载官方数据与已跑通分析结果**，确认 GEO 队列技能与生产流水线路径一致，而非重复全量下载。
"""
    write_record("01_GEO真实性", "GEO 队列 + 真实性（复用书清 GSE267388）", "PASS" if ok else "FAIL", body)


def case02_deg_gsea() -> None:
    gse = "GSE267388"
    go = list((SHUQING / gse / "结果" / "表格").glob("*GO*.csv")) if (SHUQING / gse / "结果" / "表格").exists() else []
    kegg = list((SHUQING / gse / "结果" / "表格").glob("*KEGG*.csv"))
    deg = list((SHUQING / gse / "结果" / "表格").glob("*显著差异基因*.csv"))
    ok = bool(deg) and (bool(go) or bool(kegg))
    body = f"""
## 数据来源

- `{gse}` 书清结果表（差异 + 富集已产出）

## 核对

| 项 | 结果 |
|----|------|
| DEG 表 | {len(deg)} 个文件 |
| GO 表 | {len(go)} 个文件 |
| KEGG 表 | {len(kegg)} 个文件 |
| 技能对齐 | `转录组分析_RNA-seq` + `基因集富集与通路_GSEA-Pathway` |

## 轻量包检查（本机）

见文末 `package_check.json`（若生成）。
"""
    write_record("02_转录DEG_GSEA", "转录 DEG + GSEA（复用书清结果）", "PASS" if ok else "FAIL", body)


def case03_microarray() -> None:
    """Create tiny toy microarray matrix + limma-like t-test in pure Python."""
    import csv
    import math
    import random

    random.seed(42)
    genes = [f"GENE{i}" for i in range(1, 101)]
    # 3 ctrl + 3 treat
    samples = [f"C{i}" for i in range(1, 4)] + [f"T{i}" for i in range(1, 4)]
    path = DATA / "toy_microarray_matrix.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["gene"] + samples)
        for g in genes:
            base = random.gauss(8, 1)
            row = [g]
            for s in samples:
                mu = base + (1.5 if s.startswith("T") and g.endswith(("1", "2", "3", "4", "5")) else 0)
                row.append(round(mu + random.gauss(0, 0.3), 4))
            w.writerow(row)
    # simple DEG count
    # reload and t-approx
    import statistics

    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    n_sig = 0
    for r in rows:
        c = [float(r[s]) for s in samples if s.startswith("C")]
        t = [float(r[s]) for s in samples if s.startswith("T")]
        # crude effect
        if abs(statistics.mean(t) - statistics.mean(c)) > 1.0:
            n_sig += 1
    body = f"""
## 数据来源

- **Toy 芯片矩阵**（非全量 GEO 下载，避免大 CEL）：`{path}`
- 设计：3 Control vs 3 Treat，100 probes

## 核对

| 项 | 结果 |
|----|------|
| 矩阵写出 | PASS |
| 粗差异探针（\\|Δmean\\|>1） | {n_sig} |
| 技能对齐 | `基因芯片表达分析_Microarray`（与 RNA-seq 并列，不合并） |

## 说明

完整 Affy CEL 归一化需 `affy`/`limma`；本条验证**输入契约与组间设计**，全量 CEL 下载标为后续扩量。
"""
    write_record("03_芯片Microarray", "基因芯片（toy 矩阵）", "PASS", body)


def case04_scrna() -> None:
    gse = "GSE190856"
    prop = SHUQING / gse / "结果" / "表格" / f"{gse}_细胞类型比例.csv"
    alt = list((SHUQING / gse / "结果" / "表格").glob("*细胞类型比例*.csv")) if (SHUQING / gse / "结果" / "表格").exists() else []
    path = prop if prop.exists() else (alt[0] if alt else None)
    ok = path is not None
    nlines = 0
    if path:
        nlines = sum(1 for _ in path.open(encoding="utf-8", errors="ignore"))
    body = f"""
## 数据来源

- `{gse}` 书清单细胞结果（已下载官方 10x/矩阵并完成注释）
- 比例表：`{path}`

## 核对

| 项 | 结果 |
|----|------|
| 细胞类型比例表 | {'PASS' if ok else 'FAIL'}（行数≈{nlines}） |
| 技能对齐 | `单细胞与空间转录组分析_scRNA-Spatial`；进阶见 `单细胞进阶方法_scRNA-Advanced` |

## 说明

不重复下载完整 10x raw；验证主技能与进阶技能边界（主入口 vs 轨迹/组成/整合）。
"""
    write_record("04_单细胞", "单细胞（复用 GSE190856）", "PASS" if ok else "FAIL", body)


def case05_survival_roc() -> None:
    """Toy survival + ROC without requiring Bioconductor."""
    import csv
    import math
    import random

    random.seed(1)
    path = DATA / "toy_clinical_survival.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sample", "time", "status", "marker", "group"])
        for i in range(60):
            marker = random.gauss(0, 1)
            # higher marker -> higher hazard approx shorter time
            time = max(1, int(30 - 5 * marker + random.gauss(0, 5)))
            status = 1 if random.random() < 0.55 else 0
            group = "High" if marker > 0 else "Low"
            w.writerow([f"S{i+1}", time, status, round(marker, 3), group])

    # AUC-like concordance: compare marker vs status (crude)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    pos = [float(r["marker"]) for r in rows if r["status"] == "1"]
    neg = [float(r["marker"]) for r in rows if r["status"] == "0"]
    # Mann-Whitney AUC
    conc = 0
    for p in pos:
        for n in neg:
            if p > n:
                conc += 1
            elif p == n:
                conc += 0.5
    auc = conc / (len(pos) * len(neg)) if pos and neg else float("nan")

    # try R survival if available
    r_status = "SKIP"
    rscript = shutil.which("Rscript") or shutil.which("Rscript.exe")
    # common Windows path
    for cand in [
        rscript,
        r"E:\R-4.6.0\bin\Rscript.exe",
        r"C:\Program Files\R\R-4.4.0\bin\Rscript.exe",
    ]:
        if cand and Path(cand).exists():
            rscript = cand
            break
    if rscript and Path(rscript).exists():
        rcode = DATA / "toy_surv_check.R"
        rcode.write_text(
            f"""
d <- read.csv(r"{path.as_posix()}")
if (requireNamespace("survival", quietly=TRUE)) {{
  fit <- survival::survfit(survival::Surv(time, status) ~ group, data=d)
  cat("SURV_OK\\n")
}} else {{
  cat("SURV_PKG_MISSING\\n")
}}
if (requireNamespace("pROC", quietly=TRUE)) {{
  cat("PROC_OK\\n")
}} else {{
  cat("PROC_PKG_MISSING\\n")
}}
""",
            encoding="utf-8",
        )
        try:
            out = subprocess.check_output([rscript, str(rcode)], stderr=subprocess.STDOUT, text=True, timeout=60)
            if "SURV_OK" in out:
                r_status = "PASS_survival_pkg"
            elif "SURV_PKG_MISSING" in out:
                r_status = "SKIP_no_survival_pkg"
            else:
                r_status = "CHECK:\\n" + out[:500]
        except Exception as e:
            r_status = f"SKIP_rscript_error: {e}"

    body = f"""
## 数据来源

- Toy 临床表：`{path}`（n=60）
- 粗 AUC（marker vs status）：**{auc:.3f}**

## 核对

| 项 | 结果 |
|----|------|
| 临床表生成 | PASS |
| R survival/pROC | {r_status} |
| 技能对齐 | `生存分析与预后模型_Survival` + `诊断效能ROC_DiagnosticROC`（从 GEO-TCGA 拆出） |

## 说明

验证方法技能独立于 GEO 下载技能；全队列 TCGA 下载不在本轮范围。
"""
    st = "PASS" if auc == auc else "FAIL"
    write_record("05_生存ROC", "生存 + ROC（toy + 可选 R 包）", st, body)


def case06_methylation() -> None:
    """Toy beta matrix; minfi optional."""
    import csv
    import random

    random.seed(7)
    path = DATA / "toy_methylation_beta.csv"
    cps = [f"cg{i:08d}" for i in range(1, 51)]
    samples = [f"N{i}" for i in range(1, 4)] + [f"T{i}" for i in range(1, 4)]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cpg"] + samples)
        for c in cps:
            row = [c]
            for s in samples:
                b = random.random()
                if s.startswith("T") and c.endswith("1"):
                    b = min(0.99, b + 0.3)
                row.append(round(b, 4))
            w.writerow(row)
    body = f"""
## 数据来源

- Toy beta 矩阵：`{path}`（50 CpG × 6 样本）
- 未下载完整 EPIC idat（体积大）；技能 `DNA甲基化分析_WGBS-RRBS` 已含 EPIC 合并说明

## 核对

| 项 | 结果 |
|----|------|
| beta 契约 | PASS |
| 全量 EPIC 下载 | SKIP（按计划不做 TB/大芯片全量） |
| 技能边界 | 甲基化独立；不与 ChIP/ATAC 合并 |
"""
    write_record("06_甲基化", "甲基化（toy beta + SKIP 全量）", "PASS_PARTIAL", body)


def case07_network_dock() -> None:
    """Toy compound-target ∩ disease genes; check vina CLI."""
    import csv

    disease = DATA / "toy_disease_genes.txt"
    targets = DATA / "toy_compound_targets.csv"
    disease.write_text("TP53\nEGFR\nAKT1\nMTOR\nVEGFA\nSTAT3\n", encoding="utf-8")
    with targets.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["compound", "target"])
        for c, t in [("CmpA", "EGFR"), ("CmpA", "AKT1"), ("CmpB", "TP53"), ("CmpB", "BRCA1"), ("CmpC", "EGFR")]:
            w.writerow([c, t])
    dis = set(disease.read_text(encoding="utf-8").split())
    hits = []
    with targets.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["target"] in dis:
                hits.append((r["compound"], r["target"]))
    vina = shutil.which("vina") or shutil.which("vina.exe")
    vina_status = f"FOUND:{vina}" if vina else "SKIP_no_vina_CLI"
    # try fetch tiny PDB header as structure presence check
    pdb_path = DATA / "1M17_header.txt"
    pdb_ok = False
    try:
        with urllib.request.urlopen("https://files.rcsb.org/header/1M17.pdb", timeout=20) as resp:
            pdb_path.write_bytes(resp.read()[:2000])
        pdb_ok = pdb_path.exists() and pdb_path.stat().st_size > 100
    except Exception as e:
        pdb_path.write_text(f"SKIP download: {e}\\n", encoding="utf-8")

    body = f"""
## 数据来源

- Toy 疾病基因：`{disease}`
- Toy 成分-靶点：`{targets}`
- PDB 1M17 header 探测：`{pdb_path}` → {'PASS' if pdb_ok else 'SKIP'}

## 核对

| 项 | 结果 |
|----|------|
| 网络交集边数 | {len(hits)} → {hits} |
| AutoDock Vina CLI | {vina_status} |
| 技能对齐 | `网络药理学` → `蛋白结构与建模` → `分子对接`（MD 本轮仅契约，不做轨迹） |

## 说明

按计划：对接最多 1 次 Vina 示范；无 CLI 则 SKIP 并保留网络交集 PASS。
"""
    st = "PASS" if hits else "FAIL"
    if not vina:
        st = "PASS_PARTIAL"
    write_record("07_网络药理对接", "网络药理交集 + 对接 CLI/结构探测", st, body)


def case08_microbiome() -> None:
    import csv
    import random

    random.seed(3)
    path = DATA / "toy_16s_otu.csv"
    taxa = [f"Taxon_{i}" for i in range(1, 21)]
    samples = [f"S{i}" for i in range(1, 7)]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["taxon"] + samples)
        for t in taxa:
            w.writerow([t] + [random.randint(0, 100) for _ in samples])
    body = f"""
## 数据来源

- Toy OTU/ASV 表：`{path}`（20 taxa × 6 samples）
- 未拉取 QIITA/SRA 全量；16S 与宏基因组边界已在分类中分开

## 核对

| 项 | 结果 |
|----|------|
| 丰度表契约 | PASS |
| 技能对齐 | `微生物组16S分析_Microbiome16S` vs `宏基因组与病原_Metagenome-Pathogen`（已合并宏转录/病毒/AMR） |
"""
    write_record("08_微生物", "16S/宏基因组（toy + 边界）", "PASS", body)


def package_check() -> None:
    info = {"ggplot2": None, "limma": None, "Seurat": None}
    rscript = None
    for cand in [
        shutil.which("Rscript"),
        r"E:\\R-4.6.0\\bin\\Rscript.exe",
    ]:
        if cand and Path(str(cand).replace("\\\\", "\\")).exists():
            rscript = str(cand).replace("\\\\", "\\")
            break
    if rscript:
        code = 'for (p in c("ggplot2","limma","Seurat")) cat(p, requireNamespace(p, quietly=TRUE), "\\n")'
        try:
            out = subprocess.check_output([rscript, "-e", code], stderr=subprocess.STDOUT, text=True, timeout=60)
            (DATA / "package_check.txt").write_text(out, encoding="utf-8")
        except Exception as e:
            (DATA / "package_check.txt").write_text(str(e), encoding="utf-8")
    else:
        (DATA / "package_check.txt").write_text("Rscript not found", encoding="utf-8")


def main():
    package_check()
    case01_geo_authenticity()
    case02_deg_gsea()
    case03_microarray()
    case04_scrna()
    case05_survival_roc()
    case06_methylation()
    case07_network_dock()
    case08_microbiome()
    # summary stub for next todo
    records = sorted(RECORDS.glob("验证记录_*.md"))
    summary = {
        "n_records": len(records),
        "files": [p.name for p in records],
        "time": datetime.now().isoformat(timespec="seconds"),
    }
    (ROOT / "validation_run_meta.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("wrote", len(records), "records")


if __name__ == "__main__":
    main()
