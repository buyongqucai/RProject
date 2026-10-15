# 清风项目 · 数据来源总览（含可达性实测）

> **data_provenance: REAL**（目标）；未获取前登记为 `PENDING`，契约桩标 `BLOCKED`。  
> 实测时间：2026-10-14（curl，10–12s 超时，桌面网络）；档位定义见网药 SSOT《数据库分类与流水线》§1.4 与网毒《数据库可抓取登记》。

## 1. 连通性实测矩阵（2026-10-14）

### 疾病六库（IPF 靶点）

| # | 数据库 | 实测 | 档位 | 获取策略 |
|---|--------|------|------|----------|
| 1 | GeneCards | 403（反爬，浏览器正常） | MANUAL | 注册后网页导出；或前端接口复现（见 §3） |
| 2 | TTD | ✅ 200 | MANUAL | 网页检索/下载页导出 |
| 3 | DrugBank | 403（登录墙） | MANUAL/KEY | 学术许可登录后下载（靶点表） |
| 4 | OMIM | 403（API key） | KEY | 申请 API key 或网页导出 |
| 5 | CTD | ⚠️ 302（下载页可达） | **AUTO_BULK** | `ctdbase.org/downloads/` bulk CSV（化学-基因-疾病） |
| 6 | DisGeNET | ✅ 200 | MANUAL/KEY | 学术注册 → API/网页导出（注意许可，勿二次分发） |

### 药物/成分–靶点库（9 味药）

| 库 | 实测 | 档位 | 获取策略 |
|----|------|------|----------|
| TCMSP | ✅ 200 | MANUAL | 网页检索（OB≥30%, DL≥0.18）+ 前端接口复现批量抓 |
| BATMAN-TCM | ✅ 200 | MANUAL | **仅 known/curated** 靶点；网页查询 |
| ETCM | ✅ 200 | MANUAL | 网页/下载补充 |
| HERB 2.0 | ❌ DNS 解析失败（herb.big.ac.cn） | MANUAL | 换镜像/浏览器试；失败登记 BLOCKED，成分→STP 路线不受阻 |
| TCMBank | ⚠️ 证书过期（-k 后 200） | MANUAL | 浏览器可过；可取成分再预测 |

### 预测 / 通路 / PPI

| 库 | 实测 | 档位 | 获取策略 |
|----|------|------|----------|
| SwissTargetPrediction | ✅ 200 | AUTO（表单，可达时） | 批量提交 SMILES（每药成分），剔除 Probability=0 |
| PharmMapper | ✅ 200 | MANUAL（作业制） | 提交作业收结果 |
| TargetNet | ❌ DNS 解析失败（scbdd.cn） | MANUAL | 登记 BLOCKED，等恢复再补 |
| STRING | ✅ 200（API） | **AUTO_API** | `string-db.org/api`（species=10090/9606），raw 响应落盘 |
| KEGG | ✅ 200（REST） | **AUTO_API** | `rest.kegg.jp`（hsa 通路 + 富集） |
| PubChem | ✅ 200（PUG-REST） | **AUTO_API** | 成分 CID/SMILES 核对（本方活性成分） |

**小结：** 12/16 官方可达；GeneCards/DrugBank/OMIM 是登录/反爬墙（注册即可用，业界常规）；HERB/TargetNet 当前 DNS 故障（非我方阻断）。**结论：数据拿得到**，无需为「触达」担忧；差别只在自动 vs 手动。

## 2. 三类库划分（不得混写）

| 类 | 库 |
|----|-----|
| 疾病基因 | GeneCards、TTD、DrugBank、OMIM、CTD、DisGeNET |
| 药物/成分–靶点 | TCMSP、BATMAN-TCM、ETCM、HERB、TCMBank、SwissTargetPrediction |
| 通路/PPI | KEGG、STRING |

## 3. 前端接口复现策略（用户问询 · 约束版）

对无 API 的网页库（TCMSP、BATMAN、GeneCards 检索页等），浏览器 DevTools 抓页面自身调用的 JSON 接口再脚本化重放，**用于科学研究是可行且惯例做法**，约束：

