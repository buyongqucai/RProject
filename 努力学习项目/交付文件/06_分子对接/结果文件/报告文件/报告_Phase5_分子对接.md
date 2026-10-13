# 报告：Phase 5 分子对接（核心对 · 代谢物）

> 日期：2026-10-07（单位更正 2026-10-12）｜脚本：`03_三源交集_复方UC菌群/代码文件/12_分子对接.py`
> 定位：结合候选。**主单位 kcal/mol**（FROZEN）。阈值 **−5.0 kcal/mol**（约合 −20.9 kJ/mol）。
> 产物：`对接全表.csv`、`对接汇总.csv`

## 结果（mean ± SD，kcal/mol）

| 代谢物 × 靶点 | PDB | mean kcal/mol | SD | 阈值 |
|---|---|---:|---:|---|
| Tryptophan × MMP9 | 4H3X | **-8.91** | 0.02 | PASS |
| Indole × CYP1A1 | 4I8V | **-7.10** | 0.00 | PASS |
| Adenosine × ADA | 3IAR | **-6.59** | 0.01 | PASS |
| Phenylalanine × PPARG | 1FM9 | **-6.30** | 0.01 | PASS |
| Arginine × NOS3 | 1K2S | **-6.23** | 0.02 | PASS |
| Tryptophan × MPO | 1CXP | **-5.35** | 0.15 | PASS |
| 4-Hydroxyphenylacetic acid × CA2 | 1A42 | **-5.26** | 0.01 | PASS |
| Indole-3-acetic acid × ACHE | 13CO | -4.73 | 0.02 | no |
| Butyrate × PPARG | 1FM9 | -3.93 | 0.02 | no |

## 靶点筛选说明

见 `对接选型逻辑_成分与代谢物统一.md`。本批代谢物对当时**未**按 PPI Degree 重选；本次仅将报告/汇总主单位改为 kcal/mol，**未重跑** Vina。
