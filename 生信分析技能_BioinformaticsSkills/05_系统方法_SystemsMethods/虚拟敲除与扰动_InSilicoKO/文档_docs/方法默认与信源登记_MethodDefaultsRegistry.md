# 方法默认与信源登记（SSOT）

> 改 scTenifoldKnk 默认参数或信源只改本文件。接诊表 B 类从此表填充。

## 主引擎

| 字段 | 默认 | 来源 | 可信度 |
|------|------|------|--------|
| `engine` | `scTenifoldKnk` | Osorio et al., *Patterns* 3:100434 (2022), DOI [10.1016/j.patter.2022.100434](https://doi.org/10.1016/j.patter.2022.100434)；[GitHub cailab-tamu/scTenifoldKnk](https://github.com/cailab-tamu/scTenifoldKnk) | H |
| `input_matrix` | 原始 counts，基因×细胞；`qc=TRUE` 时勿先归一化 | 包 README | H |
| `claim_language` | 输出为 virtual-KO **perturbed / DR genes**（计算预测），≠ 真实 KO DEG | *Patterns* 局限讨论 + 本技能硬规则 | H |

## 包参数默认（工具保真 = H；非课题最优证明）

| 字段 | 默认 | 来源 | 可信度 |
|------|------|------|--------|
| `param_nc_nNet` | 10 | CRAN / README | H |
| `param_nc_nCells` | 500 | 同上；亚群细胞不足时下调并披露 | H |
| `param_td_K` | 3（常用 3–5） | 官方 advanced vignette | H |
| `param_qc_minLibSize` | 1000 | 包默认；与数据集论文冲突时以数据集为准 | M–H |
| `param_qc_mt` | 小鼠基因前缀 `mt-` | 包文档（非 `MT-`） | H |

## 基因过滤

| 字段 | 默认 | 来源 | 可信度 |
|------|------|------|--------|
| `gene_filter_strategy` | 优先保留群体内 **高表达基因**；**不推荐**仅用 HVG 子集；必须包含 `gene_ko` | 作者回复 GitHub [Issue #33](https://github.com/cailab-tamu/scTenifoldKnk/issues/33) | H |
| `qc_minCells_note` | 部分版本 `qc_minCells` 可能未写回矩阵；预处理宜 **手动**按检出细胞数过滤 | GitHub [Issue #41](https://github.com/cailab-tamu/scTenifoldKnk/issues/41)（open） | M |

## 其它引擎（各自独立实例，不预设对照）

新增引擎只加卡片。如何开工见 [`虚拟敲除方法论_VkoMethodology.md`](虚拟敲除方法论_VkoMethodology.md)。  
**声称：** 结果表头与方法名必须与该引擎一致；禁止把 A 的数字标成 B。

| 引擎 | 何时单开一份实例计划 | 来源 | 可信度 |
|------|----------------------|------|--------|
| `GenKI` | 用户要 VGAE 虚拟敲除（可与 Knk 课题数据相同，但是另一份计划） | Yang et al., *NAR* (2023) [10.1093/nar/gkad450](https://doi.org/10.1093/nar/gkad450)；[GenKI](https://github.com/yjgeno/GenKI)。搜索项、15% 边阈值、1000 次排列与 top 5% / 95% 规则写在该课题实例计划，不套用本表 Knk 的 FDR | H |
| CellOracle | 用户点名 | — | M |
| DoRothEA regulon 逆转 | 仅 master TF + 已有 DEG；非转录因子不适用 | — | H（不适用边界） |

课题实例计划放在各课题目录，不在本登记表列举。

## 组织依赖标志（仅当 tissue=TG 等感觉神经节时启用）

| 字段 | 默认 | 来源 | 可信度 |
|------|------|------|--------|
| `markers_pep` | `Calca`（CGRP 肽能） | 小鼠 TG atlas 文献（如 Yang et al. / GSE197289 系） | H（TG） |
| `markers_nf200` | `Nefh`（NF200/有髓） | 同上领域惯例 | H（TG） |

换组织（如 Sp5C）时本块标 **不适用**，改用该数据集论文标志。

## 2026-09-30 已确认：画法与筛选分开

用户确认：网络**画法**用网药 PPI 同心渐变；**基因和边**用 scTenifoldKnk 论文（*Patterns* 2022）。

| 项 | 标准 | 来源 | 可信度 |
|----|------|------|--------|
| 谁能进网络/富集 | FDR < 0.05 的扰动基因；不按距离取 Top 40/50 | 论文 Trem2/Nkx2-1 例：FDR < 0.05 | H |
| 展示用的边 | STRING 蛋白互作；论文用互作富集 p < 0.01 | 论文 Figure 3/6；STRING 未写分数时用官网默认 medium **400** | H（库）；M（400，因论文未写分数） |
| 物种 | 小鼠课题用 taxonomy **10090** | STRING | H |
| 单基因查询 | **禁止**用 STRING 一阶邻域冒充子网；无 FDR 伙伴则不出多节点网 | 论文 egocentric 图注 | H |
| 同心环、Degree 颜色与大小 60–120 | 仅当 STRING 连通节点足够（建议 ≥8） | 网药 `出图约束` §B | H（画法） |
| 节点不够铺 4 环 | 不凑数、不补非显著基因；改 egocentric 或标注「无网」 | 论文人数 = 显著且 STRING 上连得上的基因 | H |
| `nc_nNet` / `nc_nCells` / `qc_minLibSize` / `td_K` | **10 / 500 / 1000 / 3** | CRAN `scTenifoldKnk` 1.1 默认参数 | H |
| 基因过多时 | 留高表达基因，不单用 HVG，必须留敲除基因 | 作者 GitHub Issue #33 | H |
| 前 100 Jaccard、`Rplp0` 阴性对照 | **不作为标准** | 论文无此条 | — |

出图脚本：`02_课题交付_Cplx2Control/代码文件/12_PDF标准网络_PlotFdrString.R`。  
旧 Top40+scGRN 网已弃用（桌面 `_deprecated_Top40非PDF标准/`）。

本次已交付的五群结果使用了缩小参数（3 张网络、200 个细胞、1000 基因、文库 500），**低于**上表官方默认，只能作试跑，不能当作按默认参数的正式结果。

## 富集焦点（可用课题覆盖）

| 字段 | 默认 term 方向 | 来源 | 可信度 |
|------|----------------|------|--------|
| `enrich_focus` | synaptic vesicle cycle；SNARE complex；neurotransmitter secretion | GO / Reactome 标准 ontology；交付写 term ID | M–H |

## 出图

| 字段 | 默认 | 来源 | 可信度 |
|------|------|------|--------|
| `figure_atlas` | [`出图图册_VkoFigureAtlas.md`](出图图册_VkoFigureAtlas.md) 序 01–07 | PDF 图种结构 + Viz/Delivery | H（结构）；结果须重绘 |
| `forbid_pdf_screenshot_as_result` | TRUE | 版权与真实性 | H |
