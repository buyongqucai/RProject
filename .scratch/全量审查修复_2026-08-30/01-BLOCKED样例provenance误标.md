# 01 — BLOCKED 样例 provenance 误标

标签: 已完成（2026-08-30）

## 修复记录

- 接缝：`规范_数据审计_DataAudit.R` 增 `data_provenance="BLOCKED"` → `toy=FALSE` 强制分支。
- 模板：12 个 BLOCKED 样例 `run_sample.R` 统一显式传 `data_provenance = "BLOCKED"`，报告正文 toy=TRUE 表述改为 BLOCKED 契约桩表述（3DGenome 变体单独修；WGBS-RRBS 为 REAL 样例，不在此列）。（复审更正：初版记录误写 13 个，实为 12 个。）
- 复审补强：12 个模板位置参数 `toy=TRUE` → `FALSE`，调用点与 `data_provenance="BLOCKED"` 不再自相矛盾。
- 测试：`统一交付规范_DeliveryStandards/测试_tests/test_blocked_provenance.R`（testthat，27 PASS）锁定接缝行为 + 全库模板回归扫描。
- E2E：重跑分子对接样例，`审计后检_AuditPost.csv` = `toy=FALSE, data_provenance="BLOCKED"`。

## 来源

Standards 轴（硬性，DeliveryStandards §1）+ Spec 轴（c）。

## 问题

`分子对接与虚拟筛选_MolecularDocking/01_样例_sample/代码文件/run_sample.R:64` 对 `analysis_kind=blocked_docking` 硬编码 `toy=TRUE`，`:78` 报告正文称「可复现模拟数据」；但 `DATA_SOURCE.md`/`STATUS.txt` 标 BLOCKED，契约桩无任何模拟数据。其它 BLOCKED 样例疑同病（同模板）。

## 验收标准

- BLOCKED 样例审计表/报告写 `data_provenance="BLOCKED"`，无 toy=TRUE 表述；
- 全库 grep 同类模板（`analysis_kind=blocked` 或 `write_delivery_audit(..., TRUE, ...)` 于 BLOCKED 样例）一并修复；
- 重跑分子对接样例，审计表与 STATUS 一致。
