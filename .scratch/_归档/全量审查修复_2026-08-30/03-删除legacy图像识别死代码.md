# 03 — 删除 legacy 图像识别死代码

标签: 已完成（2026-08-30）

## 修复记录

- `export_detail_png_from_pse.py` 900 → 361 行：删除 `export_detail_png_legacy`、`hide_code_console`、`detect_console_black_band`、`locate_toggle_click`、`open_pse_with_pymolwin`、`maximize_by_hotkey`、`close_pymol`/`send_alt_f4` 及其独占辅助（`click_screen`/`_cv2_read_bgr`/`force_window_restore`/`prepare_window_for_console_check`/`capture_window`/`capture_window_full`/`focus_window`/`ensure_maximized`/`is_maximized`/`wait_pymol_window`/`enum_pymol_hwnds`/键鼠常量/`WINDOWPLACEMENT`/`TEMPLATE_TOGGLE`）。
- 保留活代码：`_capture_hwnd_bitmap`/`extract_pymol_3d_canvas`/`cover_square`（钩子经 `PYMOL_EXPORT_HELPERS` 动态引用，已 grep 确认）。
- `git rm -r 脚本_scripts/assets/`（模板 + 5 张调试图，均仅服务 legacy）。
- 验证：模块导入 + `main()` 空根 smoke OK；对接 pytest 4 passed。真机 PyMOL E2E 未跑：桌面 `杨程茗分子对接`/`痤疮_分子对接_序号文件夹` 均已不在原位的，待项目目录恢复后补验。

## 来源

Standards 轴（Speculative Generality）+ Spec 轴（b）。

## 问题

SOP §7.3 主路径已是 PyMOL Qt API 钩子，但 `export_detail_png_from_pse.py` 仍含约 250 行不可达旧路径：`export_detail_png_legacy`、`hide_code_console`、`detect_console_black_band`、`locate_toggle_click`、`open_pse_with_pymolwin`、`maximize_by_hotkey`、`close_pymol`/`send_alt_f4`；`TEMPLATE_TOGGLE`（:29）与未跟踪 `assets/` 仅服务 legacy。

## 验收标准

- 删除 legacy 函数链与 `assets/pymol_console_toggle_template.png`；
- `main()` 无残留引用；`--debug-window` 等现行参数不受影响；
- 对 `杨程茗分子对接 --only 1` 重跑导出验证主路径完好。
