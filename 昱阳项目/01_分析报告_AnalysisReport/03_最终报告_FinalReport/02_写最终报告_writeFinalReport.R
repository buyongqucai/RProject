# 昱阳项目最终 HTML 报告生成脚本
# 范式：统一交付规范_DeliveryStandards 文档_docs/样例报告范式_SampleReportParadigm.md
# 生成器：脚本_scripts/规范_报告生成_ReportBuild.R 的 write_delivery_report()（金标调用）
# 图册口径：按分析步骤全量对账（网药出图约束 §0.7 整册交付 + 交付命名与图册门禁 §4 对账）
# 用法：Rscript 02_写最终报告_writeFinalReport.R

source(
  "E:/RProject/生信分析技能_BioinformaticsSkills/00_基础_Foundation/统一交付规范_DeliveryStandards/脚本_scripts/规范_报告生成_ReportBuild.R",
  encoding = "UTF-8"
)

out <- "E:/RProject/昱阳项目/01_分析报告_AnalysisReport/03_最终报告_FinalReport/01_最终分析报告_FinalReport.html"
F <- "../../03_补充口径_Expanded_MultiSource"   # 相对报告文件
DEGFIG <- paste0(F, "/01_差异分析与药靶断点_DEGandGate/03_图片文件_Figures")
PPIFIG <- paste0(F, "/03_富集与PPI_EnrichPPI/03_图片文件_Figures")
DOCFIG <- paste0(F, "/04_分子对接_Docking/03_图片文件_Figures")
MDFIG  <- paste0(F, "/05_分子动力学_MD/03_图片文件_Figures/3HTB_JZ4_100ns")

caveats_html <- "
<ul class='compact'>
<li><b>口径红线</b>：全链条 <b>in silico</b>（无给药臂、非重复暴露湿实验）。禁止表述为「槲皮素治疗丙泊酚重复暴露小鼠」；正确表述为「新生期丙泊酚暴露发育神经毒性 × 槲皮素（计算预测干预靶点）」。</li>
<li><b>STATUS 与 provenance 分列</b>：报告状态 <code>PARTIAL</code>（MD 进行中快照，2026-10-14）；<code>data_provenance: REAL</code>（GEO/CTD/ChEMBL/BindingDB/STP 等来源可核对）。</li>
<li>基线口径（STP×DEG 交集仅 1）为诚实阴性对照，结论不基于基线外推。</li>
</ul>
"

lead_html <- "
<p class='lead'>GSE106799（新生小鼠丙泊酚暴露）DEG ∪ CTD(propofol) 疾病侧，与槲皮素分层药靶（实验∪预测）取交集 → GO/KEGG + STRING PPI → 分子对接 → 100 ns 分子动力学。图册按分析步骤全量对账（35 图，对应各模块 STATUS 图册）。</p>
"

kpis <- list(
  list(label = "DEG（主阈值）", value = "120", unit = "个", hint = "↑82 / ↓38"),
  list(label = "药∩病交集", value = "57", unit = "基因", hint = "双证据 9"),
  list(label = "STRING 互作边", value = "712", unit = "条", hint = "v12.5 · 57/57 映射"),
  list(label = "PPI 核心 Hub", value = "Akt1 42", unit = "", hint = "Il6/Jun/Stat3 41"),
  list(label = "对接最优结合能", value = "−8.7", unit = "kcal/mol", hint = "AKT1 / EGFR"),
  list(label = "MD 体系进度", value = "1 / 6", unit = "", hint = "3HTB demo 完成；5 课题体系队列中")
)

