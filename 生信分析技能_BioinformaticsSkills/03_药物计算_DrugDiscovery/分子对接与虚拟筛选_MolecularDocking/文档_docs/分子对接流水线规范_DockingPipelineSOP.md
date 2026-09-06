# 分子对接流水线规范 / DockingPipelineSOP

> **状态：** 生效；**对接与交付已 FROZEN（2026-09-05；2026-09-06 增补 detail 导出 + result 拼图定稿 §7.3/§7.4）** — 见 [`对接与交付约束_DockingFrozen.md`](对接与交付约束_DockingFrozen.md)  
> **默认引擎路线：** [`技术路线_AutoSite_AutoDockGPU.md`](技术路线_AutoSite_AutoDockGPU.md)  
> **技能入口：** [`../技能说明_分子对接与虚拟筛选_MolecularDocking.md`](../技能说明_分子对接与虚拟筛选_MolecularDocking.md)  
> **出图回退：** 领域条款未写明时，先用 [统一可视化规范_VizStandards](../../../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)（热图标签黑色 `#000000`）  
> **交付命名：** [统一交付规范_DeliveryStandards](../../../../00_基础_Foundation/统一交付规范_DeliveryStandards/技能说明_统一交付规范_DeliveryStandards.md)  
> **不做：** 共晶配体重对接 + RMSD 自检（非验收步骤）

---

## 0. 总流程

```text
下载结构 → 目录命名与清洗加氢 → 定心定盒（登记 center_source）
    → config / AutoGrid → AutoDock-GPU（或 Vina 对照）→ 登记表 + summary（含中心方法）
    → 结合能矩阵/热图 → PyMOL（ST/PT/CJ/QJ）三视图 + 可选 result 拼图
```

禁止编造亲和力或虚构 PDB/CID。**禁止**交付不含 `center_source` 的新对接批次（见 [`中心位点方法登记_CenterSourceRegistry.md`](中心位点方法登记_CenterSourceRegistry.md)）。

---

## 1. 下载与本地结构库（强制优先级）

