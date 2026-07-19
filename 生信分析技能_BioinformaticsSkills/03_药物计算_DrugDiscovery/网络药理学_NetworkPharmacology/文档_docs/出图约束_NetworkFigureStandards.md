# 网络药理学出图约束（最终约定 SSOT）

> **状态：** 最终约定（Final agreed）  
> **代码 SSOT：** `脚本_scripts/04_交付网络布局_DeliveryNetworkLayouts.R`（在 `03_STRING与网络图_StringNetwork.R` 之后 source，覆盖其 plot helpers）  
> **样例图：** `01_样例_sample/代码文件/结果文件/图片文件/`  
> （2026-07 目录迁移：结果嵌套在 `代码文件/` 下；视觉 recipe 仍 frozen，未改布局/配色） 
> **全局出图技术：** 仍遵循 `统一可视化规范_VizStandards`（DPI≥600、同名 SVG+PNG、中文字体等）；本节只定**网药网络图**专属约束。  
> **出图后审核（项目级 SSOT，勿在此重复阈值）：** [`统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md`](../../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md) — 每张图保存后检查色块/标签互挡与长标签版式；`04_*.R` 在 HCTP/PPI 布局后调用 `viz_qa_network_nodes`（密网 WARN 可接受）。

---

## 0. 流程与边界

1. **PPI 与 HCTP 多层网络均由代码/AI 绘制，为交付默认**；Cytoscape 精修可选、**非必做**（2026-07 用户确认：无需软件手绘）。
2. **禁止编造** STRING 边、分组或疾病/药物基因列表。
3. 既有 NetPharm **柱状图 / 韦恩 / GO / KEGG** 等非网络图：**未经用户要求不得改样式**（FROZEN）。
4. STRING **API** 取边 + Degree 同心/渐变 R 图 = 正式交付路径；官网 3D 图仅陪跑。
5. 出图完成后执行**项目级 PlotQA**（见上链）；本文件不另建 NetPharm-only 遮挡阈值表。
6. 库自动/手工分工见 [`数据库可达性与自动获取_DBAutomation.md`](数据库可达性与自动获取_DBAutomation.md)。

---

## A. 多层 HCTP（Herb–Compound–Target–Pathway）

### 数据

| 层 | 含义 | type.csv |
|----|------|----------|
| A | 药（Herb） | A |
| B | 成分（Compound） | B |
| C | 靶点（Target） | C |
| D | KEGG 通路（Pathway，`hsa…`） | D |

边来自交付 `network.csv`：`A–B`、`B–C`、`C–D`（勿另造边）。

### 节点大小

- Degree → 统一视觉尺寸域 **60–120**；数据坐标半径 `r = size / size_to_r`（默认 `size_to_r=560`）。
- **同类型内**不得为避让单独缩小高 Degree 节点；不够空间就**加大间距 / 画布**。

### 描边与边

- 节点描边：`colour = "transparent"`（**禁止 `NA`**，否则 ggplot 可能回退默认边框）。
- 边：**实线**（非虚线）。
- **C–D（靶点–通路）边 = 蓝色**（`#2F6FBF`）；A–B / B–C = 低饱和灰（`#8FA0A8`）。

### 靶点（C）

- 形状：圆角正方形；圆角半径 = **边长的 10%**（`corner_frac = 0.10`，`r_corner = 0.10 * side`）。
- 填充：浅粉（`#F5C6CB`）。
- **每个靶点都标注基因名**。

### 通路（D）

- 标签：**仅通路 ID**（如 `hsa04210`），单行写在填充上；禁止全称、禁止折行。
- **columns 模式：** 通路列在最外侧（左/右），包围药+靶区域。
- **ellipse 模式：** 通路在靶点与成分之间的**中间环**；通路节点为**略扁椭圆**（代码：`a_frac=1.15`, `b_frac=0.85`）。
- ellipse 模式通路填充 ↔ 成分/药填充最小间隙：**≥ 0.5 cm**（按交付画布 data↔cm 换算后断言/外扩）。

### 药（A）与成分（B）

- 药：平顶八边形（`angle = 0`）；Morandi 低饱和、色相拉开（彼此不过近）。
- 成分：圆形，与所属药同色；成分多时（如丹参 DS）允许**多环**排布。
- **columns 模式：** 成分–成分间距相对基线 **×1.30**（`compound_spacing_factor = 1.30`）。

### 字体（类型内恒定）

| 类型 | Cytoscape pt |
|------|----------------|
| Target | 24 |
| Herb | 36 |
| Compound | 38 |
| Pathway | 38 |

ggplot 换算：`size_mm = (pt / ggplot2::.pt) * canvas_scale`（默认 `canvas_scale = 0.26`）。  
**类型之间**可不同；**同一类型内必须相同**（禁止按节点 Degree/拥挤度单独改字号）。  
无填充–填充遮挡；标签放不下时优先**加宽间距**，禁止缩字号凑合。

### 区间距

- **区段之间**（靶区 / 通路环 / 药–成分卫星）间隙相对收紧；
- **区段内部**（靶点网格、同药成分环）更透气。

### 实现状态（与 `04_*.R` 对齐，2026-07）

已落地：Degree 60–120、transparent 描边、C–D 蓝边、圆角 10%、通路 ID、columns×1.30 成分间距、ellipse 扁椭圆 + ≥0.5 cm 通路–成分间隙、类型恒定字号、Morandi 药色、多环成分。

---

## B. STRING PPI 同心渐变

1. STRING score **> 0.9**（实现侧常用 ≥900 / ≥0.9）；**剔除 isolates**。
2. Degree → **颜色与大小**同时映射；尺寸严格单调落在 **60–120**。
3. **禁止**为布局缩小高 Degree hub；环半径不够就**外扩圆环**。
4. 最高 Degree 居中；外环更密（约 **50–55%** 节点在最外环）；**4–5 环**（大图偏 5）。
5. **同一环内字号恒定**；内环字号略大于外环（温和层级）。
6. 环内按 Degree 排序放置。
7. 无填充/标签遮挡；环半径由 chord + 环间 clearance 驱动。

---

## C. 代码与样例路径

| 项 | 路径 |
|----|------|
| 布局 SSOT | `脚本_scripts/04_交付网络布局_DeliveryNetworkLayouts.R` |
| STRING 拉取/缓存 | `脚本_scripts/03_STRING与网络图_StringNetwork.R` |
| 仅刷新网络预览 | `01_样例_sample/代码文件/02_run_network_preview.R` |
| 样例输出 | `01_样例_sample/代码文件/结果文件/图片文件/11_网络图_HerbCompoundTargetPathway_Network.*`、`14_网络图_StringPPI_Concentric_Network.*` |

入口函数（约定名）：`np_plot_hctp_network()`、`np_plot_string_ppi()`（定义/覆盖以 `04_*` 为准）。
