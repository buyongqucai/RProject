# 脚本说明 / Scripts README — 统一可视化

## 文件

| 文件 | 作用 |
|------|------|
| `出版级出图_PublicationPlot.R` | `FIG_DPI=600`、`setup_cjk_fonts`、`save_plot_pub`（PNG+SVG）、`bioinfo_palette` / `theme_journal` |
| `出图后审核_PlotQA.R` | 出图后审核：`viz_qa_check_label_length` / `viz_qa_check_bbox_overlap` / `viz_qa_network_nodes` / `viz_qa_report` |

规范文档：[`../文档_docs/出图后审核_PlotQA.md`](../文档_docs/出图后审核_PlotQA.md)。

图面文字 **English only**（禁止中文）；交付文件名仍中英对照见 DeliveryStandards；勿把文件名双语拼进 `ggtitle`/`labs(title=)`。

**强制流程：** `delivery_save_plot` / `save_plot_pub` 之后跑 PlotQA（DeliveryStandards 钩子会调用 `viz_qa_after_plot`；网络图在布局后另调 `viz_qa_network_nodes`）。

书清镜像：`书清项目/共享脚本/工具_统一出图.R`（已同步 `save_plot_pub`；PlotQA 以本目录为 SSOT）。