**本机结构库根目录（强制优先读取）：** `D:\数据库\分子对接数据库\`  
（清洗后产物通常在 `D:\数据库\分子对接数据库\test\`：`big/` `big_clean/` `big_clean_h/` `small/` `small_clean/` `small_clean_h/`；登记表在库根 `分子对接_蛋白表.csv` / `分子对接_化合物表.csv` / `化合物_CID命名对照.csv`。）

| 优先级 | 来源 | 说明 |
|--------|------|------|
| **1（首选）** | `D:\数据库\分子对接数据库\` | 已下载/已清洗的受体 PDBQT、配体 CID PDBQT、登记表中心坐标；**禁止**库内已有时再重复下载 |
| 2 | RCSB PDB / AlphaFold | 仅当库内无对应 PDB / UniProt 条目 |
| 3 | PubChem `SDF?record_type=3d` | 仅当库内无对应 CID 的 3D 配体 |

| 类型 | 来源 | 要求 |
|------|------|------|
| 受体 | **先查本地库** → RCSB / AlphaFold | 记录 UniProt、PDB ID、链；**优先含共晶配体**。盒子中心/边长见 **§3.1** 与 [`对接盒子定心与定边_DockingBoxProtocol.md`](对接盒子定心与定边_DockingBoxProtocol.md)；库表 `x/y/z` 仅候选，须与指定共晶配体质心校验（\(d\le 2\) Å） |
| 配体 | **先查本地库 `small*_clean_h/{CID}_clean_h.pdbqt`** → PubChem 3D | 记录 CID；下载后校验原子块 z-span（须明显非平面）；大分子多糖/聚合物通常不对接 |

失败回退：本地已有 3D SDF/MOL2；仅当无 PubChem 3D 时才用 SMILES + Open Babel 建 3D。勿静默跳过不记日志。

**Agent 约定：** 用户课题对接时，默认 `--lib-root D:\数据库\分子对接数据库`；交付项目可在桌面（金标序号文件夹），但结构文件优先从库拷贝/软链，不另起平行下载树。

**Windows / Vina 路径硬性约定：**
- AutoDock Vina（本机 `E:\vina\vina.exe`）**不能**把含中文的路径当 cwd / `--config`；桌面工程名须用 **ASCII**（如 `PDAC_compounds_docking`）。中文说明可用旁路 txt。
- 本地库 `big*_clean_h/*.pdbqt` 若含 `ROOT`/`BRANCH`（配体式扭转树），**不可**直接作受体；须 `obabel -xr` 或仅保留 `ATOM` 行再对接。

**批量结构库脚本（2026-08-31 登记）：**
- [`脚本_scripts/结构库准备_prepareStructureLibrary.py`](../脚本_scripts/结构库准备_prepareStructureLibrary.py)：按 `分子对接_蛋白表.csv` / `分子对接_化合物表.csv` 全量下载 + 清洗 + 加氢到 `big*/small*` 六目录（幂等；PDB ID 走 RCSB，UniProt 条目走 AlphaFold v6→v4）。支持 `--workers N` 并行、`--protein-table/--compound-table` 指定扩展清单、`--max-gb` 库容上限；配体文件以 CID 命名。
- [`脚本_scripts/结构库修补_repairStructureLibrary.py`](../脚本_scripts/结构库修补_repairStructureLibrary.py)：盐型 CID → PUG 名称解析母体 CID；平面分子（z-span≈0 如苯甲酸）放行；含 Si 配体（Vina 不支持）跳过 pdbqt 并记 `SKIP_unsupported`。
- [`脚本_scripts/结构库策展_curateStructureLists.py`](../脚本_scripts/结构库策展_curateStructureLists.py)：策展扩展清单——蛋白（RCSB 人源 X-ray ≤3.0Å、含非聚合物实体、按分辨率排序、每 UniProt 限 2 个）与化合物（ChEMBL max_phase 4→3→2 上市药，InChIKey→PubChem CID，与既有 CID 去重）。
- [`脚本_scripts/化合物CID重命名_renameCompoundsToCid.py`](../脚本_scripts/化合物CID重命名_renameCompoundsToCid.py)：存量配体文件语义名 → CID 命名一次性迁移（幂等；撞车保留先见，输出对照表）。
- 已知坑：RCSB 超大复合物无 legacy PDB（404）时下 `.cif` 再 obabel 转 PDB（如 9CMK）；obabel 日志 "20 molecules converted" 含子串 "0 molecules converted"，判失败须用词边界；RCSB search API v2 的 `request_options` 是对象不是 v1 的键值列表。

**Open Babel 硬性约定（本机常见坑）：**
- **禁止**对黄酮等刚性芳香体系默认 `--gen3d`（易崩溃或写出全零/压扁坐标，报错如 `Rigid fragment … all zero coordinates`）。
- 标准路径：`PubChem 3D SDF → obabel -h → MOL2 → PDBQT（gasteiger）`，**不要**再 `--gen3d`。
- PyMOL 出图前：将 Vina pose **PDBQT→PDB** 再 `load`；直接 load PDBQT（原子类型 `OA`/`A`/`HD`）易错键，看起来像压扁配体。

---

## 2. 目录与命名规范（金标：痤疮_分子对接_序号文件夹）

**交付结构金标（强制对齐）：** 桌面 `痤疮_分子对接_序号文件夹/`（含 git、`图片/` 内 big/surface/detail/result、任务根 `.pse`、无 `_png_tmp`）。

### 2.1 项目根（痤疮式：序号直接挂在根下）

```text
痤疮_分子对接_序号文件夹/          # ← 金标项目根
  .git/  .gitignore                # 强制 git；忽略 _png_tmp/ 等
  1/ … N/                          # 每个对接任务一个数字目录
  summary_adgpu.csv                 # 默认；含 center_source（强制）
  summary_vina.csv                  # 可选对照；同样须含 center_source
  分子对接_蛋白表.csv               # 含受体级 center_source/ref_ligand
  分子对接_化合物表.csv
  分子对接组合信息表.csv           # 可选备份；主登记仍是蛋白表/化合物表
  分子对接结合能信息.xlsx
  矩阵_结合能热图_DockingAffinityHeatmap.png
  矩阵_结合能热图_DockingAffinityHeatmap.svg
  文件夹内容说明.txt               # 可选
