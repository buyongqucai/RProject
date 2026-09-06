# 对接盒子定心与定边协议 / DockingBoxProtocol

> **状态：待用户审核条款已并入 FROZEN（2026-09-05）** — 生产默认以 [`对接与交付约束_DockingFrozen.md`](对接与交付约束_DockingFrozen.md) + [`技术路线_AutoSite_AutoDockGPU.md`](技术路线_AutoSite_AutoDockGPU.md) 为准。  
> **归属 SSOT：** 被 [`分子对接流水线规范_DockingPipelineSOP.md`](分子对接流水线规范_DockingPipelineSOP.md) §3.1 引用。  
> **废止条款：** 固定立方体边长 `22 Å`；对 PDB 内**全部**非溶剂 `HETATM` 做简单平均当中心；无校验地照抄库表 `x/y/z center`；AlphaFold/无口袋时用**整链 COM**当打分盒子。  
> **不做：** 共晶配体重对接 RMSD 验收（定心仍可用共晶质心/enveloping）。

---

## 1. 依据（官方 / 论文 / 手册）

| 来源 | 结论（与本协议相关） |
|------|----------------------|
| **AutoDock Vina Manual**（[vina.scripps.edu/manual](https://vina.scripps.edu/manual/)） | 搜索空间须提供 `center_*` + `size_*`（Å）。原则：**as small as possible, but not smaller**；过大则难搜全。一般应避免 `> 30×30×30`，除非同步提高 `--exhaustiveness`。 |
| **Trott & Olson, J Comput Chem 2010**（Vina 原文，DOI [10.1002/jcc.21334](https://doi.org/10.1002/jcc.21334)） | 测试集定盒流程：① 取结合态配体的**轴对齐包围盒（AABB）**；② 三边各加 **10 Å**；③ 每一维再沿随机一侧加 **5 Å**（基准测试防“正中心偏置”）；④ 任一维若 **&lt; 22.5 Å** 则对称扩到 22.5 Å。效果：每维至少比配体大 **≈15 Å**，且每维 **≥ 22.5 Å**。 |
| **Feinstein & Brylinski, BMC Bioinformatics 2015**（[PMC4468813](https://pmc.ncbi.nlm.nih.gov/articles/PMC4468813/)） | 实验位点 = **结合配体的几何中心**；复述 Vina 默认定边逻辑；对预测口袋还讨论了与配体回转半径 \(R_g\) 相关的最优边长比。 |
| **AutoDock Vina ReadTheDocs 基础教程** | 示例为已知位点上的 `box_center` + `box_size`（如 20³），中心来自位点/共晶，而非蛋白质心。 |

**对“固定 22 Å”的澄清：**  
原文中的 **22.5 Å 是单边下限（floor）**，不是“所有任务统一用的立方边长”。本仓库此前把下限误当成固定值，**错误**。

**对“简单平均所有 HETATM”的澄清：**  
官方/论文说的是 **某一个结合配体（bound ligand）** 的几何中心或 AABB，不是把 PDB 里多种配体、多条链的杂原子混在一起平均。

---

## 2. 修正后的定心方法（Center）

### 2.1 强制优先级

1. **共晶配体（首选）**  
   - 在受体 PDB 中指定 **唯一** 参考配体：`resname` + `chain`（必要时 `resi`）。  
   - 中心 = 该配体全部（或重原子）坐标的几何中心：  
     \[
     c = \left(\frac{1}{n}\sum_i x_i,\; \frac{1}{n}\sum_i y_i,\; \frac{1}{n}\sum_i z_i\right)
     \]  
     其中 \(\{i\}\) **仅属于该参考配体**。  
   - 登记字段：`ref_ligand_resname`、`ref_ligand_chain`、`ref_ligand_resi`（可选）、`center_source=cocrystal`。

2. **文献 / UniProt 已注释活性残基**  
   - 用指定残基 CA（或侧链重原子）集合的几何中心；`center_source=annotated_site`。

3. **口袋预测（仅无 1、2 时）**  
   - 默认 **AutoSite**（`center_source=autosite`）；异常回退 **P2Rank** / **Fpocket**（见技术路线）。  
   - 须人工确认；**不得**静默当作与共晶等价。  
   - **每个任务**登记方法码与细节：[`中心位点方法登记_CenterSourceRegistry.md`](中心位点方法登记_CenterSourceRegistry.md)。

4. **禁止**  
   - 整链 / 结构域 `ATOM` COM 作为正式打分盒子（含 AlphaFold 全长）。  
   - 对文件内所有非溶剂 `HETATM` 无差别平均。  
   - 未校验距离就采用库表坐标。

### 2.2 库表 `分子对接_蛋白表.csv` 的使用规则（修正）

- 表中 `x/y/z center` **仅作候选**，不得“有数就用”。  
- **校验：** 若 PDB 存在参考共晶配体，计算  
  \(d = \| c_{\text{表}} - c_{\text{共晶}} \|\)。  
  - \(d \le 2.0\,\text{Å}\)：可采用表值，并写回/保留 `ref_ligand_*`。  
  - \(d > 2.0\,\text{Å}\) 或无法解析参考配体：**废弃表值**，按 §2.1 重算并更新表。  
- 无有机共晶配体的 PDB（例：仅水/金属）：**不得**用该 PDB 的模糊中心硬对接；换含配体的同源复合物，或走 §2.1-2/3 并标注。

### 2.3 多配体 / 多链

- 若有多个相同 `resname`：必须指定 `chain`（及 `resi`）；禁止平均多个拷贝。  
- 对称寡聚体：默认选与课题相关的一条链上的配体；在 `task_info` / 蛋白表注明。

---

## 3. 修正后的定边方法（Size）

对接盒子服务两个对象：

- **中心**：由**口袋参考**（共晶/位点）决定（§2）。  
- **边长**：须保证**当前待对接配体（query ligand）**能在盒内平移/旋转，故边长随 **query 配体尺寸** 变化，**禁止全局固定 22**。

### 3.1 生产默认（推荐采纳）—— Vina 论文定边的“生产版”

Trott 2010 基准流程里“每维随机 +5 Å”是为了**故意偏离实验构象中心**做公平测试。  
**课题生产对接不采用随机偏置**（否则同任务不可复现），改为对称扩边，数值与论文等价量级：

对 query 配体（对接用 PDBQT/SDF 的 3D 构象）计算轴对齐尺寸：

\[
L_x = \max x - \min x,\quad
L_y = \max y - \min y,\quad
L_z = \max z - \min z
\]

（建议用**重原子**；若仅极氢差异可忽略。）

每维边长：

\[
\begin{aligned}
S_x &= \max(L_x + 15.0,\; 22.5) \\
S_y &= \max(L_y + 15.0,\; 22.5) \\
S_z &= \max(L_z + 15.0,\; 22.5)
\end{aligned}
\]

- **+15.0 Å**：对应论文“+10 Å + 再 +5 Å”的总扩边量。  
- **22.5 Å**：论文与 AutoDock 实践中的**下限**（保证可旋转），不是固定边长。  
- 允许 **各向异性**（\(S_x,S_y,S_z\) 可不同）；写入 `size_x/y/z`。

### 3.2 与共晶包围盒取“更大者”（可选加强）

若存在参考共晶配体，另算其 \(L_x^{\text{ref}},\ldots\)，令  

\[
S_k = \max\!\big(L_k^{\text{query}}+15,\; L_k^{\text{ref}}+15,\; 22.5\big)
\]

避免 query 略小于共晶配体时盒子过紧。

### 3.3 上限与 exhaustiveness

- 若任一 \(S_k > 30\)：允许，但必须把 `exhaustiveness` 提到 **≥16**（建议 32），并在日志警告（对齐 Manual：“大盒子须加 exhaustiveness”）。  
- 若 \(S_k > 40\)：默认 **拒绝对接**，要求缩小为位点对接或拆结构域；禁止无声明盲对接冒充位点对接。

### 3.4 备选（虚筛 / 预测口袋，审核可选）

Feinstein 2015：对预测口袋，最优立方边长约 \(2.857 \times R_g\)（配体回转半径）。  
本课题**位点对接默认仍用 §3.1**；仅当 `center_source=predicted_pocket` 时可改用：

\[
S = \max(2.857\,R_g,\; 22.5)
\]

并记 `size_method=feinstein_rg`。

---

## 4. 写入 config / 质控（强制）

每个任务 `config.txt` 外，须在 `task_info.txt`（或旁路 JSON）记录（**中心方法词表 SSOT：** [`中心位点方法登记_CenterSourceRegistry.md`](中心位点方法登记_CenterSourceRegistry.md)）：

```text
center_source=cocrystal|cocrystal_meeko|annotated_site|autosite|p2rank|fpocket|manual|FAIL
center_detail=...
ref_ligand=RESNAME:CHAIN[:RESI]   # 共晶时必填
center_x/y/z=...
size_method=meeko_enveloping|autosite_box|rg_4_5x|vina2010_prod|feinstein_rg
size_x/y/z=...
ligand_Lx/Ly/Lz=...   # 若适用
box_qc=PASS|FAIL
fallback_used=          # 空或 p2rank|fpocket|annotated_site|manual
fail_codes=             # 如 Q2,Q6
exhaustiveness=...      # Vina；AD-GPU 则记 nrun
engine=vina|adgpu
```

**质控：**

- 亲和力应为负；**正值 → 查中心来源与边长 → 重对接**（不变）。  
- 上机前：打印参考配体与中心距离、\(L_k\) 与 \(S_k\)；中心校验失败不得开跑。  
- **新批次 summary 缺 `center_source` → 不合格。**

---

## 5. 旧实现对照（本次事故）

| 旧做法 | 问题 | 新做法 |
|--------|------|--------|
| 全局 `size=22` | 误用论文下限当固定值；大配体转不开 / 与错误中心叠加致正结合能 | §3.1 按 query \(L_k+15\)，floor 22.5 |
| `hetatm_centroid` 平均全部非溶剂 HETATM | 多配体/多链被混平均；无 resname 选择 | §2.1 指定单一共晶配体 |
| 盲信库表 x/y/z | 表值可远离真实口袋（如 3d06） | §2.2 \(d\le 2\) Å 校验 |
| FGA 用 AF 整链 COM | SOP 与 Manual 均不支持 | 无位点则预测口袋或换结构，禁止 COM 打分 |

---

## 6. 审核清单（请勾选）

- [ ] 同意 **中心 = 单一共晶配体几何中心**（禁止全 HETATM 平均 / 整链 COM）  
- [ ] 同意 **库表坐标必须通过 ≤2 Å 校验** 否则重算  
- [ ] 同意 **边长 = max(L_query+15, 22.5)**（各向异性），**废除固定 22**  
- [ ] 同意生产对接 **不做** Trott 基准里的随机 +5 Å 偏置  
- [ ] 同意 \(S>30\) 时提高 exhaustiveness；\(S>40\) 默认拒绝  
- [ ] （可选）预测口袋允许 Feinstein \(2.857 R_g\)

审核意见请直接回复；通过后我再改脚本并重跑正结合能任务。

---

## 8. 第二轮交叉核对：方案不妥之处（2026-09-05）

> 本节在用户要求下，用**额外信源**回审 §2–§3；结论：**中心原则大体正确，定边默认式有多处不妥，不宜原样落地。**

### 8.1 额外信源

| 信源 | 类型 | 与定盒相关的要点 |
|------|------|------------------|
| [Meeko 教程（Forli Lab）](https://meeko.readthedocs.io/en/develop/tutorial1.html) | 现行 AutoDock 生态官方制备 | `--box_enveloping` 包住**参考配体文件** + `--padding 5`（每维两侧合计扩 **10 Å**），**不是** \(L+15\) / 固定 22.5 |
| Feinstein & Brylinski, *J Cheminform* 2015（[DOI](https://doi.org/10.1186/s13321-015-0067-5)） | 同行评审、3659 复合物 | 最优立方边长 ≈ **\(2.857\times R_g\)**；且该最优盒**系统小于** Trott 默认定边；Trott 默认相对偏大、精度较差 |
| Trott & Olson 2010 | Vina 原文 | \(L+15\) / floor 22.5 是**重对接基准**流程：AABB 来自**晶体结合态配体**，并故意随机偏置 |
| Vina Manual / ReadTheDocs FAQ | 官方 | “尽量小但别太小”；忌盲目 \(>30^3\)；体积 \(>27000\,\text{Å}^3\) 警告 |
| BioBB + Fpocket 教程 | 社区工作流 | 口袋外包一层约 **12 Å offset**（又一数值） |
| Agarwal et al., *Mol Inf* 2023（box×exhaustiveness） | 同行评审 | 大盒子时 exhaustiveness=1 明显变差；默认 8 多数尚可；\>25 收益有限 |

### 8.2 已确认的不妥（相对上一版 §3.1）

1. **误把 Trott 基准定边当成生产默认**  
   - Trott 的 AABB 对象是**复合物里的结合态配体**，目的是评估重对接；随机 +5 Å 是为防“正中心作弊”。  
   - 生产对接若用 PubChem 游离构象的 \(L_x,L_y,L_z+15\)，**坐标轴任意**，与口袋轴向无关，各向异性 \(S_k\) **物理意义弱**。  
   - Feinstein 明确：Trott 类默认盒往往**偏大**，最优反而更小（\(2.857 R_g\)）。

2. **与 Forli/Meeko 现行实践不一致**  
   - Meeko 推荐：参考配体 enveloping + **padding≈5 Å/侧**。  
   - 教程常用经验：最长边再加 **8–10 Å** 量级 → 类药分子常落在 ~18–25 Å。  
   - 上一版默认 \(L+15\)（且 floor 22.5）偏“基准测试宽松盒”，不是当今制备工具的首选。

3. **\(d\le 2\,\text{Å}\) 库表校验阈值无文献依据**  
   - 合理作工程门槛，但**不是**论文阈值；应标为 heuristic，可调（如 1.5–3 Å）。

4. **\(S>40\) 默认拒绝过硬**  
   - Manual 只强调大空间要加 exhaustiveness，未给 40 Å 硬拒。大盒子应警告 + 提 exhaustiveness，拒对接留给课题策略而非绝对物理定律。

5. **Feinstein \(2.857 R_g\) 也不是万能**  
   - 针对 Vina、立方盒、其数据集最优；eBoxSize 脚本常数与论文表述需核对实现。  
   - 适合虚筛自动化；位点对接若已有共晶，Meeko enveloping 往往更直观。

6. **中心正确仍不足以保证负结合能**  
   - Manual FAQ：质子化、诱导契合、打分函数最小值不在正确构象、exhaustiveness/运气均可失败。  
   - “正值→只查盒子”不完整，应并列检查配体/受体准备。

### 8.3 修订后的推荐默认（待审，替换原 §3.1 生产默认）

**中心（维持并强化）：** 单一共晶 / 对齐到口袋的参考配体几何中心（与 Meeko、教程一致）。禁止全 HETATM 平均、禁止整链 COM。

**边长（改推荐）：**

| 优先级 | 方法 | 公式/操作 | 适用 |
|--------|------|-----------|------|
| **A（首选）** | Meeko 式 enveloping | 对**参考共晶配体**（或对齐到位点的参考构象）做 AABB，每维加 `2×padding`，默认 **padding=5 Å**；若 query 的最大原子跨度 \(L_{\max}\) 明显更大，再把各边扩到至少 \(L_{\max}+2\times padding\) | 有共晶或可靠参考配体 |
| **B（虚筛/多配体）** | Feinstein | 立方边长 \(S=\max(2.857\,R_g^{\text{query}},\, S_{\min})\)，\(S_{\min}\) 建议 15–18（不必强行 22.5） | 库筛、配体尺寸差异大 |
| **C（仅复现论文基准）** | Trott 2010 | 结合态 AABB +10/+5、floor 22.5 | **仅** redock 基准，不作课题默认 |

**立方 vs 各向异性：** 位点对接默认可用各向异性 enveloping；若用 \(R_g\) 则用立方。避免用“游离配体任意取向的 \(L_x,L_y,L_z\)”直接当三边。

**大盒子：** \(V>27000\,\text{Å}^3\) 或任一边 \(>30\) → 提高 exhaustiveness（≥16–32）并警告；是否拒绝由课题定，不作绝对禁令。

## 9. 关于 d≤2 Å 与 S>40：废止说明 + 近期信源（2022–2024）

### 9.1 \(d\le 2\,\text{Å}\)

- **已废止作为硬质控定数。** 仅为早期工程草稿，**无论文阈值支撑**。  
- 库表中心策略改为：**直接按单一共晶配体重算并覆盖**（脚本 `重算蛋白表中心_recenterProteinTable.py`），不再用“与旧坐标差 ≤2 Å 才采纳”。  
- `delta_old_new_A` 仅作审计字段，不作通过/拒绝阈值。

### 9.2 \(S>40\) 一律拒绝 —— **为什么曾写、为何废止**

- **来源：** 笔者对 Vina Manual「避免大于约 \(30\times30\times30\)」的**过度引申**，自行加了 40 Å 硬拒；**不是** Manual / 论文条文。  
- **废止理由：**  
  - Manual 只要求大搜索空间时**提高 exhaustiveness**，允许忽略体积警告。  
  - **2023** Results Eng. 批处理 Vina 参数研究在统计最优下使用约 **\(4.5\times R_g\)**（可放宽到 **4–5×\(R_g\)**），示例边长可到 **~30 Å**，并未设 40 Å 禁令。  
  - **2022** Agarwal et al. *Mol. Inf.*：关注 box×exhaustiveness 对 RMSD；大盒子时忌 exhaustiveness=1，默认 ≥8，\>25 收益有限——同样**无 S>40 拒绝规则**。

### 9.3 近期可信定边标准（替代 2015 单点迷信）

| 年份 | 信源 | 结论（定边/搜索） |
|------|------|-------------------|
| **持续维护** | [Meeko / Forli Lab](https://meeko.readthedocs.io/en/develop/tutorial1.html) | `--box_enveloping` + **`--padding 5`**（现行制备官方教程） |
| **2023** | Yu et al., *Results in Engineering* — batch Vina 参数 ([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2590123023004620)) | 批评 Feinstein **2.857\(R_g\) 偏小**且与脚本不一致；推荐 **exhaustiveness=16**，立方盒约 **\(4.5\times R_g\)**（可 **4–5×\(R_g\)**）；中心取结合位点几何中心 |
| **2022** | Agarwal et al., *Molecular Informatics* ([DOI 10.1002/minf.202200188](https://doi.org/10.1002/minf.202200188)) | PDBbind 上系统变 box 与 exhaustiveness；**exhaustiveness≥8**；大盒子更需足够搜索；\>25 性价比低 |
| **官方 FAQ** | Vina Manual / ReadTheDocs | 尽量小；忌盲目 \(>30^3\) 除非加 exhaustiveness；体积 \(>27000\,\text{Å}^3\) 警告 |

**本仓库生产默认（更新）：**

1. **中心：** 单一共晶配体重原子几何中心（库表已重算）；无有机共晶 → **清空中心并标记 FAIL**，换 PDB / 注释位点 / 预测口袋，禁止整链 COM。  
2. **边长：** 优先 **Meeko enveloping + padding=5**，并保证覆盖 query；批处理虚筛可采用 **2023** 建议的 **\(4\)–\(5\times R_g\)** + **exhaustiveness≥16**。  
3. **大盒子：** 任一边 \(>30\) 或 \(V>27000\) → **警告并提高 exhaustiveness**，**不**因 S>40 自动拒绝。

### 9.4 库表重算结果摘要（本机已执行）

- 备份：`分子对接_蛋白表.bak_before_recenter_*.csv`  
- 新表含：`ref_ligand` / `center_method` / `center_note` / `delta_old_new_A`  
- **课题相关：** TP53/`3d06` → `FAIL_no_organic_ligand`（无有机共晶，须换结构）；FGA/AF → 禁止 COM；其余如 AKT1/EGFR/ESR1/MAPK1/… 已按共晶配体重写中心。  
- 自动选配体规则会排除糖基/常见结晶试剂，并降低 HEM/核苷酸等辅因子优先级；**仍可能误选**，FAIL 与可疑 `ref_ligand` 须人工审核。
