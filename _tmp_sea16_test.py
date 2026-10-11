import re, requests
s=requests.Session()
s.headers.update({"User-Agent":"Mozilla/5.0"})
r=s.get("https://sea16.docking.org/search",timeout=30)
print("get",r.status_code,len(r.text),s.cookies.get_dict())
token=re.search(r'name="csrf_token"[^>]*value="([^"]+)"',r.text).group(1)
data={
"query_custom_fp_type":"rdkit_ecfp",
"ref_type":"library",
"ref_library_targets_paste":"",
"query_type":"custom",
"query_custom_targets_paste":"CC(=O)[O-] m0001",
"csrf_token":token,
}
p=s.post("https://sea16.docking.org/search",data=data,timeout=60,allow_redirects=True)
print("post",p.status_code,p.url,len(p.text))
print(p.text[:3000])