```

每任务建议另有 `task_info.txt`（`center_source` 等，见 CenterSourceRegistry）。
### 2.2 单任务目录（金标见 `…/10`）

```text
N/
  config.txt
  {PDB}_clean_h.pdbqt              # 如 4KIK_clean_h.pdbqt
  {ligand}_clean_h.pdbqt           # 如 lactic_acid_clean_h.pdbqt
  output.pdbqt
  log.txt
  task_info.txt
  big-N.pse
  surface-N.pse
  detail-N.pse                     # 手调标签后只改此文件；禁止脚本写回
  图片/                            # 所有 PNG 只在这里
    big-N.png
    surface-N.png
    detail-N.png
    result_N.png                   # big+detail 拼图（满意交付必备）
  # 禁止：_png_tmp/、任务根散落 *.png
```

### 2.3 多组合项目（努力学习式）

在金标任务结构之上，可另有：

```text
努力学习_分子对接/
  序号文件夹/N/                    # 与 §2.2 同构
  可视化组合_Top10/
    {序号}_{蛋白}_{PDB}_{成分}/
      big|surface|detail-*.pse
      组合信息.txt
      图片/
        big|surface|detail|result-*.png
    README.txt
```

上游准备目录（可选，可在项目外）：`big/` `small/` `big_clean/` `small_clean/` `big_clean_h/` `small_clean_h/`。

### 2.4 任务目录强制约定

1. **结构金标**：`痤疮_分子对接_序号文件夹/10`。  
2. **禁止**任务内 `_png_tmp/`；发现即删。  
3. **所有 PNG**（big/surface/detail/**result**）**只**在 `图片/`。  
4. **`.pse` 只在任务根**（或 Top10 子目录根），不进 `图片/`。  
5. **Git**：项目根须 git；`.gitignore` 至少 `_png_tmp/`、`Thumbs.db`、`.DS_Store`。手调 `.pse` 后先 commit 再批量操作。

命名要点：受体 `{PDB}_clean_h.pdbqt`；**配体自 2026-08-31 起一律以 PubChem CID 命名**（如 `442048_clean_h.pdbqt`；存量语义英文名文件由 `脚本_scripts/化合物CID重命名_renameCompoundsToCid.py` 一次性迁移，对照见 `D:\数据库\分子对接数据库\化合物_CID命名对照.csv`）；图面 **English**。

---

## 3. 文件处理（准备）

1. **受体**：去水、去非目标配体/离子（按课题保留辅因子）；加氢 → PDBQT。  
2. **配体**：必须用真实 3D 坐标（优先 PubChem `record_type=3d`）→ 加氢 → PDBQT；禁止在已有 3D SDF 上再跑 `--gen3d`。  
3. **对接盒子**（强制；细则 SSOT：[`对接盒子定心与定边_DockingBoxProtocol.md`](对接盒子定心与定边_DockingBoxProtocol.md)，含 **§8 第二轮交叉核对**）：  
   - **中心**：指定**单一**共晶配体（`resname+chain[+resi]`）的几何中心；或文献/注释活性位点；再否则口袋预测（须标注）。**禁止**整链 COM；**禁止**对 PDB 内全部非溶剂 `HETATM` 无差别平均；**禁止**未校验照抄库表坐标。  
   - **边长（待审，见协议 §8.3 / §9）**：**优先** Meeko enveloping + **padding≈5 Å/侧**；批处理虚筛可采用 **2023** 研究建议的立方盒约 **\(4\)–\(5\times R_g\)** + **exhaustiveness≥16**。Trott 2010 / Feinstein 2015 不作唯一默认。**禁止**全局固定 `size=22`。  
   - 任一边 \(>30\) 或体积 \(>27000\,\text{Å}^3\)：提高 `exhaustiveness`（≥16，建议 32）并**警告**；**禁止**以 \(S>40\) 硬拒（无文献依据，已废止）。  
   - 库表中心：**按共晶配体重算覆盖**（`重算蛋白表中心_recenterProteinTable.py`）；**废止** \(d\le2\) Å 采纳阈值。  
   - 依据：Vina Manual；Meeko 教程；Agarwal 2022 *Mol. Inf.*；Yu et al. 2023 *Results Eng.*。  
4. **config.txt** 至少含：`receptor` `ligand` `center_x/y/z` `size_x/y/z`（Vina）或对应 AD-GPU 地图参数；并在 **`task_info` 强制记录** `center_source`（受控词表见 [`中心位点方法登记_CenterSourceRegistry.md`](中心位点方法登记_CenterSourceRegistry.md)）+ `ref_ligand` / `size_method` / `box_qc` / `fallback_used` / `padding` 或 `Rg`。

### 3.1 废止的错误做法（2026-09-05）

| 废止 | 原因 |
|------|------|
| 固定立方边长 22 Å | 22.5 Å 在 Vina 论文中是**下限**，不是万能边长 |
| `hetatm_centroid` 平均所有非溶剂 HETATM | 不是“某一个 bound ligand”的质心 |
| 盲信 `分子对接_蛋白表.csv` 的 x/y/z | 表值可远离真实口袋，必须校验 |
| AlphaFold 全长 COM 当打分盒 | 违反 Manual“搜索空间应尽量小且对准位点” |

---

## 4. 对接与打分

- **默认引擎：** AutoDock-GPU（见 [`技术路线_AutoSite_AutoDockGPU.md`](技术路线_AutoSite_AutoDockGPU.md)）；Vina 仅可选对照，**分表**（`summary_adgpu.csv` ≠ `summary_vina.csv`）。  
- 解析最佳能量写入对应 summary；**同一行必须带 `center_source`**。  
- **质控**：正常为 **负数**；正值 → 查该行 `center_source`/`size_*`/`box_qc` → 重定盒再对接。

---

## 5. 登记表 vs 结果表（强制）

| 表 | 一行是什么 | 是否枚举全部组合 |
|----|------------|------------------|
| `分子对接_蛋白表.csv` | 一个受体（含受体级定心方法） | 否 |
| `分子对接_化合物表.csv` | 一个配体 | 否 |
| `summary_adgpu.csv` / `summary_vina.csv` / 结合能矩阵 | 实际跑过的蛋白×成分（含**任务级** `center_source`） | 是（仅已对接） |

列约定：蛋白至少 `entry号, 蛋白质靶点, 蛋白质3D结构名称, x/y/z center, center_source|center_method, ref_ligand, center_note`；化合物 `活性成分名称, 活性成分重命名, 活性成分3D结构名称`。

**每个对接任务如何说明中心方法（强制）：** 见 [`中心位点方法登记_CenterSourceRegistry.md`](中心位点方法登记_CenterSourceRegistry.md)。常用码：`cocrystal_meeko` / `cocrystal` / `autosite` / `p2rank` / `fpocket` / `annotated_site` / `manual` / `FAIL`。

**`summary_*.csv` schema（SSOT，脚本见 `脚本_scripts/dock_summary_schema.py`）：**

```text
task,protein,pdb,ligand,ligand_name,cid,affinity_kcal_mol,center_source,center_detail,size_method,box_qc,fallback_used,engine
1,KIT,1T46,quercetin,Quercetin,5280343,-10.5,cocrystal_meeko,STP:A:301,meeko_enveloping,PASS,,adgpu
```

- **新写必须含** `center_source` 及后续扩展列；缺省视为不合格批次。  
- 旧工程仅有亲和力列时，读取脚本可容忍；补登须按真实方法回填，禁止臆造。  
- legacy 中文列由 `dock_summary_schema.load_summary_rows()` 归一化；禁止在新脚本扩散旧列名。

---

## 6. 结合能矩阵与热图

- Excel：行=蛋白，列=化合物，单元格=最佳亲和力（kcal/mol）。  
- 矩形热图：DPI≥600；PNG+SVG；图面 English；文件名如 `矩阵_结合能热图_DockingAffinityHeatmap`。  
- **色标仅非正值**：`vmax=0`；**禁止** `extend` 三角箭头；**禁止**总标题、轴标题、色标标题、底部脚注（FROZEN）；格内与刻度名仍黑色。  
- **一对多圆环仪表盘（可选）**：[`脚本_scripts/plot_docking_ring_heatmap.py`](../脚本_scripts/plot_docking_ring_heatmap.py)  
  - 圆心=蛋白/PDB；圆环扇区颜色随结合能连续变化并标注数值；外周扇区放各任务 `result_N.png`  
  - 输出：`圆环_一对多对接结合能_DockingRingHeatmap.png/.svg`  
- **标签一律黑色 `#000000`**。

