# -*- coding: utf-8 -*-
"""努力学习：按新存放规范重组数据目录。

目标树（每个 0N 模块）:
  数据文件/
    原始数据/     # 外部库/数据库抓取，目录名含来源
    结果数据/     # 原 结果文件/数据文件/
  结果文件/
    图片文件/
    报告文件/
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(r"E:/RProject") / "努力学习项目"
DRY = False  # set True to preview


def ensure(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p


def move_merge(src: Path, dst: Path) -> list[str]:
    logs: list[str] = []
    if not src.exists():
        return logs
    ensure(dst.parent)
    if src.is_file():
        ensure(dst.parent)
        if dst.exists():
            logs.append(f"SKIP exists {dst}")
            return logs
        if not DRY:
            shutil.move(str(src), str(dst))
        logs.append(f"MOVE file {src} -> {dst}")
        return logs
    ensure(dst)
    for child in list(src.iterdir()):
        target = dst / child.name
        if child.is_dir():
            logs.extend(move_merge(child, target))
        else:
            if target.exists():
                logs.append(f"SKIP exists {target}")
            else:
                if not DRY:
                    ensure(target.parent)
                    shutil.move(str(child), str(target))
                logs.append(f"MOVE file {child} -> {target}")
    # remove empty src dirs
    if not DRY and src.is_dir():
        try:
            next(src.iterdir())
        except StopIteration:
            src.rmdir()
            logs.append(f"RMDIR {src}")
    return logs


def write_readme(path: Path, text: str) -> None:
    ensure(path.parent)
    if not DRY:
        path.write_text(text, encoding="utf-8")


def reorg_module(mod: Path) -> list[str]:
    logs = [f"=== {mod.name} ==="]
    data = ensure(mod / "数据文件")
    raw = ensure(data / "原始数据")
    result_data = ensure(data / "结果数据")
    res = ensure(mod / "结果文件")
    ensure(res / "图片文件")
    ensure(res / "报告文件")

    # 1) 结果文件/数据文件 -> 数据文件/结果数据
    old_res_data = res / "数据文件"
    if old_res_data.exists():
        logs.extend(move_merge(old_res_data, result_data))

    # 2) 数据文件下除 原始/结果 外的内容 -> 原始数据（保留语义名，再规范重命名）
    for child in list(data.iterdir()):
        if child.name in {"原始数据", "结果数据"}:
            continue
        # special remap names to include source
        new_name = rename_raw(mod.name, child.name)
        logs.extend(move_merge(child, raw / new_name))

    return logs


def rename_raw(mod_name: str, name: str) -> str:
    """给原始数据目录加上来源前缀（已有来源则不重复）。"""
    mapping = {
        "SEA原始": "SEA数据库_SEA原始",
        "SEA16原始": "SEA数据库_SEA16原始",
        "STP原始": "SwissTargetPrediction_STP原始",
        "外部数据库": "外部数据库_多源",
        "对接工作区": "RCSB与PubChem_对接结构工作区",
        "_手调detail备份": "课题产物_手调detail备份",
        "MD输入_Top3": "RCSB与对接姿态_MD输入_Top3",
        "MD环境": "工具链残留_MD环境_应使用E盘md_kit",
        "MD输入": "课题产物_MD输入",
    }
    if name in mapping:
        return mapping[name]
    # already looks sourced
    if any(k in name for k in ("GEO", "CTD", "PubChem", "RCSB", "PDB", "GWAS", "GTEx", "gutMGene", "GMMAD", "SEA", "Swiss", "OpenTargets")):
        return name
    return f"待标注来源_{name}"


def recover_missing_raw() -> list[str]:
    """从 03 外部库 / 交付 / 对接库 回填缺失原始数据。"""
    logs: list[str] = []
    m03 = next(ROOT.glob("03_*"))
    src_ext = m03 / "数据文件" / "原始数据" / "外部数据库_多源"
    if not src_ext.is_dir():
        # maybe not yet moved
        src_ext = m03 / "数据文件" / "外部数据库"

    # 07 needs GEO/GWAS
    m07 = next(ROOT.glob("07_*"))
    raw07 = ensure(m07 / "数据文件" / "原始数据")
    for db in ("GEO", "GWAS"):
        src = src_ext / db if src_ext.is_dir() else None
        dst = raw07 / f"{db}数据库_{db}"
        if src and src.is_dir() and not dst.exists():
            if not DRY:
                shutil.copytree(src, dst)
            logs.append(f"COPY {src} -> {dst}")
        elif not (src and src.is_dir()):
            write_readme(
                raw07 / f"README_{db}_来源指针.md",
                f"# {db} 原始数据来源\n\n本模块分析读自 `03_三源交集_复方UC菌群/数据文件/原始数据/外部数据库_多源/{db}/`。\n"
                f"若需本地副本，从该路径复制到本目录 `{db}数据库_{db}/`。\n",
            )
            logs.append(f"POINTER {m07.name}/{db}")

    # 01/02/04/05: pointer to upstream result/raw
    pointers = {
        "01_": (
            "README_原始数据来源.md",
            "# 01 网络药理学 · 原始数据来源\n\n"
            "- 疾病基因 / 成分靶点策展边：见 `03_三源交集_复方UC菌群/数据文件/原始数据/外部数据库_多源/`（CTD、OpenTargets 等）与 `…/SwissTargetPrediction_STP原始/`、`…/SEA数据库_*`。\n"
            "- 本模块产物表在 `数据文件/结果数据/`（由原 `结果文件/数据文件` 迁入）。\n",
        ),
        "02_": (
            "README_原始数据来源.md",
            "# 02 网络毒理学 · 原始数据来源\n\n"
            "- 有害暴露物 / CTD 毒性注释：`03_…/数据文件/原始数据/外部数据库_多源/CTD/`。\n"
            "- 分层输入表来自 `03_…/数据文件/结果数据/` 交集产物。\n",
        ),
        "04_": (
            "README_原始数据来源.md",
            "# 04 机制层 · 原始数据来源\n\n"
            "- PPI/富集输入基因列表：`03_…/数据文件/结果数据/`（C / hub 列表）。\n"
            "- STRING / 富集库调用记录见本模块 `数据文件/结果数据/机制层/`。\n",
        ),
        "05_": (
            "README_原始数据来源.md",
            "# 05 干预代谢物预测 · 原始数据来源\n\n"
            "- 代谢物面板与靶点：`03_…/数据文件/结果数据/代谢物/` 与原始 `SEA/STP`。\n",
        ),
    }
    for prefix, (fname, text) in pointers.items():
        mod = next(ROOT.glob(f"{prefix}*"))
        raw = ensure(mod / "数据文件" / "原始数据")
        # if raw has only readmes / empty of real data, write pointer
        real_files = [p for p in raw.rglob("*") if p.is_file() and p.suffix.lower() != ".md"]
        if not real_files:
            write_readme(raw / fname, text)
            logs.append(f"POINTER {mod.name}")

    # 06: provenance readme for docking structures + copy PDB/CID from library if workspace thin
    m06 = next(ROOT.glob("06_*"))
    raw06 = ensure(m06 / "数据文件" / "原始数据")
    write_readme(
        raw06 / "README_结构来源.md",
        "# 06 分子对接 · 原始结构来源\n\n"
        "| 类型 | 来源数据库 | 本目录位置 |\n"
        "|------|------------|------------|\n"
        "| 受体 PDB/AlphaFold | RCSB PDB / AlphaFold DB | `RCSB与PubChem_对接结构工作区/` 与本地库 `D:/数据库/分子对接数据库/` |\n"
        "| 配体 | PubChem CID | 同上 `small*`；对接姿态来自 AutoDock-GPU 输出 |\n"
        "| MD Top3 初态 | RCSB + 对接 pose | 见 `08_分子动力学/数据文件/原始数据/RCSB与对接姿态_MD输入_Top3/` |\n",
    )
    logs.append("README 06 provenance")

    # 08: MD Top3 provenance + remove misleading MD环境 if it's empty/kit leftover
    m08 = next(ROOT.glob("08_*"))
    raw08 = ensure(m08 / "数据文件" / "原始数据")
    top3 = raw08 / "RCSB与对接姿态_MD输入_Top3"
    if not top3.is_dir():
        alt = m08 / "数据文件" / "MD输入_Top3"
        if alt.is_dir():
            logs.extend(move_merge(alt, top3))
    write_readme(
        raw08 / "README_MD输入来源.md",
        "# 08 分子动力学 · 原始输入来源\n\n"
        "| 体系 | 受体来源 | 配体来源 |\n"
        "|------|----------|----------|\n"
        "| ESR2_Anhydroicaritin_1L2J | RCSB **1L2J** | PubChem / 对接最佳姿态 |\n"
        "| FOS_quercetin_1A02 | RCSB **1A02** | PubChem CID 5280343 / 对接姿态 |\n"
        "| PPARG_kaempferol_1FM9 | RCSB **1FM9** | PubChem CID 5280863 / 对接姿态 |\n\n"
        "生产轨迹工作目录在 WSL `~/md_runs/<体系>/`（大文件不进课题树）；"
        "分析表同步到 `数据文件/结果数据/分子动力学_MD/`。\n"
        "GROMACS/AmberTools 安装包不在本夹，见 `E:/md_kit`。\n",
    )
    # MD环境: if only leftover, move aside
    env = raw08 / "工具链残留_MD环境_应使用E盘md_kit"
    if env.is_dir():
        write_readme(
            env / "README_勿在此安装.md",
            "此目录不应存放 MD 安装包。请使用 `E:/md_kit`（技能 `环境安装_EnvSetup`）。\n",
        )
        logs.append("NOTE MD环境 leftover documented")

    # pull MD result tables from ~/md_runs if any exported under Windows path
    res08 = ensure(m08 / "数据文件" / "结果数据" / "分子动力学_MD")
    wsl_hint = Path(r"\\wsl$\Ubuntu-24.04\home\ywy\md_runs")
    # Also check delivery mirror
    deliv = ROOT / "交付文件" / m08.name / "数据文件"
    if deliv.is_dir() and not any(res08.rglob("*.csv")):
        for p in deliv.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".csv", ".xvg", ".dat", ".md"}:
                rel = p.relative_to(deliv)
                dst = res08 / rel
                if not dst.exists():
                    if not DRY:
                        ensure(dst.parent)
                        shutil.copy2(p, dst)
                    logs.append(f"COPY delivery {p} -> {dst}")

    return logs


def update_layout_doc() -> None:
    text = """# 努力学习项目 · 存放规范

