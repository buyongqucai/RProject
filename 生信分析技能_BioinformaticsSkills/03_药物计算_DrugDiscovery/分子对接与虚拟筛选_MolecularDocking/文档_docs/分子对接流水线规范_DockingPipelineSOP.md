# 分子对接流水线规范 / DockingPipelineSOP

> **状态：** 生效（2026-08-08；金标交付结构以桌面「痤疮_分子对接_序号文件夹」为准）  
> **技能入口：** [`../技能说明_分子对接与虚拟筛选_MolecularDocking.md`](../技能说明_分子对接与虚拟筛选_MolecularDocking.md)  
> **出图回退：** 领域条款未写明时，先用 [统一可视化规范_VizStandards](../../../../00_基础_Foundation/统一可视化规范_VizStandards/技能说明_统一可视化规范_VizStandards.md)（热图标签黑色 `#000000`）  
> **交付命名：** [统一交付规范_DeliveryStandards](../../../../00_基础_Foundation/统一交付规范_DeliveryStandards/技能说明_统一交付规范_DeliveryStandards.md)

---

## 0. 总流程

```text
下载结构 → 目录命名与清洗加氢 → 序号任务 config
    → Vina 打分/姿态 → 登记表 + 结合能矩阵/热图
    → PyMOL（ST/PT/CJ/QJ）三视图 + 可选 result 拼图
```

禁止编造亲和力或虚构 PDB/CID。

---

## 1. 下载

| 类型 | 来源 | 要求 |
|------|------|------|
| 受体 | RCSB PDB / AlphaFold | 记录 UniProt、PDB ID、链；优先含共晶配体以便定盒子中心 |
| 配体 | **优先** PubChem `SDF?record_type=3d` | 记录 CID；下载后校验原子块 z-span（须明显非平面）；大分子多糖/聚合物通常不对接 |

失败回退：本地已有 3D SDF/MOL2；仅当无 PubChem 3D 时才用 SMILES + Open Babel 建 3D。勿静默跳过不记日志。

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
  summary_vina.csv
  分子对接_蛋白表.csv
  分子对接_化合物表.csv
  分子对接组合信息表.csv           # 可选备份；主登记仍是蛋白表/化合物表
  分子对接结合能信息.xlsx
  矩阵_结合能热图_DockingAffinityHeatmap.png
  矩阵_结合能热图_DockingAffinityHeatmap.svg
  文件夹内容说明.txt               # 可选
