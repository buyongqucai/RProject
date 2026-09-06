# 网络药理学出图约束（SSOT）

> **状态：** `FROZEN`（2026-07-26 用户确认冻结）  
> **解冻条件：** 用户明确说「解冻 / unfreeze」前，**禁止**改既有视觉 recipe、疾病双口径与主 HTML 报告结构。  
> **增补例外：** 用户于 2026-07-27 明确要求写入规范的 **§J–§L**（网络分析报告 / 空靶点药味 / 生物结构动画）为授权增补，**不改** §A–§H 已冻结图样。  
> **代码 SSOT：** `脚本_scripts/04_交付网络布局_DeliveryNetworkLayouts.R`（在 `03_STRING与网络图_StringNetwork.R` 之后 source，覆盖其 plot helpers）；圈图见 `02_可视化_NetworkPharmPlots.R`；高级附图见 `05_高级附图_AdvancedPanels.R`  
> **样例图：** `01_样例_sample/代码文件/结果文件/图片文件/`  
> **全局出图技术：** `统一可视化规范_VizStandards`（DPI≥600、同名 SVG+PNG、中文字体等；HCTP 光栅可 300）  
> **命名目录：** `统一交付规范_DeliveryStandards`（轨 A：`NN_中文_English`；轨 B：项目内 `交付文件/` 中文树）  
> **出图后审核：** [`出图后审核_PlotQA.md`](../../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)  
> **范式登记：** [`已跑通范式登记_FrozenParadigms.md`](../../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/已跑通范式登记_FrozenParadigms.md)

---

## 0. 流程与边界

1. **PPI 与 HCTP 多层网络均由代码/AI 绘制，为交付默认**；Cytoscape 精修可选、**非必做**。
2. **禁止编造** STRING 边、分组或疾病/药物基因列表。
3. 既有 NetPharm **柱状图 / 韦恩 / GO / KEGG 柱棒气泡 / HCTP / PPI / 高级附图 / HTML 报告结构**：**未经解冻不得改样式与口径**。
   - 例外（仍须符合本节）：`CompoundDiseaseOverlap` 柱区等宽对齐；韦恩交付=微生信模板；韦恩 PNG 须裁空白。
4. STRING **API** 取边 + Degree 同心/渐变 R 图 = 正式交付路径；官网 3D 图仅陪跑。
5. 保存后跑 PlotQA；**标签互挡 FAIL 须修**（密网填充 WARN 可接受）。
6. 客户归档写出项目内 `交付文件/`；**禁止**把桌面路径当默认写出目录。
7. **分享交付：** 打包整个 `交付文件/` 文件夹；入口 HTML 为根目录 `图注与解读说明.html`（相对路径含图），**禁止**只发单个 HTML。

---

## 0a. 疾病基因双口径（强制 · 严谨性）

| 口径 | 文件（轨 B / 数据文件） | GeneCards | 用途 |
|------|------------------------|-----------|------|
| **韦恩全量** | `疾病靶点按库.csv`（← VennFull） | **全量导出**（可数千） | 仅多库韦恩图展示覆盖广度 |
| **下游过滤** | `疾病靶点按库_下游.csv` + `疾病靶点合并.csv` | **Relevance Score ≥ 40** ∪ TTD ∪ DrugBank ∪ OMIM ∪ CTD | 药病交集、网络、富集、PPI、桑基 |

**药病交集** = 药物靶点并集 ∩ **下游疾病并集**（不是 GeneCards 全量自交）。  
写作/HTML 必须同时写清两套数字，避免「全量 7000+ vs 交集几百」被误解为数据错误。

---

## 0b. 双轨命名与轨 B 目录（强制）

| 轨 | 用途 | 规则 |
|----|------|------|
| A | 管线/样例结果 | `{NN}_{中文图类}_{主题}_{EnType}.{png,svg}`，见 DeliveryStandards |
| B | 客户交付包 | 见下表完整树 |

**轨 B 目录树（冻结）：**

