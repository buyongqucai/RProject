# 信源与工具选型（SSOT）

检索日期：**2026-10-30**。执行分析前核对两处是否已有更新，并把实际用到的版本写入运行记录：

1. Burgess 指南是否已超过 version 3：<https://wellcomeopenresearch.org/articles/4-186>
2. 下表各包的 CRAN / 官方 GitHub 版本

指南原文写明至少每 24 个月更新一次。2023-08-04 的 version 3 到本次检索仍是该记录的最新版，未见 version 4。

## 信源层级

只采用下列层级。博客、未标注出处的中文教程、二次转述不作为参数依据。

| 层级 | 用途 | 文献或文档 | 入口 |
|------|------|------------|------|
| 操作指南 | 做哪些分析、主分析用哪种 IVW | Burgess S, Davey Smith G, Davies NM, et al. Guidelines for performing Mendelian randomization investigations: update for summer 2023 [version 3]. *Wellcome Open Res.* 2023;4:186. doi:10.12688/wellcomeopenres.15555.3 | <https://wellcomeopenresearch.org/articles/4-186/v3> |
| 报告规范 | 写报告时逐项覆盖 | Skrivankova VW, et al. STROBE-MR Statement. *JAMA.* 2021. PMID 34698778；说明与范例：*BMJ.* 2021;375:n2233 | <https://www.strobe-mr.org/> ；清单 <https://www.strobe-mr.org/download/strobe-mr-checklist/> |
| 方法总述 | 工具变量三条假设、三角验证 | Sanderson E, et al. Mendelian randomization. *Nat Rev Methods Primers.* 2022;2:6. doi:10.1038/s43586-021-00092-5 | <https://www.nature.com/articles/s43586-021-00092-5> |
| 概念与名词 | 与 IEU 用法对齐 | MRC IEU MR Dictionary | <https://mr-dictionary.mrcieu.ac.uk/> |
| 两样本流程文档 | 抽工具变量、协调、作图的函数与默认参数 | TwoSampleMR 官方文章与函数页 | <https://mrcieu.github.io/TwoSampleMR/> |
| 估计方法实现 | 与指南 Table 1 对齐的估计函数 | `MendelianRandomization` CRAN 手册与 NEWS | <https://cran.r-project.org/package=MendelianRandomization> |
| 汇总数据 API | OpenGWAS 取数与 LD | IEU OpenGWAS API；`ieugwasr` changelog | <https://api.opengwas.io/api/> ；<https://mrcieu.github.io/ieugwasr/news/> |
| 汇总数据标准 | 自行下载的 GWAS 文件 | NHGRI-EBI GWAS Catalog 文档；GWAS-SSF | <https://www.ebi.ac.uk/gwas/docs/> ；<https://www.ebi.ac.uk/gwas/docs/gwas-ssf/summary-statistics-format> |
| 分子位点 | 表达等 xQTL 中介 | SMR & HEIDI 官方说明。Zhu Z, et al. *Nat Genet.* 2016;48:481-487 | <https://yanglab.westlake.edu.cn/software/smr/> |

指南把三条工具变量假设写为：变异与暴露相关；变异不因混杂路径与结局相关；变异只通过暴露影响结局。操作指南与 STROBE-MR 分工不同：前者决定做哪些分析，后者决定报告里写哪些项。

## 现行默认工具

默认路径是**汇总数据、两样本、工具变量经 LD 剔除后近似独立、单一暴露**。数据管道用 TwoSampleMR，主分析数字用 `MendelianRandomization::mr_ivw`。

| 角色 | 工具 | 本次核对版本 | 安装位置 | 在默认路径中的职责 |
|------|------|----------------|----------|--------------------|
| 抽工具变量、协调、敏感性面板、作图数据 | TwoSampleMR | **0.7.13**（2026-10-20） | <https://github.com/MRCIEU/TwoSampleMR> ；文档 <https://mrcieu.github.io/TwoSampleMR/news/> | `extract_instruments` / `clump_data` / `harmonise_data` / `mr_ivw_mre` / 散点、森林、漏斗、留一 |
| OpenGWAS 与 LD | ieugwasr | **1.2.0**（CRAN 2026-10-07） | CRAN | JWT、`ld_clump`。TwoSampleMR 0.7.12 起改回依赖该 CRAN 版 |
| 主分析与指南 Table 1 方法 | MendelianRandomization | **0.10.0**（CRAN 2024-04-12） | CRAN。档案未见 2025–2026 新版 | `mr_ivw`、`mr_egger`、`mr_median`、`mr_mbe`、`mr_conmix`、`mr_cML`、`mr_mvivw`；0.9.0 起 `mr_ivw` 给出 F 统计 |

`MendelianRandomization::mr_ivw` 的 `model="default"`：工具变量 ≤3 个用固定效应，≥4 个用乘法随机效应；残差标准误不允许低于 1（欠离散时按固定效应）。这与指南「默认乘法随机效应、异质性不足时不损失精度」一致。

