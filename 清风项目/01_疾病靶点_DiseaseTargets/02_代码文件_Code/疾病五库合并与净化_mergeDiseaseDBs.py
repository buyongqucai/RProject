"""清风项目 Step3-4：疾病靶点清洗合并（五库）+ USER 中间表对账。
口径（技能 数据库分类与流水线 §1.1 / 出图约束 §0a）：
- 韦恩用完整 GeneCards；下游并集用 GeneCards Relevance≥40
- CTD 只取 MESH:D054990（剔除邻近病名行）；curated = Direct Evidence 非空
- 主并集 = GeneCards≥40 ∪ CTD_curated ∪ OMIM ∪ TTD ∪ DrugBank
- TTD 别名修复仅限一一对应公认写法（如 5LOX→ALOX5），其余不编造
"""
import csv, os, sys
sys.stdout.reconfigure(encoding='utf-8')

D = r'E:\RProject\清风项目\01_疾病靶点_DiseaseTargets\01_数据文件_Data\01_初始数据_RawInitial'
R = r'E:\RProject\清风项目\01_疾病靶点_DiseaseTargets\01_数据文件_Data\02_结果数据_ResultTables'
os.makedirs(R, exist_ok=True)

ALIAS = {'5LOX': 'ALOX5', '5-LOX': 'ALOX5', '15-LOX': 'ALOX15', 'cPLA2': 'PLA2G4A',
         'CTGF': 'CCN2', 'D2R': 'DRD2', 'GPR40': 'FFAR1', 'PPARgamma': 'PPARG', 'PDHK1': 'PDK1'}
# 无法唯一映射的家族名（不编造）；OMIM 表型/位点占位；非人源
EXCLUDE = {
    'CASP': '歧义家族名(caspase family)，无法唯一映射',
    'JNK': '歧义家族名(MAPK8/9/10)，无法唯一映射',
    'NOX': '歧义家族名(NOX family)，无法唯一映射',
    'PDE3': '歧义家族名(PDE3A/B)，无法唯一映射',
    'PDGFR': '歧义家族名(PDGFRA/B)，无法唯一映射',
    'TGFBR': '歧义家族名(TGFBR1/2)，无法唯一映射',
    'VEGFR': '歧义家族名(KDR/FLT1/FLT4)，无法唯一映射',
    'CCL12': '小鼠基因(物种口径 hsa)，CTD 混入',
}
for _p in ['CFEOM3C', 'CFM1', 'COPD', 'CTEPH1', 'EIG1', 'EIG2', 'EIG3', 'EIG4', 'EIG5', 'EIG7',
           'IS1', 'IS2', 'IS4', 'IS5', 'LNCR1', 'LNCR3', 'LNCR4', 'LNCR5', 'PHN', 'PLF',
           'SCLC1', 'SHOXY', 'SM2', 'TAPVR1', 'TSG11']:
    EXCLUDE[_p] = 'OMIM 表型/位点占位条目，非基因符号'
