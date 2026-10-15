# 代码文件说明

| 文件 | 用途 |
|------|------|
| `02_prepare_skill_contracts.py` | 准备技能契约 |
| `03_compute_overlap_tables.py` | 药病交集 |
| `04_enrich_clusterProfiler_and_replot.R` | clusterProfiler 富集 |
| `05_build_compound_hctp_contracts.py` | 成分/网络契约 |
| `06_run_full_atlas_skill.R` | 全量图册主入口 |
| `07_align_sample_parity.R` | 11–15 网络（全称通路；PPI≤200） |
| `08_export_uc_venn_from_delivery.py` | 微生信 SVG → 01/02 |
| `09_build_weishengxin_style_venn.py` | 模板+UC 数据生成韦恩 |
| `10_replot_circos_and_compound_bar.R` | 04/05 等宽柱 + 10 圈图 |
| `11_pack_delivery_archive.py` | 轨 A → 项目内 `交付文件/` |
| `_clean_project.py` | 删除归档/缓存/旧结果，保留 raw |

推荐：日常改数据后按 README 顺序 1→9；只改柱/圈跑 `10`；只打包跑 `11`。

## KEGG 通路动画管线（50–54）

| 文件 | 用途 |
|------|------|
| `50_download_kegg_official_pngs.py` | 按清单下载 KEGG 官方通路 PNG |
| `51_extend_kegg_mapping.py` | 映射表扩展（184–213 批） |
| `52_sync_kegg_mapping_and_manifest.py` | 该批 xlsx → 清单 CSV + `kegg_zh_names.py` |
| `53_extend_kegg_full.py` | 全量扩展：hsa 补齐 + map 中药相关代谢通路（213→469），规则翻译中文名（词表+句型+ID 覆盖），下载 PNG |
| `54_sync_kegg_full.py` | 53 扩展后的同步：追加清单 CSV 与 `kegg_zh_names.py`（幂等） |
| `47_build_full_prompts.py` | 按清单为指定 rank 区间生成 SDXL 全提示词（`_gpu_prompts/`） |
| `45_local_sd_bases.py` | 本地 GPU（RTX 4060）SDXL 生成动画底图 `_bases/` |
| `48_parallel_compose.py` | 多进程合成 GIF → `交付文件/图片/动画_生物结构/` 并复制到 `D:\数据库\KEGG数据库\KEGG动画图` |

顺序：`53 → 54 → 47 <start> <end> → 45 --batch <start> <end> → 48 <start> <end>`。