> 对齐统一交付规范。更新日期：2026-10-13（**数据文件内分原始/结果**；结果文件只放图与报告）

## 1. 顶层角色

课题规范名：**三源共有靶点整合网络药理学（毒性分层）**。网络毒理学不是父项目名。

| 路径 | 角色 |
|------|------|
| `00_全流程报告/` | 全项目论文版 + 方法版（与 01 同级） |
| `01_网络药理学/` … `08_分子动力学/` | 分模块工作树 |
| `交付文件/` | 轨 B：与上表同样编号镜像 |

## 2. 每个编号模块的子文件夹（敲定 · 2026-10-13）

```text
0N_模块名/
  README_模块说明.md
  代码文件/                      # 仅脚本
  数据文件/                      # 与代码文件同级
    原始数据/                    # 外部库抓取；目录名必须带来源库
    结果数据/                    # 本模块分析产物表（原 结果文件/数据文件）
  结果文件/
    图片文件/                    # 产物图
    报告文件/                    # 本模块阶段/方法报告
```

### 2.1 原始数据命名（强制）

目录名格式：`{来源数据库}_{内容简述}`  

示例：

| 目录名 | 含义 |
|--------|------|
| `SEA数据库_SEA原始/` | SEA 批量预测原始 JSON |
| `SwissTargetPrediction_STP原始/` | STP 导出 CSV |
| `外部数据库_多源/CTD/` | CTD 化学–基因 |
| `外部数据库_多源/GEO/` | GEO 系列 |
| `RCSB与PubChem_对接结构工作区/` | 对接用受体/配体结构 |
| `RCSB与对接姿态_MD输入_Top3/` | MD 初态（PDB ID 写在体系名或 README） |