```text
交付文件/
  图注与解读说明.html          ← 分享入口（相对路径：图片/…、数据/…、报告/…）
  README_轨B说明.txt
  图片/
    韦恩图/
    富集分析/
    网络图/                     ← 含可选子目录见 §J（网络分析报告在数据侧）
    PPI/
    补充_技能扩展/
    KEGG官方通路图/            ← Top20 REST /get/{id}/image + 00_清单.csv
    动画_生物结构/             ← §L：人体生物结构 GIF + 动画图册.html + _bases/
  数据/
    疾病/   药物/（含单药/）  网络图/  富集分析/  PPI/
  报告/
    图注与解读说明.md
    _stats.json
    图注与解读说明.html        ← 跳转 stub → ../图注与解读说明.html
```

**轨 A → 轨 B 映射（打包脚本唯一真源；写 SVG，可选同名 PNG）：**

| 轨 A stem | 轨 B 相对路径 |
|-----------|---------------|
| `01_韦恩图_DiseaseDatabases_Venn` | `图片/韦恩图/疾病数据库可视化韦恩图` |
| `02_韦恩图_DrugDisease_Venn` | `图片/韦恩图/疾病药物交集韦恩图` |
| `03`/`04`/`05` 成分柱系列 | `图片/补充_技能扩展/` 下中文短名 |
| `06_气泡图_GO_BPCCMF_Bubble` | `图片/富集分析/BPCCMF气泡图` |
| `07_柱状图_GO_BPCCMF_Bar` | `图片/补充_技能扩展/GO_BPCCMF柱状图` |
| `08_棒棒糖图_KEGG_Pathways_Lollipop` | `图片/富集分析/KEGG棒棒糖图` |
| `09_柱状图_KEGG_Pathways_Bar` | `图片/富集分析/KEGG柱状图` |
| `10_圈图_KEGG_Circos` | `图片/富集分析/KEGG圈图` |
| `10_圈图_KEGG_CircosLabeled`（若导出） | `图片/富集分析/KEGG圈图基因名` |
| `11_网络图_HerbCompoundTargetPathway_Network` | `图片/网络图/药物有效成分疾病靶点通路网络图` |
| `12_网络图_HerbCompoundTargetPathway_Ellipse_Network` | `图片/网络图/药物有效成分疾病靶点通路网络图_椭圆布局` |
| `13_网络图_StringPPI_Network` | `图片/PPI/string_vector_graphic` |
| `14_网络图_StringPPI_Concentric_Network` | `图片/PPI/PPI渐变图` |
| `15_网络图_StringPPI_Degree_Network` | `图片/PPI/PPI渐变图_Degree` |
| `16_交集图_HerbCompound_UpSet` | `图片/补充_技能扩展/药味成分交集UpSet图` |
| `17_桑基图_HerbCompoundTargetPathway_Sankey` | `图片/网络图/药成分靶点通路桑基图` |
| `18_桑基图_PerCompound_Filtered_Sankey` | `图片/网络图/筛选成分桑基图` |
| `19_热图_HerbPathwayCoverage_Heatmap` | `图片/补充_技能扩展/药味通路覆盖热图` |

规则：轨 B 可纯中文；轨 A 必须中英编号名；打包只复制不改像素；**禁止**桌面路径作默认写出。

---

## A. 多层 HCTP（Herb–Compound–Target–Pathway）

### 数据

| 层 | 含义 | type.csv |
|----|------|----------|
| A | 药（Herb） | A |
| B | 成分（Compound） | B |
| C | 靶点（Target） | C |
| D | KEGG 通路（Pathway，`hsa…` 作节点 key；网络边常用 Top20） | D |

边来自 `network.csv`：`A–B`、`B–C`、`C–D`（勿另造边）。

### A1. 颜色 / 形状 / 连线（对照参考图）