---

## 7. PyMOL 可视化规范（ST / PT / CJ / QJ）

标准脚本：[`脚本_scripts/pymol_dock_viz_standard.py`](../脚本_scripts/pymol_dock_viz_standard.py)（解释器常用 `E:\pymol\python.exe`）。

### 7.1 对象语义

| 对象 | 含义 | 显示 |
|------|------|------|
| **ST** | 完整受体（对接口袋由定心工具+盒子决定；**禁止**可视化阶段为减负删除 ST 原子） | big/detail：**cartoon**；surface：**仅 surface（无 cartoon）** |
| **PT** | 最佳对接姿态配体（AD-GPU 或 Vina 对照） | sticks |
| **QJ** | PT↔受体氢键 | 黄色虚线 |
| **CJ** | **仅参与 QJ 的残基** | **橙色** sticks；无氢键不显示 |

```python
cmd.distance("QJ", "(PT)", "(not PT)", quiet=1, mode=2, label=1, reset=1)
pairs = cmd.find_pairs("(PT and elem N+O)", "((not PT) and elem N+O)", mode=2, cutoff=3.2)
# 若空则 cutoff=3.5；禁止全原子 find_pairs 回退
```

**detail 标签：** 一位小数；`label_font_id=5`；字号 **24**；不外推；用户在 `.pse` 手调位置。

