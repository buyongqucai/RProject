# 01 多对多 3×4 对接批次（AutoDock-GPU）

标签: 已完成
优先级: frontier（无前置）

## 背景
用户新方案：多对多分子对接批次（不得 1 对 1）。组合定义（用户指定）：
- 化合物 ×3（网络图 Degree 前三）：quercetin、luteolin、kaempferol
- 蛋白 ×4（PPI Degree 前四）：PCNA、DNMT1、ESR2、FOS
- 全组合 12 对；其中 2 对复用旧批次原样引用（quercetin×FOS −8.20 任务 01；luteolin×PCNA −4.60 无任务号）；新跑 10 对。

## 任务
1. 新跑 10 对 AutoDock-GPU（AD4，--nrun 20，3 种子 1/7/42 取均值±SD）；任务目录续接 序号文件夹/13–22。
2. 盒子定心按决策树（技术路线_AutoSite_AutoDockGPU §2），每对强制登记 center_source（CenterSourceRegistry）。
3. 产出：多对多3x4_对接全表/汇总、summary_adgpu_多对多3x4、矩阵_结合能_多对多3x4.csv。
4. 已有 2 对不重跑不覆盖；失败对停在该对并如实报告，不编造。

## 执行记录
- 2026-10-15：环境补齐（FROZEN §1 允许）：AutoDock-GPU v1.6 → E:\AutoDock-GPU\；AutoGrid4 4.2.6（WSL apt）；P2Rank 2.5.1 → E:\p2rank\（AutoSite 未装，走回退链）。
- 受体复用现有对接工作区（E:\RProject\_dock_cmp\STD_*.rec.pdb），ADT prepare_receptor4 重加 Gasteiger 电荷；PCNA 剔除非目标 FEN1 肽链 B。
- 批次脚本：06_分子对接\代码文件\21_多对多3x4批量对接_ADGPU.py（引擎 cwd：E:\RProject\_dock_m2m，ASCII）。
- 2026-10-15：10 对新跑完成（任务 13–22，均 3 种子 1/7/42、nrun=20，全部负值）；2 对复用原样引用。
  - center_source：DNMT1/ESR2 = cocrystal_meeko（BGC:A:702 / ETC:A:600）；PCNA = p2rank rank2（rank1 被 Q5 距界面 13.8 Å 否决，rank2 距 PIP 界面 4.1 Å）；FOS = annotated_site（p2rank rank1/2 均 Q5 否决，落 FOS 碱性区–DNA 界面残基 F:144–158）。
  - 产出：多对多3x4_对接全表/汇总、summary_adgpu_多对多3x4、矩阵_结合能_多对多3x4.csv（结果文件 + 交付文件 各一份）。
