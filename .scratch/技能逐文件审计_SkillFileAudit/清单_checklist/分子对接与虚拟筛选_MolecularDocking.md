# 清单：分子对接与虚拟筛选_MolecularDocking

**路径:** `03_药物计算_DrugDiscovery/分子对接与虚拟筛选_MolecularDocking`  
**范式:** `docs/agents/技能范式清单_SkillParadigm.md`  
**状态:** 已审  
**总评:** 合规  
**结构:** lines=132 docs=6 scripts=20 flags=none

## 技能说明

| 文件 | A1-A3 | B1-B4 | 判定 | 笔记 |
|------|-------|-------|------|------|
| `技能说明_分子对接与虚拟筛选_MolecularDocking.md` | PASS | PASS | 合规 | lines=132 |

## 文档_docs

| 文件 | SSOT单点 | 指针有效 | 判定 | 笔记 |
|------|----------|----------|------|------|
| `result拼图与detail导出定稿_CollageDetailExport.md` | 抽查 | 是 | 保留 |  |
| `中心位点方法登记_CenterSourceRegistry.md` | 抽查 | 是 | 保留 |  |
| `分子对接流水线规范_DockingPipelineSOP.md` | 抽查 | 是 | 保留 |  |
| `对接与交付约束_DockingFrozen.md` | 抽查 | 是 | 保留 |  |
| `对接盒子定心与定边_DockingBoxProtocol.md` | 抽查 | 是 | 保留 |  |
| `技术路线_AutoSite_AutoDockGPU.md` | 抽查 | 是 | 保留 |  |

## 脚本_scripts

| 文件 | 入口/可读 | Viz/Delivery | 判定 | 笔记 |
|------|-----------|--------------|------|------|
| `collage_palette.example.json` | 有 | 按技能 | 保留 |  |
| `collapse_pymol_console.py` | 有 | 按技能 | 保留 |  |
| `collect_nuli_viz_top10.py` | 有 | 按技能 | 保留 |  |
| `dock_export_common.py` | 有 | 按技能 | 保留 |  |
| `dock_summary_schema.py` | 有 | 按技能 | 保留 |  |
| `export_detail_png_from_pse.py` | 有 | 按技能 | 保留 |  |
| `plot_docking_affinity_heatmap.py` | 有 | 按技能 | 保留 |  |
| `plot_docking_ring_heatmap.py` | 有 | 按技能 | 保留 |  |
| `pymol_detail_export_hook.py` | 有 | 按技能 | 保留 |  |
| `pymol_dock_viz_standard.py` | 有 | 按技能 | 保留 |  |
| `run_nuli_ting_detail_combine.py` | 有 | 按技能 | 保留 |  |
| `化合物CID重命名_renameCompoundsToCid.py` | 有 | 按技能 | 保留 |  |
| `批量对接_runBatchAdgpu.py` | 有 | 按技能 | 保留 |  |
| `批量对接_runBatchDocking.py` | 有 | 按技能 | 保留 |  |
| `结构库修补_repairStructureLibrary.py` | 有 | 按技能 | 保留 |  |
| `结构库准备_prepareStructureLibrary.py` | 有 | 按技能 | 保留 |  |
| `结构库策展_curateStructureLists.py` | 有 | 按技能 | 保留 |  |
| `说明_README.md` | 有 | 按技能 | 保留 |  |
| `运行骨架_runSkeleton.R` | 有 | 按技能 | 保留 |  |
| `重算蛋白表中心_recenterProteinTable.py` | 有 | 按技能 | 保留 |  |

## 样例

| 路径 | C1-C5 | 判定 | 笔记 |
|------|-------|------|------|
| `01_样例_sample/` | PASS | 有 | DATA_SOURCE=是 |

## 总结

- 总评：`合规`
- flags：none
- 已做修改：见工单 Notes / 本轮脚本小修
- 子工单：无
