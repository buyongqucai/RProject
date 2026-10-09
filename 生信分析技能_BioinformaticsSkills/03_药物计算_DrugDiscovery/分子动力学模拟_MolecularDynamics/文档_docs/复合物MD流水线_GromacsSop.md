# 复合物 MD 流水线（GROMACS + AmberTools/acpype）

> **地位：** 分子动力学技能的执行 SOP（由技能说明 §9–§10 迁出，便于入口瘦身、反馈只改此处）。  
> **出图/交付 FROZEN：** [`出图与交付约束_MdFigureStandards.md`](出图与交付约束_MdFigureStandards.md) — 图册与 Origin recipe 仍以该文件为准；本文件侧重计算与环境步骤。  
> **进化：** 你确认新跑通步骤或踩坑后，回写本文件；技能说明入口只留指针，不必同步复述。

## 9. 蛋白-配体复合物 MD 全流程 SOP（GROMACS + AmberTools/acpype）

> 实现脚本：`脚本_scripts/运行复合物MD_runComplexMd.sh`（幂等分段，断点续跑）；
> mdp 模板：`脚本_scripts/mdp模板_mdps/{ions,em,nvt,npt,md}.mdp`（`__LIG__` 占位符由脚本替换为配体残基名）。
> 验证体系：3HTB（T4 lysozyme L99A/M102Q + JZ4），GROMACS 官方教程（Lemkul）标准流程。

### 9.0 一键调用

> **每次跑 MD 前先激活隔离栈**（UV Python + conda AmberTools + GPU gmx）：`source ~/activate-md.sh`

```bash
wsl -d Ubuntu-24.04 -- bash -lc '
  source ~/activate-md.sh
  cd <工作目录> && \
  LIGAND_RES=JZ4 NET_CHARGE=0 NS=1 ACPYPE_BIN=$HOME/md-venv/bin \
  bash <技能根>/脚本_scripts/运行复合物MD_runComplexMd.sh . protein.pdb jz4_h.mol2
'
```

| 环境变量 | 默认 | 说明 |
|----------|------|------|
| `LIGAND_RES` | JZ4 | 配体残基名（≤4 字符 ASCII，须与 mol2 一致） |
| `NET_CHARGE` | 0 | 配体净电荷（antechamber -nc） |
| `NS` | 1 | 生产时长 ns；演示可 0.2，正式 ≥100 |
| `ACPYPE_BIN` | `~/md-venv/bin` | **仅** acpype（UV）；`antechamber`/`tleap` 来自 conda env `md-tools`（须在 PATH，见 §9.8） |

### 9.0.1 场景分流（先定初态，再进 §9.1）

> **2026-10-09 确认。** 有金属 ≠ 必须共晶。共晶约束的是**配体坐标从哪来**；金属和根离子约束的是**晶体里哪些非蛋白物种要留下、怎么参数化**。  
> 两条轴独立。所有场景的**公共尾部相同**：拓扑组装 → 盒子/溶剂/`genion` → EM → NVT → NPT → 分块生产 + §9.5.1 监控。分叉只在初态与约束，不在生产引擎。

**是否算共晶（轴 A 的判定，四条同时成立才是 A1）**

看的是**目标配体的坐标是不是这次实验测出来的**，不看有没有金属或根离子。

| # | 判据 | 成立 | 不成立 |
|---|------|------|--------|
| 1 | 同一套 PDB | 受体 `ATOM` 与该配体 `HETATM` 在同一个条目里 | 配体来自另一个 PDB、对接写回、或手工摆上去 |
| 2 | 化学身份 | 残基名 / RCSB Ligand ID / SMILES 与要模拟的分子相同 | 只是同口袋的别的分子 → 降为 **A2**（近缘可叠合才用） |
| 3 | 在目标口袋 | 配体重原子落在预定结合位点（相对催化金属或已知口袋） | 在晶格界面、表面或远离位点的缓冲分子 |
| 4 | 密度支持 | 该配体被一起精修：占有率不是约 0，RCSB/EDS 的 RSCC 可用 | 无密度、占有率约 0，或只是作者建模未列入配体 |

结晶方式（共结晶 vs 浸泡）写在论文方法或 PDB REMARK 里。两种都是实验位姿，**只要 1–4 成立，MD 初态都按 A1**。本 SOP 里的「共晶」指这条实验复合物位姿，不单指共结晶这一种长晶方法。

金属、PO4、SO4、水、GOL 出现在 HETATM 里，只说明晶体里有这些物种，**不能**据此判成配体共晶。

**优先级（2026-10-09，按文献改过；出处：[`初态优先级_调研_PosePriority.md`](初态优先级_调研_PosePriority.md)）**

只敲定文献覆盖到的三句，不把「以后一律共晶」或「对接只判断有没有模拟潜力」写成规则：