methods_html <- "
<ul class='compact'>
<li><b>差异与断点</b>：GEO GSE106799 主阈值 DEG（limma 口径）；CTD 化学–基因（propofol，MeSH D015742）；药靶分层并集 + 人鼠映射（断点结论见 02_阶段汇总_StageSummaries）。</li>
<li><b>富集</b>：R <code>clusterProfiler</code> + <code>org.Mm.eg.db</code> + KEGG(mmu)；ORA，BH 校正 p&lt;0.05、q&lt;0.2。</li>
<li><b>PPI</b>：STRING v12.5 API（species=10090，required_score=400）；原始响应快照登记于 01_初始数据_RawInitial。</li>
<li><b>出图</b>：网药 FROZEN 图序（<code>_shared_scripts/enrich_plot_netpharm.R</code>、<code>plot_ppi_netpharm.R</code>）；MD 图册按 <code>出图与交付约束_MdFigureStandards.md</code>（FROZEN 01–26）。</li>
<li><b>对接</b>：AutoDock-GPU 冻结路线（定心决策树 + <code>center_source</code> 登记 + PyMOL 三视图 + detail 手调断点 + <b>result 拼图</b>（SOP §7.3/§7.4 效力序，冻结交付物）+ 结合能热图（色标 vmax=0）。</li>
<li><b>MD</b>：GROMACS 2024.4，<code>运行复合物MD_runComplexMd.sh</code>（1 ns 分块 + 断点续跑 + watchdog 中止阈值：配体 RMSD &gt; 1.5 nm 等）。</li>
<li><b>本报告</b>：<code>source</code> 统一交付规范 <code>规范_报告生成_ReportBuild.R</code>（<code>write_delivery_report()</code> 金标调用）；交付与出图遵循 DeliveryStandards + VizStandards；图册按分析步骤全量对账（出图约束 §0.7 + 图册门禁 §4）。</li>
</ul>
"

data_html <- "
<p><b>data_provenance: REAL</b> —— 全部来源库可核对 accession / 参数；PPI 原始快照与派生表逐边对账一致。</p>
<table class='kv'>
<tr><th>GEO（疾病 DEG）</th><td>GSE106799（小鼠，丙泊酚暴露 vs 对照）；主阈值 DEG 120</td></tr>
<tr><th>CTD（疾病补充）</th><td>propofol 化学–基因；MeSH D015742；疾病并集 298（小鼠；与 DEG 零重叠、完全互补）</td></tr>
<tr><th>药物实验靶</th><td>ChEMBL CHEMBL50、BindingDB monomer 7460；174 个人源实验活性靶</td></tr>
<tr><th>药物预测靶</th><td>SwissTargetPrediction、PharmMapper、TargetNet、BATMAN-TCM；484 个（并集 471 小鼠映射）</td></tr>
<tr><th>配体</th><td>槲皮素 Quercetin；PubChem CID 5280343</td></tr>
<tr><th>STRING PPI</th><td>v12.5 API（species=10090，required_score=400）；原始快照 + DATA_SOURCE.md 已登记（2026-10-14 补）</td></tr>
<tr><th>受体结构（RCSB PDB）</th><td>AKT1 3CQW · EGFR 1M17 · GSK3B 1H8F · SRC 2SRC · HIF1A 4H6J（人源激酶域；缺原子经 pdbfixer 补全，登记于 MD 01_初始数据_RawInitial）</td></tr>
<tr><th>图册对账</th><td>阶段 A 3 图 + 断点韦恩 2 图 + 富集 5 图 + PPI 1 图 + 对接 7 图（含 result 拼图×5）+ MD 17 图 = 35 图，全量对应各模块 STATUS 图册</td></tr>
<tr><th>交付物索引</th><td>03_富集与PPI_EnrichPPI/ · 04_分子对接_Docking/ · 05_分子动力学_MD/ · 02_阶段汇总_StageSummaries/（均在昱阳项目下）</td></tr>
</table>
"

