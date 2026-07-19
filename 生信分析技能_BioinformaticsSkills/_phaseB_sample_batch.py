# NOTE (2026-07-18): 禁止再生成全局同构 toy DEG+sample_volcano.png。
# 新样例请用 _phaseC_delivery_rerun.py / 统一交付规范_DeliveryStandards。
# 本文件保留仅作历史；main() 已改为拒绝全量雷同生成。
# -*- coding: utf-8 -*-
"""Phase B: create 01_样例_sample/ for every skill, run lightweight analyses, write reports."""
from __future__ import annotations

import json
import os
import re
import subprocess
import textwrap
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(r"E:/RProject/生信分析技能_BioinformaticsSkills")
VAL_DIR = ROOT / "07_分类验证_Validation"
RESULTS_JSON = VAL_DIR / "每技能样例_results.json"

# Skills that cannot run full pipeline locally → BLOCKED + degraded contract sample
BLOCKED_REASON = {
    "分子动力学模拟_MolecularDynamics": "需 GROMACS/AMBER 等 MD 引擎与 GPU/长时间轨迹",
    "基因组组装与注释_GenomeAssembly": "需大规模测序读段与组装器（SPAdes/Flye 等）及 TB 级磁盘",
    "长读长测序分析_LongRead": "需长读长 FASTQ 与 minimap2/dorado 等 CLI",
    "分子对接与虚拟筛选_MolecularDocking": "需 AutoDock Vina/商业对接软件与受体准备流水线",
    "三维基因组分析_3DGenome": "需 Hi-C 原始或 .hic/.cool 全库与 juicer/cooler 栈",
    "结构变异分析_StructuralVariant": "需全基因组 BAM 与 manta/delly 等 SV caller",
    "变异检测与外显子组_Variant-WES": "需 WES BAM/GATK 完整最佳实践流水线",
    "表观遗传ChIP-seq_Epigenomics": "需 ChIP FASTQ 与 MACS2/bowtie 比对栈",
    "ATAC专论_ATAC-seq": "需 ATAC FASTQ 与 peak calling CLI",
    "RNA融合基因检测_FusionGene": "需 RNA-seq BAM/FASTQ 与 STAR-Fusion/Arriba",
    "新抗原与免疫组库_Neoantigen-TCR": "需 HLA 分型 CLI 与肽段预测工具链",
    "放射组学与病理组学_Radiomics-Pathomics": "需医学影像 DICOM/WSI 与 pyradiomics 环境",
}

LIGHT_CONTRACT = {
    "研究方案编排_ResearchOrchestrator",
    "统一可视化规范_VizStandards",
    "数据真实性验证_DataAuthenticity",
    "可复现工作流_ReproducibleWorkflow",
    "文献与数据库检索_Literature-DB",
}


def find_skills() -> list[Path]:
    docs = sorted(ROOT.rglob("技能说明_*.md"))
    out = []
    for d in docs:
        rel = d.relative_to(ROOT).as_posix()
        if rel.startswith("07_分类验证") or "01_样例_sample" in rel:
            continue
        out.append(d.parent)
    return out


def ensure_tree(skill_dir: Path) -> Path:
    sample = skill_dir / "01_样例_sample"
    for sub in [
        "代码文件",
        "数据文件",
        "结果文件/图片文件",
        "结果文件/数据文件",
        "结果文件/报告文件",
    ]:
        (sample / sub).mkdir(parents=True, exist_ok=True)
    return sample


