import requests, pathlib, concurrent.futures, os, math
url='https://ctdbase.org/reports/CTD_chemicals_diseases.csv.gz'
out=pathlib.Path(r'E:\RProject\努力学习项目\网络毒理学_菌群代谢物双交集\准备文件\外部数据库\CTD\CTD_chemicals_diseases.csv.gz')
total=163603578; workers=8; chunk=math.ceil(total/workers)
parts=[]
def fetch(i):
 s=requests.Session(); s.trust_env=False; s.headers['User-Agent']='Mozilla/5.0'
 start=i*chunk; end=min(total-1,start+chunk-1); part=out.with_suffix(out.suffix+f'.part{i:02d}')
 for attempt in range(8):
  try:
   with s.get(url,headers={'Range':f'bytes={start}-{end}'},stream=True,timeout=(30,300)) as r:
    print(i,r.status_code,r.headers.get('Content-Range'),flush=True); r.raise_for_status()
    with part.open('wb') as f:
     for b in r.iter_content(1024*1024):
      if b: f.write(b)
   print('done',i,part.stat().st_size,flush=True); return part
  except Exception as e:
   print('retry',i,attempt,repr(e),flush=True)
 raise RuntimeError(i)
with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
 parts=list(ex.map(fetch,range(workers)))
with out.open('wb') as w:
 for p in parts:
  with p.open('rb') as r:
   while True:
    b=r.read(1024*1024)
    if not b: break
    w.write(b)
print('final',out.stat().st_size,flush=True)