禁止只写 `数据/`、`raw/`、无来源的 `输入/`。  
若本模块不直接抓库、只消费上游结果：在 `原始数据/README_原始数据来源.md` 写清指针（指到 `03_…/数据文件/…`），并尽量把关键小表复制一份到本夹。

### 2.2 结果数据 vs 结果文件

| 放哪里 | 放什么 |
|--------|--------|
| `数据文件/结果数据/` | CSV/TSV/JSON 等**表型产物** |
| `结果文件/图片文件/` | PNG/SVG 等图 |
| `结果文件/报告文件/` | md/HTML 报告 |

**禁止**再使用 `结果文件/数据文件/`（已废止；内容迁入 `数据文件/结果数据/`）。

## 3. `00_全流程报告/` 内容

```text
00_全流程报告/
  README_模块说明.md
  代码文件/                    # 可选：拼装全流程 HTML 的脚本
  数据文件/
    原始数据/                  # 通常为空或指针
    结果数据/                  # 全流程汇总表（若有）
  结果文件/
    报告文件/
      打开全流程.html
      论文版_全流程.html
      方法版_全流程.html
    图片文件/                  # 全流程 HTML 自用图副本
```

## 4. 编号清单

| 编号 | 目录 | 放什么 |
|------|------|--------|
| 00 | 全流程报告 | 全项目论文版/方法版 |
| 01 | 网络药理学 | F、I₁、网药图 |
| 02 | 网络毒理学_毒性分层 | 有害暴露物支线 |
| 03 | 三源交集_复方UC菌群 | I₁/I₂/C、置换、研究计划、主代码 |
| 04 | 机制层_PPI富集 | PPI/GO/KEGG |
| 05 | 干预代谢物预测 | Tier A 等 |
| 06 | 分子对接 | 对接表与热图 |
| 07 | 外部支持_GEO与MR | GEO/MR |
| 08 | 分子动力学 | 100 ns 轨迹图与表 |

