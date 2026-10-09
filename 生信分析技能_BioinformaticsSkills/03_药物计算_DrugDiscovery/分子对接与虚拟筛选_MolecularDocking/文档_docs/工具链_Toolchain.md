# 分子对接工具链

> 引擎与定心路线 **FROZEN**：[`技术路线_AutoSite_AutoDockGPU.md`](技术路线_AutoSite_AutoDockGPU.md)、[`对接与交付约束_DockingFrozen.md`](对接与交付约束_DockingFrozen.md)。  
> 本文件登记本机程序与路径。AD-GPU 分数与 Vina 分数分表，不可混写。

| 步骤 | 工具 | 本机位置 | 备注 |
|------|------|----------|------|
| 打分（默认） | AutoDock-GPU（AD4） | `E:\AutoDock-GPU\AutoDock-GPU.exe` | `--nrun 20` 可调；产出 `summary_adgpu.csv` |
| 打分（对照） | AutoDock Vina | 本机 Vina 可执行文件 | 非默认；`summary_vina.csv` |
| 地图 | AutoGrid / Meeko | 随 AD-GPU 路线 | 共晶用 Meeko `--box_enveloping` |
| 定心 | AutoSite | 无共晶时的主路径 | 质控失败再回退 |
| 定心回退 | P2Rank、Fpocket(+PRANK) | 按技术路线顺序 | 最后才是文献位点 / manual |
| 配体格式 | Open Babel | `obabel` | PDBQT、加氢 |
| 受体清洗 / 坐标 | Python `bio3d` 或技能脚本 | `脚本_scripts/` | R 侧条图用 ggplot2 |
| 三维图 | PyMOL | `E:\pymol\python.exe` | ST/PT/CJ/QJ；`pymol_dock_viz_standard.py` |
| detail 重导 | PyMOLWin | SOP §7.3 | 不回写 `.pse` |
| result 拼图 | Pillow | `E:\PythonProject\分子对接\2.分子对接结果图组合.py` | SOP §7.4 |
| 结构库 | 本地 PDB 库 | `D:\数据库\分子对接数据库` | 优先于临时下载 |
| 出图 | ggplot2 + 出版级出图 | VizStandards | DPI≥600；热图 SVG+PNG |

课题对接工作区（pdbqt、受体、姿态）留在课题目录，不复制进本技能。
