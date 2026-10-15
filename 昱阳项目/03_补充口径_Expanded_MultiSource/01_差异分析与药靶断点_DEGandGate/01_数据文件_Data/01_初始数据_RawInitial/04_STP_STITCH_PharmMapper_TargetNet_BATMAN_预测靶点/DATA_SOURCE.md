# 预测靶点多源

PubChem CID：**5280343**（Quercetin）；mol2：`quercetin.mol2`。  
整合脚本自动并入本目录 `*genes*.csv` / STP 筛选表（需含 `gene_human` 或等价基因列）。

## 各源状态与筛选（有依据才写入主分析）

| 源 | 主分析文件 | 筛选（主分析） | 依据 |
|----|------------|----------------|------|
| SwissTargetPrediction | `01_STP_Quercetin_筛选后.csv` | **Probability > 0** | 项目技能 CompoundTargetSOP；STP 官方将 Probability 定义为交叉验证平均精确率相关量，用于排序/取舍（NAR 2014/站点说明） |
| BATMAN-TCM 2.0 | `06_BATMAN_Quercetin_genes.csv` | API `score=20`（本课题预测拓宽口径） | BATMAN 查询参数 Score cutoff；与技能「瀑布仅 known」口径不同，此处为**预测拓宽**专用 |
| PharmMapper | `04_PharmMapper_Quercetin_genes.csv` | **研究相关物种（小鼠∪人）** + **Normalized Fit Score ≥ 0.6**（已采纳加宽版） | 见下节 |
| TargetNet | `05_TargetNet_Quercetin_genes.csv` | **Prob > 0** | 站点输出概率列；**无广泛统一官方数值门槛**，故仅剔除 0（与 STP 技能默认同形） |
| SEA | （未进库） | 文献/流水线常用 **P < 0.05**（或按表头 E-value 显著） | SEA 相似性集合统计；本机接口不可用 |
| Super-PRED | （未进库） | 常用 **Probability ≥ 60%** 且 **E-value ≤ 1** | SuperPred 方法学：E-value > 1 偏随机（PMC4086135 等） |

## PharmMapper（本课题写死）

**物种（与研究计划一致，不是“必须只做人”）：**

| 保留 | UniProt organism_id | 理由 |
|------|---------------------|------|
| 小鼠 | **10090** | 疾病臂 = 新生小鼠 GSE106799；CTD→小鼠符号 |
| 人 | **9606** | 计划写明实验/预测靶「优先人源再同源小鼠」；整合脚本做人→鼠映射 |
| 剔除 | 其它（细菌、酵母、噬菌体、植物等） | 与本课题物种无关 |

**分数（用户已确认采用加宽版）：**

- **主分析：Normalized Fit Score ≥ 0.6**（小鼠∪人）
- **严格审计：≥ 0.8**（文献更常见阈值，如 Curcuma longa ≥0.8；白术 >0.8 ± z-score>0.5）——仅存 `_audit/`，不自动并入
- 官网/NAR 2017：Normalized Fit / z′-score 优于裸 Fit（[Help](https://www.lilab-ecust.cn/pharmmapper/help.html)，[PMC5793840](https://pmc.ncbi.nlm.nih.gov/articles/PMC5793840/)）

**不作为主门槛：** 裸 Fit Score。

**审计文件：**

| 文件 | 含义 |
|------|------|
| `04_PharmMapper_Quercetin_genes.csv` | **主分析（已采纳）**：小鼠∪人 ∩ Norm Fit≥0.6 |
| `_audit/04_PharmMapper_Quercetin_genes_unfiltered.csv` | 筛选前备份（**不**自动并入整合） |
| `_audit/04_PharmMapper_Quercetin_genes_studySpecies_normFit0.8.csv` | 严格版（≥0.8；非主分析） |
| `_audit/04_PharmMapper_filter_meta.json` | 计数与引用摘要 |
| `04_PharmMapper_raw_rows.json` | 含 norm_fit 的原始行 |

脚本：`02_代码文件_Code/_pm_apply_filters.py`（依赖 `_pm_uniprot_org.json`）。

## 其它脚本

- BATMAN：`07_BATMAN预测槲皮素_FetchBatman.py`
- 提交/监听：`08_预测站提交与监听_SubmitAndPoll.py`
- Job 摘要：`00_预测站任务监听_JobMonitor.json`

## 说明

宽库结果上后过滤；重提交时可勾选与计划一致的靶库物种（小鼠/人），再套同一 Norm Fit 门槛。