1. **A1**：目标配体有合格实验复合物 → MD 用这份坐标。不用对接最高分替换（Ramírez & Caballero, *Molecules* 2018；Lemkul 蛋白–配体教程从 3HTB 晶体建体系）。
2. **A2**：没有 A1、有同口袋近缘共晶 → 用近缘姿态作参照，引导对接或做极近骨架叠合。不用空口袋盲对接（Cleves & Jain, *J. Comput.-Aided Mol. Des.* 2015：无参照交叉对接常见约 20–30%，用已知共晶配体引导后最高分姿态族超过 60%）。原子替换后完全跳过搜索，这次调研没有官方文档把它定成唯一做法。
3. **A3**：A1 和 A2 都没有 → 对接姿态可以做 MD，这是文献和 GROMACS 论坛的常规入口，不是禁区（Guterres & Im, *J. Chem. Inf. Model.* 2020；Salmaso & Moro, *Front. Pharmacol.* 2018）。结论写成对接初态。对接最高分、以及约 30 ns 内「还在口袋」，都不单独证明姿态正确或值得开长轨迹（Ramírez & Caballero 2018；FXR 的 *J. Comput.-Aided Mol. Des.* 文，DOI 10.1007/s10822-017-0074-x；Liu 等, *J. Chem. Inf. Model.* 2017）。

| 场景 | 何时 | 配体坐标 | 对接 | 平衡（公共尾部之前的差别） |
|------|------|----------|------|------------------------------|
| **A1 目标配体共晶** | PDB 里就是要模拟的配体 | 晶体坐标 | 不做 | 标准 EM → NVT → NPT（位置限制在蛋白重原子） |
| **A2 同口袋近缘共晶** | 骨架可对照、口袋相同，配体不是目标分子 | 近缘共晶作参照：引导对接，或极近骨架叠合 | 不做空口袋盲对接 | 与 A1 相同的 EM → NVT → NPT（蛋白重原子位置限制） |
| **A3 没有 A1/A2** | 没有可用实验参照 | 对接姿态 | 用来提出姿态，不是资格考试 | 可以做 MD，结论写对接初态。蛋白重原子位置限制与晶体教程相同。对接分和短轨迹稳定都不单独当姿态正确的证据 |
| **A4 配体直接接触金属或口袋根离子** | 底物/抑制剂配位 Zn/Fe，或与口袋内磷酸根等成盐桥/配位 | 必须来自**同一实验结构**里的配体+金属/根离子（A1），或近缘共晶叠合（A2） | 禁止用「空口袋 + 金属/根离子当盒心」的盲对接作为正式初态 | 同 A1 或 A2 |

**轴 B — 金属 vs 根离子（跟「要不要共晶」分开判）**

根离子 = 晶体里的酸根/多原子阴离子（PO4、SO4、NO3 等）及缓冲小分子。`genion` 后加的 Na⁺/Cl⁻ 是溶剂离子，不在此列。

| 物种 | 处理 | 和共晶的关系 |
|------|------|----------------|
| 催化/结构金属（Zn²⁺、Ca²⁺、Mg²⁺、Fe、血红素） | 保留晶体坐标，按 §9.10 参数化。用实验里的那种金属（催化位 Ni 替换 Zn 的结构不替代 Zn 酶） | **金属本身不要求配体共晶。** 只有配体直接配位该金属时才升到 **A4**。空口袋 + 正确金属只适合蛋白稳定性，不能当作「该配体结合稳不稳」的正式初态 |
| 口袋内生物学根离子（底物磷酸、文献认定的结合部位酸根） | 当辅因子保留坐标并参数化，不进 acpype 的「垃圾 HETATM」清单 | 目标配体与它有直接相互作用 → **A4**；只是蛋白辅因子、配体不接触 → 保留即可，配体仍按轴 A 选 |
| 远离口袋的结晶添加剂（SO4/PO4/GOL/EDO/BME/ACT 等） | 删除（§9.1） | 不为它们找共晶 |
| `genion` 的 Na⁺/Cl⁻ | 中和 + 0.15 M | 与共晶无关 |

**ADA 重做（2026-10-09，用户改为人源）：** 7RTG 空口袋对接的腺苷约 42 ns 飞出，该 `md.cpt` 不续跑。重做目录 `ADA_Adenosine_7RTG_A2`：蛋白和 Zn 用 7RTG；3IAR 的 2′-脱氧腺苷按 349 个 CA 叠到 7RTG（RMSD 0.44 Å，Ni 与 Zn 相距 0.14 Å）后补上 O2′ 得到腺苷。不带入 Ni、甘油、硝酸根。只把 Asp19 侧链换成 3IAR 的结合态旋转异构体，不放大口袋。场景 A2。鼠源 1ADD 队列已停。

**口袋不放大（2026-10-09；出处 [`ADA金属与结构_调研.md`](ADA金属与结构_调研.md)）**

