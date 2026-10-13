import urllib.request
url = "https://string-db.org/api/tsv/network?identifiers=Cplx2%0dScarb2&species=10090&required_score=400"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as r:
    text = r.read().decode("utf-8", "replace")
print(text[:2000])
print("---lines", len(text.splitlines()))
