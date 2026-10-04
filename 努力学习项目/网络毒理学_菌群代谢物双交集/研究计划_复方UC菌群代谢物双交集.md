# 研究计划：复方–肠道菌群代谢物–溃疡性结肠炎 双交集整合（网络毒理学可插拔）

> **状态：PENDING_USER_REVIEW**（口径同交付轨 B；确认后可冻结为该课题 SSOT）
> **对应交付：** [`../交付文件/`](../交付文件/)（UC 复方 12 味网络药理学，轨 B 客户归档）
> **思路来源：** 公众号「GutMGene 数据库网药」套路（菌群代谢物→STP/SEA 靶点→疾病交集→G-T-P-M 网络→对接）
> **制定：** 2026-10-04；医学口径遵循 `docs/项目规范_ProjectStandards.md` §2–§4（预测一律表述为「候选/提示」）

---

## 0. 研究问题与定位

**研究问题：** 该复方对 UC 的作用是否经「肠道菌群代谢物—宿主靶点」轴介导？哪些靶点、代谢物、通路构成**复方与菌群代谢物共同作用轴**？

**双交集设计（用户命题）：**

```text
F = 复方成分靶点并集（交付数据：数据/药物/药物靶点_全药.csv）
D = UC 疾病靶点（交付数据：数据/疾病/疾病靶点合并.csv，|D| = 1517）
M = 肠道菌群代谢物靶点（待建：gutMGene 代谢物 → SEA/STP 预测 → 并集）

I₁ = F ∩ D = 291（交付已算，数据/药物/药物疾病交集.csv）
I₂ = M ∩ D（待算）
C  = I₁ ∩ I₂ = F ∩ M ∩ D（核心：复方-代谢物-疾病三源共有靶点）
```

**网络毒理学插拔位（已拍板 Track A，2026-10-04；Phase 4 展开）：**

| Track | 含义 | 数据源 | 故事线 |
|-------|------|--------|--------|
| **A（推荐）** | **有害菌群代谢物拮抗**：把 M 拆成有益/有害两组，有害代谢物（LPS、TMAO、次级胆汁酸、对甲酚硫酸盐、吲哚硫酸盐等）靶点单独成集 | gutMGene/GMMAD2 + CTD/TTD 毒理靶点 | 复方通过共有靶点**拮抗菌群毒害代谢物**→「减毒」机制 |
| B | 方剂安全性评价：复方靶点 ∩ 肝毒/心毒靶点，双交集仿雷公藤范式 | TCMToxDB、CTD、TTD、ToxCast | 增效减毒、安全用药 |

Track A 与命题「双交集」同构且新颖；Track B 是独立第二篇的体量。

---

## 0.1 方法标准（2026-10-04 按已发表文献定稿，审稿人认可口径）