TwoSampleMR 里与之对应的是 **`mr_ivw_mre`**（不做欠离散校正）。`mr()` 默认会调用 `mr_ivw`，该函数会做欠离散校正，标准误可以小于固定效应。默认路径的主分析列使用 `mr_ivw_mre` 或 `MendelianRandomization::mr_ivw`，把 `mr()` 的默认结果整表保留为对照。

官方默认参数（TwoSampleMR 函数页，勿改成旧教程里的 `r2=0.01`）：

| 函数 | 参数 | 官方默认 |
|------|------|----------|
| `extract_instruments` | `p1` | `5e-8` |
| 同上 | `clump` | `1` |
| 同上 | `r2` | `0.001` |
| 同上 | `kb` | `10000` |
| `clump_data` | `clump_r2` | `0.001`（文档写明已从 `0.01` 改为 `0.001`） |
| 同上 | `clump_kb` | `10000` |
| 同上 | `pop` | `"EUR"` |
| `harmonise_data` | `action` | `2`（用效应等位基因频率判断回文 SNP 的链） |

`clump_data` 使用的 OpenGWAS LD 参考为千人基因组五个超级人群，仅保留双等位、MAF>0.01 的位点；参考面板中没有的变异会被去掉。本地 `plink` 参考与 `ieugwasr::ld_clump` 优先于反复调用 API。

OpenGWAS 除 `/status`、`/batches` 外的端点需要 JWT。令牌在 <https://api.opengwas.io> 账户页生成，有效期 14 天，经 `ieugwasr` 读取环境变量 `OPENGWAS_JWT`。令牌不写入仓库。

## 分支工具

默认路径跑通之前不安装、不调用这些包。进入对应分支时，把安装来源和 `packageVersion()` 写入运行记录。

| 分支 | 工具与本次核对版本 | 文献 | 何时进入 |
|------|-------------------|------|----------|
| 暴露与结局样本可能重叠 | **MRlap 0.0.3.3**（GitHub `n-mounier/MRlap`，不在 CRAN） | Mounier N, Kutalik Z. *Genet Epidemiol.* 2023;47:314-331. doi:10.1002/gepi.22522 | 校正 IVW 的弱工具变量、赢家诅咒和样本重叠。校正值与 IVW 有统计差异时，报告校正值 |
| 工具变量很多且偏弱 | **mr.raps**：CRAN 0.2 作者标明不再维护；R-universe 索引 **0.4.3**（2025-10-31） | Zhao Q, et al. *Ann Appl Stat.* 2020. 包文档指向 arXiv:1801.09652 | 安装 `qingyuanzhao/mr.raps` 的 GitHub 版。CRAN 0.2 不作为现行版本 |
| 多个暴露共用遗传预测因子 | **MVMR 0.4.9**（2026-10-19，R-universe `mrcieu`，仓库 `wspiller/MVMR`，不在 CRAN） | Sanderson E, et al. *Int J Epidemiol.* 2019;48:713-727 | `strength_mvmr` 做条件 F；`pleiotropy_mvmr` 做 Q。估计可用 `ivw_mvmr` 或 `MendelianRandomization::mr_mvivw`，运行记录写明用的哪一个 |
| 离群位点筛查 | **MRPRESSO 1.0**（`rondolab/MR-PRESSO`；代码日期 2017-06-29） | Verbanck M, et al. *Nat Genet.* 2018;50:693-698 | 只作离群筛查。指南 Table 1 写明：无效工具变量较多时假阳性很高。它不替代中位数、众数或 contamination mixture |
| 药物靶点 / 同一基因区 | **coloc 5.2.3**（CRAN 2023-10-03） | Giambartolomei C, et al. *PLoS Genet.* 2014;10:e1004383；Wallace C. *PLoS Genet.* 2020;16:e1008720 | 先做共定位，再解释该位点的 MR。需要 SuSiE 时使用手册中的 `coloc.susie`，并记录 `susieR` 版本 |
| 暴露是基因表达或其他 xQTL | **SMR + HEIDI**（Yang 实验室官方程序，源码 `JianYang-Lab/SMR`） | Zhu Z, et al. *Nat Genet.* 2016;48:481-487 | 官方页当前 `--heidi-mtd` 默认是 `1`（cis 区最多约 20 个 SNP）。沿用默认并在记录中写明 |
| 个体水平、单样本 | **OneSampleMR**（R-universe 索引 0.1.9.9000，2026-10-22，`remlapmot/OneSampleMR`） | 指南对单样本弱工具变量偏倚的方向说明 | 仅有个体数据时。两样本、无重叠时弱工具变量偏倚朝向无效；单样本朝向混杂关联 |

