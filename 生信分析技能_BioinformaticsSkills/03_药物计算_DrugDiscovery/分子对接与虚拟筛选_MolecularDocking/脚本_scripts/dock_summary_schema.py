# -*- coding: utf-8 -*-
"""summary_vina.csv / summary_adgpu.csv schema（SSOT，议题 02 + 中心方法登记）.

canonical 列（英文，新写一律用此）：
  task, protein, pdb, ligand, ligand_name, cid, affinity_kcal_mol,
  center_source, center_detail, size_method, box_qc, fallback_used, engine

legacy 中文列（痤疮/努力学习旧项目）按 LEGACY_COLUMN_MAP 归一化，禁止再扩散。

中心方法受控词表见：
  文档_docs/中心位点方法登记_CenterSourceRegistry.md
"""
from __future__ import annotations

import csv
from pathlib import Path

CANONICAL_COLUMNS = [
    "task",
    "protein",
    "pdb",
    "ligand",
    "ligand_name",
    "cid",
    "affinity_kcal_mol",
    "center_source",
    "center_detail",
    "size_method",
    "box_qc",
    "fallback_used",
    "engine",
]

# 亲和力相关核心列；旧 CSV 可只有这些
CORE_COLUMNS = [
    "task",
    "protein",
    "pdb",
    "ligand",
    "ligand_name",
    "cid",
    "affinity_kcal_mol",
]

CENTER_SOURCE_CODES = frozenset(
    {
        "cocrystal",
        "cocrystal_meeko",
        "annotated_site",
        "autosite",
        "p2rank",
        "fpocket",
        "manual",
        "FAIL",
    }
)

# 蛋白表历史写法 → 任务级 center_source
CENTER_METHOD_ALIASES = {
    "cocrystal_single_ligand_COM": "cocrystal",
}

LEGACY_COLUMN_MAP = {
    "对接序号": "task",
    "蛋白": "protein",
    "PDB": "pdb",
    "成分": "ligand",
    "CID": "cid",
    "best_affinity_kcal": "affinity_kcal_mol",
    "中心方法": "center_source",
    "center_method": "center_source",
}


def normalize_center_source(raw: str | None) -> str:
    """归一别名；空串保持空（旧表容忍）。"""
    s = (raw or "").strip()
    if not s:
        return ""
    return CENTER_METHOD_ALIASES.get(s, s)


def center_source_ok(code: str, *, require: bool = False) -> bool:
    """新批次 require=True 时：必须非空且在受控词表内。"""
    code = normalize_center_source(code)
    if not code:
        return not require
    return code in CENTER_SOURCE_CODES


def load_summary_rows(path: Path) -> list[dict]:
    """读取 summary_*.csv，统一返回 canonical 键；affinity 转 float。

    跳过 affinity 缺失/非数值的行；task 空白行跳过。
    扩展列缺失时填空串（兼容旧工程）；不在此强制 center_source。
    """
    rows: list[dict] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            row = {LEGACY_COLUMN_MAP.get(k, k): (v or "").strip() for k, v in raw.items()}
            task = row.get("task", "")
            if not task:
                continue
            try:
                row["affinity_kcal_mol"] = float(row.get("affinity_kcal_mol") or "nan")
            except ValueError:
                continue
            if row["affinity_kcal_mol"] != row["affinity_kcal_mol"]:  # NaN
                continue
            for col in CANONICAL_COLUMNS:
                if col == "affinity_kcal_mol":
                    continue
                if col not in row or row[col] is None:
                    row[col] = ""
            row["center_source"] = normalize_center_source(row.get("center_source"))
            rows.append(row)
    return rows
