# 01: 按高分信源整理 MR 实现路径并写入技能

**类别:** enhancement
**标签:** 已完成
**Blocked by:** None（可立即开始）

**What to build:** 孟德尔随机化技能能按一份默认路径执行两样本汇总数据 MR，并知道何时改走多变量、药物靶点、xQTL 或单样本。

- [x] 操作依据落到 Burgess 2023 指南、STROBE-MR、TwoSampleMR / MendelianRandomization / OpenGWAS 官方文档
- [x] 核对现行包版本，弱工具变量、样本重叠、MVMR、coloc、SMR 标成分支而不是第二套主分析
- [x] 技能说明保持短入口；流水线与信源分文件；样例仍为 TOY
- [x] catalog 与 CONTEXT 能指向该技能及 SSOT

## Notes

完成日期 2026-10-30。指南最新核对为 Wellcome Open Research 4:186 version 3（2019 首发，2023-08-04 更新）。未见 version 4。流水线尚未冻结，等用户确认后再登记。