```

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

命名要点：受体 `{PDB}_clean_h.pdbqt`；配体语义化英文名 + `_clean_h.pdbqt`；图面 **English**。

---

## 3. 文件处理（准备）

1. **受体**：去水、去非目标配体/离子（按课题保留辅因子）；加氢 → PDBQT。  
2. **配体**：必须用真实 3D 坐标（优先 PubChem `record_type=3d`）→ 加氢 → PDBQT；禁止在已有 3D SDF 上再跑 `--gen3d`。  
3. **对接盒子**：中心取 **共晶配体质心或已知活性位点**；禁止仅用整链 COM。  
4. **config.txt** 至少含：`receptor` `ligand` `center_x/y/z` `size_x/y/z` `exhaustiveness` `num_modes` `out`。

---

## 4. 对接与打分

- 引擎：AutoDock Vina（或兼容）。  
- 解析 `log.txt` 第 1 模式亲和力写入 `summary_vina.csv`。  
- **质控**：正常为 **负数**；正值 → 查盒子 → 重对接。

---

## 5. 登记表 vs 结果表（强制）

| 表 | 一行是什么 | 是否枚举全部组合 |
|----|------------|------------------|
| `分子对接_蛋白表.csv` | 一个受体 | 否 |
| `分子对接_化合物表.csv` | 一个配体 | 否 |
| `summary_vina.csv` / 结合能矩阵 | 实际跑过的蛋白×成分 | 是（仅已对接） |

列约定：蛋白 `entry号, 蛋白质靶点, 蛋白质3D结构名称, x/y/z center`；化合物 `活性成分名称, 活性成分重命名, 活性成分3D结构名称`。

**`summary_vina.csv` 唯一 schema（SSOT，脚本实现见 `脚本_scripts/dock_summary_schema.py`）：**

```text
task,protein,pdb,ligand,ligand_name,cid,affinity_kcal_mol
1,KIT,1T46,quercetin,Quercetin,5280343,-10.5
```

新写一律用 canonical 英文列。legacy 中文列（`对接序号/蛋白/PDB/成分/CID/best_affinity_kcal`）由 `dock_summary_schema.load_summary_rows()` 归一化读取，禁止在新脚本中直接扩散旧列名。

---

## 6. 结合能矩阵与热图

- Excel：行=蛋白，列=化合物，单元格=最佳亲和力（kcal/mol）。  
- 矩形热图：DPI≥600；PNG+SVG；图面 English；文件名如 `矩阵_结合能热图_DockingAffinityHeatmap`。  
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
| **ST** | 口袋受体 | big/detail：**cartoon**；surface：**仅 surface（无 cartoon）** |
| **PT** | Vina 最佳姿态配体 | sticks |
| **QJ** | PT↔受体氢键 | 黄色虚线 |
| **CJ** | **仅参与 QJ 的残基** | **橙色** sticks；无氢键不显示 |

```python
cmd.distance("QJ", "(PT)", "(not PT)", quiet=1, mode=2, label=1, reset=1)
pairs = cmd.find_pairs("(PT and elem N+O)", "((not PT) and elem N+O)", mode=2, cutoff=3.2)
# 若空则 cutoff=3.5；禁止全原子 find_pairs 回退
```

**detail 标签：** 一位小数；`label_font_id=5`；字号 **24**；不外推；用户在 `.pse` 手调位置。

### 7.2 三视图文件

| 文件 | 内容 |
|------|------|
| `big-N.png` / `.pse` | ST cartoon + CJ + PT + QJ；无标签 |
| `surface-N.png` / `.pse` | 仅 ST surface + CJ/PT/QJ；无标签 |
| `detail-N.png` / `.pse` | ST 透明 cartoon + CJ/PT/QJ + 残基/氢键标签 |
| `result_N.png` | 左侧 big 局部放大框 + 右侧 detail（见 §7.4） |

首次自动出图：big/surface 可用 `cmd.png`；detail 首次可用 `png`。**手调标签后的 detail 禁止再用 `cmd.png`（标签会相对变小），必须走 §7.3 截图。**

默认尺寸：big/surface **9120×4164**；detail **6000×6000**；dpi=600；ray=0；白底。

### 7.3 手调 detail 后重导出（强制四步）

脚本：[`export_detail_png_from_pse.py`](../脚本_scripts/export_detail_png_from_pse.py)

1. **禁止**再跑 `pymol_dock_viz_standard.py` 重建该任务（会覆盖 `.pse`）。  
2. **只允许**截图导出 `图片/detail-N.png`；**禁止** `cmd.save` / 改 `.pse`。  
3. **四步：**  
   1. `PyMOLWin.exe "detail-N.pse" -r pymol_detail_export_hook.py` 直接打开（禁止嵌套 `finish_launching`；禁止 PyMOL 内 `run hook,main`）  
   2. 钩子内 **先最大化**，再调用 PyMOL Qt API 收起底部代码区：`toggle_command_log(False)`、`toggle_lineedit()`、`dockWidget.hide()`（主路径，禁止依赖图像识别 `>_` 猜点）  
   3. 等待布局稳定后截客户区 → 裁顶栏/右栏 → cover 成 1:1 → 写 `图片/detail-N.png`（可另存 `detail-N_debug_window.png` 供验收）  
   4. 校验 `.pse` mtime/size 未变  
4. 禁止 `cmd.png` 超大离屏重渲；日常禁止乱 `SW_RESTORE`（仅副屏纠偏时允许一次 restore 再最大化）。  
5. Agent 只处理用户**点名**的序号；禁止无确认全量重跑 / `collect --force-wipe`。

```bat
python …\export_detail_png_from_pse.py --root "…\痤疮_分子对接_序号文件夹"
REM 每数字任务目录只开一次 PyMOLWin；显式 --root 时只处理该路径
```

批量（努力学习 Top10 + 痤疮）：[`run_nuli_ting_detail_combine.py`](../脚本_scripts/run_nuli_ting_detail_combine.py)。

### 7.4 result 拼图（big + detail → result_N.png）

实现参考：`E:\PythonProject\分子对接\2.分子对接结果图组合.py`（背景模板 `背景图.png` 同目录）。

原则（强制）：

1. 左侧：big 图按配体/关键节点聚焦，尽量放大落入实线小框；裁剪越界与右侧虚线框重叠区。  
2. 右侧：detail 图按**关键内容包围盒**裁成 1:1 再缩放填满虚线大框——只圈橙色残基、配体、氢键、标签，**排除蛋白丝带主色**；边距宜小（约 0.08），使 detail **尽可能放大**。  
3. 叠加模板黑框/连线；输出 **11520×6480**，dpi=600。  
4. 输出路径：任务 `图片/result_N.png`（与金标痤疮一致）。

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
- [ ] 单任务同 `…/10`：config/output/log/pdbqt + 三视图 `.pse` + `图片/` 四类 PNG（含 `result_N.png`）  
- [ ] 无 `_png_tmp/`；PNG 不在任务根  
- [ ] 亲和力为负（或已注明并修正）  
- [ ] 热图黑标签；DPI≥600  
- [ ] big：ST=cartoon，CJ=仅 QJ 残基  
- [ ] 手调 detail 仅用截图导出；`.pse` 未改；result 中 detail 已按关键内容尽量放大  
