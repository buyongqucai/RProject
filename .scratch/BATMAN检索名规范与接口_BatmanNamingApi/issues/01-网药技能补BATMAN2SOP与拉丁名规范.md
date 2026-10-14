# 01: 网药技能补 BATMAN 2.0 SOP 与拉丁名检索规范

**类别:** enhancement
**标签:** 已完成
**Blocked by:** None（可立即开始）
**技能路径:** `03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology`

**What to build:** 把用户确认规则与 BATMAN 2.0 实测接口写入 SSOT（一处），技能说明只改指针。

- [x] `文档_docs/成分靶点获取与交付规范_CompoundTargetSOP.md`：新增 §8 检索名规范（仅拉丁/英文，禁拼音）+ §9 BATMAN-TCM 2.0 程序化接口实测（queryTarget / queryTargetResult / downloadApiFile zip，known 标注口径，SHUI ZHI 混条实证）
- [x] `文档_docs/数据库分类与流水线_DataSourcesPipeline.md` §1.4：BATMAN-TCM 2.0 → AUTO（API 实测）
- [x] `技能说明_网络药理学_NetworkPharmacology.md` §2：加检索名规范指针一行
- [x] 不动 FROZEN 出图约束；不动瀑布次序（BATMAN 仅 known 不变）

## Notes

2026-10-14 实测端点（bionet.ncpsb.org.cn / batman2api.cloudna.cn / batman2.cloudna.cn 三域）；
作业包 URL 模板 `/downloadApiFile/data/query_TARGET_result/{jobId}/Results of target protein.zip` 已验证可拉。
