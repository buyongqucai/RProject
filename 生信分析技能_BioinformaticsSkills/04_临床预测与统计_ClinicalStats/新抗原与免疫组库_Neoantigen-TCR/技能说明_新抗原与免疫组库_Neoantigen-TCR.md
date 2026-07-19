---
name: bioinfo-neoantigen
description: >-
  新抗原与免疫组库 / Neoantigen-TCR：HLA 分型前置 + 新抗原预测 + 免疫组库。。触发：新抗原, TCR, BCR, HLA, OptiType, netMHCpan。
  已合并：`HLA分型_HLA-Typing`。
---

# 新抗原与免疫组库 / Neoantigen-TCR

## 1. 数据来源

突变 VCF；WES/RNA（HLA 前置）；TCR/BCR 测序。

## 2. 数据规范（判断是否可用）

输入完整可溯源；分组官方或实验记录可核对；禁止编造结果数字。

## 3. 何时选用本技能

- HLA 分型前置 + 新抗原预测 + 免疫组库。
- 山水用途层：药物-细胞
- **不包含（边界）**：仅做体细胞 TMB/签名→肿瘤体细胞景观

不适用：应改用边界中列出的独立技能。

## 4. 数据处理方法

HLA 分型→肽段→MHC 结合预测；或 MiXCR 组库克隆型。

### 已合并原技能触发词

`HLA分型_HLA-Typing` 的触发需求一律走本技能（见 catalog `deprecated_ids`）。

## 5. R 包与软件栈

| 步骤 | R包或CLI | 作用 | 备注 |
|------|----------|------|------|
| 分析 | `ggplot2` | 核心 R 包 | |
| 上游/主分析 | `OptiType` | CLI | 非 R |
| 上游/主分析 | `HLA-HD` | CLI | 非 R |
| 上游/主分析 | `netMHCpan` | CLI | 非 R |
| 上游/主分析 | `MiXCR` | CLI | 非 R |
| 出图 | `ggplot2` + 出版级出图 | DPI≥600 | 可视化规范 |

## 6. 数据可视化

亲和力分布；**DPI≥600；SVG+PNG；中文；防遮挡**。

## 7. 数据结果解读

预测需实验验证。

## 8. 能否结合其它生信

肿瘤体细胞景观、免疫浸润；出图强制统一可视化规范。

## 9. 外部软件操作 SOP（BLOCKED 样例）

样例 `STATUS=BLOCKED`。OptiType HLA → 肿瘤 VCF 肽段 → netMHCpan → MiXCR/TRUST4 TCR 克隆图。

## 样例验证

样例：`01_样例_sample/`
