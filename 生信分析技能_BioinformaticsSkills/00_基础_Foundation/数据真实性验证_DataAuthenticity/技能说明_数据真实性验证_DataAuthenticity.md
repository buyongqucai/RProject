---
name: data-authenticity-verification
description: >-
  数据真实性验证：核对 GEO/NGDC/TCGA 样本数、分组来源、矩阵一致性，防编造。
  公共数据挖掘强制先用。脚本：书清项目/校验/数据真实性核对.R。
---

# 数据真实性验证 / DataAuthenticity

## 1. 数据来源

GEO/NGDC/TCGA 官方页面与本地 `源数据/下载清单.json`、表达矩阵、sample_info。

## 2. 数据规范（判断是否可用）

- 样本数 = 官网；分组来自 SOFT/characteristics  
- 无 average/汇总污染列；矩阵列与元数据一一对应  
- FAIL 必须修复后才能继续分析  
- **样例/交付强制标注** `data_provenance: REAL|TOY|BLOCKED`（写入 `DATA_SOURCE.md`、`STATUS.txt`、审计 CSV）  
  - REAL：须有 accession / 官网 URL / 英文病名或单药查询词 / 用户交付 provenance 可核对；**禁止**把「交付中间表」写成「已自动 API 爬取」  
  - TOY：必须写明不可外推；**禁止**包装成真实生物学结论；名似公共库的技能（如 GEO-TCGA）若仍为 TOY 须在报告大红标注  
  - BLOCKED：契约桩，不得冒充完整分析 PASS  
- **图册完成度**另用 `STATUS=PASS|PARTIAL|BLOCKED_EXTERNAL`（见 DeliveryStandards 图册门禁）；缺 GUI 图须在 skill 写软件操作 SOP，禁止伪图顶替  


## 3. 何时选用本技能

- 任何公共库下载/挖掘（GEO、TCGA、NGDC）  
- 用户质疑样本数/分组是否编造；交付前审计  

不适用：完全自有、未发表、无公共登录号的数据（仍建议内部核对设计表）。

## 4. 数据处理方法

七步：来源溯源 → 样本数对齐 → 分组真实性 → 矩阵↔元数据 → DEG 合理性 → 结果可溯源 → 可复现。  
运行：`Rscript 书清项目/校验/数据真实性核对.R` 或本目录包装脚本。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 核对脚本 | 基 R + `utils` | 读写 csv/json | 书清 `数据真实性核对.R` |
| GEO 元数据（可选） | `GEOquery` | 拉 SOFT/series | 与书清 `工具_GEO元数据.R` |
| 本库包装 | `运行真实性核对_runAuthenticityCheck.R` | source 书清脚本 | `脚本_scripts/` |

## 6. 数据可视化

本技能以报告表为主；若出 QC 图须走可视化规范。

## 7. 数据结果解读

`[FAIL]` 阻断交付；`[WARN]` 须写进局限。诚实优先于「看起来完美」。

## 8. 能否结合其它生信

编排与 `公共库挖掘_GEO-TCGA`、`转录组分析_RNA-seq`、`单细胞与空间转录组分析_scRNA-Spatial`、`差异分析与UMAP流水线_DEG-UMAP` 的硬前置。

## 样例验证

样例：`01_样例_sample/`
