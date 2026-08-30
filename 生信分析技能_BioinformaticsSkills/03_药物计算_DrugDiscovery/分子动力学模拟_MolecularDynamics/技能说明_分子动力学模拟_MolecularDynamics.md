---
name: bioinfo-molecular-dynamics
description: >-
  分子动力学模拟 / MolecularDynamics：对接后稳定性/结合自由能；山水 M17；勿假装纯 R 跑 MD。工具：bio3d, ggplot2, GROMACS, Amber。
  触发：分子动力学, GROMACS, MD, RMSD。
---

# 分子动力学模拟 / MolecularDynamics

## 1. 数据来源

对接复合物或已知复合物

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组/标注来自官方或实验记录；禁止编造结果数字。

## 3. 何时选用本技能

- 对接后稳定性/结合自由能；山水 M17；勿假装纯 R 跑 MD
- 山水用途层标签：药物-基因

不适用：输入类型不匹配或仅需其它技能可覆盖的步骤。

## 4. 数据处理方法

溶剂化→最小化→平衡→生产→RMSD/RMSF/氢键/MM-PBSA

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `bio3d` | 核心 R 包 | |
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `GROMACS` | CLI 工具 | 非 R |
| 上游/主分析 | `Amber` | CLI 工具 | 非 R |
| 出图 | `ggplot2` + 出版级出图_PublicationPlot.R | DPI≥600 | 强制可视化规范 |

## 6. 数据可视化

RMSD/RMSF 曲线；**DPI≥600；SVG+PNG；图面 English；防遮挡**。

**对齐高分期刊范式：** 遵循 [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)；近邻折线/箱线。网药视觉 **FROZEN**，勿改。

## 7. 数据结果解读

力场与时长影响结论；MM-PBSA 有近似

## 8. 能否结合其它生信

分子对接、蛋白结构；出图强制 [统一可视化规范](../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)。

## 9. 蛋白-配体复合物 MD 全流程 SOP（GROMACS + AmberTools/acpype）

> 实现脚本：`脚本_scripts/运行复合物MD_runComplexMd.sh`（幂等分段，断点续跑）；
> mdp 模板：`脚本_scripts/mdp模板_mdps/{ions,em,nvt,npt,md}.mdp`（`__LIG__` 占位符由脚本替换为配体残基名）。
> 验证体系：3HTB（T4 lysozyme L99A/M102Q + JZ4），GROMACS 官方教程（Lemkul）标准流程。

### 9.0 一键调用

```bash
wsl -d Ubuntu-24.04 -- bash -c "cd <工作目录> && \
  LIGAND_RES=JZ4 NET_CHARGE=0 NS=1 \
  bash 运行复合物MD_runComplexMd.sh . protein.pdb jz4_h.mol2"
```

| 环境变量 | 默认 | 说明 |
|----------|------|------|
| `LIGAND_RES` | JZ4 | 配体残基名（≤4 字符 ASCII，须与 mol2 一致） |
| `NET_CHARGE` | 0 | 配体净电荷（antechamber -nc） |
| `NS` | 1 | 生产时长 ns；演示可 0.2，正式 ≥100 |
| `ACPYPE_BIN` | /opt/miniforge3/envs/md/bin | acpype/AmberTools 所在目录 |

### 9.1 输入准备（Windows 侧，OpenBabel）

1. 从复合物 PDB 分离：`ATOM` 记录 → `protein.pdb`；配体 `HETATM`（按残基名过滤）→ `lig.pdb`。结晶添加剂（PO4/BME 等）与晶格水在此步剔除。
2. 配体加氢 + 部分电荷：`obabel lig.pdb -O lig_h.mol2 -h --partialcharge gasteiger`。
3. **mol2 第 2 行分子名必须是 ASCII 残基名**（如 `JZ4`）：中文 Windows 下 OpenBabel 会把 GBK 编码的中文路径写进分子名，导致下游 tleap 输出非 UTF-8、acpype 报 `UnicodeDecodeError`。

### 9.2 配体拓扑（GAFF2，acpype → AmberTools）

`acpype -i lig_h.mol2 -n <净电荷> -a gaff2 -b ligand` 依次调用：
**antechamber**（GAFF2 原子类型指认 + AM1-BCC 电荷，sqm 半经验量化计算）→ **parmchk2**（缺失参数补全）→ **tleap**（构建校验）→ 产出 `ligand.acpype/ligand_GMX.itp` + `ligand_GMX.gro`。

- **职责边界**：ChemDraw/Chem3D 只画结构、不做拓扑；Gaussian 只能替代电荷计算步（RESP），不能产出力场拓扑；antechamber 不可被它们替代。
- acpype 的 `moleculetype` 名取自 `-b` 基名而非残基名 → 脚本自动 awk 改名为 `$LIGAND_RES` 对齐 `topol.top`。

