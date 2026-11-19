from pathlib import Path
import re

html = Path(
    r"E:/RProject/_scratch_ppdock_ACACA_DLD/PPDock_ACACA_DLD/02_submit/zdock_edge_residue_page.html"
).read_text(encoding="utf-8", errors="replace")
for name in ["contactLig", "nonContactLig", "nonContactRec"]:
    m2 = re.search(rf"name=.{{0,3}}{name}\[\].*?</select>", html, re.S)
    if not m2:
        print(name, "NO SELECT")
        continue
    opts = re.findall(
        r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>',
        m2.group(0),
    )
    print(name, "n", len(opts))
    print(" first", opts[0])
    print(
        " hits",
        [o for o in opts if any(x in (o[0] + o[1]) for x in ("437", " 45 ", "315"))][:6],
    )