audit_fields <- c(
  "技能" = "网络药理学 + 分子对接 + 分子动力学（昱阳项目）",
  "审计阶段" = "DEG → 药靶断点 → 富集/PPI → 对接 → MD（补充口径主线）",
  "DEG（主阈值）" = "120（↑82 / ↓38）",
  "疾病并集（小鼠）" = "298（DEG 120 ∪ CTD 178；两来源零重叠、完全互补）",
  "药靶并集（小鼠）" = "471（实验 174 ∪ 预测 484）",
  "药∩病交集" = "57（实验∩病 12；双证据 9）",
  "STRING 互作边 / 映射" = "712 条 / 57 基因（基线口径 8 条 / 50 基因，对照）",
  "对接" = "5 靶 × 槲皮素；结合能 −7.6 ~ −8.7 kcal/mol；result 拼图 5/5 完成",
  "MD 体系" = "6（3HTB+JZ4 demo 100 ns 图册 18 图完成；AKT1 续跑 ~7.6 ns；GSK3B/SRC/HIF1A 排队；EGFR 换口袋重对接待决）",
  "图册对账" = "35 图 = 阶段A 3 + 韦恩 2 + 富集 5 + PPI 1 + 对接 7 + MD 17（全量，无缺步）",
  "数据来源标注" = "REAL",
  "Accession / PDB" = "GSE106799 · D015742 · CHEMBL50 · BindingDB 7460 · PubChem 5280343 · PDB 1M17/3CQW/1H8F/2SRC/4H6J",
  "已 source 脚本" = "规范_报告生成_ReportBuild.R；_shared_scripts/enrich_plot_netpharm.R、plot_ppi_netpharm.R",
  "审计时间" = format(Sys.time(), "%Y-%m-%d %H:%M")
)

