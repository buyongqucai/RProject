# -*- coding: utf-8 -*-
"""把 MD 样例工作目录 / 结果图按 DeliveryStandards 分类并中英对照命名。

GROMACS 运行时仍可用扁平英文名（工具强制：topol.top、md.tpr、-deffnm）。
样例归档与读入脚本走本布局。跑完 MD 后执行：

  python 整理样例目录_layoutMdSample.py

可重复执行（已在目标位置则跳过）。
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SAMPLE = SKILL / "01_样例_sample"
WORK_DIRNAME = "工作文件_MdWork"
WORK_DIRNAME_OLD = "工作文件_mdwork"

# 流水线顺序：文件夹 = {NN}_{中文}_{English}
STAGES: dict[str, str] = {
    "input": "01_输入结构_Input",
    "topo": "02_拓扑_Topology",
    "solv": "03_溶剂化离子_Solvation",
    "em": "04_最小化_EnergyMin",
    "nvt": "05_NVT平衡_Nvt",
    "npt": "06_NPT平衡_Npt",
    "prod": "07_生产轨迹_Production",
    "anal": "08_轨迹分析_Analysis",
    "mmpbsa": "09_结合自由能_MmGbsa",
    "snap": "10_轨迹快照_Snapshots",
    "logs": "99_运行日志_Logs",
}

# 引擎文件保持 GROMACS 原名（#include / -deffnm）；只搬家
ENGINE_MOVES: list[tuple[str, str]] = [
    ("topo", "protein.gro"),
    ("topo", "complex.gro"),
    ("topo", "topol.top"),
    ("topo", "posre.itp"),
    ("solv", "newbox.gro"),
    ("solv", "solv.gro"),
    ("solv", "solv_ions.gro"),
    ("solv", "ions.tpr"),
    ("em", "em.tpr"),
    ("em", "em.gro"),
    ("em", "em.edr"),
    ("em", "em.trr"),
    ("em", "em.cpt"),
    ("nvt", "nvt.tpr"),
    ("nvt", "nvt.gro"),
    ("nvt", "nvt.edr"),
    ("nvt", "nvt.trr"),
    ("nvt", "nvt.cpt"),
    ("nvt", "run_nvt.mdp"),
    ("npt", "npt.tpr"),
    ("npt", "npt.gro"),
    ("npt", "npt.edr"),
    ("npt", "npt.trr"),
    ("npt", "npt.cpt"),
    ("npt", "run_npt.mdp"),
    ("prod", "md.tpr"),
    ("prod", "md.xtc"),
    ("prod", "md_center.xtc"),
    ("prod", "md.gro"),
    ("prod", "md.edr"),
    ("prod", "md.cpt"),
    ("prod", "run_md.mdp"),
    ("anal", "index_analysis.ndx"),
    ("mmpbsa", "index.ndx"),
    ("mmpbsa", "mmpbsa.in"),
    ("mmpbsa", "RESULTS_gmx_MMPBSA.h5"),
]

# 输入与分析产物：中英对照文件名
RENAME_MOVES: list[tuple[str, str, str]] = [
    ("input", "protein.pdb", "蛋白_protein.pdb"),
    ("input", "jz4.pdb", "配体_jz4.pdb"),
    ("input", "jz4_h.mol2", "配体加氢_jz4_h.mol2"),
    ("anal", "rmsd_backbone.xvg", "骨架RMSD_RmsdBackbone.xvg"),
    ("anal", "rmsd_protein.xvg", "蛋白RMSD_RmsdProtein.xvg"),
    ("anal", "rmsd_ligand.xvg", "配体RMSD_RmsdLigand.xvg"),
    ("anal", "rmsd_complex.xvg", "复合物RMSD_RmsdComplex.xvg"),
    ("anal", "rmsf_calpha.xvg", "残基RMSF_RmsfCalpha.xvg"),
    ("anal", "hbond_num.xvg", "氢键数_HbondNum.xvg"),
    ("anal", "gyrate.xvg", "回旋半径_RadiusGyration.xvg"),
    ("anal", "sasa.xvg", "溶剂可及表面积_Sasa.xvg"),
    ("anal", "com_distance.xvg", "质心距离_ComDistance.xvg"),
    ("anal", "energy_nvt_temp.xvg", "NVT温度_NvtTemperature.xvg"),
    ("anal", "energy_npt_temp.xvg", "NPT温度_NptTemperature.xvg"),
    ("anal", "energy_npt_press.xvg", "NPT压力_NptPressure.xvg"),
    ("anal", "energy_npt_dens.xvg", "NPT密度_NptDensity.xvg"),
    ("anal", "energy_md_temp.xvg", "生产温度_MdTemperature.xvg"),
    ("anal", "energy_md_potential.xvg", "生产势能_MdPotential.xvg"),
    ("mmpbsa", "FINAL_RESULTS_MMPBSA.dat", "结合能结果_FinalResultsMmpbsa.dat"),
    ("mmpbsa", "FINAL_DECOMP_MMPBSA.dat", "残基分解_FinalDecompMmpbsa.dat"),
    ("snap", "snapshot_start.pdb", "轨迹快照始_SnapshotStart.pdb"),
    ("snap", "snapshot_mid.pdb", "轨迹快照中_SnapshotMid.pdb"),
    ("snap", "snapshot_end.pdb", "轨迹快照末_SnapshotEnd.pdb"),
    ("snap", "snapshot_start_dry.pdb", "轨迹快照始干_SnapshotStartDry.pdb"),
    ("snap", "snapshot_mid_dry.pdb", "轨迹快照中干_SnapshotMidDry.pdb"),
    ("snap", "snapshot_end_dry.pdb", "轨迹快照末干_SnapshotEndDry.pdb"),
]

# 读脚本：英文原名 → 归档名（同目录 08/09/10）
XVG_ARCHIVE = {src: dst for _st, src, dst in RENAME_MOVES if src.endswith(".xvg")}
MMPBSA_ARCHIVE = {
    "FINAL_RESULTS_MMPBSA.dat": "结合能结果_FinalResultsMmpbsa.dat",
    "FINAL_DECOMP_MMPBSA.dat": "残基分解_FinalDecompMmpbsa.dat",
}
SNAP_ARCHIVE = {src: dst for _st, src, dst in RENAME_MOVES if _st == "snap"}

# 结果图种流水号（与技能图册顺序一致）
TOPIC_ORDER: dict[str, int] = {
    "骨架RMSD": 1,
    "三线RMSD": 2,
    "残基RMSF": 3,
    "氢键数": 4,
    "回旋半径": 5,
    "溶剂可及表面积": 6,
    "质心距离": 7,
    "NVT温度": 8,
    "NPT温度": 9,
    "NPT压力": 10,
    "NPT密度": 11,
    "生产势能": 12,
    "自由能形貌": 13,
    "自由能形貌RMSDx质心": 14,
    "自由能形貌RMSDxSASA": 15,
    "自由能形貌配体蛋白RMSD": 16,
    "自由能形貌3D": 17,
    "自由能形貌3D_RMSDx质心": 18,
    "自由能形貌3D_RMSDxSASA": 19,
    "自由能形貌3D_配体蛋白RMSD": 20,
    "结合能分解": 21,
    "结合能标注柱": 22,
    "结合能表": 23,
    "残基能量贡献": 24,
    "轨迹快照": 25,
    "二维相互作用": 26,
}

LAYOUT_README = """# 工作文件布局 / Md work layout

