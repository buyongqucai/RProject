"""Drive visible Edge: ZDOCK upload → select contacting/blocking → submit.

Residue rationale (ACACA–DLD; no co-crystal interface):
  CONTACT (filter, keep few — ALL must be ≤6 Å of partner):
    DLD chain A E3BP/E2 partner face: 437, 443, 444
  BLOCK (dummy atom type 19; keep catalytic faces out of PPI):
    DLD A/B redox site: 45, 50, 452
    ACACA C ATP-loop + CoA sites: 315–320, 1823, 2127, 2129
"""
from __future__ import annotations

import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

ROOT = Path(r"E:\RProject\_scratch_ppdock_ACACA_DLD\PPDock_ACACA_DLD")
ST = ROOT / "01_clean" / "ST_ACACA_6G2D_chainC_CA.pdb"
PT = ROOT / "01_clean" / "PT_DLD_6I4Q_AB_CA.pdb"
OUT = ROOT / "02_submit"
EMAIL = "1054034696@stu.cqut.edu.cn"

# contacting: DLD A only (few)
CONTACT = {
    "2": [("A", 437), ("A", 443), ("A", 444)],  # protein 2
}
# blocking
BLOCK = {
    "1": [("C", r) for r in list(range(315, 321)) + [1823, 2127, 2129]],
    "2": [("A", 45), ("A", 50), ("A", 452), ("B", 45), ("B", 50), ("B", 452)],
}


def dump(driver, name: str) -> Path:
    p = OUT / name
    p.write_text(driver.page_source, encoding="utf-8", errors="replace")
    print("saved", p, "title=", driver.title, "url=", driver.current_url)
    return p


def option_matches(text: str, chain: str, resi: int) -> bool:
    # ZDOCK format: " 437  Chain A  GLU"
    return bool(re.search(rf"^\s*{resi}\s+Chain\s+{re.escape(chain)}\s+", text, re.I))


def select_residues(sel: Select, wanted: list[tuple[str, int]]) -> list[str]:
    """Multi-select matching options; returns matched labels."""
    matched = []
    # clear existing
    for opt in sel.options:
        if opt.is_selected:
            sel.deselect_by_index(list(sel.options).index(opt) if False else 0)
    # deselect_all if multiple
    try:
        sel.deselect_all()
    except Exception:
        pass
    for opt in sel.options:
        for ch, ri in wanted:
            if option_matches(opt.text or opt.get_attribute("value") or "", ch, ri):
                if not opt.is_selected:
                    # ctrl-click style via Select
                    sel.select_by_visible_text(opt.text) if opt.text else sel.select_by_value(opt.get_attribute("value"))
                matched.append(opt.text.strip())
                break
    return matched


def find_residue_selects(driver):
    """Return dict keyed by role from nearby labels / names / onchange."""
    selects = driver.find_elements(By.TAG_NAME, "select")
    info = []
    for s in selects:
        name = (s.get_attribute("name") or "")
        onchange = (s.get_attribute("onchange") or "")
        size = s.get_attribute("size")
        multiple = s.get_attribute("multiple")
        nopt = len(s.find_elements(By.TAG_NAME, "option"))
        # previous text
        label = ""
        try:
            label = s.find_element(By.XPATH, "./ancestor::td[1]/preceding-sibling::td[1]").text
        except Exception:
            pass
        if not label:
            try:
                label = s.find_element(By.XPATH, "./preceding::*[self::b or self::strong or self::font][1]").text
            except Exception:
                pass
        info.append(
            {
                "el": s,
                "name": name,
                "onchange": onchange,
                "size": size,
                "multiple": multiple,
                "nopt": nopt,
                "label": (label or "")[:120],
            }
        )
    return info


