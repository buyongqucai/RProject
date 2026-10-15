# 原始数据来源 README — 04_富集与PPI_EnrichPPI

**状态：PENDING（2026-10-14 建骨架）**

## 本目录放什么

`01_STRING_PPI网络_StringPpiNetwork/`：STRING API **原始响应快照**（版本/ID 映射/网络 JSON）+ `DATA_SOURCE.md`。
⚠️ 流水线须先落盘 raw 再出派生表（昱阳项目曾因只存派生表导致 raw 缺失、事后补登记）。

## 上游指针（本模块不直接抓库的部分）

| 输入 | 上游位置 |
|------|----------|
| 药∩病基因（ORA/PPI 输入） | `../../03_药病交集与网络_OverlapAndNetwork/01_数据文件_Data/02_结果数据_ResultTables/` |
| GO/KEGG | clusterProfiler + org.Hs.eg.db + KEGG(hsa)（软件库，无文件型 raw，版本记 DATA_SOURCE） |