样例归档（本目录）按 MD 阶段分类；**GROMACS 引擎文件名不改**（`topol.top`、`md.tpr`、`-deffnm`）。
分析产物（xvg / 快照 PDB / MM-GBSA dat）用中英对照名。

| 文件夹 | 内容 |
|--------|------|
| `01_输入结构_Input/` | 蛋白 PDB、配体 pdb/mol2 |
| `02_拓扑_Topology/` | `topol.top`、`ligand.acpype/`、protein/complex.gro |
| `03_溶剂化离子_Solvation/` | 盒子 / 溶剂 / 离子 |
| `04_最小化_EnergyMin/` | `em.tpr/.gro/.edr`（不归档 `.trr`） |
| `05_NVT平衡_Nvt/` | `nvt.tpr/.gro/.edr/.cpt`（不归档 `.trr`） |
| `06_NPT平衡_Npt/` | `npt.tpr/.gro/.edr/.cpt`（不归档 `.trr`） |
| `07_生产轨迹_Production/` | `md.tpr` / `md.xtc` / `md_center.xtc` |
| `08_轨迹分析_Analysis/` | RMSD/RMSF/氢键/Rg/SASA/COM/能量 xvg |
| `09_结合自由能_MmGbsa/` | gmx_MMPBSA 结果 |
| `10_轨迹快照_Snapshots/` | 首/中/末 PDB（含 dry） |
| `99_运行日志_Logs/` | gmx / acpype 日志 |