相关多效性（工具变量通过暴露–结局的混杂因素起作用，从而破坏 InSIDE）且手上有全基因组汇总统计时，可另加 CAUSE（Morrison J, et al. *Nat Genet.* 2020;52:740-747；仓库 `jean997/cause`）。本次未把某个 CAUSE 版本标成现行版；使用前读取该仓库版本并写入运行记录。

工具变量必须保留 LD 时，可用 GCTA-GSMR（Zhu Z, et al. *Nat Commun.* 2018;9:224）。独立工具变量的默认路径仍用 IVW，不把 GSMR 换成主分析。

## 指南 Table 1 在软件中的位置

下表只列出默认路径和常用敏感性会调用的方法。一致性假设以指南 Table 1 为准。

| 方法 | 一致性假设（指南 Table 1） | 本次默认栈中的函数 |
|------|---------------------------|-------------------|
| IVW | 全部工具变量有效，或水平多效性平衡 | 主分析：`MendelianRandomization::mr_ivw`；对照：`TwoSampleMR::mr_ivw_mre` |
| MR-Egger | InSIDE | 两包均有。同时报告截距 |
| 加权中位数 | 多数有效 | `mr_median` / `mr_weighted_median` |
| 众数法 | 复数有效（plurality valid） | `mr_mbe` / `mr_weighted_mode` |
| Contamination mixture | 复数有效 | `MendelianRandomization::mr_conmix` |
| MR-cML | 指南表：对三条工具变量假设的违反都较稳健的似然法 | `mr_cML`（包 0.7.0 起）或作者包 `xue-hr/MRcML` |
| MR-RAPS | InSIDE（离群点除外） | 分支：`mr.raps` |
| MR-PRESSO | 离群稳健 | 分支筛查：MRPRESSO |

模拟比较见 Slob EAW, Burgess S. *Genet Epidemiol.* 2020;44:313-329（指南 Table 1 的参考文献 26）。多种稳健方法一起报告；不从中挑选 p 值最小的一个作为唯一结论。

## 数据来源

每份暴露和结局汇总统计都记录：研究编号（OpenGWAS id 或 GWAS Catalog accession）、基因组版本、祖先、样本量（病例/对照分开）、效应量尺度（beta 或 log-OR）、下载 URL、下载日期、许可证。

| 来源 | 官方入口 | 使用要点 |
|------|----------|----------|
| IEU OpenGWAS | <https://opengwas.io> ；API <https://api.opengwas.io/api/> | 程序化取数走 `ieugwasr`。数据库内等位基因按参考序列正向链对齐，仍须 `harmonise_data` |
| GWAS Catalog | <https://www.ebi.ac.uk/gwas/> | 全基因组汇总统计优先取已转为 GWAS-SSF 的文件。Catalog 的策展位点阈值与 MR 的 `5e-8` 工具变量阈值不是同一件事 |
| FinnGen、UK Biobank 公开汇总统计、各联盟 | 各项目官网当前 freeze | 运行记录写 freeze 号或文件版本。不在技能里写死会过期的 freeze 编号 |

两样本的暴露与结局优先同一祖先。LD 参考人群与 `clump_data(pop=)` 和该祖先一致。指南指出不同祖先的 LD 不同，工具变量在结局人群中可能不再与暴露关联。

暴露若受社会分层或群体结构影响明显，且已有家系数据、把握度可接受，按指南考虑家系内 MR。家系内分析把握度通常更低；不精确的无效结果单独解释，不覆盖无关个体中的分析。

## 方法学锚点

实现细节以上文「操作指南」和软件手册为准。下列论文只用于在报告中标明方法出处：

- 工具变量比值与 IVW：Burgess S, Butterworth A, Thompson SG. *Genet Epidemiol.* 2013;37:658-665（TwoSampleMR 方法表 PMID 24114802）
- 弱工具变量与 F：Burgess S, Thompson SG. *Int J Epidemiol.* 2011;40:755-764。经验上关注平均 F 是否大于 10；MVMR 用条件 F
- MR-Egger：Bowden J, Davey Smith G, Burgess S. *Int J Epidemiol.* 2015;44:512-525
- 加权中位数：Bowden J, et al. *Genet Epidemiol.* 2016;40:304-314
- 众数：Hartwig FP, Davey Smith G, Bowden J. *Int J Epidemiol.* 2017;46:1985-1998
- 方向：Hemani G, Tilling K, Davey Smith G. *PLoS Genet.* 2017;13:e1007081（Steiger）
- 样本重叠对两样本 MR 的偏倚：Burgess S, Davies NM, Thompson SG. *Genet Epidemiol.* 2016;40:597-608
- 平台论文：Hemani G, et al. The MR-Base platform. *eLife.* 2018;7:e34408
- 包论文：Yavorska OO, Burgess S. *Int J Epidemiol.* 2017;46:1734-1739
- 临床阅读清单：Davies NM, Holmes MV, Davey Smith G. *BMJ.* 2018;362:k601