**完整入画（强制释义）：** 只改**相机**——`orient`/`zoom(complete=1)` 把当前要入画的对象都框进视口，并放宽 near/far clip，避免丝带被切黑。**不是**删除受体原子，也**不是**用「配体 14 Å」再造一个可视化口袋。对接口袋已在定心步骤由共晶/AutoSite/P2Rank/… 与盒子给出。

**detail 导出前自动选角（强制）：** 截图是 2D。在写 `detail-N.png` / `.pse` 前，脚本须旋转复合物视角，使配体、氢键、氢键标签、残基及残基标签在投影上尽量少互相遮挡；之后仍保留用户手调标签断点。

### 7.2 三视图文件

| 文件 | 内容 |
|------|------|
| `big-N.png` / `.pse` | ST cartoon + CJ + PT + QJ；无标签 |
| `surface-N.png` / `.pse` | 仅 ST surface + CJ/PT/QJ；无标签 |
| `detail-N.png` / `.pse` | ST 透明 cartoon + CJ/PT/QJ + 残基/氢键标签 |
| `result_N.png` | 左侧 big 局部放大框 + 右侧 detail（见 §7.4） |

首次自动出图：big/surface 可用 `cmd.png`；detail 首次可用 `png`。**手调标签后的 detail 禁止再用 `cmd.png`（标签会相对变小），必须走 §7.3 截图。**

默认尺寸（对齐 GUI Save Image → **Draw (fast)**）：big/surface **5040×3653**；**dpi=600**；**ray=0（禁止 Ray）**；白底。  
首轮 **detail 只写 `.pse`，不用 `cmd.png`**（避免标签相对变小）；手调后用 `export_detail_png_from_pse.py` **截图**导出 `detail-N.png`。  
批处理只 **load 一次** 结构，再切换 big/surface/detail 显示。

### 7.3 手调 detail 后重导出（定稿 · 2026-09-06 用户确认）

脚本：[`export_detail_png_from_pse.py`](../脚本_scripts/export_detail_png_from_pse.py)  
钩子：[`pymol_detail_export_hook.py`](../脚本_scripts/pymol_detail_export_hook.py)

