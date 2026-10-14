"""清风项目 Step5-6：药物靶点基因化（TCMSP+BATMAN）→ 单药靶点表 → 药病交集。
基因化复用技能 SSOT 映射器（TCMSP靶点UniProt映射_mapTcmspUniprot.build_resolver），
本地 UniProt reviewed 人源蛋白组做名称→基因简称解析；解析不上不编造，入 QC。
"""
import csv, importlib.util, os, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

DROOT = r'E:\RProject\清风项目\02_药物靶点_DrugTargets\01_数据文件_Data'
DDIR = r'E:\RProject\清风项目\01_疾病靶点_DiseaseTargets\01_数据文件_Data\02_结果数据_ResultTables'
OROOT = r'E:\RProject\清风项目\03_药病交集与网络_OverlapAndNetwork\01_数据文件_Data\02_结果数据_ResultTables'
os.makedirs(OOROOT := OROOT, exist_ok=True)

# ---- 1. 基因化映射器（技能 SSOT） ----
# 映射器按 TSV 读入；本地 UniProt 参考是逗号 CSV → 先转 TSV 副本（tmp，不改参考原件）
import csv as _csv
_uni_csv = Path(r'E:\RProject\清风项目\01_疾病靶点_DiseaseTargets\01_数据文件_Data\01_初始数据_RawInitial\00_UniProt参考_UniProtRef\UniProt_人源参考蛋白组_ReviewedHumanProteome.csv')
_uni_tsv = Path(r'E:\dock_yuyang\_qf_tmp\uniprot_reviewed_human.tsv')
if not _uni_tsv.exists():
    with _uni_csv.open(encoding='utf-8-sig', newline='') as fi, _uni_tsv.open('w', encoding='utf-8', newline='') as fo:
        rd = _csv.reader(fi)
        wr = _csv.writer(fo, delimiter='\t')
        for row in rd:
            wr.writerow(row)
