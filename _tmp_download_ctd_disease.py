import requests, pathlib, time
url='https://ctdbase.org/reports/CTD_chemicals_diseases.csv.gz'
out=pathlib.Path(r'E:\RProject\努力学习项目\网络毒理学_菌群代谢物双交集\准备文件\外部数据库\CTD\CTD_chemicals_diseases.csv.gz')
s=requests.Session(); s.trust_env=False; s.headers['User-Agent']='Mozilla/5.0'
with s.get(url,stream=True,timeout=(30,180)) as r:
 print(r.status_code,r.headers.get('content-length'),flush=True)
 r.raise_for_status()
 with out.open('wb') as f:
  for chunk in r.iter_content(1024*1024):
   if chunk: f.write(chunk)
print(out.stat().st_size,flush=True)
