# 01: 技能 SSOT 进化（解冻登记 + 口径写入）

**类别:** enhancement
**标签:** 已完成
**Blocked by:** None（可立即开始）

**What to build:** 把用户确认的 6 项口径写入网药技能 SSOT（一处真源），并在 FROZEN 出图约束里登记解冻；技能说明只改指针。

- [ ] `文档_docs/数据库分类与流水线_DataSourcesPipeline.md`：明确「疾病下游并集 = GeneCards≥40 ∪ TTD ∪ DrugBank ∪ OMIM ∪ **CTD**（5 库）」，韦恩多库展示同纳 CTD
- [ ] `文档_docs/出图约束_NetworkFigureStandards.md` §A：化合物节点命名 = 药拼音首字母+序号、共用 `same+序号`、**禁 `H_` 前缀**；靶点保留基因符号
- [ ] 同文件 §A1：通路 D 色块 = **正六边形**，长宽 **60–120**（保留待拍板注）
- [ ] 同文件：GO 气泡条款 —— X=富集分数（`enrichment`=FoldEnrichment）、竖排 BP/CC/MF、按富集分数自上而下；恢复 `np_plot_go_bubble` 默认语义
- [ ] 「修订记录」加 2026-10-15 解冻登记行（改 §0a 口径 + §A 节点 + GO 气泡；不改其余图样）
- [ ] 技能说明指针如需微调（不复述 recipe）

## Notes
备份 commit `afd483b`。范式：SkillParadigm（改技能文档须逐文件核对指针/SSOT 唯一性）。
