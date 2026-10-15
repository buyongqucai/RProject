# -*- coding: utf-8 -*-
"""清风项目：图谱套件契约装配 + 图02 微生信药病韦恩（FROZEN §G）。
把各模块结果表装配成技能契约命名（01_契约接口_DataContracts.R），
供 R 出图脚本 01/02/03 直接消费；图02 用 weishengxin_venn_lib 模板几何。
"""
from __future__ import annotations
import csv, importlib.util, json, os, shutil, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

PROJ = Path(r'E:\RProject\清风项目')
SKILL = Path(r'E:\RProject\生信分析技能_BioinformaticsSkills\03_药物计算_DrugDiscovery\网络药理学_NetworkPharmacology')
DATA = PROJ / '03_药病交集与网络_OverlapAndNetwork' / '01_数据文件_Data' / '02_结果数据_ResultTables'
DRUG = PROJ / '02_药物靶点_DrugTargets' / '01_数据文件_Data' / '02_结果数据_ResultTables'
DISE = PROJ / '01_疾病靶点_DiseaseTargets' / '01_数据文件_Data' / '02_结果数据_ResultTables'
PPI = PROJ / '04_富集与PPI_EnrichPPI' / '01_数据文件_Data' / '02_结果数据_ResultTables'
OUT = DATA / '图谱契约数据_FigureContractData'
FIG = PROJ / '04_富集与PPI_EnrichPPI' / '03_图片文件_Figures'
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

def rd(p, enc='utf-8-sig'):
    with open(p, encoding=enc, newline='') as f:
        return list(csv.DictReader(f))

