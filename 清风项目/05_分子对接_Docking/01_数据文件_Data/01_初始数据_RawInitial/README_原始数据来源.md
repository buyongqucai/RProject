# 原始数据来源 README — 05_分子对接_Docking

**状态：PENDING（预留模块，2026-10-14 建骨架）**

## 本目录放什么

`01_RCSB_受体结构_ReceptorStructures/`：RCSB PDB 受体 + 清洗记录（去水/去非目标小分子/**必去核酸**；缺原子 pdbfixer 补全，原文件存 `*_pre_fix.pdb`）。
配体结构（核心成分）来自 PubChem/TCMSP SMILES，登记 CID 与加氢参数。
每体系 `DATA_SOURCE.md` 记 PDB ID、链、pose、`center_source`。

启动前提：核心靶 × 核心成分清单由用户确认；路线走对接 FROZEN（AutoDock-GPU）。