| 维度 | 规范取值 |
|------|----------|
| 靶点 C | 圆角方；填充 **`#F0B2AE`**；基因名标在块内 |
| 药 A | 平顶八边形；pastel 色板 `.np_herb_palette`（`#CBD5E8 #80B1D3 #FB8072 #E6AB02 #FDB462 #BEBADA #8DD3C7 #FCCDE5 #B3DE69 #BC80BD …`） |
| 成分 B | 圆；与所属药同色 |
| 通路 D | columns 六边形 / ellipse 扁椭圆；绿渐变 `#C7E9C0→#41AB5D→#006D2C` |
| `same*` | 与**宿主药**同色（见 A3）；不单独刷灰 |
| A–B / B–C 边 | **`#7A8A94` 实线**；α≈0.22–0.32；线宽≈0.28–0.36 |
| C–D 边 | **`#3B7DD8` 实线**；α≈0.28；线宽≈0.40（禁止再淡到不可辨） |
| 描边 | `colour = "transparent"`（禁止 `NA`） |
| Degree→大小 | **60–120** → `r = size / size_to_r`；默认 `size_to_r≈260`（夹紧 **180–300**） |
| 字号 | Target22 / Herb30 / Compound28 / Pathway30（pt）；`canvas_scale=0.16`；`lab_scale∈[0.16,0.24]`；靶点拟合 `min_size≈0.85` |
| 色块 vs 字 | **色块大于字**；缩略图先认色再认字 |

**失败信号：** 中心被蓝边洗白、药簇只见黑字不见色盘、连线淡到不可辨、`same*` 单独灰色难认归属。

### A2. 间距算法（强制计算逻辑）

各部分间距 = `max(设计距, 标签下限, 填色下限)`；标签下限用该部分**最长的两个标签**半宽/半高之和（`.np_top2_label_min_gap`）。**间距 ≥ 该下限即可，禁止无意义再放大。**

| 部分 | 设计距 | 标签下限 | 填色/几何下限 |
|------|--------|----------|----------------|
| 靶点网格 C | fill-pitch × **0.5**（相对旧 fill 距收紧 50%） | top2 基因名 → `pitch_x`/`pitch_y` | `≥ 2.05 × r_t` |
| 成分卫星 B | columns×1.05 / ellipse×1.12；径向 clearance 从简 | top2 成分 ID | **圆心距 > 4 × r**（色块尺度 = 半宽 `r`）；环间距同用 `≥4r` |
| 通路列 D（columns） | `2 × r_p × pathway_v_gap_factor`（≈1.65） | top2 `hsa…` 半高之和 | `≥ 2.05 × r_p` |
| 层间（靶↔通路↔药） | `section_pad_*` 偏紧；ellipse `gap_cm_min=0.32` | — | 填色不相切 |

成分轨道实现要点（`np_plot_hctp_network`）：

```text
min_chord = max(4 × r_b, top2_label_gap, 2.05 × r_b)
cr = min_chord / (2 × sin(π / n_on_ring))   # 邻点圆心距 = min_chord
ring_gap ≥ 4 × r_b
密药（≥14 / ≥28）优先 2–3 环，禁止为「更紧凑」退回单环糊成黑圈
```

### A3. 成分命名与 `same*`（强制）

1. 仅 1 味药：`{药码}{n}`（如 `BX1`）。
2. ≥2 味药同名化学成分 → 唯一 ID **`same1…sameN`**（契约层）；`草药成分边` 每味相关药各挂一条到同一 `sameN`；图上节点只画一次。
3. **空间宿主：** `host = argmin_{h∈sharers}(已分配成分数)`（先挂独有，再挂 shared）；`same*` 画在宿主卫星圈内。
4. **颜色：** 与宿主药同色（`herb_owner`）；A–B 边仍连到所有共享药。

### A4. 布局模式

| 模式 | 结构 |
|------|------|
| columns（Fig 11） | 靶中心网格；药+成分环绕；通路最外左右列 |
| ellipse（Fig 12） | 靶中心；通路中环扁椭圆；药+成分最外卫星；通路↔成分 **≥0.32 cm** |

画布交付默认约 **20×18 in**；HCTP 光栅 DPI 可 300（矢量 SVG 仍交）；其它图类遵循全局 DPI≥600。

### A5. 审查 checklist

