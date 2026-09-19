# 交付命名与图册门禁（SSOT）

> 从 `技能说明_统一交付规范` 披露；改规则只改本文件。  
> 目录树细则仍见 [`样例目录与命名_SampleLayoutNaming.md`](样例目录与命名_SampleLayoutNaming.md)。

## 1. 文件名双语 ≠ 图面英文

| 层级 | 规则 | 示例 |
|------|------|------|
| **交付文件名** | **强制**中英对照 `{中文语义}_{EnglishPascal}.{ext}` | `热图_ContactMatrixStub_Heatmap.png` |
| **图内文字**（title/axis/legend/strip） | **English only** | `Contact matrix (schematic · BLOCKED)` |

禁止把文件名对照逻辑搬进图面（中英并排标题）。HTML 报告正文可用中文；**仅图面强制英文**。

## 2. 结果文件命名

```
[{NN}_]{中文语义}_{EnglishCamelOrPascal}.{ext}
```

| 类型 | 模式 | 示例 |
|------|------|------|
| 图片 | `{NN}_{中文图类}_{对比或主题}_{EnType}.{png\|svg}` | `01_火山图_TreatVsControl_Volcano.png` |
| 数据表 | `{NN}_{中文表义}_{对象}_{EnType}.csv` | `02_差异结果_TreatVsControl_Deg.csv` |
| 审计表 | `审计前检_AuditPre.csv` / `审计后检_AuditPost.csv` | |
| 契约桩 | `契约阻塞桩_ContractBlockedStub.csv` | |
| 报告 | `样例报告_SampleReport_v1.html` | |

禁止：纯英文无中文前缀的 `sample_*.csv`、`plot.png`、`fig1.png`、无语义 `out.csv`。

## 3. PlotQA 钩子

`delivery_save_plot()` 保存后自动调用 VizStandards PlotQA；默认 WARN 不中断。  
关闭：`options(bioinfo.plotqa.after_save = FALSE)`；FAIL 中断：`options(bioinfo.plotqa.hard_fail = TRUE)`。

## 4. 图册责任表门禁

每个领域技能说明须含「交付图册 × 实现状态」：

| 状态 | 含义 |
|------|------|
| **R可复现** | 样例脚本必须真正产出（SVG+PNG） |
| **外部软件必做** | 写清软件/版本/步骤；STATUS=`BLOCKED_EXTERNAL` 或 `PARTIAL` |
| **不做** | 明确范围外 |

禁止用无关简图顶替 Cytoscape/AutoDock 等必做图；禁止把 PARTIAL 写成全流程 PASS。

## 5. STATUS

| STATUS | 何时 |
|--------|------|
| `PASS` | 声明的 R 可复现图册与契约全部完成 |
| `PARTIAL` | R 子集完成 + 外部图诚实断点 |
| `BLOCKED` / `BLOCKED_EXTERNAL` | 关键 CLI/GUI 不可用 |
