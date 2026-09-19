# 高分刊 Meta 图册与工作量（SSOT）

> **地位：** 医学 SRMA 轨出图与工作量对照；组学 NES 轨仍用 `01_样例_sample/`。  
> **依据（公开方法学 + 同题高分文）：**  
> - PRISMA 2020（BMJ 2021;372:n160）— 流程、合成结果的图表呈现  
> - Cochrane Style Manual — Figures：flow / forest / funnel / RoB graph·summary  
> - 同题示例：Versteijne 等 *J Clin Med* 2020（PRISMA 流程 + OS 森林图 + 切除/R0/淋巴结阴性 RR 森林图）；BJS Open 2025 `zrae172`（PRISMA + OS/PFS + 亚组 resectable vs BRPC）；PLOS ONE 2024 e0295983（PRISMA + R0 森林图 + 敏感性）  
> **进化：** 你确认新图种或工作量档后回写本文件；技能说明只留指针。

## 1. 高分文常见「图套」（相对本技能旧 Pilot）

| 常见图 | 高分文角色 | 本技能旧 Pilot | 目标 |
|--------|------------|----------------|------|
| PRISMA 流程图 | Fig1 几乎必有 | 无 | **必备**（Pilot 用诚实计数模板；L2 换真实检索数） |
| 主终点森林图 | Fig2 | 仅 OS | **必备** |
| 次要终点森林图 | Fig3+（切除率/R0/pN0/DFS） | 仅 DFS/RFS 示意 | **必备至少 1 张次要** |
| 敏感性（留一 / 换模型） | 正文或补充 | 有留一 | **必备** |
| 漏斗图 | 常作补充；**正式检验建议 k≥10** | 无 | **出图**；k&lt;10 图注声明不检验 |
| RoB 交通灯 / 条形汇总 | Fig4 或补充 | 无 | **必备**（Pilot 可标 single-rater） |
| 亚组森林图 | resectable vs BRPC 等 | 无 | **L1 有字段即出**；正式预注册亚组 |
| Baujat / 影响分析 | 高异质性时常见 | 无 | **I² 高时出** |
| 累积 meta / TSA | 更新型 SR 可选 | 无 | L3 可选 |

## 2. 工作量档（L1 → L3）

| 档 | 检索与筛选 | 偏倚与证据 | 出图最低集 | 可写结论 |
|----|------------|------------|------------|----------|
| **L1 Pilot** | 手动精选已知 RCT；**禁止**虚构库检索数 | 单人试填 RoB 2；无 GRADE | PRISMA 模板 + OS 森林 + 留一 + 次要森林 + funnel（声明）+ RoB 灯 + Baujat（若 I² 高）+ 亚组（若可分） | 仅工具链/方向提示 |
| **L2 投稿包** | 多库检索 + 双人筛选 + 排除清单 | 双人 RoB 2 + GRADE SoF | L1 全套换真实 PRISMA 数；漏斗仅当 k≥10 做 Egger | 关联/提示 + GRADE |
| **L3 完整** | 更新检索 + 灰文献 | GRADE 全结局 | + 累积/TSA/NMA（若方案要求） | 按方案 |

## 3. 交付图文件名（医学轨）

| 序 | stem（English 部分） | 说明 |
|----|----------------------|------|
| 01 | `PrismaFlow` | Study flow |
| 02 | `OsHr_Forest` | Primary OS forest |
| 03 | `OsLeaveOneOut_Forest` | Sensitivity |
| 04 | `DfsRfsHr_Forest` | Secondary survival |
| 05 | `OsFunnel` | Funnel（caption: k&lt;10 → visual only） |
| 06 | `OsBaujat` | Heterogeneity contribution |
| 07 | `RoB2_TrafficLight` | Study × domain |
| 08 | `OsSubgroup_Population_Forest` | Resectable / BRPC / mixed |

脚本：`医学SRMA出图_plotMedicalSrma.R`、`医学SRMA合并_poolMedicalSrma.R`；入口 `02_医学SRMA样例_*/代码文件/01_run_pilot.R`。

## 4. 完成判据

- [ ] 图册与上表一致（或 STATUS 写明缺图原因）  
- [ ] 每张图 DPI≥600、SVG+PNG、图面 English、PlotQA  
- [ ] 报告写明 L1/L2/L3；Pilot 不得写成完整 SR  
- [ ] 漏斗图在 k&lt;10 时**不做** Egger 阳性结论  
