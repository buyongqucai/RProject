# 09: NFKB1 虚拟敲除 Phase 2

**类别:** enhancement
**标签:** 已完成
**Blocked by:** 08-NFkB并行主线与阶段门.md（Phase 1 已通过）
**完成日期:** 2026-10-08

**What to build:** 使用 NFKB1 作为 NF-κB 主目标基因，运行与 AHR 等价的双算法虚拟敲除。

- [x] Phase 1：NFKB1 在 TREM2 皮损 599/1515（39.5%）、M2-like 皮损 97/266（36.5%）检出
- [x] Phase 2A：scTenifoldKnk TREM2/M2 × NFKB1，各自匹配阴性对照
- [x] Phase 2B：GenKI TREM2/M2 × NFKB1，目标不在 HVG 时强制补入
- [x] 比较目标与对照响应，设置目标特异性门禁
- [x] Phase 3：M2-like NFKB1 全排序 GSEA 与对照 GSEA 对比
- [x] 结论：TREM2/ scTenifoldKnk 特异性不足；M2-like GenKI 有探索性候选，但 NF-κB 本体未严格通过

## Notes

结果：
- Knk TREM2：NFKB1 与 B3GNT5 均为 GAPDH；
- Knk M2：NFKB1 与 PSAP 均为 RPL10/RPS18；
- GenKI TREM2：NFKB1 与 AC023590.1 共有 APOE/SPP1，排名 Spearman=0.987；
- GenKI M2：NFKB1 14 个其他响应，对照 AC007613.1 2 个，响应无交集，排名 Spearman=0.048；
- GSEA：NFKB1 M2 严格通过 21 条，对照 44 条，重叠 11 条；NF-κB 相关条目未通过严格阈值。