### 9.3 蛋白拓扑与复合物组装

1. `gmx pdb2gmx -f protein.pdb -ff amber99sb-ildn -water tip3p`（配体 HETATM 必须先分离，pdb2gmx 不处理配体）。
2. 合并坐标：protein.gro + ligand_GMX.gro → complex.gro（脚本内嵌 Python 保格式合并，自动换算总原子数）。
3. `topol.top`：在蛋白 forcefield include 之后插入 `#include "ligand.acpype/ligand_GMX.itp"`，`[ molecules ]` 追加 `JZ4  1`。

### 9.4 盒子、溶剂化、离子

`editconf -bt dodecahedron -d 1.0` → `solvate -cs spc216` → `grompp ions.mdp` → `genion -neutral -conc 0.15`（0.15 M NaCl 生理盐浓度 + 电荷中和）。

- **`-maxwarn 1` 仅用于 ions 步**：加离子前体系净电荷非零是预期状态，grompp 默认 0 警告即 Fatal；中和后的后续 grompp 不加该开关（保留警告保护）。
- **防重入**：solvate/genion 会向 topol.top 追加 SOL/NA/CL 行，脚本重跑前先 sed 剔除旧行，否则坐标数与拓扑不匹配（33518 vs 64400 型报错）。

### 9.5 最小化与平衡

| 阶段 | mdp | 要点 |
|------|-----|------|
| EM | em.mdp | steep 5000 步，emtol 1000 kJ/mol/nm |
| NVT | nvt.mdp | 100 ps，V-rescale 300 K，位置限制 |
| NPT | npt.mdp | 100 ps，+ Parrinello-Rahman 1 bar |
| 生产 | md.mdp | `NS`×10³/0.002 步，2 fs，LINCS 约束 H 键 |

温控用**默认组** `Protein / <配体残基名> / Water_and_ions`（grompp 自动为非蛋白分子建组），**不需要索引文件**——GROMACS 2023.3 的 `gmx select` 不接受 `名称 = 表达式` 赋值语法，勿走该路线。

### 9.6 PBC 校正与分析

`trjconv -pbc mol -center -ur compact`（蛋白居中）→ 默认组非交互分析：

| 指标 | 命令 | 输出 |
|------|------|------|
| RMSD | `gmx rms -tu ns`（Backbone 拟合+计算） | rmsd_backbone.xvg |
| RMSF | `gmx rmsf -res`（C-alpha） | rmsf_calpha.xvg |
| 氢键 | `gmx hbond -num`（Protein ↔ 配体） | hbond_num.xvg（3 列：time/氢键数/接触对数） |
| Rg | `gmx gyrate`（Protein） | gyrate.xvg |
| SASA | `gmx sasa -tu ns`（Protein） | sasa.xvg |
| FEL | R 内 kde2d(RMSD, Rg) → ΔG = −kT ln(P/Pmax) | 由出图脚本算 |
| 结合自由能 | gmx_MMPBSA（GB igb=5 + idecomp=1 逐残基分解） | FINAL_RESULTS/FINAL_DECOMP_MMPBSA.dat |

**MM-GBSA（gmx_MMPBSA）**：模板 `脚本_scripts/mmpbsa模板_mmpbsa.in`；索引 `printf 'q\n' | gmx make_ndx -f md.tpr -o index.ndx`（默认组编号 Protein=1、配体如 JZ4=13，以实际列表为准）；
`mamba run -n md gmx_MMPBSA -O -i mmpbsa.in -cs md.tpr -ct md_center.xtc -ci index.ndx -cg 1 13 -cp topol.top -o FINAL_RESULTS_MMPBSA.dat -do FINAL_DECOMP_MMPBSA.dat`。
输出单位为 **kcal/mol**（出图脚本 ×4.184 转 kJ/mol）；结尾自动拉起 gmx_MMPBSA_ana 报 PyQt5 缺失属无害（CLI 流程不用 GUI）。熵项（nmode/QT）演示不算，正式研究再开。

### 9.7 R 出图与交付（含 Origin 数据导出）

`01_样例_sample/代码文件/分析出图_plotMdAnalysis.R`：解析 xvg + MM-GBSA .dat → CSV（结果文件）→ **必备八图**：RMSD / RMSF / 氢键 / Rg / SASA / FEL(等值线) / 结合自由能分解(堆叠柱) / 逐残基贡献 Top15(柱+误差棒)（VizStandards：DPI≥600、PNG+SVG、图面英文、PlotQA 逐图审核）→ 审计 `data_provenance=REAL` → 报告 + STATUS。

