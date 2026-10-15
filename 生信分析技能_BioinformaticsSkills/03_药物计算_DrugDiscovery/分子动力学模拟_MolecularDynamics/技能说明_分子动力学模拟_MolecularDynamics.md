---
name: bioinfo-molecular-dynamics
description: >-
  分子动力学模拟 / MolecularDynamics：对接后稳定性/结合自由能；山水 M17；勿假装纯 R 跑 MD。
  工具栈：GROMACS GPU(CUDA)、UV(md-venv: acpype/gmx_MMPBSA)、conda env md-tools(仅 AmberTools)。
  触发：分子动力学, GROMACS, MD, RMSD, acpype, MM-GBSA, AmberTools, 跑MD, 生产MD。
  Agent 默认：用户说「跑 MD」= 生产级 NS≥100+监控；开跑须过 SOP §9.0.2（mol2 几何、初态接触、EM 收敛）。仅明示「烟测/测试」才短轨迹。交付范式 FROZEN（2026-09-03）。
---

# 分子动力学模拟 / MolecularDynamics

> **出图与交付 SSOT：** [`文档_docs/出图与交付约束_MdFigureStandards.md`](文档_docs/出图与交付约束_MdFigureStandards.md) — **`FROZEN`（2026-09-03）**。改图册序/Origin recipe/报告结构前须你说「解冻」。  
> **计算/环境 SSOT：** [`文档_docs/复合物MD流水线_GromacsSop.md`](文档_docs/复合物MD流水线_GromacsSop.md)（§9 流程、§9.8 安装、§10 本机登记）。本入口不复述长 SOP。  
> 登记：[`已跑通范式登记_FrozenParadigms.md`](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/已跑通范式登记_FrozenParadigms.md)。

## 1. 数据来源

实验复合物优先；没有目标配体共晶时用同口袋近缘结构作参照；两者都没有才用对接姿态。判据与口袋限制见 SOP §9.0.1。  
**原始数据命名：** 初态结构须带来源（如 `PDB_`、`Upstream_` 对接姿态）→ DeliveryStandards SampleLayoutNaming **§2.1**。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。  
raw 文件/夹名含来源库；禁止无来源的 `输入/`、`md_in/`。  
选蛋白先过 SOP **§9.0.3**（大段 loop 缺失则换结构）。开跑再过 **§9.0.2**（mol2 几何、接触、EM 收敛）。溶剂化 / 电荷中和 / EM / NVT / NPT 不证明对接姿态正确。

## 3. 何时选用本技能

- 对接后稳定性/结合自由能；山水 M17；勿假装纯 R 跑 MD
- 山水用途层标签：药物-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。高斯不是必备（电荷默认可 AM1-BCC）。

## 4. 数据处理方法

先定初态场景（SOP §9.0.1：A1 共晶 / A2 近缘 / A3 对接 / A4 配位金属），再过 §9.0.2 门禁，然后溶剂化 → 中和 → EM → NVT → NPT → 分块生产。第 1 个生产块由监控筛选；飞出不从该检查点续跑。细节只维护在 SOP。

## 5. 工具链（2026-10-09 现行）

| 步骤 | 工具 | 作用 | 备注 |
|------|------|------|------|
| 激活 | `source ~/activate-md.sh` | 拼 PATH | **每次跑 MD 前** |
| Python | UV `~/md-venv` | acpype、gmx_MMPBSA、impi-rt | Python≥3.12；**不用 conda 管 Python** |
| 配体拓扑引擎 | conda env `md-tools` | AmberTools（antechamber 等） | 仅二进制隔离；禁止往里 pip acpype |
| 动力学 | `~/gromacs-gpu/bin/gmx` | GROMACS **2024.4 CUDA** | 源码编；host **gcc-12**（Ubuntu 24.04） |
| 分析 CSV | R `bio3d` 等 | xvg→表 | |
| 出图 | Origin（`origin出图_plotMdOrigin.py`） | DPI≥600 PNG+SVG | 分析曲线/FEL/能量柱必须 Origin |

安装步骤见 SOP §9.8；安装包在本技能 `环境安装_EnvSetup/`（联接 `E:\md_kit`）。

## 6. 数据可视化

RMSD/RMSF 曲线；**DPI≥600；SVG+PNG；图面 English；防遮挡**。本技能出图 **FROZEN**（见出图约束）。

## 7. 数据结果解读

力场、时长和有无熵项决定能说什么。短轨迹（如 0.2 ns）禁止写成发表级 ΔG / 长期稳定结合。

报告金标：`01_样例_sample/代码文件/结果文件/报告文件/样例报告_SampleReport_v1.html`

## 8. 能否结合其它生信

分子对接、蛋白结构；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 蛋白-配体复合物 MD 流水线

**执行 SOP（强制）：** [`文档_docs/复合物MD流水线_GromacsSop.md`](文档_docs/复合物MD流水线_GromacsSop.md)。  
**出图/交付 FROZEN：** [`文档_docs/出图与交付约束_MdFigureStandards.md`](文档_docs/出图与交付约束_MdFigureStandards.md)。

### 9.0 Agent 默认（2026-10-13 确认）

| 用户说法 | Agent 动作 |
|----------|------------|
| 「跑 MD / 开 MD / 生产 / 正式」或未指定时长 | **立即**启动生产：`NS=100`（或用户指定 ≥100）、`CHUNK_NS=1`、`MONITOR=1`；输入齐则 **nohup 后台跑**，不得只备输入就停下 |
| 「烟测 / 测试 / demo / 0.2 ns」 | 才允许短轨迹（`NS≤1` 或 `04_烟测_3HTB.sh`） |

禁止用示例里的 `NS=1` 当课题默认。细则与变量表见 SOP §9.0。

```bash
wsl -d Ubuntu-24.04 -- bash -lc '
  source ~/activate-md.sh
  cd <工作目录> && \
  LIGAND_RES=JZ4 NET_CHARGE=0 NS=100 CHUNK_NS=1 MONITOR=1 \
  bash <技能根>/脚本_scripts/运行复合物MD_runComplexMd.sh . protein.pdb jz4_h.mol2
'
```

烟测（须用户明示）：`source ~/activate-md.sh && bash /mnt/e/md_kit/04_烟测_3HTB.sh` → 期望 `SMOKE PASS` + `CUDA acceleration`。

**开跑门禁：** SOP §9.0.2 / §9.0.3。**过程监控：** SOP §9.5.1。飞出后**自动重搭一轮**（共晶/近缘/无大段缺环）再跑；仍失败则停（§9.0.1「飞出后的队列」）。中文邮件写明原因与是否重试。不从坏 `md.cpt` 续跑。口袋不要撑开再对接。过程草图在 `monitor/`；交付图仍为样例 **01–26**。

## 样例验证

样例：`01_样例_sample/`（**范式 FROZEN 2026-09-03**）。MD 计算侧见上述 SOP。

**异常判定与补救：** `异常知识库_ExceptionKB/`（案例索引在该目录 README；写法 SSOT：`docs/agents/异常知识库规范_ExceptionKb.md`）。
