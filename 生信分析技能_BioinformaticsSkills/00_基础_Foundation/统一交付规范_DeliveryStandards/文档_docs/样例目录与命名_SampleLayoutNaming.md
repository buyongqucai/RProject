# 样例目录与命名 / Sample Layout & Naming

**SSOT：** `统一交付规范_DeliveryStandards`  
**适用范围：** `生信分析技能_BioinformaticsSkills/` 下全部技能的 `01_样例_sample/`（及 `02_`…）  
**配套：** [`样例结构迁移清单_SampleLayoutMigration.md`](样例结构迁移清单_SampleLayoutMigration.md)

---

## 1. 规范目录树（强制）

```text
01_样例_sample/
  数据文件/                         # RAW only：原始/输入数据（下载、用户交付、缓存的上游表）
    01_<中文>_<English>.{csv|tsv|…} # 多文件时按摄入顺序编号
    DATA_SOURCE.md
    PROVENANCE.json                 # 可选
  代码文件/                         # 脚本 + 由其产生的结果
    01_run_sample.R                 # 主流程（编号 = 推荐运行顺序）
    02_run_….R                      # 可选子流程
    结果文件/                       # 分析结果（禁止再放回样例根）
      数据文件/                     # 表/网络导出等
        01_<中文>_<English>.csv
      图片文件/
        01_<中文图类>_<主题>_<EnType>.{png,svg}
      报告文件/
        STATUS.txt
        样例报告_SampleReport_v1.html
```

### 文件夹角色（硬规则）

| 路径 | 角色 | 允许 | 禁止 |
|------|------|------|------|
| `01_样例_sample/数据文件/` | **原始/raw 输入** | 公共库下载、用户交付中间表、API 缓存、`DATA_SOURCE.md` | 脚本跑出的差异表、Cytoscape 导出、审计后检、最终图 |
| `01_样例_sample/代码文件/` | 可执行脚本 | `*.R` / `*.py`（编号前缀） | 把结果目录放回样例根 |
| `01_样例_sample/代码文件/结果文件/` | **结果数据** | 图、结果表、STATUS、HTML 报告 | 伪装成 raw 的分析产物 |

**兼容旧布局：** 若仍存在样例根级 `结果文件/`，R 助手 `delivery_sample_paths()` 会回退使用它；**新样例与迁移后样例必须用嵌套路径**。

---

## 2. 编号规则

- 两位零填充：`01`、`02`、…、`99`
- **脚本：** 按推荐运行顺序（主样例 = `01_run_sample.R`）
- **结果图/表：** 按流水线产出顺序（与脚本内写出顺序一致）
- **raw 输入：** 按摄入/依赖顺序；单文件可省略编号，多文件建议编号
- 编号之后仍遵守中英对照：`{NN}_{中文语义}_{EnglishPascal}.{ext}`
- 审计/报告固定名可加编号前缀，也可保持 `审计后检_AuditPost.csv` / `样例报告_SampleReport_v1.html`（迁移期允许不编号；新建优先编号）

示例：

| 类型 | 示例 |
|------|------|
| 脚本 | `01_run_sample.R`、`02_run_network_preview.R` |
| 图 | `01_韦恩图_DrugDisease_Venn.png` + 同名 `.svg` |
| 结果表 | `03_药物疾病交集_DrugDiseaseOverlap.csv` |
| raw | `01_样本元数据_SampleMeta_GSE10072.csv` |

R API：`delivery_order_prefix(n)`、`delivery_stem(..., order = n)`、`delivery_save_plot(..., order = n)`（见 `规范_出图与命名_PlotNaming.R`）。

---

## 3. 路径助手

```r
paths <- delivery_sample_paths(sample_root)
# paths$raw_dir      -> …/数据文件
# paths$code_dir     -> …/代码文件
# paths$result_dir   -> …/代码文件/结果文件  （若无则回退 …/结果文件）
# paths$fig_dir / $tab_dir / $rep_dir
```

样例脚本顶部推荐：

```r
source(<DeliveryStandards>/规范_出图与命名_PlotNaming.R)
paths <- delivery_sample_paths(sample_root)
data_dir <- paths$raw_dir
fig_dir  <- paths$fig_dir
tab_dir  <- paths$tab_dir
rep_dir  <- paths$rep_dir
```

---

## 4. 与可视化冻结的关系

- **NetPharm (`bioinfo-network-pharmacology`) 视觉 recipe 仍为 frozen。**
- 本规范只允许：**移动/重命名路径、编号前缀、更新脚本路径指针**；**禁止**改配色、布局、网络算法参数或重绘交付图。
- 见 [`已跑通范式登记_FrozenParadigms.md`](../../统一可视化规范_VizStandards/文档_docs/已跑通范式登记_FrozenParadigms.md)。

---

## 5. 从旧布局迁移

**旧（废弃为默认）：**

```text
01_样例_sample/
  数据文件/   代码文件/   结果文件/{图片,数据,报告}
```

**新：**

```text
01_样例_sample/
  数据文件/                 # 保持 raw
  代码文件/
    01_run_….R
    结果文件/               # 整树从样例根移入
```

步骤摘要：

1. `git mv`（或等价）将 `结果文件/` → `代码文件/结果文件/`
2. 为脚本与主要图/表加 `NN_` 前缀
3. 更新 `run_*.R`、README、STATUS、技能说明中的硬编码路径
4. 改用 `delivery_sample_paths()`；保留旧路径回退一个发布周期
5. 在迁移清单中标记状态

参考实现：`03_药物计算_DrugDiscovery/网络药理学_NetworkPharmacology/01_样例_sample/`。
