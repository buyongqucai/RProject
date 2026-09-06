# 医学 SRMA Pilot — 胰腺癌新辅助 vs 直接手术

**级别：** L1 Pilot（工具链验证）  
**状态：** `REAL_PILOT` — 真实 RCT HR，**不是**完整系统评价  
**规范：** DeliveryStandards + VizStandards；方法学对齐 PRISMA 2020 / GRADE（完整版见 `文档_docs/`）

## 目录

```text
02_医学SRMA样例_MedicalSrmaPilot/
  数据文件/
    DATA_SOURCE.md
    03_提取表_Extraction_pilot.csv
  代码文件/
    01_run_pilot.R
    结果文件/
      数据文件/     # 研究级 + 合并 + 留一法 CSV
      图片文件/     # 01 OS 森林 / 02 留一法 / 03 DFS-RFS 森林
      报告文件/     # HTML + STATUS
      补充材料_Supplementary/   # L2 投稿包占位
```

## 运行

```bash
cd 02_医学SRMA样例_MedicalSrmaPilot/代码文件
Rscript 01_run_pilot.R
```

依赖：`ggplot2`、`metafor`（若无：`install.packages("metafor")`）。

## Pilot 纳入（3 项 RCT）

| 研究 | 人群 | OS HR (95%CI) |
|------|------|----------------|
| PREOPANC 2022 | Resectable + BRPC | 0.73 (0.56–0.96) |
| Prep-02/JSAP05 | Resectable | 0.73 (0.56–0.95) |
| ESPAC5 2023 | BRPC | 0.29 (0.14–0.60) |

## 暂定假设（用户可改）

- Pilot **主分析 = OS**（三研究终点一致）
- DFS/RFS 作示意合并（定义不完全一致）
- BRPC：按原文作者定义；新辅助方案 **Broad**
- 未做全库检索 / RoB 2 / GRADE

完整投稿包清单：`../文档_docs/投稿包交付清单_JournalDeliverables.md`  
PROSPERO 提纲：`../文档_docs/PROSPERO方案提纲_ProtocolOutline.md`