def wr(p, header, rows):
    with open(p, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

HERB_EN = {'水蛭': 'Leech', '旋覆花': 'Inula Flower', '川芎': 'Chuanxiong', '桃仁': 'Peach Kernel',
           '浙贝母': 'Thunberg Fritillary Bulb', '蜜麻黄': 'Honey-fried Ephedra', '紫苏子': 'Perilla Seed',
           '黄芪': 'Astragalus', '甘草': 'Licorice'}

# ---- 1. 直接复制的契约文件 ----
for f in DRUG.glob('药物_*_靶点基因_HerbTargets.csv'):
    shutil.copy2(f, OUT / f.name)
for f in DATA.glob('药物_*_疾病交集_HerbDiseaseOverlap.csv'):
    shutil.copy2(f, OUT / f.name)
for src, dst in [
    (DRUG / '药物去重基因_DrugGenesUnion.csv', OUT / '药物去重基因_DrugGenesUnion.csv'),
    (DATA / '网络边_network.csv', OUT / '网络边_network.csv'),
    (DATA / '网络节点类型_type.csv', OUT / '网络节点类型_type.csv'),
    (DATA / '成分重命名_CompoundRenameMap.csv', OUT / '成分重命名_CompoundRenameMap.csv'),
    (DATA / '草药成分边_HerbCompoundEdges.csv', OUT / '草药成分边_HerbCompoundEdges.csv'),
    (PPI / 'PPI网络_STRING' / 'PPI互作_StringInteractions_score900.tsv', OUT / '19_PPI互作_StringInteractions_score900.tsv'),
    (PPI / 'PPI网络_STRING' / 'PPI互作_StringInteractions.tsv', OUT / 'PPI互作_StringInteractions.tsv'),
]:
    shutil.copy2(src, dst)
print('[copy] contract files ok')

# ---- 2. 疾病按库 长表（下游口径 + VennFull 口径） ----
bydb = rd(DISE / '疾病靶点按库_DiseaseGenesByDB.csv')
SRC = [('GeneCards_ge40', 'GeneCards'), ('CTD_curated', 'CTD'), ('OMIM', 'OMIM'), ('TTD', 'TTD'), ('DrugBank', 'DrugBank')]
long_rows = [[r['Gene'], nm] for r in bydb for col, nm in SRC if r[col] == '1']
wr(OUT / '疾病靶点按库_DiseaseGenesByDB.csv', ['gene', 'source'], long_rows)
venn_rows = [[r['Gene'], nm] for r in bydb for col, nm in [('GeneCards_full', 'GeneCards'), ('CTD_curated', 'CTD'),
                                                          ('OMIM', 'OMIM'), ('TTD', 'TTD'), ('DrugBank', 'DrugBank')] if r[col] == '1']
wr(OUT / '疾病靶点按库_VennFull_DiseaseGenesByDB.csv', ['gene', 'source'], venn_rows)
print(f'[disease-long] downstream={len(long_rows)} vennfull={len(venn_rows)}')

# ---- 3. 疾病并集 / 药病交集（列名契约为 gene） ----
uni = rd(DISE / '疾病靶点合并_DiseaseGeneUnion.csv')
wr(OUT / '疾病靶点合并_DiseaseGenesUnion.csv', ['gene', 'sources', 'n_sources'],
   [[r['Gene'], r['来源库'], r['来源库数']] for r in uni])
ov = rd(DATA / '药物疾病交集_DrugDiseaseOverlap.csv')
wr(OUT / '药物疾病交集_DrugDiseaseOverlap.csv', ['gene', 'n_herbs', 'herbs', 'disease_sources', 'drug_sources'],
   [[r['Gene'], r['药物数'], r['药物'], r['疾病来源库'], r['药物来源库']] for r in ov])

# ---- 4. 单药交集汇总（herb_zh/herb_en/n_overlap_genes） ----
summ = rd(DATA / '单药疾病交集汇总_PerHerbOverlapSummary.csv')
rows = []
for r in summ:
    if r['药物'] == '合计(去重)':
        continue
    rows.append([r['药物'], HERB_EN.get(r['药物'], r['药物']), r['靶点数'], r['疾病交集数'], r['交集占比'], r['来源库']])
wr(OUT / '单药疾病交集汇总_PerHerbOverlapSummary.csv',
   ['herb_zh', 'herb_en', 'n_targets', 'n_overlap_genes', 'overlap_ratio', 'source'], rows)

# ---- 5. 成分靶点（herb=英文药名） ----
ct = rd(DATA / '成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv')
wr(OUT / '药物成分靶点_CompoundTargets.csv', ['herb', 'compound_id', 'target_gene', 'compound_name', 'herb_code', 'target_in_overlap'],
   [[r['herb_en'], r['compound_id'], r['target_gene'], r['compound_name'], r['herb_code'], r['in_disease_overlap']] for r in ct])

# ---- 6. GO 气泡表（top10/ontology，enrichment=富集倍数） ----
def fold(gr, br):
    try:
        k, n = gr.split('/'); K, N = br.split('/')
        return (float(k) / float(n)) / (float(K) / float(N))
    except Exception:
        return 1.0
go_rows = []
for ont in ['BP', 'CC', 'MF']:
    tag = {'BP': 'BP', 'CC': 'CC', 'MF': 'MF'}[ont]
    go = rd(PPI / f'交集功能富集_GO_{tag}_EnrichGO{tag}.csv')
    for r in go:
        r['_fold'] = fold(r.get('GeneRatio', ''), r.get('BgRatio', ''))
    go.sort(key=lambda r: float(r['pvalue']))
    for r in go[:10]:
        go_rows.append([r['Description'], f"{r['_fold']:.6g}", r['pvalue'], r['Count'], ont])
wr(OUT / '富集GO_BPCCMF_Bubble.csv', ['term', 'enrichment', 'pvalue', 'count', 'ontology'], go_rows)
print(f'[go-bubble] {len(go_rows)} rows')

# ---- 7. KEGG top25（one_type/two_type ← KEGG BRITE br08901，不编造） ----
brite = {}
try:
    import requests
    txt = requests.get('https://rest.kegg.jp/get/br:br08901', timeout=120).text
    a_name = b_name = ''
    import re as _re
    for line in txt.splitlines():
        if line.startswith('A'):
            a_name = line[1:].strip()
        elif line.startswith('B'):
            b_name = line[1:].strip()
        elif line.startswith('C'):
            m = _re.match(r'C\s+(\d{5})', line)
            if m:
                brite['hsa' + m.group(1)] = (a_name, b_name)
    print(f'[brite] {len(brite)} hsa pathways classified')
except Exception as e:
    print('[brite] FAILED', e)

kk = rd(PPI / 'KEGG通路富集_EnrichKEGG.csv')
kk.sort(key=lambda r: float(r['pvalue']))
kk_rows = []
for r in kk[:25]:
    one, two = brite.get(r['ID'], ('', ''))
    kk_rows.append([r['ID'], r['Description'], r.get('GeneRatio', ''), r.get('BgRatio', ''),
                    r['pvalue'], r['p.adjust'], r.get('geneID', ''), r.get('Count', ''), one, two])
wr(OUT / '富集KEGG_TopPathways.csv',
   ['ID', 'term', 'GeneRatio', 'BgRatio', 'pvalue', 'padj', 'geneID', 'count', 'one_type', 'two_type'], kk_rows)
print(f'[kegg-top] {len(kk_rows)} rows; one_type filled={sum(1 for r in kk_rows if r[8])}')

# ---- 8. PROVENANCE ----
prov = {
    'data_provenance': 'REAL',
    'source': 'qingfeng_pipeline_tcmsp_batman_disease5db',
    'disease_english_name': 'Idiopathic Pulmonary Fibrosis',
    'disease_mesh': 'D054990',
    'drug_union': sum(1 for _ in rd(OUT / '药物去重基因_DrugGenesUnion.csv')),
    'disease_union': sum(1 for _ in uni),
    'overlap': len(ov),
    'note': 'TCMSP 8 herbs + BATMAN-TCM 2.0 水蛭 known; GeneCards>=40 union CTD_curated+OMIM+TTD+DrugBank',
}
(OUT / 'PROVENANCE.json').write_text(json.dumps(prov, ensure_ascii=False, indent=2), encoding='utf-8')

# ---- 9. 图02 微生信两集韦恩（Drugs × Disease）+ 裁白边 ----
spec = importlib.util.spec_from_file_location('wx_venn', SKILL / '脚本_scripts' / 'weishengxin_venn_lib.py')
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)
drug_genes = [r['gene'] for r in rd(OUT / '药物去重基因_DrugGenesUnion.csv')]
disease_genes = [r['Gene'] for r in uni]
svg_text = lib.build_two_set_svg(drug_genes, disease_genes, name_a='Drugs', name_b='Disease')
svg_p, png_p = lib.write_venn_pair(svg_text, FIG, '02_韦恩图_DrugDisease_Venn')
print(f'[venn02] svg={svg_p.stat().st_size} png={png_p.stat().st_size}')

try:
    from PIL import Image
    def trim(p, tol=245):
        im = Image.open(p).convert('RGB')
        import numpy as np
        a = np.asarray(im)
        mask = (a < tol).any(axis=2)
        ys, xs = mask.any(axis=1), mask.any(axis=0)
        if not ys.any():
            return
        box = (int(xs.argmax()), int(ys.argmax()), int(len(xs) - xs[::-1].argmax()), int(len(ys) - ys[::-1].argmax()))
        im.crop(box).save(p)
    trim(png_p)
    print(f'[venn02] trimmed -> {png_p.stat().st_size}')
except Exception as e:
    print('[venn02] trim skipped:', e)

print('[done] contracts at', OUT)
