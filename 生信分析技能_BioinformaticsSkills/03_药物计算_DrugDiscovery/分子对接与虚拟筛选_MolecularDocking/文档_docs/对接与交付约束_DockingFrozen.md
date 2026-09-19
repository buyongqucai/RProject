# 分子对接 — 对接与交付约束（SSOT · FROZEN）

> **状态：** `FROZEN`（2026-09-05 用户确认冻结；同日增补热图色标仅非正值；**同日修订** PyMOL：禁止减负裁链、完整入画释义、detail 自动选角；**2026-09-06 增补** detail 截图导出 + result 拼图定稿，见 SOP §7.3/§7.4）  
> **解冻条件：** 用户明确说「解冻 / unfreeze」前，**禁止**改下列已验证范式。  
> **进化：** 解冻后把新确认规则写回本文件与 SOP **各一处对应段落**；技能说明只改指针。反馈闭环见 `docs/项目规范_ProjectStandards.md` §0。  
> **技术路线：** [`技术路线_AutoSite_AutoDockGPU.md`](技术路线_AutoSite_AutoDockGPU.md)  
> **流水线：** [`分子对接流水线规范_DockingPipelineSOP.md`](分子对接流水线规范_DockingPipelineSOP.md)  
> **中心登记：** [`中心位点方法登记_CenterSourceRegistry.md`](中心位点方法登记_CenterSourceRegistry.md)  
> **盒子协议：** [`对接盒子定心与定边_DockingBoxProtocol.md`](对接盒子定心与定边_DockingBoxProtocol.md)  
> **批处理脚本：** `脚本_scripts/批量对接_runBatchAdgpu.py`；PyMOL `pymol_dock_viz_standard.py`；detail 重导 `export_detail_png_from_pse.py`  
> **交付金标目录：** 桌面 `痤疮_分子对接_序号文件夹/`；生产例：`努力学习/docking_adgpu/`  
> **全局登记：** [`已跑通范式登记_FrozenParadigms.md`](../../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/已跑通范式登记_FrozenParadigms.md)

---

## 0. 冻结范围（Agents MUST NOT 未解冻改动）

| 类别 | 冻结内容 |
|------|----------|
| **引擎与路线** | 默认 **AutoDock-GPU**（`E:\AutoDock-GPU\`，AD4；`--nrun 20`）；AutoGrid 出 `.maps.fld`；**禁止**把 Vina 当默认主引擎；AD-GPU 与 Vina **分表**（`summary_adgpu.csv` ≠ `summary_vina.csv`） |
| **定心决策树** | 有可用共晶小分子 → `cocrystal_meeko` / `cocrystal`；无共晶 → **AutoSite**；质控 FAIL → P2Rank → Fpocket → 文献/`manual` → `FAIL`。**禁止**整链 COM、全 HETATM 平均、固定边长 22、未校验照抄库表 |
| **中心方法登记** | 每任务强制 `center_source`（受控词表见 CenterSourceRegistry）；落盘 `task_info` + `summary_*`；缺列新批次不合格 |
| **明确不做** | **不做**「共晶配体重对接 + RMSD 自检」作为流水线步骤或验收门槛（用户 2026-09-05 否决） |
| **目录与交付** | 序号任务 `N/`；PNG 仅在 `图片/`（big/surface/detail/**result**）；`.pse` 在任务根；无 `_png_tmp`；项目根 git；ASCII 对接 cwd；**result 拼图效力序见 SOP §7.4**（左右不重叠且左完整 → 右仅白边 trim 等比抵虚线 → 左黑框内尽量抵框） |
| **PyMOL** | ST=**完整受体**（禁止为减负删原子）；PT/CJ/QJ 语义与配色；**完整入画**=相机 zoom/clip；detail 导出前自动选角；字号 24、一位小数；big/surface 用 GUI 同款 **Draw(fast)**：默认 **5040×3653、dpi=600、ray=0**（禁止 Ray）；**detail 定稿 PNG=截图导出**（禁止 `cmd.png`）；手调后 `export_detail_png_from_pse.py`：**最大化** → 始终 `zoom(PT\|CJ, buffer=4)` + 自适应满度 **0.72**（标签余量 1.15）→ 视口中心正方形 **6000²**（细则 SOP §7.3；禁止 cover / 内容检测再裁 / 写回 `.pse`） |
| **热图** | DPI≥600；PNG+SVG；**蛋白/配体刻度名与格内数值黑色 `#000000`**；结合能矩阵来自已对接 summary；**色标仅非正（`vmax=0`）**；**colorbar 两端平头、无 `extend` 箭头**；**禁止**总标题、轴标题（Protein target / Ligand）、色标标题（Affinity…）、底部脚注；格内文字仍写精确 kcal/mol |
| **结构库** | 优先 `D:\数据库\分子对接数据库\`；蛋白表优先精确文件名 `分子对接_蛋白表.csv`（禁止误读 `.bak`） |

---

## 1. 允许改动（不算解冻）

- 新课题蛋白/配体清单、桌面项目名（须仍 ASCII 子目录）
- 环境安装（ADFRsuite/WSL、AutoSite、AutoGrid、Open Babel 路径登记）
- Bug 修复：编码、路径、AD4 加氢、`find_receptor` 命名、GPU `cwd` 输出等——**不得**借修复改路线/图样语义
- `--nrun` 等搜索强度按课题临时加大（默认仍写 20；改默认须解冻）
- PlotQA / Delivery 通用增强（不改变对接金标目录与 PyMOL 语义）
- **配色变量取值**（`protein_color` / `residue_color` / `hbond_color` / `ligand_spectrum`）按课题更换；拼图须用同名变量或 `--auto-colors`，不得写死单一色相

---

## 2. 冻结流程（一句话）

**本地库结构 → AD4 受体准备 → 定心（共晶包盒优先，否则 AutoSite）并登记 `center_source` → AutoGrid → AutoDock-GPU（nrun=20）→ summary_adgpu + 热图 → PyMOL 三视图 → detail 手调断点 →（用户手调后）截图导出 + result 拼图。**

不做共晶 RMSD 重对接验收。

---

## 3. 解冻口令

用户明确说「解冻分子对接」或「unfreeze docking」后，方可改 §0 表内条款；解冻后须更新日期并回写本文件状态。
