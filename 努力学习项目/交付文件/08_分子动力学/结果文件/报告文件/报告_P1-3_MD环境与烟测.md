# 报告：P1-3 MD 环境核验、构建与烟测

> 日期：2026-10-08 ｜ 依据 SOP：`生信分析技能…/文档_docs/复合物MD流水线_GromacsSop.md` §9.8–9.10
> 环境包（E 盘）：`准备文件/MD环境/`（README + 01 安装ps1 + 02 引导sh + 烟测产物）

## 1. 本地环境勘察结论

| SOP §10 登记项（2026-08-30） | E 盘实勘（2026-10-08） |
|---|---|
| WSL2 Ubuntu `E:\WSL\Ubuntu\ext4.vhdx` | **未找到**（E 盘无 WSL 目录、无 vhdx） |
| GROMACS 2023.3（apt，WSL 内） | 随 WSL 缺失（WSL 内部不可见，若 WSL 在 C 盘默认位置请先 `wsl -l -v` 确认） |
| Miniforge env `md`（AmberTools/acpype/gmx_MMPBSA） | 随 WSL 缺失 |
| Origin `E:\Origin`、LigPlus `E:\LigPlus` | **未找到**（出图层，不阻塞计算） |
| 对接栈 vina/OpenBabel/pymol/mgltools | ✅ 在位 |

**判定：本地 MD 环境需要（重新）构建** → 已产出 `准备文件/MD环境/` 安装包（完全按 SOP §9.8 规格：
WSL 落 E 盘、apt gromacs、清华镜像 Miniforge、`mamba create -n md …`）。
WSL 的安装与发行版初始化只能在 Windows 侧执行（沙盒无法跑 Windows 命令），**两步脚本交给你运行**，
运行后回写 SOP §10。

## 2. 沙盒同规格环境（已构建）

| 组件 | 版本 | 说明 |
|---|---|---|
| GROMACS | **2026.3**（conda-forge） | SOP 登记为 2023.3(apt)；版本差异已在注意事项登记 |
| acpype | 2026.9.4 | 调用 AmberTools antechamber/parmchk2/tleap/sqm |
| AmberTools | 随 conda-forge | GAFF2 + AM1-BCC 链路 |
| 力场 | amber99sb-ildn.ff + tip3p | GROMACS 自带，`pdb2gmx` 验证在位 |

## 3. 烟测（3HTB + JZ4，SOP 验证体系，smoke 参数）

参数：EM 400 步 / NVT 300 步 / NPT 300 步 / 生产 0.002 ns（1000 步），0.15 M NaCl，其余按 SOP mdp 模板。
直接调用流水线脚本 `运行复合物MD_runComplexMd.sh`（未改技能原件；mdp 用 smoke 副本经 `MDP_DIR` 传入）。

**结果：PASS，全链路 24 秒跑完（exit=0，`DONE:` 完成行）**，分段核验：

| 阶段 | 结果 |
|---|---|
| 01 acpype 配体拓扑 | ✅ 22 原子、GAFF2 类型、电荷和 = 0、`moleculetype=JZ4` 改名成功 |
| 02 pdb2gmx | ✅ amber99sb-ildn/tip3p |
| 03–04 合并/溶剂化/genion | ✅ 33,382 原子；SOL/NA/CL 各追加一次（无防重入问题） |
| 05 EM | ✅ 运行；**未达 Fmax<1000（烟测 400 步所限，正式跑用模板 5000 步）** |
| 07–08 NVT/NPT | ✅ 各 300 步完成（**烟测≠平衡**） |
| 09 生产 | ✅ 1000 步 / 2.0 ps 完成 |
| 10 分析 | ✅ rmsd_backbone / rmsf_calpha / gyrate 生成 |
| 补算脚本 | ✅ `DONE_EXTRA_ANALYSIS`：蛋白/配体/复合物三线 RMSD、质心距离、NVT/NPT/生产能量曲线、快照 ×3 |
| hbond | ⚠️ 无输出——**JZ4 无氢键供/受体**（gmx 日志：`JZ4 has 0 acceptors and 0 donors`，脚本 `|| true` 设计内；与 SOP 登记「氢键 0–2」一致） |
| sasa | 主脚本不含（SOP 归入补算/分析层），非缺失 |

烟测产物（xvg/日志/topol.top/run_meta.json，948 KB）：`准备文件/MD环境/烟测产物/`。

## 4. 注意事项（回写 SOP 候选项）

1. **GROMACS 2026.3 vs 2023.3**：本次烟测全链路无行为差异；正式跑若用 apt 2023.3（按 README 装法），
   SOP 踩坑 7（`gmx select` 语法）仍以 2023.3 为准。
