# 样例报告范式 / Sample Report Paradigm

**SSOT：** `统一交付规范_DeliveryStandards`  
**生成器：** [`脚本_scripts/规范_报告生成_ReportBuild.R`](../脚本_scripts/规范_报告生成_ReportBuild.R) 的 `write_delivery_report()`  
**金标（完整解读 + 分组图 · FROZEN）：**  
`03_药物计算_DrugDiscovery/分子动力学模拟_MolecularDynamics/01_样例_sample/代码文件/结果文件/报告文件/样例报告_SampleReport_v1.html`

只重写 MD 金标、不重跑模拟：

```bash
Rscript 01_样例_sample/代码文件/03_写样例报告_writeSampleReport.R
```

---

## 1. 报告必须有的块

| 块 | 要求 |
|----|------|
| 页眉 | 技能中英名、STATUS / provenance、报告版本 |
| KPI（可选） | 3–8 个可核对数字；禁止编造 |
| 警示 | TOY / BLOCKED / 演示尺度写在页首，不要埋进文末 |
| 方法 | 写明 source 了哪些脚本（VizStandards + DeliveryStandards + 本技能） |
| 数据来源 | REAL 给 accession / PDB；TOY 写「不可外推」 |
| 审计 | 两列表，不要把 CSV 整段丢进 `<pre>` |
| 图表 | **相对路径**；按科学问题分组，不按文件名堆叠 |
| 每张图 | 标题 + 图 + 一句 caption；解读性的话放 note 或文末「结果解读」 |
| 结果解读 | 分条；数字来自本样例表；写清**没证明什么** |
| 页脚 | 生成时间 + DeliveryStandards + VizStandards + 版本 |

图面文字仍走 VizStandards（English only）。HTML **正文可用中文**。

---

## 2. 默认调用（旧样例，不用改）

```r
write_delivery_report(
  skill_en, skill_folder, status,
  data_html, audit_html, sourced_note,
  fig_map, interp, rep_file
)
```

`fig_map` 为命名向量：`显示名 = 相对报告文件的图片路径`。  
`interp` 可以是一段中文；若含 `<p>` / `<ul>` / `<h3>` 则按 HTML 嵌入，不再包一层 `<p>`。

新 CSS 会自动套上（卡片、双栏图、审计转表）。旧位置参数保持兼容。

---

## 3. 金标调用（分组图 + KPI + 解读 HTML）

```r
write_delivery_report(
  skill_en, skill_folder, status,
  data_html, audit_html, sourced_note,
  figures = NULL, interpretation = interp_html, out_path = rep_file,
  kpis = list(
    list(label = "骨架 RMSD", value = "0.075", unit = "nm", hint = "轨迹均值")
  ),
  figure_sections = list(
    list(
      id = "stab", title = "蛋白构象稳定性",
      intro = "……", layout = "grid2",  # grid2 | grid3 | stack
      items = list(
        list(title = "骨架 RMSD", src = "../01_骨架RMSD图/01_骨架RMSD_RmsdBackbone.png",
             caption = "Backbone RMSD vs t = 0.",
             note = "均值 0.075 nm，短窗口内无展开。")
      )
    )
  ),
  methods_html = methods_html,
  caveats_html = caveats_html,
  subtitle = "……",
  lead_html = "……"
)
```

配色对齐 VizStandards journal muted：`#5B8FA8` / `#6B8F71` / `#C17B7B` / `#8B7BA8` / `#D4A574`。不要大阴影、不要渐变英雄区。

---

## 4. 解读口径（强制）

- 数字必须能在同目录 CSV / 审计表对上。
- REAL 演示尺度（如 MD 0.20 ns）**可以**写「本窗口内 RMSD 平台 / 配体未飞出」，**不可以**写成发表级 ΔG、稳定结合或 FEL 能垒。
- TOY 必须出现「不可外推」。
- STATUS（图完成度）与 `data_provenance`（REAL/TOY/BLOCKED）分开写，不要混成一个词。