def write_toy_csv(path: Path, kind: str) -> None:
    if kind == "counts":
        lines = ["gene,S1,S2,S3,S4,S5,S6"]
        for i in range(1, 41):
            # simple two-group pattern
            base = 20 + (i % 7)
            vals = [
                str(base + (3 if i <= 10 else 0)),
                str(base + (4 if i <= 10 else 1)),
                str(base + (5 if i <= 10 else 0)),
                str(base),
                str(base + 1),
                str(base),
            ]
            lines.append(f"G{i}," + ",".join(vals))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    elif kind == "meta":
        path.write_text(
            "sample,group\nS1,Case\nS2,Case\nS3,Case\nS4,Control\nS5,Control\nS6,Control\n",
            encoding="utf-8",
        )
    elif kind == "survival":
        path.write_text(
            "id,time,status,risk,group\n"
            + "\n".join(
                f"P{i},{30+i*3},{i%2},{(i%5)/5.0},{'High' if i%2 else 'Low'}"
                for i in range(1, 41)
            )
            + "\n",
            encoding="utf-8",
        )
    elif kind == "network":
        path.write_text(
            "compound,target\nC1,TP53\nC1,EGFR\nC2,EGFR\nC2,KRAS\nC3,TP53\nC3,BRAF\n",
            encoding="utf-8",
        )
        path.with_name("disease_genes.txt").write_text(
            "TP53\nEGFR\nKRAS\nMYC\n", encoding="utf-8"
        )
    elif kind == "otu":
        path.write_text(
            "taxon,A1,A2,A3,B1,B2,B3\n"
            "Taxa1,10,12,11,2,3,1\n"
            "Taxa2,5,4,6,15,14,16\n"
            "Taxa3,8,7,9,8,7,9\n"
            "Taxa4,1,2,1,10,12,11\n",
            encoding="utf-8",
        )
    elif kind == "beta":
        path.write_text(
            "cpg,S1,S2,S3,S4\n"
            "cg1,0.8,0.75,0.2,0.25\n"
            "cg2,0.7,0.72,0.3,0.28\n"
            "cg3,0.4,0.45,0.42,0.41\n"
            "cg4,0.9,0.88,0.15,0.18\n",
            encoding="utf-8",
        )
    else:
        path.write_text("x,y\n1,2\n2,3\n3,5\n4,7\n", encoding="utf-8")


