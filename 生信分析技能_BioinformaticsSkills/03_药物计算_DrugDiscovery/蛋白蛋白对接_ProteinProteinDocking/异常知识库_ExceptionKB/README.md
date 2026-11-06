# 异常知识库_ExceptionKB — 蛋白蛋白对接_ProteinProteinDocking

> 写法 SSOT：`E:\RProject\docs\agents\异常知识库规范_ExceptionKb.md`。

## 案例索引

| 序号 | 症状 | 判定要点 | 补救 | 案例 |
|------|------|----------|------|------|
| 01 | 未登记 chain_source 就上传 | task_info 无 chain_source | 停；SOP §3 补登记 | [01](案例_Cases/01-链选择未登记.md) |
| 02 | 辅因子被误删 | clean_report 无 FAD 等 | keep_cofactor 重清 | [02](案例_Cases/02-辅因子误删.md) |
| 03 | 跳过调研直接最长链 | 无 chain_survey | 补调研模板 | [03](案例_Cases/03-跳过调研直接最长链.md) |
| 04 | 全纤维链超体积 | 多全长链合计过大 | 只留代表原体/CA | [04](案例_Cases/04-全纤维链超体积.md) |
| 05 | detail 白边未裁净 | 边缘行 white_frac≥0.92 | `prepare_detail_square.py` | [05](案例_Cases/05-detail白边未裁净.md) |
