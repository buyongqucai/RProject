# detail 标签被切掉 / 误用 cover 切方

- 日期/体系：2026-11-07 ACOX1 用户截图
- 状态：已定稿纠正

## 症状

对用户宽屏 detail 截图做 `side=min` 中心裁方后，左右残基/氢键/标签消失；或垫白边凑正方形。

## 判定

对接 §7.3 钩子后半段「视口中心裁方」**前提**是已 zoom 把标签放进方框。对任意用户 PNG 直接 cover = 真异常。

## 定稿补救（只改路径）

1. 用户原图放 `图片/detail-N_用户原图.png`  
2. `prepare_detail_square.py`：对接 `build_key_content_mask` → 原图内正方形 → 拉 6000²  
3. `E:\PythonProject\分子对接\2.分子对接结果图组合.py --dir=<图片> N`  
4. 对接 `--from-image` 拒绝执行；要钩子 1:1 才用 `--root`

## 复盘

根因：把钩子「裁方」一步当成可独立用于任意截图的 API。预防：基线 §2.1。
