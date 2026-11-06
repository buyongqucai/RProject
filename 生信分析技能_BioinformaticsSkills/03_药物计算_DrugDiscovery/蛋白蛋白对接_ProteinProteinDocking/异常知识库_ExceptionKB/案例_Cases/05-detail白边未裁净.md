# detail 截图四周仍有白边 / 拼图右框露白

- 日期/体系：2026-11-02；ACACA×DLD HDOCK detail-2
- 状态：已自动化

## 症状（怎么发现的）

用户反馈「detail-2 截图白边没有去掉」；正方形 PNG 顶/底仍可见整行近白带（anti-aliased flecks），拼进 `result_2` 后虚线框内边缘发白。

## 判定（真异常还是假象）

1. 读 PNG 边缘行：`(rgb >= 248).all(axis=2).mean(axis=1)`；若 top/bot 连续行 `white_frac >= 0.92` → **真白边**。  
2. 若边缘行 white_frac 约 0.3–0.5 且可见 cartoon 像素 → **假象**（结构留白，勿再裁）。  
决定性证据：连续整行/整列近白，而非构图内空隙。

## 补救（按序尝试）

1. `python 脚本_scripts/prepare_detail_square.py <截图> -o 图片/detail-N.png`（内含 docking trim + near-white + center square）。  
2. 仍露白：略降 `--white-frac`（如 0.88）重跑；**禁止**用白边 pad 成正方形。  
3. `python 脚本_scripts/combine_pp_result.py --img-dir 图片 --index N` 重拼。

## 何时放弃

用户新截图构图本身大片留白且残基已贴边仍「显空」→ 请用户重新取景，勿无限收紧阈值。

## 复盘（根因一句话 + 预防）

对接 `trim_white_border` 只裁「几乎全白」行，抗锯齿噪点会卡住；基线切方脚本已合并近白行/列裁剪。见 `对接与交付基线_PPDockBaseline.md` §2。
