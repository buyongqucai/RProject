# Phase 4 毒性分层执行报告

> 日期：2026-10-07
> 定位：非主线毒性分层/毒性线索；不构成完整网络毒理学、拮抗或减毒结论。
> 数据源：CTD 官方 bulk 文件（CTD_chemicals、CTD_chem_gene_ixns），2026-10-07 访问。

## 1. 暴露物范围

- 小分子有害候选：TMAO、p-Cresol sulfate、Indoxyl sulfate、Deoxycholic acid、Lithocholic acid。
- 特殊暴露物：LPS（PAMP）、H₂S（气体信号）。
- 不良结局限定：肠屏障损伤、肠道炎症、黏膜损伤/癌变风险。
- beneficial/harmful 只作下游注释，不作主分析入口过滤。

## 2. CTD 策展证据

- 7 个暴露物均有 CTD 人类基因互作。
- 14,302 条人类化学–基因互作，4,188 个唯一基因。
- 有害暴露物靶点与核心 C 的暴露物–基因重叠共 97 条。
- CTD InteractionActions 同时包含 increases/decreases/affects，故效应方向不能简化为单向。

代表性重叠：
- LPS：3,898 个 CTD 人类基因，55 个与 C 重叠。
- DCA：427 个基因，18 个与 C 重叠。
- LCA：123 个基因，15 个与 C 重叠。
- Indoxyl sulfate：35 个基因，5 个与 C 重叠。
- TMAO：8 个基因，3 个与 C 重叠。

## 3. 结论边界

当前结果支持：
> “有害暴露物与复方/UC 共同靶点存在毒性线索和共同调控候选”。

当前结果不支持：
- 复方拮抗有害代谢物；
- 复方减毒；
- 剂量–反应或组织特异毒性结论；
- 将 CTD 推断关联等同实验证实。

## 4. 图件

- 暴露物覆盖图：CTD 基因、I₁ 重叠、C 重叠。
- 暴露物–共同靶点网络：仅展示与 C 重叠的 Top20 靶点。
- 方向证据热图：按 CTD 文本中的 increases/decreases 计数形成探索性方向评分，不等于净效应。

三张图均输出 PNG+SVG、DPI 600、English，PlotQA PASS。