| 类 | 通过 | 失败 |
|----|------|------|
| 色块 | A/B/D 可见；粉靶为中心主色之一；Degree 单调 | 蓝雾/黑字盖盘 |
| 标签 | PlotQA `label_overlap` PASS、deep=0；靶点字在块内 | 糊圈、空白方块、`check_overlap` 丢字 |
| `same*` | 宿主卫星 + 宿主色；映射表可核对 | 灰块独立环 / 挂到成分最多的药 |
| 成分距 | 邻心距 ≥ 4r（或被 top2 标签抬升） | 无故远大于 4r 的空环 |
| 层间 | 有缝但不空旷；ellipse ≥0.32 cm | 填色相交或大片留白 |

---

## B. STRING PPI 同心渐变

1. STRING score **≥0.9**；剔除 isolates。
2. 构图前按 Degree 取 **Top n≤200**；诱导子图；14/15 共用同一筛选集。
3. Degree → 颜色与大小（60–120）；不缩 hub；4–5 环；外环约 50–55%。
4. **禁止标签互挡**（靠加环半径/画布解决；**最外圈每个节点都标注**，禁止因 Degree 低而留空）；环半径不足则外扩。
5. 副标题含：`topDegree≤200 · n=… · e=…`。

---

## C. KEGG 圈图

代码：`np_draw_kegg_chord` / `np_save_kegg_chord`

1. 基因/通路扇区总量约 **1:1**。
2. 上下分裂缝 **视觉连续**（`gap_split≈1.5`）；禁止两瓣月牙。
3. 通路标签 = **全称**；禁止 `…` 截断；允许折行。
4. 图例与环上一致（全称）；画布右侧留白。
5. 标签互不遮挡；可双文件：`KEGG圈图` / `KEGG圈图基因名`。
6. 默认约 **13×11 in**，DPI≥600，同名 PNG+SVG。

---

## D. 代码与样例路径

| 项 | 路径 |
|----|------|
| 布局 SSOT | `脚本_scripts/04_交付网络布局_DeliveryNetworkLayouts.R` |
| 圈图 / 柱棒气泡 | `脚本_scripts/02_可视化_NetworkPharmPlots.R` |
| STRING 拉取 | `脚本_scripts/03_STRING与网络图_StringNetwork.R` |
| 高级附图 | `脚本_scripts/05_高级附图_AdvancedPanels.R` |

入口：`np_plot_hctp_network()`、`np_plot_string_ppi(max_nodes=200)`、`np_save_kegg_chord()`、`np_plot_herb_upset()`、`np_plot_hctp_sankey()`、`np_plot_hctp_sankey_by_compound()`、`np_plot_herb_pathway_heatmap()`。

---

## E. 高级附图（冻结）

技能：`脚本_scripts/05_高级附图_AdvancedPanels.R`  
项目入口示例：`努力学习项目/网络药理学/代码文件/22_plot_advanced_panels.R`、`23_replot_sankey_colored.R`、`25_plot_herb_pathway_heatmap.R`

| 轨 A | 轨 B / 说明 |
|------|-------------|
| **16** `交集图_HerbCompound_UpSet` | `药味成分交集UpSet图`；药味色板；`same*` 常在多药柱 |
| **17** `桑基图_HerbCompoundTargetPathway_Sankey` | `药成分靶点通路桑基图`；筛选总览约 **16 成分 / 16 靶 / 12 通路**；淡色流带 + 分列着色 |
| **18** `桑基图_PerCompound_Filtered_Sankey` | `筛选成分桑基图`；前 16 成分 **4×4 分面**（药→靶→通路） |
| **19** `热图_HerbPathwayCoverage_Heatmap` | `药味通路覆盖热图`；Top20 通路；格子=交集靶点数 |

~~核心靶点子网~~：用户取消，**不进交付**。

可选后续（未做、不解冻不擅自加）：交互 HTML 网络、无统计依据的装饰 3D。

---

## F. KEGG 官方通路图（冻结）