1. **官方渠道优先**：API/bulk > 注册导出 > 接口复现 > 人工导出（回退链）。
2. **限速礼貌**：单线程、请求间隔 ≥ 2–5 s、带常规 UA、失败即停；不并发压站。
3. **缓存原始响应**：JSON/HTML 原样落 `01_初始数据_RawInitial/{来源库}_*/`，附 endpoint + 参数 + 时间戳。
4. **许可边界**：不绕付费墙/验证码；库方导出**不二次分发**（尤其 DisGeNET/DrugBank/GeneCards 条款）；引用原文献与数据库版本。
5. **登记义务**：每库写 `DATA_SOURCE.md`（endpoint/参数/获取时间/档位），审计表可核对。

> 说明：以上为科研数据采集的合规惯例；具体库的 ToS 若有更新以库方为准，拿不准的库（DisGeNET 等）走注册通道。

## 4. 关键 ID

- 疾病：Idiopathic pulmonary fibrosis（MeSH D054990；英文病名六库检索）
- 组方：水蛭、旋覆花、川芎（原词「川穹」）、桃仁、浙贝母、蜜麻黄（原词「密麻黄」）、紫苏子、黄芪、甘草
- 物种口径：疾病人源（hsa）；成分靶点按库给定（人源为主，小鼠映射按需）

## 5. 状态

| 项 | 状态 |
|----|------|
| 项目建立 | DONE（2026-10-14） |
| 连通性探测 | DONE（2026-10-14，§1 矩阵） |
| 实取轮·KEGG 疾病条目 | DONE（H01299，6 基因关联落 raw，§6.1） |
| 实取轮·TCMSP 全目录 | DONE（药材 502 / 成分 13,729 / 靶点 3,339 落 raw，§6.2） |
| 实取轮·TCMSP 8 药成分 | DONE（1,183 成分，207 个过 OB≥30/DL≥0.18，§6.2） |
| 实取轮·TCMSP 成分→靶点 | DONE（182 成分钻取 0 失败：2,454 对 / 290 去重靶点，§6.2） |
| 实取轮·PubChem 属性 | DONE（黄芪甲苷/芒柄花素/毛蕊异黄酮 3 条落 raw） |
| 疾病六库导出 | PARTIAL（KEGG✅；CTD 人机验证→浏览器通道；GeneCards/OMIM/DrugBank/DisGeNET 手工档） |
| 成分瀑布（BATMAN→ETCM→HERB→STP） | PARTIAL（TCMSP 层完成；水蛭无 TCMSP 记录 → BATMAN 2.0 混杂条目人工截取水蛭专属 known 靶点 6 边已落，§7；ETCM/HERB/STP 层待做） |
| 交集/网络/富集/PPI | PENDING（STRING v12.5 已验活） |
| 对接/MD | 预留（待核心靶确认） |

## 6. 实取轮记录（2026-10-14）

### 6.1 疾病侧

- **KEGG REST（AUTO ✅）**：`find/disease/idiopathic%20pulmonary%20fibrosis` → **H01299**；`get/disease:H01299`（74 行条目）、`link/hsa/disease:H01299`（6 条基因关联：hsa:7015 TERT、hsa:7012 TERC 等）已落
  `01_疾病靶点_DiseaseTargets/01_数据文件_Data/01_初始数据_RawInitial/KEGG_*`。
- **CTD（🔒 人机验证）**：`ctdbase.org/downloads/*` 与查询接口均返回 2,774B 拦截页「To continue, we need to verify you are a human」。按 §3.4 不绕验证码 → **浏览器人工通道**（人工过验证后导出/下载，落 raw 注明来源）。

### 6.2 TCMSP 前端接口还原（三级钻取，等同前端监听复现）

站点：`https://old.tcmsp-e.com`（新版 `tcmsp-e.com` 为壳，old 站承载检索）。表单 token 为常量 `5c0be79851097fb5891270fbdac7e4dc`（多次会话实测一致）。响应数据内嵌 Kendo grid：`data: [...]` / `var tar = [...]`。