spec = importlib.util.spec_from_file_location(
    'tcmsp_map',
    r'E:\RProject\生信分析技能_BioinformaticsSkills\03_药物计算_DrugDiscovery\网络药理学_NetworkPharmacology\脚本_scripts\TCMSP靶点UniProt映射_mapTcmspUniprot.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
resolve = mod.build_resolver(_uni_tsv)
print('[map] resolver ready')

# ---- 2. TCMSP 边 → 基因 ----
edges = []          # (herb, mol, target_name, gene, OB, DL)
unmapped = {}
n_pairs = 0
with open(os.path.join(DROOT, r'02_结果数据_ResultTables\TCMSP_成分靶点映射_MoleculeTargetMap.csv'),
          encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        n_pairs += 1
        gene = resolve(row['target_name'])
        for herb in row['herbs'].split('|'):
            herb = herb.strip()
            if not herb:
                continue
            if gene:
                edges.append((herb, row['molecule_name'], row['target_name'], gene, row['OB'], row['DL']))
            else:
                unmapped.setdefault(row['target_name'], set()).add(herb)
n_map = len(edges)
print(f'[tcmsp] pairs={n_pairs} herb-edges={n_map} 未解析靶点名={len(unmapped)}')

# ---- 3. BATMAN 水蛭 known 边 ----
with open(os.path.join(DROOT, r'02_结果数据_ResultTables\BATMAN_水蛭专属成分_known靶点_ShuizhiKnownTargets.csv'),
          encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        edges.append((row['药物'], row['成分英文名'], row['基因符号'], row['基因符号'], '', ''))

# ---- 4. 基因化边表 + 单药靶点表 ----
with open(os.path.join(DROOT, r'02_结果数据_ResultTables\TCMSP_成分靶点映射_基因化_MoleculeTargetGeneMap.csv'),
          'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['药物', '成分', '靶点蛋白名', 'Gene', 'OB', 'DL', '来源库'])
    for herb, mol, tname, gene, ob, dl in edges:
        w.writerow([herb, mol, tname, gene, ob, dl,
                    'BATMAN-TCM 2.0' if ob == '' else 'TCMSP'])

herb_genes = {}     # herb -> {gene: set(mols)}
for herb, mol, tname, gene, ob, dl in edges:
    herb_genes.setdefault(herb, {}).setdefault(gene, set()).add(mol)
all_drug_genes = set(g for hg in herb_genes.values() for g in hg)

with open(os.path.join(DROOT, r'02_结果数据_ResultTables\药物_全部单药靶点_AllHerbTargets.csv'),
          'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['药物', 'Gene', '来源库', '贡献成分数', '成分'])
    for herb in sorted(herb_genes):
        for gene in sorted(herb_genes[herb]):
            mols = sorted(herb_genes[herb][gene])
            src = 'BATMAN-TCM 2.0' if herb == '水蛭' else 'TCMSP'
            w.writerow([herb, gene, src, len(mols), '|'.join(mols)])

# ---- 5. 疾病并集 ----
disease, dsrc = set(), {}
with open(os.path.join(DDIR, '疾病靶点合并_DiseaseGeneUnion.csv'), encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        disease.add(row['Gene'])
        dsrc[row['Gene']] = row['来源库']
print(f'[disease] union={len(disease)}')

# ---- 6. 药病交集 ----
overlap = all_drug_genes & disease
with open(os.path.join(OOROOT, '药物疾病交集_DrugDiseaseOverlap.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['Gene', '药物数', '药物', '疾病来源库', '药物来源库'])
    for g in sorted(overlap):
        herbs = sorted(h for h in herb_genes if g in herb_genes[h])
        src = sorted({('BATMAN-TCM 2.0' if h == '水蛭' else 'TCMSP') for h in herbs})
        w.writerow([g, len(herbs), '|'.join(herbs), dsrc.get(g, ''), '|'.join(src)])

with open(os.path.join(OOROOT, '单药疾病交集汇总_PerHerbOverlapSummary.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['药物', '靶点数', '疾病交集数', '交集占比', '来源库'])
    for herb in sorted(herb_genes):
        gs = set(herb_genes[herb])
        ov = gs & disease
        src = 'BATMAN-TCM 2.0' if herb == '水蛭' else 'TCMSP'
        w.writerow([herb, len(gs), len(ov), f'{len(ov)/len(gs):.3f}' if gs else '0', src])
    w.writerow(['合计(去重)', len(all_drug_genes), len(overlap),
                f'{len(overlap)/len(all_drug_genes):.3f}' if all_drug_genes else '0', ''])

with open(os.path.join(OOROOT, '单药疾病交集明细_PerHerbDiseaseOverlap.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['药物', 'Gene', '疾病来源库', '贡献成分'])
    for herb in sorted(herb_genes):
        for g in sorted(set(herb_genes[herb]) & disease):
            w.writerow([herb, g, dsrc.get(g, ''), '|'.join(sorted(herb_genes[herb][g]))])

# ---- 7. QC ----
with open(os.path.join(OOROOT, '交集质控_OverlapQC.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['项目', '数值/内容', '说明'])
    w.writerow(['TCMSP 成分靶点对(输入)', n_pairs, 'TCMSP_成分靶点映射_MoleculeTargetMap.csv'])
    w.writerow(['TCMSP 药-成分-靶点边(基因化后)', n_map, '按 herbs 多值展开'])
    w.writerow(['TCMSP 未解析靶点名数', len(unmapped), '不编造；见下'])
    for tname, hs in sorted(unmapped.items()):
        w.writerow([f'未解析[{tname}]', '|'.join(sorted(hs)), 'UniProt reviewed 无唯一基因简称'])
    w.writerow(['药物靶点并集(去重)', len(all_drug_genes), ''])
    w.writerow(['疾病并集', len(disease), ''])
    w.writerow(['药病交集', len(overlap), ''])

print(f'[drug] herbs={len(herb_genes)} genes={len(all_drug_genes)}')
for h in sorted(herb_genes):
    print(f'   {h}: {len(herb_genes[h])} genes')
print(f'[overlap] {len(overlap)} genes')
print(f'[unmapped] {len(unmapped)} target names')