1. 按富集 **pvalue Top20** 从 KEGG REST 下载：`https://rest.kegg.jp/get/{hsaXXXXX}/image`。
2. 写出：`交付文件/图片/KEGG官方通路图/` + `00_Top20通路图清单.csv`；遵守 [KEGG 条款](https://www.kegg.jp/kegg/legal.html)。
3. 脚本：`代码文件/24_download_kegg_pathway_maps.py`（须重试/超时；先缓存再复制交付）。
4. 官方图 = 知识地图定位 geneID，**不替代**棒棒糖/柱/圈图统计图。

---

## G. 韦恩图交付（冻结）

1. 多库韦恩用 **VennFull**；药病韦恩用 **下游疾病并集 ∩ 药物靶点**。
2. 优先微生信风格模板（`09_build_weishengxin_style_venn.py`）；光栅化后 **必须裁白边**（禁止 Chrome 大画布留巨幅空白）。
3. 裁边脚本：`代码文件/27_trim_venn_whitespace.py`（轨 A + 轨 B 同步）。

---

## H. HTML 交付报告（冻结）

| 项 | 约定 |
|----|------|
| 入口 | `交付文件/图注与解读说明.html`（**交付根目录**） |
| 资源路径 | **仅相对路径**：`图片/...`、`数据/...`、`报告/...`；禁止本机绝对路径 |
| 内容 | 关键统计仪表盘、生物学结论提纲、各图「含义/怎么看/生物学意义」、单药表、Top KEGG 解读、GeneCards 双口径 FAQ、KEGG Top20 画廊 |
| 统计 | `28_collect_report_stats.py` → `报告/_stats.json`；生成 HTML 时自动重算 |
| 生成 | `26_build_html_report.py`；`报告/` 内 stub 跳转到根目录 HTML |
| 分享 | **整夹打包** `交付文件/`；对方打开根目录 HTML 即可看图 |

---

## J. HCTP 网络分析报告（2026-07-27 增补）

> 目标：交付 **Cytoscape Network Analyzer 同构指标表** + **一份离线 HTML**；禁止再拆成多份 Top10 小表/散图。

### J1. 交付物（轨 B）

| 文件 | 说明 |
|------|------|
| `数据/网络图/网络图数据.csv` | 全节点大表；列名对齐 Cytoscape Analyze Network 导出（含 Degree、BetweennessCentrality、ClosenessCentrality、Stress、ClusteringCoefficient、NeighborhoodConnectivity、AverageShortestPathLength、Radiality、Eccentricity、TopologicalCoefficient、IsSingleNode、`name`/`shared name`、`type` 等） |
| `数据/网络图/网络图数据_含显示名.csv` | 同上 + `display_name`（阅读用；**不替代** Cytoscape 对接表） |
| `数据/网络图/网络分析报告.html` | **唯一**网络分析可视化入口：Top10 柱状图（SVG 离线）+ 可筛选排序的完整大表 |
| `数据/网络图/肉桂_无靶点说明.txt`（或等价） | 空靶点药味说明（见 §K）；有空靶点药时必出 |

**禁止：** 再交付 `Top10_*.csv` / `网络分析_Top10/` 散图专辑作为正式交付（已废弃）。

### J2. 计算与脚本

- 输入：`数据/网络图/network.csv` + `type.csv`（及药物侧 `成分重命名.csv`）。
- 项目脚本：`努力学习项目/网络药理学/代码文件/32_export_cytoscape_network_analysis.py`（NetworkX）。
- 图中须含 **孤立节点**（如 type=A 但无边的药味），`IsSingleNode=true`、`Degree=0`。

### J3. HTML 显示名（强制）

| 节点 type | HTML / `display_name` | 网络 `name` 字段 |
|-----------|----------------------|------------------|
| **B 成分** | **原始化合物名**（来自 `数据/药物/成分重命名.csv` 的 `compound_id→compound_name`） | 仍用代号（`BX1` / `same8`…）以便对接 Cytoscape / network.csv |
| **A 药物** | 中文药名（`herb_zh`） | 药码（`BX`/`RG`…） |
| **C / D** | 与 `name` 相同（基因 symbol / `hsa…`） | 不变 |

柱状图优先显示原名；悬停可带 `(代号)`。大表须同时有 `name` 与 `display_name`，搜索两者均可。

### J4. 图表配色

- **每张 Top10 图使用不同色系**（全网 Degree / Betweenness / Closeness / Stress；以及 A/B/C/D × Degree、Betweenness）。
- 同图内柱按排名渐变，避免整页同色。
- 使用内嵌 **SVG**，分享时**不依赖**外网 CDN。

---

## K. 空靶点药味 / 数据缺口（2026-07-27 增补）

> 典型案例：方剂中 **肉桂（RG）靶点数 = 0**。写作须标明 **数据缺口**，禁止写成「该药无药理作用」。

### K1. 判定与标注

1. 单药靶点表 / 药病交集行为空 → 在 HTML、图注、STATUS/说明文件中写 **`BLOCKED_EXTERNAL` 或「上游靶点缺失」**。
2. HCTP：`type.csv` **可保留**该药 A 节点；`network.csv` 无其边 → 网络分析中 `Degree=0`、`IsSingleNode=true`。
3. 桑基 / 流量图中该药通常不可见 — 图注须一句说明原因。

### K2. 常见根因（须排查，禁止静默填假靶点）

| 现象 | 处理 |
|------|------|
| TCMSP 有效成分表仅表头 / 空 | 核对拉丁名、OB≥30% & DL≥0.18；或改走 HERB/TCMBank→STP（见成分靶点 SOP） |
| `*{药}靶点基因.xlsx` 仅 UniProt 蛋白名两列、无「成分–蛋白–基因」映射列 | **不得**把 UniProt 全表当该药靶点；按 SOP 补成分靶点 |
| 解析器按「白术式」读第 5 列基因而列数 &lt; 5 | 得到 0 靶点属预期；先修上游文件再重跑 |

**禁止：** 为凑图编造成分–靶点边或从无关 UniProt 全表灌入下游韦恩/STRING。

细节对齐：[`成分靶点获取与交付规范_CompoundTargetSOP.md`](成分靶点获取与交付规范_CompoundTargetSOP.md) §3 / §7。

---

## L. 人体生物结构动画（2026-07-27 增补）

> 用途：UC / 网药语境下的 **解剖叙事示意**（受体–信号–入核），**不是** KEGG 官方拓扑复刻，也不替代富集统计图。

### L1. 交付位置

`交付文件/图片/动画_生物结构/`：

- `01`–`05_*.gif`（或按通路扩展编号）
- `_bases/*.png`（插画底图，须随交付自包含）
- `动画图册.html`、`README.txt`

### L2. 制作流水线（强制）

1. **静帧底图**：医学动画 / 组织学精细插画（GenerateImage 或同等）；须有刷状缘、膜、细胞器、核孔等生物结构特征。  
2. **动画层**：Pillow 叠信号流动 / 呼吸高光 / 中文顶栏；**禁止**仅用圆与圆角矩形 cascade 冒充生物结构。  
3. 右上角说明用 **半透明短词芯片**，禁止大块不透明白底「结构要点」卡遮挡主画面。

技能副本（中文命名）：`E:\绘图\人体生物结构动画\`（Cursor 入口可指向该目录）。  
项目合成脚本示例：`努力学习项目/网络药理学/代码文件/31_compose_vivid_bio_gifs.py`。

---

## 修订记录

| 日期 | 变更 |
|------|------|
| 2026-07-19 | 柱/韦恩/GO/KEGG 柱棒气泡等首轮冻结 |
| 2026-07-26 | HCTP/PPI/圈图修订 + 高级附图 16–19 + KEGG Top20 + HTML 报告 + 疾病双口径 + 轨 B 目录 → **用户确认 FROZEN** |
| 2026-07-27 | 用户授权增补 **§J** 网络分析大表+HTML（成分显示原名、配色差异、禁散 Top10 表）、**§K** 空靶点药味、**§L** 生物结构动画与轨 B 目录项；**未解冻** §A–§H 视觉 recipe |
