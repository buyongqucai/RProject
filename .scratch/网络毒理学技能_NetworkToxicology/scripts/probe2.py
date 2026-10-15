# -*- coding: utf-8 -*-
import concurrent.futures
import json
import urllib.request

UA = {"User-Agent": "RProject-survey/1.0", "Accept": "application/json"}


def get(name, url, data=None, headers=None, timeout=12):
    h = dict(UA)
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = r.read(100).decode("utf-8", "replace").replace("\n", " ")
            return f"{name}|{r.status}|{b[:90]}"
    except Exception as e:
        return f"{name}|FAIL|{type(e).__name__}: {str(e)[:90]}"


ot = json.dumps(
    {"query": "{ target(ensemblId: \"ENSG00000157764\") { approvedSymbol } }"}
).encode()
jobs = [
    ("pubchem", "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aspirin/cids/JSON", None, None),
    ("chembl", "https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL25.json", None, None),
    ("opentargets", "https://api.platform.opentargets.org/api/v4/graphql", ot, {"Content-Type": "application/json"}),
    ("aop", "https://aopwiki-api.cloud.vhp4safety.nl/api-git/marvinm2/AOPWikiQueries/get-all-aops", None, None),
    ("gutmgene", "https://bio-computing.hrbmu.edu.cn/gutmgene/", None, None),
    ("stitch", "http://stitch.embl.de/", None, None),
]


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(get, *j) for j in jobs]
        for f in concurrent.futures.as_completed(futs, timeout=25):
            print(f.result(), flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
