# 清单：分子动力学模拟_MolecularDynamics

**路径:** `03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics`  
**范式:** `docs/agents/技能范式清单_SkillParadigm.md`  
**状态:** 已审  
**总评:** 合规  
**结构:** lines=77 docs=2 scripts=10 flags=none

## 技能说明

| 文件 | A1-A3 | B1-B4 | 判定 | 笔记 |
|------|-------|-------|------|------|
| `技能说明_分子动力学模拟_MolecularDynamics.md` | PASS | PASS | 合规 | lines=77 |

## 文档_docs

| 文件 | SSOT单点 | 指针有效 | 判定 | 笔记 |
|------|----------|----------|------|------|
| `出图与交付约束_MdFigureStandards.md` | 抽查 | 是 | 保留 |  |
| `复合物MD流水线_GromacsSop.md` | 抽查 | 是 | 保留 |  |

## 脚本_scripts

| 文件 | 入口/可读 | Viz/Delivery | 判定 | 笔记 |
|------|-----------|--------------|------|------|
| `ligplot二维相互作用_runLigPlot2d.py` | 有 | 按技能 | 保留 |  |
| `mmpbsa模板_mmpbsa.in` | 有 | 按技能 | 保留 |  |
| `origin出图_plotMdOrigin.py` | 有 | 按技能 | 保留 |  |
| `origin隐藏FEL等值线_hideFelContours.c` | 有 | 按技能 | 保留 |  |
| `pymol轨迹快照_snapshotMd.pml` | 有 | 按技能 | 保留 |  |
| `整理样例目录_layoutMdSample.py` | 有 | 按技能 | 保留 |  |
| `补算必备分析_extraMdAnalysis.sh` | 有 | 按技能 | 保留 |  |
| `说明_README.md` | 有 | 按技能 | 保留 |  |
| `运行复合物MD_runComplexMd.sh` | 有 | 按技能 | 保留 |  |
| `运行骨架_runSkeleton.R` | 有 | 按技能 | 保留 |  |

## 样例

| 路径 | C1-C5 | 判定 | 笔记 |
|------|-------|------|------|
| `01_样例_sample/` | PASS | 有 | DATA_SOURCE=是 |

## 总结

- 总评：`合规`
- flags：none
- 已做修改：见工单 Notes / 本轮脚本小修
- 子工单：无
