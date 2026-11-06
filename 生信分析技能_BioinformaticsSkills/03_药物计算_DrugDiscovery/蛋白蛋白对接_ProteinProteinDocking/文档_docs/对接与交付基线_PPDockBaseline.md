# 蛋白–蛋白对接与交付基线（PPDockBaseline）

> **状态：BASELINE（可调优）** — 2026-11-02 由 ACACA×DLD / HDOCK 跑通路径固化。  
> **改规则：** 只改本文件 + 流水线 SOP；技能说明只留指针。你确认「冻结」前**不要**写成 MolecularDocking 级 `FROZEN`。  
> **执行 SSOT：** [`蛋白蛋白对接流水线_PPDockingSOP.md`](蛋白蛋白对接流水线_PPDockingSOP.md)

## 1. 一句话流程

调研定链 → 清理上传 → **HDOCK（默认实操）** 取回 → **桌面序号文件夹** → 拆 ST/PT → PyMOL big/surface/detail → **手调截图** → detail 切方 → result 拼图。

## 2. 定稿路径（正向）

| 步骤 | 定稿做法 |
|------|----------|
| 服务器 | 默认 **HDOCK**；ClusPro/ZDOCK 可用则登记 `server` 后改用；学术邮箱 |
| 交付夹名 | 桌面 `{ST}_{PT}_蛋白蛋白对接_序号文件夹/`（对齐分子对接「痤疮_分子对接_序号文件夹」） |
| 单构象 | `N/`：`model_N.pdb`、`ST_*.pdb`、`PT_*.pdb`、三份 `.pse`、仅 `图片/*.png` |
| 拆链 | 服务器复合物按 `task_info` 链 ID 拆成 ST/PT 再可视化 |
| 可视化 | `pymol_pp_dock_viz_standard.py`；对象 **ST/PT/CJ/QJ** |
| 标签 | black；`label_bg_transparency=1`；`label_outline_color=black`（无白底晕） |
| detail | **用户手调后截图**（可多角度 `detail-1`/`detail-2`）；Agent 不臆造裁切内容 |
| 切方 | `prepare_detail_square.py`：白边裁剪 → 近白行/列 → **居中切正方形**（禁白边垫方） |
| 拼图 | `combine_pp_result.py` → 引擎 `E:\PythonProject\分子对接\2.分子对接结果图组合.py` + `背景图.png`；**同一 big-N + 各 detail → result_N** |
| 拼图右图 | 对接 §7.4：只裁纯白带后等比铺满虚线框 |

## 3. 与分子对接的关系

- detail/result **几何与拼图效力序** 复用分子对接 SOP §7.3/§7.4（指针不双写）。  
- PP 增量：双侧蛋白语义、序号夹中英名、多 detail 共 big、切方脚本对用户截图。

## 4. 调优入口（你之后改这里）

| 可调项 | 现状默认 | 落点 |
|--------|----------|------|
| 默认服务器 | HDOCK | 本文件 §2 + Toolchain |
| 桌面夹名模板 | `{ST}_{PT}_蛋白蛋白对接_序号文件夹` | 本文件 §2 + SOP §0 |
| 近白裁阈值 | thresh=248，white_frac=0.92 | `prepare_detail_square.py` |
| ST/PT 色 | cyan / salmon | PyMOL可视化_ST-PT |
| 拼图引擎路径 | `E:\PythonProject\分子对接\` | `combine_pp_result.py` |

## 5. 完成判据（基线交付）

- [ ] `chain_survey` + `task_info`（含 `chain_source_*`、`job_id`、`server`）  
- [ ] 桌面序号文件夹内至少 1 个构象：`big`/`surface`/`detail`/`result`  
- [ ] detail 为正方形且边缘无整行/整列近白带  
- [ ] STATUS 写明服务器打分为粗筛；PlotQA  
