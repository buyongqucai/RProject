# -*- coding: utf-8 -*-
"""Measure HCTP target-grid pitch vs estimated label box (debug-360a4e)."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

LOG = Path(r"E:/RProject/debug-360a4e.log")
DATA = Path(r"E:/RProject/努力学习项目/网络药理学/数据文件")


def log(hid: str, loc: str, msg: str, data: dict) -> None:
    with LOG.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "sessionId": "360a4e",
                    "runId": "pre-fix",
                    "hypothesisId": hid,
                    "location": loc,
                    "message": msg,
                    "data": data,
                    "timestamp": int(time.time() * 1000),
                },
                ensure_ascii=False,
            )
            + "\n"
        )


def main() -> None:
    typ = pd.read_csv(DATA / "网络节点类型_type.csv", encoding="utf-8-sig")
    genes = typ.loc[typ["type"] == "C", "term"].astype(str).tolist()
    n = len(genes)
    max_len = max((len(g) for g in genes), default=1)
    # Current delivery params from last R run (approx)
    # size_to_r~457, size 60-120 → r_t max ~120/457≈0.262
    # pitch_factor_x=2.15 → pitch_x ≈ 2*0.262*2.15 ≈ 1.13 (columns last run was 0.95)
    r_t = 120 / 457.0
    for mode, fx, fy, w_in, h_in in [
        ("columns_prev", 2.15, 2.30, 21, 19),
        ("ellipse_prev", 2.25, 2.45, 21, 19),
        ("columns_need", 3.2, 3.4, 24, 22),
        ("ellipse_need", 3.2, 3.4, 24, 22),
    ]:
        pitch_x = 2 * r_t * fx
        pitch_y = 2 * r_t * fy
        # estimate label half-width in data: nch * 0.55 * lab_mm * dpm
        # dpm ≈ (data_span)/(height_mm); span ~ n_rows * pitch_y
        ncol = max(8, int((n * 1.15) ** 0.5 + 0.999))
        nrow = int((n + ncol - 1) / ncol)
        span_y = nrow * pitch_y
        height_mm = h_in * 25.4
        dpm = (span_y * 1.15) / height_mm  # data per mm
        lab_mm = 2.57
        half_w = max_len * 0.52 * lab_mm * dpm / 2
        half_h = 1.05 * lab_mm * dpm / 2
        # non-overlap if pitch/2 > half_extent
        ok_x = pitch_x / 2 > half_w * 1.05
        ok_y = pitch_y / 2 > half_h * 1.05
        log(
            "G",
            "21_measure_target_pitch.py",
            "target pitch vs label box",
            {
                "mode": mode,
                "n_targets": n,
                "max_gene_len": max_len,
                "r_t": r_t,
                "pitch_x": pitch_x,
                "pitch_y": pitch_y,
                "label_half_w_data": half_w,
                "label_half_h_data": half_h,
                "gap_x": pitch_x / 2 - half_w,
                "gap_y": pitch_y / 2 - half_h,
                "overlap_risk_x": not ok_x,
                "overlap_risk_y": not ok_y,
                "canvas_in": [w_in, h_in],
            },
        )
        print(mode, "risk_x", not ok_x, "risk_y", not ok_y, "gap_x", round(pitch_x / 2 - half_w, 4))


if __name__ == "__main__":
    main()