- 对接搜索盒变大只扩大搜索范围，不改变口袋。Vina 手册要求搜索空间尽量小。
- 空口袋不要撑开再对接。允许用的是**已结合配体的那套侧链**，或只松动与新配体碰撞的侧链（Sherman 等，*J. Med. Chem.* 2006；Miller 等，*J. Chem. Theory Comput.* 2021）。小幅主链运动留给 EM / 短平衡。
- 生产段口袋会呼吸，这不是搭体系的一步。错误姿态不要指望 MD 把口袋撑开后修回实验结构（Bhakat 等，*J. Comput.-Aided Mol. Des.* 2017）。

**飞出后的队列**

监控因配体飞出而 `ABORT` 时，保留 `md.cpt` 作对照，**不从该检查点续跑同一对接初态**。按上面的 A1 → A2 → A3 重搭新目录，排在当前生产任务结束之后再开。同一 GPU 不同时跑两套生产 MD。

### 9.1 输入准备（Windows 侧，OpenBabel）

1. 从复合物 PDB 分离：`ATOM` 记录 → `protein.pdb`；目标配体 `HETATM`（按残基名过滤）→ `lig.pdb`。**远离口袋**的结晶添加剂（PO4/SO4/BME 等）与晶格水在此步剔除；口袋内生物学根离子与金属按 §9.0.1 轴 B 另存，不一律删除。初态场景先按 §9.0.1 轴 A 定，再执行本步。
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

### 9.5.1 过程监控与异常即停（2026-10-09）

> 生产段**分块断点续跑**（`-cpi/-cpo md.cpt`）+ 块间监控；异常 **立即停止**，保留 `md.cpt` 便于查因后续跑。  
> 脚本：`脚本_scripts/过程监控_monitorMdRun.sh`；主流程：`运行复合物MD_runComplexMd.sh`（`CHUNK_NS`/`MONITOR`/`CHECK_MMGBSA`）。

| 环境变量 | 默认 | 含义 |
|----------|------|------|
| `CHUNK_NS` | 1 | 每块生产长度（ns）；块结束跑监控 |
| `MONITOR` | 1 | 1=启用监控 |
| `COM_MAX_NM` | 2.0 | 蛋白–配体 COM 距离上限（**飞出**） |
| `COM_JUMP_NM` | 1.0 | 相对首帧 COM 增量上限 |
| `LIG_RMSD_MAX_NM` | 1.5 | 配体 RMSD 上限（解离/飞出） |
| `BB_RMSD_MAX_NM` | 1.0 | 骨架 RMSD 上限（可疑展开） |
| `TEMP_MIN_K` / `TEMP_MAX_K` | 250 / 350 | 温度窗口 |
| `CHECK_MMGBSA` | 0 | 1=按间隔抽查；**ΔG（DELTA TOTAL）>0 kcal/mol 即停** |
| `MMGBSA_INTERVAL_NS` | 5 | 抽查间隔（约整数倍 ns） |

**即停条件（写 `monitor/ABORT_REASON.txt`，退出码 2）：**

1. 受体–配体 **COM 过大/突增**，或 **配体 RMSD** 超阈（飞出/解离）  
2. **骨架 RMSD** 超阈（体系崩/展开）  
3. **温度** 偏离窗口，或 **Potential** NaN/极端（积分爆炸）  
4. `md.log` 在 **Started mdrun 之后**出现 Fatal / NaN（硬失败；不要扫文件开头的 mdp 回显，`lincs-warnangle` 含子串 nan）  
5. （可选）**MM-GBSA 结合能为正**  

温度和势能**分开**抽 `gmx energy`（`energy_T.xvg` / `energy_P.xvg`）。一次多选时列序与输入顺序相反（ADA 实测：先写出 Potential ≈ −4.9×10⁵，后写出 Temperature ≈ 300 K），把势能当温度会得到约 −4.9×10⁵ K 的假停机。温度序列中位数不在 150–450 K 时按解析错误停，势能用相对中位数漂移 >50% 判断，不用绝对值 >1e9。

