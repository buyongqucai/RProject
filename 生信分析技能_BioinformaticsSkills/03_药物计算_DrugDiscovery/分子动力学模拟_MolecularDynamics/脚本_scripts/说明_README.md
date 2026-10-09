# 分子动力学模拟 · 脚本

**计算/环境 SSOT：** 上级 [`文档_docs/复合物MD流水线_GromacsSop.md`](../文档_docs/复合物MD流水线_GromacsSop.md)  
**出图 FROZEN：** [`文档_docs/出图与交付约束_MdFigureStandards.md`](../文档_docs/出图与交付约束_MdFigureStandards.md)

## 跑计算前

```bash
source ~/activate-md.sh   # UV md-venv + conda md-tools + ~/gromacs-gpu
```

## 入口脚本

| 脚本 | 用途 |
|------|------|
| `运行复合物MD_runComplexMd.sh` | 主流程；生产分块 `-cpi`；`MONITOR=1` 块间监控 |
| `过程监控_monitorMdRun.sh` | COM/RMSD/T/势能阈值；可选 MM-GBSA>0 即停；`monitor/` 草图 |
| `补算必备分析_extraMdAnalysis.sh` | 补算 RMSD/能量等 |
| `mdp模板_mdps/` | em/nvt/npt/md/ions |
| `mmpbsa模板_mmpbsa.in` | gmx_MMPBSA（调用 `~/md-venv/bin/gmx_MMPBSA`） |
| `origin出图_plotMdOrigin.py` | Origin 出图（Windows） |
| `整理样例目录_layoutMdSample.py` | 样例目录归档 |

骨架：`运行骨架_runSkeleton.R`（若存在）。安装见 SOP §9.8；准备包烟测 `E:\md_kit\04_烟测_3HTB.sh`。