| 级 | endpoint | 入参 | 返回 |
|----|----------|------|------|
| 0 目录 | `browse.php?qc=herbs\|ingredients\|targets\|diseases` | — | 全量目录 JSON（502 / 13,729 / 3,339 / 867 行） |
| 1 药材 | `tcmspsearch.php?q=<中文名>&qs=herb_all_name&token=` | 药材中文名 | 药材记录（cn/pinyin/拉丁名） |
| 2 成分 | `tcmspsearch.php?qr=<herb_en_name>&qsr=herb_en_name&token=` | 拉丁名 | 成分表（MOL_ID、molecule_ID、OB、DL 全 ADME） |
| 3 靶点 | `molecule.php?qn=<molecule_ID>` | 分子数字 ID | `var tar` 靶点数组（target_ID、target_name、drugbank_ID、SVM/RF score） |

**9 药 TCMSP 口径与实取清单**（raw：`02_药物靶点_DrugTargets/.../01_初始数据_RawInitial/01_TCMSP_成分靶点_CompoundTargets/TCMSP_*`）：

| 药材 | TCMSP 拉丁名 | 成分数 | 过 OB≥30/DL≥0.18 | 备注 |
|------|--------------|--------|------------------|------|
| 旋覆花 | Inulae Flos | 53 | 19 | |
| 川芎 | Chuanxiong Rhizoma | 189 | 7 | |
| 桃仁 | Persicae Semen | 66 | 23 | |
| 浙贝母 | Fritillariae Thunbrgii Bulbus | 17 | 7 | |
| 蜜麻黄 | Ephedra Herba | 363 | 23 | 炮制品，TCMSP 以**麻黄**条目承载（映射登记） |
| 紫苏子 | Perillae Fructus | 128 | 16 | |
| 黄芪 | Hedysarum Multijugum Maxim. | 87 | 20 | TCMSP 口径拉丁名 |
| 甘草 | licorice | 280 | 92 | |
| 水蛭 | — | 0 | 0 | **TCMSP/ETCM/HERB 全无覆盖**（2026-10-14 终验，见 §6.3）；BATMAN 2.0 仅存同音混条目（水蛭/水栀子），已人工截取水蛭专属成分 → **§7** |
| 合计 | | 1,183 | 207 | 去重后批量→靶点进行中 |

- **PubChem PUG-REST（AUTO ✅）**：黄芪甲苷（CID 13943297）/ 芒柄花素（CID 5280378）/ 毛蕊异黄酮（CID 5280448）属性 JSON 落 raw（对接配体 SMILES 来源）。
- **STRING（AUTO ✅）**：v12.5 验活（`stable_address=version-12-5.string-db.org`），PPI 阶段用。

## 7. BATMAN-TCM 2.0 实取：水蛭（2026-10-14）

**端点**（SPA `#/search`，官方 API 选项卡文档 + chunk 逆向 + 实测一致）：`POST /api/queryTarget`（type=caoyao）→ 轮询 `GET /api/queryTargetResult`（status 500=查无此药）→ 作业包 `http://batman2.cloudna.cn/downloadApiFile/data/query_TARGET_result/{jobId}/Results of target protein.zip`。细则已入技能 SSOT（网络药理学 CompoundTargetSOP §9）。

**检索名教训（写入技能 §8，用户确认）**：拼音 `shui zhi` 命中的是**水栀子**（Gardenia jasminoides var. grandiflora）同音混条目——45 成分含 12 个栀子属专属（藏红花素/西红花酸/京尼平/栀子苷等），仅 4 个水蛭专属；`hirudo / hirudo nipponica / whitmania pigra / leech / 水蛭` 均 NO MATCH。今后非 TCMSP 库只用拉丁/英文名并核对返回 Latin 字段。

**水蛭截取交付**（混杂条目人工归属，判据与排除清单入审计表）：

