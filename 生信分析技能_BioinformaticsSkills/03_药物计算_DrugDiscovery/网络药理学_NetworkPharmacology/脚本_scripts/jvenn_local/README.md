# 本地 jvenn（微生信韦恩）

上游：[微生信 jvenn](https://bioinformatics.com.cn/static/others/jvenn/example.html)（Bardou et al. BMC Bioinformatics 2014）。

| 文件 | 用途 |
|------|------|
| `jquery.min.js` / `canvas2svg.js` / `jvenn.min.js` | 运行时（`jvenn.min.js` 已修 frame `height` 引号笔误） |
| `headless_venn.html` | 无头 Chrome 驱动：注入 `window.__JVENN_PAYLOAD__`，修标签位置/不透明度 |

**调用：** `脚本_scripts/weishengxin_venn_lib.py` → `render_jvenn_sets` / `write_disease_venn`。  
配色必须 `rgb(r,g,b)`。画幅留白见出图约束 **§G**。
