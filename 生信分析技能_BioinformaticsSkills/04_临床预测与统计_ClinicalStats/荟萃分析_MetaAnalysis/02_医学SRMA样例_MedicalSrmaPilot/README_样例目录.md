# 医学 SRMA Pilot — 胰腺癌新辅助 vs 直接手术

**级别：** L1 Pilot 图册（对齐高分刊图种；非完整 SR）  
**状态：** `REAL_PILOT`  
**图册 SSOT：** `../文档_docs/高分刊Meta图册与工作量_JournalFigureWorkload.md`

## 目录

```text
02_医学SRMA样例_MedicalSrmaPilot/
  数据文件/
    DATA_SOURCE.md
    03_提取表_Extraction_pilot.csv
    04_PRISMA计数_PrismaCounts_pilot.csv
    05_RoB2_pilot.csv
  代码文件/
    01_run_pilot.R
    结果文件/
      图片文件/   # 01–08：PRISMA / OS / LOO / DFS / funnel / Baujat / RoB / subgroup
      数据文件/
      报告文件/
```

## 运行

```bash
cd 02_医学SRMA样例_MedicalSrmaPilot/代码文件
Rscript 01_run_pilot.R
```

依赖：`ggplot2`、`metafor`。

## L1 出图（8）

| 序 | 内容 |
|----|------|
| 01 | PRISMA flow（手选路径） |
| 02 | OS forest |
| 03 | OS leave-one-out |
| 04 | DFS/RFS forest（示意） |
| 05 | Funnel（k&lt;10 仅视觉） |
| 06 | Baujat |
| 07 | RoB 2 traffic light（单人） |
| 08 | OS subgroup by population |

投稿包：`../文档_docs/投稿包交付清单_JournalDeliverables.md`
