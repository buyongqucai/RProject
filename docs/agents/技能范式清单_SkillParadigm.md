# 技能范式清单（Skill Paradigm）— SSOT

> **地位：** 新建 / 逐文件审计领域技能时的唯一勾选清单。  
> **写法杠杆：** `writing-for-agents`（短入口、SSOT、完成判据、渐进披露）。  
> **存放：** 技能根在 `生信分析技能_BioinformaticsSkills/<类>/<名>/`。  
> **进化：** 你确认新强制项后只改本文件；入口文档留指针。

## A. 目录与入口（每个技能根）

| ID | 检查项 | 完成判据 |
|----|--------|----------|
| A1 | `技能说明_*.md` 存在且为唯一入口 | agent 只须 Read 此文件即可知道下一步指针 |
| A2 | YAML `name` + `description`（含触发词） | description 能单独决定是否引用 |
| A3 | 入口 **≤ ~120 行**（细则已披露） | 长步骤在 `文档_docs/`，入口只有指针/三行摘要 |
| A4 | `脚本_scripts/`（或明确「无脚本/仅文档」） | README 或技能说明写明入口脚本名 |
| A5 | `01_样例_sample/` 或显式「样例待建」 | 有样例则符合 Delivery 目录树 |
| A6 | `文档_docs/` 或显式「无独立 SOP」 | FROZEN/SOP 不写在技能说明正文 |

## B. 技能说明八节（可裁剪，勿空壳标题）

与现网金标一致时保留：数据来源 → 数据规范 → 何时选用 → 方法 → 软件栈 → 可视化 → 解读 → 结合其它技能。  
缺节须在入口写一句「不适用：…」。

| ID | 检查项 | 完成判据 |
|----|--------|----------|
| B1 | 「何时选用 / 不适用」可判定 | 不会与兄弟技能抢触发 |
| B2 | 出图任务声明叠加 Viz + Delivery | 或写明「本技能无图」 |
| B3 | FROZEN/定稿用**正向**表述 | 「定稿路径 / 解冻前保持」；禁令配对正向目标 |
| B4 | 无双源：细则不复述 SOP 长文 | 改规则只改 `文档_docs/` 一处 |

## C. 样例与交付（有样例时强制）

| ID | 检查项 | 完成判据 |
|----|--------|----------|
| C1 | `数据文件/DATA_SOURCE.md` | 含 `data_provenance: REAL\|TOY\|BLOCKED` |
| C2 | 结果在 `代码文件/结果文件/` | 无根级散落 `结果文件/`（除非兼容回退已文档化） |
| C3 | 图/表命名中英对照 + 可选 `01_` 序 | 走 `delivery_stem` 或等价 |
| C4 | `STATUS.txt` / 报告标明 Pilot 局限 | 不把 TOY/BLOCKED 写成真实结论 |
| C5 | 出图 DPI≥600、图面 English、PlotQA | 领域未写明时用 VizStandards |

## D. 仓库级挂钩

| ID | 检查项 | 完成判据 |
|----|--------|----------|
| D1 | `intent-skill-router/catalog.md` 可解析到本技能 | 新增后跑 `refresh_catalog.py` 或手工补行 |
| D2 | 新术语写入 `CONTEXT.md`（若引入） | 无对话残留术语 |
| D3 | 架构边界 → ADR（若需要） | 不把边界只写在聊天里 |

## E. 逐文件审计怎么做

对每个技能 **单独一张工单**（`.scratch/技能逐文件审计_SkillFileAudit/issues/NN-audit-*.md`），按路径逐文件勾选（清单：`清单_checklist/<技能文件夹>.md`）：

1. **技能说明_*.md** — A1–A3, B1–B4  
2. **文档_docs/*** — SSOT 是否单点；FROZEN 指针是否有效  
3. **脚本_scripts/*** — 入口是否可运行；是否 source Viz/Delivery  
4. **01_样例_sample/** — C1–C5  
5. **其它**（README、STATUS）— 与入口无矛盾  

审计产出：`合规` / `小修` / `大修` / `骨架可接受`；小修可当场改；大修开子工单。  
看板：同目录 `BOARD.md`。

## F. 新建技能最小骨架

```text
<中文名>_<EnglishName>/
  技能说明_<中文名>_<EnglishName>.md
  脚本_scripts/
    说明_README.md
  01_样例_sample/
    README_样例目录.md
    数据文件/DATA_SOURCE.md
  文档_docs/
    （需要时再添 SOP；不要空文件刷屏）
```

创建后：勾本清单 A–D → 更新 catalog → 若有可跑样例则跑通 STATUS。
