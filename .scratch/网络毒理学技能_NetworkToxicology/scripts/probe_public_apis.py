# -*- coding: utf-8 -*-
"""Probe public toxicology endpoints. No CAPTCHA bypass."""
import json
import urllib.request

UA = {"User-Agent": "RProject-network-toxicology-survey/1.0", "Accept": "application/json"}


def get(url, timeout=25, data=None, headers=None):
    h = dict(UA)
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(400)
            return r.status, r.headers.get("Content-Type", ""), body[:180]
    except Exception as e:
        return "FAIL", type(e).__name__, str(e)[:160]


checks = [
    ("pubchem", "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aspirin/property/CanonicalSMILES,CID/JSON"),
    ("chembl", "https://www.ebi.ac.uk/chembl/api/data/molecule/CHEMBL25.json"),
    ("opentargets", None),
    ("dgidb", None),
    ("aop_api", "https://aopwiki-api.cloud.vhp4safety.nl/api-git/marvinm2/AOPWikiQueries/get-all-aops"),
    ("stitch", "http://stitch.embl.de/"),
    ("t3db", "http://www.t3db.ca/"),
    ("ctd_home", "https://ctdbase.org/"),
    ("gutmgene", "https://bio-computing.hrbmu.edu.cn/gutmgene/"),
]

# GraphQL posts
ot_q = json.dumps({"query": "{ target(ensemblId: \"ENSG00000157764\") { id approvedSymbol } }"}).encode()
dg_q = json.dumps({"query": "{ genes(names: [\"TP53\"]) { nodes { name } } }"}).encode()

for name, url in checks:
    if name == "opentargets":
        st, ct, body = get(
            "https://api.platform.opentargets.org/api/v4/graphql",
            data=ot_q,
            headers={"Content-Type": "application/json"},
        )
    elif name == "dgidb":
        st, ct, body = get(
            "https://dgidb.org/api/graphql",
            data=dg_q,
            headers={"Content-Type": "application/json"},
        )
    else:
        st, ct, body = get(url)
    print(f"{name}\t{st}\t{ct}\t{body!r}")