def r_script_for(skill_dir: Path, folder: str, mode: str) -> str:
    """Generate R sample script content."""
    title = folder
    status_default = "PASS" if mode != "blocked" else "BLOCKED"
    reason = BLOCKED_REASON.get(folder, "")
    return textwrap.dedent(
        f"""\
        # 样例分析脚本 — {title}
        # 数据来源：toy / 可复现随机矩阵（诚实标注，非真实临床结论）
        options(stringsAsFactors = FALSE)
        set.seed(42)

        # 本脚本位于 01_样例_sample/代码文件/；样例根为上一级
        sample_root <- normalizePath("..", winslash = "/", mustWork = TRUE)
        skill_root <- normalizePath("../..", winslash = "/", mustWork = TRUE)
        data_dir <- file.path(sample_root, "数据文件")
        fig_dir <- file.path(sample_root, "结果文件", "图片文件")
        tab_dir <- file.path(sample_root, "结果文件", "数据文件")
        rep_dir <- file.path(sample_root, "结果文件", "报告文件")
        dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)
        dir.create(tab_dir, recursive = TRUE, showWarnings = FALSE)
        dir.create(rep_dir, recursive = TRUE, showWarnings = FALSE)
        dir.create(data_dir, recursive = TRUE, showWarnings = FALSE)

        # 尽量 source 同级脚本骨架（若存在）
        scripts_dir <- file.path(skill_root, "脚本_scripts")
        sk <- list.files(scripts_dir, pattern = "[.][Rr]$", full.names = TRUE)
        skeleton_note <- "无骨架或未执行"
        if (length(sk)) {{
          # 仅记录路径，不强制 source 可能含交互/路径假设的骨架
          skeleton_note <- paste(basename(sk), collapse = ", ")
        }}

        mode <- "{mode}"
        status <- "{status_default}"
        blocked_reason <- "{reason}"

        # ---- 轻量分析：两组表达差异玩具 + PCA 图 ----
        counts_f <- file.path(data_dir, "toy_counts.csv")
        meta_f <- file.path(data_dir, "toy_meta.csv")
        if (!file.exists(counts_f)) {{
          # fallback generate
          genes <- paste0("G", 1:40)
          mat <- matrix(rpois(40 * 6, lambda = 20), nrow = 40)
          mat[1:10, 1:3] <- mat[1:10, 1:3] + 15
          colnames(mat) <- paste0("S", 1:6)
          df <- data.frame(gene = genes, mat, check.names = FALSE)
          write.csv(df, counts_f, row.names = FALSE)
          write.csv(data.frame(sample = colnames(mat),
                               group = c(rep("Case", 3), rep("Control", 3))),
                    meta_f, row.names = FALSE)
        }}

        counts <- read.csv(counts_f, check.names = FALSE)
        meta <- read.csv(meta_f, check.names = FALSE)
        mat <- as.matrix(counts[, -1])
        rownames(mat) <- counts[[1]]
        storage.mode(mat) <- "numeric"
        logc <- log2(mat + 1)
        group <- meta$group[match(colnames(mat), meta$sample)]

        # t-test per gene (toy DEG)
        pvals <- apply(logc, 1, function(v) {{
          tryCatch(t.test(v[group == "Case"], v[group == "Control"])$p.value,
                   error = function(e) NA_real_)
        }})
        lfc <- rowMeans(logc[, group == "Case", drop = FALSE]) -
          rowMeans(logc[, group == "Control", drop = FALSE])
        deg <- data.frame(
          gene = rownames(logc),
          logFC = lfc,
          pvalue = pvals,
          stringsAsFactors = FALSE
        )
        deg$padj <- p.adjust(deg$pvalue, method = "BH")
        deg <- deg[order(deg$pvalue), ]
        write.csv(deg, file.path(tab_dir, "toy_deg_results.csv"), row.names = FALSE)

        # summary stats
        summary_df <- data.frame(
          n_genes = nrow(deg),
          n_sig_p05 = sum(deg$pvalue < 0.05, na.rm = TRUE),
          n_samples = ncol(mat),
          mode = mode,
          status = status,
          skill = "{title}",
          skeleton_files = skeleton_note
        )
        write.csv(summary_df, file.path(tab_dir, "sample_summary.csv"), row.names = FALSE)

        # PCA scatter PNG @ 600 dpi
        pc <- prcomp(t(logc), scale. = TRUE)
        png(file.path(fig_dir, "sample_pca.png"), width = 6, height = 5,
            units = "in", res = 600)
        cols <- ifelse(group == "Case", "#C44E52", "#4C72B0")
        plot(pc$x[, 1], pc$x[, 2], col = cols, pch = 19,
             xlab = paste0("PC1 (", round(summary(pc)$importance[2, 1] * 100, 1), "%)"),
             ylab = paste0("PC2 (", round(summary(pc)$importance[2, 2] * 100, 1), "%)"),
             main = paste("Sample PCA —", "{title}"))
        legend("topright", legend = c("Case", "Control"),
               col = c("#C44E52", "#4C72B0"), pch = 19, bty = "n")
        dev.off()

        # volcano-like
        png(file.path(fig_dir, "sample_volcano.png"), width = 6, height = 5,
            units = "in", res = 600)
        plot(deg$logFC, -log10(pmax(deg$pvalue, 1e-300)),
             pch = 19, col = ifelse(deg$pvalue < 0.05, "#C44E52", "grey70"),
             xlab = "logFC (Case - Control)", ylab = "-log10(p)",
             main = "Toy volcano")
        abline(h = -log10(0.05), lty = 2, col = "grey40")
        dev.off()

        # HTML report
        fig_rel1 <- "../图片文件/sample_pca.png"
        fig_rel2 <- "../图片文件/sample_volcano.png"
        pass_note <- if (status == "BLOCKED") {{
          paste0("<p><b>状态：BLOCKED</b> — ", blocked_reason,
                 "。本样例为<strong>降级契约检查</strong>（toy 矩阵统计+出图），证明目录与出图规范可运行。</p>")
        }} else if (mode == "light") {{
          "<p><b>状态：PASS</b>（轻量契约样例：目录结构、toy 统计与出版级出图）。</p>"
        }} else {{
          "<p><b>状态：PASS</b>。玩具两组差异 + PCA/火山图；非真实生物学结论。</p>"
        }}

        html <- paste0(
          "<!DOCTYPE html><html><head><meta charset='utf-8'><title>",
          "{title} 样例报告</title>",
          "<style>body{{font-family:Segoe UI,Arial,sans-serif;max-width:900px;margin:2rem auto;line-height:1.5}}",
          "img{{max-width:100%;border:1px solid #ddd}} table{{border-collapse:collapse}} td,th{{border:1px solid #ccc;padding:4px 8px}}</style>",
          "</head><body>",
          "<h1>", "{title}", " — 样例验证报告</h1>",
          "<p><b>目的</b>：验证技能目录 <code>01_样例_sample/</code> 可运行，并产出数据/图片/报告。</p>",
          "<p><b>数据来源</b>：内置 toy 表达矩阵（6 样本×40 基因，Case vs Control）；诚实标注为模拟数据。</p>",
          "<p><b>步骤</b>：1) 读取 toy_counts/meta；2) log2(count+1)；3) 基因水平 t 检验；4) PCA 与火山图（DPI=600 PNG）；5) 写 CSV 与本 HTML。</p>",
          "<p><b>关联骨架</b>：", skeleton_note, "</p>",
          pass_note,
          "<h2>主要图表</h2>",
          "<p>PCA</p><img src='", fig_rel1, "' alt='PCA'/>",
          "<p>Volcano</p><img src='", fig_rel2, "' alt='volcano'/>",
          "<h2>结果解读</h2>",
          "<p>Top 基因见 <code>结果文件/数据文件/toy_deg_results.csv</code>。",
          "本报告仅证明流程与出图契约，不可作为发表级生物学结论。</p>",
          "<p>生成时间：", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "</p>",
          "</body></html>"
        )
        writeLines(html, file.path(rep_dir, "样例报告.html"), useBytes = TRUE)

        # machine-readable status
        writeLines(status, file.path(rep_dir, "STATUS.txt"))
        message("DONE ", status, " — ", "{title}")
        """
    )


