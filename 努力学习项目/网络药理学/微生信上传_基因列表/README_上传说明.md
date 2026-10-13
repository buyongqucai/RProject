# 微生信上传清单（UC / Ulcerative Colitis）

按技能：韦恩交付图 = 微生信导出，不是 R 
p_plot_*_venn。

## 疾病多库韦恩
依次上传（建议集合名与文件名一致）：
1. DiseaseDB_TTD.txt
2. DiseaseDB_DrugBank.txt
3. DiseaseDB_GeneCards.txt（完整 GeneCards，仅用于韦恩）
4. DiseaseDB_OMIM.txt

导出 SVG → 保存为 参考_交付原图/Venn_DiseaseDatabases.svg

## 药–病韦恩
1. DrugDisease_Drugs.txt（药物去重靶点）
2. DrugDisease_Disease.txt（过滤后疾病并集，下游交集用这套）

导出 SVG → 保存为 参考_交付原图/Venn_DrugDisease.svg

然后运行：python 代码文件/08_export_uc_venn_from_delivery.py
