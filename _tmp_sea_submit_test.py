import base64, hashlib, json, time, requests
base="http://sea.bkslab.org"
s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36","Accept":"application/json, text/plain, */*","Referer":"https://sea.bkslab.org/"})
resp=s.get(base+"/api/captcha/challenge",timeout=30); print("challenge_http",resp.status_code,resp.url,resp.text[:500]); ch=resp.json()
target=bytes.fromhex(ch["challenge"])
salt=ch["salt"].encode()
number=None
for n in range(ch["maxNumber"]+1):
    if hashlib.sha256(salt+str(n).encode()).digest()==target:
        number=n
        break
print("number",number)
obj={"algorithm":ch["algorithm"],"challenge":ch["challenge"],"number":number,"salt":ch["salt"],"signature":ch["signature"]}
payload=base64.b64encode(json.dumps(obj,separators=(",",":")).encode()).decode()
query_text="CC(=O)[O-] m0001\nCCCC(=O)[O-] m0002"
body={"query":query_text,"fingerprint_type":"ecfp4","reference_target":"all","reference_custom_targets":"","query_target":"subset","query_subset_targets":"","query_custom":"","altcha":payload}
r=s.post(base+"/api/submit",json=body,timeout=60)
print(r.status_code,r.text[:2000])
if r.ok:
    tid=r.json().get("task_id")
    for i in range(40):
        rr=s.get(base+"/api/result",params={"taskId":tid},timeout=60)
        print("poll",i,rr.status_code,rr.text[:500])
        data=rr.json()
        if data.get("status") in ("SUCCESS","ERROR"):
            break
        time.sleep(5)