def prepare_skill(skill_dir: Path) -> dict:
    folder = skill_dir.name
    sample = ensure_tree(skill_dir)
    data_dir = sample / "数据文件"

    # pick toy data flavor
    if folder in BLOCKED_REASON:
        mode = "blocked"
    elif folder in LIGHT_CONTRACT:
        mode = "light"
    else:
        mode = "full"

    if "Survival" in folder or "生存" in folder:
        write_toy_csv(data_dir / "toy_survival.csv", "survival")
    if "16S" in folder or "Microbiome" in folder:
        write_toy_csv(data_dir / "toy_otu.csv", "otu")
    if "甲基化" in folder or "WGBS" in folder:
        write_toy_csv(data_dir / "toy_beta.csv", "beta")
    if "网络药理" in folder or "NetworkPharmacology" in folder:
        write_toy_csv(data_dir / "compound_targets.csv", "network")

    write_toy_csv(data_dir / "toy_counts.csv", "counts")
    write_toy_csv(data_dir / "toy_meta.csv", "meta")
    (data_dir / "DATA_SOURCE.md").write_text(
        "# 数据来源\n\n"
        "- **类型**：可复现 toy / 模拟矩阵\n"
        "- **说明**：用于技能样例契约验证，非真实患者/GEO 原始下载（除非另有复用说明）\n"
        f"- **技能**：`{folder}`\n"
        f"- **模式**：`{mode}`\n",
        encoding="utf-8",
    )

    code = sample / "代码文件" / "run_sample.R"
    code.write_text(r_script_for(skill_dir, folder, mode), encoding="utf-8")
    return {"skill_dir": skill_dir, "folder": folder, "mode": mode, "code": code}