| 文件（`02_结果数据_ResultTables/`） | 内容 |
|---|---|
| `BATMAN_水蛭专属成分_known靶点_ShuizhiKnownTargets.csv` | **主交付** 6 边：Heparin→SERPINC1(TTD)；Fragmin→SELL/F2/HPSE/SELP(HIT)、F10(TTD) |
| `BATMAN_水蛭_known靶点基因列表_ShuizhiKnownGeneList.csv` | 6 基因：F2、F10、SERPINC1、SELL、SELP、HPSE（凝血/肝素生物学，符合水蛭"破血"） |
| `BATMAN_水蛭专属成分_预测靶点参考_ShuizhiPredictedRef.csv` | 非交付参考 71 边（数字 confidence，含 Hirudin→F2 0.89——水蛭素经典靶点但 BATMAN 未标 known；**用户确认 2026-10-14：不纳入主交付**，仅留参考） |
| `BATMAN_水蛭成分归属审计_ShuizhiCurationQC.csv` | 45 成分逐条归属：保留 4（Hirudin/Heparin/Sodium Heparin/Fragmin）、排除 41（栀子属 12 + 无法归属 29） |

原始证据落 `02_BATMAN_成分靶点_CompoundTargets/`（作业包 zip、ScoreGT2 全量 txt、tab1 全量/known 双视图 JSON，作业号 `batman-I2026-10-14-22-53-52-1791989632`）。

## 8. 疾病五库清洗合并（2026-10-14，脚本 `疾病五库合并与净化_mergeDiseaseDBs.py`）

**口径**：GeneCards 全量 9,787（韦恩用）/ Relevance≥40 4,254（下游）；CTD 按 MESH:D054990 过滤邻近病名 20,948→20,509 行（curated=Direct Evidence 非空 23 基因，含 TERT/TERC/MUC5B/SFTPC/RTEL1/PARN 教科书 IPF 基因 ✓）；OMIM 125、TTD 40、DrugBank 38→净化后 100/33/38。**主并集 = GeneCards≥40 ∪ CTD_curated ∪ OMIM ∪ TTD ∪ DrugBank = 4,269 基因**，全部包含于 USER 中间表 21,841（后者≈未过滤全并集，反向差 17,572 为 CTD_any/GeneCards 全量噪声）。

**净化处置**（全部入 `疾病靶点质控_DiseaseQC.csv`）：公认一一别名修复 6（5LOX→ALOX5、CTGF→CCN2、D2R→DRD2、GPR40→FFAR1、PPARgamma→PPARG、PDHK1→PDK1）；排除 33（歧义家族名 7：JNK/NOX/PDE3/PDGFR/TGFBR/VEGFR/CASP；OMIM 表型位点占位 25：EIG/IS/LNCR/CFM1/COPD 等；小鼠基因 CCL12）；真实非编码基因保留（MALAT1/LUCAT1/TERC 等）。

## 9. 药物靶点基因化与药病交集（2026-10-14，脚本 `靶点基因化与药病交集_mapGeneOverlap.py`）

TCMSP 2,454 成分靶点对 → 靶点蛋白名经 **技能 SSOT 映射器**（`TCMSP靶点UniProt映射_mapTcmspUniprot.build_resolver`，本地 UniProt reviewed 人源参考）解析为基因简称：药-成分-靶点边 2,986、未解析 46 靶点名入 `交集质控_OverlapQC.csv`（不编造）；+ BATMAN 水蛭 6 边。**九药去重靶点 244 基因**（川芎 26 / 旋覆花 176 / 桃仁 42 / 水蛭 6 / 浙贝母 44 / 甘草 200 / 紫苏子 118 / 蜜麻黄 197 / 黄芪 180）。**药病交集 197 基因**（占 80.7%；含 PTGS1/2、CASP3/8/9、BAX/BCL2、HSP90AA1 等经典网药核心靶点）。

## 10. GO/KEGG 富集（2026-10-14，R clusterProfiler 4.5.x，脚本 `交集功能富集_enrichGOKEGG.R`）

197 交集基因（SYMBOL→ENTREZID 映射 214 行，含 1:many）：GO BP 2,400 / CC 83 / MF 205 terms（padj<0.05）；KEGG hsa 193 通路（padj<0.05，KEGG REST 需 `options(timeout=300)`）；产出 `KEGG靶点通路长表_KEGGGenePathway.csv`（2,979 行）供网络 D 层。

