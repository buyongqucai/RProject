---
name: formula-gut-metabolite-docking
description: >-
  复方–菌群代谢物–疾病三源整合后的靶点/成分/代谢物筛选与对接论文范式。
  网毒硬过滤有害小分子暴露物后得 C*，再算成分 Degree 与 STRING PPI 枢纽，分别对接成分与代谢物。
  触发：复方菌群代谢物对接, 三源靶点筛选, C星, 网毒后对接, FormulaGutMetaboliteDocking。
---

# 复方菌群代谢物整合对接 / FormulaGutMetaboliteDocking

> **研究思路与筛选标准 SSOT 夹：** [`研究思路与标准_Paradigm/`](研究思路与标准_Paradigm/)  
> **筛选标准正文：** [`研究思路与标准_Paradigm/筛选标准_SelectionCriteria.md`](研究思路与标准_Paradigm/筛选标准_SelectionCriteria.md)（改规则只改此处）  
> **对接引擎/单位：** 分子对接技能 FROZEN（主单位 **kcal/mol**，阈值默认 −5.0）

## 何时选用

- 课题同时有：**网药 F**、**菌群代谢物 M**、**疾病 D**，并要做**成分对接 + 代谢物对接**且共用过筛靶点宇宙。  
- 需要可引用的「先网毒过滤 → 再 Degree/PPI → 再对接」论文方法段。

## 不适用

- 纯经典网药（只成分×疾病）→ `网络药理学_NetworkPharmacology`  
- 只有暴露物毒理、无复方层 → `网络毒理学_NetworkToxicology`  
- 只改 Vina/盒子/PyMOL → `分子对接与虚拟筛选_MolecularDocking`

## 方法（三行）

1. `C = F∩M∩D` → 网毒硬剔除有害小分子暴露物相关靶点得 **C\***（LPS/H₂S 不整片删 C，见标准）。  
2. 在 C\* 上重算成分 Degree；STRING 边诱导 PPI，取 Degree/MCC 前几位靶点。  
3. 成分 / 代谢物各自终筛后，与枢纽靶点对接（kcal/mol）；旧硬编码对剔除。

## 脚本

- 课题执行入口（筛选 + 双轨对接 + 旧结果归档）：`努力学习项目/06_分子对接/代码文件/19_按标准筛选并对接.py`  
- 本技能 `脚本_scripts/` 仅存说明；Vina 引擎与单位遵循分子对接技能 FROZEN（kcal/mol）。

## 样例

见 `01_样例_sample/`（努力学习课题指针 + DATA_SOURCE）。  
**原始数据命名：** 上游/库导出须带库名或 `Upstream_`（见 DeliveryStandards SampleLayoutNaming **§2.1**；课题落地见 `努力学习项目/存放规范_ProjectLayout.md` §2.1）。

## 结合其它技能

网药交付 F/I₁ → 本技能筛选 → 分子对接引擎 → 可选 MD。出图叠加 VizStandards + DeliveryStandards。