GROMACS 生产请在**扁平临时目录**跑 `运行复合物MD_runComplexMd.sh`，结束后再执行
`python 脚本_scripts/整理样例目录_layoutMdSample.py` 归档。
"""


def topic_folder_name(topic: str) -> str:
    n = TOPIC_ORDER.get(topic)
    if n is None:
        return f"{topic}图"
    return f"{n:02d}_{topic}图"


def numbered_name(topic: str, filename: str) -> str:
    n = TOPIC_ORDER.get(topic)
    if n is None:
        return filename
    prefix = f"{n:02d}_"
    if filename.startswith(prefix):
        return filename
    return prefix + filename


def work_root(sample_root: Path | None = None) -> Path:
    sample = sample_root or SAMPLE
    new = sample / WORK_DIRNAME
    old = sample / WORK_DIRNAME_OLD
    if new.exists():
        return new
    return old if old.exists() else new


def system_dir(sample_root: Path | None = None, system: str = "3HTB") -> Path:
    return work_root(sample_root) / system


def stage_dir(sysdir: Path, key: str) -> Path:
    return sysdir / STAGES[key]


def resolve_analysis_file(sysdir: Path, english_name: str) -> Path:
    """英文原名或归档中英名，先 08/09/10 再根目录。"""
    staged: list[tuple[str, dict[str, str]]] = [
        ("anal", XVG_ARCHIVE),
        ("mmpbsa", MMPBSA_ARCHIVE),
        ("snap", SNAP_ARCHIVE),
    ]
    cands: list[Path] = []
    for key, mapping in staged:
        d = stage_dir(sysdir, key)
        if english_name in mapping:
            cands.append(d / mapping[english_name])
        cands.append(d / english_name)
    cands.append(sysdir / english_name)
    if english_name in XVG_ARCHIVE:
        cands.append(sysdir / XVG_ARCHIVE[english_name])
    for p in cands:
        if p.is_file():
            return p
    return cands[0]


def _move(src: Path, dest: Path, dry: bool) -> bool:
    if not src.exists():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if src.resolve() == dest.resolve():
            return False
        return False
    if dry:
        print(f"MOVE {src.name} -> {dest}")
        return True
    shutil.move(str(src), str(dest))
    return True


def apply_mdwork_layout(sample_root: Path, *, dry: bool = False) -> int:
    n = 0
    wr = sample_root / WORK_DIRNAME_OLD
    wn = sample_root / WORK_DIRNAME
    if wr.exists() and not wn.exists():
        if dry:
            print(f"RENAME {wr.name} -> {wn.name}")
        else:
            wr.rename(wn)
        n += 1
    sysdir = system_dir(sample_root)
    if not sysdir.is_dir():
        print("missing", sysdir)
        return n

    if not dry:
        for d in STAGES.values():
            (sysdir / d).mkdir(parents=True, exist_ok=True)

    lig_src = sysdir / "ligand.acpype"
    lig_dst = stage_dir(sysdir, "topo") / "ligand.acpype"
    if lig_src.is_dir() and not lig_dst.exists():
        n += int(_move(lig_src, lig_dst, dry))

    for key, name in ENGINE_MOVES:
        n += int(_move(sysdir / name, stage_dir(sysdir, key) / name, dry))

    for key, src, dst in RENAME_MOVES:
        dst_p = stage_dir(sysdir, key) / dst
        src_root = sysdir / src
        src_stage = stage_dir(sysdir, key) / src
        if src_root.exists():
            n += int(_move(src_root, dst_p, dry))
        elif src_stage.exists() and src_stage.name != dst:
            n += int(_move(src_stage, dst_p, dry))

    # 样例归档不留全精度 .trr（NVT/NPT 各约 80 MB）；分析用 xtc，续跑用 cpt
    for key, trr in (("em", "em.trr"), ("nvt", "nvt.trr"), ("npt", "npt.trr")):
        p = stage_dir(sysdir, key) / trr
        if p.exists() and not dry:
            p.unlink()
            n += 1

    logs = stage_dir(sysdir, "logs")
    for p in list(sysdir.glob("*.log")):
        n += int(_move(p, logs / p.name, dry))
    # 阶段目录里的 log 也归 99（引擎目录只留 gro/tpr/xtc）
    for key in ("em", "nvt", "npt", "prod", "anal", "mmpbsa", "snap", "solv", "topo"):
        d = stage_dir(sysdir, key)
        if not d.is_dir():
            continue
        for p in list(d.glob("*.log")):
            n += int(_move(p, logs / p.name, dry))

    readme = sysdir / "00_目录说明_Layout.md"
    if not dry and not readme.exists():
        readme.write_text(LAYOUT_README, encoding="utf-8")
        n += 1
    return n


def _topic_from_folder(name: str) -> str | None:
    if name == "报告文件":
        return None
    if name.endswith("图"):
        body = name[:-1]
        if len(body) >= 3 and body[:2].isdigit() and body[2] == "_":
            body = body[3:]
        if body in TOPIC_ORDER:
            return body
    return None


def apply_result_layout(sample_root: Path, *, dry: bool = False) -> int:
    result = sample_root / "代码文件" / "结果文件"
    if not result.is_dir():
        return 0
    n = 0
    # 先按主题重命名文件夹
    for child in list(result.iterdir()):
        if not child.is_dir():
            continue
        topic = _topic_from_folder(child.name)
        if topic is None:
            continue
        dest = result / topic_folder_name(topic)
        if child.resolve() == dest.resolve():
            continue
        if dest.exists():
            for p in child.iterdir():
                n += int(_move(p, dest / p.name, dry))
            if not dry and child.exists() and not any(child.iterdir()):
                child.rmdir()
            continue
        if dry:
            print(f"RENAME DIR {child.name} -> {dest.name}")
            n += 1
        else:
            child.rename(dest)
            n += 1

    def _has_cjk(s: str) -> bool:
        return any("\u4e00" <= ch <= "\u9fff" for ch in s)

    for child in list(result.iterdir()):
        if not child.is_dir():
            continue
        topic = _topic_from_folder(child.name)
        if topic is None:
            continue
        for p in list(child.iterdir()):
            if not p.is_file():
                continue
            # Origin 英文缓存 CSV 保持原名；中英对照交付文件加流水号
            if not _has_cjk(p.name):
                continue
            new_name = numbered_name(topic, p.name)
            if new_name == p.name:
                continue
            n += int(_move(p, child / new_name, dry))
    return n


def apply_raw_and_scripts(sample_root: Path, *, dry: bool = False) -> int:
    n = 0
    raw = sample_root / "数据文件" / "3HTB.pdb"
    dest = sample_root / "数据文件" / "01_复合物结构_3HTB.pdb"
    n += int(_move(raw, dest, dry))

    code = sample_root / "代码文件"
    pairs = [
        ("run_sample.R", "01_run_sample.R"),
        ("分析出图_plotMdAnalysis.R", "02_分析出图_plotMdAnalysis.R"),
    ]
    for src, dst in pairs:
        n += int(_move(code / src, code / dst, dry))
    return n


def rewrite_report_paths(sample_root: Path, *, dry: bool = False) -> bool:
    html = sample_root / "代码文件" / "结果文件" / "报告文件" / "样例报告_SampleReport_v1.html"
    if not html.exists():
        return False
    text = html.read_text(encoding="utf-8")
    orig = text
    text = text.replace("工作文件_mdwork", WORK_DIRNAME)
    text = text.replace("1 ns 生产（演示尺度）", "0.20 ns 生产（演示尺度）")
    for topic, num in TOPIC_ORDER.items():
        folder = topic_folder_name(topic)
        old_folder = f"{topic}图"
        text = text.replace(f"../{old_folder}/", f"../{folder}/")
        prefix = f"{num:02d}_"
        # 给尚未编号的文件名加前缀（避免重复加）
        # 形如 ../26_二维相互作用图/二维相互作用_LigPlot2D.png
        needle = f"../{folder}/"
        parts = text.split(needle)
        if len(parts) > 1:
            rebuilt = [parts[0]]
            for chunk in parts[1:]:
                rebuilt.append(needle)
                if chunk.startswith(prefix):
                    rebuilt.append(chunk)
                else:
                    rebuilt.append(prefix + chunk)
            text = "".join(rebuilt)
    if text == orig:
        return False
    if dry:
        print("PATCH report HTML")
        return True
    html.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=Path, default=SAMPLE)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-results", action="store_true")
    args = ap.parse_args()
    sample = args.sample
    dry = args.dry_run
    n = apply_mdwork_layout(sample, dry=dry)
    n += apply_raw_and_scripts(sample, dry=dry)
    if not args.skip_results:
        n += apply_result_layout(sample, dry=dry)
        rewrite_report_paths(sample, dry=dry)
    print(f"layout_ops={n} dry={dry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
