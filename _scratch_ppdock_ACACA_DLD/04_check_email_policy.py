# -*- coding: utf-8 -*-
import re
import urllib.request
import ssl

ctx = ssl.create_default_context()
UA = {"User-Agent": "Mozilla/5.0"}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
        return r.read().decode("utf-8", "replace"), r.geturl()


for url in [
    "https://cluspro.bu.edu/login.php",
    "https://cluspro.bu.edu/",
    "https://cluspro.org/",
    "https://zdock.wenglab.org/",
]:
    try:
        html, final = fetch(url)
    except Exception as e:
        print("FAIL", url, e)
        continue
    print("====", url, "->", final)
    for m in re.finditer(r'href=["\']([^"\']+)["\']', html):
        h = m.group(1)
        if any(k in h.lower() for k in ["reg", "sign", "creat", "account", "join", "help"]):
            print(" link:", h)
    text = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = " ".join(text.split())
    low = text.lower()
    for key in ["academic", "edu", "email", "register", "non-profit", "commercial", "username"]:
        i = low.find(key)
        if i >= 0:
            print(" ", key, ":", text[max(0, i - 40) : i + 100])
    print()