figure_sections <- list(
  list(
    id = "deg", title = "一、差异表达与质量控制（阶段 A）",
    intro = "GEO GSE106799 主阈值 DEG 120（↑82 / ↓38）：样本质控、差异全景与差异基因表达模式。",
    layout = "grid3",
    items = list(
      list(title = "PCA 质控",
           src = paste0(DEGFIG, "/01_PCA质控_PcaQc.png"),
           caption = "PCA of samples (quality control).",
           note = "处理组与对照组分离、组内聚拢。"),
      list(title = "火山图",
           src = paste0(DEGFIG, "/02_火山图_Volcano.png"),
           caption = "Volcano plot: log2FC vs −log10(p)."),
      list(title = "差异基因热图",
           src = paste0(DEGFIG, "/03_差异基因热图_DegHeatmap.png"),
           caption = "Heatmap of DEGs (z-score by gene).",
           note = "主阈值 DEG 120：↑82 / ↓38。")
    )
  ),
  list(
    id = "gate", title = "二、疾病/药物基因集与数量断点",
    intro = "疾病侧 = DEG ∪ CTD；药物侧 = 实验∪预测分层药靶。交集 57 基因为 ORA/PPI/对接的输入。",
    layout = "grid2",
    items = list(
      list(title = "疾病基因集合：DEG vs CTD",
           src = paste0(PPIFIG, "/04_韦恩图_Disease_DEG_vs_CTD_Venn.png"),
           caption = "Disease gene sets: DEG vs CTD (mouse).",
           note = "重要特征：两来源<b>零重叠、完全互补</b>（DEG 120 = 表达响应基因；CTD 178 = 文献化学–基因注释基因），并集 298 作疾病侧。零重叠同时意味着疾病侧对来源选择敏感（见解读）。"),
      list(title = "药∩病韦恩图",
           src = paste0(PPIFIG, "/05_韦恩图_DrugDisease_Venn.png"),
           caption = "Drug targets vs disease genes.",
           note = "交集 57：实验∩病 12、双证据（实验+预测）9。基线口径（STP×DEG）交集仅 1（Alox15），为阴性对照。")
    )
  ),
  list(
    id = "enrich", title = "三、GO/KEGG 富集（ORA on 交集 57 基因）",
    intro = "BH 校正 p<0.05；主题集中于神经元凋亡调控与缺氧应答，与发育神经毒性表型方向一致。",
    layout = "grid2",
    items = list(
      list(title = "GO BP/CC/MF 气泡图",
           src = paste0(PPIFIG, "/01_气泡图_GO_BPCCMF_Bubble.png"),
           caption = "GO enrichment (top terms per ontology).",
           note = "Top BP：regulation of neuron apoptotic process（21 基因，p≈2.0×10⁻²⁵）；response to hypoxia（20 基因，p≈9.8×10⁻²⁴）。"),
      list(title = "GO BP/CC/MF 柱状图",
           src = paste0(PPIFIG, "/02_柱状图_GO_BPCCMF_Bar.png"),
           caption = "GO enrichment (bar view)."),
      list(title = "KEGG 棒棒糖图",
           src = paste0(PPIFIG, "/03_棒棒糖图_KEGG_Pathways_Lollipop.png"),
           caption = "KEGG pathways (top by gene count).",
           note = "Apoptosis（17 基因，p=6.0×10⁻²⁰）；EGFR tyrosine kinase inhibitor resistance（16 基因，p=2.9×10⁻²²，由共享激酶骨架基因驱动）。"),
      list(title = "KEGG 柱状图",
           src = paste0(PPIFIG, "/07_柱状图_KEGG_Pathways_Bar.png"),
           caption = "KEGG pathways (bar view)."),
      list(title = "KEGG 圈图", wide = TRUE,
           src = paste0(PPIFIG, "/08_圈图_KEGG_Circos.png"),
           caption = "KEGG circos: genes × pathways.",
           note = "疾病类条目（病毒感染/肿瘤）解读时聚焦机制通路（Apoptosis 等）。")
    )
  ),
  list(
    id = "ppi", title = "四、STRING PPI 网络与核心 Hub",
    intro = "57 基因 → 712 条互作边（STRING v12.5，required_score=400）；同心 Degree 布局（网药 FROZEN）。",
    layout = "stack",
    items = list(
      list(title = "STRING PPI Degree 网络", wide = TRUE,
           src = paste0(PPIFIG, "/13_网络图_StringPPI_Degree_Network.png"),
           caption = "STRING PPI network (concentric, node size = degree).",
           note = "Hub Top：Akt1 42、Il6 41、Jun 41、Stat3 41、Mtor 40、Tnf 40、Casp3/Fos/Hif1a/Mapk3 39。原始 API 快照登记于该模块 01_初始数据_RawInitial（2026-10-14 补，与派生表逐边对账一致）。")
    )
  ),
  list(
    id = "dock", title = "五、分子对接（核心靶 × 槲皮素 · 含 result 拼图）",
    intro = "AutoDock-GPU 冻结路线；结合能 −7.6 ~ −8.7 kcal/mol。每靶交付 PyMOL 三视图（big/surface/detail）与 result 拼图（SOP §7.4 效力序定稿），下方为 result 拼图 ×5 与结合能总览图。",
    layout = "grid3",
    items = list(
      list(title = "result 拼图 — AKT1（3CQW，−8.7）",
           src = paste0(DOCFIG, "/01_Akt1/图片/result_01.png"),
           caption = "Result panel (big + surface + detail) — AKT1.",
           note = "单图 big-01/surface-01/detail-01.png 同目录。"),
      list(title = "result 拼图 — EGFR（1M17，−8.7）",
           src = paste0(DOCFIG, "/02_Egfr/图片/result_02.png"),
           caption = "Result panel (big + surface + detail) — EGFR."),
      list(title = "result 拼图 — SRC（2SRC，−8.1）",
           src = paste0(DOCFIG, "/03_Src/图片/result_03.png"),
           caption = "Result panel (big + surface + detail) — SRC."),
      list(title = "result 拼图 — GSK3B（1H8F，−8.3）",
           src = paste0(DOCFIG, "/04_Gsk3b/图片/result_04.png"),
           caption = "Result panel (big + surface + detail) — GSK3B."),
      list(title = "result 拼图 — HIF1A（4H6J，−7.6）",
           src = paste0(DOCFIG, "/05_Hif1a/图片/result_05.png"),
           caption = "Result panel (big + surface + detail) — HIF1A."),
      list(title = "结合能矩阵热图", wide = TRUE,
           src = paste0(DOCFIG, "/矩阵_结合能热图_DockingAffinityHeatmap.png"),
           caption = "Docking affinity matrix (kcal/mol; color scale vmax = 0, FROZEN).",
           note = "数值精确至 0.1 kcal/mol；色标仅非正值（冻结条款）。"),
      list(title = "一对多对接结合能圆环图", wide = TRUE,
           src = paste0(DOCFIG, "/圆环_一对多对接结合能_DockingRingHeatmap.png"),
           caption = "Ring heatmap: ligand × targets.",
           note = "结合能明细表：04_分子对接_Docking/01_数据文件_Data/02_结果数据_ResultTables/矩阵_结合能_DockingAffinityMatrix.csv。")
    )
  ),
  list(
    id = "md1", title = "六、分子动力学 100 ns（一）构象稳定性",
    intro = "demo 体系 3HTB+JZ4 图册（非课题配体，验证流水线；不外推为课题体系结论）。课题体系 5 个进行中：AKT1 断点续跑 ~7.6 ns、GSK3B/SRC/HIF1A 排队、EGFR 换口袋重对接待决。",
    layout = "grid3",
    items = list(
      list(title = "骨架 RMSD",
           src = paste0(MDFIG, "/01_骨架RMSD图/RmsdBackbone.png"),
           caption = "Backbone RMSD vs t = 0."),
      list(title = "三线 RMSD",
           src = paste0(MDFIG, "/02_三线RMSD图/RmsdProteinLigandComplex.png"),
           caption = "RMSD: protein / ligand / complex."),
      list(title = "残基 RMSF",
           src = paste0(MDFIG, "/03_残基RMSF图/RmsfCalpha.png"),
           caption = "Cα RMSF per residue."),
      list(title = "蛋白–配体氢键数",
           src = paste0(MDFIG, "/04_氢键数图/HbondNum.png"),
           caption = "Protein–ligand hydrogen bonds over time."),
      list(title = "回旋半径",
           src = paste0(MDFIG, "/05_回旋半径图/RadiusGyration.png"),
           caption = "Radius of gyration over time."),
      list(title = "质心距离",
           src = paste0(MDFIG, "/07_质心距离图/ComDistance.png"),
           caption = "Protein–ligand COM distance.")
    )
  ),
  list(
    id = "md2", title = "七、分子动力学（二）能量与热力学环境",
    intro = "NVT/NPT 平衡与生产段能量监控（GROMACS 2024.4）。",
    layout = "grid3",
    items = list(
      list(title = "NVT 温度",
           src = paste0(MDFIG, "/08_NVT温度图/NvtTemperature.png"),
           caption = "Temperature during NVT."),
      list(title = "NPT 温度",
           src = paste0(MDFIG, "/09_NPT温度图/NptTemperature.png"),
           caption = "Temperature during NPT."),
      list(title = "NPT 压力",
           src = paste0(MDFIG, "/10_NPT压力图/NptPressure.png"),
           caption = "Pressure during NPT."),
      list(title = "NPT 密度",
           src = paste0(MDFIG, "/11_NPT密度图/NptDensity.png"),
           caption = "Density during NPT."),
      list(title = "生产段势能",
           src = paste0(MDFIG, "/12_生产势能图/MdPotential.png"),
           caption = "Potential energy during production.")
    )
  ),
  list(
    id = "md3", title = "八、分子动力学（三）自由能形貌",
    intro = "FEL 多坐标视角（MdFigureStandards FROZEN 图序）。",
    layout = "grid3",
    items = list(
      list(title = "FEL（RMSD × Rg）",
           src = paste0(MDFIG, "/13_自由能形貌图/FreeEnergyLandscape.png"),
           caption = "Free energy landscape (RMSD × Rg)."),
      list(title = "FEL（RMSD × 质心距离）",
           src = paste0(MDFIG, "/14_自由能形貌RMSDx质心图/FreeEnergyRmsdCom.png"),
           caption = "FEL (RMSD × COM distance)."),
      list(title = "FEL（配体–蛋白 RMSD）",
           src = paste0(MDFIG, "/16_自由能形貌配体蛋白RMSD图/FreeEnergyLigandProteinRmsd.png"),
           caption = "FEL (ligand–protein RMSD)."),
      list(title = "FEL 3D（RMSD × Rg）",
           src = paste0(MDFIG, "/17_自由能形貌3D图/FreeEnergyLandscape3D.png"),
           caption = "3D FEL (RMSD × Rg)."),
      list(title = "FEL 3D（RMSD × 质心距离）",
           src = paste0(MDFIG, "/18_自由能形貌3D_RMSDx质心图/FreeEnergyRmsdCom3D.png"),
           caption = "3D FEL (RMSD × COM distance)."),
      list(title = "FEL 3D（配体–蛋白 RMSD）",
           src = paste0(MDFIG, "/20_自由能形貌3D_配体蛋白RMSD图/FreeEnergyLigandProteinRmsd3D.png"),
           caption = "3D FEL (ligand–protein RMSD).",
           note = "demo 图册 18 图全量；课题体系完成后按同一 FROZEN 图序替换本节并更新状态 pill。")
    )
  )
)

