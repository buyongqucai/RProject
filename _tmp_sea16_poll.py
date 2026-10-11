import re, requests, time
s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0"})
r=s.get("https://sea16.docking.org/search",timeout=30)
token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',r.text).group(1)
p=s.post("https://sea16.docking.org/search",data={"query_custom_fp_type":"rdkit_ecfp","ref_type":"library","ref_library_targets_paste":"","query_type":"custom","query_custom_targets_paste":"CCCC(=O)[O-] m0002","csrf_token":token},timeout=60)
url=p.url
print("job",url)
for i in range(20):
    rr=s.get(url,timeout=30)
    print("poll",i,rr.status_code,len(rr.text),"finished" in rr.text.lower(),"result" in rr.text.lower())
    if "finished" in rr.text.lower() or rr.status_code==200 and "In Progress" not in rr.text:
        print(rr.text[:10000])
        break
    time.sleep(5)
