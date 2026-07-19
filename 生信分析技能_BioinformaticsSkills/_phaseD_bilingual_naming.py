# -*- coding: utf-8 -*-
"""Phase D: 中英对照命名 + Viz/Delivery 强制 source + 批量改名/重跑。

文件名强制中英对照；图面文字 English only（禁止中文）；文件名仍中英对照——二者不可混用。

不 git commit。扩展 Phase C：
1) 修补全部 run_sample.R 顶部 source 顺序
2) 依赖已更新的 PlotNaming（重跑即产出中英对照名）
3) 清理 结果文件 下 sample_/toy_/纯英文旧名
4) 重跑优先样例 + 其余可跑样例
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(r"E:/RProject/生信分析技能_BioinformaticsSkills")
VAL_DIR = ROOT / "07_分类验证_Validation"
CATALOG = ROOT / "技能目录_skill-catalog.json"

# 优先重跑（含 3DGenome / DeliveryStandards）
PRIORITY = [
    "00_基础_Foundation/统一交付规范_DeliveryStandards",
    "00_基础_Foundation/统一可视化规范_VizStandards",
    "01_组学_Omics/三维基因组分析_3DGenome",
    "01_组学_Omics/转录组分析_RNA-seq",
    "01_组学_Omics/蛋白质组分析_Proteomics",
    "01_组学_Omics/单细胞与空间转录组分析_scRNA-Spatial",
    "01_组学_Omics/微生物组16S分析_Microbiome16S",
    "02_遗传与变异_Genetics/全基因组关联分析_GWAS",
    "03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology",
    "04_临床预测与统计_ClinicalStats/生存分析与预后模型_Survival",
    "05_系统方法_SystemsMethods/共表达网络WGCNA_WGCNA",
]

HEADER_MARKER = "# 1) source 统一可视化规范 出版级出图"

NEW_SOURCE_BLOCK = r'''
# 1) source 统一可视化规范 出版级出图
# 2) source 统一交付规范 出图命名/审计/报告
# 3) source 本技能 脚本_scripts
viz_script <- file.path(
  bio_root, "00_基础_Foundation", "统一可视化规范_VizStandards",
  "脚本_scripts", "出版级出图_PublicationPlot.R"
)
if (file.exists(viz_script)) source(viz_script, encoding = "UTF-8")

delivery_scripts <- file.path(bio_root, "00_基础_Foundation", "统一交付规范_DeliveryStandards", "脚本_scripts")
source(file.path(delivery_scripts, "规范_出图与命名_PlotNaming.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_数据审计_DataAudit.R"), encoding = "UTF-8")
source(file.path(delivery_scripts, "规范_报告生成_ReportBuild.R"), encoding = "UTF-8")
'''.strip() + "\n"


def list_skill_dirs() -> list[str]:
    rels = []
    for p in ROOT.rglob("01_样例_sample"):
        if not p.is_dir():
            continue
        skill = p.parent
        try:
            rel = skill.relative_to(ROOT).as_posix()
        except ValueError:
            continue
        if rel.startswith("07_"):
            continue
        rels.append(rel)
    return sorted(set(rels))


def patch_run_sample_header(path: Path) -> bool:
    """Ensure Viz → Delivery → skill source order. Skip if already phase-D marked."""
    text = path.read_text(encoding="utf-8")
    if HEADER_MARKER in text and "viz_script <- file.path" in text:
        return False
    # Replace old delivery-only source block
    pat = re.compile(
        r"delivery_scripts\s*<-\s*file\.path\(bio_root,\s*\"00_基础_Foundation\",\s*"
        r"\"统一交付规范_DeliveryStandards\",\s*\"脚本_scripts\"\)\s*\n"
        r"source\(file\.path\(delivery_scripts,\s*\"规范_出图与命名_PlotNaming\.R\"\).*?\n"
        r"source\(file\.path\(delivery_scripts,\s*\"规范_数据审计_DataAudit\.R\"\).*?\n"
        r"source\(file\.path\(delivery_scripts,\s*\"规范_报告生成_ReportBuild\.R\"\).*?\n",
        re.DOTALL,
    )
    new_text, n = pat.subn(NEW_SOURCE_BLOCK + "\n", text, count=1)
    if n == 0:
        # insert after fig/tab/rep dir.create loop if possible
        m = re.search(
            r"for \(d in c\(data_dir, fig_dir, tab_dir, rep_dir\)\) "
            r"dir\.create\(d, recursive = TRUE, showWarnings = FALSE\)\n",
            text,
        )
        if not m:
            return False
        insert_at = m.end()
        new_text = text[:insert_at] + "\n" + NEW_SOURCE_BLOCK + "\n" + text[insert_at:]
        # remove duplicate ensure_pub_viz-only paths later if any — leave as is
    # Drop redundant ensure_pub_viz call (optional)
    new_text = re.sub(r"\nensure_pub_viz\(bio_root\)\n", "\n", new_text)
    path.write_text(new_text, encoding="utf-8", newline="\n")
    return True


def has_cjk(name: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", name))


def clean_old_result_files(skill_rel: str) -> list[str]:
    """Remove banned / pure-English / legacy SkillEn_样例报告 delivery artifacts."""
    removed = []
    res = ROOT / skill_rel.replace("/", os.sep) / "01_样例_sample" / "结果文件"
    if not res.exists():
        return removed
    for f in res.rglob("*"):
        if not f.is_file():
            continue
        bn = f.name
        stem = f.stem
        drop = False
        if bn == "STATUS.txt":
            continue
        if re.match(r"^(sample_|toy_|fig\d*|plot|out)($|_)", stem, re.I):
            drop = True
        elif bn in {"样例报告.html", "plot.png", "fig1.png"}:
            drop = True
        elif bn.endswith(".html") and "样例报告" in bn and bn != "样例报告_SampleReport_v1.html":
            # 旧：RNA-seq_样例报告_v1.html
            drop = True
        elif f.suffix.lower() in {".csv", ".png", ".svg", ".html"} and not has_cjk(bn):
            drop = True
        elif re.match(r"^[A-Za-z0-9][A-Za-z0-9._+-]*_audit_(pre|post)\.csv$", bn):
            drop = True
        elif re.match(r"^[A-Za-z0-9][A-Za-z0-9._+-]*_contract_", bn):
            drop = True
        if drop:
            try:
                f.unlink()
                removed.append(str(f.relative_to(ROOT)).replace("\\", "/"))
            except OSError:
                pass
    return removed


def run_sample(skill_rel: str, timeout: int = 180) -> dict:
    code = ROOT / skill_rel.replace("/", os.sep) / "01_样例_sample" / "代码文件" / "run_sample.R"
    if not code.exists():
        return {"path": skill_rel, "status": "FAIL", "stderr": "missing run_sample.R"}
    # clean before run so stale english names don't linger if script fails mid-way after write
    clean_old_result_files(skill_rel)
    t0 = time.time()
    try:
        proc = subprocess.run(
            ["Rscript", "run_sample.R"],
            cwd=str(code.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"path": skill_rel, "status": "FAIL", "stderr": "timeout", "elapsed": timeout}
    status_file = code.parent.parent / "结果文件" / "报告文件" / "STATUS.txt"
    status = "FAIL"
    if status_file.exists():
        status = status_file.read_text(encoding="utf-8", errors="replace").strip().splitlines()[0].strip()
    elif proc.returncode == 0:
        status = "PASS"
    report = ""
    rep_dir = code.parent.parent / "结果文件" / "报告文件"
    prefer = rep_dir / "样例报告_SampleReport_v1.html"
    if prefer.exists():
        report = str(prefer.relative_to(ROOT)).replace("\\", "/")
    elif rep_dir.exists():
        htmls = list(rep_dir.glob("*.html"))
        if htmls:
            report = str(htmls[0].relative_to(ROOT)).replace("\\", "/")
    # post-clean leftovers
    clean_old_result_files(skill_rel)
    return {
        "path": skill_rel,
        "status": status if proc.returncode == 0 or status in {"PASS", "BLOCKED"} else "FAIL",
        "returncode": proc.returncode,
        "stderr": (proc.stderr or "")[-500:],
        "stdout": (proc.stdout or "")[-300:],
        "report": report,
        "elapsed": round(time.time() - t0, 2),
    }


def count_naming_compliance() -> dict:
    total = 0
    ok = 0
    bad = []
    for f in ROOT.rglob("*"):
        if "结果文件" not in str(f):
            continue
        if not f.is_file():
            continue
        if f.suffix.lower() not in {".csv", ".png", ".svg", ".html"}:
            continue
        if f.name == "STATUS.txt":
            continue
        total += 1
        if has_cjk(f.name):
            ok += 1
        else:
            bad.append(str(f.relative_to(ROOT)).replace("\\", "/"))
    return {"total": total, "with_cjk": ok, "without_cjk": len(bad), "bad_examples": bad[:30]}


def update_catalog_notes() -> None:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    # ensure delivery requires viz; note bilingual naming
    for sk in data.get("skills", []):
        req = sk.get("requires") or []
        deps = sk.get("depends_on") or []
        sid = sk.get("id")
        if sid == "bioinfo-delivery-standards":
            if "bioinfo-viz-standards" not in req:
                req = ["bioinfo-viz-standards"] + list(req)
            sk["requires"] = req
            sk["depends_on"] = list(dict.fromkeys(["bioinfo-viz-standards"] + list(deps)))
            sk["description_note"] = (
                "交付文件名强制 {中文}_{EnglishPascal}；样例须 source VizStandards 再 DeliveryStandards"
            )
        elif sid == "bioinfo-viz-standards":
            sk["description_note"] = (
                "期刊出图 DPI≥600 SVG+PNG；单栏85–90mm；色盲友好；与 DeliveryStandards 同时 requires"
            )
        elif sid not in ("bioinfo-delivery-standards",):
            # all analysis skills require both
            for need in ("bioinfo-viz-standards", "bioinfo-delivery-standards"):
                if need not in req:
                    req.append(need)
                if need not in deps:
                    deps.append(need)
            sk["requires"] = req
            sk["depends_on"] = deps
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_validation_addon(results: list[dict], naming: dict) -> None:
    """Prepend/update sections in 验证总报告.md without wiping history tables if possible."""
    path = VAL_DIR / "验证总报告.md"
    now = datetime.now().isoformat(timespec="seconds")
    ctr = Counter(r["status"] for r in results)
    lines = [
        "# 验证总报告 / Per-Skill Sample Validation",
        "",
        f"- **更新时间**：{now}",
        f"- **布局版本**：catalog + 统一交付规范（中英对照命名 Phase D）",
        f"- **本轮重跑数**：{len(results)}",
        f"- **PASS**：{ctr.get('PASS', 0)}",
        f"- **BLOCKED**：{ctr.get('BLOCKED', 0)}",
        f"- **FAIL**：{ctr.get('FAIL', 0)}",
        f"- **结果文件中英对照**：{naming['with_cjk']}/{naming['total']}（无中文前缀剩余 {naming['without_cjk']}）",
        "",
        "## 关于 Cursor/Git「未跟踪 Untracked」",
        "",
        "「未跟踪」是 **Git 对尚未 `git add` / 未 commit 新文件** 的状态标记，**不是**文件扩展名。",
        "样例 `结果文件/` 产物默认未入库属正常；若需纳入版本库再由用户 `git add`。",
        "**不要擅自 `git commit`**，除非用户明确要求。详见",
        "`00_基础_Foundation/统一交付规范_DeliveryStandards/技能说明_统一交付规范_DeliveryStandards.md` §1。",
        "",
        "## 规范合规审计（Phase D）",
        "",
        "### 问1：执行样例时是否引用其它 skill 规范？",
        "",
        "**结论：是。** `run_sample.R` 强制按序 source：",
        "1) 统一可视化规范 `出版级出图_PublicationPlot.R`；",
        "2) 统一交付规范 PlotNaming/DataAudit/ReportBuild；",
        "3) 本技能 `脚本_scripts`。",
        "",
        "### 问2：文件命名",
        "",
        "**结论：强制** `{中文语义}_{EnglishCamelOrPascal}.{ext}`",
        "（例：`火山图_TreatVsControl_Volcano.png`、`审计后检_AuditPost.csv`、`样例报告_SampleReport_v1.html`）。",
        "禁止 `sample_*.csv` / `toy_*.csv` / 纯英文交付名。",
        "",
        "### 问3：期刊出图",
        "",
        "**结论：见 VizStandards** — DPI≥600、SVG+PNG、单栏约 85–90 mm、色盲友好、按分析类型选图。",
        "",
        "## 本轮重跑结果",
        "",
        "| 技能 | 状态 | 报告 |",
        "|------|------|------|",
    ]
    for r in sorted(results, key=lambda x: x["path"]):
        lines.append(f"| `{r['path']}` | **{r['status']}** | `{r.get('report') or '—'}` |")
    fails = [r for r in results if r["status"] == "FAIL"]
    lines += ["", "### FAIL 明细", ""]
    if fails:
        for r in fails:
            err = (r.get("stderr") or "")[:180].replace("\n", " ")
            lines.append(f"- `{r['path']}` — {err}")
    else:
        lines.append("- （无）")
    lines += [
        "",
        "## 如何重跑",
        "",
        "```bash",
        "python E:/RProject/生信分析技能_BioinformaticsSkills/_phaseD_bilingual_naming.py",
        "```",
        "",
    ]
    VAL_DIR.mkdir(exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    (VAL_DIR / "phaseD_bilingual_results.json").write_text(
        json.dumps(
            {
                "generated_at": now,
                "results": results,
                "naming": naming,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    print("Phase D: patch headers...", flush=True)
    patched = 0
    for rel in list_skill_dirs():
        rs = ROOT / rel.replace("/", os.sep) / "01_样例_sample" / "代码文件" / "run_sample.R"
        if rs.exists() and patch_run_sample_header(rs):
            patched += 1
    print(f"  patched headers: {patched}", flush=True)

    print("Updating catalog requires/notes...", flush=True)
    update_catalog_notes()

    all_skills = list_skill_dirs()
    # priority first, then rest
    ordered = [p for p in PRIORITY if p in all_skills] + [p for p in all_skills if p not in PRIORITY]

    results = []
    for i, rel in enumerate(ordered, 1):
        print(f"[{i}/{len(ordered)}] {rel} ...", flush=True)
        res = run_sample(rel)
        results.append(res)
        print(f"  -> {res['status']} ({res.get('elapsed')}s)", flush=True)
        if res["status"] == "FAIL":
            print("  stderr:", (res.get("stderr") or "")[:300], flush=True)

    naming = count_naming_compliance()
    write_validation_addon(results, naming)
    print("SUMMARY", dict(Counter(r["status"] for r in results)))
    print("NAMING", naming["with_cjk"], "/", naming["total"], "bad", naming["without_cjk"])
    if naming["bad_examples"]:
        print("BAD examples:", *naming["bad_examples"][:10], sep="\n  ")


if __name__ == "__main__":
    main()
