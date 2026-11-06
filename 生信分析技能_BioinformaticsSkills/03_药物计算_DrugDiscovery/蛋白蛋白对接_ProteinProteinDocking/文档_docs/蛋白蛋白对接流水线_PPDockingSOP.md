# 蛋白–蛋白对接流水线（PPDockingSOP）

> 本技能执行 SSOT。  
> **交付基线（可调优）：** [`对接与交付基线_PPDockBaseline.md`](对接与交付基线_PPDockBaseline.md)。  
> 拼图/detail 几何定稿**不在此复述**：分子对接 SOP §7.3/§7.4（指针见 [`result拼图与detail导出定稿`](../../分子对接与虚拟筛选_MolecularDocking/文档_docs/result拼图与detail导出定稿_CollageDetailExport.md)）。  
> 链调研细则：[`结构调研与链选择_ChainSurvey.md`](结构调研与链选择_ChainSurvey.md)。  
> PyMOL ST/PT：[`PyMOL可视化_ST-PT.md`](PyMOL可视化_ST-PT.md)。

## 0. 目录建议

流水线暂存（下载/清理/提交）可按阶段编号；**对接结果交付必须一任务一夹**（对齐分子对接金标「序号文件夹」）。

**用户可见金标（默认）：** 桌面 `{ST}_{PT}_蛋白蛋白对接_序号文件夹/`  
（工作区亦可写 `<课题>/PPDock_<ST>_<PT>/` 再拷到桌面同名交付夹；二者结构同构。）

```text
桌面/{ST}_{PT}_蛋白蛋白对接_序号文件夹/   # 或课题内 PPDock_* + 同构拷贝
  （可选）00_raw/ 01_clean/ 02_submit/ task_info.yaml STATUS.md
  summary_*_scores.tsv                  # 可放交付夹根或 ServerRaw
  00_服务器原始包_ServerRaw/            # 可选
  1/ … N/                               # 每个构象（rank）一个数字任务夹 —— 强制
```

### 0.1 单任务夹（强制，同分子对接 §2.2）

```text
N/
  model_N.pdb             # 服务器复合物
  ST_*.pdb  PT_*.pdb      # 按 task_info 链拆分后的可视化源
  interface_N.txt         # 若有
  task_info.txt
  big-N.pse  surface-N.pse  detail-N.pse   # .pse 只在任务根
  图片/                   # 所有 PNG 只在这里
    big-N.png  surface-N.png
    detail-1.png  detail-2.png …   # 多角度截图；切方后再拼
    result_1.png  result_2.png …   # 同一 big-N + 对应 detail
  # 禁止：任务根散落 *.png；禁止多构象共用一个「图片/」大杂烩
```

## 1. task_info 强制字段

| 字段 | 含义 |
|------|------|
| `st_partner` / `pt_partner` | 基因或蛋白名（ST=固定侧，PT=移动侧） |
| `pdb_st` / `pdb_pt` | PDB/AF ID |
| `chains_st` / `chains_pt` | 实际上传的链 ID 列表 |
| `chain_source_st` / `chain_source_pt` | 受控词，见 §3（两侧各自登记） |
| `chain_survey` | 相对路径，默认 `01_clean/chain_survey.md` |
| `het_policy` | `keep_cofactor` / `protein_only` / `custom` |
| `het_kept` / `het_dropped` | 残基名列表 |
| `server` | `zdock` / `cluspro` / `hdock` / … |
| `job_id` | 可空（待提交） |
| `model_note` | 如 CA-only、截域、分辨率 |

兼容旧字段 `partner_a`/`chains_a` 时：约定 a→ST、b→PT，并在 STATUS 注明迁移。

## 2. 结构调研（强制，先于选链）

**禁止**未写调研就清理上传。调研 = **文献** + **结构自身特性**，产出 `01_clean/chain_survey.md`（模板见 ChainSurvey 文档）。

| 维度 | 必查 |
|------|------|
| 文献 | 互作是否有实验/综述依据；已知互作结构域；寡聚态（单体/二聚/纤维） |
| PDB 页 | title、method、resolution、biological assembly、auth chain 表 |
| 链特性 | 每链残基数/是否全长/是否片段；HET（辅因子 vs 结晶试剂） |
| 体积 | 预估上传字节；ZDOCK≈1.2 MB/文件上限 |

脚本辅助：`脚本_scripts/summarize_pdb_chains.py`（只读统计，不替代文献结论）。