uniprot_genes = set()
with open(os.path.join(D, '00_UniProt参考_UniProtRef', 'UniProt_人源参考蛋白组_ReviewedHumanProteome.csv'),
          encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        g = (row.get('Gene Names (primary)') or '').strip()
        if g:
            uniprot_genes.add(g)

stats = {}
alias_log = []

# ---- GeneCards ----
gc_full, gc40, gc_score = set(), set(), {}
with open(os.path.join(D, '01_GeneCards_疾病靶点_IpfTargets', 'GeneCards_疾病靶点_IpfTargets.csv'),
          encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        s = (row.get('Symbol') or '').strip()
        if not s:
            continue
        try:
            sc = float(row.get('Relevance Score') or 0)
        except ValueError:
            sc = 0.0
        gc_full.add(s)
        gc_score[s] = max(gc_score.get(s, 0), sc)
        if sc >= 40:
            gc40.add(s)
stats['GeneCards_full'] = len(gc_full)
stats['GeneCards_ge40'] = len(gc40)

# ---- CTD ----
ctd_any, ctd_direct, ctd_refs = set(), set(), {}
n_rows = n_keep = 0
with open(os.path.join(D, '05_CTD_疾病靶点_IpfTargets', 'CTD_疾病靶点_IpfTargets.csv'),
          encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        n_rows += 1
        did = (row.get('Disease ID') or '').strip()
        dname = (row.get('Disease Name') or '').strip()
        if did != 'MESH:D054990' and dname.lower() != 'idiopathic pulmonary fibrosis':
            continue
        n_keep += 1
        s = (row.get('Gene Symbol') or '').strip()
        if not s:
            continue
        ctd_any.add(s)
        try:
            ctd_refs[s] = max(ctd_refs.get(s, 0), int(row.get('Reference Count') or 0))
        except ValueError:
            pass
        if (row.get('Direct Evidence') or '').strip():
            ctd_direct.add(s)
stats['CTD_总行'] = n_rows
stats['CTD_D054990行'] = n_keep
stats['CTD_any基因'] = len(ctd_any)
stats['CTD_curated基因'] = len(ctd_direct)

def purge(s, tag):
    out = set()
    for g in s:
        if g in EXCLUDE:
            alias_log.append([tag, g, '（排除）', EXCLUDE[g]])
        else:
            out.add(g)
    return out

gc_full = purge(gc_full, 'GeneCards')
gc40 = purge(gc40, 'GeneCards_ge40')
ctd_any = purge(ctd_any, 'CTD')
ctd_direct = purge(ctd_direct, 'CTD_curated')

def load_list(path):
    out = set()
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        for line in f:
            s = line.strip().strip('"')
            if s and ',' not in s and len(s) < 30:
                out.add(s)
    return out

def load_col(path, col):
    out = set()
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        for row in csv.DictReader(f):
            s = (row.get(col) or '').strip()
            if s:
                out.add(s)
    return out

def fix_alias(genes, tag):
    fixed = set()
    for g in genes:
        if g in EXCLUDE:
            alias_log.append([tag, g, '（排除）', EXCLUDE[g]])
            continue
        if g in ALIAS:
            alias_log.append([tag, g, ALIAS[g], '公认一一对应别名修复'])
            fixed.add(ALIAS[g])
        else:
            fixed.add(g)
    return fixed

omim = fix_alias(load_list(os.path.join(D, '04_OMIM_疾病靶点_IpfTargets', 'OMIM_靶点列表_TargetList.csv')), 'OMIM')
ttd = fix_alias(load_list(os.path.join(D, '02_TTD_疾病靶点_IpfTargets', 'TTD_靶点列表_TargetList.csv')), 'TTD')
drugbank = fix_alias(load_col(os.path.join(D, '03_DrugBank_疾病靶点_IpfTargets', 'DrugBank_靶点列表_TargetList.csv'), 'Gene'), 'DrugBank')
stats['OMIM'] = len(omim); stats['TTD'] = len(ttd); stats['DrugBank'] = len(drugbank)

user = load_list(os.path.join(R, '疾病基因合并_DiseaseGeneUnion_USER.csv'))
stats['USER中间表'] = len(user)

union = gc40 | ctd_direct | omim | ttd | drugbank
stats['主并集'] = len(union)
stats['主并集∩USER'] = len(union & user)

# ---- 按库表 ----
allg = sorted(gc_full | ctd_any | omim | ttd | drugbank | user)
with open(os.path.join(R, '疾病靶点按库_DiseaseGenesByDB.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['Gene', 'GeneCards_full', 'GeneCards_ge40', 'RelevanceScore', 'CTD_curated',
                'CTD_any', 'CTD_RefCount', 'OMIM', 'TTD', 'DrugBank', 'USER中间表', '主并集'])
    for g in allg:
        w.writerow([g, int(g in gc_full), int(g in gc40), round(gc_score.get(g, 0), 2),
                    int(g in ctd_direct), int(g in ctd_any), ctd_refs.get(g, 0),
                    int(g in omim), int(g in ttd), int(g in drugbank), int(g in user), int(g in union)])

# ---- 主并集表 ----
def srcs(g):
    s = []
    if g in gc40: s.append('GeneCards_ge40')
    if g in ctd_direct: s.append('CTD_curated')
    if g in omim: s.append('OMIM')
    if g in ttd: s.append('TTD')
    if g in drugbank: s.append('DrugBank')
    return s
with open(os.path.join(R, '疾病靶点合并_DiseaseGeneUnion.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['Gene', '来源库数', '来源库', 'GeneCards_Relevance', 'CTD_RefCount', 'UniProt_reviewed收录'])
    for g in sorted(union):
        s = srcs(g)
        w.writerow([g, len(s), '|'.join(s), round(gc_score.get(g, 0), 2), ctd_refs.get(g, 0),
                    int(g in uniprot_genes)])

# ---- QC ----
nonstd = [g for g in sorted(union) if g not in uniprot_genes]
with open(os.path.join(R, '疾病靶点质控_DiseaseQC.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['项目', '数值/内容', '说明'])
    for k, v in stats.items():
        w.writerow([k, v, ''])
    w.writerow(['USER差集(仅USER)', len(user - union), 'USER中间表有而主并集无'])
    w.writerow(['主并集差集(仅本表)', len(union - user), '主并集有而USER中间表无'])
    w.writerow(['主并集中非UniProt标准符号', len(nonstd), '|'.join(nonstd[:40])])
    for tag, old, new, why in alias_log:
        w.writerow([f'处置[{tag}]', f'{old} -> {new}', why])

print('== 统计 ==')
for k, v in stats.items():
    print(f'  {k}: {v}')
print(f'  USER差集(仅USER): {len(user - union)}  主并集差集(仅本表): {len(union - user)}')
print(f'  主并集中非UniProt标准符号: {len(nonstd)}', nonstd[:20])
print('  别名修复:', alias_log)
