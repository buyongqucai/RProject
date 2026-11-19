# 蛋白–蛋白对接与交付基线（PPDockBaseline）

> **状态：BASELINE（可调优）** — 2026-11-02 固化；**2026-11-07 detail 切方定稿**。  
> **改规则：** 只改本文件 + 流水线 SOP；技能说明只留指针。  
> **执行 SSOT：** [`蛋白蛋白对接流水线_PPDockingSOP.md`](蛋白蛋白对接流水线_PPDockingSOP.md)  
> **拼图几何：** 分子对接 SOP **§7.4**；用户截图切方见本文件 §2.1（对接颜色函数，禁止自造）

## 1. 一句话流程

调研定链 → 清理上传 → **HDOCK（默认）** → 桌面序号文件夹/`1/`（仅最优）→ PyMOL ST/PT → 手调截图 → detail 切方 → result 拼图。

## 2. 定稿路径（正向）

| 步骤 | 定稿做法 |
|------|----------|
| 服务器 | 默认 **HDOCK**；登记 `server` / `job_id` |
| 交付夹名 | 桌面 `{ST}_{PT}_蛋白蛋白对接_序号文件夹/` |
| 交付构象数 | **默认只交最优 `1/`**；其余 rank 留 ServerRaw |
| 可视化 | `pymol_pp_dock_viz_standard.py`；**ST/PT/CJ/QJ** |
| 标签 | black；`label_bg_transparency=1`；outline black |

### 2.1 detail 定稿（只改路径）

| 场景 | 命令（只改路径） |
|------|------------------|
| 用户已截图（主路径） | 原图放 `图片/detail-N_用户原图.png` → `prepare_detail_square.py <原图> -o <图片/detail-N.png>` → 拼图 |
| 切方逻辑 | 对接 `build_key_content_mask` 定残基/氢键/标签 → 原图内裁正方形 → 拉到 6000²（不预放大、不垫白、禁止 `side=min` cover） |
| 仅有 `.pse`、未截图 | `export_detail_png_from_pse.py --root <任务夹>`（对接 §7.3 钩子） |
| 拼图 | `E:\PythonProject\分子对接\2.分子对接结果图组合.py --dir=<图片> <序号>` |

禁止自造切方；对接 `--from-image` 拒绝（勿对宽屏 PNG 做钩子后半段 cover）。

## 3. 调优入口

| 可调项 | 默认 | 落点 |
|--------|------|------|
| 默认服务器 | HDOCK | 本文件 |
| 交付构象数 | 1 | 本文件 + 打包脚本 |
| detail 满度/buffer | 0.72 / 4Å | 对接钩子（仅 `--root`） |
| 拼图引擎 | `E:\PythonProject\分子对接\` | 本文件 §2.1 |

## 4. 完成判据

- [ ] `chain_survey` + `task_info`  
- [ ] 桌面仅 `1/`：big/surface + detail（标签完整）+ result  
- [ ] detail **无**被 cover 切掉的残基/氢键/标签；**无**垫白边  
- [ ] 用户原图在 `图片/`（`detail-N_用户原图.png`）  
- [ ] STATUS 标明粗筛；PlotQA  