def run_one(prep: dict) -> dict:
    code: Path = prep["code"]
    folder = prep["folder"]
    skill_rel = prep["skill_dir"].relative_to(ROOT).as_posix()
    try:
        proc = subprocess.run(
            ["Rscript", str(code.name)],
            cwd=str(code.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        ok = proc.returncode == 0
        status_file = (
            prep["skill_dir"]
            / "01_样例_sample"
            / "结果文件"
            / "报告文件"
            / "STATUS.txt"
        )
        status = status_file.read_text(encoding="utf-8").strip() if status_file.exists() else (
            "PASS" if ok else "FAIL"
        )
        if not ok and status != "BLOCKED":
            status = "FAIL"
        report = (
            prep["skill_dir"]
            / "01_样例_sample"
            / "结果文件"
            / "报告文件"
            / "样例报告.html"
        )
        return {
            "folder": folder,
            "path": skill_rel,
            "status": status,
            "mode": prep["mode"],
            "report": report.relative_to(ROOT).as_posix() if report.exists() else "",
            "returncode": proc.returncode,
            "stderr": (proc.stderr or "")[-500:],
            "blocked_reason": BLOCKED_REASON.get(folder, ""),
        }
    except Exception as e:
        return {
            "folder": folder,
            "path": skill_rel,
            "status": "FAIL",
            "mode": prep["mode"],
            "report": "",
            "returncode": -1,
            "stderr": str(e),
            "blocked_reason": BLOCKED_REASON.get(folder, ""),
        }


def annotate_skill_doc(skill_dir: Path) -> None:
    docs = list(skill_dir.glob("技能说明_*.md"))
    if not docs:
        return
    doc = docs[0]
    text = doc.read_text(encoding="utf-8")
    marker = "样例：`01_样例_sample/`"
    if marker in text:
        return
    # append near end
    text = text.rstrip() + f"\n\n## 样例验证\n\n{marker}\n"
    doc.write_text(text, encoding="utf-8", newline="\n")


def write_summary(results: list[dict]) -> None:
    VAL_DIR.mkdir(exist_ok=True)
    RESULTS_JSON.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "n": len(results),
                "counts": dict(Counter(r["status"] for r in results)),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# 验证总报告 / Per-Skill Sample Validation",
        "",
        f"- **生成时间**：{datetime.now().isoformat(timespec='seconds')}",
        f"- **布局版本**：见 catalog `layout_version` / [目录重构说明_LayoutMigration.md](../目录重构说明_LayoutMigration.md)",
        f"- **技能样例数**：{len(results)}",
        f"- **PASS**：{sum(1 for r in results if r['status']=='PASS')}",
        f"- **BLOCKED**：{sum(1 for r in results if r['status']=='BLOCKED')}",
        f"- **FAIL**：{sum(1 for r in results if r['status']=='FAIL')}",
        "",
        "## 说明",
        "",
        "- 每个技能目录下 `01_样例_sample/`：`代码文件/` · `数据文件/` · `结果文件/` 同级；禁止结果嵌套在代码内。",
        "- BLOCKED：客观缺 CLI/商业软件/TB 数据；已提供降级契约样例（toy 统计+DPI600 图+HTML）。",
        "- 机器可读：`每技能样例_results.json`",
        "",
        "## 每技能样例总表",
        "",
        "| 技能 | 状态 | 报告路径 |",
        "|------|------|----------|",
    ]
    for r in sorted(results, key=lambda x: x["path"]):
        rep = r["report"] or "—"
        note = f" （{r['blocked_reason']}）" if r["status"] == "BLOCKED" and r.get("blocked_reason") else ""
        lines.append(f"| `{r['path']}` | **{r['status']}**{note} | `{rep}` |")

    fails = [r for r in results if r["status"] == "FAIL"]
    lines += ["", "## FAIL 明细", ""]
    if not fails:
        lines.append("无。")
    else:
        for r in fails:
            lines.append(f"- `{r['path']}`: `{r.get('stderr','')[:200]}`")

    lines += [
        "",
        "## 如何跑某一个样例",
        "",
        "```bash",
        "cd \"E:/RProject/生信分析技能_BioinformaticsSkills/<顶层>/<技能目录>/01_样例_sample/代码文件\"",
        "Rscript run_sample.R",
        "```",
        "",
        "## 历史分类验证（八条）",
        "",
        "原八条分类验证记录仍保留在 `验证记录_records/`，见本目录既有说明。",
        "",
    ]
    (VAL_DIR / "验证总报告.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    print("REFUSED: _phaseB_sample_batch.py 会生成全技能同构 volcano/PCA（已审计不合规）。")
    print("请改用: python _phaseC_delivery_rerun.py")
    print("规范: 00_基础_Foundation/统一交付规范_DeliveryStandards/")
    raise SystemExit(2)



if __name__ == "__main__":
    main()
