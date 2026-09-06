# 分子动力学模拟 — 出图与交付约束（SSOT）

> **状态：** `FROZEN`（2026-09-03 用户确认冻结）  
> **解冻条件：** 用户明确说「解冻 / unfreeze」前，**禁止**改下列已验证范式（样例图、Origin recipe、报告版式、目录布局、解读口径）。  
> **代码 SSOT：** `脚本_scripts/origin出图_plotMdOrigin.py`；`脚本_scripts/整理样例目录_layoutMdSample.py`  
> **样例：** `01_样例_sample/`（`STATUS=REAL`，`data_provenance=REAL`）  
> **报告金标：** `01_样例_sample/代码文件/结果文件/报告文件/样例报告_SampleReport_v1.html`  
> **报告范式：** [`统一交付规范 样例报告范式`](../../../00_基础_Foundation/统一交付规范_DeliveryStandards/文档_docs/样例报告范式_SampleReportParadigm.md)（MD 为金标实现）  
> **全局登记：** [`已跑通范式登记_FrozenParadigms.md`](../../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/已跑通范式登记_FrozenParadigms.md)

---

## 0. 冻结范围（Agents MUST NOT 未解冻改动）

| 类别 | 冻结内容 |
|------|----------|
| **图册顺序** | `01`–`26` 主题文件夹与图种顺序（见技能说明 §9.7 表）；禁止删图、乱序、用 ggplot 仿画替代 Origin 正式图 |
| **Origin 分析图** | journal muted 柱色（`#5B8FA8/#C17B7B/#8B7BA8/#6B8F71/#D4A574`）；FEL **Viridis**；2D FEL `layer.cmap.lineN=0`（**禁止** `showLines(3)`）；3D FEL 填色曲面 + `hide_fel_contours`；**禁止** `set %C -pfb color()`；一图一 Origin 进程 |
| **PyMOL / LigPlot** | 快照三帧 + 拼图；LigPlot 必须为官方 `ligplot.ps` 化学结构（**禁止**圆点+方框示意网）；LigPlot CPK/紫键/疏水砖红为图种惯例 |
| **样例目录** | `工作文件_MdWork/3HTB/` 阶段夹（`01_输入`…`10_快照`/`99_日志`）；`一图一文件夹` + `{NN}_{中文}_{English}`；GROMACS 引擎原名（`topol.top`、`md.tpr`）不改名 |
| **HTML 报告** | KPI 条 + 分组章节（平衡 → 稳定 → 结合 → FEL → MM-GBSA → 快照/LigPlot）+ 分条解读 + 页首 **0.20 ns / 21 帧** 警示；审计两列表（非 CSV `<pre>`） |
| **解读口径** | 可陈述本窗口 RMSD/Rg/COM/氢键/MM-GBSA 数字；**禁止**写成发表级 ΔG、长期稳定结合、FEL 能垒；必须写未含熵、需 ≥100 ns + 重复轨迹 |

---

## 1. 允许改动（不算解冻）

- 样例**路径迁移**、`NN_` 前缀、脚本指针更新（**不得**改视觉）
- 用户指定 **`NS` 加大**重跑生产轨迹（新数据可出新数字，但出图/报告**范式**仍跟本约束）
- 环境安装、WSL/GROMACS 版本登记、踩坑文档增补
- PlotQA / 审计字段、DeliveryStandards 通用 API 向后兼容增强（**不得**改变 MD 金标 HTML 结构与图样）
- Bug 修复：仅当修复导致图样/报告**偏离**当前金标时为回归修复；修复后须与 `01_样例_sample` 金标一致

---

## 2. 图册清单（冻结序号）

| NN | 主题 | 引擎 |
|----|------|------|
| 01–07 | 骨架 RMSD、三线 RMSD、RMSF、氢键、Rg、SASA、COM | Origin |
| 08–12 | NVT/NPT 温度/压力/密度、生产势能 | Origin（ggplot 仅备 CSV） |
| 13–20 | FEL 2D/3D（RMSD×Rg/COM/SASA、配体×蛋白 RMSD） | Origin |
| 21–24 | MM-GBSA 分解/标注柱/表、残基贡献 | Origin |
| 25 | 轨迹快照始/中/末 + 拼图 | PyMOL |
| 26 | 二维相互作用 | LigPlot+ |

---

## 3. 报告与交付入口

```bash
# 全流程（xvg 就绪后）
Rscript 01_样例_sample/代码文件/01_run_sample.R

# 仅重写 HTML（不重跑模拟 / Origin）
Rscript 01_样例_sample/代码文件/03_写样例报告_writeSampleReport.R
```

生成器：`write_delivery_report()` + `03_写样例报告_writeSampleReport.R`（参数化 KPI/分组/解读 HTML）。

---

## 4. 修订记录

| 日期 | 变更 |
|------|------|
| 2026-09-03 | 用户确认冻结：样例目录双语编号、`工作文件_MdWork` 归档、Origin 24 图 + PyMOL/LigPlot、分组 HTML 报告与分条解读 |
| 2026-08-30 | 3HTB REAL E2E；BLOCKED 解除；`STATUS=REAL` |
