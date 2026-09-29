# 接诊与确认表单（SSOT）

> **地位：** 虚拟敲除任务唯一接诊正文。改字段/可信度词表只改本文件。  
> **强制：** 每次调用本技能 → 自动抽取 → 输出确认表 → **用户确认前禁止 Phase2（正式敲除）**。Phase1（公共数据可行性）可在 A 类关键字段确认后进行。

## 可信度词表

| 级 | 含义 |
|----|------|
| **H** | 方法原文或工具作者明确推荐 |
| **M** | 领域惯例 / 标准 ontology；课题焦点仍可改 |
| **L** | 启发式；必须知情同意 |

## 每次调用固定动作

1. Read 本文件 + [`方法默认与信源登记_MethodDefaultsRegistry.md`](方法默认与信源登记_MethodDefaultsRegistry.md) + [`出图图册_VkoFigureAtlas.md`](出图图册_VkoFigureAtlas.md) + [`数据集筛选与M4规程_DatasetScreening.md`](数据集筛选与M4规程_DatasetScreening.md)
2. 从用户消息/附件路径抽取 A 类字段（下表「抽取线索」）
3. 用方法登记表填满 B 类默认（带来源与可信度）
4. C 类标 `待Phase1` 或留空
5. 输出 Markdown 确认表（模板见下）；**停止等待确认**
6. 用户确认 A+B 后可 Phase1；Phase1 写回 C 后 **二次确认** 再 Phase2

## A. 课题必填（文献替不了）

| 字段 ID | 含义 | 抽取线索 | 空则 |
|---------|------|----------|------|
| `species` | 物种 | 小鼠/老鼠/mouse/人/human | 标红；本题常用 `Mus_musculus` |
| `gene_ko` | 敲除基因符号 | 基因名/CPLX2/Cplx2 | 标红，禁止猜测多个 |
| `tissue` | 组织 | TG/三叉神经节/Sp5C/DRG | 标红 |
| `bio_state` | 建网生物学状态 | naive/对照/造模/TN/CION/CFA | 标红或给选项 |
| `contrast_priority` | 数据检索优先级 | 「模型vs正常」「只要图谱」 | 默认询问 |
| `cell_universe` | 细胞宇宙 | 亚群/全神经元/含胶质 | 默认问亚群 vs 合并 |
| `method` | 主算法 | scTenifoldKnk/CellOracle/regulon | 默认 scTenifoldKnk（见 B） |
| `delivery_scope` | 交付边界 | 只做VKO/联合网药报告 | 默认问 |

## B. 文献/工具默认（仍列出供确认）

字段与默认值见 [`方法默认与信源登记_MethodDefaultsRegistry.md`](方法默认与信源登记_MethodDefaultsRegistry.md)。  
图序默认见 [`出图图册_VkoFigureAtlas.md`](出图图册_VkoFigureAtlas.md)。

## C. Phase1 后再定

| 字段 ID | 含义 |
|---------|------|
| `dataset_id` | GSE 或其它登录号 |
| `dataset_fit` | 是否满足物种+组织+状态+sc/sn |
| `fallback_choice` | 无理想集时的备选（如 Sp5C 模型 sc / naive TG atlas） |
| `subtypes_to_ko` | 实际敲除的亚群列表 |
| `n_cells_per_subtype` | 各亚群细胞数 |
| `gene_detection_rate` | 靶基因各亚群检出率 |

## 输出模板（Agent 必须用）

```markdown
## 虚拟敲除确认表

| 栏 | 字段 | 提议值 | 来源 | 可信度 | 你的确认 |
|----|------|--------|------|--------|----------|
| A | species | … | 用户 / 未提供 | H/— | [ ] |
| A | gene_ko | … | … | … | [ ] |
| … | … | … | … | … | [ ] |
| B | engine | scTenifoldKnk | Patterns 2022 | H | [ ] |
| C | dataset_id | 待Phase1 | — | — | [ ] |

**下一步：** 请改填或回复「表单确认」。未确认不跑正式敲除。
**禁止：** 将虚拟敲除结果写成真实动物 KO 的差异表达。
```

## 空白表单（可复制给用户手填）

见同目录附录语气：复制上表，提议值留空，由用户填写后发回。

## 与旧样例关系

`01_样例_sample` 中 TF-rescue 柱图 = **regulon 备选线**演示，不是 scTenifoldKnk 主线金标。主线出图以出图图册为准。
