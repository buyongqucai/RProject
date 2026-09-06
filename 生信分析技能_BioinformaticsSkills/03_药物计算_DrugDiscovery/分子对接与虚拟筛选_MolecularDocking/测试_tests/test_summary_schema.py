# -*- coding: utf-8 -*-
"""summary_vina.csv 唯一 schema 的行为契约（议题 02）。

接缝：
  1. dock_summary_schema.load_summary_rows(path) — 两种 schema → 统一 canonical dict
  2. plot_docking_ring_heatmap.load_summary(root) — 接受 legacy 中文 schema
  3. pymol_dock_viz_standard.select_jobs(..., top=N) — 接受 canonical 英文 schema
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "脚本_scripts"


def _import(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CANONICAL_CSV = (
    "task,protein,pdb,ligand,ligand_name,cid,affinity_kcal_mol,"
    "center_source,center_detail,size_method,box_qc,fallback_used,engine\n"
    "1,KIT,1T46,quercetin,Quercetin,5280343,-10.5,"
    "cocrystal_meeko,STP:A:301,meeko_enveloping,PASS,,adgpu\n"
    "2,KIT,1T46,luteolin,Luteolin,5280445,-8.3,"
    "cocrystal_meeko,STP:A:301,meeko_enveloping,PASS,,adgpu\n"
)

LEGACY_CSV = (
    "对接序号,蛋白,PDB,成分,CID,best_affinity_kcal,status\n"
    "1,KIT,1T46,quercetin,5280343,-10.5,ok\n"
    "2,KIT,1T46,luteolin,5280445,-8.3,ok\n"
)

MINIMAL_CANONICAL_CSV = (
    "task,protein,pdb,ligand,ligand_name,cid,affinity_kcal_mol\n"
    "1,KIT,1T46,quercetin,Quercetin,5280343,-10.5\n"
)


@pytest.fixture()
def canonical_csv(tmp_path: Path) -> Path:
    p = tmp_path / "summary_vina.csv"
    p.write_text(CANONICAL_CSV, encoding="utf-8")
    return p


@pytest.fixture()
def legacy_csv(tmp_path: Path) -> Path:
    p = tmp_path / "summary_vina.csv"
    p.write_text(LEGACY_CSV, encoding="utf-8")
    return p


def test_canonical_schema_parsed(canonical_csv: Path) -> None:
    schema = _import("dock_summary_schema")
    rows = schema.load_summary_rows(canonical_csv)
    assert len(rows) == 2
    assert rows[0]["task"] == "1"
    assert rows[0]["protein"] == "KIT"
    assert rows[0]["pdb"] == "1T46"
    assert rows[0]["ligand"] == "quercetin"
    assert rows[0]["cid"] == "5280343"
    assert rows[0]["affinity_kcal_mol"] == pytest.approx(-10.5)
    assert rows[0]["center_source"] == "cocrystal_meeko"
    assert rows[0]["engine"] == "adgpu"
    assert schema.center_source_ok(rows[0]["center_source"], require=True)


def test_legacy_schema_normalized_to_canonical(legacy_csv: Path) -> None:
    schema = _import("dock_summary_schema")
    rows = schema.load_summary_rows(legacy_csv)
    assert len(rows) == 2
    assert rows[1]["task"] == "2"
    assert rows[1]["ligand"] == "luteolin"
    assert rows[1]["affinity_kcal_mol"] == pytest.approx(-8.3)
    assert rows[1]["center_source"] == ""  # 旧表无列，容忍空
    assert schema.center_source_ok("", require=False)
    assert not schema.center_source_ok("", require=True)


def test_minimal_canonical_fills_center_fields(tmp_path: Path) -> None:
    p = tmp_path / "summary_vina.csv"
    p.write_text(MINIMAL_CANONICAL_CSV, encoding="utf-8")
    schema = _import("dock_summary_schema")
    rows = schema.load_summary_rows(p)
    assert rows[0]["center_source"] == ""
    assert rows[0]["center_detail"] == ""


def test_center_method_alias_normalized() -> None:
    schema = _import("dock_summary_schema")
    assert schema.normalize_center_source("cocrystal_single_ligand_COM") == "cocrystal"
    assert schema.center_source_ok("autosite", require=True)
    assert not schema.center_source_ok("chain_com", require=True)


def test_ring_heatmap_accepts_legacy_schema(tmp_path: Path) -> None:
    (tmp_path / "summary_vina.csv").write_text(LEGACY_CSV, encoding="utf-8")
    (tmp_path / "1").mkdir()
    ring = _import("plot_docking_ring_heatmap")
    rows = ring.load_summary(tmp_path)
    assert [r["task"] for r in rows] == ["1", "2"]
    assert rows[0]["affinity"] == pytest.approx(-10.5)


def test_viz_standard_top_n_accepts_canonical_schema(tmp_path: Path) -> None:
    jobs_root = tmp_path / "序号文件夹"
    (jobs_root / "1").mkdir(parents=True)
    (jobs_root / "2").mkdir()
    (tmp_path / "summary_vina.csv").write_text(CANONICAL_CSV, encoding="utf-8")
    viz = _import("pymol_dock_viz_standard")
    picked = viz.select_jobs(jobs_root, only=None, top=1, do_all=False)
    assert [p.name for p in picked] == ["1"]
