# 01 — BLOCKED 样例 provenance 误标

标签: 待Agent处理

## 来源

Standards 轴（硬性，DeliveryStandards §1）+ Spec 轴（c）。

## 问题

`分子对接与虚拟筛选_MolecularDocking/01_样例_sample/代码文件/run_sample.R:64` 对 `analysis_kind=blocked_docking` 硬编码 `toy=TRUE`，`:78` 报告正文称「可复现模拟数据」；但 `DATA_SOURCE.md`/`STATUS.txt` 标 BLOCKED，契约桩无任何模拟数据。其它 BLOCKED 样例疑同病（同模板）。

## 验收标准

- BLOCKED 样例审计表/报告写 `data_provenance="BLOCKED"`，无 toy=TRUE 表述；
- 全库 grep 同类模板（`analysis_kind=blocked` 或 `write_delivery_audit(..., TRUE, ...)` 于 BLOCKED 样例）一并修复；
- 重跑分子对接样例，审计表与 STATUS 一致。
