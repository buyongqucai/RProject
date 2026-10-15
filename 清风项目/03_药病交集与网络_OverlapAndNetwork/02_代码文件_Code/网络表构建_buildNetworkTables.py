"""清风项目 Step7：网络表构建（对齐技能样例 schema）。
产出：每药靶点/交集、成分级交集、药物去重基因、network.csv(ID,SYMBOL)、
     type.csv(term,type A药/B成分/C靶点/D通路)、节点中心性、Cytoscape 边/点、
     VennFull 疾病按库表、交集核对表。
D 层 = KEGG padj<0.05 top20；C 层 = 药病交集靶点（与样例口径一致）。
"""
import csv, os, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

DROOT = r'E:\RProject\清风项目\02_药物靶点_DrugTargets\01_数据文件_Data\02_结果数据_ResultTables'
DISE = r'E:\RProject\清风项目\01_疾病靶点_DiseaseTargets\01_数据文件_Data\02_结果数据_ResultTables'
OROOT = r'E:\RProject\清风项目\03_药病交集与网络_OverlapAndNetwork\01_数据文件_Data\02_结果数据_ResultTables'
KROOT = r'E:\RProject\清风项目\04_富集与PPI_EnrichPPI\01_数据文件_Data\02_结果数据_ResultTables'
os.makedirs(OROOT, exist_ok=True)

HERB = {  # 药名 -> (code, en)；节点 ID 统一 H_ 前缀防与基因符号冲突（如 甘草 GC = GC 基因）
    '水蛭': ('H_SZ', 'Leech'), '旋覆花': ('H_XFH', 'Inula Flower'), '川芎': ('H_CX', 'Chuanxiong'),
    '桃仁': ('H_TR', 'Peach Kernel'), '浙贝母': ('H_ZBM', 'Thunberg Fritillary Bulb'),
    '蜜麻黄': ('H_MMH', 'Honey-fried Ephedra'), '紫苏子': ('H_ZSZ', 'Perilla Seed'),
    '黄芪': ('H_HQ', 'Astragalus'), '甘草': ('H_GC', 'Licorice'),
}

# 网络 A 节点 ID = 中文药名（不加 H_ 前缀）。中文药名（甘草/水蛭…）不与拉丁基因符号（GC/EGFR）或
# hsa 通路号冲突，故无需用 H_ 前缀防撞；若出现同名药味（本方 9 味唯一，通常不触发）以尾部空格区分节点键，
# 使 network.csv 键唯一且图上肉眼看着是同一药名。
HERB_NODE, _seen_nid = {}, set()
for _h in HERB:
    _nid = _h
    while _nid in _seen_nid:
        _nid += ' '
    HERB_NODE[_h] = _nid
    _seen_nid.add(_nid)

# ---- 载入疾病并集 ----
disease, dsrc = set(), {}
for r in csv.DictReader(open(os.path.join(DISE, '疾病靶点合并_DiseaseGeneUnion.csv'), encoding='utf-8-sig')):
    disease.add(r['Gene'])
    dsrc[r['Gene']] = r['来源库']

# ---- 成分登记（每药独立 compound_id，样例口径 herb_code+序号） ----
comp_name, comp_reg, comp_src = {}, {}, {}   # (herb, mol) -> id
def reg_comp(herb, mol, mol_id, src):
    key = (herb, mol)
    if key in comp_reg:
        return comp_reg[key]
    code = HERB[herb][0]
    n = sum(1 for (h, m) in comp_reg if h == herb) + 1
    cid = f'{code}{n}'
    comp_reg[key] = cid
    comp_name[cid] = mol
    comp_src[cid] = (src, mol_id)
    return cid

for r in csv.DictReader(open(os.path.join(DROOT, 'TCMSP_过筛成分表_FilteredCompounds.csv'), encoding='utf-8-sig')):
    for herb in r['herbs'].split('|'):
        herb = herb.strip()
        if herb in HERB:
            reg_comp(herb, r['molecule_name'], r['molecule_ID'], 'TCMSP')
for r in csv.DictReader(open(os.path.join(DROOT, 'BATMAN_水蛭专属成分_known靶点_ShuizhiKnownTargets.csv'), encoding='utf-8-sig')):
    reg_comp('水蛭', r['成分英文名'], r['PubChem_CID'], 'BATMAN-TCM 2.0')

# ---- 成分-基因边（基因化） ----
c2g = defaultdict(set)   # (herb, mol) -> genes
for r in csv.DictReader(open(os.path.join(DROOT, 'TCMSP_成分靶点映射_基因化_MoleculeTargetGeneMap.csv'), encoding='utf-8-sig')):
    if r['Gene'] and r['来源库'] == 'TCMSP':
        c2g[(r['药物'], r['成分'])].add(r['Gene'])