**第一原则：清晰完整。** 中心残基、配体、氢键、标签必须全部在 `detail-N.png` 画面内；拼图阶段找不回被截掉的内容。宁可略空，不要裁切。

#### 禁止

- 再跑 `pymol_dock_viz_standard.py` 重建该任务（会覆盖 `.pse`）
- `cmd.save` / 任何写回或改动 `.pse`
- 用 `cmd.png` 定稿带标签的 detail（标签会相对变小）
- `cover` 居中裁切宽视口成正方形（会切掉左右内容）
- 按颜色/内容检测再缩小裁切 detail（浅色标签与丝带晕染同色，检测必翻车）
- 无用户点名时全量重跑 / `collect --force-wipe`

#### 强制流程（每任务只开一次 PyMOLWin）

1. `PyMOLWin.exe "detail-N.pse" -r pymol_detail_export_hook.py`  
   （禁止嵌套 `finish_launching`；禁止在 PyMOL 内 `run hook,main`，`__file__` 会错位）
2. **最大化窗口**（`showMaximized` + Win32 `SW_MAXIMIZE`，日志须 `IsZoomed=True`；截图前再压一次）。  
   手调标签在最大化视口里完成，截图必须同一窗口状态，标签相对布局才不变。
3. 隐藏右侧对象面板（Qt dock）+ 收起底部代码区（`toggle_command_log(False)` 等），让 3D 视口尽量大。
4. **取景（只改缩放/居中，保留手调旋转）**  
   - **始终** `zoom(PT or CJ, buffer, complete=1)`（无 CJ 则 `PT`）。  
     **禁止**「手调取景更宽就保留」——过宽会使内容只占画面约三成。  
     `cmd.zoom` 本身不改旋转矩阵；**禁止** zoom 后再写回旧旋转（会挤偏中心）。  
   - `buffer` 默认 **4 Å**（环境变量 `PYMOL_DETAIL_BUFFER`；越大越空、越小越满，过小易切标签引线）。  
   - 宽屏上 zoom 常被横向撑满，中间裁正方形后显得偏小：按正方形内内容占比**自适应拉近**（改 `get_view()[11]` 相机距离）。  
     - 目标满度默认 **0.72**（`PYMOL_DETAIL_FILL_TARGET`；金标 detail-4 可靠内容约 71% 宽）。  
     - 测 span 时 ×**1.15** 标签余量（`PYMOL_DETAIL_LABEL_PAD`；浅色标签常不进 sticks 掩膜）。  
     - 拉近下限 `factor≥0.75`（不要一次拉太狠）。曾用目标 0.88 过紧会切标签，已废止。
5. 截客户区 → **顶栏剥离**（浅色标题条 + 深色菜单/工具条，按行均亮度；**不用**「纯白占比>0.7 才算视口」——丝带铺满时白占比常 <0.5，会误切半屏）→ `strip_dark_chrome_edges` 二次保险 → 取**视口几何中心**正方形（边长=视口高）→ 等比放大到 **6000×6000**、dpi=600。  
   交付物是 `detail-N.png`；`detail-N_debug_window.png` 仅调试用（含菜单黑边），**不得**当交付、验收完应删除。
6. 校验 `.pse` mtime/size 未变。  
   **产物新鲜度：** PyMOLWin 可能是启动器（subprocess 立即返回），须轮询 `detail-N.png` 的 mtime ≥ 启动时刻再验收。

```bat
python …\export_detail_png_from_pse.py --root "…\某任务目录或序号根"
REM 显式 --root 时只处理该路径；每任务只开一次 PyMOLWin
```

批量（努力学习 Top10 + 痤疮）：[`run_nuli_ting_detail_combine.py`](../脚本_scripts/run_nuli_ting_detail_combine.py)。

### 7.4 result 拼图（big + detail → result_N.png）（定稿 · 2026-09-06 用户确认）

实现：`E:\PythonProject\分子对接\2.分子对接结果图组合.py`（背景模板 `背景图.png` 同目录）。  
布局金标：杨程茗 `result_*.png`；满度/构图参照用户审核通过的 detail-4 / result_4。

