# 网络毒理学工具链

> 步骤顺序：[`流水线摘要_Pipeline.md`](流水线摘要_Pipeline.md)。  
> 库是否可自动抓：[`数据库可抓取登记_FetchRegistry.md`](数据库可抓取登记_FetchRegistry.md)。  
> 本文件只登记程序与证据类型，不把预测边写成策展边。

| 步骤 | 工具 | 调用 | 备注 |
|------|------|------|------|
| 身份 | PubChem PUG-REST | AUTO_API | CID + SMILES；失败则停，不编造结构 |
| 活性 / 疾病 | ChEMBL REST、Open Targets GraphQL | AUTO_API | |
| 策展化学–基因/疾病 | CTD 本地表 | 用户下载的 `CTD_*.csv` | 商业使用先核对许可 |
| 预测靶点 | SEA、SwissTargetPrediction | 导出表 | `evidence=predicted`，不与 CTD 行合并 |
| 菌群轴 | gutMGene | 手工导出 | 不是 16S/代谢组实测 |
| 富集 / PPI | clusterProfiler、STRING、KEGG | 与网药相同交付约束 | |
| 出图 | VizStandards | R | **不用**网药 HCTP 的 FROZEN 配色冒充毒理图 |
| 可选对接 / MD | 分子对接技能、分子动力学技能 | 各自工具链 | 不在本技能里改对接 FROZEN |

课题里的 SEA/STP 原始文件、外部数据库留在课题 `准备文件/`，不迁进本技能。
