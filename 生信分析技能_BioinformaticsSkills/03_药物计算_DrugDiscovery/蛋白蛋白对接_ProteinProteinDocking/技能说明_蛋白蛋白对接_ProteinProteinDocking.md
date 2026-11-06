---
name: bioinfo-protein-protein-docking
description: >-
  蛋白–蛋白对接 / ProteinProteinDocking：两蛋白对接预测与交付。
  强制文献+结构特性调研定链；清理→HDOCK(默认)/ZDOCK/ClusPro→桌面序号文件夹→
  PyMOL ST/PT/CJ/QJ→手调截图→切方→result 拼图（复用分子对接 §7.3/§7.4）。
  触发：蛋白蛋白对接, PP docking, ZDOCK, ClusPro, HDOCK, 蛋白复合物对接, PPI docking, chain_survey。
  与分子对接(MolecularDocking，蛋白–配体)区分。
---

# 蛋白蛋白对接 / ProteinProteinDocking

> **基线（可调优）：** [`文档_docs/对接与交付基线_PPDockBaseline.md`](文档_docs/对接与交付基线_PPDockBaseline.md) — **BASELINE 2026-11-02**；确认「冻结」前可按该文 §4 调优。  
> **流水线 SSOT：** [`文档_docs/蛋白蛋白对接流水线_PPDockingSOP.md`](文档_docs/蛋白蛋白对接流水线_PPDockingSOP.md)  
> **调研定链：** [`文档_docs/结构调研与链选择_ChainSurvey.md`](文档_docs/结构调研与链选择_ChainSurvey.md)  
> **PyMOL：** [`文档_docs/PyMOL可视化_ST-PT.md`](文档_docs/PyMOL可视化_ST-PT.md)（**ST/PT/CJ/QJ**）  
> **拼图指针：** 分子对接 [`result拼图与detail导出定稿`](../分子对接与虚拟筛选_MolecularDocking/文档_docs/result拼图与detail导出定稿_CollageDetailExport.md)  
> **叠加：** DeliveryStandards + VizStandards + PlotQA。  
> **金标目录：** 桌面 `{ST}_{PT}_蛋白蛋白对接_序号文件夹/`（例：`ACACA_DLD_蛋白蛋白对接_序号文件夹/1/`）

## 1. 数据来源

PDB / EMDB / AlphaFold；课题 `.pdb` 须带来源前缀（Delivery §2.1）。

## 2. 数据规范

- `task_info`：`st_partner`/`pt_partner`、两侧 `chains_*` + `chain_source_*`、`het_policy`、`server`、`job_id`。  
- **禁止**未写 `01_clean/chain_survey.md` 就选链上传。  
- 清理默认 `keep_cofactor`（留 FAD/催化金属；去水与结晶试剂）。

## 3. 何时选用 / 不适用

| 选用 | 不适用 |
|------|--------|
| 两蛋白结合姿态 / PPI 粗模 | 蛋白–小分子 → [MolecularDocking](../分子对接与虚拟筛选_MolecularDocking/技能说明_分子对接与虚拟筛选_MolecularDocking.md) |
| HDOCK / ZDOCK / ClusPro | 仅结构清洗 → [ProteinStructure](../蛋白结构与建模_ProteinStructure/技能说明_蛋白结构与建模_ProteinStructure.md) |
| ST/PT 三视图 + detail/result | STRING 网络图册 → 网药 |

## 4. 方法（摘要）

1. 下载 → `summarize_pdb_chains.py` → **调研** → `chain_survey` → 登记 `chain_source`  
2. 清理 → 上传（默认 **HDOCK**；学术邮箱）→ 取回姿态 → 按链拆 ST/PT  
3. 写入桌面 `{ST}_{PT}_蛋白蛋白对接_序号文件夹/N/`  
4. `pymol_pp_dock_viz_standard.py`（ST/PT/CJ/QJ）→ big/surface/detail `.pse`  
5. **手调标签并截图** → `prepare_detail_square.py` → `combine_pp_result.py`（可多 detail 共 big）

## 5. 工具链

[`文档_docs/工具与服务器_Toolchain.md`](文档_docs/工具与服务器_Toolchain.md)；脚本见 `脚本_scripts/说明_README.md`。

## 6. 可视化

| 对象 | 含义 |
|------|------|
| **ST** | 固定侧蛋白（通常更大） |
| **PT** | 移动侧蛋白（通常较小） |
| **QJ** | ST↔PT 接触/氢键 |
| **CJ** | 两侧界面残基 |

对接前检查图 ≠ 对接构象。DPI≥600；English；未写明 → VizStandards。

## 7. 解读

服务器打分为粗筛；低分辨率 EM 须在 STATUS 标明局限。

## 8. 结合其它技能

ProteinStructure、MolecularDocking（§7.3/§7.4 拼图钩子）、网药 PPI、MD（可选精修）。

## 样例 / 异常

`01_样例_sample/`；`异常知识库_ExceptionKB/`。