def main() -> None:
    assert ST.exists() and PT.exists(), (ST, PT)
    OUT.mkdir(parents=True, exist_ok=True)

    opts = Options()
    opts.add_argument("--start-maximized")
    opts.set_capability("unhandledPromptBehavior", "accept")
    # visible Edge
    driver = webdriver.Edge(options=opts)
    wait = WebDriverWait(driver, 60)
    try:
        driver.get("https://zdock.wenglab.org/")
        time.sleep(2)
        dump(driver, "zdock_edge_home.html")

        # Protein 1/2 → PDB File
        Select(driver.find_element(By.NAME, "pdb1select")).select_by_value("file")
        Select(driver.find_element(By.NAME, "pdb2select")).select_by_value("file")
        time.sleep(0.5)
        driver.find_element(By.ID, "file1").send_keys(str(ST))
        driver.find_element(By.ID, "file2").send_keys(str(PT))
        email = driver.find_element(By.NAME, "useremail")
        email.clear()
        email.send_keys(EMAIL)

        # ensure Skip residue selection OFF
        skip = driver.find_element(By.NAME, "skipselect")
        if skip.is_selected():
            skip.click()

        # ZDOCK 3.0.2 default
        driver.find_element(By.NAME, "upload").click()
        time.sleep(5)
        dump(driver, "zdock_edge_after_upload.html")

        # Wait until residue selects appear or confirmation
        for _ in range(24):
            src = driver.page_source.lower()
            if "contact" in src or "block" in src or "show_selected" in src:
                break
            if "two emails" in src or "average wait" in src:
                print("Job submitted without residue page (skip?).")
                dump(driver, "zdock_edge_done_early.html")
                return
            time.sleep(2)
        dump(driver, "zdock_edge_residue_page.html")

        # Jmol often pops a compatibility alert in Edge — dismiss and continue
        for _ in range(3):
            try:
                al = driver.switch_to.alert
                print("alert:", al.text[:120].replace("\n", " "))
                al.accept()
                time.sleep(0.5)
            except Exception:
                break

        infos = find_residue_selects(driver)
        print("--- selects ---")
        for i, inf in enumerate(infos):
            print(
                i,
                "nopt=",
                inf["nopt"],
                "mult=",
                inf["multiple"],
                "name=",
                inf["name"],
                "onchange=",
                inf["onchange"][:80],
                "label=",
                repr(inf["label"][:80]),
            )

        # Classify multi-selects with many options as residue lists
        residue_boxes = [inf for inf in infos if inf["nopt"] >= 50 and inf["multiple"] is not None]
        if not residue_boxes:
            residue_boxes = [inf for inf in infos if inf["nopt"] >= 50]

        # Heuristic: pair by onchange show_selected(this, pdb_num, is_block)
        # is_block 0/1, pdb_num 0/1 (0=prot1, 1=prot2)
        assigned = {}
        for inf in residue_boxes:
            m = re.search(r"show_selected\s*\([^,]+,\s*(\d+)\s*,\s*['\"]?(\d+)['\"]?\s*\)", inf["onchange"])
            if m:
                pdb_num, is_block = m.group(1), m.group(2)
                key = ("block" if is_block == "1" else "contact", str(int(pdb_num) + 1))
                assigned[key] = inf
            else:
                # fallback by label keywords
                lab = (inf["label"] + " " + inf["name"]).lower()
                role = "block" if "block" in lab else ("contact" if "contact" in lab or "bind" in lab else None)
                prot = "1" if ("protein 1" in lab or "pdb1" in lab or lab.endswith("1")) else (
                    "2" if ("protein 2" in lab or "pdb2" in lab) else None
                )
                if role and prot:
                    assigned[(role, prot)] = inf

        print("assigned", {k: v["nopt"] for k, v in assigned.items()})

        report = {}

        def dismiss_alerts() -> None:
            for _ in range(2):
                try:
                    driver.switch_to.alert.accept()
                    time.sleep(0.3)
                except Exception:
                    break

        # Prefer JS over live WebElements (survives Jmol alerts / reflows)
        name_map = {
            ("block", "1"): "nonContactRec[]",
            ("block", "2"): "nonContactLig[]",
            ("contact", "1"): "contactRec[]",
            ("contact", "2"): "contactLig[]",
        }
        for role, prot in [
            ("contact", "2"),
            ("block", "1"),
            ("block", "2"),
        ]:
            wanted = (CONTACT if role == "contact" else BLOCK).get(prot, [])
            if not wanted:
                continue
            dismiss_alerts()
            name = name_map[(role, prot)]
            # Build selected=true by matching option text in-page
            js = """
            const name = arguments[0];
            const wanted = arguments[1]; // [[chain, resi], ...]
            const sel = document.getElementsByName(name)[0];
            if (!sel) return {error: 'no select', got: []};
            // clear prior
            for (const opt of sel.options) opt.selected = false;
            const got = [];
            const unmatched = wanted.map(w => w[0] + ':' + w[1]);
            for (const opt of sel.options) {
              // normalize spaces: " 437  Chain A  GLU" -> "437 Chain A GLU"
              const t = (opt.textContent || '').replace(/\\s+/g, ' ').trim();
              for (let i = 0; i < wanted.length; i++) {
                const ch = wanted[i][0], ri = String(wanted[i][1]);
                const needle = ri + ' Chain ' + ch + ' ';
                if (t.startsWith(needle) || t.indexOf(needle) === 0) {
                  opt.selected = true;
                  got.push(t);
                  const key = ch + ':' + ri;
                  const ix = unmatched.indexOf(key);
                  if (ix >= 0) unmatched.splice(ix, 1);
                  break;
                }
              }
            }
            sel.dispatchEvent(new Event('change', {bubbles:true}));
            return {got: got, unmatched: unmatched,
                    nSelected: Array.prototype.filter.call(sel.options, o => o.selected).length,
                    sample: (sel.options[0] && sel.options[0].textContent) || ''};
            """
            wanted_js = [[ch, int(ri)] for ch, ri in wanted]
            try:
                result = driver.execute_script(js, name, wanted_js)
            except Exception as e:
                dismiss_alerts()
                result = driver.execute_script(js, name, wanted_js)
            print(role, prot, result)
            report[f"{role}_P{prot}"] = result.get("got") if isinstance(result, dict) else result
            dismiss_alerts()

        print("REPORT", report)
        (OUT / "zdock_residue_selection_report.txt").write_text(
            "\n".join(f"{k}: {v}" for k, v in report.items()), encoding="utf-8"
        )

        dismiss_alerts()
        # abort submit if nothing selected
        n_sel = sum(len(v) for v in report.values() if isinstance(v, list))
        if n_sel == 0:
            # report values may be dicts
            n_sel = 0
            for v in report.values():
                if isinstance(v, dict):
                    n_sel += len(v.get("got") or [])
                elif isinstance(v, list):
                    n_sel += len(v)
        if n_sel == 0:
            raise SystemExit("No residues selected — not submitting empty selection")

        time.sleep(1)
        try:
            driver.execute_script(
                """
                const b = document.querySelector('input[type=submit].btn, input[type=submit][value=Submit], input[type=submit]');
                if (b) { b.click(); return true; }
                return false;
                """
            )
        except Exception as e:
            print("JS submit error", e)
            dismiss_alerts()
        time.sleep(4)
        dismiss_alerts()
        dump(driver, "zdock_edge_after_residue_submit.html")
        try:
            body = driver.find_element(By.TAG_NAME, "body").text
        except Exception:
            dismiss_alerts()
            body = driver.find_element(By.TAG_NAME, "body").text
        print("confirm snippet:", re.sub(r"\s+", " ", body)[:600])

        # confirmation page: click OK
        if "click OK" in body or "correct residues" in body.lower():
            try:
                driver.execute_script(
                    """
                    const b = [...document.querySelectorAll('input[type=submit],input[type=button],button')]
                      .find(x => /ok/i.test(x.value||x.textContent||''));
                    if (b) b.click();
                    """
                )
            except Exception as e:
                print("OK click failed", e)
            time.sleep(5)
            dismiss_alerts()
            dump(driver, "zdock_edge_final.html")
            try:
                body2 = driver.find_element(By.TAG_NAME, "body").text
            except Exception:
                dismiss_alerts()
                body2 = driver.find_element(By.TAG_NAME, "body").text
            print("final snippet:", re.sub(r"\s+", " ", body2)[:500])

        print("Edge left open 45s for you to inspect…")
        time.sleep(45)
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
