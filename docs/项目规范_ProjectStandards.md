# 项目规范（Project Standards）

> 本文件是仓库级规范的**索引与增量**：只写本仓库特有的约定；出图/交付细则以指针落到 `生信分析技能_BioinformaticsSkills/00_基础_Foundation/` 的 SSOT，此处不复述。

## 1. 规范优先级（冲突时从高到低）

1. **医学/生物学/学术规范**（外部权威，§2–§4）
2. 领域技能已写明条款（技能说明 / SOP / FROZEN）
3. 统一交付规范 DeliveryStandards + 统一可视化规范 VizStandards
4. 本文件 §5–§6（写作与存放约定）
5. 通用习惯

## 2. 医学规范

- 涉及诊断/预后/治疗结论时，注明证据等级与局限；对接打分、计算预测一律表述为「提示/候选」，禁止写成疗效结论。
- 报告类研究遵循对应报告规范：RCT → CONSORT；观察性 → STROBE；预测模型 → TRIPOD；诊断准确性 → STARD。交付报告附方法学清单。
- 涉及人体数据：只用公开脱敏数据（GEO/TCGA 等），记录来源与使用条款。

## 3. 生物学规范

- 标识符用权威命名：基因 HGNC 符号、蛋白 UniProt、结构 PDB ID、化合物 PubChem CID；禁止编造 ID 或亲和力。
- 记录版本：参考基因组/注释版本、数据库下载日期、软件版本（Vina、PyMOL、R 包）。
- 分子对接盒子取活性位点/共晶配体中心；黄酮等刚性芳香体系禁止 `--gen3d`（详见对接 SOP §1）。

## 4. 学术规范

- 图面 English、DPI≥600、热图 SVG+PNG 双格式（细则 → VizStandards）。
- 数据可得性：样例/交付须附 `DATA_SOURCE.md`（来源、日期、provenance：REAL / TOY / BLOCKED）。
- 统计报告写全：检验名、效应量、多重校正方法、阈值；禁止只报 P 值。

## 5. 规范文件写法（面向 agent）

- **正向表述**：写目标行为；禁令只用于硬护栏，并配对正向目标。
- **主导词**：复用已定义术语（见 `CONTEXT.md`），同一概念一个名字。
- **SSOT**：同一规则只在一处维护；其它文档用指针引用，不复制条文。
- **完成判据**：每个步骤以可检查的条件结尾（「审计表与 STATUS 一致」而非「完成检查」）。
- **渐进披露**：入口文档保持短；细则放 `文档_docs/`，用指针连接。
- 写法细则参考 `writing-for-agents` 技能。

## 6. 项目文件存放

```text
E:\RProject\
  AGENTS.md                  # agent 入口（指针集，保持短）
  CONTEXT.md                 # 领域词汇 SSOT
  docs/
    agents/                  # 工具链配置（issue 跟踪/标签/领域文档）
    架构决策_ADR/            # NNNN-标题.md，决策落地即写
    项目规范_ProjectStandards.md   # 本文件
  .scratch/                  # 议题跟踪（本地 markdown，见 docs/agents/问题跟踪）
  生信分析技能_BioinformaticsSkills/   # 技能库（结构见各技能说明）
  校验/                      # 数据真实性核对
```

- 交付项目在桌面独立成库（如 `杨程茗分子对接/`），结构对齐各技能金标。
- 大文件/缓存（原始 SRA、表达矩阵、`.pse` 备份）不进 git；用 `.gitignore` + 项目内 `_raw/` 约定。
- 每个改动单元完成即提交；提交只含当次相关文件。
