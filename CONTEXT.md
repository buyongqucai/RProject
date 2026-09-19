# CONTEXT — RProject 领域词汇与边界

> 单上下文 SSOT（见 `docs/agents/领域文档_domain.md`）。新术语/边界决策落地即更新本文件；架构级决策另建 `docs/架构决策_ADR/`。  
> **进化：** 你的口头确认是技能的主更新源——满意则写入 SOP/FROZEN（单点），解冻口令后可改冻结项；入口文档只留指针，避免双源。

## 项目定位

个人生信技能库 + 仓内课题沙箱。核心资产：`生信分析技能_BioinformaticsSkills/`（技能 = 文档 + 脚本 + 样例）。正式交付金标在桌面独立目录（见边界）。

## 领域词汇

| 术语 | 含义 |
|------|------|
| 技能（skill） | `生信分析技能_BioinformaticsSkills/<类别>/<名称>/` 下的完整单元：`技能说明_*.md`（入口）+ `脚本_scripts/` + `01_样例_sample/` + `文档_docs/` |
| 技能说明 | 技能的必读入口；agent 动手前必须先 Read；只写决策边界与指针，细则在 SOP |
| SOP | `文档_docs/` 内流水线细则，技能内执行优先级最高（同技能内） |
| FROZEN | 已用户确认的交付/视觉范式；改前须用户说「解冻 / unfreeze」；**冻结≠永不进化**，解冻后按反馈改 SSOT 一处即可 |
| 金标 | 桌面正式交付目录样板（如 `痤疮_分子对接_序号文件夹/`） |
| 仓内课题沙箱 | 本仓根下课题目录（如 `努力学习项目/`）；脚本可入库，大图默认忽略（ADR 0003） |
| SSOT | 单一事实来源；同一含义只在一处维护 |
| 反馈闭环 | 用户确认满意 → 写入 SOP 或 FROZEN → 技能说明只改指针/摘要 → 下次反馈仍改同一 SSOT |
| `center_source` | 对接任务定心方法受控词（如 `cocrystal_meeko` / `autosite` / `FAIL`）；summary 强制列 |
| provenance | 样例/数据真实性：`REAL` / `TOY` / `BLOCKED`（契约桩用 BLOCKED，不用 toy） |
| detail / result | 对接：`detail-N`=口袋特写；`result_N`=big+detail 拼图；定稿规则见对接 SOP §7.3/§7.4 |
| intent-skill-router | `.cursor/skills/intent-skill-router`：未 @ 技能时按意图自动 Read 对应 `技能说明_*.md` |
| 工单 / frontier | `.scratch/<功能>/issues/NN-*.md`；只做 Blocked by 已完成且 `待Agent处理` 的单（见 `docs/agents/工单工作流_WorkOrder.md`） |
| 技能范式 | 新建/审计领域技能的勾选 SSOT：`docs/agents/技能范式清单_SkillParadigm.md` |
| 接缝（seam） | 测试的公开边界；TDD 前须与用户书面确认 |
| 红绿循环 | 先写失败测试（红）再最小实现（绿）；重构不属于循环 |
| 双轴审查 | code-review 的 Standards + Spec 两轴，分开报告不合并排名 |
| 契约桩（BLOCKED） | 无真实数据时的合规占位；provenance 必须标 BLOCKED |

## 边界

- 技能库脚本服务**所有**项目；项目专用脚本须在文件头注明。  
- **金标交付**在桌面独立成库；**仓内课题沙箱**可留在本仓（ADR [`0003-仓内课题沙箱与桌面金标交付.md`](docs/架构决策_ADR/0003-仓内课题沙箱与桌面金标交付.md)）。  
- 医学/生物学/学术口径见 `docs/项目规范_ProjectStandards.md`。  
- Agent 入口：`AGENTS.md`（短指针）+ 意图路由 `intent-skill-router`。
