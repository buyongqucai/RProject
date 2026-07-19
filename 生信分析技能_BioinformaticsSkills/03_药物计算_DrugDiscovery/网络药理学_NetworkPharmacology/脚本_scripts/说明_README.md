# 网络药理学脚本说明

| 文件 | 作用 |
|------|------|
| `01_契约接口_DataContracts.R` | 单药/分库 CSV 契约读写与交集 |
| `02_可视化_NetworkPharmPlots.R` | 真韦恩、单药交集、成分交集（均分/按药水平柱）、GO/KEGG（含 circlize 圈图；图面 English only） |
| `03_STRING与网络图_StringNetwork.R` | STRING API/缓存 PPI；官方 3D 图下载；基础网络工具 |
| `04_交付网络布局_DeliveryNetworkLayouts.R` | **网络图布局 SSOT**（覆盖 `03_*`）：PPI Degree 同心；HCTP columns/ellipse；布局后 `viz_qa_network_nodes`（项目级 PlotQA） |
| `运行骨架_runSkeleton.R` | 项目入口骨架 |

**出图约束（最终约定）：** [`../文档_docs/出图约束_NetworkFigureStandards.md`](../文档_docs/出图约束_NetworkFigureStandards.md)

样例数据准备：上级目录 `_prepare_sample_from_delivery.py`（从用户交付按单药组装）。

网络预览（不重跑其它图）：`01_样例_sample/代码文件/02_run_network_preview.R`。
主样例：`01_样例_sample/代码文件/01_run_sample.R`。
结果目录：`01_样例_sample/代码文件/结果文件/`。

**Cytoscape**：可选精修（先看 R 预览）；勿用假边冒充 STRING。