**效力序（高→低，后者不得破坏前者）：**

| # | 规则 |
|---|------|
| 1 | **左右不重叠**；左图**完整展示**丝带、氢键、残基、配体 |
| 2 | 右图：内容**完整** + **锁纵横比** + 尽可能放大并**抵住虚线** |
| 3 | 左图：氢键/残基/配体在实线黑框内并尽可能抵框（不得破坏 #1） |

**左图（big）**

- 完整铺开蛋白丝带、氢键、残基、配体。  
- **实线黑框只是「放大区域」标注，不是裁切框**——禁止把左图裁进黑框、禁止裁掉丝带。  
- 以残基+配体+氢键并集为锚缩放，使关键簇尽量落入实线小框；粘贴整图，只裁画布越界及与右虚线框重叠区。

**右图（detail）**

- **完整性在 §7.3 截图阶段保证**；拼图找不回被截掉的内容。  
- **不做内容检测裁切**（浅色标签颜色不定，与丝带晕染/底色无法可靠区分）。  
- 仅裁四边**纯白带**（整行/整列近白才算空）→ **等比**缩放铺满虚线框（锁纵横比，禁止横纵独立缩放）：受限维度抵住虚线、不变形。  
- 要更大/更小内容占比：调 §7.3 的 `PYMOL_DETAIL_BUFFER` / `PYMOL_DETAIL_FILL_TARGET` 后**重导 detail**，不要在拼图里裁。

**输出：** 11520×6480，dpi=600 → 任务 `图片/result_N.png`。

**配色变量（与 PyMOL 对齐；裁切/定位不得写死单一色相）：**

| 变量 | PyMOL / 拼图 CLI | 默认 | 含义 |
|------|------------------|------|------|
| `protein_color` | `--protein-color` | `cyan` | ST 丝带（拼图排除用） |
| `residue_color` | `--residue-color` | `orange` | CJ 残基 sticks |
| `hbond_color` | `--hbond-color` | `yellow` | QJ 氢键虚线 |
| `ligand_spectrum` | `--ligand-spectrum` | `rainbow` | PT 配体：`rainbow` 或实心色名 |

- 同批组合部位颜色不同：拼图加 `--auto-colors`（按每张 detail 推断），或 `--palette-json=`（`default` + `by_index`，见 `脚本_scripts/collage_palette.example.json`）。  
- 指定配色若残基几乎检不出，引擎回退到该图推断，避免整批失败。  
- 换色只改变量，不改本节几何规则。  

### 7.5 多组合汇总

- `可视化组合_Top10/`：结构同 §2.3；`collect_nuli_viz_top10.py` 默认 merge。  
- 手调后禁止无确认 `--force-wipe`。

---

## 8. 与其它技能的关系

- 网络药理学选靶/选成分 → 本技能对接验证。  
- PyMOL/登记/金标目录：**本 SOP 优先**；热图未另写时回退 VizStandards。  
- 网药 FROZEN 图册不得被本技能改样式。

---

## 9. 验收清单

- [ ] 项目根对齐金标：数字任务目录 + 登记表 + summary + 热图；已 git  
- [ ] **每个已对接任务**的 summary / `task_info` 均有合法非空 `center_source`（见 CenterSourceRegistry）  
- [ ] 单任务同 `…/10`：config/output/log/pdbqt + 三视图 `.pse` + `图片/` 四类 PNG（含 `result_N.png`）  
- [ ] 无 `_png_tmp/`；PNG 不在任务根  
- [ ] 亲和力为负（或已注明并修正）；解读时点明对应 `center_source`  
- [ ] 热图黑标签；DPI≥600；**colorbar 无正值（vmax=0）**  
- [ ] big：ST=cartoon，CJ=仅 QJ 残基  
- [ ] 手调 detail 仅用截图导出；`.pse` 未改；**detail 截图内中心残基/配体/氢键/标签全部在画面内**；result 符合 §7.4：左右不重叠、左图完整铺开且黑框套住口袋、右图锁纵横比、内容完整并抵住虚线  
