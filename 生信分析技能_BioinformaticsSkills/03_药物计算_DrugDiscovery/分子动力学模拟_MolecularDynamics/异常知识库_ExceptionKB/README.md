# 异常知识库_ExceptionKB — 分子动力学模拟_MolecularDynamics

> 写法与案例模板：`E:\RProject\docs\agents\异常知识库规范_ExceptionKb.md`（SSOT）。  
> 生产门禁/SOP：`文档_docs/复合物MD流水线_GromacsSop.md`；监控：`脚本_scripts/过程监控_monitorMdRun.sh`。

## 案例索引

| 序号 | 症状 | 判定要点（一锤定音） | 补救路径 | 案例 |
|------|------|----------------------|----------|------|
| 01 | 配体飞散/骨架展开（RMSD/COM 越界） | `gmx mindist` 最小镜像距离全程 <0.3nm 即假象 | 免疫门禁：mindist + 配体自RMSD；合并 BB RMSD 只记录 | [01](案例_Cases/01-PBC成像伪影假飞散.md) |
| 02 | 配体 RMSD 飞但骨架不动 | itp 零键原子数 >0 | PubChem 3D 重建+姿态对齐；零键熔断门禁 | [02](案例_Cases/02-配体拓扑零键幽灵原子.md) |
| 03 | mdrun Fatal（NaN/Fatal 字样） | `Started mdrun` 后仅 GMX_MAXBACKUP/gro 备份超限 | 清 `#md.gro.*` + `GMX_MAXBACKUP=-1` 续跑 | [03](案例_Cases/03-GMX_MAXBACKUP写gro超限Fatal.md) |
| 04 | 体系启动即 rc=127 | `command not found` + 合并/同步后出现 | `git show <旧版>` 找回函数定义 | [04](案例_Cases/04-合并丢函数rc127.md) |
| 05 | 开跑门禁 `EXCLUDE: long_gap` | REMARK 465/CA 缺口 ≥5 | 自动重搭换结构（登记表 UniProt 检索），≥5 缺口结构不跑 | [05](案例_Cases/05-蛋白缺口门禁EXCLUDE.md) |
| 06 | 开跑门禁 `pose contact clash` | 蛋白-配体重原子最近距 <0.05nm | 配体沿逃离方向微调 0.05Å/步；仍撞则换姿态/结构 | [06](案例_Cases/06-初态接触门禁clash.md) |
