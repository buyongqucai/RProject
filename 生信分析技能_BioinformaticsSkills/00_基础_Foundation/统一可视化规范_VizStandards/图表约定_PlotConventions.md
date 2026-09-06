# 图表约定（通用）

详见上级 [技能说明](技能说明_统一可视化规范_VizStandards.md)。

## 高分期刊子图风格（强制）

- **DPI ≥ 600**；同名 **SVG + PNG**
- 默认主题：`theme_journal()`（白底、浅灰主网格、无次网格、细浅边框）
- 分组色：`bioinfo_groups`（muted 绿/红/紫：`#6B8F71` / `#C17B7B` / `#8B7BA8`）
- 热图/活性：`bioinfo_diverging_rb`（蓝–白–红，`#2166AC`…`#B2182B`）
- **热图标签一律黑色 `#000000`**（行/列名、格内 annot、轴标题、图例文字）；禁止随底色自动反白；Python/seaborn 须设 `annot_kws=dict(color="#000000")` 并显式设 tick/title 为黑色
- 火山：`bioinfo_volcano`（up `#C0392B` / down `#1A7A6D` / ns `#BDBDBD`）
- **富集默认：水平柱 / 气泡点图**（`bioinfo_enrich_facet`：BP/CC/MF/KEGG）；**禁止以棒棒糖（lollipop）为默认图种**
- UMAP 分类：`bioinfo_umap_discrete`；feature：`bioinfo_feature_blue`
- 图面 **English only**；文件名中英对照见 DeliveryStandards
- 参考面板映射（简述）：PCA/箱线→`bioinfo_groups`；火山→`bioinfo_volcano`；热图→BWR + 黑标签；富集→水平 bar/dot + facet 色；UMAP→discrete / feature blue
- 禁止彩虹、灰糊默认主题、用简陋柱图顶替韦恩/Cytoscape
- **规范回退**：领域技能未写明出图条款时，**先用本约定 / VizStandards 技能说明**（用户指定或 FROZEN 样例优先）
- **出图后审核（项目级强制）**：每张图保存后检查色块互挡、标签互挡、长标签版式；见 [`文档_docs/出图后审核_PlotQA.md`](文档_docs/出图后审核_PlotQA.md) 与 `脚本_scripts/出图后审核_PlotQA.R`
