# 04 — 患病范式推进（Fig2/ROC/MR/scRNA）

标签: 待Agent处理  
Blocked by: （无；用户已确认仅人类 + 去生存）

## 目标

按 `文档/出图范式图册_FigureAtlas.md`（患病版）推进：

1. Fig2 致病相关基因：多队列一致 DEG/韦恩/森林（替代死亡 Cox）
2. 诊断 ROC：FOXO1 脓毒症 vs 对照
3. 发病 MR + coloc（ieu-b-4980 / ieu-b-69；路径 C）
4. GSE167363 定位 + 优势细胞分子特征

## 验收

- [x] Fig2 + 诊断 ROC 已落入 `结果文件/`（REAL / PASS）
- [x] 死亡旧图不进主 STATUS 必出列表（图册已改）
- [x] MR 无 JWT / eQTLGen 失败时诚实 BLOCKED（`STATUS_MR_Incidence.txt`）
- [ ] GSE167363 下载完成并跑通 `07_*.R`
- [ ] 用户提供 `OPENGWAS_JWT` 后重跑 `06_*.R` 得发病 MR 估计
