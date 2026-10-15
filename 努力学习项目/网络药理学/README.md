# 溃疡性结肠炎 · 12 味药 · 网络药理学

## 目录（强制）

```
网络药理学/
  数据文件/                 # RAW：契约表、上游疾病/药物、富集表、PPI 缓存
  代码文件/
    02–11 脚本（运行顺序见下）
    结果文件/
      图片文件/             # 轨 A：01–15 NN_中文_English.{png,svg}
      数据文件/             # 中间结果表
      报告文件/             # STATUS
  交付文件/                 # 轨 B：客户中文归档（11_pack 生成）
                            #   图注与解读说明.html（分享入口，相对路径含图）
                            #   图片/…（含 KEGG官方通路图）
                            #   数据/{疾病,药物,网络图,富集分析,PPI}/
                            #   报告/
  参考_交付原图/            # 微生信韦恩模板
  微生信上传_基因列表/
  _归档/                    # 仅放明确废弃物（默认可空）
```

规范 SSOT：`生信分析技能_BioinformaticsSkills/.../网络药理学_NetworkPharmacology/`  
出图约束状态：**`FROZEN`（2026-07-26 用户确认）** — 解冻前不得改视觉 recipe / 双口径 / HTML 约定。

## 一键重跑顺序

| 顺序 | 脚本 | 作用 |
|------|------|------|
| 1 | `02_prepare_skill_contracts.py` | 契约 |
| 2 | `03_compute_overlap_tables.py` | 药病交集 |
| 3 | `05_build_compound_hctp_contracts.py` | 成分/HCTP 边 |
| 4 | `04_enrich_clusterProfiler_and_replot.R` | GO/KEGG（若 `数据文件/富集*.csv` 已有可跳过） |
| 5 | `09_build_weishengxin_style_venn.py` | 01–02 韦恩 |
| 6 | `06_run_full_atlas_skill.R` | 全图册主入口 |
| 7 | `07_align_sample_parity.R` | 11–15 网络（通路全称；PPI≤200） |
| 8 | `10_replot_circos_and_compound_bar.R` | 04/05 等宽柱 + 10 圈图 |
| 9 | `11_pack_delivery_archive.py` | 轨 A → `交付文件/` |
| 10 | `26_build_html_report.py` | 根目录 HTML 报告（含统计；相对路径） |
| — | `24_download_kegg_pathway_maps.py` | KEGG Top20 官方通路图 |
| — | `23`/`25` | 桑基 17/18、热图 19 |

清理临时产物：`python 代码文件/_clean_project.py`（保留 `数据文件/` 与核心脚本）。
