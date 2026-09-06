# 样例目录说明 / Sample layout

> **范式状态：** `FROZEN`（2026-09-03）— 图册 `01`–`26`、Origin/PyMOL/LigPlot 交付件、分组 HTML 报告未经用户「解冻」不得改样式与结构。SSOT：[`../文档_docs/出图与交付约束_MdFigureStandards.md`](../文档_docs/出图与交付约束_MdFigureStandards.md)。

样例根按 DeliveryStandards；MD 另有工作目录与「一图一文件夹」覆盖条款。

```text
01_样例_sample/
  数据文件/                         # RAW only
    DATA_SOURCE.md
    01_复合物结构_3HTB.pdb
  代码文件/
    01_run_sample.R                 # 检查 xvg 后调分析
    02_分析出图_plotMdAnalysis.R
    结果文件/
      报告文件/                     # STATUS、HTML、审计、PlotQA
      01_骨架RMSD图/                # CSV + Origin PNG/SVG
      …
      25_轨迹快照图/                # PyMOL
      26_二维相互作用图/            # LigPlot
  工作文件_MdWork/3HTB/             # GROMACS 归档（按阶段分类）
    00_目录说明_Layout.md
    01_输入结构_Input/
    02_拓扑_Topology/               # topol.top、ligand.acpype（引擎原名）
    03_溶剂化离子_Solvation/
    04_最小化_EnergyMin/
    05_NVT平衡_Nvt/
    06_NPT平衡_Npt/
    07_生产轨迹_Production/         # md.tpr / md_center.xtc
    08_轨迹分析_Analysis/           # 中英对照 xvg
    09_结合自由能_MmGbsa/
    10_轨迹快照_Snapshots/
    99_运行日志_Logs/
```

- 交付文件名：`{NN}_{中文}_{EnglishPascal}`（例：`01_骨架RMSD_RmsdBackbone.png`）
- GROMACS 引擎文件（`topol.top`、`md.tpr`、`-deffnm`）**不改名**，只按阶段入夹
- 分析产物 xvg / 快照 PDB / MM-GBSA dat 用中英对照名

规范 SSOT：`00_基础_Foundation/统一交付规范_DeliveryStandards/文档_docs/样例目录与命名_SampleLayoutNaming.md`  
本技能覆盖：`技能说明_分子动力学模拟_MolecularDynamics.md` §9.7

GROMACS 在扁平临时目录跑完后归档：

```bash
python 脚本_scripts/整理样例目录_layoutMdSample.py
```

分析出图：

```bash
Rscript 代码文件/01_run_sample.R
```

只更新 HTML 报告（不重跑模拟、不重画 Origin）：

```bash
Rscript 代码文件/03_写样例报告_writeSampleReport.R
```

报告金标：`代码文件/结果文件/报告文件/样例报告_SampleReport_v1.html`  
版式范式：`00_基础_Foundation/统一交付规范_DeliveryStandards/文档_docs/样例报告范式_SampleReportParadigm.md`

只搬结果目录、不重画 Origin：

```bash
python 脚本_scripts/origin出图_plotMdOrigin.py --layout-only
```
