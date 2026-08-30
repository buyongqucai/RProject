# 03 — 删除 legacy 图像识别死代码

标签: 待Agent处理

## 来源

Standards 轴（Speculative Generality）+ Spec 轴（b）。

## 问题

SOP §7.3 主路径已是 PyMOL Qt API 钩子，但 `export_detail_png_from_pse.py` 仍含约 250 行不可达旧路径：`export_detail_png_legacy`、`hide_code_console`、`detect_console_black_band`、`locate_toggle_click`、`open_pse_with_pymolwin`、`maximize_by_hotkey`、`close_pymol`/`send_alt_f4`；`TEMPLATE_TOGGLE`（:29）与未跟踪 `assets/` 仅服务 legacy。

## 验收标准

- 删除 legacy 函数链与 `assets/pymol_console_toggle_template.png`；
- `main()` 无残留引用；`--debug-window` 等现行参数不受影响；
- 对 `杨程茗分子对接 --only 1` 重跑导出验证主路径完好。