## 11. STRING PPI（2026-10-14，API `string-db.org/api/tsv/network`，脚本 `PPI获取_STRING_ppiString.py`）

197 基因提交：**score≥900 主交付 687 边 / 173 节点**（24 基因无高置信互作，入 QC）；≥400 全量参考 4,572 边。落 `04_富集与PPI_EnrichPPI/01_数据文件_Data/02_结果数据_ResultTables/PPI网络_STRING/`。

## 12. 网络表构建（2026-10-14，脚本 `网络表构建_buildNetworkTables.py`，对齐技能样例 schema）

`网络边_network.csv`（ID,SYMBOL）+ `网络节点类型_type.csv`（term,type：A药/B成分/C靶点/D通路）+ 节点中心性 `网络节点属性_NetworkNodes.csv` + Cytoscape 边/点 + 成分重命名表。规模：**A9 / B183 / C197 / D20（KEGG top20）**，边 3,422（A→B 183、B→C 2,632、C→D 607）。药名节点统一 `H_` 前缀防撞基因符号（甘草 GC = GC 基因实测冲突）。每药交付 `药物_<code>_<名>_靶点基因_HerbTargets.csv` / `_疾病交集_HerbDiseaseOverlap.csv` 各 9。

## 13. 图谱套件 01–15 出图（2026-10-15）

**真源：** 技能 FROZEN 图 recipe（`网络药理学_NetworkPharmacology/脚本_scripts/` 02 可视化 / 03 STRING / 04 交付布局）+ 样例 runner 接线法；本项目 3 个出图脚本只接契约数据，不复制 recipe。

| 环节 | 内容 | 规模 |
|------|------|------|
| 契约装配 | `图谱契约装配_buildFigureContracts.py`：按库长表双口径、GO 气泡表（fold enrichment）、KEGG top25（KEGG BRITE `br08901` 补 one_type/two_type）、成分靶点、PROVENANCE | 契约 20 文件 |
| 图 01 疾病多库韦恩 | 微生信五库（GeneCards全量/**CTD_curated**/OMIM/TTD/DrugBank）；与图02同 `write_venn_pair` 链 | GC 9786 / CTD_curated 22 / OMIM 100 / TTD 33 / DrugBank 38 |
| 图 02 药病韦恩 | 微生信模板 `build_two_set_svg` + PNG 裁白边（FROZEN §G） | 244 ∩ 4269 = 197 |
| 图 03–05 | 单药交集柱 / 成分交集柱（均分 / 按药） | 9 药 / 183 成分 |
| 图 06–10 | GO 气泡+柱（top10/ontology）、KEGG 棒棒糖+柱（top20）、KEGG 圈图（circlize） | 30 GO / 25 KEGG |
| 图 11–12 | HCTP columns + ellipse（18.5×16.5 in，`04_交付网络布局` 布局引擎） | 409 节点 / 3422 边 |
| 图 13 | STRING 官方网络图（REST `image`，evidence/3D/隐 isolates） | PNG 12MB + SVG |
| 图 14–15 | PPI 同心 Degree 渐变（173/173 标注，5 环外环 86 点） | 687 边 @score≥900 |

**PlotQA：** label_overlap 全 PASS（deep=0）；label_length FAIL 4 处均为 FROZEN 冻结副标题误判（STRING/HCTP 统计副标题 125–219 字），按「冻结文案不改」记录例外。

**落位（by_stage，用户确认 2026-10-15）：**  
- 图 01 → `01_疾病靶点_DiseaseTargets/03_图片文件_Figures/`  
- 图 02–05、11–12、16–19 → `03_药病交集与网络_OverlapAndNetwork/03_图片文件_Figures/`  
- 图 06–10、13–15 → `04_富集与PPI_EnrichPPI/03_图片文件_Figures/`  
- 轨 B 汇总 → `交付文件/`；编号表在 `图谱套件编号表_FigureSuiteTables/`。
