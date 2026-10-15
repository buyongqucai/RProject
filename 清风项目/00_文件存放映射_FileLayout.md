# 清风项目 · 文件存放映射（FileLayout SSOT）

> 项目结构对齐 `生信分析技能_BioinformaticsSkills/项目结构规范_ProjectLayout.md` 与昱阳项目先例。  
> 原始数据命名强制来源库前缀（DeliveryStandards SampleLayoutNaming §2.1）；结果文件中英对照 `{NN}_{中文}_{English}`。

```text
清风项目/
├── 00_文件存放映射_FileLayout.md            ← 本文件
├── 01_分析报告_AnalysisReport/
│   ├── 01_课题说明_ProjectBrief/
│   │   ├── 01_研究计划_ResearchPlan.md      ← 科学问题/组方/路线 SSOT
│   │   └── 02_数据来源总览_DATA_SOURCE.md   ← 连通性矩阵 + 获取策略
│   ├── 02_阶段汇总_StageSummaries/          ← 数量断点结论、阶段小结
│   └── 03_最终报告_FinalReport/             ← HTML 报告（write_delivery_report 范式）
│       ├── 01_最终分析报告_FinalReport.html
│       └── 02_写最终报告_writeFinalReport.R
├── 01_疾病靶点_DiseaseTargets/
│   ├── 01_数据文件_Data/
│   │   ├── 01_初始数据_RawInitial/          ← {来源库}_疾病靶点_*（六库原始导出 + DATA_SOURCE.md）
│   │   └── 02_结果数据_ResultTables/        ← 韦恩计数、疾病并集（双口径）、审计
│   ├── 02_代码文件_Code/
│   ├── 03_图片文件_Figures/                 ← 疾病六库韦恩图（网药 FROZEN §G）
│   └── 04_报告文件_Reports/
├── 02_药物靶点_DrugTargets/
│   └── …同上结构…                           ← 每药瀑布：成分表、靶点表、异常清单
├── 03_药病交集与网络_OverlapAndNetwork/
│   └── …同上结构…                           ← 全药∩疾病、每药∩疾病、network.csv + type.csv
├── 04_富集与PPI_EnrichPPI/
│   └── …同上结构…                           ← STRING raw + GO/KEGG + 01–15 图序出图
└── 05_分子对接_Docking/                     ← 预留：AutoDock-GPU 冻结路线
```

## 约定

| 项 | 规则 |
|----|------|
| raw | `[{NN}_]{来源库}_{中文}_{English}.{ext}`；子目录同理；禁止 `raw.csv`/`输入/` |
| 结果表 | `{NN}_{中文表义}_{对象}_{EnType}.csv` |
| 图片 | `{NN}_{中文图类}_{主题}_{EnType}.png/.svg`（DPI≥600，图面 English only） |
| 报告 | 模块内 `01_STATUS.txt`；最终报告 HTML（相对路径引用图片） |
| 审计 | `审计前检_AuditPre.csv` / `审计后检_AuditPost.csv`；`data_provenance` 显式标注 |
| 大图/中间产物 | 默认不入库（ADR 0003）；脚本与登记文件入库 |