无依据且多链歧义 → `chain_source=fail_need_input`，**停**，问用户。

## 3. 链怎么选（必须登记）

在调研表写完后，按优先级写入 `chain_source_*`：

| 优先级 | `chain_source` | 做法 |
|--------|----------------|------|
| 1 | `user_specified` | 用户明确亚基或链 ID |
| 2 | `literature_domain` | 互作结构域已知 → 只留该域链/残基范围 |
| 3 | `auth_asym_partner` | 同源二聚/作者标注互作伙伴（如 DLD A+B） |
| 4 | `entity_longest` | 每实体取最长完整多肽（如纤维中全长原体） |
| 5 | `fail_need_input` | 多链且无依据 → 停 |

**是否该保留？**

- ST、PT 各至少保留其功能相关蛋白链。  
- 同聚体辅链：无互作证据默认不带（减小体积、避免假界面）。  
- 「保留 PDB 全部链」通常不可行（纤维/超大）且不等于更科学。  
- 核酸：默认剔除。  
- 截域：全长过大或分辨率极低时优先文献域；写 `model_note`。

**ST/PT 指派：** 通常更大或固定侧 → ST（ZDOCK Protein 1）；较小或移动侧 → PT（Protein 2）。用户指定优先。

## 4. 清理（het_policy）

默认 **`keep_cofactor`**：

| 类别 | 动作 | 例 |
|------|------|----|
| 蛋白 `ATOM` | 保留；去氢；altLoc 仅 ` `/`A` | — |
| 催化金属 | **保留** | MG, MN, ZN, FE, CA（非结晶堆积） |
| 辅因子 | **保留** | FAD, FMN, NAD*, HEM, SF4, PLP, TPP… |
| 水 | 删除 | HOH, WAT |
| 结晶试剂 | 删除 | SO4, GOL, EDO, PEG, BTB, ACT, DMS… |
| 不明 HET | 查 PDB 配体摘要；不确定 → `het_dropped` + STATUS | — |

`protein_only`：仅当服务器拒 HET 或用户明示；须写丢失辅因子风险。

脚本：`脚本_scripts/clean_pp_structures.py` → `*_clean.pdb` + `clean_report.json`。

## 5. 上传与取回

1. 学术/教育邮箱（`.edu.cn` 等）；个人 QQ / `*.wecom.work` 通常不可用。  
2. 体积超限 → CA 或截域并登记 `model_note`。  
3. 回执 HTML + `job_id` → `02_submit/`（或交付夹根 `task_info`）。  
4. **默认实操：HDOCK**；ZDOCK / ClusPro 当日可达且用户指定时改用，并写 `server`。  
5. 结果构象 → **直接写入** `{ST}_{PT}_蛋白蛋白对接_序号文件夹/N/`（`model_N.pdb`）；原始包可归档 `00_服务器原始包_ServerRaw/`。  
6. 按 `chains_st` / `chains_pt` 从 `model_N.pdb` 拆出 `ST_*.pdb` / `PT_*.pdb`。

主路径：半自动/手工上传 + 落盘；scratch 提交脚本仅作附录，不作脆弱主依赖。

## 6. PyMOL 与出图

| 阶段 | 要求 |
|------|------|
| 对接前检查 | 可并排 `fig_clean_check`；**不得**当对接结果交付 |
| 对接后 | 对象 **ST / PT / CJ / QJ**（见 PyMOL可视化_ST-PT） |
| big / surface | 完整入画；无残基标签；PNG 仅在 `图片/` |
| detail | **先手调标签再截图**（用户截图优先）；再 `prepare_detail_square.py` 切方 |
| result | 分子对接 §7.4；`combine_pp_result.py`（引擎=分子对接拼图脚本 + `背景图.png`） |

脚本：`pymol_pp_dock_viz_standard.py`（常用 `E:\pymol\python.exe`）；切方/拼图见 `脚本_scripts/说明_README.md`。

多角度：同一 `big-N` 可配 `detail-1`/`detail-2` → `result_1`/`result_2`。

## 7. 完成判据

- [ ] `chain_survey.md` 存在且含文献+特性结论  
- [ ] `task_info` 含 `st_partner`/`pt_partner`、两侧 `chain_source_*`、`het_*`、`server`、`job_id`  
- [ ] `clean_report.json` 与上传文件一致  
- [ ] 桌面序号文件夹内 `N/图片/` 含 big + detail（正方形）+ result  
- [ ] PlotQA；STATUS 标明粗筛局限  
