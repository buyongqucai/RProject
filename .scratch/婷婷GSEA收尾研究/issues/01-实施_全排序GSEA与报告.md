# 01: 实施全排序 GSEA 与详细报告

**类别:** enhancement
**标签:** 已完成
**Blocked by:** 00-研究_婷婷缺失收尾.md（已完成）
**完成日期:** 2026-10-07

**What to build:** 对婷婷 AHR 虚拟敲除完整排名运行 GSEA，形成可复现数据、图和详细报告，并如实报告是否找到合适通路。

- [x] scTenifoldKnk TREM2/M2 × AHR 的完整 `扰动_Dr.csv` 做 GO BP/CC/MF + KEGG 全排序 GSEA
- [x] GenKI TREM2/M2 × AHR 的完整 `KL排序_RankKL.csv` 做独立探索性 GSEA
- [x] 保存完整结果、通过条目、参数/版本/映射审计和可复现脚本
- [x] 出图：特异性诊断、GSEA 曲线、严格通过数、NES/P 汇总图；English、DPI≥600、SVG+PNG
- [x] 生成详细 HTML 报告，区分 ORA/GSEA、Knk/GenKI，不把扰动方向写成上下调
- [x] 更新报告入口、STATUS；链接校验 BAD=0
- [x] 报告明确回答：没有跨亚群/跨引擎稳定通路；GenKI 对 M2-like 有额外候选主题

## Notes

- 完整结果 44,184 行；目标严格通过 88 条，对照严格通过 18 条。
- scTenifoldKnk distance 主结果以 translation/ribosome/structural molecule 为主。
- GenKI TREM2 无严格条目；GenKI M2 有 extracellular exosome/vesicle、receptor-ligand、immune response 等候选主题。
- 特异性诊断显示 Knk AHR 与对照响应基因完全重合；GenKI M2 目标/对照区分较好。
- 报告：`C:\Users\10540\Desktop\婷婷\虚拟敲除\结果文件\_跨亚群\课题报告_ProjectReports\报告文件\全排序GSEA报告_RankedGsea.html`