# 中心位点方法登记（强制）/ CenterSourceRegistry

> **状态：生效；随对接技能 FROZEN（2026-09-05）** — 见 [`对接与交付约束_DockingFrozen.md`](对接与交付约束_DockingFrozen.md)  
> **归属：** 被技能入口与 [`分子对接流水线规范_DockingPipelineSOP.md`](分子对接流水线规范_DockingPipelineSOP.md) §5 引用。  
> **决策树：** [`技术路线_AutoSite_AutoDockGPU.md`](技术路线_AutoSite_AutoDockGPU.md) §2。  
> **定心/定边细则：** [`对接盒子定心与定边_DockingBoxProtocol.md`](对接盒子定心与定边_DockingBoxProtocol.md)。  
> **说明：** 共晶用于**定心/定盒**（`cocrystal_meeko`）；**不是**「把共晶配体再对接一遍算 RMSD」——后者本技能明确不做。

---

## 0. 强制原则

**每一个对接任务（每个蛋白×配体组合）必须写明：本任务盒子中心是用哪一种方法算出来的。**

- 禁止只写亲和力、不写 `center_source`。  
- 禁止用笼统词（如「口袋预测」「默认」「库表」）代替受控词表。  
- **受体级候选**写在 `分子对接_蛋白表.csv`；**任务级实际采用值**写在 `task_info` + `summary_*.csv`（二者 `center_source` 必须一致；若任务覆盖蛋白表，以任务为准并注明原因）。

---

## 1. 受控词表 `center_source`（任务级，唯一合法码）

| 码 | 含义 | 何时使用 | 必填细节字段 |
|----|------|----------|--------------|
| `cocrystal` | 单一共晶小分子重原子几何中心 | 有明确参考配体、未走 Meeko enveloping 时 | `ref_ligand`（`RESNAME:CHAIN[:RESI]`） |
| `cocrystal_meeko` | Meeko `--box_enveloping` + padding | 共晶包盒主路径（推荐） | `ref_ligand`；`padding`；`size_method=meeko_enveloping` |
| `annotated_site` | 文献 / UniProt 注释活性残基中心 | 无可用共晶、有可靠注释 | `site_residues`（如 `A:120,A:145`）；`site_citation` |
| `autosite` | AutoSite Top 位点（能量探针） | **无共晶时的默认主路径** | `autosite_rank`；`autosite_version`；`box_qc` |
| `p2rank` | P2Rank 预测口袋质心 | AutoSite 质控 FAIL 后回退 | `p2rank_rank`；`fallback_used=p2rank`；`fail_codes` |
| `fpocket` | Fpocket（可 +PRANK）质心 | P2Rank 仍歧义时回退 | `fpocket_pocket_id`；`fallback_used=fpocket`；`fail_codes` |
| `manual` | 人工指定坐标 | 文献位点手填 / 专家指定 | `center_note`（为何人工）；操作者 |
| `FAIL` | 无法定心，**不得对接** | 无有机共晶且口袋工具全失败等 | `fail_codes`；`center_note` |

**禁止写入正式结果的伪方法（废止码，出现即拒收）：**

| 废止码 / 做法 | 原因 |
|---------------|------|
| `chain_com` / 整链 COM | 违反位点对接原则（含 AlphaFold 全长） |
| `hetatm_all_mean` | 全 HETATM 无差别平均 |
| `library_blind` / 未校验照抄库表 | 库表仅候选；须重算或校验后改写为上表合法码 |
| `fixed22` 暗示的盲盒 | 固定边长 22 已废止 |

历史蛋白表若出现 `cocrystal_single_ligand_COM`，任务登记时归一为 **`cocrystal`**（细节仍写 `ref_ligand`）。

---

## 2. 决策树 → 应填码（与技术路线一致）

```text
有可用共晶小分子？
  ├─ 是 → center_source=cocrystal_meeko（或 cocrystal）
  └─ 否 → AutoSite
            ├─ box_qc=PASS → center_source=autosite
            └─ box_qc=FAIL → 依次试 p2rank → fpocket → annotated_site → manual
                              仍失败 → center_source=FAIL（阻塞，不写亲和力冒充）
```

同一靶点下多个配体任务：**中心方法通常相同**（受体级定心一次）；若某配体因盒过小扩边，**`center_source` 不变**，只改 `size_*` / `size_method`。

---

## 3. 必须落盘的位置（三处齐全）

| 位置 | 最低字段 |
|------|----------|
| 每任务 `task_info.txt`（或 `task_info.json`） | `center_source`、`center_x/y/z`、`size_x/y/z`、`size_method`、`box_qc`；有则 `ref_ligand` / `fallback_used` / `fail_codes` |
| `summary_vina.csv` 或 `summary_adgpu.csv` | 见 §4（**每一行一个任务**） |
| `分子对接_蛋白表.csv`（受体级） | `center_source` 或 `center_method`、`ref_ligand`、`center_note`、`x/y/z` |

报告/解读中引用亲和力时，**须同时给出该行的 `center_source`**（可表格一列，勿省略）。

---

## 4. summary 扩展列（与 `dock_summary_schema.py` 同步）

在原有 `task,protein,pdb,ligand,ligand_name,cid,affinity_kcal_mol` 之后，**新写任务必须追加**：

```text
center_source,center_detail,size_method,box_qc,fallback_used,engine
```

| 列 | 说明 |
|----|------|
| `center_source` | §1 受控码；缺列或空值 → 该行**不合格**（新工程） |
| `center_detail` | 一行可读细节，如 `STP:A:301` / `autosite_rank=1` / `P2Rank pocket1` |
| `size_method` | 如 `meeko_enveloping` / `autosite_box` / `rg_4_5x` / `vina2010_prod` |
| `box_qc` | `PASS` \| `FAIL`（采用回退前 AutoSite 结果亦记 FAIL+fallback） |
| `fallback_used` | 空，或 `p2rank` / `fpocket` / `annotated_site` / `manual` |
| `engine` | `vina` \| `adgpu`（两表勿混打分） |

旧工程仅有亲和力列时：读取脚本可容忍缺列，但 **Agent 不得在新跑批次中省略**；补登时按真实方法回填，禁止臆造 `cocrystal`。

---

## 5. 交付自检（勾选）

- [ ] 每个已对接 task 的 summary 行均有非空合法 `center_source`  
- [ ] `FAIL` 行无亲和力，或亲和力旁明确标注未正式打分  
- [ ] 无共晶靶点未静默写 `cocrystal`  
- [ ] AutoSite 异常任务的 `fallback_used` 与最终 `center_source` 一致  
- [ ] 热图/报告图注或附表能追溯「该能量对应何种定心」
