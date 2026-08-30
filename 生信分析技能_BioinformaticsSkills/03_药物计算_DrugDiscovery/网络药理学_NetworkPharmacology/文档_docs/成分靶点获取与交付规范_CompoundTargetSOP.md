# 成分→靶点获取与交付规范（SSOT）

> 与 [`技能说明_网络药理学_NetworkPharmacology.md`](../技能说明_网络药理学_NetworkPharmacology.md) §4.1 对齐。本文件把 **HERB / SwissTargetPrediction** 路径写死，避免再交付「UniProt 全表左拼」或杂散中间文件。

## 1. 瀑布（不变）

TCMSP（OB≥30%, DL≥0.18）→ BATMAN（**仅 known**）→ ETCM/ETCM2 → **HERB/TCMBank 取成分+SMILES → SwissTargetPrediction**。

有上游库的成分–靶点则**停在该层**，不得用 STP 预测结果覆盖 curated 靶点。

## 2. SwissTargetPrediction 预测方式

| 项 | 规范 |
|----|------|
| 站点 | https://www.swisstargetprediction.ch/ |
| 物种 | **Homo sapiens** |
| 输入 | 成分 **SMILES**（优先来自 HERB / TCMBank；可附 PubChem CID） |
| 推荐实现 | 程序化：先 `POST /locate.php`（页面坐标），再 `POST /predict.php`（`organism=Homo_sapiens`, `smiles=…`, `ioi=2`），解析 `result.php?job=…` 结果表；失败则 MANUAL 浏览器导出 |
| 保留阈值 | **Probability > 0**（剔除 `probability = 0` / 空分） |
| MW 过大或站点拒跑 | **不得编造靶点**；写入 `异常清单_CompoundTargetExceptions.csv` |

**说明：** STP 对每个 SMILES 通常返回 Top 预测列表；列表中 **probability=0** 的行一律删除。棕榈炭实测两成分返回行均为 >0，故删除数为 0，不等于“未执行过滤”。

## 3. 「空基因 / 空行」怎么处理

STP 表字段通常含：Target（蛋白名）、**Common name（基因）**、Uniprot ID、Probability。

| 现象 | 原因 | 处理 |
|------|------|------|
| `Gene Names (primary)` / Common name 为空 | 多为**多亚基复合物**，Uniprot ID 形如 `P06493&P14635` | **Swiss 成分明细表保留原行**；整合表用 UniProt reviewed human 将各 Accession **展开为基因** |
| 展开后仍无基因 | Accession 不在 reviewed human | **不进入整合靶点表**；可在规范说明中记 `unresolved` 条数 |
| 真正的空行（整行无蛋白/无 ID） | 解析噪声 | **删除** |

**禁止：** 把空 Common name 当成“空靶点”留给下游韦恩/STRING（会造成空节点）。

## 4. 交付文件（HERB→STP 路径，精简）

单药目录或 `准备文件/` 下**只保留**：

| 文件 | 内容 |
|------|------|
| `HERB_{药}_有效成分.csv` | HERB 匹配到的成分、SMILES、MW、ingredient_id |
| `HERB_{药}_靶点明细.csv` | HERB 侧草药/成分统计靶点（若有） |
| **`{化合物英文名}_Swiss预测靶点_筛选前.csv`** | 该成分 STP **原始返回**（未做 Probability 过滤） |
| **`{化合物英文名}_Swiss预测靶点_筛选后.csv`** | 同上，但仅 **Probability > 0**（复合物空基因可 UniProt 展开） |
| `{药}靶点基因.xlsx` | 整合靶点 + 与上列同名的工作表 |

### 4.1 Swiss 文件命名（强制）

用 SMILES 做 SwissTargetPrediction 时，**每个化合物各出两份**，名称必须带英文成分名，并区分筛选前后：

```
{compound_en}_Swiss预测靶点_筛选前.csv   ← STP 网站/接口返回原表
{compound_en}_Swiss预测靶点_筛选后.csv   ← Probability > 0 之后
```

示例：`cellulose_Swiss预测靶点_筛选前.csv`、`cellulose_Swiss预测靶点_筛选后.csv`。

- **禁止**只用 `Swiss_cellulose`、`STP成分靶点` 等看不出筛选阶段的名字当最终交付。
- 即便某次返回中 Probability≤0 行数为 0，**仍须同时保留「筛选前 / 筛选后」两套文件**（行数可相同，便于审计「已执行过滤」）。
- xlsx 工作表名与 csv 主名一致（Excel 限 31 字符）。

**`{药}靶点基因.xlsx` 工作表：**

| Sheet | 必备列 | 说明 |
|-------|--------|------|
| `整合靶点` | `成分`, `Protein names`, `Gene Names (primary)` | 各成分**筛选后**合并；**无空基因** |
| `{英文名}_Swiss预测靶点_筛选前` | STP 原列 + Probability | 与对应 csv 一致 |
| `{英文名}_Swiss预测靶点_筛选后` | 同上 + 可选 Gene 展开列 | 与对应 csv 一致 |
| `HERB_有效成分` / `HERB_靶点` | 与 csv 同构 | 单文件交付用 |
| `命名规范` / `文件命名对照`（可选） | — | 记录本药文件清单 |

**明确不做 / 不交付：**

- 不把 UniProt reviewed **全蛋白组**（约 2 万行）左拼进 `{药}靶点基因` 当作主表。
- 不保留疾病交集、STATUS、GeneList 等旁路文件，除非用户明确要求下游分析。
- 异常清单仅在有 error 时保留；全空文件可删。

## 5. 整合 schema（下游不变式）

进入药病交集 / 网络前，边表语义仍为：

**药物 – 有效成分 – 靶点(基因)**

由 `整合靶点` 的 `成分` + `Gene Names (primary)` 生成；药物名由文件名/项目表补全。

## 6. AUTO vs MANUAL（2026-07 修订）

| 步骤 | 状态 |
|------|------|
| **TCMSP-e 全量抓取**（token→搜索→成分 JSON→molecule.php 靶点） | **AUTO**：`脚本_scripts/TCMSP批量抓取_tcmspBatchScrape.py`（2026-08-31 验证，502 味全量 OK；模板列 FASA- 实为 tpsa 字段） |
| HERB 2.0 `chedi` API（search/detail） | **AUTO**（可达时） |
| SwissTargetPrediction 表单提交 + 结果解析 | **AUTO**（可达时）；失败 → MANUAL 导出 |
| BATMAN / ETCM / GeneCards 等 | 仍以 MANUAL 导出为主（无稳定公开 API） |

## 7. 空靶点药味（2026-07-27）

当某味药最终基因数为 **0**（如肉桂）：

1. **禁止**用 UniProt 全蛋白表（仅 `Protein names` / `Gene Names` 两列、约 2 万行）冒充该药靶点。
2. **禁止**为凑网络编造 TCMSP/STP 边。
3. 在交付中标注 **数据缺口 / BLOCKED_EXTERNAL**（见出图约束 **§K**）；网络可保留药节点但无边。
4. 补数路径：核对 TCMSP 拉丁名与 OB/DL → 或 HERB/TCMBank 取成分+SMILES → SwissTargetPrediction → 重写 `{药}靶点基因.xlsx`（须含成分–基因映射列，白术式 ≥5 列或 `整合靶点` sheet）→ 重跑交集与 HCTP。

与出图约束交叉引用：[`出图约束_NetworkFigureStandards.md`](出图约束_NetworkFigureStandards.md) §J（网络分析显示名）、§K（空靶点）。
