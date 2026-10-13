import re
import urllib.request

base = "https://ftp.ncbi.nlm.nih.gov/geo/series/"
urls = [
    "GSE197nnn/GSE197289/suppl/",
    "GSE131nnn/GSE131272/suppl/",
    "GSE322nnn/GSE322600/suppl/",
]
for u in urls:
    url = base + u
    print("==", url)
    try:
        with urllib.request.urlopen(url, timeout=90) as r:
            t = r.read().decode("utf-8", "replace")
        names = re.findall(r'href="([^"]+)"', t)
        for n in names:
            if n not in ("../", "/"):
                print(" ", n)
    except Exception as e:
        print(" ERR", type(e).__name__, e)