监控 `abort` 时由 `E:\md_kit\notify_md_alert.sh` 拼装 MD 正文后调用全局 `E:\alert_kit\`（QQ SMTP `smtp.qq.com:587`）发纯文本告警。授权码只放在本地 `QQ邮箱.txt`（指针 `E:\alert_kit\qq_auth_path.txt`），脚本不回显。同一目录、同一原因只发一次。其它项目直接用 `alert_kit` / Cursor 技能 `qq-smtp-alert`。  

飞出、温度、势能这些判定在监控脚本的 Python 段里，原先 `sys.exit(2)` 后直接结束，**没有调用**发信的 `abort()`。2026-10-09 ADA 约 42 ns 停机因此没有邮件，`alert.log` 也不存在。Python 退出码为 2 时必须再调用 `abort()`。  

查因后再续跑：修正拓扑/盒子/初态后，同目录保留 `md.cpt` 时主脚本会从检查点继续（勿删 `md.tpr`/`md.cpt`）。

**过程期要盯的曲线（对齐样例图种，监控草图 ≠ Origin 金标）：**

| 监控草图（`monitor/*_monitor_*.png`） | 对应样例正式图（FROZEN 01–12） |
|--------------------------------------|--------------------------------|
| Backbone / Ligand RMSD | 01 骨架 RMSD、02 三线 RMSD |
| COM distance | 07 质心距离 |
| Temperature | 08/09 NVT·NPT 温度 |
| Potential | 12 生产势能 |

正式交付图仍按 [`出图与交付约束_MdFigureStandards.md`](出图与交付约束_MdFigureStandards.md) **01–26** 用 Origin/PyMOL/LigPlot 出；过程监控 PNG 只用于跑中判停，不进金标报告。

```bash
source ~/activate-md.sh
CHUNK_NS=1 MONITOR=1 CHECK_MMGBSA=0 NS=100 \
  bash 运行复合物MD_runComplexMd.sh . protein.pdb lig_h.mol2
# 单独复查当前轨迹：
LIGAND_RES=JZ4 bash 过程监控_monitorMdRun.sh .
```

### 9.6 PBC 校正与分析

`trjconv -pbc mol -center -ur compact`（蛋白居中）→ 默认组非交互分析：

| 指标 | 命令 | 输出 |
|------|------|------|
| RMSD | `gmx rms -tu ns`（Backbone 拟合+计算） | rmsd_backbone.xvg |
| RMSF | `gmx rmsf -res`（C-alpha） | rmsf_calpha.xvg |
| 氢键 | `gmx hbond -num`（Protein ↔ 配体） | hbond_num.xvg（3 列：time/氢键数/接触对数） |
| Rg | `gmx gyrate`（Protein） | gyrate.xvg |
| SASA | `gmx sasa -tu ns`（Protein） | sasa.xvg |
| FEL | R 内 kde2d(RMSD, Rg) 默认带宽 → ΔG = −kT ln(P/Pmax)；**禁止**人为加宽带宽 / gaussian 后处理平滑；2D/3D 同网格 | 由出图脚本算 |
| 结合自由能 | gmx_MMPBSA（GB igb=5 + idecomp=1 逐残基分解） | FINAL_RESULTS/FINAL_DECOMP_MMPBSA.dat |

**MM-GBSA（gmx_MMPBSA）**：模板 `脚本_scripts/mmpbsa模板_mmpbsa.in`；索引 `printf 'q\n' | gmx make_ndx -f md.tpr -o index.ndx`（默认组编号 Protein=1、配体如 JZ4=13，以实际列表为准）；
先 `source ~/activate-md.sh`，再：
`gmx_MMPBSA -O -i mmpbsa.in -cs md.tpr -ct md_center.xtc -ci index.ndx -cg 1 13 -cp topol.top -o FINAL_RESULTS_MMPBSA.dat -do FINAL_DECOMP_MMPBSA.dat`
（工具在 `~/md-venv/bin`；也可用绝对路径 `~/md-venv/bin/gmx_MMPBSA`。历史：整包 conda env `md` 已废弃。）
输出单位为 **kcal/mol**（出图脚本 ×4.184 转 kJ/mol）；结尾自动拉起 gmx_MMPBSA_ana 报 PyQt5 缺失属无害（CLI 流程不用 GUI）。熵项（nmode/QT）演示不算，正式研究再开。

### 9.7 出图与交付（**分析图由 Origin 绘制 · FROZEN**）

> **冻结 SSOT：** [`文档_docs/出图与交付约束_MdFigureStandards.md`](出图与交付约束_MdFigureStandards.md)（2026-09-03）。下列 recipe 与图册顺序未经用户解冻不得改动。

GROMACS/xvg 解析与 CSV 仍由 `01_样例_sample/代码文件/02_分析出图_plotMdAnalysis.R` 负责；**RMSD / RMSF / 氢键 / Rg / SASA / COM / 平衡曲线 / FEL 2D·3D / MM-GBSA 柱图必须用本机 Origin 出图**，禁止只对照 Origin 样图再用 ggplot/matplotlib 仿画。

入口：`脚本_scripts/origin出图_plotMdOrigin.py`（COM 操作 `E:\Origin\Origin64.exe`，LabTalk 导入 `E:\Origin_Data\<项目>\` CSV → 导出 PNG/SVG 600 dpi）。**一图一进程**：画完一张即导出并关闭 Origin，再开下一张，避免 `.opju` 占用/只读。禁止对 COM `Save()` 传绝对路径（Origin UFF=`E:\Origin_Data` 会拼成 `E:\Origin_Data\"E:/....opju".opju`）。配色对齐 VizStandards journal muted（`#5B8FA8/#C17B7B/#8B7BA8/#6B8F71/#D4A574`）；FEL colormap 用 Viridis（与 ggplot 一致，不用 Rainbow）。柱图实心填充，禁止默认黑白图案。

样例结果按**分析图种一文件夹**存放（覆盖 DeliveryStandards 默认的 `结果文件/数据文件` + `结果文件/图片文件` 总分）。文件夹与交付文件均加流水号：`{NN}_{中文}图/` + `{NN}_{中文}_{English}.png`。

```text
01_样例_sample/
  数据文件/01_复合物结构_3HTB.pdb
  代码文件/01_run_sample.R
  代码文件/02_分析出图_plotMdAnalysis.R
  代码文件/结果文件/
    报告文件/                      # STATUS、HTML、审计后检、PlotQA
    01_骨架RMSD图/                 # CSV + Origin PNG/SVG
    10_NPT压力图/
    17_自由能形貌3D图/
    25_轨迹快照图/                 # PyMOL
    26_二维相互作用图/             # LigPlot
  工作文件_MdWork/3HTB/            # GROMACS 归档，按阶段分类
    01_输入结构_Input/
    02_拓扑_Topology/              # topol.top、ligand.acpype（引擎原名）
    07_生产轨迹_Production/
    08_轨迹分析_Analysis/          # 中英对照 xvg
    09_结合自由能_MmGbsa/
    10_轨迹快照_Snapshots/
    99_运行日志_Logs/
```

GROMACS 引擎文件（`topol.top`、`md.tpr`、`-deffnm`）**保持原名**，只按阶段入夹。分析产物（xvg / 快照 PDB / MM-GBSA dat）用中英对照。生产在扁平临时目录跑 `运行复合物MD_runComplexMd.sh`，结束后：

`python 脚本_scripts/整理样例目录_layoutMdSample.py`

文件名仍用中英对照（例：`17_自由能形貌3D_FreeEnergyLandscape3D.png`）。

PyMOL 轨迹快照与 LigPlot 二维相互作用仍走各自脚本（写入对应 `{主题}图/`，不是 Origin 图种）。LigPlot 正式图必须是官方 `ligplot.ps` 的化学结构（配体骨架、原子色、疏水弧/氢键、图例），由 `ligplot二维相互作用_runLigPlot2d.py` 复绘 PNG/SVG；**禁止**配体圆 + 残基方框示意网。LigPlot CPK/配体键紫/疏水砖红是该图种惯例，不改成 journal muted。

`02_分析出图_plotMdAnalysis.R` 产出数据表与 Origin CSV 后，调用 Origin 脚本绘制：

| 图 | 文件主题 | 数据来源 |
|----|----------|----------|
| Backbone RMSD | `RmsdBackbone` | `rmsd_backbone.xvg` |
| **Protein/Ligand/Complex 三线 RMSD** | `RmsdProteinLigandComplex` | `rmsd_{protein,ligand,complex}.xvg` |
| C-alpha RMSF | `RmsfCalpha` | `rmsf_calpha.xvg` |
| 氢键数（阶梯） | `HbondNum` | `hbond_num.xvg` |
| Rg | `RadiusGyration` | `gyrate.xvg` |
| SASA | `Sasa` | `sasa.xvg` |
| **质心距离 COM** | `ComDistance` | `com_distance.xvg` |
| **NVT/NPT 平衡** | `NvtTemperature` / `NptTemperature|Pressure|Density` | `energy_*.xvg` |
| **生产势能** | `MdPotential` | `energy_md_potential.xvg` |
| FEL 2D 等值线 | `FreeEnergyLandscape` | RMSD×Rg kde（默认带宽，禁止后处理平滑） |
| **FEL 3D 曲面** | `FreeEnergyLandscape3D` | 与 2D 同网格；**Origin 列类型 X/Y/Z → `xyz_regular`→`plotm` 103 OpenGL colormap surface（Viridis）** |
| **FEL RMSD×COM** | `FreeEnergyRmsdCom` / `…3D` | 结合松紧 |
| **FEL RMSD×SASA** | `FreeEnergyRmsdSasa` / `…3D` | 溶剂暴露 |
| **FEL 配体×蛋白 RMSD** | `FreeEnergyLigandProteinRmsd` / `…3D` | 谁在动 |
| MM-GBSA 分解柱 | `BindingEnergyDecomp` / `BindingEnergyLabeled` | `FINAL_RESULTS_MMPBSA.dat` |
| **能量表图** | `BindingEnergyTable` | 同上 |
| 逐残基 Top15 | `ResidueEnergyContrib` | `FINAL_DECOMP_MMPBSA.dat` |
| **轨迹快照** | `Snapshot{Start,Mid,End}` / `TrajectorySnapshots` | PyMOL + dry PDB |
| **二维相互作用** | `LigPlot2D` | `E:\LigPlus` + `脚本_scripts/ligplot二维相互作用_runLigPlot2d.py` |

交付文件名用语义中英对照加流水号（例：`02_三线RMSD_RmsdProteinLigandComplex.png`），勿用仅「折线图_*_Line」。

补算脚本：`脚本_scripts/补算必备分析_extraMdAnalysis.sh`（幂等）；PyMOL：`脚本_scripts/pymol轨迹快照_snapshotMd.pml`（中文路径易 GBK 报错时用 `E:\Origin_Data\3HTB\snaps\snapshot_md.pml`）。

VizStandards：DPI≥600、PNG+SVG、图面英文、PlotQA 逐图审核 → 审计 `data_provenance=REAL` → 报告 + STATUS。

**Origin 出图（强制，分析图）**：用户侧 Origin 装于 `E:\Origin`（`Origin64.exe`）。每图数据以英文列名 CSV 落在 `E:\Origin_Data\<项目名>\`（样例 `E:\Origin_Data\3HTB\`，LabTalk 不能走中文样例路径）；由 `origin出图_plotMdOrigin.py` **启动并操作 Origin** 绘图、导出 `E:\Origin_Data\<项目>\OriginFigures\*.png/.svg`（DPI≥600），再拷到样例 `{NN}_{主题}图/`。**每图独立 Origin 进程**（导出后关闭），不批量堆在同一项目里。R/Python 只做数据准备与备图，**不得替代 Origin 成为 FEL/曲线/能量柱的正式出图引擎**。

仅重组目录、不重画：`python origin出图_plotMdOrigin.py --layout-only`。FEL 热图/OpenGL 曲面禁止设置 `layer.cmap.shown`（会弹 `LAYER.CMAP.SHOWN: error setting property value`），只用 `set %C -cpal Viridis`。禁止 `set %C -pfb color()`（大整数当色板索引会变黑）。2D FEL 棋盘条纹来自 60×60 KDE 格子被画成热图单元格；显示改为填色等值线 + 2× 双线性加密，不改 kde2d 带宽。2D 等值黑线用 `layer.cmap.lineN = 0`（勿用 `showLines(3)`，会抹掉填色）。3D OpenGL 等值线：`run.LoadOC("hideFelContours.c", 16)` 后 `hide_fel_contours` 把 `EnableContour/MajorLines` 置 0，且 `set %C -b3t 1`（填色）+ `-b3m 0`；XYZ 墙面网格保留。多色柱：Energy 右侧 `Rgb` 列 + `layer.plot1.color = color(1, r)` Direct RGB，对齐 journal muted。单色柱：`layer.plot1.color = color(R,G,B)`。

### 9.8 本机环境安装（WSL2 · **2026-10-09 现行：UV Python + conda `md-tools`(仅 AmberTools) + GPU GROMACS**）

> **分工（用户确认 2026-10-09）：**
> - **UV** → 只管 Python：`~/md-venv`（acpype / gmx_MMPBSA / impi-rt）
> - **conda/Miniconda** → 只建隔离环境 `md-tools`，**只装 AmberTools 二进制**（不做 Python 环境管理）
> - **源码** → GPU 版 GROMACS → `~/gromacs-gpu`
> - **一键激活**：`~/activate-md.sh`（拼 PATH：`md-venv` 在前，保证 `python`/`acpype` 不落到 conda）
> 安装包：技能目录 `环境安装_EnvSetup/`；联接 `E:\md_kit`。课题 `准备文件/` 不再存放这套脚本。
> 旧「整包 conda env `md`」与「AmberTools 仅 micromamba→/opt」见 git 历史；沙盒烟测见 `报告_P1-3_MD环境与烟测.md`。

1. **WSL2**：`wsl --install -d Ubuntu-24.04 --location E:\WSL\Ubuntu`（忽略 `docker-desktop`；虚拟盘 `E:\WSL\Ubuntu\ext4.vhdx`）。
2. **UV（Python 唯一管理器）**：
   - `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - `uv venv ~/md-venv --python 3.12`（**必须 ≥3.12**，acpype≥2026.9.4）
   - `uv pip install --python ~/md-venv/bin/python "acpype>=2026.9.4" "gmx_MMPBSA>=1.7.0" impi-rt`
     （**必须 `impi-rt`**，否则 gmx_MMPBSA 因 mpi4py 缺 libmpi 启动即崩）
3. **AmberTools（conda 隔离 env，推荐）**：
   - Miniconda → `~/miniconda3`；若遇 ToS：`conda tos accept` 后对 forge 使用 `--override-channels`
   - `conda create -y -n md-tools --override-channels -c <tuna conda-forge> ambertools`
   - **禁止**在 `md-tools` 里再 `pip install acpype`（Python 只走 UV）
   - 备选：`AMBER_METHOD=source` 装到 `/opt/ambertools`，或 `binary` micromamba 前缀（见准备包 `02_*.sh`）
4. **GROMACS GPU（源码，脚本 `03_构建GPU版GROMACS.sh`）**：
   - 最小 CUDA：`cuda-nvcc cuda-cudart-dev cuda-cccl`（WSL 仓库）
   - ⚠️ Ubuntu 24.04 默认 **GCC 13+**，CUDA 12.0 nvcc **不支持 >12** → 装 `gcc-12 g++-12`，
     cmake 使用 `-DCMAKE_C_COMPILER=gcc-12 -DCMAKE_CXX_COMPILER=g++-12 -DCMAKE_CUDA_HOST_COMPILER=g++-12`
   - 默认版本 **2024.4**，前缀 `~/gromacs-gpu`；验收：`gmx --version` 含 `GPU support: CUDA`
5. **激活脚本 `~/activate-md.sh`**（示例）：
   ```bash
   source "$HOME/miniconda3/etc/profile.d/conda.sh"
   conda activate md-tools
   export PATH="$HOME/.local/bin:$HOME/md-venv/bin:$HOME/gromacs-gpu/bin:$PATH"
   ```
6. **验证**：`source ~/activate-md.sh` →
   `which acpype` 含 `md-venv`；`which antechamber` 含 `envs/md-tools`；
   `gmx --version` 含 CUDA → 再跑准备包 `04_烟测_3HTB.sh`（`SMOKE PASS`）。

> 版本锚点（CreazyWork 2026-10-09）：uv 0.12.24；acpype 2026.10.8；gmx_MMPBSA 1.7.0；
> AmberTools 26.0（md-tools）；GROMACS 2024.4 CUDA；nvcc 12.0；host gcc-12；GPU RTX 4080 SUPER。

### 9.9 踩坑登记（回填提醒）

1. Windows 写出的 .sh/.mdp 是 CRLF → WSL bash/grompp 报错；**必须转 LF**。
2. mol2 分子名 GBK 中文 → acpype UnicodeDecodeError（见 9.1.3）。
3. ambermd.org 表单须 `multipart/form-data`（curl -F）；`-d` 会挂起。
4. Ubuntu 24.04 apt 无 ambertools 包；PyPI 无 antechamber；**UV 不能给 AmberTools 建 venv**。
5. solvate/genion 重复追加 topol.top（见 9.4）。
6. ions 步 grompp 需 `-maxwarn 1`（见 9.4）。
7. `gmx select` 赋值命名语法在 2023.3 不可用 → 全程默认组（见 9.5）。
8. 性能参考：GPU 版正式研究 ≥100 ns；演示/烟测 `NS=0.02`～`0.2`。
9. **CUDA nvcc + GCC>12**：`unsupported GNU version` → 用 gcc-12 作 host compiler（§9.8 第 4 条）。
10. **conda ToS**：`CondaToSNonInteractiveError` → `conda tos accept` 或 `--override-channels` 只用 forge。
11. **Windows 控制台托管 `wsl|Tee`**：UTF-8 中文进度易乱码 → 安装脚本 echo 用 ASCII；或 `chcp 65001`。
12. **PATH 顺序**：`conda activate` 后须把 `~/md-venv/bin` 放前面，否则 `python`/`acpype` 可能落到 conda。

### 9.10 辅因子与金属酶体系扩展（**2026-10-09 新增**；课题 top3 MD 用，源自 UC 课题 P1-3）

> 适用：受体含金属离子（Zn²⁺/Ca²⁺/Ni²⁺）或血红素（HEME）时，§9.1–9.6 的参数补丁。  
> **初态走哪条场景以 §9.0.1 为准**（金属 ≠ 必须共晶）。本轮体系：MMP9/4H3X（2 ZN+3 CA，口袋有共晶配体 → 配体按 A1/A2）、CYP1A1/4I8V（HEME）、ADA 若问结合稳定性则按 A4 重选初态（7RTG 空口袋对接只作对照）。

**9.10.1 结构选择政策（先于一切）**
1. **优先野生型**：下载后必查 `SEQADV`——`ENGINEERED MUTATION` 在活性位点 → 换结构（本课题：1GKD=E402Q → 换 **4H3X**，1.76 Å WT；3IAR 催化位为 Ni 取代 → 人 ADA1 用实验 Zn 结构）；仅表达标签突变可保留。
2. 备选池（MMP-9 WT+羟肟酸）：4H3X(1.76Å)/4XCT(1.30Å)/5I12(1.59Å)。ADA 结合稳定性初态从含腺苷/近缘核苷的共晶里选（§9.0.1 A4），不把「有 Zn 的空口袋」当作充分条件。
3. 多链只取 **A 链**做 MD；表达标签（7RTG 364 起）切除。
4. 换结构后按 **§9.0.1 轴 A** 决定保留共晶位姿、近缘叠合，或（仅 A3）重对接。重对接时盒心 = 口袋配体或文献位点；对接表新增行（pdb 列区分）。**禁止**把「换了 PDB」自动理解成必须盲对接。

**9.10.2 pdb2gmx 输入边界**
- `protein.pdb` = **仅 ATOM**（pdb2gmx 不认识 ZN/CA/HEM，混入即 Fatal）。
- 辅因子另存 `cofactors_*.pdb`（HETATM），按 9.10.3/9.10.4 单独入拓扑。
- 口袋配体走 acpype → 残基名 `LIG`（mol2 第 2 行 sed 成 ASCII）；对接阶段去口袋配体/水/甘油，**ZN/HEME 保留**。

**9.10.3 二价金属（Zn²⁺/Ca²⁺/Ni²⁺）—— 非键合模型（抽查级默认）**
- 处理：金属坐标沿用晶体位置 → 以 +2 单原子离子入拓扑（ff 自带离子类型优先；缺则按
  [Li-Merz 12-6 表](https://ambermd.org/AmberModels_ions.php) 手写单原子 itp，LJ 取 12-6 非键合）。
- **必做监控**：配位距离轨迹（Zn–His Nε2 目标 2.0–2.3 Å；MMP-9 催化 Zn 配位 His175/Asp177/His190/His203 类位点），发散即报。
- **必写敏感性**：非键合模型下结合稳定性结论附「金属位点模型」说明；催化机制/配位数变化类结论不适用。
- 升级选项（正式论文级，1–2 天）：**MCPB.py 键合模型**（AmberTools 自带）——小模型 QM（含配位残基；**若抑制剂/底物直接配位金属，其配位原子必须进 QM 模型**）→ Seminario 取力常数 → tleap prmtop → ParmEd/GROMACS 转换；边界：不能模拟配位数变化。

**9.10.4 HEME（细胞色素 P450）—— 禁走 acpype**
- 参数：**Shahrokh, Orendt, Yost, Cheatham, JCC 2012**（AMBER 兼容、覆盖 P450 多状态、含轴向 Cys）为首选；备选 CYPForge（GitHub，2026 预印本流程）。
- 流程：HEME + 去质子轴向 Cys 在 tleap 手工建 Fe–S 键与 LJ 排除 → prmtop → ParmEd 转 GROMACS itp；
  与 pdb2gmx 蛋白拓扑、acpype 配体 itp 三方合并（同 §9.3 机制）。
- acpype/antechamber **无金属元素类型**，跑 HEME 必失败——HEME 是参数问题不是拓扑问题。

**9.10.5 输入目录规范（课题级）**
```text
课题top3输入/<对名>/
  protein.pdb        # 仅 ATOM、目标链、已切标签（pdb2gmx 直用）
  cofactors_*.pdb    # ZN/CA/HEM HETATM（9.10.3/4 处理）
  lig_h.mol2         # 姿势+全氢，第2行=LIG，净电荷≈0（acpype 直用）
  口袋参照_*.pdb     # 盒心依据留痕
```

**9.10.6 本轮踩坑回填**
1. **PDB 2 字符残基名（ZN/CA/NI）第 20 列是空格** → awk `substr($0,18,3)=="ZN"` 恒假，须 `gsub(/ /,"",r)` 后比较（HEME 恰 3 字符不触发，最易漏查）。
2. 多链 HETATM 必须按 `substr($0,22,1)`（col22）过滤链，否则把 B 链金属拷进 A 链体系。
3. 无口袋配体时，催化金属坐标**只可作 A3 对接的盒心**，不能把该对接姿态当成 A4（配体接触金属）的正式初态。ADA/7RTG：Zn 盒心对接在 ~42 ns 配体解离，监控按设计停机；正式重跑走 §9.0.1 A4。
4. 本轮结构审计锚点：4H3X 链A = 2 ZN + 3 CA（口袋 10B）；4I8V 链A = HEM 43 原子（口袋 BHF）；7RTG 链A = 1 ZN（标签 364+ 已切，无口袋配体）。



| 项 | 值 | 备注 |
|----|----|------|
| GROMACS | **2024.4**（`~/gromacs-gpu`，CUDA） | host **gcc-12**；nvcc 12.0；非 apt CPU 版 |
| 运行层 | WSL2 `Ubuntu-24.04` | 虚拟磁盘 `E:\WSL\Ubuntu\ext4.vhdx` |
| Windows 调用 | `wsl -d Ubuntu-24.04 -- bash -lc 'source ~/activate-md.sh; …'` | E 盘 → `/mnt/e/...`；联接 `E:\md_kit` |
| Python（UV） | `~/md-venv`：acpype **2026.10.8**、gmx_MMPBSA **1.7.0**、impi-rt；Python **3.12.3** | **不**用 conda 管 Python |
| AmberTools | conda env **`md-tools`**：AmberTools **26.0** | 仅二进制；`antechamber` 等 |
| 激活 | `~/activate-md.sh` | 拼 PATH：UV + md-tools + gromacs-gpu |
| GPU | **RTX 4080 SUPER**（WSL 内 `nvidia-smi`） | |
| Origin | ✅ `E:\Origin\Origin64.exe`（用户 2026-10-09 已装） | 分析图 COM/LabTalk：`origin出图_plotMdOrigin.py`；数据宜落 `E:\Origin_Data\<项目>\` |
| LigPlot+ | `E:\LigPlus`（若已装） | 二维相互作用脚本见 `脚本_scripts/` |
| 配套（Windows） | PyMOL `E:\pymol`、OpenBabel 3.1.1、Vina、MGLTools | 对接/格式转换 |

**历史锚点（勿当作现行安装目标）：** 2026-08-30 曾用 apt GROMACS 2023.3 + Miniforge env `md` 跑通 3HTB 0.2 ns E2E（`STATUS=REAL`）；2026-10-08 沙盒 UV+conda-forge GROMACS 2026.3 烟测 PASS。现行以本表 2026-10-09 行为准。
