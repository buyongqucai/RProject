# 数据来源

- **data_provenance: REAL**（2026-08-30 由 BLOCKED 翻转：3HTB E2E 跑通，见下节）

- **技能**：`分子动力学模拟_MolecularDynamics`
- **analysis_kind**：`md_3htb`
- **规范**：统一交付规范_DeliveryStandards

## 3HTB.pdb（议题：MD 真实数据落地，2026-08-30）

- **data_provenance:** REAL
- **accession / source:** RCSB PDB 3HTB
- **URL:** https://files.rcsb.org/download/3HTB.pdb
- **内容:** T4 lysozyme L99A/M102Q（链 A，1364 原子）+ 配体 JZ4（2-propylphenol，10 原子）；结晶添加剂 PO4×2 / BME 与晶格水在预处理中去除
- **用途:** 蛋白-配体复合物 MD E2E（pdb2gmx→GAFF 配体拓扑→溶剂化→NVT/NPT→生产→RMSD/RMSF/氢键）；GROMACS 官方教程（Lemkul）标准体系
- **embedded:** 2026-08-30
- **样例存放：** `数据文件/01_复合物结构_3HTB.pdb`；MD 工作归档 `工作文件_MdWork/3HTB/`（阶段目录见该目录 `00_目录说明_Layout.md`）
