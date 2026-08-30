# -*- coding: utf-8 -*-
"""summary_vina.csv 唯一 schema（SSOT，议题 02）。

canonical 列（英文，新写一律用此）：
  task, protein, pdb, ligand, ligand_name, cid, affinity_kcal_mol

legacy 中文列（痤疮/努力学习旧项目）按 LEGACY_COLUMN_MAP 归一化，禁止再扩散。
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
]

LEGACY_COLUMN_MAP = {
    "对接序号": "task",
    "蛋白": "protein",
    "PDB": "pdb",
    "成分": "ligand",
    "CID": "cid",
    "best_affinity_kcal": "affinity_kcal_mol",
}


def load_summary_rows(path: Path) -> list[dict]:
    """读取 summary_vina.csv，统一返回 canonical 键；affinity 转 float。

    跳过 affinity 缺失/非数值的行；task 空白行跳过。
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
            rows.append(row)
    return rows
