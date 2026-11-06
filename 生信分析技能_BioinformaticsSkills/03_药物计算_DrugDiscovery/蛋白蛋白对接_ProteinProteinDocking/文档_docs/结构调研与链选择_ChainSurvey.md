# 结构调研与链选择（ChainSurvey）

> SSOT 配套：[`蛋白蛋白对接流水线_PPDockingSOP.md`](蛋白蛋白对接流水线_PPDockingSOP.md) §2–§3。  
> 每个 PP 任务在清理前落盘：`01_clean/chain_survey.md`（可复制下方模板）。

## 1. 模板

```markdown
# chain_survey — <ST_gene> × <PT_gene>

## ST — <gene> / <pdb_id>
- title / method / resolution:
- biological assembly:
- literature (互作域 / 寡聚态 / PMID):
- chain table (from summarize_pdb_chains.py or PDB):
  | chain | n_res | note | HET |
  |-------|-------|------|-----|
- chosen chains: …
- chain_source: user_specified | literature_domain | auth_asym_partner | entity_longest | fail_need_input
- discarded chains + why:
- volume estimate (MB):

## PT — <gene> / <pdb_id>
- （同上）

## ST/PT assignment
- ST = …（更大/固定）; PT = …（较小/移动）
- rationale:

## Decision
- proceed | fail_need_input
```

## 2. 调研清单（勾选）

**文献**

- [ ] 双方是否有 PPI / 通路共现依据  
- [ ] 已知互作结构域或界面残基  
- [ ] 生理寡聚态（单体 / 二聚 / 纤维）

**结构自身特性**

- [ ] 分辨率与方法（X-ray / EM）；EM >4 Å 须在 STATUS 写局限  
- [ ] assembly 与 auth 链表  
- [ ] 全长 vs 片段链（残基数差一个数量级时勿一视同仁）  
- [ ] 辅因子（FAD 等）vs 结晶试剂（SO4、BTB、HOH）  
- [ ] 上传体积是否触服务器上限  

## 3. 示例：ACACA (6G2D) × DLD (6I4Q)

### ST — ACACA / 6G2D

| 项 | 内容 |
|----|------|
| title | Citrate-induced ACC-Cit filament，5.4 Å EM |
| assembly | 纤维；多条 ACC1 链 |
| 链表 | B≈625、F≈634（片段）；**C≈2121、D≈2121**（完整样原体） |
| HET | 无 |
| 文献要点 | ACC 纤维组装；对接伙伴时通常取**一个全长原体**，而非整段纤维 |
| chosen | **C**（或 D） |
| chain_source | `entity_longest`（纤维中完整原体；非“全链保留”） |
| discarded | B、F（短片段）；另一条全长原体（避免同蛋白自对接体积） |
| volume | 全原子单链仍大；ZDOCK 常需 CA/截域 → `model_note` |

### PT — DLD / 6I4Q

| 项 | 内容 |
|----|------|
| title | Human DLD，1.75 Å X-ray |
| assembly | **obligate homodimer** A+B（C2） |
| 链表 | A≈472、B≈481；各含 **FAD**；另有 BTB/SO4/HOH |
| 文献要点 | 功能相关二聚体；界面含跨亚基催化残基 |
| chosen | **A+B** + keep FAD |
| chain_source | `auth_asym_partner` |
| discarded HET | BTB、SO4、HOH（`keep_cofactor`） |
| volume | 二聚+FAD 通常可接受 |

### Assignment

- ST = ACACA chain C；PT = DLD A+B  
- 勿把 6G2D 的 B+C+D+F 全部上传当作“更完整”

## 4. 辅助命令

```text
python 脚本_scripts/summarize_pdb_chains.py path/to/raw.pdb
```
