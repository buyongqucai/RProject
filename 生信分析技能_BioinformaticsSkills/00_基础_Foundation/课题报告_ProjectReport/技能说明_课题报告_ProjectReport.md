---
name: bioinfo-project-report
description: >-
  课题终局报告：论文式 + 方法论 + 入口。没有另行说明就用侧栏版式、分节正文和逐图分析。
  触发：课题报告, 双报告, 论文式报告, 方法论报告, 报告生成, HTML报告。
---

# 课题报告 / ProjectReport

> **要求 SSOT：** [`文档_docs/报告要求_ReportRequirements.md`](文档_docs/报告要求_ReportRequirements.md)  
> **页面函数：** [`脚本_scripts/report_page.py`](脚本_scripts/report_page.py) 的 `page()` / `figure()` / `check_html()`  
> 样例报告不走本技能，走 DeliveryStandards 的样例报告范式。轨 B 图注页不替代本双报告。

没有另行说明时，凡是课题终局报告都按上面两处做。不要自写顶栏窄页，不要把图堆在一个「图」标题下。

## 1. 数据来源

本技能不产生生物学数据。正文数字来自该课题的结果表或 `_stats.json`。

## 2. 数据规范

- 三文件：`00_报告入口_index.html`、`01_论文式报告_PaperStyle.html`、`02_方法论报告_Methodology.html`
- 存放：`01_分析报告_AnalysisReport/03_最终报告_FinalReport/`
- 图：`图片文件/` 相对路径；内容哈希去重；两份报告各嵌同一套

## 3. 何时选用

用户要课题报告、双报告、论文式或方法论 HTML，或分析做完需要终局报告。  
不适用：技能样例的 `write_delivery_report()`；只改一张图的出图任务。

## 4. 数据处理方法

1. 读报告要求，列出论文式结果分节（按该课题实际做过的步骤，没做的不写进结果）。
2. 用 `page()` 写三份 HTML。论文式把图放进对应结果节；方法论把同一套图放进阅读指南，分析角度不同。
3. 每张图用 `figure_blocks()` 分块详写。论文式 4 块：`setup` / `findings` / `takeaway` / `boundary`；方法论 4 块：`legend` / `protocol` / `params` / `pitfall`。**§3.3.0 强制**：自洽可读、禁止「见方法论/见脚本」推诿、每块不得电报体；方法论须写清包名/函数名与参数阈值。依据见 `文档_docs/图后分块依据_FigBlockRationale.md`。
4. `check_html` 两份正文加入口。领域禁词用 `forbidden` 传入。
5. STATUS 写嵌图数和 provenance。

完成判据：`check_html` 通过（含每图强制块）；章节 id 与要求文件一致；嵌图数等于去重后的交付 PNG 数；坏链为 0。

## 5. 工具链

Python 标准库。版式在 `report_page.py`，不另抄一套 CSS。

## 6. 数据可视化

本技能不画出图。图已经按领域技能和 VizStandards 画好后再嵌入。对接拼图若已在图片目录，必须登记进图集。

## 7. 数据结果解读

论文式解释结果并写边界。方法论解释阈值。两份不互相粘贴成长文。每图分块，不写单段空评。

## 8. 能否结合其它生信

生成报告时叠加本技能 + DeliveryStandards。出图仍读该领域技能（网络药理学、对接等）。网络药理学正文另遵守该技能的禁词。

## 样例验证

样例待建。金标外壳是本目录 `report_page.py`（侧栏来自婷婷课题 `page()`）。无生物学样例数据。