interp_html <- "
<h3>结论（补充口径 · 计算预测）</h3>
<ul class='compact'>
<li>槲皮素药靶与丙泊酚暴露相关疾病基因交集 <b>57</b>（实验∩病 12、双证据 9），富集主题为 <b>神经元凋亡调控</b> 与 <b>缺氧应答</b>（GO BP top：regulation of neuron apoptotic process，21 基因，p≈2.0×10⁻²⁵；KEGG：Apoptosis，17 基因，p=6.0×10⁻²⁰）。</li>
<li>PPI 核心模块：Akt1–Stat3–Mtor–Il6/Tnf–Jun/Fos–Casp3–Hif1a（degree 39–42），覆盖 PI3K-Akt-mTOR、MAPK、炎症、凋亡与缺氧骨架，与富集主题互相印证。</li>
<li>对接支持潜在结合假说：AKT1/EGFR −8.7、GSK3B −8.3、SRC −8.1、HIF1A −7.6 kcal/mol（result 拼图见 §五）。</li>
</ul>
<h3>没证明什么（必读）</h3>
<ul class='compact'>
<li><b>未证明</b>槲皮素对丙泊酚暴露具有任何治疗/保护效力——无给药臂、无湿实验，全部为计算预测，不构成诊疗建议。</li>
<li><b>未证明</b>结合能等于功效；<b>未证明</b> hub 度数等于因果（STRING 有研究热度偏倚；KEGG 疾病类条目由共享凋亡–MAPK 骨架基因驱动）。</li>
<li><b>疾病侧零重叠的双刃性</b>：DEG 与 CTD 基因集完全互补（0 交集）说明两个来源覆盖不同基因空间，但也意味着疾病侧构成对来源选择敏感；更换疾病侧来源可能显著改变交集与富集结果。</li>
<li><b>MD 尚未完成</b>（快照 2026-10-14）：EGFR 口袋内两姿态均飞散，换口袋重对接前不解读其 MD；AKT1 续跑中（~7.6 ns，配体 RMSD 0.20 nm）；GSK3B/SRC/HIF1A 排队。</li>
<li>基线口径（STP×DEG 交集仅 1：Alox15；GO/KEGG 无显著条目）为<b>诚实阴性对照</b>，任何结论不得基于基线外推。</li>
</ul>
"

write_delivery_report(
  skill_en = "NetworkPharmacology + MolecularDocking + MolecularDynamics",
  skill_folder = "昱阳项目",
  status = "PARTIAL",
  data_source_html = data_html,
  audit_summary_html = "",
  sourced_scripts = methods_html,
  figures = NULL,
  interpretation = interp_html,
  out_path = out,
  version = "v2",
  kpis = kpis,
  figure_sections = figure_sections,
  methods_html = methods_html,
  caveats_html = caveats_html,
  subtitle = "主口径：03_补充口径_Expanded_MultiSource（实验∪预测 × DEG∪CTD）；对照：02_未补充口径_Baseline_STPonly",
  lead_html = lead_html,
  report_title = "昱阳项目最终分析报告 — 新生期丙泊酚暴露发育神经毒性 × 槲皮素（计算预测）",
  audit_fields = audit_fields,
  toc = TRUE
)

message("report written: ", out)
