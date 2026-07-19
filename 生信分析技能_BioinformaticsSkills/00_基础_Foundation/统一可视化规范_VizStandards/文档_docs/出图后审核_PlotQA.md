# 出图后审核 / PlotQA（项目级 SSOT）

> **适用范围：** 整个 `生信分析技能_BioinformaticsSkills` 项目（不限网络药理学）。  
> **时机：** **每张图保存完成后**、在宣称 PASS / 交付给用户之前。  
> **脚本：** [`../脚本_scripts/出图后审核_PlotQA.R`](../脚本_scripts/出图后审核_PlotQA.R)  
> **与 DeliveryStandards：** `delivery_save_plot()` 在可行时自动调用轻量启发式审核；网络布局等有坐标的图应在布局完成后额外调用 `viz_qa_network_nodes()`。

---

## 1. 何时必须做

| 触发点 | 要求 |
|--------|------|
| `save_plot_pub()` / `delivery_save_plot()` 写出 PNG+SVG 后 | 必做（自动启发式 + Agent 目视） |
| 网络布局得到节点 `x,y,r` 与标签后 | 必做几何审核（`viz_qa_network_nodes`） |
| 用户要求「交付 / PASS / 可交图」 | 审核未完成不得宣称 PASS |

**不做的借口（禁止）：** 「图太多」「密网必然糊」「先交付再改」。密网允许 **WARN** 并记录残差，但不得跳过审核步骤。

---

## 2. 审核清单（中文）

### A. 色块 / 节点填充互挡

- [ ] 相邻填充（圆/方/柱条）是否大面积重叠，导致底层色块不可辨？
- [ ] 网络图：节点圆/方的数据坐标半径是否与布局防重叠假设一致？
- [ ] 热图色块本身允许相邻；检查的是**叠加图层**（如标签框、额外 geom）是否盖住关键色块。

### B. 标签互挡

- [ ] 基因名 / 通路名 / 轴刻度 / 图例文字是否两两重叠难读？
- [ ] 火山 / PCA：`ggrepel` 是否仍有严重叠字？
- [ ] 富集水平柱：长 term 是否互相叠或叠到相邻柱？
- [ ] 网络图：同环/同类型标签是否糊成一团？

### C. 长标签导致版式失衡

- [ ] 最长标签是否把画布横向/纵向「撑歪」（一侧留白过大、面板比例失调）？
- [ ] 标签是否溢出 panel / 被 `clip` 裁切？
- [ ] 富集 / 柱图：是否应折行、截断 Top-N、或改用 ID（如 KEGG `hsa*`）而非全称？
- [ ] 轴刻度过密时是否旋转/缩小导致主体绘图区被挤压？

### D. 交付前通用（与既有 VizStandards 对齐）

- [ ] 同名 PNG + SVG；DPI ≥ 600  
- [ ] 图面 English only  
- [ ] 文件名中英对照（DeliveryStandards）  

---

## 3. Pass / Warn / Fail 标准

| 等级 | 含义 | 可否交付 |
|------|------|----------|
| **PASS** | 自动化三项均无 WARN/FAIL；目视无明显遮挡与比例失衡 | 可交付 |
| **WARN** | 存在可察觉拥挤/少量重叠/长标签风险，但不致无法读图；密网常见 | 可交付，须在 STATUS/报告注明残差 |
| **FAIL** | 灾难性填充互挡、大面积标签不可读、或长标签严重扭曲版式 | **不可**宣称 PASS；须改布局/截断/折行/加宽画布后重跑 |

### 自动化阈值（脚本默认，可调）

| 检查 | WARN | FAIL |
|------|------|------|
| 填充圆/AABB 重叠对数占比 | > 2% 且 ≥1 对 | > 25% 或单对重叠深度极大（中心距 < 0.5×(r1+r2) 占比 > 10%） |
| 标签近似框重叠占比 | > 5% | > 40% |
| 标签长度 | max > 40 或 >25% 标签长度 > 28 | max > 80（严重版式风险） |