**标准 M-1 代谢物清单：** gutMGene v2.0 **全库代谢物不预筛**（文献量级 250–280 个）。有益/有害只作下游分层注释，不作入口过滤；分类锚定 [Nat Rev Gastro Hepatol 2019](https://www.nature.com/articles/s41575-019-0258-z) 三大类（SCFAs、胆汁酸、色氨酸代谢物）与 dysbiotic 清单（TMAO、H₂S、对甲酚硫酸盐、吲哚硫酸盐、次级胆汁酸 DCA/LCA，[IJMS 2023](https://www.mdpi.com/1422-0067/24/20/15256)）；毒性/成药性标注用 SwissADME + ADMETlab 2.0（肾纤维化 2026 同款）。Track A 有害组自全集拆出做对比。锚点论文：[Sci Rep 2026（278 个全取）](https://www.nature.com/articles/s41598-026-44114-2)、[Front Microbiol 2025（251 个全取）](https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2025.1617496/full)、[肾纤维化 2026（全库+末端无毒筛选）](https://exa.ai/library/publication/qtnh116tby6)。

**标准 M-2 靶点来源：** M = gutMGene 实证靶点（证据级 H）∪（**SEA ∩ STP 两工具一致**的预测靶点，证据级 M）；单工具命中（L）丢弃。锚点：[Sci Rep 2026「only overlapping targets identified by both were retained」](https://www.nature.com/articles/s41598-026-44114-2)、[Front Microbiol 2025（SEA 1773 ∩ STP 947 → 706）](https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2025.1617496/full)。gutMGene 版本引用 [NAR 2025;53(D1):D783-D788](https://pubmed.ncbi.nlm.nih.gov/39475181/)，记录访问日期。

---

## 1. 规模测算：双交集会不会「取空」？（用交付真实数据）

随机期望（以 D 为背景宇宙）：`E[|C|] = |I₁| · |I₂| / |D|`，|I₁|=291，|D|=1517。

| 情形 | \|M\|（代谢物靶点） | \|I₂\|=M∩D | E[\|C\|] 随机 | 预期实测（炎症通路收敛上调） | 判定 |
|------|-----|-----|-----|-----|------|
| 保守 | ~600 | ~200 | ≈ 38 | 50–80 | ✅ 可做 |
| 中位 | ~1200 | ~400 | ≈ 77 | 80–150 | ✅ 可做 |
| 宽松 | ~1800 | ~600 | ≈ 115 | 120–200 | ✅ 可做 |

参照：Sci Rep 2025 代谢物-UC 研究得 I₂=465；公众号肾纤维化案例双层交集后 47 个。**C 预期 40–150 量级，足够支撑 PPI/富集/对接，不会取空**；若实测 <30，走 §3 风险 2 的通路级兜底。结论：**能做**（统计显著性检验见 Phase 2）。

---

## 2. 可行性论证：先例与依据

### 2.1 两条腿各自有已发表先例

| 腿 | 先例 | 期刊/年份 | 关键结果 |
|----|------|-----------|----------|
| M∩D（菌群代谢物×UC） | [Gut microbiota metabolites against UC via network pharmacology + docking](https://www.nature.com/articles/s41598-025-10851-z) | Sci Rep, 2025 | gutMGene+SEA/STP 靶点 ∩ UC 靶点=465→46 核心；PPARG/IL6/AKT1；equol/butyrate |
| M∩D + 多组学 | [Microbial metabolite-associated host gene network in UC](https://link.springer.com/article/10.1007/s12026-026-09837-4) | Immunol Res, 2026 | MR+GutMGene+转录组交集=47 候选基因 |
| F∩D（复方×UC） | 本仓交付轨 B（291 靶点）；[大黄甘草蒲公英汤×UC](https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2025.1735021/full) | Front Immunol, 2025 | 305 交集靶点，NF-κB 主轴 |
| 复方+菌群+代谢物（实验线） | [半夏泻心汤 flora-metabolite-inflammation 轴](https://onlinelibrary.wiley.com/doi/pdfdirect/10.1002/bmc.70275)；[葛根芩连汤 16S+代谢组+网药](https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2026.1765637/full) | Biomed Chromatogr 2026；Front Immunol 2026 | 证明「复方-菌群代谢物-UC」故事被领域接受 |
| 网毒双交集成例 | [雷公藤：网药+网毒+对接+MD](https://cjournal.hep.com.cn/1673-842X/CN/10.13194/j.issn.1673-842X.2026.07.019) | 中华中医药, 2026 | 药效交集 256 / 毒性交集 151 双线并行 |

### 2.2 整合层（双交集）的新颖性与价值

- 单做 M∩D 已有 2025–2026 发文（5–6 分纯生信），但**「复方∩疾病∩菌群代谢物靶点」三层取交**在 UC 尚未见发表 → 有抢发窗口（公众号也明确提示红利期短）。
- 生物学假设明确：C 中的靶点是**复方与菌群代谢物共同调控的宿主节点**，直接产出可验证的「代谢物面板（丁酸/丙酸/equol/IPA…）× 核心靶点」实验假设，衔接半夏泻心汤等的菌群-代谢物实验先例。
- 比单纯网药多一层**内源性配体证据**，比单纯代谢组多一层**靶点机制**。

### 2.3 数据库与工具可行性（全部免费可抓）

| 环节 | 资源 | 备注 |
|------|------|------|
| 代谢物清单 | [gutMGene](http://bio-annotation.cn/gutmgene/)（NAR 2022）、[GMMAD2](http://gepa.org.cn/GMMAD2/)、VMH、HMDB | GMMAD2 有定量疾病-代谢物评分（Front Microbiol 2026） |
| 代谢物靶点 | gutMGene 实证 + SEA + SwissTargetPrediction（PubChem SMILES 输入） | 实证与预测分层报告 |
| 疾病靶点 | 交付已有（GeneCards/OMIM/DisGeNET/CTD 等多库 1517） | 直接复用，省一轮抓取 |
| 毒理靶点（Track A/B） | CTD、TTD、TCMToxDB、ToxCast | 网毒模块 |
| 网络/富集 | STRING、Cytoscape/cytoHubba、clusterProfiler | 同交付轨 B 流水线 |
| 对接 | AutoDock Vina / CB-Dock2，阈值 ≤ −20.9 kJ·mol⁻¹（约 −5 kcal/mol） | 同中文文献口径 |

---

## 3. 方法学风险登记与对策（严谨性核心）

| # | 风险 | 证据来源 | 对策（写进论文方法/局限） |
|---|------|----------|--------------------------|
| 1 | **枢纽偏倚/循环论证**：交集必然捞出 AKT1/IL6/TNF/TP53 等被研究过度的 hub，不代表疾病特异机制 | [Discover Chemistry 2026 综述](https://link.springer.com/article/10.1007/s44371-026-00567-y)（hub 循环性、数据库肿瘤偏倚）；[民族药网络分析偏倚路线图](https://pmc.ncbi.nlm.nih.gov/articles/PMC12962898/)（quercetin/PAINS、度中心性误用） | ①度保留置换检验（网络随机化后比较 C 的富集倍数）；②hub 剔除敏感性分析（去掉 top10% 度节点后结论是否保持）；③结肠组织表达过滤（GTEx/HPA 限定结肠表达基因）；④优先用模块（MCODE）而非纯度数排序 |
| 2 | **交集层层缩水、不稳**：三源交集对数据库选择/阈值敏感，可能取空或换库即变 | 同上；本设计 C = 三源交集 | ①预注册宇宙集与阈值（GeneCards score、STP probability）；②gutMGene vs GMMAD2 vs 合并的敏感性分析；③**通路级收敛兜底**：I₁ 与 I₂ 各自富集后比对通路（GSEA/KEGG 重叠），基因级 C<30 时以通路级为主结论 |
| 3 | **Venn 统计谬误**：把「A 显著 B 不显著」当特异集合是公认错误 | [Venn Diagrams May Indicate Erroneous Statistical Reasoning](https://pmc.ncbi.nlm.nih.gov/articles/PMC9046926/) | 只做**共同显著集合**的交集（本设计满足）；富集背景用 D 或全基因组注释集而非全基因；报超几何 p、FDR、Jaccard，不画无统计的韦恩讲故事 |
| 4 | **方向性缺失**：靶点交集不区分激活/抑制、代谢物有益/有害 | 领域共识；BXD/葛根芩连实验文献 | 代谢物分**有益/有害两组**分别分析（有害组即网毒 Track A）；文献标注效应方向；对接仅作结合提示，不写疗效/毒性结论（项目规范 §2） |
| 5 | **预测靶点不确定性**：SEA/STP 配体相似性预测假阳性高 | 同综述 | 证据分层 H（gutMGene/文献实证）\|M（多预测源一致）\|L（单源），核心结论只依赖 H+M；全程记录数据库访问日期与版本（项目规范 §3） |
| 6 | **疾病注释偏倚**：UC 靶点集本身富炎症大类 | — | 敏感性分析用「高置信 D 子集」重跑；差异不大部分如实写入局限 |
| 7 | **医学口径** | 项目规范 §2 | 全文「候选/提示」，不写疗效结论；观察性推断标注证据等级 |

**结论：设计在方法学上成立**——交集在这里的正确角色是**假设生成过滤器**而非验证；只要落实上表对策（置换检验 + 敏感性 + 分层证据 + 通路兜底），可达到主流 3–6 分期刊的审稿要求。

---

## 4. 分析流程（Phase 0–5）

每 Phase 结束以可检查条件为验收；产物落本目录 `数据/`、`图片/`、`报告/`（大图 gitignore 见 ADR 0003）。

### Phase 0 — 数据登记（0.5 天）
- [ ] 建 `DATA_SOURCE.md`：交付数据 provenance=REAL、gutMGene/GMMAD2/SEA/STP 访问日期与版本
- [ ] 复用交付 1517/291 靶点，核对 HGNC 标准化（项目规范 §3）

### Phase 1 — M 集构建（2–4 天）
- [ ] 按标准 M-1：gutMGene v2.0 全库代谢物（不预筛），PubChem SMILES
- [ ] 按标准 M-2：SEA + STP 预测，取两工具一致；实证(H) ∪ 一致预测(M)，单工具丢弃
- [ ] 代谢物注释：有益/有害分组（NRH 2019 分类 + SwissADME/ADMETlab 2.0 毒性标注，H/M/L）
- [ ] 标准化 HGNC/UniProt，输出 `M_代谢物靶点.csv`（含证据级列）

### Phase 2 — 双交集计算与统计（2–3 天）
- [ ] I₂ = M∩D；C = I₁∩I₂；输出三表 + 韦恩/UpSet
- [ ] 超几何检验 + FDR、Jaccard、**度保留置换检验**（1000 次）
- [ ] 敏感性：分库、分阈值、去 hub、结肠表达过滤，四套结果并列
- [ ] 预案触发器：|C|<30 → 切通路级收敛主线

### Phase 3 — 机制层（4–6 天）
- [ ] PPI + cytoHubba（MCC）+ MCODE 模块；GO/KEGG（背景集明确）
- [ ] **G-C-T-P-M 五层网络**（菌群-代谢物-成分-靶点-通路；公众号 G-T-P-M 的扩展层=复方，创新点 1）
- [ ] 反推核心代谢物（度+文献支持双标准）；核心靶点-代谢物配对表

### Phase 4 — 网络毒理学模块（2–4 天，已拍板 Track A）
- [ ] **Track A（主线）**：有害代谢物靶点集 ∩ I₁，析出「拮抗毒害代谢物」候选轴；对照有益代谢物组
- [ ] Track B：TCMToxDB/CTD/TTD 毒性靶点 ∩ F，肝毒/心毒双交集（雷公藤范式）
- [ ] 毒理结论仅写「提示潜在毒性/拮抗候选」，附证据等级

### Phase 5 — 验证层（已拍板档位：计算验证 + GEO + MR）
- [ ] 分子对接：C 核心对（代谢物×核心靶点，Vina/CB-Dock2，3 次独立重复，阈值 −20.9 kJ/mol）
- [ ] **GEO 转录组再验证（主线）**：UC 队列（GSE92415/GSE75214）中 C 的表达一致性 + 诊断效能（写全 AUC/CI）
- [ ] **MR 分析（主线）**：MiBioGen→FinnGen 菌群-UC 因果支持（复刻 Immunol Res 2026 框架）
- [ ] （加分）分子动力学 100 ns 抽查 top3 对
- [ ] （实验档备选）DSS 小鼠：16S + 靶向代谢组（SCFAs/胆汁酸/吲哚）+ qPCR/WB 验证核心对

---

## 5. 图表与统计报告清单

- Fig1 流程图（双交集逻辑）；Fig2 三源韦恩/UpSet + 置换检验条；Fig3 敏感性面板（4 套）
- Fig4 PPI+模块；Fig5 GO/KEGG；Fig6 G-C-T-P-M 五层网络；Fig7 核心对对接热图/构象
- 表：靶点清单（含证据级）、代谢物清单（含方向）、富集全表、对接全表
- 统计写全：检验名、效应量（富集倍数/odds ratio）、FDR 方法、置换次数（项目规范 §4）

## 6. 发表策略

- **创新点 1**：首次把复方网药与菌群代谢物靶点用「双交集=三源共有靶点」形式化整合于 UC；
- **创新点 2**：G-C-T-P-M 五层网络把内源性代谢物与复方成分放进同一网络；
- **创新点 3**（Track A）：有益/有害代谢物分组对比，给出「拮抗毒害代谢物」机制假设。
- 定位：纯生信可冲 4–6 分（Sci Rep/Int Immunopharmacol/J Ethnopharmacol 类）；加 GEO+MR 验证冲 5–7 分；加动物+代谢组实验对标半夏泻心汤/葛根芩连汤档位。
- 风险提示：GutMGene 纯生信红利期短（公众号自述），建议 **1–2 个月内出初稿**。

## 7. 里程碑

| 周 | 目标 |
|----|------|
| 1 | Phase 0–1：M 集建成（标准 M-1/M-2），DATA_SOURCE.md |
| 2 | Phase 2：双交集 + 统计 + 敏感性（Go/No-Go 决策点） |
| 3–4 | Phase 3–4：机制层 + 网毒模块（Track A） |
| 5–6 | Phase 5：对接 + GEO 再验证 |
| 7–8 | MR 分析 + 图表 + 初稿（验证档位已拍板 GEO+MR，总工期约 8 周） |

## 8. 参考文献（主要）

1. gutMGene: Cheng L, et al. Nucleic Acids Res. 2022;50(D1):D795-D800. [doi:10.1093/nar/gkab786](https://academic.oup.com/nar/article/50/D1/D795/6431812)
2. Gut microbiota metabolites against UC. Sci Rep. 2025. [s41598-025-10851-z](https://www.nature.com/articles/s41598-025-10851-z)
3. GMMAD v2.0. Front Microbiol. 2026;17:1770840. [doi:10.3389/fmicb.2026.1770840](https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2026.1770840/full)
4. GMMAD v1.0. BMC Genomics. 2023;24:482. [doi:10.1186/s12864-023-09599-5](https://bmcgenomics.biomedcentral.com/articles/10.1186/s12864-023-09599-5)
5. UC microbial metabolite host gene network. Immunol Res. 2026. [doi:10.1007/s12026-026-09837-4](https://link.springer.com/article/10.1007/s12026-026-09837-4)
6. 半夏泻心汤 flora-metabolite-inflammation 轴. Biomed Chromatogr. 2026. [doi:10.1002/bmc.70275](https://onlinelibrary.wiley.com/doi/pdfdirect/10.1002/bmc.70275)
7. 葛根芩连汤 16S+代谢组+网药. Front Immunol. 2026. [doi:10.3389/fimmu.2026.1765637](https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2026.1765637/full)
8. 雷公藤 网药+网毒+对接+MD. 中华中医药杂志. 2026. [链接](https://cjournal.hep.com.cn/1673-842X/CN/10.13194/j.issn.1673-842X.2026.07.019)
9. TCMToxDB. Database. 2019;baag019. [doi:10.1093/database/baag019](https://academic.oup.com/database/article/doi/10.1093/database/baag019/8654706)
10. Network pharmacology in the multi-omics era（hub 偏倚批评）. Discover Chemistry. 2026. [doi:10.1007/s44371-026-00567-y](https://link.springer.com/article/10.1007/s44371-026-00567-y)
11. Rethinking network analysis in ethnopharmacology. [PMC12962898](https://pmc.ncbi.nlm.nih.gov/articles/PMC12962898/)
12. Venn diagrams & erroneous statistical reasoning. Brief Bioinform. 2022. [PMC9046926](https://pmc.ncbi.nlm.nih.gov/articles/PMC9046926/)
