# 手工导出与 Cytoscape 可选操作

> 由网药技能说明迁出：可选精修与浏览器导出步骤。  
> **代码出图仍为交付默认**（见 [`出图约束_NetworkFigureStandards.md`](出图约束_NetworkFigureStandards.md)）。  
> **成分靶点瀑布权威正文：** [`成分靶点获取与交付规范_CompoundTargetSOP.md`](成分靶点获取与交付规范_CompoundTargetSOP.md)。  
> **进化：** 你确认新的手工步骤或库可达性后，回写本文件；技能说明入口只留指针。

### Cytoscape SOP — 成分网络图

1. 安装 Cytoscape 3.10.2。  
2. File → Import → Network from File：优先样例导出的 `网络边_CompoundGene_Cytoscape.csv`（或全量 `网络边_network.csv`）。  
3. Import → Table：`网络节点_CompoundGene_Cytoscape.csv`（或 `网络节点类型_type.csv`），按节点名匹配属性 A/B/C。  
4. Style：按 Degree 映射节点 Width/Height（min 60, max 120）；连续色映射 Degree。  
5. 导出 SVG → 交付名建议 `网络图_HerbCompoundTarget_Cytoscape.svg`。

刷新成分–交集表（交付盘可用时）：

```text
python 网络药理学_NetworkPharmacology/_prepare_compound_overlap_from_delivery.py
```

再运行 `01_样例_sample/代码文件/01_run_sample.R`。

样例目录约定（raw=`数据文件/`；结果=`代码文件/结果文件/`；文件流水线编号）：见 DeliveryStandards [`样例目录与命名_SampleLayoutNaming.md`](../../00_基础_Foundation/统一交付规范_DeliveryStandards/文档_docs/样例目录与命名_SampleLayoutNaming.md)。

### Cytoscape SOP — PPI 渐变图

1. STRING 上传「药物疾病交集」基因列表，物种 Homo sapiens，导出 `string_interactions_short.tsv`。  
2. Cytoscape 导入该 tsv → Tools → Analyze Network。  
3. Degree 映射大小 60–120、连续颜色；导出 `PPI渐变图` SVG 与节点表 CSV；保存 `.cys`。

### 疾病库按英文病名导出 SOP（摘要）

1. 确定**英文病名**（样例动脉粥样硬化：`Atherosclerosis`；测试肺癌：`lung cancer` / MeSH `Lung Neoplasms` / `MESH:D008175`）。  
2. GeneCards：检索英文病名 → 导出 Results CSV（无公开批量 API；浏览器导出）。  
3. TTD / DrugBank / OMIM / CTD / **DisGeNET**：同样以**英文病名**检索并导出靶点/基因列（DisGeNET：https://disgenet.com/）。  
4. DrugBank 靶点与 UniProt reviewed human 匹配后保存 `Drugbank靶点数据.csv`。  
5. 将各库 gene symbol 标准化后做韦恩与并集。

**配置 / 断点（与 2026-07-19 网址实测一致）：**

| 库 | 自动拉取 | 说明 |
|----|----------|------|
| GeneCards / DrugBank / OMIM | **否**（403 或需登录） | 请你浏览器导出；缺文件 → `BLOCKED_EXTERNAL`，禁止编造 |
| TTD / DisGeNET / TCMSP / BATMAN / ETCM2 / TCMBank | **否**（页可达或仅表单，无稳定公开 API） | 请你按瀑布导出；TCMBank 优先 **http://tcmbank.cn/** |
| HERB 2.0 | **是（chedi API，可达时）** | search/detail；失败 → MANUAL |
| SwissTargetPrediction | **是（表单提交，可达时）** | locate→predict→result；滤 Probability=0；失败 → MANUAL |
| OMIM API | 可选 | https://www.omim.org/api → `OMIM_API_KEY` |
| CTD | **是（bulk）** | `CTD_curated_genes_diseases.tsv.gz` 实测可下 |
| KEGG REST / STRING API | **是** | 通路列表与 PPI 边可程序化；网络图代码绘制 |
| OpenTargets | 陪跑 | GraphQL 可用；**非**交付主疾病库 |

### 单药成分–靶点导出 SOP（摘要）

完整瀑布见 **§4.1**。操作要点：

1. **TCMSP** 检索单药 → OB≥30%、DL≥0.18 → 参数表 + 成分靶点（有则结束本药获取）。  
2. 无 → **BATMAN-TCM**（http://bionet.ncpsb.org.cn/batman-tcm/#/search）仅 **known** 靶点。  
3. 无 → **ETCM2**（http://www.tcmip.cn/ETCM2/front/#/）。  
4. 无 → **HERB 2.0** 取成分与 SMILES → **SwissTargetPrediction**（Homo sapiens）；**TCMBank** 可作成分来源后同走预测。  
5. 剔除 Probability=0；复合物空基因用 UniProt Accession 展开；MW 过大 → `异常清单_CompoundTargetExceptions.csv`。  
6. 交付 `{药}靶点基因.xlsx`（整合三列 + 各成分 Swiss）；**不做** UniProt 全表左拼。schema = 药物–有效成分–靶点(基因)。

