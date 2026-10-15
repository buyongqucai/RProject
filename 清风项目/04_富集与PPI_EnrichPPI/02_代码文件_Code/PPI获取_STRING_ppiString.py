"""清风项目 Step8：STRING PPI（API v12，score≥900 主交付 + ≥400 全量参考）。
输入: 药物疾病交集_DrugDiseaseOverlap.csv (Gene)
输出: 04_富集与PPI_EnrichPPI\...\PPI网络_STRING\ 下 tsv×2 + 节点度表 + QC
"""
import csv, os, sys, time
import requests
sys.stdout.reconfigure(encoding='utf-8')

IN = r'E:\RProject\清风项目\03_药病交集与网络_OverlapAndNetwork\01_数据文件_Data\02_结果数据_ResultTables\药物疾病交集_DrugDiseaseOverlap.csv'
OUT = r'E:\RProject\清风项目\04_富集与PPI_EnrichPPI\01_数据文件_Data\02_结果数据_ResultTables\PPI网络_STRING'
os.makedirs(OUT, exist_ok=True)

genes = [r['Gene'] for r in csv.DictReader(open(IN, encoding='utf-8-sig'))]
genes = sorted(set(genes))
print(f'[in] {len(genes)} genes')

def fetch(score, dest):
    url = 'https://string-db.org/api/tsv/network'
    payload = {
        'identifiers': '\r'.join(genes),
        'species': 9606,
        'required_score': score,
        'caller_identity': 'qingfeng_netpharm',
    }
    for attempt in range(3):
        try:
            r = requests.post(url, data=payload, timeout=180)
            r.raise_for_status()
            break
        except Exception as e:
            print(f'  [retry {attempt+1}] {e}')
            time.sleep(5)
    else:
        raise RuntimeError('STRING API failed')
    txt = r.text
    with open(dest, 'w', encoding='utf-8', newline='') as f:
        f.write(txt if txt.endswith('\n') else txt + '\n')
    lines = [l for l in txt.splitlines() if l.strip()]
    print(f'[score {score}] {max(0, len(lines)-1)} interactions -> {os.path.basename(dest)}')
    return lines

lines900 = fetch(900, os.path.join(OUT, 'PPI互作_StringInteractions_score900.tsv'))
time.sleep(1)
lines400 = fetch(400, os.path.join(OUT, 'PPI互作_StringInteractions.tsv'))

# 节点度（按 900 高置信）
deg = {}
hdr = lines900[0].split('\t')
ia, ib = hdr.index('preferredName_A'), hdr.index('preferredName_B')
for l in lines900[1:]:
    p = l.split('\t')
    for g in (p[ia], p[ib]):
        deg[g] = deg.get(g, 0) + 1
with open(os.path.join(OUT, 'PPI节点度表_STRING900.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['Gene', 'degree_900'])
    for g, d in sorted(deg.items(), key=lambda x: (-x[1], x[0])):
        w.writerow([g, d])

with open(os.path.join(OUT, 'PPI质控_PPIQC.csv'), 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['项目', '数值'])
    w.writerow(['输入基因', len(genes)])
    w.writerow(['STRING命中节点(900)', len(deg)])
    w.writerow(['互作边(900)', max(0, len(lines900) - 1)])
    w.writerow(['互作边(400)', max(0, len(lines400) - 1)])
    miss = [g for g in genes if g not in deg]
    w.writerow(['无互作基因数(900)', len(miss)])
    w.writerow(['无互作基因(900)', '|'.join(miss)])

print(f'[deg] {len(deg)} nodes; isolated(900)={len(genes)-len(deg)}')
