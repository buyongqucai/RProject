# 开跑门禁 EXCLUDE: long_gap — 结构缺环 ≥5 不跑

- 日期/体系：2026-10-13；ESR2@1L2J（`protein gap gate failed`）
- 状态：已解决

## 症状（怎么发现的）
SOP §9.0.3 门禁输出：`EXCLUDE: long_gap chain A 285-289 len=5 (>=5); chain B 281-293 len=13 (>=5)`，开跑即停。

## 判定（真异常还是假象）
真实门禁（非假象）：REMARK 465 / CA 缺口扫描确认连续缺环 ≥5。缺环处 pdbfixer 只补残基内原子、不砌 loop，强行跑会假不稳定。

## 补救（按序尝试）
1. 走自动重搭：`自动重搭初态_rebuildPoseRetry.py`（UniProt 检索 RCSB 候选，最大连续缺环 <5、分辨率排序、近缘口袋配体参照），如 ESR2：1L2J→3OLL。
2. 无合格候选：AlphaFold/同源模型路线（蛋白结构技能）再评；仍无则换靶点/体系并留档。
3. 登记表 `md重搭登记_PoseRetryRegistry.json` 补 gene/uniprot/ligand_cid/prefer_chain，重搭可全自动。

## 何时放弃
UniProt 下无 <5 缺环结构且模型路线不可用 ⇒ 弃该复合物，换体系（缺环 >5 的结构禁止放宽门禁硬跑）。

## 复盘
根因：PDB 晶体结构固有缺环。预防：开跑前即查 gap；登记表预填重搭参数。