2. 烟测参数（400/300/300/1000 步）**只验链路不验物理**；正式 MD 必须恢复 mdp 模板原步数，生产 `NS≥100`。
3. mol2 第 2 行已按 SOP §9.1.3 改 `JZ4`（obabel 默认写文件名）——烟测再次验证此坑真实存在。
4. 结论边界：本烟测为**环境/流水线验证**，不产出任何 MD 科学结论；`NS≥0.2` 的演示与 `≥100 ns` 的
   正式计算在本机环境装好后按 SOP 执行。

## 5. 状态与分工

- ✅ E 盘勘察、沙盒环境构建、3HTB 链路烟测、环境包交付（本报告）
- ⏳ 你：`01_安装WSL与检查.ps1` → `02_环境内引导_bootstrap_md_env.sh` → README 第 3–4 步验证烟测 → 回写 SOP §10
- ⏳ 之后（如启动 P1-3 正式部分）：Top 对 100 ns + gmx_MMPBSA（出图按 FROZEN 走 Origin）

## 6. UV 版执行记录（2026-10-08 追加：环境配置与烟测计划实跑）

**可执行部分全部实跑，结果如下：**

| 执行项 | 结果 |
|---|---|
| 脚本静态校验 | ✅ 01/02/03 三脚本 `bash -n`/无 CRLF 全通过 |
| UV 环境（02 §3 同参数） | ✅ uv 0.12.13 → `uv venv --python 3.12` → acpype 2026.9.4 运行 OK、openbabel 3.1.0（wheel）加载 OK、gmx_MMPBSA 1.7.0 装齐 |
| **实测坑 A** | ❌→✅ 初版 `--python 3.11` 装不上：acpype≥2026.9.4 要求 **Python≥3.12** → 脚本/SOP/README 已改 3.12 |
| **实测坑 B** | ❌→✅ gmx_MMPBSA `--help` 启动即崩（`cannot load MPI library`，mpi4py 无 libmpi）→ 补 `impi-rt 2021.18.1` 后 **exit=0** → 三处文档已改 |
| AmberTools 方案B 命令 | ⚠️ tuna 镜像可达、命令执行至下载阶段成功；沙盒磁盘一度 100% 未建重复前缀（antechamber 用已有前缀验证 PATH 机制）。**用户 WSL 无此限制** |
| **UV 版 3HTB 烟测** | ✅ **PASS（26 秒，exit=0，DONE）**：`ACPYPE_BIN=~/md-venv/bin`（acpype 来自 UV venv）+ PATH 上的 antechamber/gmx，全流程含分析段产出 |
| 03 GPU 脚本预检 | ✅ 语法通过；GROMACS 主源/GitHub 回退/NVIDIA WSL 仓库三个下载源均 HTTP 200 |
| GPU 构建与 GPU 烟测 | ⛔ 沙盒无 GPU、无 sudo —— **只能在你 WSL 执行（README 第 3 步）** |
| 沙盒磁盘事件 | 处理：清理已完成任务副本与缓存后回到 1.7G 可用（不影响交付物） |

**结论：UV 路线的 Python 层与全链路烟测已在本环境验证通过；两处实测坑已回写
`02_环境内引导…sh`、SOP §9.8、README。剩余全部为 Windows/WSL 侧动作（第 1–5 步）。**

### 6.1 第二轮补充执行（同日追加）

| 执行项 | 结果 |
|---|---|
| UV 烟测·补算分析段 | ✅ `DONE_EXTRA_ANALYSIS`（三线 RMSD、质心、平衡/能量曲线、快照 ×3），与首轮烟测同口径 |
| **MM-GBSA 层（gmx_MMPBSA 1.7.0 × SOP 模板）** | ✅ **PASS，exit=0**：模板三段 namelist 被 1.7.0 全部接受，产出 `FINAL_RESULTS_MMPBSA.dat`（VDWAALS/EEL/EGB 实数）+ `FINAL_DECOMP_MMPBSA.dat`；**SOP「模板兼容性待核对」风险点就此关闭**。注：烟测轨迹仅 1 帧（步数 < nstxout-compressed=5000），SD 为 nan 属预期；结尾 PyQt5 警告 = SOP §9.6 登记的无害项 |
| 烟测输入预制 | ✅ `烟测输入_3HTB/{protein.pdb, lig.pdb, jz4_h.mol2}`（mol2 分子名=JZ4 已修），第 4 步零手工 |
| **04 一键烟测脚本** | ✅ 新增并**沙盒实测 PASS**：NVT/NPT 快速段（2000 步）+ 生产 NS=0.02（10000 步，~85 s CPU）→ DONE + 三产物 + `SMOKE PASS`；GPU 判定逻辑正确（沙盒 CPU 构建如实报「无 GPU 字样」，03 的 GPU 版应出现 CUDA acceleration 行） |
| 本机状态复查 | ⏳ `E:\WSL` 仍未出现——第 1 步尚未执行 |

**第 4 步现已一键化**：`wsl -d Ubuntu-24.04 -- bash -c "bash '/mnt/e/RProject/努力学习项目/…/准备文件/MD环境/04_烟测_3HTB.sh'"`
