# MD 真实数据落地（解除分子动力学样例 BLOCKED）

标签: 已完成（2026-08-30 E2E 跑通，STATUS=REAL）
创建: 2026-08-30
来源: 用户指令「帮我补齐，尤其是拓扑」；接续 GROMACS 环境安装（d05d957）

## 目标

3HTB（T4 lysozyme L99A/M102Q + JZ4 配体，RCSB 真实数据）跑通
pdb2gmx → GAFF2 配体拓扑 → 溶剂化 → 离子 → EM → NVT/NPT → 1 ns 生产
→ RMSD/RMSF/氢键/回旋半径 → R 出版级出图 + 审计 REAL，并把 SOP 沉淀进技能说明。

## 环境决策记录

| 决策点 | 结论 | 理由 |
|--------|------|------|
| MD 引擎 | GROMACS 2023.3（WSL2 Ubuntu-24.04 @ E:\WSL\Ubuntu） | 用户指定，免费开源 |
| 配体拓扑 | AmberTools(antechamber/parmchk2/tleap) + acpype | GAFF2 经典路线；ChemDraw/Chem3D 不做拓扑，Gaussian 只能替代电荷步 |
| 包管理 | 用户拒 conda → 试 UV；antechamber 无 PyPI → 官网表单下载 88 B/s 不可用 → 用户授权「从大局」用 conda 生态 → Miniforge(清华镜像) + mamba + tuna conda-forge | 稳定性最好，官方推荐 |
| UV 保留 | /opt/venv-md（acpype 已装）作备用/轻量 Python 层 | 用户偏好 UV |

## 已修复的坑（回填 SOP 用）

1. Windows 写出的 .sh/.mdp 是 CRLF → WSL bash/grompp 报错；须转 LF。
2. OpenBabel 在中文 Windows 把 mol2 分子名写成 GBK 中文路径 → tleap 输出非 UTF-8 → acpype UnicodeDecodeError；须把 mol2 第 2 行改为 ASCII 残基名。
3. ambermd.org 表单须 multipart/form-data（curl -F），-d 会挂起。
4. Ubuntu 24.04 apt 无 ambertools 包。

## 进度

- [x] WSL2 + GROMACS 2023.3（d05d957）
- [x] 3HTB.pdb 下载 + DATA_SOURCE 登记
- [x] mdp 模板 5 件（ions/em/nvt/npt/md）
- [x] 流水线脚本 运行复合物MD_runComplexMd.sh（幂等分段）
- [x] md 环境（ambertools+acpype，tuna 镜像）重建（22 s）
- [x] acpype 配体拓扑 + 复合物组装 + 溶剂化/离子/EM 通过
- [x] NVT/NPT/0.2 ns 生产（实测 22.98 ns/day，全程 ~24 min；早前"慢"是 WSL 时钟漂移误判）
- [x] R 出图 + 审计 REAL + STATUS 翻 REAL（四图 PlotQA 全 PASS，目视通过）
- [x] 技能说明 §9 详细 SOP + §10 环境登记更新
- [x] 清理 BLOCKED/toy 残留（柱状图_BlockedContract、toy_counts/meta、契约阻塞桩 csv）
- [ ] 增量提交

## 追加踩坑（2026-08-30 晚）

5. grompp ions 步需 `-maxwarn 1`（净电荷警告先于中和）。
6. `gmx select` 赋值命名语法 2023.3 不可用 → 全程默认组，免索引文件。
7. mamba 须配 .condarc custom_channels 指向 tuna，否则回落官方源超时。
8. WSL 时钟漂移导致 mdrun 进度时间戳不可信，须用实测步速。
9. 6 核实测 ~14–23 步/s（3.3 万原子）→ 演示 NS=0.2。
