# 工具与服务器（PP Docking）

| 用途 | 工具 |
|------|------|
| 下载 | RCSB PDB / `wget`/`curl`；AFDB |
| 链调研辅助 | `脚本_scripts/summarize_pdb_chains.py` |
| 清理 | `脚本_scripts/clean_pp_structures.py` |
| 对接服务器 | **默认实操 [HDOCK](http://hdock.phys.hust.edu.cn/)**；备选 [ZDOCK](https://zdock.wenglab.org/)、[ClusPro](https://cluspro.bu.edu/)（可达性视网络，写入 `task_info.server`） |
| 可视化 | `pymol_pp_dock_viz_standard.py`（ST/PT/CJ/QJ）；解释器常用 `E:\pymol\python.exe` |
| detail 切方 | `脚本_scripts/prepare_detail_square.py` |
| result 拼图 | `脚本_scripts/combine_pp_result.py` → 引擎 `E:\PythonProject\分子对接\2.分子对接结果图组合.py` + 同目录 `背景图.png` |
| 出图规范 | VizStandards + DeliveryStandards |

邮箱：优先机构 `.edu` / `.edu.cn`；结果邮件用网页邮箱查收亦可。

基线调优入口：[`对接与交付基线_PPDockBaseline.md`](对接与交付基线_PPDockBaseline.md) §4。