密网（节点数 ≥ 80 且标签全开）允许将「标签重叠」上限放宽为 WARN（脚本 `dense_network = TRUE`），但仍记录统计。

---

## 4. 图种要点

| 图种 | 几何审核 | 标签/长名 | 目视重点 |
|------|----------|-----------|----------|
| 火山图 | 点重叠可接受 | ggrepel；Top 标签过长则缩写 | 标签是否盖住阈值线/关键点 |
| 热图 | 色块相邻 OK | 行/列名过长 → 缩小字号或截断 | 树状图与标签是否挤出画布 |
| 富集 bar/dot | 柱/点间距 | term 折行或 Top-N；禁止默认棒棒糖 | y 轴长名是否挤压绘图区 |
| GSEA 经典曲线 | ES/barcode/metric 三层比例 | 子图标题勿叠曲线峰 | barcode 是否过密糊成一片 |
| Feature UMAP | 点过密可降 size | 连续色图例完整 | 低分点是否被高分点完全覆盖（宜按 score 排序绘制） |
| 堆叠比例图 | 柱宽一致 | 图例细胞类型名过长则缩写 | facet 风险组是否对齐 |
| 箱线+括号 | 括号勿出界 | p 标签勿叠箱体 | 括号层叠间距 |
| 配对箱线 | 连线可交叉 | p 注释放顶部 | 灰线是否盖住箱体中位 |
| 趋势 smooth+CI | CI 带透明 | 轴标题清晰 | 分组色与 Fig1 一致 |
| 样本树状图 | 枝干可交叉于叶 | 叶标签旋转 45° | 分组色点是否对齐叶序 |
| 网络（HCTP/PPI） | **必做** `x,y,r` AABB/圆重叠 | 通路用 ID；类型/环内字号恒定 | 填充互挡优先于标签残差 |
| 生存 KM | 曲线可交叉 | 图例/risk table 勿叠曲线末端 | 风险表与主图比例；须有 log-rank p |
| UMAP | 点密度高可接受 | 簇标签 ggrepel | 标签是否盖住小簇 |
| 箱线/PCA/韦恩 | 点/椭圆框 | 组别名过长 | 图例与面板边距 |

网络专属细则仍见各技能（如 NetPharm `文档_docs/出图约束_NetworkFigureStandards.md`）；**遮挡审核本身以本文为 SSOT**，技能内只链接、不复制阈值表。

---

## 5. Agent 工作流（强制）

```text
1. 出图并 save（delivery_save_plot / save_plot_pub）
2. 若有节点坐标 → viz_qa_network_nodes(...)；否则依赖 delivery 钩子 / viz_qa_ggplot_heuristic
3. 阅读 viz_qa_report 的 PASS/WARN/FAIL
4. Read 保存的 PNG（目视残差：自动化漏检的软重叠、白边失衡、裁切）
5. FAIL → 修布局/标签策略后重跑；WARN → 可交付但写明
6. 全部目标图完成审核后，才可在 STATUS/对话中宣称交付完成
```

依赖保持轻量：**base R + 已使用的 ggplot2**（可选从 `ggplot_build` 抽标签）。

---

## 6. 调用示例

```r
source(".../统一可视化规范_VizStandards/脚本_scripts/出图后审核_PlotQA.R", encoding = "UTF-8")

# 网络：布局后
viz_qa_network_nodes(
  data.frame(x = nd$x, y = nd$y, r = nd$r, label = nd$label),
  plot_id = "HCTP_ellipse",
  dense_network = TRUE
)

# ggplot 启发式（无坐标时）
viz_qa_ggplot_heuristic(p, plot_id = "GO_Bar")

# 结构化汇总
viz_qa_report(list(fill = ..., label = ..., length = ...), plot_id = "PPI")
```

`delivery_save_plot()` 在 PlotQA 已 source（或可自动定位）时，会对 ggplot 对象做启发式审核并 `message` 结果；**不会因 WARN 中断保存**。仅当 `options(bioinfo.plotqa.hard_fail = TRUE)` 且等级为 FAIL 时才 `stop`。