**Origin 协同**：用户侧 Origin 装于 `E:\Origin`；出图脚本同步把每图数据以英文列名 CSV 导出到 `E:\Origin_Data\<项目名>\`（样例为 `E:\Origin_Data\3HTB\`），供 Origin 复绘/精修；R 图为规范交付件，Origin 图为用户自选加工。

### 9.8 环境安装 SOP（2026-08-30 实测）

1. WSL2：`wsl --install -d Ubuntu-24.04 --location E:\WSL\Ubuntu`（虚拟磁盘落 E 盘）。
2. GROMACS：`apt install gromacs`（2023.3；GPU 加速需源码构建，后续议题）。
3. 拓扑工具链（**关键决策**）：antechamber/tleap 无 apt、无 PyPI，官网源码表单下载在国内仅 ~88 B/s 不可用 → 用 **Miniforge（清华镜像）+ mamba + tuna conda-forge** 建 `md` 环境：`mamba create -n md -c conda-forge ambertools acpype python=3.11`（~22 s 完成）。
   - `.condarc` 须配 `custom_channels: conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud`，否则 mamba 仍回落 conda.anaconda.org 超时。
   - UV 环境 `/opt/venv-md`（acpype pip 版）保留作轻量 Python 层备用；UV 无法提供 antechamber 二进制。

### 9.9 踩坑登记（回填提醒）

1. Windows 写出的 .sh/.mdp 是 CRLF → WSL bash/grompp 报错；**必须转 LF**。
2. mol2 分子名 GBK 中文 → acpype UnicodeDecodeError（见 9.1.3）。
3. ambermd.org 表单须 `multipart/form-data`（curl -F）；`-d` 会挂起。
4. Ubuntu 24.04 apt 无 ambertools 包；PyPI 无 antechamber。
5. solvate/genion 重复追加 topol.top（见 9.4）。
6. ions 步 grompp 需 `-maxwarn 1`（见 9.4）。
7. `gmx select` 赋值命名语法在 2023.3 不可用 → 全程默认组（见 9.5）。
8. 性能参考：WSL2 6 核约 14–23 步/s（3.3 万原子），1 ns ≈ 6–10 h；演示用 `NS=0.2`，正式研究 ≥100 ns 且需 GPU 构建。

## 10. 运行环境登记（2026-08-30）

| 项 | 值 | 备注 |
|----|----|------|
| GROMACS | 2023.3（Ubuntu apt `gromacs` 2023.3-1ubuntu3） | mixed precision / thread_mpi / SSE4.1，CPU 通用构建 |
| 运行层 | WSL2 `Ubuntu-24.04`（WSL 2.7.12.0） | 虚拟磁盘 `E:\WSL\Ubuntu\ext4.vhdx`（数据落 E 盘） |
| Windows 调用 | `wsl -d Ubuntu-24.04 -- gmx <args>` | 默认 root；E 盘文件经 `/mnt/e/...` 访问 |
| 拓扑工具链 | Miniforge `/opt/miniforge3` + env `md`：AmberTools（antechamber/parmchk2/tleap/sqm）+ acpype，python 3.11 | 清华 tuna 镜像安装；用户拒 conda 官网慢源 → 镜像方案 |
| 自由能 | 同 env `md`：gmx_MMPBSA 1.5.3（conda-forge） | GB/PB + 逐残基分解；gmx_MMPBSA_ana GUI 需 PyQt5（未装，CLI 不受影响） |
| UV 备用 | `/opt/venv-md`（uv venv，pip 版 acpype） | 轻量 Python 层；不含 antechamber |
| Origin | `E:\Origin`（Windows 侧，用户已装） | 项目数据约定放 `E:\Origin_Data\<项目>\`；出图脚本自动导出 |
| GPU | RTX 4060 已对 WSL2 可见（`nvidia-smi` 通过） | apt 版不含 CUDA；GPU 加速需源码构建（后续议题） |
| 配套（Windows 侧已装） | PyMOL `E:\pymol`、OpenBabel 3.1.1、Vina、MGLTools、LigPlot+ | 对接/格式转换/可视化沿用 |

**BLOCKED 已解除（2026-08-30）**：3HTB 真实数据 E2E 跑通——pdb2gmx(amber99sb-ildn/tip3p) + acpype/GAFF2(JZ4) → 溶剂化/0.15 M NaCl → EM/NVT/NPT → 0.2 ns 生产（22.98 ns/day）→ RMSD 0.084 nm / Rg 1.65 nm / SASA ~91 nm² / 氢键 0–2 个；MM-GBSA ΔG_bind = −105.2 kJ/mol（GB igb=5，21 帧，未含熵）。必备八图 PlotQA 全 PASS、审计 REAL、`STATUS=REAL`；Origin 数据同步导出 `E:\Origin_Data\3HTB\`。1 ns 及以上将 `NS` 调大重跑即可（幂等续跑）。

## 样例验证

样例：`01_样例_sample/`（STATUS=REAL，2026-08-30）。入口 `代码文件/run_sample.R` → 检查 xvg 就绪后调 `分析出图_plotMdAnalysis.R`；MD 计算侧 SOP 见 §9。
