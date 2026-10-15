# 异常知识库_ExceptionKB — 分子对接与虚拟筛选_MolecularDocking

> 写法与案例模板：`E:\RProject\docs\agents\异常知识库规范_ExceptionKb.md`（SSOT）。  
> 路线与约束：`文档_docs/对接与交付约束_DockingFrozen.md`、`文档_docs/技术路线_AutoSite_AutoDockGPU.md`。

## 案例索引

| 序号 | 症状 | 判定要点（一锤定音） | 补救路径 | 案例 |
|------|------|----------------------|----------|------|
| 01 | 结合能为正 / 姿态贴盒缘 | affinity>0 或 pose 出盒 | AutoSite §2–§3 重定盒重跑，禁沿用旧盒 | [01](案例_Cases/01-正结合能或错盒.md) |
| 02 | 配体 PDBQT 构建失败 / 结构怪异 | z-span≈0、盐型、含 Si | 回退链：本地库→PubChem 3D→SMILES+obabel；逐条登记 | [02](案例_Cases/02-配体结构异常与构建失败.md) |
| 03 | 受体带核酸/多链混入 | `ATOM` 行链含 DA/DC/DG/DT/RNA 残基 | 剔核酸重清洗（FROZEN：蛋白对接默认剔核酸） | [03](案例_Cases/03-受体核酸混入.md) |
| 04 | 交付缺 center_source / 无法追溯定心 | summary 行无 `center_source` | 不交付；按登记表补方法与决策树出处 | [04](案例_Cases/04-定心来源不可追溯.md) |
