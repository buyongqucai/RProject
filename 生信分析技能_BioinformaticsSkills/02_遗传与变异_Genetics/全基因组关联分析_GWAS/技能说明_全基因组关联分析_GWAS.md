---
name: bioinfo-gwas
description: >-
  全基因组关联：质控、关联、矫正、功能注释。CLI：PLINK、REGENIE；R：qqman、
  CMplot、biomaRt。勿假装「纯 R 跑全 GWAS」。
---

# 全基因组关联分析 / GWAS

## 1. 数据来源

芯片/WGS 基因型；表型与协变量；公开 summary statistics（GWAS Catalog）。

## 2. 数据规范（判断是否可用）

样本质控、MAF、HWE、亲缘；表型定义清晰；知情同意与伦理完备。

## 3. 何时选用本技能

- 遗传关联、多基因风险、eQTL/共定位起点  
- 编排：遗传主线  

不适用：无基因型/无 summary stats。

## 4. 数据处理方法

PLINK QC → 关联（PLINK/REGENIE）→ λ/QQ → 注释 →（可选）PRS。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 质控/关联 | PLINK 1.9/2.0 | 主分析 | CLI 必需 |
| 大样本 | REGENIE | 混合模型 | CLI |
| Manhattan/QQ | `qqman` / `CMplot` | 出图 | R |
| 注释 | `biomaRt`, ANNOVAR | 基因注释 | R/CLI |
| 共定位（可选） | `coloc` | eQTL 共定位 | R |
| 出图规范 | 出版级出图 | DPI≥600 | |

## 6. 数据可视化

Manhattan、QQ、区域图；**DPI≥600；SVG+PNG；图面 English**。

**对齐高分期刊范式：** 遵循 [期刊范式](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/高分期刊出图范式_JournalFigureParadigm.md) + [PlotQA](../../00_基础_Foundation/统一可视化规范_VizStandards/文档_docs/出图后审核_PlotQA.md)；主题图种保持曼哈顿/QQ，配色与主题继承 VizStandards（勿强行套用火山顶替）。

## 7. 数据结果解读

基因组显著阈值；人群分层；关联≠因果。

## 8. 能否结合其它生信

转录 eQTL；TWAS；临床表型；多组学。

## 样例验证

样例：`01_样例_sample/`
