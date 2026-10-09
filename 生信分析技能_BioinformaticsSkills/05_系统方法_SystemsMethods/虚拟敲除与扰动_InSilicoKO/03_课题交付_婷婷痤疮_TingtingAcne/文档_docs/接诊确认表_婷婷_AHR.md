# 虚拟敲除确认表（补录）

> **状态：** 补录归档。正式敲除（scTenifoldKnk 1.4.3 GPU + GenKI）已于 2026-10-04 完成；本表按 [`接诊与确认表单_IntakeConfirmForm.md`](../../../文档_docs/接诊与确认表单_IntakeConfirmForm.md) 回填当时已确认的口径，补 SOP 缺口。  
> **用户确认记录：** 本表随「补齐婷婷交付三件套」请求一并认可（2026-10-04）。

| 栏 | 字段 | 值 | 来源 | 可信度 | 确认 |
|----|------|----|------|--------|------|
| A | species | 人（Homo sapiens） | 用户：GSE175817 痤疮 | H | [x] |
| A | gene_ko | AHR | 用户指定；NF-κB/Th17/M1M2 面板为读出不敲 | H | [x] |
| A | tissue | 人面部皮肤（痤疮皮损/非皮损） | GSE175817（Do 等） | H | [x] |
| A | bio_state | 建网用 Lesional（皮损）；对比 Nonlesional | 计划 §3 | H | [x] |
| A | contrast_priority | 皮损亚群内虚拟敲除；皮损 vs 非皮损另做伪 bulk 差异（不在本技能） | 用户 2026-10-04 | H | [x] |
| A | cell_universe | 作者注释巨噬亚群：TREM2 / M1-like / M2-like（不用 AHR 表达选群） | 计划 §3 | H | [x] |
| A | method | 双引擎两实例：scTenifoldKnk（1.4.3 GPU）+ GenKI | 用户点名 | H | [x] |
| A | delivery_scope | 只做虚拟敲除交付（09 夹）；差异/WGCNA/极化/对接各归其技能 | 用户 | H | [x] |
| B | engine | scTenifoldKnk 1.4.3 GPU + GenKI（VGAE） | 方法登记 | H | [x] |
| B | Knk 参数 | nNet=10，nCells=min(500,n−1)，td_K=3，minLibSize=1000；pcnet_143 n_comp=3 q=0.9 GPU | Osorio 2022 / 包默认 | H | [x] |
| B | GenKI 参数 | HVG=3000（vst，AHR 补入）；100 次搜索；1000 次不放回排列；响应=KL top5% ∩ hit>95% | Yang NAR 2023 | H | [x] |
| B | claim_language | 计算预测；响应基因 ≠ Seurat DEG；禁写湿实验 KO | 技能硬规则 | H | [x] |
| C | dataset_id | GSE175817（作者 myeloid.Rdata 注释） | Phase1 | H | [x] |
| C | dataset_fit | 满足：人、皮肤、皮损/非皮损、基因×细胞 counts、作者注释分亚群 | Phase1 | H | [x] |
| C | subtypes_to_ko | 皮损 TREM2 macrophage、皮损 M2-like macrophage（M1-like AHR 检出 0 不敲） | Phase1 检出率 | H | [x] |
| C | n_cells_per_subtype | TREM2 皮损 1515；M2-like 皮损 266；M1-like 皮损 116 | 2026-10-04 导出 | H | [x] |
| C | gene_detection_rate | AHR 检出：TREM2 436/1515（28.8%）；M2-like 95/266（35.7%）；M1-like 0/116（0%） | 检出率表 | H | [x] |
| C | control_gene | Knk：MGAT4A；GenKI：TREM2→DHRS9、M2→FEN1（各引擎网内 |Pearson| 最低） | 运行日志 | H | [x] |

**结果去向：** 桌面 `婷婷\虚拟敲除\结果文件\`；报告入口 `_跨亚群\课题报告_ProjectReports\报告文件\index_报告入口.html`。  
**禁止：** 将虚拟敲除结果写成真实动物/细胞 KO 的差异表达。