## 5. 轨 B

`交付文件/` 下同样 `00`–`08`。客户包内仍可用扁平 `数据文件/`（表）+ `图片文件/` + `报告文件/`；工作树必须遵守 §2。

## 6. 脚本路径约定

- 读原始：`ROOT/数据文件/原始数据/...`
- 写表：`ROOT/数据文件/结果数据/...`
- 写图/报告：`ROOT/结果文件/{图片文件,报告文件}/...`

旧路径 `结果文件/数据文件` 已废止；改脚本时一并替换。
"""
    path = ROOT / "存放规范_ProjectLayout.md"
    if not DRY:
        path.write_text(text, encoding="utf-8")


def main() -> int:
    all_logs: list[str] = []
    update_layout_doc()
    all_logs.append("updated 存放规范_ProjectLayout.md")

    for mod in sorted([p for p in ROOT.iterdir() if p.is_dir() and p.name[:2].isdigit()]):
        all_logs.extend(reorg_module(mod))

    all_logs.extend(recover_missing_raw())

    # note in 说明
    note = ROOT / "说明_目录编号与层级_2026-10-11.md"
    if note.exists() and not DRY:
        extra = (
            "\n\n## 2026-10-13 修订\n\n"
            "- `数据文件/` 内分 `原始数据/`（带来源库名）与 `结果数据/`。\n"
            "- `结果文件/` **只**保留 `图片文件/` + `报告文件/`（废止 `结果文件/数据文件/`）。\n"
            "- 详见 `存放规范_ProjectLayout.md` §2。\n"
        )
        t = note.read_text(encoding="utf-8")
        if "2026-10-13 修订" not in t:
            note.write_text(t + extra, encoding="utf-8")

    out = Path(r"E:/RProject/_tmp_nuli_reorg_log.txt")
    out.write_text("\n".join(all_logs), encoding="utf-8")
    print(f"log={out} lines={len(all_logs)} dry={DRY}")
    # summary counts
    summary = {}
    for mod in sorted([p for p in ROOT.iterdir() if p.is_dir() and p.name[:2].isdigit()]):
        raw = mod / "数据文件" / "原始数据"
        rd = mod / "数据文件" / "结果数据"
        old = mod / "结果文件" / "数据文件"
        summary[mod.name] = {
            "raw_files": sum(1 for p in raw.rglob("*") if p.is_file()) if raw.is_dir() else 0,
            "result_data_files": sum(1 for p in rd.rglob("*") if p.is_file()) if rd.is_dir() else 0,
            "old_res_data_exists": old.exists(),
        }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
