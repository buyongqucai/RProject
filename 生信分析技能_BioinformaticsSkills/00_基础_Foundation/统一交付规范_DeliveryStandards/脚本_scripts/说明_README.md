# 统一交付规范 — 脚本说明
# - 规范_出图与命名_PlotNaming.R：文件名中英对照 `{中文}_{EnglishPascal}`；delivery_stem / delivery_save_plot
#   （图面文字 English only，禁止中文；见技能说明 §6「文件名双语 ≠ 图面英文」）
#   样例路径：delivery_sample_paths(sample_root) → raw/code/result（结果在 代码文件/结果文件，兼容旧根级）
#   流水线编号：delivery_order_prefix / delivery_stem(..., order=) / delivery_save_plot(..., order=)
#   保存后钩子：VizStandards 出图后审核_PlotQA（viz_qa_after_plot；options(bioinfo.plotqa.*)）
# - 规范_数据审计_DataAudit.R：write_delivery_audit → 审计前检_AuditPre / 审计后检_AuditPost
# - 规范_报告生成_ReportBuild.R：write_delivery_report → 样例报告_SampleReport_v1.html
#
# 目录约定 SSOT：../文档_docs/样例目录与命名_SampleLayoutNaming.md
# 样例 run_sample.R 强制按序 source：VizStandards → DeliveryStandards → 本技能脚本
#   Rscript 01_run_sample.R
#
# 批量重命名/重跑：../../_phaseD_bilingual_naming.py