for r in csv.DictReader(open(os.path.join(DROOT, 'BATMAN_水蛭专属成分_known靶点_ShuizhiKnownTargets.csv'), encoding='utf-8-sig')):
    c2g[('水蛭', r['成分英文名'])].add(r['基因符号'])

herb_genes = defaultdict(set)
for (herb, mol), gs in c2g.items():
    herb_genes[herb] |= gs
all_drug = set().union(*herb_genes.values())
overlap = all_drug & disease

# ---- 每药文件 ----
for herb, (code, en) in HERB.items():
    gs = sorted(herb_genes[herb])
    with open(os.path.join(DROOT, f'药物_{code}_{herb}_靶点基因_HerbTargets.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['herb_zh', 'herb_en', 'gene'])
        for g in gs:
            w.writerow([herb, en, g])
    with open(os.path.join(OROOT, f'药物_{code}_{herb}_疾病交集_HerbDiseaseOverlap.csv'), 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['herb_zh', 'herb_en', 'gene'])
        for g in sorted(set(gs) & disease):
            w.writerow([herb, en, g])
with open(os.path.join(DROOT, '药物去重基因_DrugGenesUnion.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['gene'])
    for g in sorted(all_drug):
        w.writerow([g])

# ---- 成分级交集 ----
rows = []
for (herb, mol), gs in sorted(c2g.items()):
    cid = comp_reg.get((herb, mol))
    if cid is None:
        cid = reg_comp(herb, mol, '', 'TCMSP')
    for g in sorted(gs):
        rows.append([herb, HERB[herb][1], HERB[herb][0], mol, cid, g, g in disease])
with open(os.path.join(OROOT, '成分疾病交集靶点_CompoundDiseaseOverlapTargets.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['herb_zh', 'herb_en', 'herb_code', 'compound_name', 'compound_id', 'target_gene', 'in_disease_overlap'])
    w.writerows(rows)
with open(os.path.join(OROOT, '成分疾病交集汇总_CompoundDiseaseOverlapSummary.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['herb_zh', 'herb_en', 'herb_code', 'compound_id', 'compound_name', 'n_targets', 'n_overlap_targets'])
    agg = defaultdict(lambda: [0, 0])
    for herb, he, hc, mol, cid, g, ov in rows:
        agg[(herb, cid, mol)][0] += 1
        agg[(herb, cid, mol)][1] += int(ov)
    for (herb, cid, mol), (n, nov) in sorted(agg.items()):
        w.writerow([herb, HERB[herb][1], HERB[herb][0], cid, mol, n, nov])

# ---- KEGG top20 通路 ----
kk = list(csv.DictReader(open(os.path.join(KROOT, 'KEGG通路富集_EnrichKEGG.csv'), encoding='utf-8-sig')))
kk.sort(key=lambda r: float(r['p.adjust']))
top20 = [(r['ID'], r['Description']) for r in kk[:20]]
g2p = defaultdict(set)
for r in csv.DictReader(open(os.path.join(KROOT, 'KEGG靶点通路长表_KEGGGenePathway.csv'), encoding='utf-8-sig')):
    if r['Pathway'] in dict(top20):
        g2p[r['Gene']].add(r['Pathway'])

# ---- network.csv / type.csv（A药 B成分 C靶点 D通路） ----
edges = []
for (herb, mol), gs in sorted(c2g.items()):
    cid = comp_reg[(herb, mol)]
    ogs = gs & overlap
    if not ogs:
        continue
    edges.append((HERB_NODE[herb], cid))
    for g in sorted(ogs):
        edges.append((cid, g))
        for p in sorted(g2p.get(g, ())):
            edges.append((g, p))
edges = list(dict.fromkeys(edges))  # C→D 按成分循环会重复，去重保序
with open(os.path.join(OROOT, '网络边_network.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['ID', 'SYMBOL']); w.writerows(edges)

nodes = {}
for a, b in edges:
    for n in (a, b):
        nodes.setdefault(n, None)
for n in list(nodes):
    if n in {c for c in comp_reg.values()}:
        nodes[n] = 'B'
    elif n.startswith('hsa'):
        nodes[n] = 'D'
    elif n in set(HERB_NODE.values()):
        nodes[n] = 'A'
    else:
        nodes[n] = 'C'
with open(os.path.join(OROOT, '网络节点类型_type.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['term', 'type'])
    for n, t in sorted(nodes.items(), key=lambda x: (x[1], x[0])):
        w.writerow([n, t])

# ---- 节点中心性 ----
deg = defaultdict(int)
for a, b in edges:
    deg[a] += 1; deg[b] += 1
bet = clo = {}
try:
    import networkx as nx
    G = nx.Graph()
    G.add_edges_from(edges)
    bet = nx.betweenness_centrality(G)
    clo = nx.closeness_centrality(G)
except Exception as e:
    print('[nx] fallback:', e)
with open(os.path.join(OROOT, '网络节点属性_NetworkNodes.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['node', 'type', 'degree', 'betweenness', 'closeness'])
    for n in sorted(nodes):
        w.writerow([n, nodes[n], deg.get(n, 0), bet.get(n, 0), clo.get(n, 0)])

# ---- Cytoscape 边/点（HCTP 全网 + 成分-基因二部） ----
with open(os.path.join(OROOT, '网络边_HerbCompoundTargetPathway_Cytoscape.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['source', 'target']); w.writerows(edges)
with open(os.path.join(OROOT, '网络节点_HerbCompoundTargetPathway_Cytoscape.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['name', 'type', 'Degree'])
    for n in sorted(nodes):
        w.writerow([n, nodes[n], deg.get(n, 0)])
cg = [(comp_reg[(h, m)], g) for (h, m), gs2 in sorted(c2g.items()) for g in sorted(gs2 & overlap)]
with open(os.path.join(OROOT, '网络边_CompoundGene_Cytoscape.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['source', 'target']); w.writerows(cg)
cgn = defaultdict(int)
for a, b in cg:
    cgn[a] += 1; cgn[b] += 1
with open(os.path.join(OROOT, '网络节点_CompoundGene_Cytoscape.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['name', 'type', 'Degree'])
    for n in sorted(cgn):
        w.writerow([n, nodes.get(n, 'C'), cgn[n]])

# ---- 成分重命名表 + 草药成分边 ----
with open(os.path.join(OROOT, '成分重命名_CompoundRenameMap.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['herb_code', 'compound_id', 'herb_zh', 'herb_en', 'compound_name', 'source_id', '来源库'])
    for (herb, mol), cid in sorted(comp_reg.items(), key=lambda x: x[1]):
        src, sid = comp_src.get(cid, ('', ''))
        w.writerow([HERB[herb][0], cid, herb, HERB[herb][1], mol, sid, src])
with open(os.path.join(OROOT, '草药成分边_HerbCompoundEdges.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['herb_code', 'compound_id', 'herb'])
    for (herb, mol), cid in sorted(comp_reg.items(), key=lambda x: x[1]):
        w.writerow([HERB[herb][0], cid, herb])

# ---- VennFull 疾病按库（完整 GeneCards 口径） ----
bydb = list(csv.DictReader(open(os.path.join(DISE, '疾病靶点按库_DiseaseGenesByDB.csv'), encoding='utf-8-sig')))
with open(os.path.join(DISE, '疾病靶点按库_VennFull_DiseaseGenesByDB.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['Gene', 'GeneCards', 'CTD_curated', 'OMIM', 'TTD', 'DrugBank'])
    for r in bydb:
        w.writerow([r['Gene'], r['GeneCards_full'], r['CTD_curated'], r['OMIM'], r['TTD'], r['DrugBank']])

# ---- 交集核对 ----
n_tc_pairs = sum(1 for _ in csv.DictReader(open(os.path.join(DROOT, 'TCMSP_成分靶点映射_基因化_MoleculeTargetGeneMap.csv'), encoding='utf-8-sig')))
with open(os.path.join(OROOT, '交集核对_OverlapIntegrity.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['metric', 'value'])
    w.writerow(['n_herbs', len(HERB)])
    w.writerow(['drug_union', len(all_drug)])
    w.writerow(['disease_union', len(disease)])
    w.writerow(['overlap_union', len(overlap)])
    w.writerow(['n_compounds_registry', len(comp_reg)])
    w.writerow(['n_compounds_in_network', sum(1 for t in nodes.values() if t == 'B')])
    w.writerow(['n_compound_target_edges_gene_mapped', n_tc_pairs])
    w.writerow(['n_compound_overlap_edges', sum(1 for r in rows if r[6])])
    w.writerow(['n_kegg_top20', len(top20)])
    w.writerow(['n_network_edges', len(edges)])
    w.writerow(['n_network_nodes', len(nodes)])

from collections import Counter
tc = Counter(nodes.values())
print('[network] edges=%d nodes=%d types=%s' % (len(edges), len(nodes), dict(tc)))
print('[overlap]', len(overlap), '[drug]', len(all_drug), '[disease]', len(disease))
print('[top20 pathways]', top20[:5], '...')
